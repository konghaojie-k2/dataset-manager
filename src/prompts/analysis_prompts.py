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
    
    def get_device_time_identification_prompt(self,
                                            dataset_name: str,
                                            total_columns: int,
                                            columns_info: str) -> str:
        """获取设备列和时间列识别提示词
        
        Args:
            dataset_name: 数据集名称
            total_columns: 总列数
            columns_info: 列信息详情
            
        Returns:
            str: 提示词
        """
        try:
            template = self.loader.get_prompt_template("device_time_identification")
            return template.format(
                dataset_name=dataset_name,
                total_columns=total_columns,
                columns_info=columns_info
            )
        except Exception as e:
            logger.error(f"获取设备时间识别提示词失败: {e}")
            return self._get_fallback_device_time_prompt(dataset_name, total_columns, columns_info)
    
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
                                                device_time_identification: str,
                                                business_meaning_analysis: str,
                                                correlation_analysis: str,
                                                columns_info: str) -> str:
        """获取控制原理分析提示词
        
        Args:
            dataset_name: 数据集名称
            user_requirements: 用户需求
            device_time_identification: 设备时间识别结果
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
                device_time_identification=device_time_identification,
                business_meaning_analysis=business_meaning_analysis,
                correlation_analysis=correlation_analysis,
                columns_info=columns_info
            )
        except Exception as e:
            logger.error(f"获取控制原理分析提示词失败: {e}")
            return self._get_fallback_control_relationships_prompt(
                dataset_name, user_requirements, device_time_identification,
                business_meaning_analysis, correlation_analysis, columns_info
            )
    
    def get_recommendations_prompt(self, analysis_context: Dict[str, Any]) -> str:
        """获取建议生成提示词
        
        Args:
            analysis_context: 分析上下文
            
        Returns:
            str: 提示词
        """
        try:
            # 尝试使用模板，如果没有则使用备用方法
            template = self.loader.get_prompt_template("recommendations")
            return template.format(analysis_context=analysis_context)
        except Exception as e:
            logger.error(f"获取建议提示词失败: {e}")
            return self._get_fallback_recommendations_prompt(analysis_context)
    
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

    def _get_fallback_device_time_prompt(self, dataset_name: str, total_columns: int, columns_info: str) -> str:
        """备用设备时间识别提示词"""
        return f"""
请分析以下数据集的列信息，识别出设备列和时间列：

数据集名称：{dataset_name}
总列数：{total_columns}

列信息详情：
{columns_info}

请按照以下格式返回识别结果：

## 时间列识别
- 主要时间列：[列名]
- 其他时间相关列：[列名1, 列名2, ...]
- 时间格式分析：[描述时间格式和特点]

## 设备列识别  
- 设备标识列：[列名]
- 设备类型列：[列名]
- 设备状态列：[列名1, 列名2, ...]
- 设备参数列：[列名1, 列名2, ...]

## 识别依据
请说明识别这些列的主要依据和特征。
"""

    def _get_fallback_business_meaning_prompt(self, dataset_name: str, user_requirements: str, columns_business_info: str) -> str:
        """备用业务含义分析提示词"""
        return f"""
请分析以下工业数据集中各列的可能业务含义：

数据集名称：{dataset_name}
用户需求：{user_requirements}

列详细信息：
{columns_business_info}

请按照以下格式分析每列的业务含义：

## 业务含义分析

### [列名1]
- **业务类型**：[如：传感器数据/控制参数/状态标识/时间戳等]
- **具体含义**：[详细描述该列在业务中的作用和意义]
- **数据特征**：[描述数据的分布特征和异常情况]
- **业务价值**：[说明该列对业务分析的重要性]

### [列名2]
...

## 业务域分类
请将所有列按照业务功能进行分类：
- **时间维度**：[时间相关的列]
- **设备标识**：[设备识别相关的列]
- **过程参数**：[工艺过程参数列]
- **控制变量**：[可控制的变量列]
- **监测指标**：[监测和测量的指标列]
- **状态标志**：[设备或过程状态列]
- **质量指标**：[产品或过程质量相关列]

## 数据质量评估
对各列的数据质量进行评估，指出可能的数据问题。
"""

    def _get_fallback_control_relationships_prompt(self, dataset_name: str, user_requirements: str, 
                                                 device_time_identification: str, business_meaning_analysis: str,
                                                 correlation_analysis: str, columns_info: str) -> str:
        """备用控制原理分析提示词"""
        return f"""
请分析以下工业数据集中列之间可能的控制原理和因果关系：

数据集名称：{dataset_name}
用户需求：{user_requirements}

已识别的设备和时间列信息：
{device_time_identification}

业务含义分析结果：
{business_meaning_analysis}

相关性分析结果：
{correlation_analysis}

列基本信息：
{columns_info}

请按照以下格式分析控制原理：

## 控制系统架构分析

### 控制回路识别
请识别可能的控制回路，包括：
- **主控制回路**：[描述主要的控制逻辑]
- **辅助控制回路**：[描述辅助控制系统]
- **安全联锁回路**：[描述安全保护机制]

### 变量关系分析

#### 控制变量 → 被控变量
- **[控制变量名]** → **[被控变量名]**
  - 控制原理：[描述控制机制]
  - 响应特性：[描述响应时间和特性]
  - 控制策略：[如PID控制、开关控制等]

#### 扰动变量影响
- **[扰动变量名]** → **[受影响变量名]**
  - 影响机制：[描述影响原理]
  - 影响程度：[强/中/弱]
  - 补偿策略：[如何补偿该扰动]

### 过程动态特性
- **时间常数**：[各控制回路的时间特性]
- **滞后特性**：[系统的滞后情况]
- **耦合关系**：[变量间的相互影响]

### 操作约束条件
- **物理约束**：[设备物理限制]
- **工艺约束**：[工艺过程限制]
- **安全约束**：[安全操作限制]

## 控制策略建议

### 优化机会
基于数据分析，识别可能的控制优化点。

### 异常检测
建议监控的关键变量组合和异常模式。

### 预测性维护
基于变量关系，建议预测性维护策略。

## 数据驱动洞察
基于实际数据，发现的控制系统特点和改进建议。
"""

    def _get_fallback_recommendations_prompt(self, analysis_context: Dict[str, Any]) -> str:
        """备用建议生成提示词"""
        return f"""
基于以下分析结果，请提供实用的建议：

分析上下文：
{analysis_context}

请提供以下建议：

## 数据质量改进建议
- 数据清洗建议
- 数据收集优化
- 数据验证方法

## 分析深化建议
- 进一步分析方向
- 推荐的分析方法
- 需要补充的数据

## 业务应用建议
- 实际应用场景
- 实施步骤
- 预期效果

## 技术实现建议
- 工具和技术选择
- 实施难度评估
- 资源需求分析
""" 