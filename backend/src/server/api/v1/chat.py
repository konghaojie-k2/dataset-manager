#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""聊天API路由"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from src.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    FormSubmitRequest
)
from src.core.chat_service import ChatService
from src.server.dependencies import get_dataset_service

# 创建路由器
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# 全局聊天服务实例
_chat_service: ChatService = None


def get_chat_service() -> ChatService:
    """获取聊天服务实例

    Returns:
        ChatService: 聊天服务实例

    Raises:
        HTTPException: 当服务未初始化时
    """
    global _chat_service
    if _chat_service is None:
        dataset_service = get_dataset_service()
        _chat_service = ChatService(dataset_service)
        logger.info("聊天服务实例已初始化")

    return _chat_service


@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """发送聊天消息

    Args:
        request: 聊天请求
        chat_service: 聊天服务

    Returns:
        ChatResponse: 聊天响应
    """
    try:
        logger.info(f"收到聊天消息: session_id={request.session_id}, content={request.content[:50]}...")

        response = await chat_service.process_message(request)

        logger.info(f"聊天响应: type={response.type}, datasets={len(response.datasets)}")
        return response

    except Exception as e:
        logger.error(f"处理聊天消息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取聊天会话历史

    Args:
        session_id: 会话ID
        chat_service: 聊天服务

    Returns:
        dict: 消息历史
    """
    try:
        logger.info(f"获取会话历史: session_id={session_id}")

        messages = chat_service.get_session_history(session_id)

        return {
            "session_id": session_id,
            "messages": messages,
            "total": len(messages)
        }

    except Exception as e:
        logger.error(f"获取会话历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """清除聊天会话

    Args:
        session_id: 会话ID
        chat_service: 聊天服务

    Returns:
        dict: 成功消息
    """
    try:
        logger.info(f"清除会话: session_id={session_id}")

        chat_service.clear_session(session_id)

        return {
            "success": True,
            "message": "会话已清除",
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"清除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/form-submit", response_model=ChatResponse)
async def submit_form(
    request: FormSubmitRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """提交A2UI表单

    Args:
        request: 表单提交请求
        chat_service: 聊天服务

    Returns:
        ChatResponse: 聊天响应
    """
    try:
        logger.info(f"收到表单提交: session_id={request.session_id}, form_id={request.form_id}")

        response = await chat_service.submit_form(request.session_id, request.form_id, request.data)

        logger.info(f"表单提交响应: type={response.type}, datasets={len(response.datasets)}")
        return response

    except Exception as e:
        logger.error(f"处理表单提交失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
