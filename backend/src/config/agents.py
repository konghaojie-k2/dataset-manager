"""代理配置模块"""

from enum import Enum
from typing import Literal


class LLMType(str, Enum):
    """LLM类型枚举"""
    REASONING = "reasoning"  # 推理模型，用于复杂分析
    BASIC = "basic"         # 基础模型，用于一般任务
    VISION = "vision"       # 视觉模型，用于图像分析


# 类型别名
LLMTypeAlias = Literal["reasoning", "basic", "vision"] 