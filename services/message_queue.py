"""
消息队列系统 - 基于 Redis
提供异步任务处理、事件驱动架构和系统解耦
"""

import json
import time
import threading
import logging
from typing import Callable, Dict, Any, Optional
from functools import wraps
from queue import Queue
import pickle

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: redis-py not installed. Using fallback queue system.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== 消息队列抽象基类 =====
class MessageQueueBase:
    """消息队列抽象基类"""

    def publish(self, channel: str, message: Dict) -> bool:
        """发布消息"""
        raise NotImplementedError

    def subscribe(self, channel: str, handler: Callable) -> None:
        """订阅频道"""
        raise NotImplementedError

    def push_task(self, queue_name: str, task: Dict) -> bool:
        """推送任务到队列"""
        raise NotImplementedError

    def pop_task(self, queue_name: str, timeout: int = 0) -> Optional[Dict]:
        """从队列弹出任务"""
        raise NotImplementedError

    def get_queue_size(self, queue_name: str) -> int:
        """获取队列大小"""
        raise NotImplementedError


# ===== Redis 消息队列实现 =====
class RedisMessageQueue(MessageQueueBase):
    """基于 Redis 的消息队列"""

    def __init__(self, host='localhost', port=6379, db=0, password=None):
        if not REDIS_AVAILABLE:
            raise RuntimeError("redis-py is not installed")

        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False  # 使用二进制模式
        )

        self.pubsub = self.redis_client.pubsub()
        self.subscribers = {}
        self.running = False
        self.listener_thread = None

        # 测试连接
        try:
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except redis.ConnectionError:
            logger.error(f"Failed to connect to Redis at {host}:{port}")
            raise

    def publish(self, channel: str, message: Dict) -> bool:
        """发布消息到频道"""
        try:
            serialized = json.dumps(message)
            result = self.redis_client.publish(channel, serialized)
            logger.debug(f"Published to {channel}: {message}")
            return result > 0
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {str(e)}")
            return False

    def subscribe(self, channel: str, handler: Callable) -> None:
        """订阅频道"""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
            self.pubsub.subscribe(channel)

        self.subscribers[channel].append(handler)
        logger.info(f"Subscribed to channel: {channel}")

        # 启动监听线程
        if not self.running:
            self._start_listener()

    def _start_listener(self):
        """启动消息监听线程"""
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()
        logger.info("Message listener started")

    def _listen(self):
        """监听消息"""
        for message in self.pubsub.listen():
            if not self.running:
                break

            if message['type'] == 'message':
                channel = message['channel'].decode('utf-8')
                data = message['data']

                try:
                    parsed_data = json.loads(data)
                    handlers = self.subscribers.get(channel, [])

                    for handler in handlers:
                        try:
                            handler(parsed_data)
                        except Exception as e:
                            logger.error(f"Error in handler for {channel}: {str(e)}")
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in message from {channel}")

    def push_task(self, queue_name: str, task: Dict) -> bool:
        """推送任务到队列"""
        try:
            serialized = pickle.dumps(task)
            self.redis_client.rpush(queue_name, serialized)
            logger.debug(f"Pushed task to {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Error pushing task to {queue_name}: {str(e)}")
            return False

    def pop_task(self, queue_name: str, timeout: int = 0) -> Optional[Dict]:
        """从队列弹出任务（阻塞式）"""
        try:
            if timeout > 0:
                result = self.redis_client.blpop(queue_name, timeout=timeout)
            else:
                result = self.redis_client.lpop(queue_name)

            if result:
                if isinstance(result, tuple):
                    _, data = result
                else:
                    data = result

                task = pickle.loads(data)
                logger.debug(f"Popped task from {queue_name}")
                return task
            return None
        except Exception as e:
            logger.error(f"Error popping task from {queue_name}: {str(e)}")
            return None

    def get_queue_size(self, queue_name: str) -> int:
        """获取队列大小"""
        try:
            return self.redis_client.llen(queue_name)
        except Exception as e:
            logger.error(f"Error getting queue size for {queue_name}: {str(e)}")
            return 0

    def stop(self):
        """停止监听"""
        self.running = False
        if self.pubsub:
            self.pubsub.close()
        logger.info("Message queue stopped")


# ===== 内存消息队列实现（降级方案）=====
class InMemoryMessageQueue(MessageQueueBase):
    """基于内存的消息队列（降级方案）"""

    def __init__(self):
        self.channels = {}
        self.queues = {}
        self.lock = threading.Lock()
        logger.info("Using in-memory message queue (fallback)")

    def publish(self, channel: str, message: Dict) -> bool:
        """发布消息"""
        with self.lock:
            if channel in self.channels:
                for handler in self.channels[channel]:
                    try:
                        # 异步执行处理器
                        threading.Thread(target=handler, args=(message,), daemon=True).start()
                    except Exception as e:
                        logger.error(f"Error in handler for {channel}: {str(e)}")
                return True
            return False

    def subscribe(self, channel: str, handler: Callable) -> None:
        """订阅频道"""
        with self.lock:
            if channel not in self.channels:
                self.channels[channel] = []
            self.channels[channel].append(handler)
            logger.info(f"Subscribed to channel: {channel}")

    def push_task(self, queue_name: str, task: Dict) -> bool:
        """推送任务"""
        with self.lock:
            if queue_name not in self.queues:
                self.queues[queue_name] = Queue()
            self.queues[queue_name].put(task)
            return True

    def pop_task(self, queue_name: str, timeout: int = 0) -> Optional[Dict]:
        """弹出任务"""
        with self.lock:
            if queue_name not in self.queues:
                self.queues[queue_name] = Queue()

        queue = self.queues[queue_name]
        try:
            if timeout > 0:
                return queue.get(timeout=timeout)
            else:
                return queue.get_nowait()
        except:
            return None

    def get_queue_size(self, queue_name: str) -> int:
        """获取队列大小"""
        with self.lock:
            if queue_name in self.queues:
                return self.queues[queue_name].qsize()
            return 0


# ===== 消息队列工厂 =====
class MessageQueueFactory:
    """消息队列工厂"""

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, config: Dict = None) -> MessageQueueBase:
        """获取消息队列实例（单例）"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    config = config or {}

                    # 尝试使用 Redis
                    if REDIS_AVAILABLE and config.get('use_redis', True):
                        try:
                            cls._instance = RedisMessageQueue(
                                host=config.get('redis_host', 'localhost'),
                                port=config.get('redis_port', 6379),
                                db=config.get('redis_db', 0),
                                password=config.get('redis_password', None)
                            )
                        except Exception as e:
                            logger.warning(f"Failed to initialize Redis MQ: {str(e)}")
                            cls._instance = InMemoryMessageQueue()
                    else:
                        cls._instance = InMemoryMessageQueue()

        return cls._instance


# ===== 任务工作器 =====
class TaskWorker:
    """任务工作器 - 从队列中消费任务"""

    def __init__(self, queue_name: str, mq: MessageQueueBase, num_workers: int = 3):
        self.queue_name = queue_name
        self.mq = mq
        self.num_workers = num_workers
        self.workers = []
        self.running = False
        self.handlers = {}

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """注册任务处理器"""
        self.handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    def start(self):
        """启动工作器"""
        self.running = True

        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        logger.info(f"Started {self.num_workers} workers for queue: {self.queue_name}")

    def _worker_loop(self, worker_id: int):
        """工作器循环"""
        logger.info(f"Worker {worker_id} started for queue: {self.queue_name}")

        while self.running:
            try:
                # 从队列获取任务（阻塞式，超时5秒）
                task = self.mq.pop_task(self.queue_name, timeout=5)

                if task:
                    task_type = task.get('type')
                    task_id = task.get('id', 'unknown')

                    logger.info(f"Worker {worker_id} processing task {task_id} of type {task_type}")

                    # 执行任务
                    handler = self.handlers.get(task_type)
                    if handler:
                        try:
                            result = handler(task.get('data', {}))
                            logger.info(f"Worker {worker_id} completed task {task_id}")

                            # 发布任务完成事件
                            self.mq.publish('task_completed', {
                                'task_id': task_id,
                                'task_type': task_type,
                                'result': result,
                                'worker_id': worker_id,
                                'timestamp': time.time()
                            })
                        except Exception as e:
                            logger.error(f"Worker {worker_id} failed task {task_id}: {str(e)}")

                            # 发布任务失败事件
                            self.mq.publish('task_failed', {
                                'task_id': task_id,
                                'task_type': task_type,
                                'error': str(e),
                                'worker_id': worker_id,
                                'timestamp': time.time()
                            })
                    else:
                        logger.warning(f"No handler for task type: {task_type}")

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
                time.sleep(1)

        logger.info(f"Worker {worker_id} stopped")

    def stop(self):
        """停止工作器"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=10)
        logger.info(f"Stopped all workers for queue: {self.queue_name}")


# ===== 任务调度器 =====
class TaskScheduler:
    """任务调度器 - 提交任务到队列"""

    def __init__(self, mq: MessageQueueBase):
        self.mq = mq

    def submit_task(self, queue_name: str, task_type: str, data: Dict, task_id: str = None) -> str:
        """提交任务"""
        if task_id is None:
            task_id = f"{task_type}_{time.time()}"

        task = {
            'id': task_id,
            'type': task_type,
            'data': data,
            'submitted_at': time.time()
        }

        success = self.mq.push_task(queue_name, task)

        if success:
            logger.info(f"Task {task_id} submitted to queue {queue_name}")
            return task_id
        else:
            logger.error(f"Failed to submit task {task_id}")
            raise RuntimeError("Failed to submit task")

    def get_queue_status(self, queue_name: str) -> Dict:
        """获取队列状态"""
        return {
            'queue_name': queue_name,
            'size': self.mq.get_queue_size(queue_name),
            'timestamp': time.time()
        }


# ===== 装饰器：异步任务 =====
def async_task(queue_name: str = 'default', task_type: str = None):
    """异步任务装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取消息队列
            mq = MessageQueueFactory.get_instance()
            scheduler = TaskScheduler(mq)

            # 确定任务类型
            _task_type = task_type or func.__name__

            # 提交任务
            task_data = {
                'args': args,
                'kwargs': kwargs
            }

            task_id = scheduler.submit_task(queue_name, _task_type, task_data)

            return {
                'task_id': task_id,
                'status': 'submitted',
                'queue': queue_name
            }

        # 保存原始函数引用，供工作器使用
        wrapper._original_func = func
        wrapper._task_type = task_type or func.__name__

        return wrapper
    return decorator


# ===== 事件驱动系统 =====
class EventDrivenSystem:
    """事件驱动系统"""

    def __init__(self, mq: MessageQueueBase):
        self.mq = mq
        self.event_handlers = {}

    def on(self, event_type: str, handler: Callable) -> None:
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

            # 订阅事件频道
            self.mq.subscribe(f"event_{event_type}", self._handle_event)

        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event: {event_type}")

    def _handle_event(self, message: Dict):
        """处理事件"""
        event_type = message.get('type')
        event_data = message.get('data', {})

        handlers = self.event_handlers.get(event_type, [])

        for handler in handlers:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error handling event {event_type}: {str(e)}")

    def emit(self, event_type: str, data: Dict) -> None:
        """发射事件"""
        message = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }

        self.mq.publish(f"event_{event_type}", message)
        logger.info(f"Emitted event: {event_type}")


# ===== 导出 =====
__all__ = [
    'MessageQueueFactory',
    'TaskWorker',
    'TaskScheduler',
    'EventDrivenSystem',
    'async_task'
]
