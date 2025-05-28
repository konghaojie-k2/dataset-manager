"""
提示模板模块 - 重构版本

提供基于 .md 文件的提示词模板系统，参考 DeerFlow 的设计模式
"""

from .loader import PromptLoader, prompt_loader
from .metadata_prompts import MetadataPrompts
from .analysis_prompts import AnalysisPrompts
from .utils import (
    apply_prompt_template,
    format_state_for_prompt,
    create_system_prompt,
    create_user_prompt,
    merge_prompts,
    truncate_prompt
)

# 创建全局实例
metadata_prompts = MetadataPrompts()
analysis_prompts = AnalysisPrompts()

__all__ = [
    # 加载器
    "PromptLoader",
    "prompt_loader",
    
    # 提示词类
    "MetadataPrompts", 
    "AnalysisPrompts",
    
    # 全局实例
    "metadata_prompts",
    "analysis_prompts",
    
    # 工具函数
    "apply_prompt_template",
    "format_state_for_prompt",
    "create_system_prompt",
    "create_user_prompt", 
    "merge_prompts",
    "truncate_prompt"
] 