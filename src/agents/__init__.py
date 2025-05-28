"""
智能代理模块

参考 DeerFlow 的简洁设计，提供统一的 Agent 创建接口
"""

from .factory import (
    create_agent,
    create_metadata_agent,
    create_analysis_agent,
    create_insight_agent,
    create_basic_agent,
    get_agent,
    get_available_agents,
    AGENT_LLM_MAP,
    AGENT_CREATORS
)

__all__ = [
    "create_agent",
    "create_metadata_agent",
    "create_analysis_agent", 
    "create_insight_agent",
    "create_basic_agent",
    "get_agent",
    "get_available_agents",
    "AGENT_LLM_MAP",
    "AGENT_CREATORS"
] 