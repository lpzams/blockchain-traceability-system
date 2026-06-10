from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from models.database import get_db_connection, get_user_by_id

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@chat_bp.route('/room')
@login_required
def chat_room():
    """聊天室页面"""
    current_user = get_user_by_id(session['user_id'])
    return render_template('chat/room.html', current_user=current_user)


@chat_bp.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    """获取聊天消息"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.user_id, m.message, m.created_at,
                   u.username, u.company_name, u.role
            FROM chat_messages m
            JOIN users u ON m.user_id = u.id
            ORDER BY m.created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        messages = cursor.fetchall()

    return jsonify({
        'success': True,
        'messages': [dict(m) for m in reversed(messages)]
    })


@chat_bp.route('/api/send', methods=['POST'])
@login_required
def send_message():
    """发送聊天消息"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'success': False, 'error': '消息不能为空'}), 400

        if len(message) > 500:
            return jsonify({'success': False, 'error': '消息过长'}), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_messages (user_id, message)
                VALUES (?, ?)
            ''', (session['user_id'], message))

        return jsonify({'success': True, 'message': '消息已发送'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/api/user-count', methods=['GET'])
@login_required
def get_user_count():
    """获取在线用户数（当日活跃）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as count
            FROM chat_messages
            WHERE date(created_at) = date('now')
        ''')
        result = cursor.fetchone()

    return jsonify({
        'success': True,
        'online_users': result['count'] if result else 0
    })
