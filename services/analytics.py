"""
高级数据分析模块 - 提供深度数据挖掘和可视化支持
"""

import json
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from services.services import cache_manager, cached

logger = logging.getLogger(__name__)


class AdvancedAnalytics:
    """高级分析服务"""

    def __init__(self):
        pass

    @cached(ttl=600)
    def get_supply_chain_graph(self) -> Dict:
        """获取供应链图谱"""
        from models.database import get_all_events, get_all_products

        events = get_all_events()
        products = get_all_products()

        # 构建节点和边
        nodes = {}
        edges = []

        for event in events:
            if event['event_type'] == 'transfer':
                from_user = event['from_username']
                to_user = event['to_username']

                if from_user and from_user not in nodes:
                    nodes[from_user] = {
                        'id': from_user,
                        'type': 'user',
                        'transfers_out': 0,
                        'transfers_in': 0
                    }

                if to_user and to_user not in nodes:
                    nodes[to_user] = {
                        'id': to_user,
                        'type': 'user',
                        'transfers_out': 0,
                        'transfers_in': 0
                    }

                if from_user and to_user:
                    nodes[from_user]['transfers_out'] += 1
                    nodes[to_user]['transfers_in'] += 1

                    edges.append({
                        'from': from_user,
                        'to': to_user,
                        'product_id': event['product_id'],
                        'timestamp': event['created_at']
                    })

        return {
            'nodes': list(nodes.values()),
            'edges': edges,
            'total_nodes': len(nodes),
            'total_edges': len(edges)
        }

    @cached(ttl=600)
    def get_product_flow_analysis(self) -> Dict:
        """产品流转分析"""
        from models.database import get_all_events

        events = get_all_events()

        flow_data = {
            'by_hour': defaultdict(int),
            'by_day': defaultdict(int),
            'by_type': defaultdict(int),
            'average_transfer_time': 0,
            'hottest_routes': []
        }

        routes = Counter()
        transfer_times = []

        for event in events:
            # 按类型统计
            flow_data['by_type'][event['event_type']] += 1

            # 按时间统计
            if event['created_at']:
                dt = datetime.fromisoformat(event['created_at'])
                hour_key = dt.strftime('%Y-%m-%d %H:00')
                day_key = dt.strftime('%Y-%m-%d')
                flow_data['by_hour'][hour_key] += 1
                flow_data['by_day'][day_key] += 1

            # 统计热门路线
            if event['event_type'] == 'transfer':
                from_user = event['from_username'] if 'from_username' in event.keys() else 'unknown'
                to_user = event['to_username'] if 'to_username' in event.keys() else 'unknown'
                route = f"{from_user} → {to_user}"
                routes[route] += 1

        # 最热门的10条路线
        flow_data['hottest_routes'] = [
            {'route': route, 'count': count}
            for route, count in routes.most_common(10)
        ]

        # 转换为列表
        flow_data['by_hour'] = dict(flow_data['by_hour'])
        flow_data['by_day'] = dict(flow_data['by_day'])
        flow_data['by_type'] = dict(flow_data['by_type'])

        return flow_data

    @cached(ttl=600)
    def get_quality_analysis(self) -> Dict:
        """质量分析"""
        from models.database import get_all_events

        events = get_all_events()

        quality_data = {
            'total_checks': 0,
            'passed': 0,
            'failed': 0,
            'pass_rate': 0.0,
            'by_product': defaultdict(list),
            'by_inspector': defaultdict(int),
            'trend': []
        }

        for event in events:
            if event['event_type'] == 'quality_check':
                quality_data['total_checks'] += 1

                # 解析数据
                try:
                    data = json.loads(event['data']) if event['data'] else {}
                    result = data.get('result', 'unknown')

                    if result in ['pass', 'passed', '合格']:
                        quality_data['passed'] += 1
                    elif result in ['fail', 'failed', '不合格']:
                        quality_data['failed'] += 1

                    # 按产品统计
                    quality_data['by_product'][event['product_id']].append({
                        'result': result,
                        'timestamp': event['created_at']
                    })

                    # 按检验员统计
                    inspector = event['from_username'] if 'from_username' in event.keys() else 'unknown'
                    quality_data['by_inspector'][inspector] += 1

                except json.JSONDecodeError:
                    pass

        # 计算合格率
        if quality_data['total_checks'] > 0:
            quality_data['pass_rate'] = (quality_data['passed'] / quality_data['total_checks']) * 100

        # 转换为可序列化格式
        quality_data['by_product'] = dict(quality_data['by_product'])
        quality_data['by_inspector'] = dict(quality_data['by_inspector'])

        return quality_data

    @cached(ttl=600)
    def get_logistics_heatmap(self) -> Dict:
        """物流热力图数据"""
        from models.database import get_all_events

        events = get_all_events()

        heatmap_data = {
            'locations': defaultdict(int),
            'routes': [],
            'busy_times': defaultdict(int)
        }

        for event in events:
            if event['event_type'] == 'logistics' and event['location']:
                location = event['location']
                heatmap_data['locations'][location] += 1

                # 按时间段统计
                if event['created_at']:
                    dt = datetime.fromisoformat(event['created_at'])
                    hour = dt.hour
                    time_slot = f"{hour:02d}:00-{(hour+1):02d}:00"
                    heatmap_data['busy_times'][time_slot] += 1

        # 转换为列表格式
        location_list = [
            {'location': loc, 'count': count}
            for loc, count in sorted(heatmap_data['locations'].items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            'locations': location_list[:20],  # 前20个最忙的地点
            'busy_times': dict(heatmap_data['busy_times'])
        }

    @cached(ttl=900)
    def get_predictive_insights(self) -> Dict:
        """预测性洞察"""
        from models.database import get_all_events, get_all_products

        events = get_all_events()
        products = get_all_products()

        insights = {
            'predicted_bottlenecks': [],
            'risk_products': [],
            'recommended_actions': []
        }

        # 检测瓶颈
        location_times = defaultdict(list)
        for event in events:
            if event['event_type'] == 'logistics' and event['location']:
                location_times[event['location']].append(event['created_at'])

        # 找出停留时间过长的地点
        for location, times in location_times.items():
            if len(times) > 5:
                insights['predicted_bottlenecks'].append({
                    'location': location,
                    'event_count': len(times),
                    'severity': 'high' if len(times) > 10 else 'medium'
                })

        # 检测风险产品（质检失败或无质检记录）
        product_quality = defaultdict(list)
        for event in events:
            if event['event_type'] == 'quality_check':
                try:
                    data = json.loads(event['data']) if event['data'] else {}
                    result = data.get('result', 'unknown')
                    product_quality[event['product_id']].append(result)
                except json.JSONDecodeError:
                    pass

        for product in products:
            product_id = product['product_id']
            if product_id not in product_quality:
                insights['risk_products'].append({
                    'product_id': product_id,
                    'name': product['name'],
                    'risk_type': 'no_quality_check',
                    'severity': 'medium'
                })
            elif any(r in ['fail', 'failed', '不合格'] for r in product_quality[product_id]):
                insights['risk_products'].append({
                    'product_id': product_id,
                    'name': product['name'],
                    'risk_type': 'quality_failed',
                    'severity': 'high'
                })

        # 推荐行动
        if insights['predicted_bottlenecks']:
            insights['recommended_actions'].append({
                'type': 'logistics_optimization',
                'description': f"优化 {insights['predicted_bottlenecks'][0]['location']} 的物流流程",
                'priority': 'high'
            })

        if len(insights['risk_products']) > 5:
            insights['recommended_actions'].append({
                'type': 'quality_inspection',
                'description': '增加质检频率，发现多个高风险产品',
                'priority': 'high'
            })

        return insights

    def get_realtime_metrics(self) -> Dict:
        """实时指标（不缓存）"""
        from models.database import get_all_events
        from models.blockchain import blockchain

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        events = get_all_events()

        recent_events = []
        for event in events:
            if event['created_at']:
                try:
                    event_time = datetime.fromisoformat(event['created_at'])
                    if event_time >= one_hour_ago:
                        recent_events.append(event)
                except ValueError:
                    pass

        return {
            'events_last_hour': len(recent_events),
            'blockchain_height': len(blockchain.chain),
            'timestamp': now.isoformat(),
            'system_load': 'normal'  # 可以扩展为实际的系统负载检测
        }


# 导出
__all__ = ['AdvancedAnalytics']
