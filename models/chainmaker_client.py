"""
长安链（ChainMaker）集成模块
支持真实连接和模拟模式
"""
import logging
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)


class ChainMakerClient:
    """长安链客户端（真实版本）"""

    def __init__(self, config_path: str = None, chain_id: str = 'chain1'):
        """
        初始化长安链客户端

        Args:
            config_path: SDK 配置文件路径
            chain_id: 链 ID
        """
        self.chain_id = chain_id
        self.config_path = config_path
        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化客户端连接"""
        try:
            from chainmaker.chain_client import ChainClient

            if self.config_path and os.path.exists(self.config_path):
                self.client = ChainClient.from_conf(self.config_path)
                logger.info(f"✓ 长安链客户端已连接 (配置: {self.config_path})")
            else:
                logger.warning(f"⚠ 长安链配置文件不存在: {self.config_path}")
                self.client = None
        except ImportError:
            logger.warning("⚠ 长安链 SDK 未安装，已切换到模拟模式")
            self.client = None
        except Exception as e:
            logger.error(f"✗ 长安链客户端初始化失败: {e}，已切换到模拟模式")
            self.client = None

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.client is not None

    def get_chain_version(self) -> Optional[str]:
        """获取链版本信息"""
        if not self.is_connected():
            return None

        try:
            version = self.client.get_chainmaker_server_version()
            return version
        except Exception as e:
            logger.error(f"获取链版本失败: {e}")
            return None

    def get_block_height(self) -> Optional[int]:
        """获取区块链高度"""
        if not self.is_connected():
            return None

        try:
            info = self.client.get_chain_info()
            return info.get('block_height', 0) if isinstance(info, dict) else 0
        except Exception as e:
            logger.error(f"获取区块高度失败: {e}")
            return None

    def get_block_by_height(self, height: int) -> Optional[Dict]:
        """根据高度获取区块"""
        if not self.is_connected():
            return None

        try:
            block = self.client.get_block_by_height(height, with_rw_set=True)
            return self._parse_block(block) if block else None
        except Exception as e:
            logger.error(f"获取区块失败 (高度: {height}): {e}")
            return None

    def get_block_by_hash(self, block_hash: str) -> Optional[Dict]:
        """根据哈希获取区块"""
        if not self.is_connected():
            return None

        try:
            block = self.client.get_block_by_hash(block_hash, with_rw_set=True)
            return self._parse_block(block) if block else None
        except Exception as e:
            logger.error(f"获取区块失败 (哈希: {block_hash}): {e}")
            return None

    def get_recent_blocks(self, limit: int = 10) -> List[Dict]:
        """获取最近的 N 个区块"""
        if not self.is_connected():
            return []

        try:
            height = self.get_block_height()
            if not height:
                return []

            blocks = []
            for i in range(max(0, height - limit), height):
                block = self.get_block_by_height(i)
                if block:
                    blocks.append(block)

            return list(reversed(blocks))
        except Exception as e:
            logger.error(f"获取最近区块失败: {e}")
            return []

    def get_tx_by_txid(self, txid: str) -> Optional[Dict]:
        """根据交易 ID 获取交易"""
        if not self.is_connected():
            return None

        try:
            tx = self.client.get_tx_by_txid(txid)
            return self._parse_transaction(tx) if tx else None
        except Exception as e:
            logger.error(f"获取交易失败 (ID: {txid}): {e}")
            return None

    def get_block_by_txid(self, txid: str) -> Optional[Dict]:
        """根据交易 ID 获取所在区块"""
        if not self.is_connected():
            return None

        try:
            result = self.client.get_tx_by_txid(txid)
            if result and hasattr(result, 'block_height'):
                return self.get_block_by_height(result.block_height)
            return None
        except Exception as e:
            logger.error(f"获取交易所在区块失败: {e}")
            return None

    def _parse_block(self, block) -> Dict:
        """解析区块对象为字典"""
        try:
            return {
                'height': block.get('height', 0) if isinstance(block, dict) else 0,
                'hash': block.get('hash', '') if isinstance(block, dict) else '',
                'prev_hash': block.get('prev_hash', '') if isinstance(block, dict) else '',
                'timestamp': block.get('timestamp', 0) if isinstance(block, dict) else 0,
                'tx_count': block.get('tx_count', 0) if isinstance(block, dict) else 0,
                'transactions': block.get('txs', []) if isinstance(block, dict) else []
            }
        except Exception as e:
            logger.error(f"解析区块失败: {e}")
            return {}

    def _parse_transaction(self, tx) -> Dict:
        """解析交易对象为字典"""
        try:
            return {
                'txid': tx.get('txid', '') if isinstance(tx, dict) else '',
                'timestamp': tx.get('timestamp', 0) if isinstance(tx, dict) else 0,
                'type': tx.get('type', '') if isinstance(tx, dict) else '',
                'sender': tx.get('sender', '') if isinstance(tx, dict) else '',
                'contract_name': tx.get('contract_name', '') if isinstance(tx, dict) else '',
                'method': tx.get('method', '') if isinstance(tx, dict) else '',
                'code': tx.get('code', 0) if isinstance(tx, dict) else 0,
                'message': tx.get('message', '') if isinstance(tx, dict) else ''
            }
        except Exception as e:
            logger.error(f"解析交易失败: {e}")
            return {}

    def query_contract(self, contract_name: str, method: str, params: Dict = None) -> Optional[str]:
        """查询合约"""
        if not self.is_connected():
            return None

        try:
            result = self.client.query_contract(
                contract_name=contract_name,
                method=method,
                params=params or {}
            )
            return result
        except Exception as e:
            logger.error(f"查询合约失败: {e}")
            return None


# 全局客户端实例
_chainmaker_client = None


def get_chainmaker_client() -> ChainMakerClient:
    """获取全局长安链客户端"""
    global _chainmaker_client

    if _chainmaker_client is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'chainmaker_config',
            'sdk_config.yml'
        )
        _chainmaker_client = ChainMakerClient(config_path)

    return _chainmaker_client

