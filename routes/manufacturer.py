from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from functools import wraps
import logging
from models.traceability import register_product, add_quality_check, transfer_ownership
from models.database import (get_products_by_manufacturer, get_product_by_id, get_product_events, get_db_connection,
                             get_purchase_requests_for_manufacturer, update_purchase_request_status,
                             get_user_by_id, get_user_notifications, mark_notification_read,
                             get_unread_notification_count, add_notification, create_recall, get_active_recalls)
from services.services import ProductService, cache_manager
from services.notifications import NotificationManager, NotificationType, NotificationPriority

logger = logging.getLogger(__name__)

manufacturer_bp = Blueprint('manufacturer', __name__, url_prefix='/manufacturer')


def manufacturer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'manufacturer':
            flash('权限不足', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@manufacturer_bp.route('/dashboard')
@manufacturer_required
def dashboard():
    from models.database import get_user_by_id
    from models.blockchain import blockchain

    products = get_products_by_manufacturer(session['user_id'])
    current_user = get_user_by_id(session['user_id'])
    unread_count = get_unread_notification_count(session['user_id'])

    # 使用 ProductService 获取统计数据（带缓存）
    product_service = ProductService(current_app.mq)
    stats = product_service.get_product_statistics(session['user_id'])

    blockchain_height = len(blockchain.chain)

    return render_template('manufacturer/dashboard.html',
                         products=products,
                         current_user=current_user,
                         stats=stats,
                         blockchain_height=blockchain_height,
                         unread_count=unread_count)


@manufacturer_bp.route('/register', methods=['GET', 'POST'])
@manufacturer_required
def register_product_page():
    if request.method == 'POST':
        name = request.form.get('name')
        batch_number = request.form.get('batch_number')
        production_date = request.form.get('production_date')
        use_async = request.form.get('use_async') == 'on'

        try:
            if use_async:
                # 异步注册（处理高峰）
                product_service = ProductService(current_app.mq)
                task_id = product_service.register_product_async(
                    name=name,
                    batch_number=batch_number,
                    manufacturer_id=session['user_id'],
                    production_date=production_date
                )
                flash(f'产品注册已提交（任务ID: {task_id}），请稍候...', 'info')
                return redirect(url_for('manufacturer.dashboard'))
            else:
                # 同步注册
                product_id, block_hash = register_product(
                    name=name,
                    batch_number=batch_number,
                    manufacturer_id=session['user_id'],
                    production_date=production_date
                )
                flash(f'产品注册成功！产品ID: {product_id}', 'success')
                # 清除缓存
                cache_manager.delete(f"user_stats:{session['user_id']}")
                return redirect(url_for('manufacturer.product_detail', product_id=product_id))
        except Exception as e:
            flash(f'注册失败: {str(e)}', 'danger')

    return render_template('manufacturer/register_product.html')


@manufacturer_bp.route('/product/<product_id>')
@manufacturer_required
def product_detail(product_id):
    from models.traceability import get_product_history
    from models.database import get_user_by_id

    # 先直接查询产品
    product = get_product_by_id(product_id)
    if not product:
        flash('产品不存在', 'danger')
        return redirect(url_for('manufacturer.dashboard'))

    # 获取历史记录
    history = get_product_history(product_id)
    if not history:
        flash('产品不存在', 'danger')
        return redirect(url_for('manufacturer.dashboard'))

    current_user = get_user_by_id(session['user_id'])

    return render_template('manufacturer/product_detail.html',
                         product=product,
                         events=history['events'],
                         current_user=current_user)


@manufacturer_bp.route('/quality_check', methods=['GET', 'POST'])
@manufacturer_required
def quality_check():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        result = request.form.get('result')
        notes = request.form.get('notes')
        use_async = request.form.get('use_async') == 'on'

        try:
            if use_async:
                # 异步质检
                product_service = ProductService(current_app.mq)
                task_id = product_service.quality_check_async(
                    product_id=product_id,
                    inspector_id=session['user_id'],
                    result=result,
                    notes=notes
                )
                flash(f'质检任务已提交（任务ID: {task_id}）', 'info')
                return redirect(url_for('manufacturer.dashboard'))
            else:
                # 同步质检
                add_quality_check(product_id, session['user_id'], result, notes)
                flash('质检记录添加成功', 'success')
                cache_manager.delete(f"user_stats:{session['user_id']}")
                return redirect(url_for('manufacturer.product_detail', product_id=product_id))
        except Exception as e:
            flash(f'添加失败: {str(e)}', 'danger')

    products = get_products_by_manufacturer(session['user_id'])
    return render_template('manufacturer/quality_check.html', products=products)


@manufacturer_bp.route('/transfer', methods=['GET', 'POST'])
@manufacturer_required
def transfer_product():
    """生产商转移产品给经销商"""
    from models.database import get_user_by_id

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        to_user_id = request.form.get('to_user_id')
        location = request.form.get('location', '')

        try:
            transfer_ownership(product_id, session['user_id'], int(to_user_id), location)
            flash('产品转移成功', 'success')
            cache_manager.delete(f"user_stats:{session['user_id']}")
            return redirect(url_for('manufacturer.dashboard'))
        except Exception as e:
            flash(f'转移失败: {str(e)}', 'danger')

    products = get_products_by_manufacturer(session['user_id'])
    current_user = get_user_by_id(session['user_id'])

    # 获取所有经销商和消费者用户
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, role, company_name
            FROM users
            WHERE id != ? AND role IN ('distributor', 'consumer')
        ''', (session['user_id'],))
        available_users = cursor.fetchall()

    return render_template('manufacturer/transfer.html',
                         products=products,
                         users=available_users,
                         current_user=current_user)


@manufacturer_bp.route('/purchase_requests', methods=['GET'])
@manufacturer_required
def purchase_requests():
    """查看收到的采购申请"""
    current_user = get_user_by_id(session['user_id'])
    requests = get_purchase_requests_for_manufacturer(session['user_id'])

    return render_template('manufacturer/purchase_requests.html',
                         requests=requests,
                         current_user=current_user)


@manufacturer_bp.route('/approve_request/<int:request_id>', methods=['POST'])
@manufacturer_required
def approve_request(request_id):
    """批准采购申请"""
    try:
        # 获取申请信息
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pr.*, p.name as product_name, p.current_owner_id
                FROM purchase_requests pr
                LEFT JOIN products p ON pr.product_id = p.product_id
                WHERE pr.id = ?
            ''', (request_id,))
            purchase_req = cursor.fetchone()

        if not purchase_req:
            flash('申请不存在', 'danger')
            return redirect(url_for('manufacturer.purchase_requests'))

        # 验证权限：必须是生产商
        if purchase_req['manufacturer_id'] != session['user_id']:
            flash('无权限审批此申请', 'danger')
            return redirect(url_for('manufacturer.purchase_requests'))

        # 检查产品当前所有者：只有生产商或当前所有者才能批准转移
        if purchase_req['current_owner_id'] != session['user_id']:
            flash('您不是该产品的当前所有者，无法转移产品', 'danger')
            return redirect(url_for('manufacturer.purchase_requests'))

        # 转移产品给申请者
        transfer_ownership(
            purchase_req['product_id'],
            session['user_id'],
            purchase_req['requester_id'],
            location='采购申请'
        )

        # 更新申请状态
        update_purchase_request_status(request_id, 'approved')

        # 发送通知给申请者
        try:
            nm = NotificationManager()
            nm.send_notification(
                user_id=purchase_req['requester_id'],
                notification_type=NotificationType.PURCHASE_APPROVED,
                title='采购申请已批准',
                message=f'您申请的产品《{purchase_req["product_name"]}》已批准并转移给您',
                priority=NotificationPriority.HIGH
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {str(e)}")

        flash('采购申请已批准，产品已转移', 'success')

    except Exception as e:
        flash(f'批准失败: {str(e)}', 'danger')

    return redirect(url_for('manufacturer.purchase_requests'))


@manufacturer_bp.route('/reject_request/<int:request_id>', methods=['POST'])
@manufacturer_required
def reject_request(request_id):
    """拒绝采购申请"""
    try:
        # 获取申请信息
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pr.*, p.name as product_name
                FROM purchase_requests pr
                LEFT JOIN products p ON pr.product_id = p.product_id
                WHERE pr.id = ?
            ''', (request_id,))
            purchase_req = cursor.fetchone()

        if not purchase_req:
            flash('申请不存在', 'danger')
            return redirect(url_for('manufacturer.purchase_requests'))

        # 验证权限
        if purchase_req['manufacturer_id'] != session['user_id']:
            flash('无权限处理此申请', 'danger')
            return redirect(url_for('manufacturer.purchase_requests'))

        # 更新申请状态
        update_purchase_request_status(request_id, 'rejected')

        # 发送通知给申请者
        try:
            nm = NotificationManager()
            nm.send_notification(
                user_id=purchase_req['requester_id'],
                notification_type=NotificationType.PURCHASE_REJECTED,
                title='采购申请已拒绝',
                message=f'您申请的产品《{purchase_req["product_name"]}》已被拒绝',
                priority=NotificationPriority.MEDIUM
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {str(e)}")

        flash('采购申请已拒绝', 'success')

    except Exception as e:
        flash(f'拒绝失败: {str(e)}', 'danger')

    return redirect(url_for('manufacturer.purchase_requests'))


@manufacturer_bp.route('/api/product-events/<product_id>')
@manufacturer_required
def get_product_events_api(product_id):
    """获取产品事件的 API 端点"""
    try:
        events = get_product_events(product_id)
        return jsonify({
            'success': True,
            'events': [dict(e) for e in events]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@manufacturer_bp.route('/batch-register', methods=['GET', 'POST'])
@manufacturer_required
def batch_register():
    """批量注册产品"""
    if request.method == 'POST':
        try:
            import csv
            import io

            file = request.files['file']
            if not file or file.filename == '':
                flash('请选择文件', 'warning')
                return render_template('manufacturer/batch_register.html')

            # 读取 CSV 文件
            stream = io.TextIOWrapper(file.stream, encoding='utf-8')
            reader = csv.DictReader(stream)

            product_service = ProductService(current_app.mq)
            task_count = 0

            for row in reader:
                try:
                    product_service.register_product_async(
                        name=row.get('name', ''),
                        batch_number=row.get('batch_number', ''),
                        manufacturer_id=session['user_id'],
                        production_date=row.get('production_date', '')
                    )
                    task_count += 1
                except Exception as e:
                    logger.error(f"Failed to register product: {str(e)}")
                    continue

            flash(f'已提交 {task_count} 个产品注册任务', 'success')
            cache_manager.delete(f"user_stats:{session['user_id']}")
            return redirect(url_for('manufacturer.dashboard'))

        except Exception as e:
            flash(f'批量注册失败: {str(e)}', 'danger')

    return render_template('manufacturer/batch_register.html')


@manufacturer_bp.route('/statistics')
@manufacturer_required
def statistics():
    """产品统计页面"""
    product_service = ProductService(current_app.mq)
    stats = product_service.get_product_statistics(session['user_id'])
    products = get_products_by_manufacturer(session['user_id'])

    return render_template('manufacturer/statistics.html',
                         stats=stats,
                         products=products)


@manufacturer_bp.route('/notifications')
@manufacturer_required
def notifications():
    """查看通知"""
    current_user = get_user_by_id(session['user_id'])
    notifications = get_user_notifications(session['user_id'], limit=50)
    unread_count = get_unread_notification_count(session['user_id'])

    return render_template('notifications.html',
                         notifications=notifications,
                         unread_count=unread_count,
                         current_user=current_user)


@manufacturer_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@manufacturer_required
def mark_manufacturer_notification_read(notification_id):
    """标记通知为已读"""
    mark_notification_read(notification_id)
    return jsonify({'success': True})


@manufacturer_bp.route('/recalls', methods=['GET', 'POST'])
@manufacturer_required
def product_recalls():
    """产品召回管理"""
    current_user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        try:
            reason = request.form.get('reason')
            severity = request.form.get('severity', 'medium')
            product_id = request.form.get('product_id')

            recall_id = create_recall(
                manufacturer_id=session['user_id'],
                reason=reason,
                severity=severity,
                product_id=product_id
            )

            # 通知消费者
            if product_id:
                product = get_product_by_id(product_id)
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT DISTINCT current_owner_id FROM products
                        WHERE product_id = ?
                    ''', (product_id,))
                    owner = cursor.fetchone()
                    if owner and owner['current_owner_id']:
                        add_notification(
                            user_id=owner['current_owner_id'],
                            notification_type='PRODUCT_RECALL',
                            title='产品召回警告',
                            message=f'产品《{product["name"]}》因{reason}被召回，请立即停止使用',
                            priority='high'
                        )

            flash('产品召回已创建并通知相关方', 'success')
            return redirect(url_for('manufacturer.product_recalls'))

        except Exception as e:
            flash(f'召回失败: {str(e)}', 'danger')

    recalls = get_active_recalls(session['user_id'])
    products = get_products_by_manufacturer(session['user_id'])

    return render_template('manufacturer/recalls.html',
                         recalls=recalls,
                         products=products,
                         current_user=current_user)
