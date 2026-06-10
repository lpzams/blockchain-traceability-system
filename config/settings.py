import os
from datetime import timedelta

class Config:
    """基础配置"""

    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 数据库配置
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'blockchain.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 会话配置
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # 区块链配置
    BLOCKCHAIN_DIFFICULTY = 4  # 挖矿难度

    # 并发配置
    MAX_WORKERS = 5  # 线程池最大工作线程数
    TASK_TIMEOUT = 30  # 任务超时时间（秒）

    # 缓存配置
    CACHE_DEFAULT_TTL = 300  # 默认缓存时间（秒）
    CACHE_CLEANUP_INTERVAL = 600  # 缓存清理间隔（秒）

    # API 配置
    API_RATE_LIMIT = 100  # 每分钟最大请求数
    API_TIMEOUT = 30  # API 超时时间（秒）

    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'blockchain.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # 性能配置
    ENABLE_QUERY_CACHE = True
    ENABLE_ASYNC_TASKS = True
    ENABLE_PERFORMANCE_MONITORING = True

    # 安全配置
    BCRYPT_LOG_ROUNDS = 12
    PASSWORD_MIN_LENGTH = 8

    # 分页配置
    PRODUCTS_PER_PAGE = 20
    BLOCKS_PER_PAGE = 10


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    BLOCKCHAIN_DIFFICULTY = 2
    LOG_LEVEL = 'DEBUG'
    CACHE_DEFAULT_TTL = 60


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    BCRYPT_LOG_ROUNDS = 14
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    DATABASE_PATH = ':memory:'
    BLOCKCHAIN_DIFFICULTY = 1
    ENABLE_QUERY_CACHE = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """获取配置对象"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
