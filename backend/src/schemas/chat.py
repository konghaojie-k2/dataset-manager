#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""聊天相关的数据结构定义"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ResponseType(str, Enum):
    """响应类型"""
    SEARCH_RESULTS = "search_results"  # 搜索结果
    CLARIFICATION_NEEDED = "clarification_needed"  # 需要澄清（生成A2UI表单）
    ERROR = "error"  # 错误
    INFO = "info"  # 信息提示


class ChatMessage(BaseModel):
    """聊天消息"""
    id: str = Field(description="消息ID")
    role: MessageRole = Field(description="消息角色")
    content: str = Field(description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    session_id: str = Field(description="会话ID")

    # 可选的附加数据
    datasets: Optional[List[Dict[str, Any]]] = Field(None, description="关联的数据集")
    a2ui_form: Optional[Dict[str, Any]] = Field(None, description="A2UI表单JSON")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class SearchIntent(BaseModel):
    """搜索意图分析结果"""
    search_query: str = Field(description="提炼后的搜索查询")
    entities: Dict[str, Any] = Field(default_factory=dict, description="提取的实体")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    needs_clarification: bool = Field(default=False, description="是否需要澄清")
    clarification_reason: Optional[str] = Field(None, description="需要澄清的原因")
    confidence: float = Field(default=0.0, description="置信度(0-1)")


class ChatResponse(BaseModel):
    """聊天响应"""
    type: ResponseType = Field(description="响应类型")
    message: str = Field(description="响应消息")
    datasets: List[Dict[str, Any]] = Field(default_factory=list, description="搜索到的数据集")
    a2ui_form: Optional[Dict[str, Any]] = Field(None, description="A2UI表单（如需澄清）")
    session_id: str = Field(description="会话ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

    # 可选的元数据
    total_results: Optional[int] = Field(None, description="总结果数")
    search_query: Optional[str] = Field(None, description="使用的搜索查询")
    relevance_scores: Optional[List[float]] = Field(None, description="每个数据集的相关性评分")


class ChatSession(BaseModel):
    """聊天会话"""
    session_id: str = Field(description="会话ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="消息历史")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    # 搜索上下文
    search_history: List[Dict[str, Any]] = Field(default_factory=list, description="搜索历史")
    current_context: Dict[str, Any] = Field(default_factory=dict, description="当前上下文")

    # 用户偏好
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好")

    def add_message(self, role: MessageRole, content: str, **kwargs):
        """添加消息到会话"""
        message = ChatMessage(
            id=f"{self.session_id}_{len(self.messages)}",
            role=role,
            content=content,
            session_id=self.session_id,
            **kwargs
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message

    def add_search_result(self, search_query: str, datasets: List[Dict[str, Any]]):
        """添加搜索结果到历史"""
        self.search_history.append({
            "query": search_query,
            "count": len(datasets),
            "dataset_ids": [ds.get("id") for ds in datasets],
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    def get_recent_messages(self, n: int = 5) -> List[ChatMessage]:
        """获取最近N条消息"""
        return self.messages[-n:] if n > 0 else []

    def update_context(self, key: str, value: Any):
        """更新上下文"""
        self.current_context[key] = value
        self.updated_at = datetime.now()


class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: str = Field(description="会话ID（如新会话可传入'new'）")
    content: str = Field(description="用户消息内容")
    timestamp: Optional[datetime] = Field(None, description="时间戳（可选）")


class A2UIField(BaseModel):
    """A2UI字段定义"""
    name: str = Field(description="字段名称")
    type: str = Field(description="字段类型: text|select|multiselect|range|date_range|toggle")
    label: str = Field(description="显示标签")
    placeholder: Optional[str] = Field(None, description="占位符文本")
    options: Optional[List[Dict[str, str]]] = Field(None, description="选项（用于select/multiselect）")
    required: bool = Field(default=False, description="是否必填")
    validation: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    default: Any = Field(None, description="默认值")


class A2UIAction(BaseModel):
    """A2UI操作定义"""
    id: str = Field(description="操作ID")
    type: str = Field(description="操作类型: submit|button|cancel")
    label: str = Field(description="显示标签")
    primary: bool = Field(default=False, description="是否为主要操作")


class A2UISchema(BaseModel):
    """A2UI表单Schema"""
    version: str = Field(default="1.0", description="版本")
    form_type: str = Field(description="表单类型: search_refinement|filter_builder|preference_setting")
    title: str = Field(description="表单标题")
    description: str = Field(description="表单描述")
    fields: List[A2UIField] = Field(description="字段列表")
    actions: List[A2UIAction] = Field(description="操作列表")


class A2UIFormSubmission(BaseModel):
    """A2UI表单提交"""
    form_id: str = Field(description="表单ID")
    session_id: str = Field(description="会话ID")
    data: Dict[str, Any] = Field(description="表单数据")


class DatasetSearchRequest(BaseModel):
    """数据集搜索请求"""
    query: str = Field(description="搜索查询")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    top_k: int = Field(default=10, description="返回结果数量")
    session_id: Optional[str] = Field(None, description="会话ID（可选）")
