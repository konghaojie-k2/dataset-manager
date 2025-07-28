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
            
            # 确保file_path是Path对象
            file_path = Path(state["file_path"])
            
            # 处理ZIP文件：先解压，获取CSV文件
            if file_path.suffix.lower() == '.zip':
                # 使用FileProcessor提取CSV文件
                csv_files = self.file_processor.extract_csv_files(file_path)
                if not csv_files:
                    raise ValueError("ZIP文件中未找到CSV文件")
                
                # 使用第一个CSV文件进行分析
                csv_file_path = csv_files[0]
                logger.info(f"从ZIP文件中提取到CSV文件: {csv_file_path}")
                
                # 使用FileProcessor的load_csv_data方法加载数据
                self.data_analyzer.data = self.file_processor.load_csv_data(csv_file_path)
                
            elif file_path.suffix.lower() == '.csv':
                # 直接加载CSV文件
                self.data_analyzer.data = self.file_processor.load_csv_data(file_path)
                
            else:
                # 使用原来的方法处理其他格式
                data = self.data_analyzer.load_data(file_path)
            
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
            
            # 列级分析（限制数量和内容以减少token使用）
            column_analyses = {}
            if state["data_info"] and "columns" in state["data_info"]:
                for col in state["data_info"]["columns"][:3]:  # 只分析前3列，减少数据量
                    try:
                        col_analysis = self.data_analyzer.get_column_analysis(col)
                        # 只保留关键信息，减少token使用
                        column_analyses[col] = {
                            "dtype": str(col_analysis.get("dtype", "unknown")),
                            "null_count": col_analysis.get("null_count", 0),
                            "unique_count": col_analysis.get("unique_count", 0),
                            "sample_values": col_analysis.get("sample_values", [])[:3]  # 只保留3个示例值
                        }
                    except Exception as e:
                        logger.warning(f"列 {col} 分析失败: {e}")
            
            state["column_analyses"] = column_analyses
            
            # 生成简化的详细分析报告（减少数据量）
            simplified_context = {
                "data_shape": state["data_info"].get("shape", "未知"),
                "column_count": len(state["data_info"].get("columns", [])),
                "quality_score": quality_analysis.get("completeness", {}).get("completeness_rate", 0),
                "has_outliers": any(outliers.get(col, {}).get("count", 0) > 0 for col in outliers),
                "correlation_summary": "存在相关性" if correlation_analysis.get("strong_correlations") else "相关性较弱"
            }
            
            # 使用简化的统计分析提示词
            prompt = f"""
请对以下数据进行统计分析：

数据概况：
- 数据形状：{simplified_context['data_shape']}
- 列数：{simplified_context['column_count']}
- 数据完整性：{simplified_context['quality_score']:.1f}%
- 异常值情况：{'存在异常值' if simplified_context['has_outliers'] else '无明显异常值'}
- 相关性：{simplified_context['correlation_summary']}

请提供简要的统计分析建议，包括：
1. 数据质量评估
2. 统计特征总结
3. 分析建议

请保持回答简洁明了。
"""
            
            messages = [
                SystemMessage(content="你是一个专业的数据科学家，请提供简洁的统计分析。"),
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
            # 即使详细分析失败，也继续执行后续步骤
            state["detailed_analysis"] = "详细分析暂时跳过，继续执行工业数据分析。"
            state["completed_steps"].append("detailed_analysis")
        
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
                    # 初始化默认值
                    col_analysis = None
                    try:
                        col_analysis = self.data_analyzer.get_column_analysis(col)
                    except Exception as e:
                        logger.warning(f"获取列 {col} 信息失败: {e}")
                    
                    # 构建列信息，确保col_analysis不为None
                    if col_analysis is not None:
                        columns_info[col] = {
                            "dtype": col_analysis.get("dtype", "unknown"),
                            "unique_count": col_analysis.get("unique_count", 0),
                            "null_count": col_analysis.get("null_count", 0),
                            "sample_values": col_analysis.get("sample_values", [])
                        }
                    else:
                        # 提供默认值，避免NoneType错误
                        columns_info[col] = {
                            "dtype": "unknown", 
                            "unique_count": 0, 
                            "null_count": 0, 
                            "sample_values": []
                        }
            
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
                    # 初始化默认值
                    col_analysis = None
                    try:
                        col_analysis = self.data_analyzer.get_column_analysis(col)
                    except Exception as e:
                        logger.warning(f"获取列 {col} 分析信息失败: {e}")
                    
                    # 获取统计摘要
                    statistical_summary = state.get("statistical_summary", {})
                    col_stats = statistical_summary.get(col, {}) if statistical_summary else {}
                    
                    # 构建列信息，确保col_analysis不为None
                    if col_analysis is not None:
                        columns_business_info[col] = {
                            "dtype": col_analysis.get("dtype", "unknown"),
                            "unique_count": col_analysis.get("unique_count", 0),
                            "null_count": col_analysis.get("null_count", 0),
                            "sample_values": col_analysis.get("sample_values", []),
                            "statistics": col_stats
                        }
                    else:
                        # 提供默认值，避免NoneType错误
                        columns_business_info[col] = {
                            "dtype": "unknown",
                            "unique_count": 0,
                            "null_count": 0,
                            "sample_values": [],
                            "statistics": col_stats
                        }
            
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
                    # 初始化默认值
                    col_analysis = None
                    try:
                        col_analysis = self.data_analyzer.get_column_analysis(col)
                    except Exception as e:
                        logger.warning(f"获取列 {col} 信息失败: {e}")
                    
                    # 构建列信息，确保col_analysis不为None
                    if col_analysis is not None:
                        columns_info[col] = col_analysis
                    else:
                        # 提供默认值，避免NoneType错误
                        columns_info[col] = {
                            "dtype": "unknown",
                            "unique_count": 0,
                            "null_count": 0,
                            "sample_values": []
                        }
            
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