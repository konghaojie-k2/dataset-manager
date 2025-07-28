"""
语言模型管理模块

基于配置驱动的方式创建和管理 ChatOpenAI 实例
"""

# 从工厂模块导入核心功能
from .factory import get_llm_by_type, clear_llm_cache, get_cache_info

# 从高级接口模块导入便捷函数
from .llms import (
    get_reasoning_llm,
    get_basic_llm, 
    get_vision_llm,
    get_default_llm
)

# 从配置模块导入类型
from ..config import LLMType

__all__ = [
    # 核心工厂函数
    "get_llm_by_type",
    "clear_llm_cache",
    "get_cache_info",
    
    # 高级接口
    "get_reasoning_llm", 
    "get_basic_llm",
    "get_vision_llm",
    "get_default_llm",
    
    # 类型
    "LLMType",
] 