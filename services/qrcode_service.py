"""
二维码生成服务 - 为产品生成唯一的二维码
"""

import io
import base64
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# 尝试导入二维码库
try:
    import qrcode
    from qrcode.image.pure import PyPNGImage
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    logger.warning("qrcode library not installed. QR code generation will be limited.")


class QRCodeService:
    """二维码生成服务"""

    @staticmethod
    def generate_product_qr(product_id: str, base_url: str = "http://localhost:5000") -> Optional[str]:
        """
        生成产品二维码（Base64编码的图片）

        Args:
            product_id: 产品ID
            base_url: 系统基础URL

        Returns:
            Base64编码的二维码图片，如果生成失败返回None
        """
        if not QR_AVAILABLE:
            return QRCodeService._generate_simple_qr(product_id, base_url)

        try:
            # 生成溯源查询链接
            trace_url = f"{base_url}/consumer/trace_result/{product_id}"

            # 创建二维码实例
            qr = qrcode.QRCode(
                version=1,  # 控制二维码大小，1-40
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # 高容错率
                box_size=10,  # 每个格子的像素大小
                border=4,  # 边框宽度
            )

            # 添加数据
            qr.add_data(trace_url)
            qr.make(fit=True)

            # 创建图片
            img = qr.make_image(fill_color="black", back_color="white")

            # 转换为Base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            logger.error(f"Failed to generate QR code: {str(e)}")
            return None

    @staticmethod
    def _generate_simple_qr(product_id: str, base_url: str) -> str:
        """
        生成简单的文本二维码（当qrcode库不可用时的备用方案）
        返回一个SVG格式的简单二维码
        """
        trace_url = f"{base_url}/consumer/trace_result/{product_id}"

        # 创建一个简单的SVG二维码替代品
        svg = f'''
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="200" fill="white"/>
            <rect x="20" y="20" width="160" height="160" fill="none" stroke="black" stroke-width="2"/>
            <text x="100" y="100" font-family="Arial" font-size="12" text-anchor="middle" fill="black">
                <tspan x="100" dy="0">扫描查看</tspan>
                <tspan x="100" dy="20">产品溯源</tspan>
            </text>
        </svg>
        '''

        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

    @staticmethod
    def generate_qr_with_logo(product_id: str, logo_path: Optional[str] = None,
                               base_url: str = "http://localhost:5000") -> Optional[str]:
        """
        生成带logo的二维码

        Args:
            product_id: 产品ID
            logo_path: logo图片路径
            base_url: 系统基础URL

        Returns:
            Base64编码的二维码图片
        """
        if not QR_AVAILABLE:
            return QRCodeService.generate_product_qr(product_id, base_url)

        try:
            from PIL import Image

            trace_url = f"{base_url}/consumer/trace_result/{product_id}"

            # 创建二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(trace_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # 如果提供了logo，添加到二维码中心
            if logo_path:
                try:
                    logo = Image.open(logo_path)
                    # 计算logo大小（二维码的1/5）
                    qr_width, qr_height = img.size
                    logo_size = qr_width // 5
                    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

                    # 将logo放置在二维码中心
                    logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
                    img.paste(logo, logo_pos)
                except Exception as e:
                    logger.warning(f"Failed to add logo to QR code: {str(e)}")

            # 转换为Base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_base64}"

        except ImportError:
            logger.warning("PIL library not available, falling back to simple QR code")
            return QRCodeService.generate_product_qr(product_id, base_url)
        except Exception as e:
            logger.error(f"Failed to generate QR code with logo: {str(e)}")
            return QRCodeService.generate_product_qr(product_id, base_url)

    @staticmethod
    def generate_batch_qr_codes(product_ids: list, base_url: str = "http://localhost:5000") -> Dict[str, str]:
        """
        批量生成二维码

        Args:
            product_ids: 产品ID列表
            base_url: 系统基础URL

        Returns:
            产品ID到二维码的映射字典
        """
        qr_codes = {}
        for product_id in product_ids:
            qr_code = QRCodeService.generate_product_qr(product_id, base_url)
            if qr_code:
                qr_codes[product_id] = qr_code

        logger.info(f"Generated {len(qr_codes)} QR codes")
        return qr_codes

    @staticmethod
    def get_qr_info(product_id: str, base_url: str = "http://localhost:5000") -> Dict:
        """
        获取二维码信息

        Returns:
            包含URL和其他元数据的字典
        """
        trace_url = f"{base_url}/consumer/trace_result/{product_id}"
        return {
            'product_id': product_id,
            'trace_url': trace_url,
            'qr_available': QR_AVAILABLE
        }


# 导出
__all__ = ['QRCodeService']
