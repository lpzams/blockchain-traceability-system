from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from functools import wraps
import logging
from models.traceability import transfer_ownership, add_logistics, get_product_history
from models.database import (get_products_by_owner, get_db_connection, get_product_events, get_all_products,
                             get_product_by_id, create_purchase_request, get_purchase_requests_for_requester,
                             get_purchase_requests_for_manufacturer, update_purchase_request_status, get_user_by_id,
                             get_user_notifications, mark_notification_read, get_unread_notification_count,
                             add_carbon_footprint)
from services.services import DistributorService, cache_manager
from services.notifications import NotificationManager, NotificationType, NotificationPriority

logger = logging.getLogger(__name__)

distributor_bp = Blueprint('distributor', __name__, url_prefix='/distributor')


def distributor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'distributor':
            flash('权限不足', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@distributor_bp.route('/dashboard')
@distributor_required
def dashboard():
    from models.database import get_user_by_id
    from models.blockchain import blockchain

    products = get_products_by_owner(session['user_id'])
    current_user = get_user_by_id(session['user_id'])
    unread_count = get_unread_notification_count(session['user_id'])

    # 使用 DistributorService 获取分析数据
    dist_service = DistributorService(current_app.mq)
    analytics = dist_service.get_distributor_analytics(session['user_id'])

    blockchain_height = len(blockchain.chain)

    return render_template('distributor/dashboard.html',
                         products=products,
                         current_user=current_user,
                         analytics=analytics,
                         blockchain_height=blockchain_height,
                         unread_count=unread_count)


@distributor_bp.route('/product/<product_id>')
@distributor_required
def product_detail(product_id):
    from models.database import get_user_by_id
    from models.traceability import get_product_history

    # 获取完整历史记录
    history = get_product_history(product_id)
    if not history:
        flash('产品不存在', 'danger')
        return redirect(url_for('distributor.dashboard'))

    current_user = get_user_by_id(session['user_id'])
    product = history.get('product')

    return render_template('distributor/product_detail.html',
                         product=product,
                         history=history,
                         current_user=current_user)


@distributor_bp.route('/query', methods=['GET', 'POST'])
@distributor_required
def query():
    """经销商查询所有可用产品"""
    from models.database import get_user_by_id

    all_products = get_all_products()
    current_user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        query_input = request.form.get('product_id', '').strip()
        if query_input:
            product = get_product_by_id(query_input)
            if not product:
                product = next((p for p in all_products if p['batch_number'] == query_input), None)

            if product:
                return redirect(url_for('distributor.product_detail', product_id=product['product_id']))
            else:
                flash('产品不存在，请检查产品ID或批次号', 'danger')
        else:
            flash('请输入产品ID或批次号', 'warning')

    return render_template('distributor/query.html',
                         all_products=all_products,
                         current_user=current_user)


@distributor_bp.route('/purchase_requests', methods=['GET'])
@distributor_required
def purchase_requests():
    """查看采购申请列表"""
    current_user = get_user_by_id(session['user_id'])
    requests = get_purchase_requests_for_requester(session['user_id'])

    return render_template('distributor/purchase_requests.html',
                         requests=requests,
                         current_user=current_user)


@distributor_bp.route('/request_product/<product_id>', methods=['GET', 'POST'])
@distributor_required
def request_product(product_id):
    """向生产商请求产品"""
    product = get_product_by_id(product_id)
    if not product:
        flash('产品不存在', 'danger')
        return redirect(url_for('distributor.query'))

    if request.method == 'POST':
        quantity = int(request.form.get('quantity', 1))
        notes = request.form.get('notes', '')

        try:
            create_purchase_request(
                product_id=product_id,
                requester_id=session['user_id'],
                manufacturer_id=product['manufacturer_id'],
                quantity=quantity,
                notes=notes
            )
            flash('采购申请已提交，请等待生产商审核', 'success')
            return redirect(url_for('distributor.purchase_requests'))
        except Exception as e:
            flash(f'提交失败: {str(e)}', 'danger')

    current_user = get_user_by_id(session['user_id'])
    return render_template('distributor/request_product.html',
                         product=product,
                         current_user=current_user)


@distributor_bp.route('/transfer', methods=['GET', 'POST'])
@distributor_required
def transfer():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        to_user_id = request.form.get('to_user_id')
        location = request.form.get('location')
        use_async = request.form.get('use_async') == 'on'

        try:
            if use_async:
                # 异步转移（解耦处理）
                dist_service = DistributorService(current_app.mq)
                task_id = dist_service.transfer_ownership_async(
                    product_id=product_id,
                    from_user_id=session['user_id'],
                    to_user_id=int(to_user_id),
                    location=location
                )
                flash(f'产品转移已提交（任务ID: {task_id}）', 'info')
            else:
                # 同步转移
                transfer_ownership(product_id, session['user_id'], int(to_user_id), location)
                flash('产品转移成功', 'success')
                cache_manager.delete(f"distributor_analytics:{session['user_id']}")

            return redirect(url_for('distributor.dashboard'))
        except Exception as e:
            flash(f'转移失败: {str(e)}', 'danger')

    products = get_products_by_owner(session['user_id'])

    # 获取所有可以转移的用户（经销商和消费者）
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, role, company_name
            FROM users
            WHERE id != ? AND role IN ('distributor', 'consumer')
        ''', (session['user_id'],))
        users = cursor.fetchall()

    return render_template('distributor/transfer.html', products=products, users=users)


@distributor_bp.route('/logistics', methods=['GET', 'POST'])
@distributor_required
def logistics():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        location = request.form.get('location')
        status = request.form.get('status')
        use_async = request.form.get('use_async') == 'on'

        try:
            if use_async:
                # 异步添加物流（高并发处理）
                dist_service = DistributorService(current_app.mq)
                task_id = dist_service.add_logistics_async(
                    product_id=product_id,
                    user_id=session['user_id'],
                    location=location,
                    status=status
                )
                flash(f'物流信息已提交（任务ID: {task_id}）', 'info')
            else:
                # 同步添加物流
                add_logistics(product_id, session['user_id'], location, status)
                flash('物流信息添加成功', 'success')
                cache_manager.delete(f"distributor_analytics:{session['user_id']}")

            return redirect(url_for('distributor.dashboard'))
        except Exception as e:
            flash(f'添加失败: {str(e)}', 'danger')

    products = get_products_by_owner(session['user_id'])
    return render_template('distributor/logistics.html', products=products)


@distributor_bp.route('/add_logistics/<product_id>', methods=['GET', 'POST'])
@distributor_required
def add_logistics_for_product(product_id):
    from models.database import get_product_by_id, get_user_by_id

    product = get_product_by_id(product_id)
    current_user = get_user_by_id(session['user_id'])

    if not product:
        flash('产品不存在', 'danger')
        return redirect(url_for('distributor.dashboard'))

    if request.method == 'POST':
        location = request.form.get('location')
        status = request.form.get('status')

        try:
            add_logistics(product_id, session['user_id'], location, status)
            flash('物流信息添加成功', 'success')
            cache_manager.delete(f"distributor_analytics:{session['user_id']}")
            return redirect(url_for('distributor.product_detail', product_id=product_id))
        except Exception as e:
            flash(f'添加失败: {str(e)}', 'danger')

    class Form:
        def hidden_tag(self):
            return ''

    form = Form()
    return render_template('distributor/add_logistics.html',
                         product=product,
                         current_user=current_user,
                         form=form)


@distributor_bp.route('/network')
@distributor_required
def distribution_network():
    """查看分销网络"""
    dist_service = DistributorService(current_app.mq)
    network = dist_service.get_distribution_network()

    return render_template('distributor/network.html', network=network)


@distributor_bp.route('/api/analytics')
@distributor_required
def get_analytics_api():
    """获取分析数据的 API"""
    dist_service = DistributorService(current_app.mq)
    analytics = dist_service.get_distributor_analytics(session['user_id'])
    return jsonify(analytics)


@distributor_bp.route('/notifications')
@distributor_required
def notifications():
    """查看通知"""
    current_user = get_user_by_id(session['user_id'])
    notifications = get_user_notifications(session['user_id'], limit=50)
    unread_count = get_unread_notification_count(session['user_id'])

    return render_template('notifications.html',
                         notifications=notifications,
                         unread_count=unread_count,
                         current_user=current_user)


@distributor_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@distributor_required
def mark_distributor_notification_read(notification_id):
    """标记通知为已读"""
    mark_notification_read(notification_id)
    return jsonify({'success': True})


@distributor_bp.route('/add_logistics/<product_id>/with_carbon', methods=['POST'])
@distributor_required
def add_logistics_with_carbon(product_id):
    """添加物流信息并记录碳排放"""
    try:
        product = get_product_by_id(product_id)
        if not product:
            flash('产品不存在', 'danger')
            return redirect(url_for('distributor.dashboard'))

        location = request.form.get('location')
        status = request.form.get('status')
        distance_km = float(request.form.get('distance_km', 0))

        # 添加物流
        add_logistics(product_id, session['user_id'], location, status)

        # 计算碳排放（简化公式：0.12kg CO2 per km for truck）
        if distance_km > 0:
            co2_kg = distance_km * 0.12
            add_carbon_footprint(
                product_id=product_id,
                event_type='logistics',
                co2_kg=co2_kg,
                user_id=session['user_id'],
                notes=f'From {product["owner_company"]} to {location}, {distance_km}km'
            )

        flash('物流信息已添加，碳排放已记录', 'success')
        return redirect(url_for('distributor.product_detail', product_id=product_id))

    except Exception as e:
        flash(f'添加失败: {str(e)}', 'danger')
        return redirect(url_for('distributor.dashboard'))


