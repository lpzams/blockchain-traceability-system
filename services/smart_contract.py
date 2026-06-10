"""
智能合约模块 - 自动化审批和业务规则执行
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ContractStatus(Enum):
    """合约状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class RuleType(Enum):
    """规则类型"""
    QUALITY_CHECK = "quality_check"
    TRANSFER_APPROVAL = "transfer_approval"
    PRICE_LIMIT = "price_limit"
    QUANTITY_LIMIT = "quantity_limit"


class SmartContract:
    """智能合约基类"""

    def __init__(self, contract_id: str, rule_type: RuleType, conditions: Dict):
        self.contract_id = contract_id
        self.rule_type = rule_type
        self.conditions = conditions
        self.status = ContractStatus.PENDING
        self.created_at = datetime.now()
        self.executed_at = None

    def evaluate(self, context: Dict) -> bool:
        """评估合约条件"""
        raise NotImplementedError

    def execute(self, context: Dict) -> Dict:
        """执行合约"""
        raise NotImplementedError


class QualityCheckContract(SmartContract):
    """质检自动审批合约"""

    def __init__(self, contract_id: str, min_score: float = 80.0):
        super().__init__(contract_id, RuleType.QUALITY_CHECK, {"min_score": min_score})
        self.min_score = min_score

    def evaluate(self, context: Dict) -> bool:
        """评估质检结果是否达标"""
        score = context.get("quality_score", 0)
        return score >= self.min_score

    def execute(self, context: Dict) -> Dict:
        """执行自动审批"""
        if self.evaluate(context):
            self.status = ContractStatus.APPROVED
            result = {
                "approved": True,
                "message": f"质检分数 {context.get('quality_score')} 达到标准 {self.min_score}",
                "action": "auto_approved"
            }
        else:
            self.status = ContractStatus.REJECTED
            result = {
                "approved": False,
                "message": f"质检分数 {context.get('quality_score')} 未达标准 {self.min_score}",
                "action": "requires_manual_review"
            }

        self.executed_at = datetime.now()
        logger.info(f"Contract {self.contract_id} executed: {result}")
        return result


class TransferApprovalContract(SmartContract):
    """转移自动审批合约"""

    def __init__(self, contract_id: str, allowed_parties: List[str], max_value: float = None):
        super().__init__(contract_id, RuleType.TRANSFER_APPROVAL, {
            "allowed_parties": allowed_parties,
            "max_value": max_value
        })
        self.allowed_parties = allowed_parties
        self.max_value = max_value

    def evaluate(self, context: Dict) -> bool:
        """评估转移是否符合条件"""
        to_user = context.get("to_user")
        value = context.get("value", 0)

        if to_user not in self.allowed_parties:
            return False

        if self.max_value and value > self.max_value:
            return False

        return True

    def execute(self, context: Dict) -> Dict:
        """执行转移审批"""
        if self.evaluate(context):
            self.status = ContractStatus.APPROVED
            result = {
                "approved": True,
                "message": "转移请求自动批准",
                "action": "transfer_approved"
            }
        else:
            self.status = ContractStatus.REJECTED
            reasons = []
            if context.get("to_user") not in self.allowed_parties:
                reasons.append("接收方不在授权列表中")
            if self.max_value and context.get("value", 0) > self.max_value:
                reasons.append(f"价值超过限额 {self.max_value}")

            result = {
                "approved": False,
                "message": "转移请求被拒绝",
                "reasons": reasons,
                "action": "transfer_rejected"
            }

        self.executed_at = datetime.now()
        return result


class SmartContractEngine:
    """智能合约引擎"""

    def __init__(self):
        self.contracts: Dict[str, SmartContract] = {}
        self.execution_history: List[Dict] = []

    def register_contract(self, contract: SmartContract):
        """注册合约"""
        self.contracts[contract.contract_id] = contract
        logger.info(f"Contract registered: {contract.contract_id} ({contract.rule_type.value})")

    def execute_contract(self, contract_id: str, context: Dict) -> Dict:
        """执行指定合约"""
        if contract_id not in self.contracts:
            return {"error": "Contract not found"}

        contract = self.contracts[contract_id]
        result = contract.execute(context)

        self.execution_history.append({
            "contract_id": contract_id,
            "executed_at": contract.executed_at.isoformat() if contract.executed_at else None,
            "status": contract.status.value,
            "result": result
        })

        return result

    def get_contract_status(self, contract_id: str) -> Optional[Dict]:
        """获取合约状态"""
        if contract_id not in self.contracts:
            return None

        contract = self.contracts[contract_id]
        return {
            "contract_id": contract.contract_id,
            "rule_type": contract.rule_type.value,
            "status": contract.status.value,
            "conditions": contract.conditions,
            "created_at": contract.created_at.isoformat(),
            "executed_at": contract.executed_at.isoformat() if contract.executed_at else None
        }

    def list_active_contracts(self) -> List[Dict]:
        """列出所有活跃合约"""
        return [
            self.get_contract_status(contract_id)
            for contract_id in self.contracts.keys()
        ]


# 全局合约引擎实例
contract_engine = SmartContractEngine()


__all__ = ['SmartContract', 'QualityCheckContract', 'TransferApprovalContract',
           'SmartContractEngine', 'contract_engine', 'ContractStatus', 'RuleType']
