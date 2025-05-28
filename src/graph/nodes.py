"""
工作流节点定义模块

定义数据分析工作流中的各个节点函数，每个节点负责特定的处理步骤
"""

from typing import Dict, Any
from pathlib import Path
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AnalysisState
from ..tools.data_analyzer import DataAnalyzer
from ..tools.file_processor import FileProcessor
from ..llms import get_reasoning_llm, get_basic_llm
from ..prompts.metadata_prompts import MetadataPrompts
from ..prompts.analysis_prompts import AnalysisPrompts


class AnalysisNodes:
    """分析工作流节点类"""
    
    def __init__(self):
        """初始化节点类"""
        self.data_analyzer = DataAnalyzer()
        self.file_processor = FileProcessor()
        self.metadata_prompts = MetadataPrompts()
        self.analysis_prompts = AnalysisPrompts()
        
        # LLM实例延迟初始化
        self._reasoning_llm = None
        self._basic_llm = None
        
        logger.info("分析工作流节点初始化完成")
    
    @property
    def reasoning_llm(self):
        """获取推理LLM实例（延迟初始化）"""
        if self._reasoning_llm is None:
            self._reasoning_llm = get_reasoning_llm()
        return self._reasoning_llm
    
    @property
    def basic_llm(self):
        """获取基础LLM实例（延迟初始化）"""
        if self._basic_llm is None:
            self._basic_llm = get_basic_llm()
        return self._basic_llm
    
    def load_data_node(self, state: AnalysisState) -> AnalysisState:
        """数据加载节点
        
        Args:
            state: 当前状态
            
        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info(f"开始加载数据: {state['file_path']}")
            
            # 加载数据
            data = self.data_analyzer.load_data(state["file_path"])
            
            # 获取基础信息
            basic_info = self.data_analyzer.get_basic_info()
            
            # 更新状态
            state["data_info"] = basic_info
            state["current_step"] = "basic_analysis"
            state["completed_steps"].append("load_data")
            
            logger.info(f"数据加载完成，形状: {basic_info['shape']}")
            
        except Exception as e:
            error_msg = f"数据加载失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    async def basic_analysis_node(self, state: AnalysisState) -> AnalysisState:
        """基础分析节点
        
        Args:
            state: 当前状态
            
        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始基础分析")
            
            # 获取统计摘要
            statistical_summary = self.data_analyzer.get_statistical_summary()
            state["statistical_summary"] = statistical_summary
            
            # 生成基础分析提示词
            prompt = self.metadata_prompts.get_basic_analysis_prompt()
            
            # 准备数据信息
            data_context = {
                "basic_info": state["data_info"],
                "statistical_summary": statistical_summary,
                "dataset_name": state["dataset_name"]
            }
            
            # 调用LLM生成基础分析
            messages = [
                SystemMessage(content="你是一个专业的数据分析师，请对提供的数据进行详细分析。"),
                HumanMessage(content=f"数据信息：\n{data_context}\n\n请进行基础分析。")
            ]
            
            response = await self.basic_llm.ainvoke(messages)
            state["basic_analysis"] = response.content
            state["current_step"] = "detailed_analysis"
            state["completed_steps"].append("basic_analysis")
            
            logger.info("基础分析完成")
            
        except Exception as e:
            error_msg = f"基础分析失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    async def detailed_analysis_node(self, state: AnalysisState) -> AnalysisState:
        """详细分析节点
        
        Args:
            state: 当前状态
            
        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始详细分析")
            
            # 进行数据质量分析
            quality_analysis = self.data_analyzer.analyze_data_quality()
            
            # 进行相关性分析
            correlation_analysis = self.data_analyzer.get_correlation_analysis()
            
            # 异常值检测
            outliers = self.data_analyzer.detect_outliers()
            
            # 列级分析
            column_analyses = {}
            if state["data_info"] and "columns" in state["data_info"]:
                for col in state["data_info"]["columns"][:5]:  # 限制分析前5列
                    try:
                        col_analysis = self.data_analyzer.get_column_analysis(col)
                        column_analyses[col] = col_analysis
                    except Exception as e:
                        logger.warning(f"列 {col} 分析失败: {e}")
            
            state["column_analyses"] = column_analyses
            
            # 生成详细分析报告
            detailed_context = {
                "quality_analysis": quality_analysis,
                "correlation_analysis": correlation_analysis,
                "outliers": outliers,
                "column_analyses": column_analyses
            }
            
            # 使用统计分析提示词
            prompt = self.analysis_prompts.get_statistical_analysis_prompt(detailed_context)
            
            messages = [
                SystemMessage(content="你是一个专业的数据科学家，请提供深入的统计分析。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.reasoning_llm.ainvoke(messages)
            state["detailed_analysis"] = response.content
            state["current_step"] = "generate_insights"
            state["completed_steps"].append("detailed_analysis")
            
            logger.info("详细分析完成")
            
        except Exception as e:
            error_msg = f"详细分析失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    async def generate_insights_node(self, state: AnalysisState) -> AnalysisState:
        """生成洞察节点
        
        Args:
            state: 当前状态
            
        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始生成洞察")
            
            # 准备分析结果
            analysis_results = {
                "basic_analysis": state.get("basic_analysis"),
                "detailed_analysis": state.get("detailed_analysis"),
                "data_info": state.get("data_info"),
                "statistical_summary": state.get("statistical_summary"),
                "column_analyses": state.get("column_analyses")
            }
            
            # 使用商业洞察提示词
            prompt = self.analysis_prompts.get_business_insight_prompt(analysis_results)
            
            messages = [
                SystemMessage(content="你是一个资深的商业分析师，请提供有价值的商业洞察。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.reasoning_llm.ainvoke(messages)
            state["insights"] = response.content
            state["current_step"] = "create_recommendations"
            state["completed_steps"].append("generate_insights")
            
            logger.info("洞察生成完成")
            
        except Exception as e:
            error_msg = f"洞察生成失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    async def create_recommendations_node(self, state: AnalysisState) -> AnalysisState:
        """生成建议节点
        
        Args:
            state: 当前状态
            
        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始生成建议")
            
            # 收集所有分析结果
            analysis_context = {
                "basic_analysis": state.get("basic_analysis", ""),
                "detailed_analysis": state.get("detailed_analysis", ""),
                "insights": state.get("insights", []),
                "analysis_goals": state.get("analysis_goals", []),
                "user_requirements": state.get("user_requirements", "")
            }
            
            # 生成建议提示词
            prompt = self.analysis_prompts.get_recommendations_prompt(analysis_context)
            
            messages = [
                SystemMessage(content="你是一个资深的数据科学顾问，请基于分析结果提供实用的建议。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.reasoning_llm.ainvoke(messages)
            state["recommendations"] = response.content
            state["current_step"] = "completed"
            state["completed_steps"].append("create_recommendations")
            
            logger.info("建议生成完成")
            
        except Exception as e:
            error_msg = f"建议生成失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state

    async def identify_device_time_columns_node(self, state: AnalysisState) -> AnalysisState:
        """识别设备列和时间列节点
        
        Args:
            state: 当前状态
            
        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始识别设备列和时间列")
            
            # 获取列信息
            columns_info = {}
            if state.get("data_info") and "columns" in state["data_info"]:
                for col in state["data_info"]["columns"]:
                    try:
                        col_analysis = self.data_analyzer.get_column_analysis(col)
                        columns_info[col] = {
                            "dtype": col_analysis.get("dtype", "unknown"),
                            "unique_count": col_analysis.get("unique_count", 0),
                            "null_count": col_analysis.get("null_count", 0),
                            "sample_values": col_analysis.get("sample_values", [])
                        }
                    except Exception as e:
                        logger.warning(f"获取列 {col} 信息失败: {e}")
                        columns_info[col] = {"dtype": "unknown", "unique_count": 0, "null_count": 0, "sample_values": []}
            
            # 构建列信息字符串
            columns_info_str = ""
            for col_name, col_info in columns_info.items():
                columns_info_str += f"""
列名：{col_name}
- 数据类型：{col_info['dtype']}
- 唯一值数量：{col_info['unique_count']}
- 空值数量：{col_info['null_count']}
- 示例值：{col_info['sample_values'][:5]}
"""
            
            # 使用外部提示词模板
            prompt = self.analysis_prompts.get_device_time_identification_prompt(
                dataset_name=state.get('dataset_name', '未知'),
                total_columns=len(columns_info),
                columns_info=columns_info_str
            )
            
            messages = [
                SystemMessage(content="你是一个专业的工业数据分析专家，擅长识别时间序列数据中的设备相关列和时间列。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.reasoning_llm.ainvoke(messages)
            state["device_time_identification"] = response.content
            state["completed_steps"].append("identify_device_time_columns")
            
            logger.info("设备列和时间列识别完成")
            
        except Exception as e:
            error_msg = f"设备列和时间列识别失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state

    async def analyze_business_meaning_node(self, state: AnalysisState) -> AnalysisState:
        """分析业务含义节点
        
        Args:
            state: 当前状态
            
        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始分析列的业务含义")
            
            # 获取列的统计信息
            columns_business_info = {}
            if state.get("data_info") and "columns" in state["data_info"]:
                for col in state["data_info"]["columns"]:
                    try:
                        col_analysis = self.data_analyzer.get_column_analysis(col)
                        statistical_summary = state.get("statistical_summary", {})
                        col_stats = statistical_summary.get(col, {})
                        
                        columns_business_info[col] = {
                            "dtype": col_analysis.get("dtype", "unknown"),
                            "unique_count": col_analysis.get("unique_count", 0),
                            "null_count": col_analysis.get("null_count", 0),
                            "sample_values": col_analysis.get("sample_values", []),
                            "statistics": col_stats
                        }
                    except Exception as e:
                        logger.warning(f"获取列 {col} 业务信息失败: {e}")
            
            # 构建列业务信息字符串
            columns_business_info_str = ""
            for col_name, col_info in columns_business_info.items():
                columns_business_info_str += f"""
列名：{col_name}
- 数据类型：{col_info['dtype']}
- 唯一值数量：{col_info['unique_count']}
- 空值数量：{col_info['null_count']}
- 示例值：{col_info['sample_values'][:10]}
- 统计信息：{col_info.get('statistics', {})}
"""
            
            # 使用外部提示词模板
            prompt = self.analysis_prompts.get_business_meaning_analysis_prompt(
                dataset_name=state.get('dataset_name', '未知'),
                user_requirements=state.get('user_requirements', '无特殊要求'),
                columns_business_info=columns_business_info_str
            )
            
            messages = [
                SystemMessage(content="你是一个资深的工业数据分析专家，具有丰富的制造业、能源、化工等行业经验，擅长理解工业数据的业务含义。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.reasoning_llm.ainvoke(messages)
            state["business_meaning_analysis"] = response.content
            state["completed_steps"].append("analyze_business_meaning")
            
            logger.info("业务含义分析完成")
            
        except Exception as e:
            error_msg = f"业务含义分析失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state

    async def analyze_control_relationships_node(self, state: AnalysisState) -> AnalysisState:
        """分析控制原理节点
        
        Args:
            state: 当前状态
            
        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始分析列之间的控制原理")
            
            # 获取相关性分析结果
            correlation_analysis = state.get("correlation_analysis", {})
            
            # 获取列信息和业务含义
            columns_info = {}
            if state.get("data_info") and "columns" in state["data_info"]:
                for col in state["data_info"]["columns"]:
                    try:
                        col_analysis = self.data_analyzer.get_column_analysis(col)
                        columns_info[col] = col_analysis
                    except Exception as e:
                        logger.warning(f"获取列 {col} 信息失败: {e}")
            
            # 构建列信息字符串
            columns_info_str = ""
            for col_name, col_info in columns_info.items():
                columns_info_str += f"""
- {col_name}: {col_info.get('dtype', 'unknown')} (唯一值: {col_info.get('unique_count', 0)})
"""
            
            # 使用外部提示词模板
            prompt = self.analysis_prompts.get_control_relationships_analysis_prompt(
                dataset_name=state.get('dataset_name', '未知'),
                user_requirements=state.get('user_requirements', '无特殊要求'),
                device_time_identification=state.get('device_time_identification', '暂未识别'),
                business_meaning_analysis=state.get('business_meaning_analysis', '暂未分析'),
                correlation_analysis=str(correlation_analysis),
                columns_info=columns_info_str
            )
            
            messages = [
                SystemMessage(content="你是一个资深的工业自动化和过程控制专家，具有丰富的控制系统设计和优化经验，擅长分析工业过程中的控制原理和变量关系。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.reasoning_llm.ainvoke(messages)
            state["control_relationships_analysis"] = response.content
            state["completed_steps"].append("analyze_control_relationships")
            
            # 设置为完成状态，因为这是工业分析流程的最后一步
            state["current_step"] = "completed"
            
            logger.info("控制原理分析完成")
            
        except Exception as e:
            error_msg = f"控制原理分析失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state


# 创建全局节点实例
analysis_nodes = AnalysisNodes()

# 导出节点函数
load_data_node = analysis_nodes.load_data_node
basic_analysis_node = analysis_nodes.basic_analysis_node
detailed_analysis_node = analysis_nodes.detailed_analysis_node
generate_insights_node = analysis_nodes.generate_insights_node
create_recommendations_node = analysis_nodes.create_recommendations_node
identify_device_time_columns_node = analysis_nodes.identify_device_time_columns_node
analyze_business_meaning_node = analysis_nodes.analyze_business_meaning_node
analyze_control_relationships_node = analysis_nodes.analyze_control_relationships_node 