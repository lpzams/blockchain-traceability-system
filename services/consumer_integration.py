"""消费者与其他角色的数据集成服务"""

from models.database import (
    get_all_products, get_product_by_id, get_product_events,
    get_products_by_manufacturer, get_products_by_owner
)
from models.traceability import verify_product
import json


class ConsumerIntegrationService:
    """消费者集成服务 - 处理消费者与其他角色的数据交互"""

    @staticmethod
    def get_product_full_timeline(product_id):
        """获取产品完整时间线（包含所有角色的事件）"""
        product = get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        events = get_product_events(product_id)

        timeline = {
            'product': {
                'id': product['product_id'],
                'name': product['name'],
                'batch_number': product['batch_number'],
                'manufacturer': product['manufacturer_name'],
                'current_owner': product['owner_name'],
                'current_owner_company': product['owner_company']
            },
            'timeline': []
        }

        for event in events:
            timeline_item = {
                'type': event['event_type'],
                'timestamp': event['created_at'],
                'location': event['location'],
                'from_user': event['from_username'],
                'from_company': event['from_company'],
                'to_user': event['to_username'],
                'to_company': event['to_company']
            }
            timeline['timeline'].append(timeline_item)

        return timeline

    @staticmethod
    def get_manufacturer_products(manufacturer_id):
        """获取特定制造商的所有产品（消费者视图）"""
        products = get_products_by_manufacturer(manufacturer_id)

        result = []
        for product in products:
            result.append({
                'id': product['product_id'],
                'name': product['name'],
                'batch_number': product['batch_number'],
                'manufacturer': product['manufacturer_name'],
                'production_date': product['production_date']
            })

        return result

    @staticmethod
    def get_product_with_verification(product_id):
        """获取带有验证状态的产品信息"""
        product = get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        is_authentic, verification_msg = verify_product(product_id)

        return {
            'product': {
                'id': product['product_id'],
                'name': product['name'],
                'batch_number': product['batch_number'],
                'manufacturer': product['manufacturer_name'],
                'production_date': product['production_date']
            },
            'verification': {
                'is_authentic': is_authentic,
                'message': verification_msg
            }
        }

    @staticmethod
    def search_products_with_filters(keyword, filters=None):
        """带过滤的产品搜索（消费者使用）"""
        all_products = get_all_products()
        results = []

        filters = filters or {}
        search_type = filters.get('search_type', 'name')
        manufacturer = filters.get('manufacturer', None)

        for product in all_products:
            if search_type == 'name':
                if keyword.lower() not in product['name'].lower():
                    continue
            elif search_type == 'batch':
                if keyword not in product['batch_number']:
                    continue

            if manufacturer and product['manufacturer_name'] != manufacturer:
                continue

            results.append({
                'id': product['product_id'],
                'name': product['name'],
                'batch_number': product['batch_number'],
                'manufacturer': product['manufacturer_name'],
                'production_date': product['production_date']
            })

        return results
