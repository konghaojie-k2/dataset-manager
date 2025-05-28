"""
LLM高级接口模块

提供便捷的LLM获取接口，封装了工厂模块的复杂性
"""

from langchain_openai import ChatOpenAI

from ..config import LLMType
from .factory import get_llm_by_type


def get_reasoning_llm() -> ChatOpenAI:
    """获取推理模型（用于复杂分析任务）
    
    Returns:
        ChatOpenAI: 推理模型实例
    """
    return get_llm_by_type(LLMType.REASONING)


def get_basic_llm() -> ChatOpenAI:
    """获取基础模型（用于一般任务）
    
    Returns:
        ChatOpenAI: 基础模型实例
    """
    return get_llm_by_type(LLMType.BASIC)


def get_vision_llm() -> ChatOpenAI:
    """获取视觉模型（用于图像分析）
    
    Returns:
        ChatOpenAI: 视觉模型实例
    """
    return get_llm_by_type(LLMType.VISION)


def get_default_llm() -> ChatOpenAI:
    """获取默认LLM实例（基础模型）
    
    Returns:
        ChatOpenAI: 默认LLM实例
    """
    return get_basic_llm() 