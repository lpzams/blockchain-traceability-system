from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from functools import wraps
import logging
from models.database import (get_db_connection, get_user_by_id, get_all_products, get_active_recalls,
                             get_user_notifications, mark_notification_read, get_unread_notification_count)

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('权限不足', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """管理员仪表板"""
    from models.blockchain import blockchain

    current_user = get_user_by_id(session['user_id'])
    unread_count = get_unread_notification_count(session['user_id'])

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 统计信息
        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM products')
        total_products = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM notifications WHERE is_read = 0')
        unread_notifications = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM product_recalls WHERE status = "active"')
        active_recalls = cursor.fetchone()['count']

        # 用户统计
        cursor.execute('''
            SELECT role, COUNT(*) as count FROM users
            GROUP BY role
        ''')
        user_stats = cursor.fetchall()

    blockchain_height = len(blockchain.chain)

    return render_template('admin/dashboard.html',
                         current_user=current_user,
                         unread_count=unread_count,
                         total_users=total_users,
                         total_products=total_products,
                         unread_notifications=unread_notifications,
                         active_recalls=active_recalls,
                         blockchain_height=blockchain_height,
                         user_stats=user_stats)


@admin_bp.route('/users')
@admin_required
def users():
    """用户管理"""
    current_user = get_user_by_id(session['user_id'])

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        all_users = cursor.fetchall()

    return render_template('admin/users.html',
                         users=all_users,
                         current_user=current_user)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    if user_id == session['user_id']:
        flash('无法删除自己', 'danger')
        return redirect(url_for('admin.users'))

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        flash('用户已删除', 'success')
    except Exception as e:
        flash(f'删除失败: {str(e)}', 'danger')

    return redirect(url_for('admin.users'))


@admin_bp.route('/products')
@admin_required
def products():
    """产品管理"""
    current_user = get_user_by_id(session['user_id'])
    all_products = get_all_products()

    return render_template('admin/products.html',
                         products=all_products,
                         current_user=current_user)


@admin_bp.route('/recalls')
@admin_required
def recalls():
    """召回管理"""
    current_user = get_user_by_id(session['user_id'])
    recalls = get_active_recalls()

    return render_template('admin/recalls.html',
                         recalls=recalls,
                         current_user=current_user)


@admin_bp.route('/recalls/<int:recall_id>/close', methods=['POST'])
@admin_required
def close_recall(recall_id):
    """关闭召回"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE product_recalls
                SET status = "closed", updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (recall_id,))
        flash('召回已关闭', 'success')
    except Exception as e:
        flash(f'关闭失败: {str(e)}', 'danger')

    return redirect(url_for('admin.recalls'))


@admin_bp.route('/notifications')
@admin_required
def notifications():
    """查看通知"""
    current_user = get_user_by_id(session['user_id'])
    notifications = get_user_notifications(session['user_id'], limit=50)
    unread_count = get_unread_notification_count(session['user_id'])

    return render_template('notifications.html',
                         notifications=notifications,
                         unread_count=unread_count,
                         current_user=current_user)


@admin_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@admin_required
def mark_admin_notification_read(notification_id):
    """标记通知为已读"""
    mark_notification_read(notification_id)
    return jsonify({'success': True})


@admin_bp.route('/system')
@admin_required
def system():
    """系统监控"""
    from models.blockchain import blockchain

    current_user = get_user_by_id(session['user_id'])

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 获取数据库统计
        cursor.execute('SELECT COUNT(*) as count FROM blocks')
        total_blocks = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM events')
        total_events = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM notifications WHERE created_at > datetime("now", "-1 day")')
        notifications_24h = cursor.fetchone()['count']

    return render_template('admin/system.html',
                         current_user=current_user,
                         blockchain_height=len(blockchain.chain),
                         total_blocks=total_blocks,
                         total_events=total_events,
                         notifications_24h=notifications_24h)
