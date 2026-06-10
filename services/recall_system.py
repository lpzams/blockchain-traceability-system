"""
产品召回管理系统 - 快速定位问题产品并追踪所有受影响方
"""

import logging
from datetime import datetime
from typing import Dict, List, Set, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RecallSeverity(Enum):
    """召回严重程度"""
    LOW = "low"          # 轻微问题，建议召回
    MEDIUM = "medium"    # 中等问题，需要召回
    HIGH = "high"        # 严重问题，紧急召回
    CRITICAL = "critical"  # 危及安全，立即召回


class RecallStatus(Enum):
    """召回状态"""
    INITIATED = "initiated"      # 已启动
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消


class ProductRecall:
    """产品召回记录"""

    def __init__(self, recall_id: str, reason: str, severity: RecallSeverity,
                 affected_criteria: Dict):
        self.recall_id = recall_id
        self.reason = reason
        self.severity = severity
        self.affected_criteria = affected_criteria  # 受影响产品的筛选条件
        self.status = RecallStatus.INITIATED
        self.initiated_at = datetime.now()
        self.completed_at = None
        self.affected_products: Set[str] = set()
        self.notified_parties: Set[str] = set()
        self.recovered_products: Set[str] = set()

    def to_dict(self) -> Dict:
        return {
            "recall_id": self.recall_id,
            "reason": self.reason,
            "severity": self.severity.value,
            "status": self.status.value,
            "initiated_at": self.initiated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "affected_products_count": len(self.affected_products),
            "notified_parties_count": len(self.notified_parties),
            "recovered_products_count": len(self.recovered_products),
            "recovery_rate": self._calculate_recovery_rate()
        }

    def _calculate_recovery_rate(self) -> float:
        """计算召回回收率"""
        if len(self.affected_products) == 0:
            return 0.0
        return (len(self.recovered_products) / len(self.affected_products)) * 100


class RecallManagementSystem:
    """召回管理系统"""

    def __init__(self):
        self.active_recalls: Dict[str, ProductRecall] = {}
        self.recall_history: List[ProductRecall] = []

    def initiate_recall(self, recall_id: str, reason: str, severity: RecallSeverity,
                       affected_criteria: Dict) -> ProductRecall:
        """启动产品召回"""
        recall = ProductRecall(recall_id, reason, severity, affected_criteria)

        # 查找受影响的产品
        affected_products = self._find_affected_products(affected_criteria)
        recall.affected_products = set(affected_products)

        # 查找需要通知的相关方
        affected_parties = self._find_affected_parties(affected_products)
        recall.notified_parties = affected_parties

        self.active_recalls[recall_id] = recall

        logger.warning(
            f"Recall initiated: {recall_id}, Severity: {severity.value}, "
            f"Affected products: {len(recall.affected_products)}, "
            f"Parties to notify: {len(recall.notified_parties)}"
        )

        return recall

    def _find_affected_products(self, criteria: Dict) -> List[str]:
        """根据条件查找受影响的产品"""
        from models.database import get_all_products

        all_products = get_all_products()
        affected = []

        for product in all_products:
            if self._matches_criteria(product, criteria):
                affected.append(product['product_id'])

        return affected

    def _matches_criteria(self, product: Dict, criteria: Dict) -> bool:
        """检查产品是否匹配召回条件"""
        # 按批次号
        if 'batch_number' in criteria:
            if product['batch_number'] != criteria['batch_number']:
                return False

        # 按生产日期范围
        if 'production_date_range' in criteria:
            start, end = criteria['production_date_range']
            prod_date = product['production_date']
            if not prod_date or not (start <= prod_date <= end):
                return False

        # 按制造商
        if 'manufacturer_id' in criteria:
            if product['manufacturer_id'] != criteria['manufacturer_id']:
                return False

        # 按产品名称
        if 'product_name' in criteria:
            prod_name = product['name'] if 'name' in product.keys() else ''
            if criteria['product_name'].lower() not in prod_name.lower():
                return False

        return True

    def _find_affected_parties(self, product_ids: List[str]) -> Set[str]:
        """查找所有接触过这些产品的相关方"""
        from models.database import get_events_by_product_id

        parties = set()

        for product_id in product_ids:
            events = get_events_by_product_id(product_id)
            for event in events:
                from_user = event['from_username'] if 'from_username' in event.keys() else None
                to_user = event['to_username'] if 'to_username' in event.keys() else None
                if from_user:
                    parties.add(from_user)
                if to_user:
                    parties.add(to_user)

        return parties

    def trace_product_flow(self, product_id: str) -> Dict:
        """追踪产品的完整流转路径"""
        from models.database import get_events_by_product_id, get_product_by_id

        product = get_product_by_id(product_id)
        if not product:
            return {"error": "Product not found"}

        events = get_events_by_product_id(product_id)

        flow_chain = []
        current_holder = None

        for event in events:
            location = event['location'] if 'location' in event.keys() else None
            from_user = event['from_username'] if 'from_username' in event.keys() else None
            to_user = event['to_username'] if 'to_username' in event.keys() else None

            node = {
                "timestamp": event['created_at'],
                "event_type": event['event_type'],
                "location": location,
                "from": from_user,
                "to": to_user
            }

            if event['event_type'] == 'transfer':
                current_holder = to_user

            flow_chain.append(node)

        return {
            "product_id": product_id,
            "product_name": product['name'],
            "current_holder": current_holder,
            "flow_chain": flow_chain,
            "total_transfers": len([e for e in events if e['event_type'] == 'transfer'])
        }

    def mark_product_recovered(self, recall_id: str, product_id: str) -> bool:
        """标记产品已回收"""
        if recall_id not in self.active_recalls:
            return False

        recall = self.active_recalls[recall_id]
        if product_id in recall.affected_products:
            recall.recovered_products.add(product_id)
            logger.info(f"Product {product_id} marked as recovered for recall {recall_id}")
            return True

        return False

    def complete_recall(self, recall_id: str) -> bool:
        """完成召回"""
        if recall_id not in self.active_recalls:
            return False

        recall = self.active_recalls[recall_id]
        recall.status = RecallStatus.COMPLETED
        recall.completed_at = datetime.now()

        # 移至历史记录
        self.recall_history.append(recall)
        del self.active_recalls[recall_id]

        logger.info(
            f"Recall completed: {recall_id}, "
            f"Recovery rate: {recall._calculate_recovery_rate():.2f}%"
        )

        return True

    def get_recall_status(self, recall_id: str) -> Optional[Dict]:
        """获取召回状态"""
        # 先查活跃召回
        if recall_id in self.active_recalls:
            return self.active_recalls[recall_id].to_dict()

        # 再查历史记录
        for recall in self.recall_history:
            if recall.recall_id == recall_id:
                return recall.to_dict()

        return None

    def list_active_recalls(self) -> List[Dict]:
        """列出所有活跃的召回"""
        return [recall.to_dict() for recall in self.active_recalls.values()]

    def generate_recall_report(self, recall_id: str) -> Dict:
        """生成召回报告"""
        recall_data = self.get_recall_status(recall_id)
        if not recall_data:
            return {"error": "Recall not found"}

        recall = self.active_recalls.get(recall_id) or \
                 next((r for r in self.recall_history if r.recall_id == recall_id), None)

        if not recall:
            return {"error": "Recall not found"}

        # 生成详细报告
        report = {
            "recall_id": recall_id,
            "summary": recall_data,
            "affected_products": list(recall.affected_products),
            "notified_parties": list(recall.notified_parties),
            "recovered_products": list(recall.recovered_products),
            "outstanding_products": list(recall.affected_products - recall.recovered_products),
            "recommendations": self._generate_recommendations(recall)
        }

        return report

    def _generate_recommendations(self, recall: ProductRecall) -> List[str]:
        """生成召回建议"""
        recommendations = []

        recovery_rate = recall._calculate_recovery_rate()

        if recovery_rate < 50:
            recommendations.append("回收率偏低，建议增加通知渠道和频率")

        if recall.severity in [RecallSeverity.HIGH, RecallSeverity.CRITICAL]:
            recommendations.append("高风险召回，建议联系监管部门并发布公告")

        outstanding = len(recall.affected_products - recall.recovered_products)
        if outstanding > 10:
            recommendations.append(f"仍有 {outstanding} 件产品未回收，建议加强追踪")

        return recommendations


# 全局召回系统实例
recall_system = RecallManagementSystem()


__all__ = ['RecallManagementSystem', 'ProductRecall', 'RecallSeverity',
           'RecallStatus', 'recall_system']
