"""
区块链数据导出与审计系统 - 生成合规报告和可验证的审计记录
"""

import json
import csv
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional
from io import StringIO
from enum import Enum

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """导出格式"""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    PDF = "pdf"


class AuditLevel(Enum):
    """审计级别"""
    BASIC = "basic"           # 基础审计
    STANDARD = "standard"     # 标准审计
    COMPREHENSIVE = "comprehensive"  # 全面审计


class BlockchainAuditSystem:
    """区块链审计系统"""

    def __init__(self):
        self.audit_logs: List[Dict] = []

    def verify_blockchain_integrity(self) -> Dict:
        """验证区块链完整性"""
        from models.blockchain import blockchain

        is_valid, message = blockchain.is_chain_valid()

        total_blocks = len(blockchain.chain)
        verified_blocks = 0
        integrity_issues = []

        for i, block in enumerate(blockchain.chain):
            # 验证哈希
            calculated_hash = block.calculate_hash()
            if calculated_hash != block.hash:
                integrity_issues.append({
                    "block_index": i,
                    "issue": "Hash mismatch",
                    "expected": block.hash,
                    "calculated": calculated_hash
                })
            else:
                verified_blocks += 1

            # 验证链接
            if i > 0:
                previous_block = blockchain.chain[i - 1]
                if block.previous_hash != previous_block.hash:
                    integrity_issues.append({
                        "block_index": i,
                        "issue": "Chain link broken",
                        "previous_hash": block.previous_hash,
                        "expected": previous_block.hash
                    })

        integrity_score = (verified_blocks / total_blocks * 100) if total_blocks > 0 else 0

        audit_result = {
            "is_valid": is_valid,
            "message": message,
            "total_blocks": total_blocks,
            "verified_blocks": verified_blocks,
            "integrity_score": round(integrity_score, 2),
            "issues": integrity_issues,
            "audited_at": datetime.now().isoformat()
        }

        self._log_audit("blockchain_integrity", audit_result)
        return audit_result

    def audit_product_history(self, product_id: str, level: AuditLevel = AuditLevel.STANDARD) -> Dict:
        """审计产品历史记录"""
        from models.database import get_product_by_id, get_events_by_product_id

        product = get_product_by_id(product_id)
        if not product:
            return {"error": "Product not found"}

        events = get_events_by_product_id(product_id)

        product_name = product['name'] if 'name' in product.keys() else None
        audit_result = {
            "product_id": product_id,
            "product_name": product_name,
            "audit_level": level.value,
            "total_events": len(events),
            "event_summary": self._summarize_events(events),
            "timeline": [],
            "anomalies": [],
            "compliance_checks": {},
            "audited_at": datetime.now().isoformat()
        }

        # 构建时间线
        for event in events:
            from_user = event['from_username'] if 'from_username' in event.keys() else None
            to_user = event['to_username'] if 'to_username' in event.keys() else None
            actor = from_user or to_user
            location = event['location'] if 'location' in event.keys() else None

            timeline_entry = {
                "timestamp": event['created_at'],
                "event_type": event['event_type'],
                "actor": actor,
                "location": location,
                "block_hash": event['block_hash']
            }
            audit_result["timeline"].append(timeline_entry)

        # 异常检测
        if level in [AuditLevel.STANDARD, AuditLevel.COMPREHENSIVE]:
            anomalies = self._detect_anomalies(events)
            audit_result["anomalies"] = anomalies

        # 合规性检查
        if level == AuditLevel.COMPREHENSIVE:
            compliance = self._check_compliance(product, events)
            audit_result["compliance_checks"] = compliance

        self._log_audit("product_history", audit_result)
        return audit_result

    def _summarize_events(self, events: List) -> Dict:
        """统计事件摘要"""
        from collections import Counter

        event_types = Counter(e['event_type'] for e in events)
        unique_actors = set()
        unique_locations = set()

        for event in events:
            from_user = event['from_username'] if 'from_username' in event.keys() else None
            to_user = event['to_username'] if 'to_username' in event.keys() else None
            location = event['location'] if 'location' in event.keys() else None

            if from_user:
                unique_actors.add(from_user)
            if to_user:
                unique_actors.add(to_user)
            if location:
                unique_locations.add(location)

        return {
            "by_type": dict(event_types),
            "unique_actors": len(unique_actors),
            "unique_locations": len(unique_locations),
            "actors": list(unique_actors),
            "locations": list(unique_locations)
        }

    def _detect_anomalies(self, events: List) -> List[Dict]:
        """检测异常模式"""
        anomalies = []

        # 检测时间异常（快速连续转移）
        transfer_events = [e for e in events if e['event_type'] == 'transfer']
        for i in range(len(transfer_events) - 1):
            current = transfer_events[i]
            next_event = transfer_events[i + 1]

            try:
                current_time = datetime.fromisoformat(current['created_at'])
                next_time = datetime.fromisoformat(next_event['created_at'])
                time_diff = (next_time - current_time).total_seconds()

                if time_diff < 60:  # 1分钟内连续转移
                    anomalies.append({
                        "type": "rapid_transfer",
                        "description": "检测到快速连续转移",
                        "time_difference_seconds": time_diff,
                        "events": [current['id'], next_event['id']]
                    })
            except (ValueError, TypeError):
                pass

        # 检测循环转移（A->B->A）
        for i in range(len(transfer_events) - 1):
            current = transfer_events[i]
            for j in range(i + 1, len(transfer_events)):
                future = transfer_events[j]
                if (current.get('from_username') == future.get('to_username') and
                    current.get('to_username') == future.get('from_username')):
                    anomalies.append({
                        "type": "circular_transfer",
                        "description": "检测到循环转移模式",
                        "actors": [current.get('from_username'), current.get('to_username')]
                    })
                    break

        # 检测缺失质检
        has_quality_check = any(e['event_type'] == 'quality_check' for e in events)
        if not has_quality_check and len(events) > 2:
            anomalies.append({
                "type": "missing_quality_check",
                "description": "产品流转过程中未进行质量检验",
                "severity": "medium"
            })

        return anomalies

    def _check_compliance(self, product: Dict, events: List) -> Dict:
        """合规性检查"""
        compliance = {
            "passed": [],
            "failed": [],
            "warnings": []
        }

        # 检查：必须有注册事件
        has_register = any(e['event_type'] == 'register' for e in events)
        if has_register:
            compliance["passed"].append("产品已正确注册")
        else:
            compliance["failed"].append("缺少产品注册记录")

        # 检查：转移记录完整性
        transfer_events = [e for e in events if e['event_type'] == 'transfer']
        incomplete_transfers = [
            e for e in transfer_events
            if not e.get('from_username') or not e.get('to_username')
        ]
        if not incomplete_transfers:
            compliance["passed"].append("所有转移记录完整")
        else:
            compliance["failed"].append(f"发现 {len(incomplete_transfers)} 条不完整的转移记录")

        # 检查：质检频率
        quality_checks = [e for e in events if e['event_type'] == 'quality_check']
        if len(quality_checks) >= len(transfer_events) * 0.5:
            compliance["passed"].append("质检频率符合标准")
        else:
            compliance["warnings"].append("质检频率偏低，建议增加检验")

        # 检查：区块链记录
        all_have_blocks = all(e.get('block_hash') for e in events)
        if all_have_blocks:
            compliance["passed"].append("所有事件均已上链")
        else:
            compliance["failed"].append("部分事件未上链存储")

        return compliance

    def export_blockchain_data(self, export_format: ExportFormat,
                               start_block: int = 0, end_block: int = None) -> str:
        """导出区块链数据"""
        from models.blockchain import blockchain

        blocks = blockchain.chain[start_block:end_block] if end_block else blockchain.chain[start_block:]

        if export_format == ExportFormat.JSON:
            return self._export_json(blocks)
        elif export_format == ExportFormat.CSV:
            return self._export_csv(blocks)
        elif export_format == ExportFormat.XML:
            return self._export_xml(blocks)
        else:
            return json.dumps({"error": "Unsupported format"})

    def _export_json(self, blocks: List) -> str:
        """导出为JSON格式"""
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_blocks": len(blocks),
            "blocks": [block.to_dict() for block in blocks]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _export_csv(self, blocks: List) -> str:
        """导出为CSV格式"""
        output = StringIO()
        writer = csv.writer(output)

        # 写入表头
        writer.writerow(['Index', 'Timestamp', 'Hash', 'Previous Hash', 'Nonce', 'Data'])

        # 写入数据
        for block in blocks:
            writer.writerow([
                block.index,
                block.timestamp,
                block.hash,
                block.previous_hash,
                block.nonce,
                json.dumps(block.data)
            ])

        return output.getvalue()

    def _export_xml(self, blocks: List) -> str:
        """导出为XML格式"""
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append('<blockchain>')
        xml_lines.append(f'  <export_timestamp>{datetime.now().isoformat()}</export_timestamp>')
        xml_lines.append(f'  <total_blocks>{len(blocks)}</total_blocks>')
        xml_lines.append('  <blocks>')

        for block in blocks:
            xml_lines.append('    <block>')
            xml_lines.append(f'      <index>{block.index}</index>')
            xml_lines.append(f'      <timestamp>{block.timestamp}</timestamp>')
            xml_lines.append(f'      <hash>{block.hash}</hash>')
            xml_lines.append(f'      <previous_hash>{block.previous_hash}</previous_hash>')
            xml_lines.append(f'      <nonce>{block.nonce}</nonce>')
            xml_lines.append(f'      <data><![CDATA[{json.dumps(block.data)}]]></data>')
            xml_lines.append('    </block>')

        xml_lines.append('  </blocks>')
        xml_lines.append('</blockchain>')

        return '\n'.join(xml_lines)

    def generate_audit_certificate(self, audit_results: Dict) -> Dict:
        """生成审计证书"""
        # 计算审计结果的哈希值
        audit_hash = hashlib.sha256(
            json.dumps(audit_results, sort_keys=True).encode()
        ).hexdigest()

        certificate = {
            "certificate_id": f"AUDIT_{int(datetime.now().timestamp())}",
            "audit_hash": audit_hash,
            "audit_summary": {
                "total_blocks": audit_results.get("total_blocks", 0),
                "verified_blocks": audit_results.get("verified_blocks", 0),
                "integrity_score": audit_results.get("integrity_score", 0),
                "is_valid": audit_results.get("is_valid", False)
            },
            "auditor": "Blockchain Audit System v1.0",
            "issued_at": datetime.now().isoformat(),
            "valid_until": None  # 可设置有效期
        }

        return certificate

    def compare_blockchain_snapshots(self, snapshot1: Dict, snapshot2: Dict) -> Dict:
        """比较两个区块链快照"""
        comparison = {
            "snapshot1_blocks": snapshot1.get("total_blocks", 0),
            "snapshot2_blocks": snapshot2.get("total_blocks", 0),
            "blocks_added": 0,
            "differences": []
        }

        blocks_added = comparison["snapshot2_blocks"] - comparison["snapshot1_blocks"]
        comparison["blocks_added"] = blocks_added

        if blocks_added < 0:
            comparison["differences"].append({
                "type": "warning",
                "message": "检测到区块数量减少，可能存在问题"
            })

        return comparison

    def _log_audit(self, audit_type: str, result: Dict):
        """记录审计日志"""
        log_entry = {
            "audit_type": audit_type,
            "timestamp": datetime.now().isoformat(),
            "result_summary": {
                k: v for k, v in result.items()
                if k in ['is_valid', 'total_events', 'integrity_score']
            }
        }
        self.audit_logs.append(log_entry)
        logger.info(f"Audit logged: {audit_type}")

    def get_audit_history(self, limit: int = 10) -> List[Dict]:
        """获取审计历史"""
        return self.audit_logs[-limit:]

    def generate_compliance_report(self) -> Dict:
        """生成合规性报告"""
        from models.database import get_all_products, get_all_events

        products = get_all_products()
        events = get_all_events()

        report = {
            "report_date": datetime.now().isoformat(),
            "total_products": len(products),
            "total_events": len(events),
            "blockchain_status": self.verify_blockchain_integrity(),
            "product_compliance": [],
            "overall_score": 0.0
        }

        # 检查每个产品的合规性
        compliance_scores = []
        for product in products[:10]:  # 限制数量以提高性能
            product_events = get_events_by_product_id(product['product_id'])
            compliance = self._check_compliance(product, product_events)

            score = len(compliance["passed"]) / (
                len(compliance["passed"]) + len(compliance["failed"]) + len(compliance["warnings"])
            ) * 100 if compliance["passed"] or compliance["failed"] or compliance["warnings"] else 0

            compliance_scores.append(score)

            report["product_compliance"].append({
                "product_id": product['product_id'],
                "score": round(score, 2),
                "status": "compliant" if score >= 80 else "non_compliant"
            })

        report["overall_score"] = round(
            sum(compliance_scores) / len(compliance_scores), 2
        ) if compliance_scores else 0

        return report


# 全局审计系统实例
audit_system = BlockchainAuditSystem()


__all__ = ['BlockchainAuditSystem', 'ExportFormat', 'AuditLevel', 'audit_system']
