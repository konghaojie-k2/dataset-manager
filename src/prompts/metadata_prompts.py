"""元数据分析提示词模板 - 重构版本

使用 .md 文件加载提示词模板，参考 DeerFlow 的设计模式
"""

from typing import Dict, Any
from .loader import prompt_loader
from loguru import logger


class MetadataPrompts:
    """元数据分析提示词模板类 - 从 .md 文件加载"""
    
    def __init__(self):
        """初始化元数据提示词"""
        self.loader = prompt_loader
        logger.info("初始化元数据提示词模板")
    
    def get_basic_analysis_prompt(self) -> str:
        """获取基础分析提示词
        
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("basic_metadata_analysis")
            return template
        except Exception as e:
            logger.error(f"获取基础分析提示词失败: {e}")
            return self._get_fallback_basic_prompt()
    
    def list_available_templates(self) -> list:
        """列出所有可用的元数据模板
        
        Returns:
            list: 模板名称列表
        """
        return self.loader.list_available_prompts()
    
    def reload_templates(self) -> None:
        """重新加载所有模板"""
        self.loader.clear_cache()
        logger.info("重新加载元数据提示词模板")
    
    # 以下是备用提示词，当 .md 文件加载失败时使用
    def _get_fallback_basic_prompt(self) -> str:
        """备用基础分析提示词"""
        return """
你是一个专业的数据分析师，请对提供的数据集进行基础分析。

请按照以下格式输出分析结果：

## 数据集基本信息
- 数据集名称：
- 数据行数：
- 数据列数：
- 文件大小：

## 列信息分析
对每一列进行分析，包括：
- 列名
- 数据类型
- 缺失值数量和比例
- 唯一值数量
- 基本统计信息（如适用）

## 数据质量评估
- 整体数据完整性
- 潜在的数据质量问题
- 建议的数据清洗步骤

## 初步洞察
- 数据的主要特征
- 可能的分析方向
- 需要注意的问题

请确保分析结果准确、详细且易于理解。
""" 