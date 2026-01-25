#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
进度事件总线

用于连接 LangGraph Agent 的进度事件和 FastAPI SSE 端点。
Agent 工具调用 publish() 推送进度，SSE 端点调用 subscribe() 获取队列。

使用 asyncio.Queue 实现异步的发布-订阅模式。
"""

import asyncio
from typing import Dict, Optional, AsyncIterator
from loguru import logger
from datetime import datetime, timedelta


class ProgressEvent:
    """进度事件数据结构"""

    def __init__(
        self,
        dataset_id: str,
        current_step: str,
        progress: int,
        steps_completed: str,
        steps_remaining: Optional[str] = None,
        intermediate_result: Optional[str] = None,
        event_type: str = "analysis_progress"
    ):
        self.dataset_id = dataset_id
        self.current_step = current_step
        self.progress = progress
        self.steps_completed = steps_completed
        self.steps_remaining = steps_remaining or "无"
        self.intermediate_result = intermediate_result or "{}"
        self.event_type = event_type
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "type": self.event_type,
            "dataset_id": self.dataset_id,
            "current_step": self.current_step,
            "progress": self.progress,
            "steps_completed": self.steps_completed,
            "steps_remaining": self.steps_remaining,
            "intermediate_result": self.intermediate_result,
            "timestamp": self.timestamp.isoformat()
        }


class ProgressEventBus:
    """
    进度事件总线

    单例模式，管理所有数据集的进度事件队列。
    """

    _instance: Optional['ProgressEventBus'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 数据集ID -> 队列列表（支持多个订阅者）
        self._subscribers: Dict[str, list[asyncio.Queue]] = {}

    # 队列超时时间（秒）
        self._queue_timeout = 600  # 10分钟（增加超时时间）

        # 心跳间隔（秒）
        self._heartbeat_interval = 5  # 每5秒发送心跳

        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None

        self._initialized = True
        logger.info("[ProgressEventBus] 初始化完成")

    async def subscribe(self, dataset_id: str) -> asyncio.Queue:
        """
        订阅数据集的进度事件

        Args:
            dataset_id: 数据集ID

        Returns:
            asyncio.Queue: 事件队列
        """
        async with self._lock:
            if dataset_id not in self._subscribers:
                self._subscribers[dataset_id] = []

            queue: asyncio.Queue = asyncio.Queue()
            self._subscribers[dataset_id].append(queue)

            logger.info(f"[ProgressEventBus] 新订阅者: {dataset_id} (总订阅数: {len(self._subscribers[dataset_id])})")

            # 启动清理任务
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_inactive_subscribers())

            return queue

    async def unsubscribe(self, dataset_id: str, queue: asyncio.Queue):
        """
        取消订阅

        Args:
            dataset_id: 数据集ID
            queue: 要取消的队列
        """
        async with self._lock:
            if dataset_id in self._subscribers:
                try:
                    self._subscribers[dataset_id].remove(queue)
                    logger.info(f"[ProgressEventBus] 取消订阅: {dataset_id} (剩余订阅数: {len(self._subscribers[dataset_id])})")

                    # 如果没有订阅者了，删除该数据集的记录
                    if not self._subscribers[dataset_id]:
                        del self._subscribers[dataset_id]
                except ValueError:
                    logger.warning(f"[ProgressEventBus] 队列不在订阅列表中: {dataset_id}")

    async def publish(self, event: ProgressEvent):
        """
        发布进度事件到所有订阅者

        Args:
            event: 进度事件
        """
        async with self._lock:
            if event.dataset_id not in self._subscribers:
                # 没有订阅者，记录日志但不报错
                logger.warning(f"[ProgressEventBus] 无订阅者，事件丢弃: {event.dataset_id} (当前订阅的datasets: {list(self._subscribers.keys())})")
                return

            # 将事件放入所有订阅者的队列
            dead_queues = []
            subscriber_count = len(self._subscribers[event.dataset_id])
            for queue in self._subscribers[event.dataset_id]:
                try:
                    # 非阻塞 put，如果队列满了就丢弃
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning(f"[ProgressEventBus] 队列已满，事件丢弃: {event.dataset_id}")
                except Exception as e:
                    logger.error(f"[ProgressEventBus] 入队错误: {e}")
                    dead_queues.append(queue)

            # 清理失效的队列
            for dead_queue in dead_queues:
                try:
                    self._subscribers[event.dataset_id].remove(dead_queue)
                except ValueError:
                    pass

            logger.debug(f"[ProgressEventBus] 事件已发布: {event.dataset_id} - {event.current_step} ({event.progress}%) 到 {subscriber_count} 个订阅者")

    async def iter_events(self, dataset_id: str, queue: asyncio.Queue) -> AsyncIterator[ProgressEvent]:
        """
        迭代队列中的事件（用于 SSE 端点）

        Args:
            dataset_id: 数据集ID
            queue: 事件队列

        Yields:
            ProgressEvent: 进度事件
        """
        try:
            while True:
                try:
                    # 等待事件，带超时
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield event

                    # 如果事件进度为100，发送完成事件后结束
                    if event.progress >= 100:
                        logger.info(f"[ProgressEventBus] 分析完成，结束流: {dataset_id}")
                        break

                except asyncio.TimeoutError:
                    # 发送心跳事件
                    yield ProgressEvent(
                        dataset_id=dataset_id,
                        current_step="保持连接",
                        progress=-1,  # -1 表示心跳
                        steps_completed="",
                        event_type="heartbeat"
                    )
        except asyncio.CancelledError:
            logger.info(f"[ProgressEventBus] 流迭代被取消: {dataset_id}")
        except Exception as e:
            logger.error(f"[ProgressEventBus] 流迭代错误: {dataset_id} - {e}")
            raise

    async def _cleanup_inactive_subscribers(self):
        """
        定期清理不活跃的订阅者
        
        注意：不应该基于队列是否为空来判断订阅者是否活跃。
        队列为空只意味着暂时没有事件，不代表订阅者断开连接。
        订阅者应该通过 unsubscribe 方法主动取消订阅。
        """
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟检查一次（延长检查间隔）

                async with self._lock:
                    # 只清理明显失效的队列（例如队列已关闭的情况）
                    # 但不要仅仅因为队列为空就删除订阅者
                    # 订阅者应该通过 unsubscribe 方法主动取消订阅
                    
                    # 如果所有数据集都没有订阅者，停止清理任务
                    if not self._subscribers:
                        logger.debug("[ProgressEventBus] 所有订阅者已清理，停止清理任务")
                        break

            except asyncio.CancelledError:
                logger.info("[ProgressEventBus] 清理任务被取消")
                break
            except Exception as e:
                logger.error(f"[ProgressEventBus] 清理任务错误: {e}")

    async def shutdown(self):
        """
        关闭事件总线，清理所有资源
        """
        logger.info("[ProgressEventBus] 正在关闭...")

        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            self._subscribers.clear()

        logger.info("[ProgressEventBus] 已关闭")


# 全局单例
_progress_event_bus: Optional[ProgressEventBus] = None


def get_progress_event_bus() -> ProgressEventBus:
    """
    获取进度事件总线单例

    Returns:
        ProgressEventBus: 全局事件总线实例
    """
    global _progress_event_bus
    if _progress_event_bus is None:
        _progress_event_bus = ProgressEventBus()
    return _progress_event_bus
