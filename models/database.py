import sqlite3
import os
from contextlib import contextmanager
from config.config import get_config

Config = get_config()


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    # 确保 data 目录存在
    db_dir = os.path.dirname(Config.DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('manufacturer', 'distributor', 'consumer', 'admin', 'regulator')),
                company_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                index_num INTEGER UNIQUE NOT NULL,
                timestamp REAL NOT NULL,
                data TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                nonce INTEGER DEFAULT 0,
                hash TEXT UNIQUE NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                batch_number TEXT,
                manufacturer_id INTEGER NOT NULL,
                production_date DATE,
                current_owner_id INTEGER,
                block_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manufacturer_id) REFERENCES users(id),
                FOREIGN KEY (current_owner_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK(event_type IN ('register', 'transfer', 'quality_check', 'logistics')),
                from_user_id INTEGER,
                to_user_id INTEGER,
                location TEXT,
                data TEXT,
                block_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (from_user_id) REFERENCES users(id),
                FOREIGN KEY (to_user_id) REFERENCES users(id)
            )
        ''')

        # 产品评价表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(product_id, user_id)
            )
        ''')

        # 产品收藏表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(product_id, user_id)
            )
        ''')

        # 产品关注表（用于接收更新通知）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_watches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                notify_on_transfer BOOLEAN DEFAULT 1,
                notify_on_quality_check BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(product_id, user_id)
            )
        ''')

        # 采购申请表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                requester_id INTEGER NOT NULL,
                manufacturer_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'completed')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (requester_id) REFERENCES users(id),
                FOREIGN KEY (manufacturer_id) REFERENCES users(id)
            )
        ''')

        # 消费者查询历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumer_query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                query_type TEXT CHECK(query_type IN ('trace', 'verify')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        ''')

        # 用户通知表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                priority TEXT DEFAULT 'medium',
                is_read BOOLEAN DEFAULT 0,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # 产品召回表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_recalls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manufacturer_id INTEGER NOT NULL,
                product_id TEXT,
                batch_number TEXT,
                reason TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manufacturer_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        ''')

        # 碳足迹表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carbon_footprint (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user_id INTEGER,
                co2_kg REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # 聊天消息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()


def save_block_to_db(block):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO blocks (index_num, timestamp, data, previous_hash, nonce, hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (block.index, block.timestamp, str(block.data), block.previous_hash, block.nonce, block.hash))


def get_user_by_username(username):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()


def get_user_by_id(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()


def create_user(username, password_hash, role, company_name=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, company_name)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, role, company_name))
        return cursor.lastrowid


def get_product_by_id(product_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*,
                   m.username as manufacturer_name, m.company_name as manufacturer_company,
                   o.username as owner_name, o.company_name as owner_company
            FROM products p
            LEFT JOIN users m ON p.manufacturer_id = m.id
            LEFT JOIN users o ON p.current_owner_id = o.id
            WHERE p.product_id = ?
        ''', (product_id,))
        return cursor.fetchone()


def get_products_by_owner(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*,
                   m.username as manufacturer_name, m.company_name as manufacturer_company
            FROM products p
            LEFT JOIN users m ON p.manufacturer_id = m.id
            WHERE p.current_owner_id = ?
            ORDER BY p.created_at DESC
        ''', (user_id,))
        return cursor.fetchall()


def get_products_by_manufacturer(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*,
                   o.username as owner_name, o.company_name as owner_company
            FROM products p
            LEFT JOIN users o ON p.current_owner_id = o.id
            WHERE p.manufacturer_id = ?
            ORDER BY p.created_at DESC
        ''', (user_id,))
        return cursor.fetchall()


def create_product(product_id, name, batch_number, manufacturer_id, production_date, block_hash):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (product_id, name, batch_number, manufacturer_id, production_date, current_owner_id, block_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, name, batch_number, manufacturer_id, production_date, manufacturer_id, block_hash))
        return cursor.lastrowid


def update_product_owner(product_id, new_owner_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products SET current_owner_id = ? WHERE product_id = ?
        ''', (new_owner_id, product_id))


def create_event(product_id, event_type, block_hash, from_user_id=None, to_user_id=None, location=None, data=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO events (product_id, event_type, from_user_id, to_user_id, location, data, block_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, event_type, from_user_id, to_user_id, location, data, block_hash))
        return cursor.lastrowid


def get_product_events(product_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*,
                   fu.username as from_username, fu.company_name as from_company,
                   tu.username as to_username, tu.company_name as to_company
            FROM events e
            LEFT JOIN users fu ON e.from_user_id = fu.id
            LEFT JOIN users tu ON e.to_user_id = tu.id
            WHERE e.product_id = ?
            ORDER BY e.created_at ASC
        ''', (product_id,))
        return cursor.fetchall()


def get_all_blocks_from_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM blocks ORDER BY index_num ASC')
        return cursor.fetchall()


def get_all_products():
    """获取所有产品（用于监管者）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*,
                   m.username as manufacturer_name, m.company_name as manufacturer_company,
                   o.username as owner_name, o.company_name as owner_company
            FROM products p
            LEFT JOIN users m ON p.manufacturer_id = m.id
            LEFT JOIN users o ON p.current_owner_id = o.id
            ORDER BY p.created_at DESC
        ''')
        return cursor.fetchall()


def get_all_events():
    """获取所有事件（用于监管者）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*,
                   fu.username as from_username, fu.company_name as from_company,
                   tu.username as to_username, tu.company_name as to_company
            FROM events e
            LEFT JOIN users fu ON e.from_user_id = fu.id
            LEFT JOIN users tu ON e.to_user_id = tu.id
            ORDER BY e.created_at DESC
        ''')
        return cursor.fetchall()


# ========== 产品评价相关函数 ==========

def add_product_rating(product_id, user_id, rating, comment=None):
    """添加或更新产品评价"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO product_ratings (product_id, user_id, rating, comment)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(product_id, user_id)
            DO UPDATE SET rating=?, comment=?, created_at=CURRENT_TIMESTAMP
        ''', (product_id, user_id, rating, comment, rating, comment))
        return cursor.lastrowid


def get_product_ratings(product_id):
    """获取产品的所有评价"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, u.username, u.company_name
            FROM product_ratings r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC
        ''', (product_id,))
        return cursor.fetchall()


def get_product_average_rating(product_id):
    """获取产品平均评分"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT AVG(rating) as avg_rating, COUNT(*) as rating_count
            FROM product_ratings
            WHERE product_id = ?
        ''', (product_id,))
        result = cursor.fetchone()
        return {
            'average': round(result['avg_rating'], 2) if result['avg_rating'] else 0,
            'count': result['rating_count']
        }


def get_user_rating_for_product(product_id, user_id):
    """获取用户对某产品的评价"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM product_ratings
            WHERE product_id = ? AND user_id = ?
        ''', (product_id, user_id))
        return cursor.fetchone()


# ========== 产品收藏相关函数 ==========

def add_product_favorite(product_id, user_id):
    """添加产品收藏"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO product_favorites (product_id, user_id)
            VALUES (?, ?)
        ''', (product_id, user_id))
        return cursor.lastrowid


def remove_product_favorite(product_id, user_id):
    """移除产品收藏"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM product_favorites
            WHERE product_id = ? AND user_id = ?
        ''', (product_id, user_id))
        return cursor.rowcount


def get_user_favorites(user_id):
    """获取用户的所有收藏"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, f.created_at as favorited_at,
                   m.username as manufacturer_name, m.company_name as manufacturer_company
            FROM product_favorites f
            JOIN products p ON f.product_id = p.product_id
            LEFT JOIN users m ON p.manufacturer_id = m.id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        ''', (user_id,))
        return cursor.fetchall()


def is_product_favorited(product_id, user_id):
    """检查产品是否已被收藏"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM product_favorites
            WHERE product_id = ? AND user_id = ?
        ''', (product_id, user_id))
        return cursor.fetchone()['count'] > 0


# ========== 产品关注相关函数 ==========

def add_product_watch(product_id, user_id, notify_on_transfer=True, notify_on_quality_check=True):
    """添加产品关注"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO product_watches
            (product_id, user_id, notify_on_transfer, notify_on_quality_check)
            VALUES (?, ?, ?, ?)
        ''', (product_id, user_id, notify_on_transfer, notify_on_quality_check))
        return cursor.lastrowid


def remove_product_watch(product_id, user_id):
    """移除产品关注"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM product_watches
            WHERE product_id = ? AND user_id = ?
        ''', (product_id, user_id))
        return cursor.rowcount


def get_user_watches(user_id):
    """获取用户关注的所有产品"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, w.notify_on_transfer, w.notify_on_quality_check, w.created_at as watched_at,
                   m.username as manufacturer_name, m.company_name as manufacturer_company
            FROM product_watches w
            JOIN products p ON w.product_id = p.product_id
            LEFT JOIN users m ON p.manufacturer_id = m.id
            WHERE w.user_id = ?
            ORDER BY w.created_at DESC
        ''', (user_id,))
        return cursor.fetchall()


def get_product_watchers(product_id, event_type=None):
    """获取关注某产品的所有用户"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if event_type == 'transfer':
            cursor.execute('''
                SELECT u.*, w.notify_on_transfer, w.notify_on_quality_check
                FROM product_watches w
                JOIN users u ON w.user_id = u.id
                WHERE w.product_id = ? AND w.notify_on_transfer = 1
            ''', (product_id,))
        elif event_type == 'quality_check':
            cursor.execute('''
                SELECT u.*, w.notify_on_transfer, w.notify_on_quality_check
                FROM product_watches w
                JOIN users u ON w.user_id = u.id
                WHERE w.product_id = ? AND w.notify_on_quality_check = 1
            ''', (product_id,))
        else:
            cursor.execute('''
                SELECT u.*, w.notify_on_transfer, w.notify_on_quality_check
                FROM product_watches w
                JOIN users u ON w.user_id = u.id
                WHERE w.product_id = ?
            ''', (product_id,))
        return cursor.fetchall()


def is_product_watched(product_id, user_id):
    """检查产品是否已被关注"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM product_watches
            WHERE product_id = ? AND user_id = ?
        ''', (product_id, user_id))
        return cursor.fetchone()['count'] > 0


def get_product_events_for_user(user_id):
    """获取与用户相关的所有产品事件"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*,
                   fu.username as from_username, fu.company_name as from_company,
                   tu.username as to_username, tu.company_name as to_company
            FROM events e
            LEFT JOIN users fu ON e.from_user_id = fu.id
            LEFT JOIN users tu ON e.to_user_id = tu.id
            WHERE e.to_user_id = ? OR e.from_user_id = ?
            ORDER BY e.created_at DESC
        ''', (user_id, user_id))
        return cursor.fetchall()


# ========== 采购申请相关函数 ==========

def create_purchase_request(product_id, requester_id, manufacturer_id, quantity=1, notes=None):
    """创建采购申请"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO purchase_requests (product_id, requester_id, manufacturer_id, quantity, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, requester_id, manufacturer_id, quantity, notes))
        return cursor.lastrowid


def get_purchase_requests_for_manufacturer(manufacturer_id, status=None):
    """获取当前所有者收到的采购申请（只显示自己拥有的产品的申请）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute('''
                SELECT pr.*,
                       p.name as product_name, p.batch_number,
                       r.username as requester_name, r.company_name as requester_company
                FROM purchase_requests pr
                JOIN products p ON pr.product_id = p.product_id
                JOIN users r ON pr.requester_id = r.id
                WHERE p.current_owner_id = ? AND pr.status = ?
                ORDER BY pr.created_at DESC
            ''', (manufacturer_id, status))
        else:
            cursor.execute('''
                SELECT pr.*,
                       p.name as product_name, p.batch_number,
                       r.username as requester_name, r.company_name as requester_company
                FROM purchase_requests pr
                JOIN products p ON pr.product_id = p.product_id
                JOIN users r ON pr.requester_id = r.id
                WHERE p.current_owner_id = ?
                ORDER BY pr.created_at DESC
            ''', (manufacturer_id,))
        return cursor.fetchall()


def get_purchase_requests_for_requester(requester_id):
    """获取经销商发送的采购申请"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pr.*,
                   p.name as product_name, p.batch_number,
                   m.username as manufacturer_name, m.company_name as manufacturer_company
            FROM purchase_requests pr
            JOIN products p ON pr.product_id = p.product_id
            JOIN users m ON pr.manufacturer_id = m.id
            WHERE pr.requester_id = ?
            ORDER BY pr.created_at DESC
        ''', (requester_id,))
        return cursor.fetchall()


def update_purchase_request_status(request_id, status):
    """更新采购申请状态"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE purchase_requests
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, request_id))
        return cursor.rowcount


def record_query_history(user_id, product_id, query_type):
    """记录消费者查询历史"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consumer_query_history (user_id, product_id, query_type)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, query_type))


def get_query_count(user_id, query_type):
    """获取消费者查询次数"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM consumer_query_history
            WHERE user_id = ? AND query_type = ?
        ''', (user_id, query_type))
        result = cursor.fetchone()
        return result['count'] if result else 0


# ========== 产品评价相关函数 ==========

def add_product_rating(product_id: str, user_id: int, rating: int, comment: str = None) -> int:
    """添加或更新产品评价"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO product_ratings
            (product_id, user_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (product_id, user_id, rating, comment))
        return cursor.lastrowid


def get_product_ratings(product_id: str):
    """获取产品的所有评价"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pr.*, u.username
            FROM product_ratings pr
            LEFT JOIN users u ON pr.user_id = u.id
            WHERE pr.product_id = ?
            ORDER BY pr.created_at DESC
        ''', (product_id,))
        return cursor.fetchall()


def get_product_average_rating(product_id: str):
    """获取产品的平均评分"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT AVG(rating) as average, COUNT(*) as count
            FROM product_ratings
            WHERE product_id = ?
        ''', (product_id,))
        result = cursor.fetchone()
        return {'average': round(result['average'], 1) if result['average'] else 0, 'count': result['count']}


def get_user_rating_for_product(product_id: str, user_id: int):
    """获取用户对产品的评价"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM product_ratings
            WHERE product_id = ? AND user_id = ?
        ''', (product_id, user_id))
        return cursor.fetchone()


# ========== 产品收藏相关函数 ==========

def add_product_favorite(product_id: str, user_id: int) -> int:
    """添加产品收藏"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO product_favorites (product_id, user_id)
            VALUES (?, ?)
        ''', (product_id, user_id))
        return cursor.lastrowid


def remove_product_favorite(product_id: str, user_id: int) -> int:
    """移除产品收藏"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM product_favorites
            WHERE product_id = ? AND user_id = ?
        ''', (product_id, user_id))
        return cursor.rowcount


# ========== 通知相关函数 ==========

def add_notification(user_id: int, notification_type: str, title: str, message: str = None, priority: str = 'medium', data: str = None) -> int:
    """添加通知"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, notification_type, title, message, priority, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, notification_type, title, message, priority, data))
        return cursor.lastrowid


def get_user_notifications(user_id: int, unread_only: bool = False, limit: int = 20):
    """获取用户通知"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if unread_only:
            cursor.execute('''
                SELECT * FROM notifications
                WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM notifications
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        return cursor.fetchall()


def mark_notification_read(notification_id: int) -> int:
    """标记通知为已读"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE notifications
            SET is_read = 1
            WHERE id = ?
        ''', (notification_id,))
        return cursor.rowcount


def get_unread_notification_count(user_id: int) -> int:
    """获取未读通知数"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM notifications
            WHERE user_id = ? AND is_read = 0
        ''', (user_id,))
        result = cursor.fetchone()
        return result['count']


# ========== 产品召回相关函数 ==========

def create_recall(manufacturer_id: int, reason: str, severity: str = 'medium', product_id: str = None, batch_number: str = None) -> int:
    """创建产品召回"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO product_recalls (manufacturer_id, product_id, batch_number, reason, severity)
            VALUES (?, ?, ?, ?, ?)
        ''', (manufacturer_id, product_id, batch_number, reason, severity))
        return cursor.lastrowid


def get_active_recalls(manufacturer_id: int = None):
    """获取活跃的召回记录"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if manufacturer_id:
            cursor.execute('''
                SELECT * FROM product_recalls
                WHERE status = 'active' AND manufacturer_id = ?
                ORDER BY created_at DESC
            ''', (manufacturer_id,))
        else:
            cursor.execute('''
                SELECT * FROM product_recalls
                WHERE status = 'active'
                ORDER BY created_at DESC
            ''')
        return cursor.fetchall()


def update_recall_status(recall_id: int, status: str) -> int:
    """更新召回状态"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE product_recalls
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, recall_id))
        return cursor.rowcount


# ========== 碳足迹相关函数 ==========

def add_carbon_footprint(product_id: str, event_type: str, co2_kg: float, user_id: int = None, notes: str = None):
    """记录产品碳足迹"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO carbon_footprint (product_id, event_type, user_id, co2_kg, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, event_type, user_id, co2_kg, notes))
        return cursor.lastrowid


def get_product_carbon_footprint(product_id: str):
    """获取产品总碳足迹"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(co2_kg) as total_co2, COUNT(*) as events_count
            FROM carbon_footprint
            WHERE product_id = ?
        ''', (product_id,))
        result = cursor.fetchone()
        return {
            'total_co2': result['total_co2'] or 0,
            'events_count': result['events_count']
        }
