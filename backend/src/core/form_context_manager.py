#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""表单上下文管理器"""

from typing import Dict, List, Any
from loguru import logger


class FormContextManager:
    """表单上下文管理器

    职责：
    1. 从消息和意图中提取实体
    2. 维护会话上下文
    3. 支持智能预填
    """

    def __init__(self):
        logger.info("表单上下文管理器初始化完成")

    def extract_entities_from_message(
        self,
        message: str,
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从消息和意图中提取实体

        Args:
            message: 用户消息
            intent: 意图分析结果

        Returns:
            Dict: 提取的实体字典
        """
        entities = {}

        # 从filters中提取
        filters = intent.get("filters", {})
        for key, value in filters.items():
            entities[key] = value

        logger.info(f"提取实体: {entities}")
        return entities

    def update_session_context(
        self,
        session: Any,
        entities: Dict[str, Any]
    ):
        """更新会话上下文

        Args:
            session: 聊天会话对象
            entities: 提取的实体
        """
        if not hasattr(session, 'current_context') or not session.current_context:
            session.current_context = {}

        # 合并实体（新实体覆盖旧实体）
        mentioned = session.current_context.get("mentioned_entities", {})
        mentioned.update(entities)
        session.current_context["mentioned_entities"] = mentioned

        # 更新最近搜索
        recent = session.current_context.get("recent_searches", [])
        recent.append(entities)
        session.current_context["recent_searches"] = recent[-5:]  # 只保留最近5次

        logger.debug(f"会话上下文已更新: mentioned_entities={list(mentioned.keys())}")

    def get_prefill_value(
        self,
        field_name: str,
        session_context: Dict[str, Any]
    ) -> Any:
        """获取字段的预填值

        Args:
            field_name: 字段名称
            session_context: 会话上下文

        Returns:
            Any: 预填值，如果没有则返回None
        """
        if not session_context:
            return None

        # 优先从已提实体中获取
        mentioned_entities = session_context.get("mentioned_entities", {})
        if field_name in mentioned_entities:
            return mentioned_entities[field_name]

        # 从最近搜索中获取
        recent_searches = session_context.get("recent_searches", [])
        for search in reversed(recent_searches):  # 最优先
            if field_name in search:
                return search[field_name]

        return None
