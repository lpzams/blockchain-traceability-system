"""
智能报警系统 - 监控异常并自动发送警报
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta
from services.message_queue import MessageQueueFactory
from services.notifications import NotificationManager, NotificationType, NotificationPriority

logger = logging.getLogger(__name__)


class AlertRule:
    """报警规则"""
    def __init__(self, name: str, condition_func, severity: str, message: str):
        self.name = name
        self.condition_func = condition_func
        self.severity = severity
        self.message = message
        self.last_triggered = None


class AlertSystem:
    """智能报警系统"""

    def __init__(self, notification_manager=None):
        self.notification_manager = notification_manager
        self.rules = []
        self.alert_history = []
        self._register_default_rules()

    def _register_default_rules(self):
        """注册默认报警规则"""
        # 规则1：产品质检失败率过高
        self.add_rule(
            name='high_failure_rate',
            condition_func=self._check_quality_failure_rate,
            severity='high',
            message='质检失败率超过阈值，需要立即检查'
        )

        # 规则2：物流停滞
        self.add_rule(
            name='logistics_stagnation',
            condition_func=self._check_logistics_stagnation,
            severity='medium',
            message='检测到物流停滞，产品长时间未更新位置'
        )

        # 规则3：区块链异常
        self.add_rule(
            name='blockchain_integrity',
            condition_func=self._check_blockchain_integrity,
            severity='critical',
            message='区块链完整性校验失败'
        )

        # 规则4：无质检产品过多
        self.add_rule(
            name='missing_quality_checks',
            condition_func=self._check_missing_quality_checks,
            severity='medium',
            message='发现大量产品未进行质检'
        )

        # 规则5：异常转移行为
        self.add_rule(
            name='abnormal_transfers',
            condition_func=self._check_abnormal_transfers,
            severity='high',
            message='检测到异常的产品转移行为'
        )

    def add_rule(self, name: str, condition_func, severity: str, message: str):
        """添加报警规则"""
        rule = AlertRule(name, condition_func, severity, message)
        self.rules.append(rule)
        logger.info(f"Alert rule added: {name}")

    def check_all_rules(self) -> List[Dict]:
        """检查所有规则"""
        triggered_alerts = []

        for rule in self.rules:
            try:
                is_triggered, details = rule.condition_func()
                if is_triggered:
                    alert = {
                        'rule_name': rule.name,
                        'severity': rule.severity,
                        'message': rule.message,
                        'details': details,
                        'timestamp': datetime.now().isoformat()
                    }
                    triggered_alerts.append(alert)
                    self.alert_history.append(alert)
                    rule.last_triggered = datetime.now()

                    # 发送通知
                    if self.notification_manager:
                        self._send_alert_notification(alert)

                    logger.warning(f"Alert triggered: {rule.name}")
            except Exception as e:
                logger.error(f"Error checking rule {rule.name}: {str(e)}")

        return triggered_alerts

    def _check_quality_failure_rate(self) -> tuple:
        """检查质检失败率"""
        from models.database import get_all_events

        events = get_all_events()
        quality_checks = [e for e in events if e['event_type'] == 'quality_check']

        if len(quality_checks) < 10:
            return False, {}

        import json
        failed_count = 0
        for event in quality_checks[-50:]:  # 检查最近50次质检
            try:
                data = json.loads(event['data']) if event['data'] else {}
                result = data.get('result', '')
                if result in ['fail', 'failed', '不合格']:
                    failed_count += 1
            except:
                pass

        failure_rate = (failed_count / min(len(quality_checks), 50)) * 100

        if failure_rate > 30:
            return True, {
                'failure_rate': f"{failure_rate:.2f}%",
                'failed_count': failed_count,
                'total_checks': min(len(quality_checks), 50)
            }

        return False, {}

    def _check_logistics_stagnation(self) -> tuple:
        """检查物流停滞"""
        from models.database import get_all_products, get_product_events

        products = get_all_products()
        stagnant_products = []

        now = datetime.now()
        threshold = timedelta(days=7)  # 7天未更新视为停滞

        for product in products:
            events = get_product_events(product['product_id'])
            logistics_events = [e for e in events if e['event_type'] == 'logistics']

            if logistics_events:
                last_event = logistics_events[-1]
                try:
                    last_update = datetime.fromisoformat(last_event['created_at'])
                    if now - last_update > threshold:
                        stagnant_products.append({
                            'product_id': product['product_id'],
                            'name': product['name'],
                            'days_stagnant': (now - last_update).days
                        })
                except:
                    pass

        if len(stagnant_products) > 5:
            return True, {
                'stagnant_count': len(stagnant_products),
                'products': stagnant_products[:5]
            }

        return False, {}

    def _check_blockchain_integrity(self) -> tuple:
        """检查区块链完整性"""
        from models.blockchain import blockchain

        is_valid, message = blockchain.is_chain_valid()

        if not is_valid:
            return True, {
                'validation_message': message,
                'chain_length': len(blockchain.chain)
            }

        return False, {}

    def _check_missing_quality_checks(self) -> tuple:
        """检查缺失质检的产品"""
        from models.database import get_all_products, get_product_events

        products = get_all_products()
        missing_quality = []

        for product in products:
            events = get_product_events(product['product_id'])
            has_quality_check = any(e['event_type'] == 'quality_check' for e in events)

            if not has_quality_check:
                missing_quality.append({
                    'product_id': product['product_id'],
                    'name': product['name'],
                    'manufacturer': product['manufacturer_name'] if 'manufacturer_name' in product.keys() else 'unknown'
                })

        missing_rate = (len(missing_quality) / len(products) * 100) if products else 0

        if missing_rate > 20:
            return True, {
                'missing_count': len(missing_quality),
                'total_products': len(products),
                'missing_rate': f"{missing_rate:.2f}%",
                'samples': missing_quality[:5]
            }

        return False, {}

    def _check_abnormal_transfers(self) -> tuple:
        """检查异常转移"""
        from models.database import get_all_events

        events = get_all_events()
        transfers = [e for e in events if e['event_type'] == 'transfer']

        # 统计每个用户的转移频率
        from collections import defaultdict
        user_transfers = defaultdict(list)

        for transfer in transfers[-100:]:  # 检查最近100次转移
            from_user = transfer.get('from_username')
            if from_user:
                try:
                    transfer_time = datetime.fromisoformat(transfer['created_at'])
                    user_transfers[from_user].append(transfer_time)
                except:
                    pass

        # 检测异常高频转移（1小时内超过10次）
        abnormal_users = []
        for user, times in user_transfers.items():
            if len(times) < 2:
                continue

            times.sort()
            for i in range(len(times) - 1):
                window_count = 1
                for j in range(i + 1, len(times)):
                    if times[j] - times[i] <= timedelta(hours=1):
                        window_count += 1

                if window_count > 10:
                    abnormal_users.append({
                        'user': user,
                        'transfers_in_hour': window_count
                    })
                    break

        if abnormal_users:
            return True, {
                'abnormal_count': len(abnormal_users),
                'users': abnormal_users
            }

        return False, {}

    def _send_alert_notification(self, alert: Dict):
        """发送报警通知"""
        if not self.notification_manager:
            return

        severity_map = {
            'critical': NotificationPriority.URGENT,
            'high': NotificationPriority.HIGH,
            'medium': NotificationPriority.NORMAL,
            'low': NotificationPriority.LOW
        }

        priority = severity_map.get(alert['severity'], NotificationPriority.NORMAL)

        # 通知所有监管者
        from models.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE role='regulator'")
            regulators = cursor.fetchall()

            for regulator in regulators:
                self.notification_manager.send_notification(
                    user_id=regulator['id'],
                    notification_type=NotificationType.SYSTEM_ALERT,
                    title=f"⚠️ 系统警报: {alert['rule_name']}",
                    message=alert['message'],
                    priority=priority,
                    data=alert['details']
                )

    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """获取报警历史"""
        return self.alert_history[-limit:]

    def get_alert_statistics(self) -> Dict:
        """获取报警统计"""
        from collections import Counter

        severity_counts = Counter(a['severity'] for a in self.alert_history)
        rule_counts = Counter(a['rule_name'] for a in self.alert_history)

        return {
            'total_alerts': len(self.alert_history),
            'by_severity': dict(severity_counts),
            'by_rule': dict(rule_counts),
            'most_frequent_rule': rule_counts.most_common(1)[0] if rule_counts else None
        }


# 导出
__all__ = ['AlertSystem', 'AlertRule']
