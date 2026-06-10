"""
产品溯源区块链浏览器
将产品和交易信息映射到区块链结构
"""
from models.database import get_db_connection, get_all_products, get_all_events


def get_blockchain_explorer_data():
    """获取区块链浏览器数据 - 基于实际产品和事件"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 获取所有产品
        products = get_all_products()

        # 获取所有事件
        events = get_all_events()

        # 构建区块数据：每个产品作为一个"区块"
        blocks = []
        for idx, product in enumerate(products):
            # 获取该产品的所有事件
            product_events = [e for e in events if e['product_id'] == product['product_id']]

            block = {
                'height': idx,
                'hash': product['block_hash'],
                'prev_hash': products[idx-1]['block_hash'] if idx > 0 else '0' * 64,
                'product_id': product['product_id'],
                'product_name': product['name'],
                'batch_number': product['batch_number'],
                'manufacturer': product['manufacturer_name'],
                'current_owner': product['owner_name'],
                'created_at': product['created_at'],
                'tx_count': len(product_events),
                'transactions': product_events
            }
            blocks.append(block)

        # 获取统计信息
        cursor.execute('SELECT COUNT(*) as count FROM events')
        total_events = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM products')
        total_products = cursor.fetchone()['count']

        return {
            'blocks': blocks,
            'total_blocks': len(blocks),
            'total_events': total_events,
            'total_products': total_products,
            'latest_block': blocks[-1] if blocks else None
        }


def get_product_trace_chain(product_id):
    """获取单个产品的完整溯源链"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 获取产品信息
        cursor.execute('''
            SELECT p.*,
                   m.username as manufacturer_name, m.company_name as manufacturer_company,
                   o.username as owner_name, o.company_name as owner_company
            FROM products p
            LEFT JOIN users m ON p.manufacturer_id = m.id
            LEFT JOIN users o ON p.current_owner_id = o.id
            WHERE p.product_id = ?
        ''', (product_id,))
        product = cursor.fetchone()

        if not product:
            return None

        # 获取产品的所有事件（按时间顺序）
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
        events = cursor.fetchall()

        # 获取产品评价
        cursor.execute('''
            SELECT r.*, u.username
            FROM product_ratings r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC
        ''', (product_id,))
        ratings = cursor.fetchall()

        return {
            'product': dict(product),
            'events': [dict(e) for e in events],
            'ratings': [dict(r) for r in ratings]
        }
