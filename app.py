import os
import logging
from flask import Flask, render_template, session, jsonify
from config.config import get_config
from routes.auth import auth_bp
from routes.manufacturer import manufacturer_bp
from routes.distributor import distributor_bp
from routes.consumer import consumer_bp
from routes.regulator import regulator_bp
from routes.admin import admin_bp
from routes.advanced_features import advanced_features_bp
from routes.chat import chat_bp
from routes.analytics import analytics_bp
from routes.blockchain_features import blockchain_features_bp
from models.traceability import get_blockchain_status
from models.blockchain import blockchain
from models.database import init_database, get_db_connection, create_user, get_user_by_username
from services.message_queue import MessageQueueFactory
from services.notifications import NotificationManager
from services.async_processor import AsyncTaskProcessor
from werkzeug.security import generate_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 从环境变量获取配置，默认为开发环境 - 必须在使用任何 session 之前设置
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(get_config(env))

# 初始化数据库
init_database()

# 创建默认管理员账号（如果不存在）
try:
    logger.info("开始检查管理员账号...")
    admin_user = get_user_by_username('admin')
    logger.info(f"查询结果: {admin_user}")

    if not admin_user:
        logger.info("开始创建管理员账号...")
        password_hash = generate_password_hash('1')
        logger.info(f"密码已哈希")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role, company_name)
                    VALUES (?, ?, ?, ?)
                ''', ('admin', password_hash, 'admin', '系统管理'))
                logger.info("✓ 默认管理员账号已创建 (用户名: admin, 密码: 1)")
            except Exception as insert_err:
                logger.error(f"管理员账号创建异常: {insert_err}")
                logger.info("尝试使用 INSERT OR IGNORE")
                cursor.execute('''
                    INSERT OR IGNORE INTO users (username, password_hash, role, company_name)
                    VALUES (?, ?, ?, ?)
                ''', ('admin', password_hash, 'admin', '系统管理'))
                logger.info("✓ 管理员账号已准备就绪")
    else:
        logger.info("✓ 管理员账号已存在")
except Exception as e:
    logger.error(f"创建管理员账号时发生错误: {e}")
    import traceback
    logger.error(traceback.format_exc())

# 创建演示数据用于测试高级功能
try:
    from datetime import datetime
    demo_user = get_user_by_username('demo_factory')
    if not demo_user:
        logger.info("创建演示用户...")
        demo_password_hash = generate_password_hash('123456')
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, company_name)
                VALUES (?, ?, ?, ?)
            ''', ('demo_factory', demo_password_hash, 'manufacturer', '演示工厂有限公司'))

            # 获取用户ID
            cursor.execute('SELECT id FROM users WHERE username = ?', ('demo_factory',))
            user_id = cursor.fetchone()[0]

            # 创建产品
            batch_number = 'DEMO-2024-001'
            for i in range(1, 4):
                product_id = f'DEMO-PROD-{i:03d}'
                cursor.execute('''
                    INSERT OR IGNORE INTO products
                    (product_id, name, batch_number, manufacturer_id, current_owner_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (product_id, f'演示产品{i}', batch_number, user_id, user_id, datetime.now().isoformat()))

            # 创建事件
            cursor.execute('SELECT product_id FROM products WHERE batch_number = ?', (batch_number,))
            products = cursor.fetchall()
            for product in products:
                product_id = product[0]
                cursor.execute('''
                    INSERT INTO events (product_id, event_type, from_user_id, to_user_id, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (product_id, 'register', user_id, user_id, '已注册', datetime.now().isoformat()))
                cursor.execute('''
                    INSERT INTO events (product_id, event_type, from_user_id, to_user_id, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (product_id, 'quality_check', user_id, user_id, '合格', datetime.now().isoformat()))

            # 创建区块
            for i, product in enumerate(products, 1):
                product_id = product[0]
                cursor.execute('''
                    INSERT INTO blocks (product_id, block_number, hash, data, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (product_id, i, f'0x{"a"*62}{i:02d}', f'{{"product_id":"{product_id}"}}', datetime.now().isoformat()))

            logger.info("✓ 演示数据已创建 (用户名: demo_factory, 密码: 123456)")
    else:
        logger.info("✓ 演示用户已存在")
except Exception as e:
    logger.warning(f"创建演示数据时出错: {e}")

# 初始化消息队列
app.mq = MessageQueueFactory.get_instance({
    'use_redis': False,
    'redis_host': os.environ.get('REDIS_HOST', 'localhost'),
    'redis_port': int(os.environ.get('REDIS_PORT', 6379))
})

# 初始化通知管理器
app.notification_manager = None

# 初始化异步处理器
app.async_processor = None

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(manufacturer_bp)
app.register_blueprint(distributor_bp)
app.register_blueprint(consumer_bp)
app.register_blueprint(regulator_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(advanced_features_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(blockchain_features_bp)


@app.before_request
def init_services():
    """初始化服务"""
    if app.notification_manager is None:
        from models.database import get_db_connection
        with get_db_connection() as db:
            app.notification_manager = NotificationManager(db, app.mq)

    if app.async_processor is None:
        app.async_processor = AsyncTaskProcessor(app.mq, app.notification_manager)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/blockchain')
def blockchain_explorer():
    """产品溯源区块链浏览器 - 专业长安链集成"""
    from models.mock_chainmaker_client import get_mock_chainmaker_client

    try:
        # 获取模拟长安链客户端
        cm_client = get_mock_chainmaker_client()

        if cm_client.is_connected():
            # 获取长安链数据
            blocks = cm_client.get_recent_blocks(20)
            chain_info = cm_client.get_chain_info()
            system_status = cm_client.get_system_status()

            blockchain_info = {
                'is_connected': True,
                'version': cm_client.get_chain_version(),
                'height': cm_client.get_block_height(),
                'blocks': blocks,
                'type': 'chainmaker',
                'mode': '长安链产品溯源',
                'chain_info': chain_info,
                'system_status': system_status,
                'tx_count': chain_info.get('tx_count', 0),
                'node_count': chain_info.get('node_count', 4)
            }

            return render_template('blockchain_explorer_chainmaker.html',
                                 blockchain_info=blockchain_info,
                                 blocks=blocks)
        else:
            return render_template('blockchain_explorer_chainmaker.html',
                                 blockchain_info={'is_connected': False},
                                 blocks=[])

    except Exception as e:
        logger.error(f"区块链浏览器错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return render_template('blockchain_explorer_chainmaker.html',
                             blockchain_info={'is_connected': False, 'error': str(e)},
                             blocks=[])


@app.route('/system/stats')
def system_stats():
    """系统统计信息"""
    from models.database import get_all_products, get_all_events

    products = get_all_products()
    events = get_all_events()

    return jsonify({
        'total_products': len(products),
        'total_events': len(events),
        'blockchain_height': len(blockchain.chain),
        'mq_health': 'healthy'
    })


@app.route('/api/health')
def api_health():
    """API 健康检查"""
    return jsonify({
        'status': 'healthy',
        'blockchain_height': len(blockchain.chain),
        'mq_status': 'operational'
    })


if __name__ == '__main__':
    # 启动异步任务处理器
    try:
        async_processor = AsyncTaskProcessor(app.mq)
        workers = async_processor.start_workers()
        logger.info("Async task processors started successfully")
    except Exception as e:
        logger.error(f"Failed to start async processors: {str(e)}")

    app.run(host='0.0.0.0', port=5000, debug=True)
