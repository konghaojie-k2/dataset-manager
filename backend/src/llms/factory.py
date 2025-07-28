"""
LLM工厂模块

负责根据配置创建和管理 ChatOpenAI 实例
"""

from typing import Dict
from langchain_openai import ChatOpenAI
from loguru import logger

from ..config import get_settings, LLMType

# LLM实例缓存
_llm_cache: Dict[LLMType, ChatOpenAI] = {}


def _create_llm_by_type(llm_type: LLMType) -> ChatOpenAI:
    """根据类型创建LLM实例
    
    Args:
        llm_type: LLM类型
        
    Returns:
        ChatOpenAI: LLM实例
        
    Raises:
        ValueError: 当API密钥未配置或LLM类型未知时
    """
    settings = get_settings()
    
    # 检查API密钥
    if not settings.deepseek_api_key:
        raise ValueError("DeepSeek API密钥未配置，请设置 DATASET_MANAGER_DEEPSEEK_API_KEY 环境变量")
    
    # 根据类型选择模型
    model_map = {
        LLMType.REASONING: settings.reasoning_model,
        LLMType.BASIC: settings.basic_model,
        LLMType.VISION: settings.vision_model,
    }
    
    model_name = model_map.get(llm_type)
    if not model_name:
        raise ValueError(f"未知的LLM类型: {llm_type}")
    
    # 创建ChatOpenAI实例
    llm_config = {
        "model": model_name,
        "api_key": settings.deepseek_api_key,
        "base_url": settings.deepseek_base_url,
        "temperature": settings.llm_temperature,
    }
    
    # 添加可选参数
    if settings.llm_max_tokens:
        llm_config["max_tokens"] = settings.llm_max_tokens
    
    logger.info(f"创建LLM实例: {llm_type.value} -> {model_name}")
    return ChatOpenAI(**llm_config)


def get_llm_by_type(llm_type: LLMType) -> ChatOpenAI:
    """根据类型获取LLM实例（带缓存）
    
    Args:
        llm_type: LLM类型
        
    Returns:
        ChatOpenAI: LLM实例
    """
    if llm_type in _llm_cache:
        return _llm_cache[llm_type]
    
    llm = _create_llm_by_type(llm_type)
    _llm_cache[llm_type] = llm
    return llm


def clear_llm_cache():
    """清空LLM缓存"""
    global _llm_cache
    _llm_cache.clear()
    logger.info("LLM缓存已清空")


def get_cache_info() -> Dict[str, str]:
    """获取缓存信息
    
    Returns:
        Dict[str, str]: 缓存状态信息
    """
    return {
        "cached_types": [llm_type.value for llm_type in _llm_cache.keys()],
        "cache_size": len(_llm_cache)
    } 