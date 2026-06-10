"""
区块链溯源系统 - 核心创新功能模块
包括：
- 产品认证证书系统（NFT概念）
- 供应链合同智能管理
- 产品防伪验证码生成
- 供应链协议自动执行
- 产品批次关联管理
- 区块链交易验证
- 产品溯源完整性证明
"""
import hashlib
import json
from datetime import datetime, timedelta
from models.database import get_db_connection
import qrcode
from io import BytesIO
import base64


class BlockchainCertification:
    """区块链认证证书系统 - 为每个产品生成不可篡改的认证"""

    @staticmethod
    def generate_product_certificate(product_id):
        """为产品生成区块链认证证书"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 获取产品信息
            cursor.execute('''
                SELECT p.*, m.username as manufacturer, m.company_name
                FROM products p
                LEFT JOIN users m ON p.manufacturer_id = m.id
                WHERE p.product_id = ?
            ''', (product_id,))
            product = cursor.fetchone()

            if not product:
                return None

            # 获取产品所有事件的哈希链（使用第一条block的hash）
            cursor.execute('''
                SELECT hash FROM blocks ORDER BY id LIMIT 1
            ''')
            block = cursor.fetchone()
            block_hash = block['hash'] if block else 'GENESIS'

            # 生成认证信息
            cert_data = {
                'certificate_id': hashlib.sha256(f"{product_id}{datetime.now().isoformat()}".encode()).hexdigest()[:16].upper(),
                'product_id': product_id,
                'product_name': product['name'],
                'batch_number': product['batch_number'],
                'manufacturer': product['manufacturer'],
                'production_date': product['created_at'],
                'block_hash': block_hash,
                'certification_date': datetime.now().isoformat(),
                'validity_period': 365,  # 一年有效期
                'certificate_hash': None  # 将在下面计算
            }

            # 生成证书哈希
            cert_hash = hashlib.sha256(json.dumps(cert_data, sort_keys=True).encode()).hexdigest()
            cert_data['certificate_hash'] = cert_hash

            return cert_data

    @staticmethod
    def verify_certificate(cert_id, product_id):
        """验证证书的真伪"""
        cert = BlockchainCertification.generate_product_certificate(product_id)
        if cert and cert['certificate_id'] == cert_id:
            return {
                'verified': True,
                'message': '证书真伪已验证',
                'cert': cert
            }
        return {
            'verified': False,
            'message': '证书验证失败，产品可能为假冒'
        }


class AntiCounterfeitCode:
    """防伪验证码系统"""

    @staticmethod
    def generate_qr_code(product_id):
        """为产品生成二维码"""
        try:
            import qrcode
            from io import BytesIO
            import base64

            # 创建包含产品信息的二维码
            qr_data = f"http://localhost:5000/features/verify?product={product_id}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # 转换为base64以便在网页显示
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            print(f"生成二维码失败: {e}")
            return None

    @staticmethod
    def generate_anti_counterfeit_code(product_id):
        """生成防伪验证码"""
        timestamp = datetime.now().isoformat()
        code_data = f"{product_id}{timestamp}"

        # 多层哈希加密防伪码
        hash1 = hashlib.sha256(code_data.encode()).hexdigest()[:8]
        hash2 = hashlib.sha512(hash1.encode()).hexdigest()[:8]
        hash3 = hashlib.md5(hash2.encode()).hexdigest()[:8]

        anti_code = f"{hash1}-{hash2}-{hash3}".upper()

        return {
            'code': anti_code,
            'product_id': product_id,
            'generated_at': timestamp,
            'verification_url': f"https://verify.blockchaintraces.app/?code={anti_code}"
        }


class SmartContract:
    """供应链智能合约系统 - 自动执行交易规则"""

    @staticmethod
    def create_supply_chain_contract(from_user_id, to_user_id, product_id, terms):
        """创建供应链智能合约"""
        contract = {
            'contract_id': hashlib.sha256(f"{from_user_id}{to_user_id}{product_id}{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
            'product_id': product_id,
            'terms': terms,  # 合同条款（如价格、交付期限等）
            'status': 'pending',  # pending, accepted, rejected, completed
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),
            'checksum': None
        }

        # 生成合同校验和
        contract_str = json.dumps(contract, sort_keys=True)
        contract['checksum'] = hashlib.sha256(contract_str.encode()).hexdigest()

        return contract

    @staticmethod
    def validate_contract_execution(contract_id, from_user_id, to_user_id, product_id):
        """验证合同是否可以执行"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 检查产品所有权
            cursor.execute('''
                SELECT current_owner_id FROM products WHERE product_id = ?
            ''', (product_id,))
            product = cursor.fetchone()

            if not product or product['current_owner_id'] != from_user_id:
                return {
                    'can_execute': False,
                    'reason': '所有权验证失败'
                }

            return {
                'can_execute': True,
                'reason': '合同可执行'
            }


class ProductBatchManagement:
    """产品批次关联管理 - 追踪同批次产品"""

    @staticmethod
    def get_batch_products(batch_number):
        """获取同一批次的所有产品"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT p.*, m.username as manufacturer, o.username as owner,
                       COUNT(e.id) as event_count
                FROM products p
                LEFT JOIN users m ON p.manufacturer_id = m.id
                LEFT JOIN users o ON p.current_owner_id = o.id
                LEFT JOIN events e ON p.product_id = e.product_id
                WHERE p.batch_number = ?
                GROUP BY p.product_id
            ''', (batch_number,))

            products = cursor.fetchall()

            # 分析批次质量
            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN data LIKE '%合格%' THEN 1 ELSE 0 END) as qualified
                FROM events e
                JOIN products p ON p.product_id = e.product_id
                WHERE p.batch_number = ? AND e.event_type = 'quality_check'
            ''', (batch_number,))

            quality = cursor.fetchone()

            return {
                'batch_number': batch_number,
                'total_products': len(products),
                'products': [dict(p) for p in products],
                'quality_stats': {
                    'total_checks': quality['total'] if quality else 0,
                    'qualified': quality['qualified'] if quality else 0,
                    'qualified_rate': (quality['qualified'] / quality['total'] * 100) if quality and quality['total'] > 0 else 0
                }
            }

    @staticmethod
    def batch_risk_analysis(batch_number):
        """批次风险分析 - 评估整个批次的质量风险"""
        batch_data = ProductBatchManagement.get_batch_products(batch_number)

        if batch_data['quality_stats']['total_checks'] == 0:
            risk_level = '未知'
            risk_score = 50
        else:
            qualified_rate = batch_data['quality_stats']['qualified_rate']
            if qualified_rate >= 95:
                risk_level = '低风险'
                risk_score = 20
            elif qualified_rate >= 85:
                risk_level = '中风险'
                risk_score = 50
            else:
                risk_level = '高风险'
                risk_score = 80

        return {
            'batch_number': batch_number,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'recommendation': '建议加强质检' if risk_score > 50 else '质量稳定，可继续生产'
        }


class BlockchainVerification:
    """区块链完整性验证系统"""

    @staticmethod
    def verify_product_chain_integrity(product_id):
        """验证产品溯源链的完整性和连续性"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 获取产品的所有事件
            cursor.execute('''
                SELECT e.*, fu.username as from_user, tu.username as to_user
                FROM events e
                LEFT JOIN users fu ON e.from_user_id = fu.id
                LEFT JOIN users tu ON e.to_user_id = tu.id
                WHERE e.product_id = ?
                ORDER BY e.created_at ASC
            ''', (product_id,))

            events = cursor.fetchall()

            # 验证事件链的逻辑连贯性
            verification_results = {
                'product_id': product_id,
                'total_events': len(events),
                'chain_valid': True,
                'issues': [],
                'integrity_score': 100
            }

            # 检查1：所有权转移的连续性
            current_owner = None
            for event in events:
                if event['event_type'] == 'transfer':
                    if current_owner and event['from_user'] != current_owner:
                        verification_results['chain_valid'] = False
                        verification_results['issues'].append(
                            f"所有权转移断裂：期望从 {current_owner} 转移，实际从 {event['from_user']}"
                        )
                    current_owner = event['to_user']

            # 检查2：质检前是否有转移
            has_transfer_before_check = False
            for i, event in enumerate(events):
                if event['event_type'] == 'quality_check':
                    if i > 0 and any(e['event_type'] == 'transfer' for e in events[:i]):
                        has_transfer_before_check = True

            if not has_transfer_before_check and len(events) > 0:
                verification_results['issues'].append("未检测到质检流程")
                verification_results['integrity_score'] -= 20

            # 计算完整性得分
            verification_results['integrity_score'] = max(0, 100 - len(verification_results['issues']) * 10)

            return verification_results

    @staticmethod
    def calculate_traceability_completeness(product_id):
        """计算产品溯源完整性指数"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN event_type = 'register' THEN 1 ELSE 0 END) as has_register,
                       SUM(CASE WHEN event_type = 'quality_check' THEN 1 ELSE 0 END) as has_quality,
                       SUM(CASE WHEN event_type = 'transfer' THEN 1 ELSE 0 END) as has_transfer,
                       SUM(CASE WHEN event_type = 'logistics' THEN 1 ELSE 0 END) as has_logistics
                FROM events
                WHERE product_id = ?
            ''', (product_id,))

            result = cursor.fetchone()

            # 计算完整性指数：最高100分
            score = 0
            if result['has_register']:
                score += 25
            if result['has_quality']:
                score += 25
            if result['has_transfer']:
                score += 25
            if result['has_logistics']:
                score += 25

            return {
                'product_id': product_id,
                'completeness_score': score,
                'has_registration': bool(result['has_register']),
                'has_quality_check': bool(result['has_quality']),
                'has_transfer_records': bool(result['has_transfer']),
                'has_logistics_info': bool(result['has_logistics']),
                'description': f"产品溯源完整性: {score}%" +
                              ("✓ 完全溯源" if score == 100 else "✓ 大部分溯源" if score >= 75 else "⚠ 溯源不完整")
            }
