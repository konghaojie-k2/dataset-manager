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
    
    def get_statistical_analysis_prompt(self, data_info: Dict[str, Any]) -> str:
        """获取统计分析提示词
        
        Args:
            data_info: 数据信息
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("statistical_analysis")
            return template.format(data_info=data_info)
        except Exception as e:
            logger.error(f"获取统计分析提示词失败: {e}")
            return self._get_fallback_statistical_prompt(data_info)
    
    def get_visualization_prompt(self, data_summary: str) -> str:
        """获取可视化建议提示词
        
        Args:
            data_summary: 数据摘要
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("visualization_analysis")
            return template.format(data_summary=data_summary)
        except Exception as e:
            logger.error(f"获取可视化提示词失败: {e}")
            return self._get_fallback_visualization_prompt(data_summary)
    
    def get_modeling_prompt(self, analysis_goal: str, data_features: Dict[str, Any]) -> str:
        """获取建模建议提示词
        
        Args:
            analysis_goal: 分析目标
            data_features: 数据特征
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("modeling_analysis")
            return template.format(
                analysis_goal=analysis_goal,
                data_features=data_features
            )
        except Exception as e:
            logger.error(f"获取建模提示词失败: {e}")
            return self._get_fallback_modeling_prompt(analysis_goal, data_features)
    
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
    
    def get_research_planner_prompt(self, 
                                  research_question: str,
                                  available_data: str,
                                  analysis_goals: str) -> str:
        """获取研究规划提示词
        
        Args:
            research_question: 研究问题
            available_data: 可用数据
            analysis_goals: 分析目标
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("research_planner")
            return template.format(
                research_question=research_question,
                available_data=available_data,
                analysis_goals=analysis_goals
            )
        except Exception as e:
            logger.error(f"获取研究规划提示词失败: {e}")
            return f"研究问题: {research_question}\n可用数据: {available_data}\n分析目标: {analysis_goals}"
    
    def get_data_researcher_prompt(self,
                                 research_task: str,
                                 data_context: str,
                                 analysis_methods: str) -> str:
        """获取数据研究员提示词
        
        Args:
            research_task: 研究任务
            data_context: 数据上下文
            analysis_methods: 分析方法
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("data_researcher")
            return template.format(
                research_task=research_task,
                data_context=data_context,
                analysis_methods=analysis_methods
            )
        except Exception as e:
            logger.error(f"获取数据研究员提示词失败: {e}")
            return f"研究任务: {research_task}\n数据上下文: {data_context}\n分析方法: {analysis_methods}"
    
    def get_coordinator_prompt(self,
                             user_request: str,
                             available_agents: str,
                             current_state: str) -> str:
        """获取协调员提示词
        
        Args:
            user_request: 用户请求
            available_agents: 可用智能体
            current_state: 当前状态
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("coordinator")
            return template.format(
                user_request=user_request,
                available_agents=available_agents,
                current_state=current_state
            )
        except Exception as e:
            logger.error(f"获取协调员提示词失败: {e}")
            return f"用户请求: {user_request}\n可用智能体: {available_agents}\n当前状态: {current_state}"
    
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
    def _get_fallback_statistical_prompt(self, data_info: Dict[str, Any]) -> str:
        """备用统计分析提示词"""
        return f"""
请对以下数据进行统计分析：

数据信息：
{data_info}

请提供描述性统计、数据分布分析、相关性分析和统计检验建议。
"""
    
    def _get_fallback_visualization_prompt(self, data_summary: str) -> str:
        """备用可视化提示词"""
        return f"""
基于以下数据摘要，请提供可视化建议：

数据摘要：
{data_summary}

请提供基础图表建议、探索性数据分析图表、高级可视化和工具推荐。
"""
    
    def _get_fallback_modeling_prompt(self, analysis_goal: str, data_features: Dict[str, Any]) -> str:
        """备用建模提示词"""
        return f"""
分析目标：{analysis_goal}

数据特征：
{data_features}

请提供机器学习建模建议，包括问题类型识别、算法选择、特征工程和模型评估策略。
"""
    
    def _get_fallback_business_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """备用商业洞察提示词"""
        return f"""
基于以下分析结果，请提供商业洞察：

分析结果：
{analysis_results}

请提供关键发现总结、商业机会识别、风险评估和决策支持建议。
""" 