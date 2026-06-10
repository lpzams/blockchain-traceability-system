"""
数据导出和报告生成模块
"""

import json
import csv
import io
import logging
from typing import Dict, List
from datetime import datetime
from services.services import cache_manager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""

    def generate_product_report(self, product_id: str) -> Dict:
        """生成产品详细报告"""
        from models.database import get_product_by_id, get_product_events
        from models.traceability import verify_product

        product = get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        events = get_product_events(product_id)
        is_authentic, verification_msg = verify_product(product_id)

        report = {
            'report_type': 'product_detail',
            'generated_at': datetime.now().isoformat(),
            'product_info': dict(product),
            'verification': {
                'is_authentic': is_authentic,
                'message': verification_msg
            },
            'timeline': [],
            'statistics': {
                'total_events': len(events),
                'transfers': 0,
                'quality_checks': 0,
                'logistics_updates': 0
            }
        }

        # 处理事件时间线
        for event in events:
            event_detail = {
                'type': event['event_type'],
                'timestamp': event['created_at'],
                'location': event['location'],
                'from_user': event['from_username'] if 'from_username' in event.keys() else None,
                'to_user': event['to_username'] if 'to_username' in event.keys() else None
            }

            if event['event_type'] == 'transfer':
                report['statistics']['transfers'] += 1
            elif event['event_type'] == 'quality_check':
                report['statistics']['quality_checks'] += 1
            elif event['event_type'] == 'logistics':
                report['statistics']['logistics_updates'] += 1

            report['timeline'].append(event_detail)

        return report

    def generate_manufacturer_report(self, manufacturer_id: int) -> Dict:
        """生成生产商报告"""
        from models.database import get_products_by_manufacturer, get_user_by_id

        manufacturer = get_user_by_id(manufacturer_id)
        products = get_products_by_manufacturer(manufacturer_id)

        report = {
            'report_type': 'manufacturer_summary',
            'generated_at': datetime.now().isoformat(),
            'manufacturer': dict(manufacturer),
            'summary': {
                'total_products': len(products),
                'products_with_quality_check': 0,
                'transferred_products': 0
            },
            'products': []
        }

        for product in products:
            from models.database import get_product_events
            events = get_product_events(product['product_id'])

            has_quality = any(e['event_type'] == 'quality_check' for e in events)
            has_transfer = any(e['event_type'] == 'transfer' for e in events)

            if has_quality:
                report['summary']['products_with_quality_check'] += 1
            if has_transfer:
                report['summary']['transferred_products'] += 1

            report['products'].append({
                'product_id': product['product_id'],
                'name': product['name'],
                'batch_number': product['batch_number'],
                'created_at': product['created_at']
            })

        return report

    def generate_compliance_report(self) -> Dict:
        """生成合规报告"""
        from models.database import get_all_products, get_all_events
        from models.blockchain import blockchain

        products = get_all_products()
        events = get_all_events()
        is_valid, chain_message = blockchain.is_chain_valid()

        report = {
            'report_type': 'compliance',
            'generated_at': datetime.now().isoformat(),
            'blockchain_status': {
                'valid': is_valid,
                'message': chain_message,
                'total_blocks': len(blockchain.chain)
            },
            'statistics': {
                'total_products': len(products),
                'total_events': len(events),
                'products_without_quality_check': 0,
                'products_with_issues': []
            }
        }

        # 检查合规性
        for product in products:
            from models.database import get_product_events
            product_events = get_product_events(product['product_id'])

            has_quality = any(e['event_type'] == 'quality_check' for e in product_events)

            if not has_quality:
                report['statistics']['products_without_quality_check'] += 1
                report['statistics']['products_with_issues'].append({
                    'product_id': product['product_id'],
                    'name': product['name'],
                    'issue': 'No quality check'
                })

        return report

    def export_to_csv(self, data: List[Dict], filename: str = None) -> str:
        """导出数据为CSV"""
        if not data:
            return ""

        output = io.StringIO()
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        csv_content = output.getvalue()
        output.close()

        if filename:
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_content)

        return csv_content

    def export_to_json(self, data, filename: str = None) -> str:
        """导出数据为JSON"""
        json_content = json.dumps(data, ensure_ascii=False, indent=2)

        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_content)

        return json_content


class DataExporter:
    """数据导出器"""

    def export_all_products(self, format: str = 'csv') -> str:
        """导出所有产品"""
        from models.database import get_all_products

        products = get_all_products()
        products_list = [dict(p) for p in products]

        report_gen = ReportGenerator()

        if format == 'csv':
            return report_gen.export_to_csv(products_list)
        elif format == 'json':
            return report_gen.export_to_json(products_list)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_events(self, product_id: str = None, format: str = 'csv') -> str:
        """导出事件"""
        from models.database import get_all_events, get_product_events

        if product_id:
            events = get_product_events(product_id)
        else:
            events = get_all_events()

        events_list = [dict(e) for e in events]

        report_gen = ReportGenerator()

        if format == 'csv':
            return report_gen.export_to_csv(events_list)
        elif format == 'json':
            return report_gen.export_to_json(events_list)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_supply_chain(self, format: str = 'json') -> str:
        """导出供应链数据"""
        from services.analytics import AdvancedAnalytics

        analytics = AdvancedAnalytics()
        graph = analytics.get_supply_chain_graph()

        report_gen = ReportGenerator()
        return report_gen.export_to_json(graph)


# 导出
__all__ = ['ReportGenerator', 'DataExporter']
