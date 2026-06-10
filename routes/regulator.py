from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from functools import wraps
from models.database import get_db_connection
from models.traceability import get_product_history, verify_product
from services.services import RegulatorService, cache_manager

regulator_bp = Blueprint('regulator', __name__, url_prefix='/regulator')


def regulator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'regulator':
            flash('权限不足', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@regulator_bp.route('/dashboard')
@regulator_required
def dashboard():
    from models.database import get_user_by_id, get_all_products
    from models.blockchain import blockchain

    current_user = get_user_by_id(session['user_id'])
    reg_service = RegulatorService(current_app.mq)

    # 获取系统健康状态
    health = reg_service.get_system_health()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 获取统计数据
        cursor.execute('SELECT COUNT(*) as count FROM products')
        total_products = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_companies = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM events')
        total_events = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role='manufacturer'")
        manufacturer_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role='distributor'")
        distributor_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role='consumer'")
        consumer_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_type='transfer'")
        total_transfers = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_type='quality_check'")
        total_quality_checks = cursor.fetchone()['count']

        # 获取最近注册的产品
        cursor.execute('''
            SELECT p.*, u1.company_name as manufacturer_company, u1.username as manufacturer_name,
                   u2.company_name as owner_company, u2.username as owner_name
            FROM products p
            LEFT JOIN users u1 ON p.manufacturer_id = u1.id
            LEFT JOIN users u2 ON p.current_owner_id = u2.id
            ORDER BY p.created_at DESC
            LIMIT 10
        ''')
        recent_products = cursor.fetchall()

        blockchain_height = len(blockchain.chain)

    return render_template('regulator/dashboard.html',
                         current_user=current_user,
                         total_products=total_products,
                         total_companies=total_companies,
                         total_quality_checks=total_quality_checks,
                         blockchain_height=blockchain_height,
                         manufacturer_count=manufacturer_count,
                         distributor_count=distributor_count,
                         consumer_count=consumer_count,
                         total_transfers=total_transfers,
                         recent_products=recent_products,
                         health=health)


@regulator_bp.route('/audit_trail')
@regulator_required
def audit_trail():
    from models.database import get_user_by_id

    current_user = get_user_by_id(session['user_id'])
    page = request.args.get('page', 1, type=int)
    activity_type = request.args.get('activity_type', '')

    reg_service = RegulatorService(current_app.mq)
    audit_data = reg_service.get_audit_trail()

    # 分页处理
    items_per_page = 20
    total_events = len(audit_data['events'])
    total_pages = (total_events + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page

    events = audit_data['events'][start:end]

    return render_template('regulator/audit_trail.html',
                         current_user=current_user,
                         events=events,
                         audit_data=audit_data,
                         page=page,
                         total_pages=total_pages)


@regulator_bp.route('/blockchain_info')
@regulator_required
def blockchain_info():
    """区块链信息页面"""
    from models.database import get_user_by_id

    current_user = get_user_by_id(session['user_id'])
    reg_service = RegulatorService(current_app.mq)

    integrity = reg_service.verify_blockchain_integrity()

    return render_template('regulator/blockchain_info.html',
                         current_user=current_user,
                         integrity=integrity)


@regulator_bp.route('/product/<product_id>')
@regulator_required
def product_detail(product_id):
    from models.database import get_user_by_id

    current_user = get_user_by_id(session['user_id'])
    history = get_product_history(product_id)

    if not history:
        flash('产品不存在', 'danger')
        return redirect(url_for('regulator.dashboard'))

    verification = verify_product(product_id)

    return render_template('regulator/product_detail.html',
                         current_user=current_user,
                         product=history['product'],
                         history=history,
                         verification_status=verification[0])


@regulator_bp.route('/api/health')
@regulator_required
def api_health():
    """系统健康状态 API"""
    reg_service = RegulatorService(current_app.mq)
    health = reg_service.get_system_health()
    return jsonify(health)


@regulator_bp.route('/api/audit-summary')
@regulator_required
def api_audit_summary():
    """审计摘要 API"""
    reg_service = RegulatorService(current_app.mq)
    audit_data = reg_service.get_audit_trail()

    return jsonify({
        'total_events': audit_data['total_events'],
        'total_products': audit_data['total_products'],
        'events_by_type': audit_data['events_by_type'],
        'events_by_date': audit_data['events_by_date']
    })


@regulator_bp.route('/api/blockchain-integrity')
@regulator_required
def api_blockchain_integrity():
    """区块链完整性检查 API"""
    reg_service = RegulatorService(current_app.mq)
    integrity = reg_service.verify_blockchain_integrity()
    return jsonify(integrity)


@regulator_bp.route('/compliance-report')
@regulator_required
def compliance_report():
    """合规报告"""
    from models.database import get_user_by_id, get_all_products, get_all_events

    current_user = get_user_by_id(session['user_id'])
    reg_service = RegulatorService(current_app.mq)

    # 获取审计数据
    audit_data = reg_service.get_audit_trail()
    integrity = reg_service.verify_blockchain_integrity()

    # 计算合规指标
    report = {
        'timestamp': audit_data.get('timestamp', ''),
        'total_products': audit_data['total_products'],
        'total_events': audit_data['total_events'],
        'blockchain_valid': integrity['valid'],
        'compliance_status': 'PASS' if integrity['valid'] else 'FAIL',
        'events_summary': audit_data['events_by_type']
    }

    return render_template('regulator/compliance_report.html',
                         current_user=current_user,
                         report=report)


@regulator_bp.route('/system-monitor')
@regulator_required
def system_monitor():
    """系统监控页面"""
    from models.database import get_user_by_id

    current_user = get_user_by_id(session['user_id'])
    reg_service = RegulatorService(current_app.mq)

    health = reg_service.get_system_health()

    return render_template('regulator/system_monitor.html',
                         current_user=current_user,
                         health=health)
