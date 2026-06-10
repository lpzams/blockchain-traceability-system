from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from functools import wraps
from models.traceability import get_product_history, verify_product
from services.services import ConsumerService, cache_manager
from services.product_features import (
    ProductRatingService, ProductFavoriteService,
    ProductWatchService, ProductComparisonService
)
from services.qrcode_service import QRCodeService
from models.database import (get_user_by_id, get_user_notifications, mark_notification_read,
                             get_unread_notification_count, get_active_recalls, get_product_by_id,
                             get_all_products, record_query_history, get_products_by_owner)

consumer_bp = Blueprint('consumer', __name__, url_prefix='/consumer')


def consumer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'consumer':
            flash('权限不足', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@consumer_bp.route('/dashboard')
@consumer_required
def dashboard():
    from models.database import get_user_by_id, get_all_products, get_product_events_for_user, get_db_connection
    from models.blockchain import blockchain

    current_user = get_user_by_id(session['user_id'])
    blockchain_height = len(blockchain.chain)
    unread_count = get_unread_notification_count(session['user_id'])

    all_products = get_all_products()
    all_events = get_product_events_for_user(session['user_id'])

    # 修复查询统计
    query_count = 0
    verification_count = 0
    trace_count = 0

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 查询次数
        cursor.execute('SELECT COUNT(*) as count FROM consumer_query_history WHERE user_id = ? AND query_type = "trace"', (session['user_id'],))
        result = cursor.fetchone()
        query_count = result['count'] if result else 0

        # 验证次数
        cursor.execute('SELECT COUNT(*) as count FROM consumer_query_history WHERE user_id = ? AND query_type = "verify"', (session['user_id'],))
        result = cursor.fetchone()
        verification_count = result['count'] if result else 0

        # 最近查询记录
        cursor.execute('''
            SELECT cqh.*, p.name as product_name, p.batch_number
            FROM consumer_query_history cqh
            LEFT JOIN products p ON cqh.product_id = p.product_id
            WHERE cqh.user_id = ?
            ORDER BY cqh.created_at DESC
            LIMIT 5
        ''', (session['user_id'],))
        recent_queries = cursor.fetchall()

    trace_count = query_count + verification_count

    # 获取消费者持有的产品
    my_products = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*,
                   m.username as manufacturer_name, m.company_name as manufacturer_company
            FROM products p
            LEFT JOIN users m ON p.manufacturer_id = m.id
            WHERE p.current_owner_id = ?
            ORDER BY p.created_at DESC
        ''', (session['user_id'],))
        my_products = cursor.fetchall()

    return render_template('consumer/dashboard.html',
                         current_user=current_user,
                         blockchain_height=blockchain_height,
                         query_count=query_count,
                         verification_count=verification_count,
                         trace_count=trace_count,
                         recent_queries=recent_queries,
                         my_products=my_products,
                         unread_count=unread_count)


@consumer_bp.route('/query', methods=['GET', 'POST'])
@consumer_required
def query():
    from models.database import get_all_products, record_query_history

    if request.method == 'POST':
        query_input = request.form.get('product_id', '').strip()
        if query_input:
            from models.database import get_product_by_id
            product = get_product_by_id(query_input)

            if not product:
                all_products = get_all_products()
                product = next((p for p in all_products if p['batch_number'] == query_input), None)

            if product:
                # 记录查询历史
                record_query_history(session['user_id'], product['product_id'], 'trace')
                return redirect(url_for('consumer.trace_result', product_id=product['product_id']))
            else:
                flash('产品不存在，请检查产品ID或批次号', 'danger')
        else:
            flash('请输入产品ID或批次号', 'warning')

    return render_template('consumer/query.html')


@consumer_bp.route('/verify', methods=['GET', 'POST'])
@consumer_required
def verify():
    from models.database import get_product_by_id, get_all_products, record_query_history

    if request.method == 'POST':
        query_input = request.form.get('product_id', '').strip()
        if query_input:
            # 先尝试用UUID查
            product = get_product_by_id(query_input)

            # 找不到则用批次号查
            if not product:
                all_products = get_all_products()
                product = next((p for p in all_products if p['batch_number'] == query_input), None)

            if product:
                # 记录验证历史
                record_query_history(session['user_id'], product['product_id'], 'verify')
                verification = verify_product(product['product_id'])
                return render_template('consumer/verify.html',
                                     product_id=product['product_id'],
                                     verification={'valid': verification[0], 'message': verification[1]})
            else:
                flash('产品不存在，请检查产品ID或批次号', 'danger')
        else:
            flash('请输入产品ID或批次号', 'warning')

    return render_template('consumer/verify.html')


@consumer_bp.route('/trace', methods=['GET', 'POST'])
@consumer_required
def trace():
    from models.database import get_user_by_id, get_product_by_id, get_all_products

    current_user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        query_input = request.form.get('product_id', '').strip()
        if query_input:
            # 先尝试用UUID查
            product = get_product_by_id(query_input)

            # 找不到则用批次号查
            if not product:
                all_products = get_all_products()
                product = next((p for p in all_products if p['batch_number'] == query_input), None)

            if product:
                consumer_service = ConsumerService(current_app.mq)
                try:
                    trace_data = consumer_service.trace_product(product['product_id'])
                    return render_template('consumer/trace.html',
                                         product=trace_data,
                                         trace_data=trace_data,
                                         current_user=current_user)
                except ValueError:
                    flash('产品不存在', 'danger')
            else:
                flash('产品不存在，请检查产品ID或批次号', 'danger')
        else:
            flash('请输入产品ID或批次号', 'warning')

    return render_template('consumer/trace.html',
                         product=None,
                         current_user=current_user)


@consumer_bp.route('/trace_result/<product_id>')
@consumer_required
def trace_result(product_id):
    consumer_service = ConsumerService(current_app.mq)
    try:
        trace_data = consumer_service.trace_product(product_id)
        return render_template('consumer/trace_result.html',
                             product=trace_data,
                             trace_data=trace_data)
    except ValueError:
        flash('产品不存在', 'danger')
        return redirect(url_for('consumer.query'))


@consumer_bp.route('/search', methods=['GET', 'POST'])
@consumer_required
def search():
    """产品搜索"""
    results = []
    if request.method == 'POST':
        keyword = request.form.get('keyword', '')
        search_type = request.form.get('search_type', 'name')

        if keyword:
            consumer_service = ConsumerService(current_app.mq)
            results = consumer_service.search_products(keyword, search_type)

            if not results:
                flash('未找到匹配的产品', 'info')

    return render_template('consumer/search.html', results=results)


@consumer_bp.route('/api/trace/<product_id>')
@consumer_required
def api_trace(product_id):
    """获取产品溯源信息的 API"""
    try:
        consumer_service = ConsumerService(current_app.mq)
        trace_data = consumer_service.trace_product(product_id)
        return jsonify({
            'success': True,
            'data': trace_data
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consumer_bp.route('/api/search')
@consumer_required
def api_search():
    """搜索 API"""
    keyword = request.args.get('keyword', '')
    search_type = request.args.get('type', 'name')

    if not keyword:
        return jsonify({'success': False, 'error': 'Missing keyword'}), 400

    consumer_service = ConsumerService(current_app.mq)
    results = consumer_service.search_products(keyword, search_type)

    return jsonify({
        'success': True,
        'results': results,
        'count': len(results)
    })


# ========== 产品评价功能 ==========

@consumer_bp.route('/rate/<product_id>', methods=['GET', 'POST'])
@consumer_required
def rate_product(product_id):
    """产品评价页面"""
    from models.database import get_user_by_id

    current_user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '').strip()

        try:
            ProductRatingService.add_rating(product_id, session['user_id'], rating, comment)
            flash('评价成功！', 'success')
            return redirect(url_for('consumer.trace_result', product_id=product_id))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('评价失败，请稍后重试', 'danger')

    # 获取产品信息和现有评价
    try:
        consumer_service = ConsumerService(current_app.mq)
        trace_data = consumer_service.trace_product(product_id)
        rating_summary = ProductRatingService.get_product_rating_summary(product_id)
        user_rating = ProductRatingService.get_user_rating(product_id, session['user_id'])

        return render_template('consumer/rate_product.html',
                             product=trace_data,
                             rating_summary=rating_summary,
                             user_rating=user_rating,
                             current_user=current_user)
    except ValueError:
        flash('产品不存在', 'danger')
        return redirect(url_for('consumer.query'))


@consumer_bp.route('/api/rate/<product_id>', methods=['POST'])
@consumer_required
def api_rate_product(product_id):
    """产品评价API"""
    try:
        data = request.get_json()
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '').strip()

        result = ProductRatingService.add_rating(product_id, session['user_id'], rating, comment)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@consumer_bp.route('/api/ratings/<product_id>')
@consumer_required
def api_get_ratings(product_id):
    """获取产品评价API"""
    try:
        rating_summary = ProductRatingService.get_product_rating_summary(product_id)
        return jsonify({'success': True, 'data': rating_summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 产品收藏功能 ==========

@consumer_bp.route('/favorites')
@consumer_required
def favorites():
    """收藏列表页面"""
    from models.database import get_user_by_id

    current_user = get_user_by_id(session['user_id'])
    favorites = ProductFavoriteService.get_user_favorites(session['user_id'])

    return render_template('consumer/favorites.html',
                         favorites=favorites,
                         current_user=current_user)


@consumer_bp.route('/api/favorite/<product_id>', methods=['POST'])
@consumer_required
def api_add_favorite(product_id):
    """添加收藏API"""
    try:
        result = ProductFavoriteService.add_favorite(product_id, session['user_id'])
        return jsonify(result)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@consumer_bp.route('/api/favorite/<product_id>', methods=['DELETE'])
@consumer_required
def api_remove_favorite(product_id):
    """取消收藏API"""
    try:
        result = ProductFavoriteService.remove_favorite(product_id, session['user_id'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@consumer_bp.route('/api/favorite/<product_id>/status')
@consumer_required
def api_favorite_status(product_id):
    """检查收藏状态API"""
    try:
        is_favorited = ProductFavoriteService.is_favorited(product_id, session['user_id'])
        return jsonify({'success': True, 'is_favorited': is_favorited})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 产品关注功能 ==========

@consumer_bp.route('/watches')
@consumer_required
def watches():
    """关注列表页面"""
    from models.database import get_user_by_id

    current_user = get_user_by_id(session['user_id'])
    watches = ProductWatchService.get_user_watches(session['user_id'])

    return render_template('consumer/watches.html',
                         watches=watches,
                         current_user=current_user)


@consumer_bp.route('/api/watch/<product_id>', methods=['POST'])
@consumer_required
def api_add_watch(product_id):
    """添加关注API"""
    try:
        data = request.get_json() or {}
        notify_on_transfer = data.get('notify_on_transfer', True)
        notify_on_quality_check = data.get('notify_on_quality_check', True)

        result = ProductWatchService.add_watch(
            product_id, session['user_id'],
            notify_on_transfer, notify_on_quality_check
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@consumer_bp.route('/api/watch/<product_id>', methods=['DELETE'])
@consumer_required
def api_remove_watch(product_id):
    """取消关注API"""
    try:
        result = ProductWatchService.remove_watch(product_id, session['user_id'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@consumer_bp.route('/api/watch/<product_id>/status')
@consumer_required
def api_watch_status(product_id):
    """检查关注状态API"""
    try:
        is_watched = ProductWatchService.is_watched(product_id, session['user_id'])
        return jsonify({'success': True, 'is_watched': is_watched})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 产品对比功能 ==========

@consumer_bp.route('/compare')
@consumer_required
def compare():
    """产品对比页面"""
    from models.database import get_user_by_id

    current_user = get_user_by_id(session['user_id'])
    product_ids = request.args.getlist('products')

    comparison_data = None
    if product_ids:
        try:
            comparison_data = ProductComparisonService.compare_products(product_ids)
        except ValueError as e:
            flash(str(e), 'warning')
        except Exception as e:
            flash('对比失败，请稍后重试', 'danger')

    return render_template('consumer/compare.html',
                         comparison_data=comparison_data,
                         current_user=current_user)


@consumer_bp.route('/api/compare', methods=['POST'])
@consumer_required
def api_compare():
    """产品对比API"""
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])

        if not product_ids:
            return jsonify({'success': False, 'error': '请提供产品ID列表'}), 400

        comparison_data = ProductComparisonService.compare_products(product_ids)
        return jsonify({'success': True, 'data': comparison_data})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 二维码生成功能 ==========

@consumer_bp.route('/qrcode/<product_id>')
@consumer_required
def product_qrcode(product_id):
    """产品二维码页面"""
    from models.database import get_user_by_id

    current_user = get_user_by_id(session['user_id'])

    try:
        consumer_service = ConsumerService(current_app.mq)
        trace_data = consumer_service.trace_product(product_id)

        # 生成二维码
        base_url = request.host_url.rstrip('/')
        qr_code = QRCodeService.generate_product_qr(product_id, base_url)
        qr_info = QRCodeService.get_qr_info(product_id, base_url)

        return render_template('consumer/qrcode.html',
                             product=trace_data,
                             qr_code=qr_code,
                             qr_info=qr_info,
                             current_user=current_user)
    except ValueError:
        flash('产品不存在', 'danger')
        return redirect(url_for('consumer.query'))


@consumer_bp.route('/api/qrcode/<product_id>')
@consumer_required
def api_generate_qrcode(product_id):
    """生成产品二维码API"""
    try:
        from models.database import get_product_by_id

        product = get_product_by_id(product_id)
        if not product:
            return jsonify({'success': False, 'error': '产品不存在'}), 404

        base_url = request.host_url.rstrip('/')
        qr_code = QRCodeService.generate_product_qr(product_id, base_url)
        qr_info = QRCodeService.get_qr_info(product_id, base_url)

        if qr_code:
            return jsonify({
                'success': True,
                'qr_code': qr_code,
                'qr_info': qr_info
            })
        else:
            return jsonify({'success': False, 'error': '二维码生成失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@consumer_bp.route('/api/qrcode/batch', methods=['POST'])
@consumer_required
def api_batch_qrcode():
    """批量生成二维码API"""
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])

        if not product_ids:
            return jsonify({'success': False, 'error': '请提供产品ID列表'}), 400

        if len(product_ids) > 20:
            return jsonify({'success': False, 'error': '最多只能批量生成20个二维码'}), 400

        base_url = request.host_url.rstrip('/')
        qr_codes = QRCodeService.generate_batch_qr_codes(product_ids, base_url)

        return jsonify({
            'success': True,
            'qr_codes': qr_codes,
            'count': len(qr_codes)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@consumer_bp.route('/notifications')
@consumer_required
def notifications():
    """查看通知"""
    current_user = get_user_by_id(session['user_id'])
    notifications = get_user_notifications(session['user_id'], limit=50)
    unread_count = get_unread_notification_count(session['user_id'])

    return render_template('notifications.html',
                         notifications=notifications,
                         unread_count=unread_count,
                         current_user=current_user)


@consumer_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@consumer_required
def mark_consumer_notification_read(notification_id):
    """标记通知为已读"""
    mark_notification_read(notification_id)
    return jsonify({'success': True})


@consumer_bp.route('/recalls')
@consumer_required
def recalls():
    """查看产品召回警告"""
    current_user = get_user_by_id(session['user_id'])
    recalls = get_active_recalls()

    # 检查消费者持有的产品是否在召回列表中
    my_recalls = []
    if recalls:
        from models.database import get_products_by_owner
        my_products = get_products_by_owner(session['user_id'])
        my_product_ids = [p['product_id'] for p in my_products]

        for recall in recalls:
            if recall['product_id'] in my_product_ids:
                my_recalls.append(recall)

    return render_template('consumer/recalls.html',
                         recalls=my_recalls,
                         current_user=current_user)
