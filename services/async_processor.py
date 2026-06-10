"""
异步任务处理 API - 处理消息队列中的任务
"""

import logging
from services.message_queue import MessageQueueFactory, TaskWorker
from models.traceability import register_product, transfer_ownership, add_quality_check, add_logistics
from services.notifications import NotificationManager

logger = logging.getLogger(__name__)


class AsyncTaskProcessor:
    """异步任务处理器"""

    def __init__(self, mq=None, notification_manager=None):
        self.mq = mq or MessageQueueFactory.get_instance()
        self.notification_manager = notification_manager

    def start_workers(self):
        """启动异步任务工作器"""
        # 产品注册工作器
        product_worker = TaskWorker(
            'product_registration',
            self.mq,
            num_workers=3
        )
        product_worker.register_handler('register_product', self._handle_register_product)
        product_worker.start()
        logger.info("Product registration worker started")

        # 产品转移工作器
        transfer_worker = TaskWorker(
            'product_transfer',
            self.mq,
            num_workers=3
        )
        transfer_worker.register_handler('transfer_ownership', self._handle_transfer_ownership)
        transfer_worker.start()
        logger.info("Product transfer worker started")

        # 质检工作器
        quality_worker = TaskWorker(
            'quality_checks',
            self.mq,
            num_workers=2
        )
        quality_worker.register_handler('quality_check', self._handle_quality_check)
        quality_worker.start()
        logger.info("Quality check worker started")

        # 物流工作器
        logistics_worker = TaskWorker(
            'logistics',
            self.mq,
            num_workers=4
        )
        logistics_worker.register_handler('add_logistics', self._handle_add_logistics)
        logistics_worker.start()
        logger.info("Logistics worker started")

        return [product_worker, transfer_worker, quality_worker, logistics_worker]

    def _handle_register_product(self, data):
        """处理产品注册任务"""
        try:
            product_id, block_hash = register_product(
                name=data['name'],
                batch_number=data['batch_number'],
                manufacturer_id=data['manufacturer_id'],
                production_date=data['production_date']
            )

            logger.info(f"Product registered successfully: {product_id}")

            # 发送通知
            if self.notification_manager:
                self.notification_manager.notify_product_registered(
                    data['manufacturer_id'],
                    product_id
                )

            # 发布事件
            self.mq.publish('product_registered', {
                'product_id': product_id,
                'block_hash': block_hash,
                'manufacturer_id': data['manufacturer_id']
            })

            return {
                'success': True,
                'product_id': product_id,
                'block_hash': block_hash
            }

        except Exception as e:
            logger.error(f"Failed to register product: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _handle_transfer_ownership(self, data):
        """处理所有权转移任务"""
        try:
            block_hash = transfer_ownership(
                product_id=data['product_id'],
                from_user_id=data['from_user_id'],
                to_user_id=data['to_user_id'],
                location=data.get('location')
            )

            logger.info(f"Product transferred: {data['product_id']}")

            # 发送通知
            if self.notification_manager:
                self.notification_manager.notify_product_transferred(
                    data['from_user_id'],
                    data['to_user_id'],
                    data['product_id']
                )

            # 发布事件
            self.mq.publish('product_transferred', {
                'product_id': data['product_id'],
                'from_user_id': data['from_user_id'],
                'to_user_id': data['to_user_id'],
                'location': data.get('location'),
                'block_hash': block_hash
            })

            return {
                'success': True,
                'block_hash': block_hash
            }

        except Exception as e:
            logger.error(f"Failed to transfer product: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _handle_quality_check(self, data):
        """处理质检任务"""
        try:
            block_hash = add_quality_check(
                product_id=data['product_id'],
                inspector_id=data['inspector_id'],
                result=data['result'],
                notes=data['notes']
            )

            logger.info(f"Quality check completed: {data['product_id']}")

            # 发送通知
            if self.notification_manager:
                self.notification_manager.notify_quality_check_completed(
                    data['inspector_id'],
                    data['product_id'],
                    data['result']
                )

            # 发布事件
            self.mq.publish('quality_check_completed', {
                'product_id': data['product_id'],
                'result': data['result'],
                'block_hash': block_hash
            })

            return {
                'success': True,
                'block_hash': block_hash
            }

        except Exception as e:
            logger.error(f"Failed to add quality check: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _handle_add_logistics(self, data):
        """处理物流信息任务"""
        try:
            block_hash = add_logistics(
                product_id=data['product_id'],
                user_id=data['user_id'],
                location=data['location'],
                status=data['status']
            )

            logger.info(f"Logistics added: {data['product_id']}")

            # 发布事件
            self.mq.publish('logistics_updated', {
                'product_id': data['product_id'],
                'location': data['location'],
                'status': data['status'],
                'block_hash': block_hash
            })

            return {
                'success': True,
                'block_hash': block_hash
            }

        except Exception as e:
            logger.error(f"Failed to add logistics: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# 导出
__all__ = ['AsyncTaskProcessor']
