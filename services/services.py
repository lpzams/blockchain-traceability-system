"""
业务服务层 - 处理核心业务逻辑
集成消息队列实现异步处理、缓存和解耦
"""

import json
import time
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps
from services.message_queue import MessageQueueFactory, TaskScheduler, EventDrivenSystem

logger = logging.getLogger(__name__)


# ===== 装饰器：缓存管理 =====
class CacheManager:
    """缓存管理器"""

    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl

    def set(self, key: str, value, ttl=None):
        """设置缓存"""
        self.cache[key] = {
            'value': value,
            'expire_at': time.time() + (ttl or self.ttl)
        }

    def get(self, key: str):
        """获取缓存"""
        if key not in self.cache:
            return None

        item = self.cache[key]
        if time.time() > item['expire_at']:
            del self.cache[key]
            return None

        return item['value']

    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """清空缓存"""
        self.cache.clear()


cache_manager = CacheManager(ttl=300)


def cached(ttl=300):
    """缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()

            # 尝试从缓存获取
            result = cache_manager.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return result

            # 执行函数
            result = func(*args, **kwargs)

            # 存储到缓存
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache set: {func.__name__}")

            return result

        return wrapper
    return decorator


# ===== 产品服务 =====
class ProductService:
    """产品服务 - 处理产品相关业务逻辑"""

    def __init__(self, mq=None):
        self.mq = mq or MessageQueueFactory.get_instance()
        self.scheduler = TaskScheduler(self.mq)
        self.events = EventDrivenSystem(self.mq)

        # 注册事件处理器
        self.events.on('product_registered', self._on_product_registered)
        self.events.on('product_transferred', self._on_product_transferred)
        self.events.on('quality_check_completed', self._on_quality_check_completed)

    def register_product_async(self, name: str, batch_number: str, manufacturer_id: int,
                                production_date: str, callback=None) -> str:
        """异步注册产品 - 使用消息队列处理高峰"""
        task_data = {
            'name': name,
            'batch_number': batch_number,
            'manufacturer_id': manufacturer_id,
            'production_date': production_date,
            'callback': callback
        }

        task_id = self.scheduler.submit_task(
            queue_name='product_registration',
            task_type='register_product',
            data=task_data
        )

        logger.info(f"Product registration task submitted: {task_id}")
        return task_id

    def transfer_ownership_async(self, product_id: str, from_user_id: int,
                                  to_user_id: int, location: str = None) -> str:
        """异步转移所有权 - 解耦转移逻辑"""
        task_data = {
            'product_id': product_id,
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
            'location': location
        }

        task_id = self.scheduler.submit_task(
            queue_name='product_transfer',
            task_type='transfer_ownership',
            data=task_data
        )

        logger.info(f"Product transfer task submitted: {task_id}")
        return task_id

    def quality_check_async(self, product_id: str, inspector_id: int,
                            result: str, notes: str) -> str:
        """异步质检 - 异步处理质检流程"""
        task_data = {
            'product_id': product_id,
            'inspector_id': inspector_id,
            'result': result,
            'notes': notes
        }

        task_id = self.scheduler.submit_task(
            queue_name='quality_checks',
            task_type='quality_check',
            data=task_data
        )

        logger.info(f"Quality check task submitted: {task_id}")
        return task_id

    def get_product_statistics(self, user_id: int) -> Dict:
        """获取用户产品统计"""
        cache_key = f"user_stats:{user_id}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        from models.database import get_products_by_manufacturer, get_product_events

        products = get_products_by_manufacturer(user_id)

        stats = {
            'total_products': len(products),
            'quality_checked': 0,
            'transferred': 0,
            'in_transit': 0
        }

        for product in products:
            events = get_product_events(product['product_id'])
            for event in events:
                if event['event_type'] == 'quality_check':
                    stats['quality_checked'] += 1
                elif event['event_type'] == 'transfer':
                    stats['transferred'] += 1
                elif event['event_type'] == 'logistics':
                    stats['in_transit'] += 1

        cache_manager.set(cache_key, stats, ttl=300)
        return stats

    def _on_product_registered(self, data: Dict):
        """产品注册事件处理"""
        logger.info(f"Product registered event: {data}")

    def _on_product_transferred(self, data: Dict):
        """产品转移事件处理"""
        logger.info(f"Product transferred event: {data}")

    def _on_quality_check_completed(self, data: Dict):
        """质检完成事件处理"""
        logger.info(f"Quality check completed event: {data}")


# ===== 分销服务 =====
class DistributorService:
    """分销服务 - 处理分销相关业务逻辑"""

    def __init__(self, mq=None):
        self.mq = mq or MessageQueueFactory.get_instance()
        self.scheduler = TaskScheduler(self.mq)

    def add_logistics_async(self, product_id: str, user_id: int,
                            location: str, status: str) -> str:
        """异步添加物流信息 - 高并发处理"""
        task_data = {
            'product_id': product_id,
            'user_id': user_id,
            'location': location,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }

        task_id = self.scheduler.submit_task(
            queue_name='logistics',
            task_type='add_logistics',
            data=task_data
        )

        logger.info(f"Logistics task submitted: {task_id}")
        return task_id

    @cached(ttl=600)
    def get_distribution_network(self) -> Dict:
        """获取分销网络信息（缓存）"""
        from models.database import get_all_products, get_all_events

        products = get_all_products()
        events = get_all_events()

        distributor_stats = {}
        for event in events:
            if event['event_type'] == 'transfer' and event['to_username']:
                distributor = event['to_username']
                if distributor not in distributor_stats:
                    distributor_stats[distributor] = {
                        'products_received': 0,
                        'locations': set()
                    }
                distributor_stats[distributor]['products_received'] += 1
                if event['location']:
                    distributor_stats[distributor]['locations'].add(event['location'])

        # 转换 set 为 list
        for distributor in distributor_stats:
            distributor_stats[distributor]['locations'] = list(
                distributor_stats[distributor]['locations']
            )

        return distributor_stats

    def get_distributor_analytics(self, distributor_id: int) -> Dict:
        """获取分销商分析数据"""
        cache_key = f"distributor_analytics:{distributor_id}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        from models.database import get_products_by_owner, get_product_events

        products = get_products_by_owner(distributor_id)

        analytics = {
            'total_products': len(products),
            'total_transfers': 0,
            'logistics_updates': 0,
            'average_delivery_time': 0,
            'locations_served': set()
        }

        delivery_times = []

        for product in products:
            events = get_product_events(product['product_id'])
            for event in events:
                if event['event_type'] == 'transfer':
                    analytics['total_transfers'] += 1
                elif event['event_type'] == 'logistics':
                    analytics['logistics_updates'] += 1
                    if event['location']:
                        analytics['locations_served'].add(event['location'])

        analytics['locations_served'] = list(analytics['locations_served'])

        cache_manager.set(cache_key, analytics, ttl=600)
        return analytics


# ===== 消费者服务 =====
class ConsumerService:
    """消费者服务 - 处理消费者溯源相关业务逻辑"""

    def __init__(self, mq=None):
        self.mq = mq or MessageQueueFactory.get_instance()

    @cached(ttl=600)
    def trace_product(self, product_id: str) -> Dict:
        """追溯产品 - 包含缓存"""
        from models.database import get_product_by_id, get_product_events
        from models.traceability import verify_product

        product = get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        events = get_product_events(product_id)
        is_authentic, verification_msg = verify_product(product_id)

        trace_data = {
            'product': {
                'id': product['product_id'],
                'name': product['name'],
                'batch_number': product['batch_number'],
                'manufacturer': product['manufacturer_name'],
                'manufacturer_company': product['manufacturer_company'],
                'production_date': product['production_date'],
                'current_owner': product['owner_name'],
                'current_owner_company': product['owner_company']
            },
            'is_authentic': is_authentic,
            'verification_message': verification_msg,
            'events': []
        }

        for event in events:
            event_info = {
                'type': event['event_type'],
                'timestamp': event['created_at'],
                'location': event['location']
            }

            if event['event_type'] == 'register':
                event_info['title'] = '产品注册'
                event_info['details'] = f"由 {event['to_username']} 注册"
            elif event['event_type'] == 'transfer':
                event_info['title'] = '所有权转移'
                event_info['details'] = f"从 {event['from_username']} 转移到 {event['to_username']}"
            elif event['event_type'] == 'quality_check':
                data = json.loads(event['data']) if event['data'] else {}
                event_info['title'] = '质检'
                event_info['details'] = f"质检结果: {data.get('result', 'unknown')}"
            elif event['event_type'] == 'logistics':
                data = json.loads(event['data']) if event['data'] else {}
                event_info['title'] = '物流更新'
                event_info['details'] = f"状态: {data.get('status', 'unknown')}"

            trace_data['events'].append(event_info)

        return trace_data

    def search_products(self, keyword: str, search_type: str = 'name') -> List[Dict]:
        """搜索产品"""
        from models.database import get_all_products

        products = get_all_products()
        results = []

        for product in products:
            if search_type == 'name' and keyword.lower() in product['name'].lower():
                results.append({
                    'id': product['product_id'],
                    'name': product['name'],
                    'batch_number': product['batch_number'],
                    'manufacturer': product['manufacturer_name']
                })
            elif search_type == 'batch' and keyword in product['batch_number']:
                results.append({
                    'id': product['product_id'],
                    'name': product['name'],
                    'batch_number': product['batch_number'],
                    'manufacturer': product['manufacturer_name']
                })

        return results


# ===== 监管服务 =====
class RegulatorService:
    """监管服务 - 处理监管审计相关业务逻辑"""

    def __init__(self, mq=None):
        self.mq = mq or MessageQueueFactory.get_instance()

    @cached(ttl=900)
    def get_audit_trail(self, start_date: str = None, end_date: str = None) -> Dict:
        """获取审计追踪（缓存）"""
        from models.database import get_all_events, get_all_products

        all_events = get_all_events()
        products = get_all_products()

        audit_data = {
            'total_events': len(all_events),
            'total_products': len(products),
            'events_by_type': {},
            'events_by_date': {},
            'events': []
        }

        for event in all_events:
            # 按类型统计
            event_type = event['event_type']
            if event_type not in audit_data['events_by_type']:
                audit_data['events_by_type'][event_type] = 0
            audit_data['events_by_type'][event_type] += 1

            # 按日期统计
            event_date = event['created_at'][:10] if event['created_at'] else 'unknown'
            if event_date not in audit_data['events_by_date']:
                audit_data['events_by_date'][event_date] = 0
            audit_data['events_by_date'][event_date] += 1

            # 详细事件信息
            audit_data['events'].append({
                'id': event['id'],
                'product_id': event['product_id'],
                'type': event['event_type'],
                'from_user': event['from_username'],
                'to_user': event['to_username'],
                'location': event['location'],
                'timestamp': event['created_at']
            })

        return audit_data

    def verify_blockchain_integrity(self) -> Dict:
        """验证区块链完整性"""
        from models.blockchain import blockchain

        is_valid, message = blockchain.is_chain_valid()

        return {
            'valid': is_valid,
            'message': message,
            'total_blocks': len(blockchain.chain),
            'chain_hash': blockchain.chain[-1].hash if blockchain.chain else None
        }

    def get_system_health(self) -> Dict:
        """获取系统健康状态"""
        from models.database import get_all_products

        products = get_all_products()

        # 计算系统指标
        health = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'metrics': {
                'total_products': len(products),
                'cache_size': len(cache_manager.cache),
                'mq_queue_size': self.mq.get_queue_size('product_registration') +
                                self.mq.get_queue_size('product_transfer') +
                                self.mq.get_queue_size('quality_checks')
            }
        }

        # 判断系统状态
        if health['metrics']['mq_queue_size'] > 100:
            health['status'] = 'warning'
        elif health['metrics']['mq_queue_size'] > 500:
            health['status'] = 'critical'

        return health


# ===== 导出 =====
__all__ = [
    'ProductService',
    'DistributorService',
    'ConsumerService',
    'RegulatorService',
    'cache_manager',
    'CacheManager',
    'cached'
]
