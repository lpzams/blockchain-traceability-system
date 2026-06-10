"""
通知系统 - 支持多种通知方式
包括：系统内通知、邮件通知、WebSocket 实时推送
"""

import json
import time
import threading
import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ===== 通知类型 =====
class NotificationType(Enum):
    """通知类型"""
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'
    SYSTEM = 'system'


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


# ===== 通知模型 =====
class Notification:
    """通知对象"""

    def __init__(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Dict = None
    ):
        self.id = f"notif_{int(time.time() * 1000)}"
        self.user_id = user_id
        self.title = title
        self.message = message
        self.type = notification_type
        self.priority = priority
        self.data = data or {}
        self.created_at = datetime.now()
        self.read = False

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type.value,
            'priority': self.priority.value,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'read': self.read
        }


# ===== 通知存储 =====
class NotificationStore:
    """通知存储（内存）"""

    def __init__(self):
        self.notifications = {}  # user_id -> [Notification]
        self.lock = threading.Lock()

    def add(self, notification: Notification) -> None:
        """添加通知"""
        with self.lock:
            user_id = notification.user_id
            if user_id not in self.notifications:
                self.notifications[user_id] = []

            self.notifications[user_id].append(notification)

            # 保持最新100条
            if len(self.notifications[user_id]) > 100:
                self.notifications[user_id] = self.notifications[user_id][-100:]

    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 20
    ) -> List[Dict]:
        """获取用户通知"""
        with self.lock:
            notifications = self.notifications.get(user_id, [])

            if unread_only:
                notifications = [n for n in notifications if not n.read]

            # 按时间倒序
            notifications = sorted(
                notifications,
                key=lambda n: n.created_at,
                reverse=True
            )

            return [n.to_dict() for n in notifications[:limit]]

    def mark_as_read(self, user_id: int, notification_id: str) -> bool:
        """标记为已读"""
        with self.lock:
            notifications = self.notifications.get(user_id, [])
            for notif in notifications:
                if notif.id == notification_id:
                    notif.read = True
                    return True
            return False

    def mark_all_as_read(self, user_id: int) -> int:
        """标记所有为已读"""
        with self.lock:
            notifications = self.notifications.get(user_id, [])
            count = 0
            for notif in notifications:
                if not notif.read:
                    notif.read = True
                    count += 1
            return count

    def get_unread_count(self, user_id: int) -> int:
        """获取未读数量"""
        with self.lock:
            notifications = self.notifications.get(user_id, [])
            return sum(1 for n in notifications if not n.read)


# ===== 邮件通知器 =====
class EmailNotifier:
    """邮件通知器"""

    def __init__(self, smtp_config: Dict = None):
        self.smtp_config = smtp_config or {}
        self.enabled = smtp_config is not None

        if self.enabled:
            logger.info("Email notifier initialized")
        else:
            logger.info("Email notifier disabled (no SMTP config)")

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """发送邮件"""
        if not self.enabled:
            logger.debug(f"Email simulation: To={to}, Subject={subject}")
            return True

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config.get('from_address')
            msg['To'] = to

            if html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')

            msg.attach(part)

            # 发送邮件
            with smtplib.SMTP(
                self.smtp_config.get('host'),
                self.smtp_config.get('port', 587)
            ) as server:
                server.starttls()
                server.login(
                    self.smtp_config.get('username'),
                    self.smtp_config.get('password')
                )
                server.send_message(msg)

            logger.info(f"Email sent to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def send_notification_email(
        self,
        to: str,
        notification: Notification
    ) -> bool:
        """发送通知邮件"""
        subject = f"[区块链溯源系统] {notification.title}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white; padding: 20px; border-radius: 10px;">
                    <h2>🔔 {notification.title}</h2>
                </div>
                <div style="background: #f9fafb; padding: 20px; margin-top: 20px; border-radius: 10px;">
                    <p style="font-size: 16px; line-height: 1.6;">
                        {notification.message}
                    </p>
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                    <p style="color: #6b7280; font-size: 14px;">
                        通知类型: <strong>{notification.type.value}</strong><br>
                        优先级: <strong>{notification.priority.name}</strong><br>
                        时间: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
                <div style="text-align: center; margin-top: 20px; color: #9ca3af;">
                    <p>这是一封自动发送的邮件，请勿回复</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to, subject, html_body, html=True)


# ===== 通知管理器 =====
class NotificationManager:
    """通知管理器"""

    def __init__(self, db, message_queue=None, email_config=None):
        self.db = db
        self.store = NotificationStore()
        self.message_queue = message_queue
        self.email_notifier = EmailNotifier(email_config)

    def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Dict = None,
        send_email: bool = False
    ) -> Notification:
        """发送通知"""
        # 创建通知
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            data=data
        )

        # 存储通知
        self.store.add(notification)

        # 通过消息队列发布实时通知
        if self.message_queue:
            self.message_queue.publish(
                f'user_notifications_{user_id}',
                notification.to_dict()
            )

        # 发送邮件（异步）
        if send_email:
            user_email = self._get_user_email(user_id)
            if user_email:
                threading.Thread(
                    target=self.email_notifier.send_notification_email,
                    args=(user_email, notification),
                    daemon=True
                ).start()

        logger.info(f"Notification sent to user {user_id}: {title}")
        return notification

    def _get_user_email(self, user_id: int) -> Optional[str]:
        """获取用户邮箱"""
        cursor = self.db.cursor()
        cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        return result['email'] if result else None

    def get_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 20
    ) -> List[Dict]:
        """获取用户通知列表"""
        return self.store.get_user_notifications(user_id, unread_only, limit)

    def mark_as_read(self, user_id: int, notification_id: str) -> bool:
        """标记为已读"""
        return self.store.mark_as_read(user_id, notification_id)

    def mark_all_as_read(self, user_id: int) -> int:
        """标记所有为已读"""
        return self.store.mark_all_as_read(user_id)

    def get_unread_count(self, user_id: int) -> int:
        """获取未读数量"""
        return self.store.get_unread_count(user_id)

    # ===== 业务通知快捷方法 =====

    def notify_product_registered(self, user_id: int, product_id: str):
        """产品注册通知"""
        self.send_notification(
            user_id=user_id,
            title='产品注册成功',
            message=f'产品 {product_id} 已成功注册到区块链',
            notification_type=NotificationType.SUCCESS,
            data={'product_id': product_id}
        )

    def notify_product_transferred(
        self,
        from_user_id: int,
        to_user_id: int,
        product_id: str
    ):
        """产品转移通知"""
        # 通知发送方
        self.send_notification(
            user_id=from_user_id,
            title='产品已转让',
            message=f'产品 {product_id} 已成功转让',
            notification_type=NotificationType.INFO,
            data={'product_id': product_id}
        )

        # 通知接收方
        self.send_notification(
            user_id=to_user_id,
            title='收到新产品',
            message=f'您收到了产品 {product_id}',
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.HIGH,
            data={'product_id': product_id},
            send_email=True
        )

    def notify_quality_check_completed(
        self,
        user_id: int,
        product_id: str,
        result: str
    ):
        """质检完成通知"""
        is_pass = result == 'pass'
        self.send_notification(
            user_id=user_id,
            title='质检完成',
            message=f'产品 {product_id} 质检结果: {"合格" if is_pass else "不合格"}',
            notification_type=NotificationType.SUCCESS if is_pass else NotificationType.WARNING,
            data={'product_id': product_id, 'result': result}
        )

    def notify_system_alert(self, user_id: int, message: str):
        """系统警告通知"""
        self.send_notification(
            user_id=user_id,
            title='系统警告',
            message=message,
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            send_email=True
        )


# ===== 批量通知 =====
class BulkNotifier:
    """批量通知器"""

    def __init__(self, notification_manager: NotificationManager):
        self.manager = notification_manager

    def notify_all_users(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        user_ids: List[int] = None
    ):
        """通知所有用户或指定用户列表"""
        if user_ids is None:
            # 从数据库获取所有用户ID
            cursor = self.manager.db.cursor()
            cursor.execute('SELECT id FROM users')
            user_ids = [row['id'] for row in cursor.fetchall()]

        logger.info(f"Sending bulk notification to {len(user_ids)} users")

        for user_id in user_ids:
            try:
                self.manager.send_notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {str(e)}")

    def notify_by_role(
        self,
        role: str,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM
    ):
        """按角色通知"""
        cursor = self.manager.db.cursor()
        cursor.execute('SELECT id FROM users WHERE role = ?', (role,))
        user_ids = [row['id'] for row in cursor.fetchall()]

        self.notify_all_users(title, message, notification_type, user_ids)


# ===== 导出 =====
__all__ = [
    'NotificationManager',
    'NotificationType',
    'NotificationPriority',
    'BulkNotifier',
    'EmailNotifier'
]
