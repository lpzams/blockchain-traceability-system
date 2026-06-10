"""
长安链（ChainMaker）模拟客户端
基于产品溯源系统的真实数据生成模拟区块链
"""
import logging
import time
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MockChainMakerClient:
    """长安链模拟客户端 - 基于产品溯源数据"""

    def __init__(self, chain_id: str = 'supply-chain'):
        """初始化模拟客户端"""
        self.chain_id = chain_id
        self.connected = True
        self.blocks = []
        self._generate_product_trace_blocks()
        logger.info(f"✓ 长安链模拟客户端已初始化 (链ID: {chain_id})")

    def _generate_product_trace_blocks(self):
        """基于产品溯源生成模拟区块"""
        try:
            from models.database import get_db_connection, get_all_products, get_all_events

            with get_db_connection() as conn:
                # 获取所有产品和事件
                products = get_all_products()
                events = get_all_events()

                # 创世区块
                genesis_block = {
                    'height': 0,
                    'hash': self._generate_hash('genesis_block'),
                    'prev_hash': '0' * 64,
                    'timestamp': int(datetime.now().timestamp()) - 86400,
                    'tx_count': 1,
                    'transactions': [{
                        'txid': self._generate_hash('tx_genesis'),
                        'timestamp': int(datetime.now().timestamp()) - 86400,
                        'type': 'CHAIN_INIT',
                        'sender': 'system@chainmaker.org',
                        'contract_name': 'supply_chain',
                        'method': 'init',
                        'code': 0,
                        'message': 'SUCCESS',
                        'gas_used': 0,
                        'read_set': 0,
                        'write_set': 1
                    }],
                    'proposer': 'validator-0',
                    'version': '2.3.0',
                    'consensus_type': 'RAFT'
                }
                self.blocks.append(genesis_block)

                # 为每个产品创建区块
                for idx, product in enumerate(products):
                    product_events = [e for e in events if e['product_id'] == product['product_id']]

                    # 转换事件为交易
                    transactions = []
                    for event in product_events:
                        tx = {
                            'txid': self._generate_hash(f'tx_{event["id"]}'),
                            'timestamp': int(datetime.strptime(event['created_at'], '%Y-%m-%d %H:%M:%S').timestamp()),
                            'type': self._map_event_type(event['event_type']),
                            'sender': f"{event.get('from_username', 'system')}@{self._get_org_id(event.get('from_username'))}",
                            'contract_name': 'product_traceability',
                            'method': event['event_type'],
                            'code': 0,
                            'message': 'SUCCESS',
                            'gas_used': 5000 + (len(transactions) * 100),
                            'read_set': 2,
                            'write_set': 3,
                            'data': {
                                'product_id': product['product_id'],
                                'event_type': event['event_type'],
                                'from': event.get('from_username'),
                                'to': event.get('to_username'),
                                'location': event.get('location')
                            }
                        }
                        transactions.append(tx)

                    block = {
                        'height': idx + 1,
                        'hash': product['block_hash'],
                        'prev_hash': self.blocks[idx]['hash'],
                        'timestamp': int(datetime.strptime(product['created_at'], '%Y-%m-%d %H:%M:%S').timestamp()),
                        'tx_count': len(transactions),
                        'transactions': transactions,
                        'proposer': f'validator-{(idx + 1) % 4}',
                        'version': '2.3.0',
                        'consensus_type': 'RAFT',
                        'product_id': product['product_id'],
                        'product_name': product['name'],
                        'batch_number': product['batch_number'],
                        'manufacturer': product['manufacturer_name'],
                        'current_owner': product['owner_name']
                    }
                    self.blocks.append(block)

        except Exception as e:
            logger.error(f"生成产品溯源区块失败: {e}")
            # 如果生成失败，生成默认的演示数据
            self._generate_demo_blocks()

    def _generate_demo_blocks(self):
        """生成演示区块"""
        products_demo = [
            {'id': 1, 'name': '西湖龙井茶叶', 'batch': '001', 'manufacturer': '优质茶叶公司', 'owner': '经销商A'},
            {'id': 2, 'name': '有机绿茶', 'batch': '002', 'manufacturer': '优质茶叶公司', 'owner': '经销商C'},
            {'id': 3, 'name': '铁观音', 'batch': '003', 'manufacturer': '优质茶叶公司', 'owner': '消费者1'},
            {'id': 4, 'name': '有机大米', 'batch': '004', 'manufacturer': '有机食品基地', 'owner': '消费者3'},
            {'id': 5, 'name': '黑芝麻', 'batch': '005', 'manufacturer': '有机食品基地', 'owner': '消费者2'},
        ]

        # 创世区块
        self.blocks.append({
            'height': 0,
            'hash': self._generate_hash('genesis'),
            'prev_hash': '0' * 64,
            'timestamp': int(datetime.now().timestamp()) - 86400,
            'tx_count': 1,
            'transactions': [{'txid': self._generate_hash('tx_0'), 'type': 'CHAIN_INIT', 'sender': 'system', 'message': 'SUCCESS'}],
            'proposer': 'validator-0',
            'consensus_type': 'RAFT'
        })

        # 产品区块
        for idx, prod in enumerate(products_demo, 1):
            self.blocks.append({
                'height': idx,
                'hash': self._generate_hash(f'product_{prod["id"]}'),
                'prev_hash': self.blocks[idx-1]['hash'],
                'timestamp': int(datetime.now().timestamp()) - (86400 - idx * 3600),
                'tx_count': 3 + idx,
                'transactions': self._generate_demo_transactions(idx),
                'proposer': f'validator-{idx % 4}',
                'consensus_type': 'RAFT',
                'product_id': f'PROD-{prod["id"]:03d}',
                'product_name': prod['name'],
                'batch_number': prod['batch'],
                'manufacturer': prod['manufacturer'],
                'current_owner': prod['owner']
            })

    def _generate_demo_transactions(self, block_idx) -> List[Dict]:
        """生成演示交易"""
        transactions = []
        event_types = ['register', 'transfer', 'quality_check', 'logistics']

        for i in range(3 + block_idx):
            tx = {
                'txid': self._generate_hash(f'tx_block{block_idx}_{i}'),
                'timestamp': int(time.time()) - (3600 - i * 100),
                'type': 'INVOKE_CONTRACT',
                'sender': f'user{(block_idx + i) % 5}@wx-org{(block_idx + i) % 3 + 1}.chainmaker.org',
                'contract_name': 'product_traceability',
                'method': event_types[i % len(event_types)],
                'code': 0,
                'message': 'SUCCESS',
                'gas_used': 5000 + i * 200,
                'read_set': 2,
                'write_set': 3
            }
            transactions.append(tx)

        return transactions

    def _map_event_type(self, event_type: str) -> str:
        """将事件类型映射到长安链交易类型"""
        mapping = {
            'register': 'INVOKE_CONTRACT',
            'transfer': 'INVOKE_CONTRACT',
            'quality_check': 'INVOKE_CONTRACT',
            'logistics': 'INVOKE_CONTRACT'
        }
        return mapping.get(event_type, 'INVOKE_CONTRACT')

    def _get_org_id(self, username: str) -> str:
        """根据用户名获取组织ID"""
        if not username:
            return 'system.chainmaker.org'
        return f'wx-org{hash(username) % 3 + 1}.chainmaker.org'

    def _generate_hash(self, data: str) -> str:
        """生成SHA256哈希"""
        return hashlib.sha256(data.encode()).hexdigest()

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected

    def get_chain_version(self) -> str:
        """获取链版本"""
        return '长安链 v2.3.0 (产品溯源专用)'

    def get_block_height(self) -> int:
        """获取区块高度"""
        return len(self.blocks) - 1

    def get_block_by_height(self, height: int) -> Optional[Dict]:
        """按高度获取区块"""
        if 0 <= height < len(self.blocks):
            return self.blocks[height]
        return None

    def get_block_by_hash(self, block_hash: str) -> Optional[Dict]:
        """按哈希获取区块"""
        for block in self.blocks:
            if block['hash'] == block_hash:
                return block
        return None

    def get_recent_blocks(self, limit: int = 10) -> List[Dict]:
        """获取最近的区块"""
        return list(reversed(self.blocks[-limit:]))

    def get_tx_by_txid(self, txid: str) -> Optional[Dict]:
        """按交易ID获取交易"""
        for block in self.blocks:
            for tx in block.get('transactions', []):
                if tx['txid'] == txid:
                    return tx
        return None

    def get_block_by_txid(self, txid: str) -> Optional[Dict]:
        """按交易ID获取区块"""
        for block in self.blocks:
            for tx in block.get('transactions', []):
                if tx['txid'] == txid:
                    return block
        return None

    def query_contract(self, contract_name: str, method: str, params: Dict = None) -> str:
        """查询合约"""
        responses = {
            'product_traceability': '{"status": "success", "data": {"product_id": "PROD-001", "status": "verified"}}',
            'supply_chain': '{"status": "success", "data": {"chain_height": ' + str(self.get_block_height()) + '}}'
        }
        return responses.get(contract_name, '{"status": "error"}')

    def get_chain_info(self) -> Dict:
        """获取链信息"""
        return {
            'chain_id': self.chain_id,
            'block_height': self.get_block_height(),
            'block_hash': self.blocks[-1]['hash'] if self.blocks else '',
            'tx_count': sum(b.get('tx_count', 0) for b in self.blocks),
            'node_count': 4,
            'consensus_type': 'RAFT',
            'version': '2.3.0'
        }

    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            'is_healthy': True,
            'memory_usage': '1.2 GB',
            'cpu_usage': '24%',
            'goroutine_count': 248,
            'pending_tx_count': len([b for b in self.blocks if b.get('tx_count', 0) > 0])
        }


# 全局客户端实例
_mock_chainmaker_client = None


def get_mock_chainmaker_client() -> MockChainMakerClient:
    """获取全局模拟长安链客户端"""
    global _mock_chainmaker_client

    if _mock_chainmaker_client is None:
        _mock_chainmaker_client = MockChainMakerClient()

    return _mock_chainmaker_client

