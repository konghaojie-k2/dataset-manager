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
    
    def get_column_analysis_prompt(self, column_name: str, column_data: str) -> str:
        """获取列分析提示词
        
        Args:
            column_name: 列名
            column_data: 列数据样本
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("column_analysis")
            return template.format(
                column_name=column_name,
                column_data=column_data
            )
        except Exception as e:
            logger.error(f"获取列分析提示词失败: {e}")
            return self._get_fallback_column_prompt(column_name, column_data)
    
    def get_relationship_analysis_prompt(self, data_sample: str) -> str:
        """获取关系分析提示词
        
        Args:
            data_sample: 数据样本
            
        Returns:
            str: 提示词
        """
        try:
            # 如果有关系分析模板文件，使用它
            template = self.loader.get_prompt_template("relationship_analysis")
            return template.format(data_sample=data_sample)
        except Exception as e:
            logger.error(f"获取关系分析提示词失败: {e}")
            return self._get_fallback_relationship_prompt(data_sample)
    
    def get_summary_prompt(self, analyses: Dict[str, Any]) -> str:
        """获取总结提示词
        
        Args:
            analyses: 各项分析结果
            
        Returns:
            str: 提示词
        """
        try:
            # 如果有总结模板文件，使用它
            template = self.loader.get_prompt_template("metadata_summary")
            return template.format(analyses=analyses)
        except Exception as e:
            logger.error(f"获取总结提示词失败: {e}")
            return self._get_fallback_summary_prompt(analyses)
    
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
    
    def _get_fallback_column_prompt(self, column_name: str, column_data: str) -> str:
        """备用列分析提示词"""
        return f"""
请对数据集中的列 "{column_name}" 进行详细分析。

列数据样本：
{column_data}

请提供以下分析：
- 列基本信息
- 数据分布分析
- 数据质量分析
- 业务含义推断
- 处理建议

请基于提供的数据样本进行准确分析。
"""
    
    def _get_fallback_relationship_prompt(self, data_sample: str) -> str:
        """备用关系分析提示词"""
        return f"""
请分析数据集中各列之间的潜在关系。

数据样本：
{data_sample}

请提供以下分析：
- 列间关系分析
- 数据结构分析
- 业务逻辑推断
- 分析建议

请基于数据特征进行深入分析。
"""
    
    def _get_fallback_summary_prompt(self, analyses: Dict[str, Any]) -> str:
        """备用总结提示词"""
        return f"""
请基于以下分析结果，生成数据集的综合分析报告。

分析结果：
{analyses}

请生成包含以下内容的综合报告：
- 执行摘要
- 数据质量报告
- 业务价值分析
- 技术建议
- 后续行动计划

请确保报告结构清晰、内容全面、建议可行。
""" 