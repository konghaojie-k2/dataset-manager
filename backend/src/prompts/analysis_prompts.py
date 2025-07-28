"""数据分析提示词模板 - 重构版本

使用 .md 文件加载提示词模板，参考 DeerFlow 的设计模式
"""

from typing import Dict, Any
from .loader import prompt_loader
from loguru import logger


class AnalysisPrompts:
    """数据分析提示词模板类 - 从 .md 文件加载"""
    
    def __init__(self):
        """初始化分析提示词"""
        self.loader = prompt_loader
        logger.info("初始化分析提示词模板")
    
    def get_business_insight_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """获取商业洞察提示词
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("business_insight")
            return template.format(analysis_results=analysis_results)
        except Exception as e:
            logger.error(f"获取商业洞察提示词失败: {e}")
            return self._get_fallback_business_prompt(analysis_results)
    

    
    def get_business_meaning_analysis_prompt(self,
                                           dataset_name: str,
                                           user_requirements: str,
                                           columns_business_info: str) -> str:
        """获取业务含义分析提示词
        
        Args:
            dataset_name: 数据集名称
            user_requirements: 用户需求
            columns_business_info: 列业务信息
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("business_meaning_analysis")
            return template.format(
                dataset_name=dataset_name,
                user_requirements=user_requirements,
                columns_business_info=columns_business_info
            )
        except Exception as e:
            logger.error(f"获取业务含义分析提示词失败: {e}")
            return self._get_fallback_business_meaning_prompt(dataset_name, user_requirements, columns_business_info)
    
    def get_control_relationships_analysis_prompt(self,
                                                dataset_name: str,
                                                user_requirements: str,
                                                business_meaning_analysis: str,
                                                correlation_analysis: str,
                                                columns_info: str) -> str:
        """获取控制关系分析提示词
        
        Args:
            dataset_name: 数据集名称
            user_requirements: 用户需求
            business_meaning_analysis: 业务含义分析结果
            correlation_analysis: 相关性分析结果
            columns_info: 列信息
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("control_relationships_analysis")
            return template.format(
                dataset_name=dataset_name,
                user_requirements=user_requirements,
                business_meaning_analysis=business_meaning_analysis,
                correlation_analysis=correlation_analysis,
                columns_info=columns_info
            )
        except Exception as e:
            logger.error(f"获取控制关系分析提示词失败: {e}")
            return self._get_fallback_control_relationships_prompt(
                dataset_name, user_requirements,
                business_meaning_analysis, correlation_analysis, columns_info
            )
    
    def get_recommendations_prompt(self, analysis_context: Dict[str, Any]) -> str:
        """获取建议提示词
        
        Args:
            analysis_context: 分析上下文
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("recommendations")
            return template.format(analysis_context=analysis_context)
        except Exception as e:
            logger.error(f"获取建议提示词失败: {e}")
            return self._get_fallback_recommendations_prompt(analysis_context)
    
    def get_data_quality_column_optimization_prompt(self, 
                                                   columns_info: str,
                                                   user_requirements: str) -> str:
        """获取数据质量列优化提示词
        
        Args:
            columns_info: 列信息
            user_requirements: 用户需求
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("data_quality_column_optimization")
            return template.format(
                columns_info=columns_info,
                user_requirements=user_requirements
            )
        except Exception as e:
            logger.error(f"获取数据质量列优化提示词失败: {e}")
            return self._get_fallback_column_optimization_prompt(columns_info, user_requirements)
    
    def get_data_quality_insights_prompt(self,
                                       report_summary: str,
                                       user_requirements: str) -> str:
        """获取数据质量洞察提示词
        
        Args:
            report_summary: 报告摘要
            user_requirements: 用户需求
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("data_quality_insights")
            return template.format(
                report_summary=report_summary,
                user_requirements=user_requirements
            )
        except Exception as e:
            logger.error(f"获取数据质量洞察提示词失败: {e}")
            return self._get_fallback_quality_insights_prompt(report_summary, user_requirements)
    
    def list_available_templates(self) -> list:
        """列出所有可用的分析模板
        
        Returns:
            list: 模板名称列表
        """
        return self.loader.list_available_prompts()
    
    def reload_templates(self) -> None:
        """重新加载所有模板"""
        self.loader.clear_cache()
        logger.info("重新加载分析提示词模板")
    
    # 以下是备用提示词，当 .md 文件加载失败时使用
    def _get_fallback_business_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """备用商业洞察提示词"""
        return f"""
基于以下分析结果，请提供商业洞察和建议：

分析结果：
{analysis_results}

请提供：
- 关键发现
- 商业价值
- 行动建议
- 风险评估
"""
    

    
    def _get_fallback_business_meaning_prompt(self, dataset_name: str, user_requirements: str, columns_business_info: str) -> str:
        """备用业务含义分析提示词"""
        return f"""
请对数据集 "{dataset_name}" 进行业务含义分析。

用户需求：{user_requirements}
列业务信息：{columns_business_info}

请提供：
- 业务域分析
- 列业务含义
- 业务关联性
- 应用场景

请确保分析结果符合用户需求。
"""
    
    def _get_fallback_control_relationships_prompt(self, dataset_name: str, user_requirements: str, 
                                                 business_meaning_analysis: str,
                                                 correlation_analysis: str, columns_info: str) -> str:
        """备用控制关系分析提示词"""
        return f"""
请对数据集 "{dataset_name}" 进行控制关系分析。

输入信息：
- 用户需求：{user_requirements}
- 业务含义分析：{business_meaning_analysis}
- 相关性分析：{correlation_analysis}
- 列信息：{columns_info}

请分析：
1. 控制系统架构
2. 变量关系
3. 控制策略
4. 系统优化建议

## ⚠️ Mermaid语法要求（重要）
- **必须严格按照Mermaid语法规范编写图表**
- **图表声明必须是 `graph TD` 而不是其他变体**
- **每个节点连接必须单独一行，不能连写**
- **节点标识符只能使用字母和数字，避免中文**

正确格式示例：
```mermaid
graph TD
    A[控制层] --> B[执行层]
    B --> C[被控对象]
    C --> D[传感器]
    D --> A
```

请提供详细的控制关系分析，并使用正确的Mermaid图表展示。
"""
    
    def _get_fallback_recommendations_prompt(self, analysis_context: Dict[str, Any]) -> str:
        """备用建议提示词"""
        return f"""
基于分析上下文，请提供改进建议：

分析上下文：
{analysis_context}

请提供：
- 数据质量改进建议
- 分析方法建议
- 业务应用建议
- 技术实施建议

请确保建议具体可行。
"""
    
    def _get_fallback_column_optimization_prompt(self, columns_info: str, user_requirements: str) -> str:
        """备用列优化提示词"""
        return f"""
请对数据列进行质量优化分析。

列信息：{columns_info}
用户需求：{user_requirements}

请提供：
- 列质量评估
- 优化建议
- 处理方案
- 预期效果

请确保建议符合用户需求。
"""
    
    def _get_fallback_quality_insights_prompt(self, report_summary: str, user_requirements: str) -> str:
        """备用质量洞察提示词"""
        return f"""
基于质量报告摘要，请提供数据质量洞察。

报告摘要：{report_summary}
用户需求：{user_requirements}

请提供：
- 质量问题分析
- 影响评估
- 改进策略
- 监控建议

请确保洞察深入且可操作。
""" 