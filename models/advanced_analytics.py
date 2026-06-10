"""
高级功能模块：产品溯源分析和预测
包括：
- 产品风险评估
- 供应链网络分析
- 碳足迹计算与可视化
- 质量追溯热力图
- 智能推荐系统
"""
from models.database import get_db_connection, get_all_products, get_all_events
from datetime import datetime, timedelta
import json


class ProductTraceAnalytics:
    """产品溯源高级分析引擎"""

    @staticmethod
    def get_risk_assessment(product_id=None):
        """产品风险评估 - 基于供应链复杂度和交易历史"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if product_id:
                cursor.execute('''
                    SELECT p.*, COUNT(e.id) as event_count
                    FROM products p
                    LEFT JOIN events e ON p.product_id = e.product_id
                    WHERE p.product_id = ?
                    GROUP BY p.product_id
                ''', (product_id,))
                products = [cursor.fetchone()]
            else:
                cursor.execute('''
                    SELECT p.*, COUNT(e.id) as event_count
                    FROM products p
                    LEFT JOIN events e ON p.product_id = e.product_id
                    GROUP BY p.product_id
                ''')
                products = cursor.fetchall()

            assessments = []
            for product in products:
                if not product:
                    continue

                # 计算风险分数 (0-100)
                event_count = product.get('event_count', 0) if isinstance(product, dict) else product['event_count']

                # 因素：交易复杂度、时间跨度等
                complexity_score = min(100, event_count * 10)  # 交易越多风险越高

                # 时间因素：产品在系统中存在时间越长越可信
                created_at = product.get('created_at') if isinstance(product, dict) else product['created_at']
                age_days = (datetime.now() - datetime.strptime(str(created_at), '%Y-%m-%d %H:%M:%S')).days
                time_score = max(0, 100 - (age_days * 2))  # 新产品风险更高

                # 综合风险评分
                risk_score = (complexity_score * 0.6 + time_score * 0.4)

                # 风险等级
                if risk_score < 30:
                    risk_level = '低风险'
                    risk_color = 'success'
                elif risk_score < 60:
                    risk_level = '中风险'
                    risk_color = 'warning'
                else:
                    risk_level = '高风险'
                    risk_color = 'danger'

                assessments.append({
                    'product_id': product.get('product_id') if isinstance(product, dict) else product['product_id'],
                    'product_name': product.get('name') if isinstance(product, dict) else product['name'],
                    'risk_score': round(risk_score, 2),
                    'risk_level': risk_level,
                    'risk_color': risk_color,
                    'event_count': event_count,
                    'age_days': age_days
                })

            return assessments

    @staticmethod
    def get_supply_chain_network():
        """供应链网络分析 - 节点和边的关系图"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 获取所有参与方
            cursor.execute('''
                SELECT DISTINCT user_id, username, role, company_name
                FROM (
                    SELECT from_user_id as user_id FROM events WHERE from_user_id IS NOT NULL
                    UNION
                    SELECT to_user_id as user_id FROM events WHERE to_user_id IS NOT NULL
                    UNION
                    SELECT manufacturer_id as user_id FROM products
                    UNION
                    SELECT current_owner_id as user_id FROM products
                ) as users
                JOIN users u ON u.id = user_id
                ORDER BY user_id
            ''')

            nodes = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                nodes.append({
                    'id': row_dict.get('user_id'),
                    'label': row_dict.get('username', '未知'),
                    'role': row_dict.get('role', 'unknown'),
                    'company': row_dict.get('company_name', ''),
                    'size': 30
                })

            # 获取所有交互关系（边）
            cursor.execute('''
                SELECT from_user_id, to_user_id, COUNT(*) as count
                FROM events
                WHERE from_user_id IS NOT NULL AND to_user_id IS NOT NULL
                GROUP BY from_user_id, to_user_id
            ''')

            edges = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                edges.append({
                    'source': row_dict.get('from_user_id'),
                    'target': row_dict.get('to_user_id'),
                    'weight': row_dict.get('count', 1)
                })

            return {
                'nodes': nodes,
                'edges': edges,
                'node_count': len(nodes),
                'edge_count': len(edges)
            }

    @staticmethod
    def get_carbon_footprint_analysis():
        """碳足迹分析与可视化"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 获取所有碳足迹数据
            cursor.execute('''
                SELECT product_id, event_type, SUM(co2_kg) as total_co2, COUNT(*) as event_count
                FROM carbon_footprint
                GROUP BY product_id, event_type
                ORDER BY total_co2 DESC
            ''')

            carbon_data = []
            total_carbon = 0

            for row in cursor.fetchall():
                row_dict = dict(row)
                total_carbon += row_dict.get('total_co2', 0)
                carbon_data.append({
                    'product_id': row_dict.get('product_id'),
                    'event_type': row_dict.get('event_type'),
                    'co2_kg': round(row_dict.get('total_co2', 0), 2),
                    'event_count': row_dict.get('event_count', 0)
                })

            # 按事件类型统计
            cursor.execute('''
                SELECT event_type, SUM(co2_kg) as total_co2
                FROM carbon_footprint
                GROUP BY event_type
            ''')

            by_event_type = {}
            for row in cursor.fetchall():
                row_dict = dict(row)
                by_event_type[row_dict.get('event_type')] = round(row_dict.get('total_co2', 0), 2)

            return {
                'total_carbon': round(total_carbon, 2),
                'by_product': carbon_data[:10],  # 排放最多的10个产品
                'by_event_type': by_event_type,
                'carbon_trend': ProductTraceAnalytics._calculate_carbon_trend()
            }

    @staticmethod
    def _calculate_carbon_trend():
        """计算碳排放趋势"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 获取过去7天的碳排放趋势
            cursor.execute('''
                SELECT DATE(created_at) as date, SUM(co2_kg) as daily_co2
                FROM carbon_footprint
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date ASC
            ''')

            trend = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                trend.append({
                    'date': row_dict.get('date'),
                    'co2': round(row_dict.get('daily_co2', 0), 2)
                })

            return trend

    @staticmethod
    def get_quality_heatmap():
        """质量追溯热力图 - 产品质检分布"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 获取质检事件
            cursor.execute('''
                SELECT p.product_id, p.name, COUNT(e.id) as check_count,
                       SUM(CASE WHEN e.data LIKE '%合格%' THEN 1 ELSE 0 END) as pass_count
                FROM products p
                LEFT JOIN events e ON p.product_id = e.product_id
                WHERE e.event_type = 'quality_check'
                GROUP BY p.product_id
            ''')

            heatmap_data = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                check_count = row_dict.get('check_count', 0)
                pass_count = row_dict.get('pass_count', 0)

                if check_count > 0:
                    pass_rate = (pass_count / check_count) * 100
                else:
                    pass_rate = 0

                heatmap_data.append({
                    'product_id': row_dict.get('product_id'),
                    'product_name': row_dict.get('name'),
                    'check_count': check_count,
                    'pass_count': pass_count,
                    'pass_rate': round(pass_rate, 2),
                    'intensity': max(0, min(100, pass_rate))  # 0-100用于热力图强度
                })

            return sorted(heatmap_data, key=lambda x: x['check_count'], reverse=True)

    @staticmethod
    def get_intelligent_recommendations():
        """智能推荐系统 - 基于历史数据推荐下一步操作"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            recommendations = []

            # 推荐1：存在风险的产品需要额外质检
            cursor.execute('''
                SELECT p.product_id, p.name, COUNT(e.id) as event_count
                FROM products p
                LEFT JOIN events e ON p.product_id = e.product_id
                WHERE e.event_type = 'quality_check' IS NULL
                GROUP BY p.product_id
                HAVING COUNT(e.id) > 5
            ''')

            for row in cursor.fetchall():
                row_dict = dict(row)
                recommendations.append({
                    'type': '质量风险预警',
                    'product_id': row_dict.get('product_id'),
                    'product_name': row_dict.get('name'),
                    'priority': 'high',
                    'message': f'产品 {row_dict.get("name")} 经历多次转移，建议进行额外质检'
                })

            # 推荐2：长期未更新的产品
            cursor.execute('''
                SELECT p.product_id, p.name, MAX(e.created_at) as last_event
                FROM products p
                LEFT JOIN events e ON p.product_id = e.product_id
                GROUP BY p.product_id
                HAVING (julianday('now') - julianday(MAX(e.created_at))) > 7
            ''')

            for row in cursor.fetchall():
                row_dict = dict(row)
                recommendations.append({
                    'type': '物流进度提醒',
                    'product_id': row_dict.get('product_id'),
                    'product_name': row_dict.get('name'),
                    'priority': 'medium',
                    'message': f'产品 {row_dict.get("name")} 已7天未更新，请确认物流进度'
                })

            return recommendations


class PredictionEngine:
    """预测引擎 - 基于历史数据的预测"""

    @staticmethod
    def predict_delivery_time(product_id):
        """预测产品交付时间"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT e.event_type, COUNT(*) as count,
                       AVG(julianday(e.created_at)) as avg_time
                FROM events e
                WHERE e.product_id = ?
                GROUP BY e.event_type
                ORDER BY e.created_at DESC
                LIMIT 1
            ''', (product_id,))

            last_event = cursor.fetchone()

            if not last_event:
                return {
                    'estimated_days': '未知',
                    'confidence': 0,
                    'status': '数据不足'
                }

            # 基于最后一个事件类型预测
            if last_event['event_type'] == 'transfer':
                estimated_days = 2
                confidence = 75
            elif last_event['event_type'] == 'logistics':
                estimated_days = 3
                confidence = 80
            else:
                estimated_days = 5
                confidence = 60

            return {
                'estimated_days': estimated_days,
                'confidence': confidence,
                'status': '预测中'
            }

    @staticmethod
    def predict_quality_issues():
        """预测可能的质量问题"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 分析历史质检失败率
            cursor.execute('''
                SELECT p.manufacturer_id,
                       COUNT(CASE WHEN e.data LIKE '%不合格%' THEN 1 END) as fail_count,
                       COUNT(*) as total_count
                FROM products p
                LEFT JOIN events e ON p.product_id = e.product_id
                WHERE e.event_type = 'quality_check'
                GROUP BY p.manufacturer_id
                HAVING COUNT(*) > 0
            ''')

            predictions = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                total = row_dict.get('total_count', 1)
                fail = row_dict.get('fail_count', 0)
                fail_rate = (fail / total) * 100 if total > 0 else 0

                if fail_rate > 20:
                    predictions.append({
                        'manufacturer_id': row_dict.get('manufacturer_id'),
                        'fail_rate': round(fail_rate, 2),
                        'risk_level': '高风险' if fail_rate > 40 else '中风险',
                        'recommendation': '建议加强质检或改进生产流程'
                    })

            return predictions
