"""基于LangGraph的元数据提取代理"""

import json
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import pandas as pd
from pathlib import Path

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from loguru import logger

from ..models.dataset import (
    DatasetMetadata, 
    ColumnMetadata, 
    DataQualityMetrics
)


class MetadataExtractionState(TypedDict):
    """元数据提取状态"""
    dataset_id: str
    file_path: str
    dataframe: Optional[pd.DataFrame]
    messages: List[Dict[str, Any]]
    
    # 提取的元数据
    dataset_description: Optional[str]
    time_range_start: Optional[datetime]
    time_range_end: Optional[datetime]
    sampling_rate: Optional[str]
    columns_metadata: List[Dict[str, Any]]
    
    # 用户交互
    user_input: Optional[str]
    awaiting_user_input: bool
    current_step: str
    
    # 数据质量
    quality_metrics: Optional[Dict[str, Any]]
    
    # 标签
    suggested_tags: List[str]
    suggested_industry: Optional[str]
    suggested_domains: List[str]
    suggested_algorithms: List[str]


class MetadataExtractionAgent:
    """元数据提取代理"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """初始化代理
        
        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url=base_url,
            temperature=0.1
        )
        
        # 创建状态图
        self.graph = self._create_graph()
        logger.info("元数据提取代理初始化完成")
    
    def _create_graph(self) -> StateGraph:
        """创建LangGraph状态图"""
        
        # 定义工作流
        workflow = StateGraph(MetadataExtractionState)
        
        # 添加节点
        workflow.add_node("analyze_structure", self._analyze_data_structure)
        workflow.add_node("identify_columns", self._identify_key_columns)
        workflow.add_node("extract_time_info", self._extract_time_information)
        workflow.add_node("generate_description", self._generate_dataset_description)
        workflow.add_node("analyze_quality", self._analyze_data_quality)
        workflow.add_node("suggest_tags", self._suggest_tags_and_domains)
        workflow.add_node("await_user_input", self._await_user_input)
        workflow.add_node("finalize_metadata", self._finalize_metadata)
        
        # 设置入口点
        workflow.set_entry_point("analyze_structure")
        
        # 添加边
        workflow.add_edge("analyze_structure", "identify_columns")
        workflow.add_edge("identify_columns", "extract_time_info")
        workflow.add_edge("extract_time_info", "generate_description")
        workflow.add_edge("generate_description", "analyze_quality")
        workflow.add_edge("analyze_quality", "suggest_tags")
        workflow.add_edge("suggest_tags", "await_user_input")
        workflow.add_edge("await_user_input", "finalize_metadata")
        workflow.add_edge("finalize_metadata", END)
        
        # 编译图
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def extract_metadata(
        self, 
        dataset_id: str, 
        file_path: Path, 
        dataframe: pd.DataFrame,
        user_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """提取数据集元数据
        
        Args:
            dataset_id: 数据集ID
            file_path: 文件路径
            dataframe: 数据框
            user_input: 用户输入的额外信息
            
        Returns:
            Dict[str, Any]: 提取的元数据
        """
        
        # 初始化状态
        initial_state = MetadataExtractionState(
            dataset_id=dataset_id,
            file_path=str(file_path),
            dataframe=dataframe,
            messages=[],
            dataset_description=None,
            time_range_start=None,
            time_range_end=None,
            sampling_rate=None,
            columns_metadata=[],
            user_input=user_input,
            awaiting_user_input=False,
            current_step="analyze_structure",
            quality_metrics=None,
            suggested_tags=[],
            suggested_industry=None,
            suggested_domains=[],
            suggested_algorithms=[]
        )
        
        # 运行工作流
        config = {"configurable": {"thread_id": dataset_id}}
        
        try:
            result = await self.graph.ainvoke(initial_state, config)
            logger.info(f"元数据提取完成: {dataset_id}")
            return result
        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            raise
    
    def _analyze_data_structure(self, state: MetadataExtractionState) -> MetadataExtractionState:
        """分析数据结构"""
        df = state["dataframe"]
        
        logger.info(f"开始分析数据结构，数据形状: {df.shape}")
        
        # 基本统计信息
        basic_info = {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "null_counts": df.isnull().sum().to_dict()
        }
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"数据基本信息: {json.dumps(basic_info, default=str, ensure_ascii=False)}"
        })
        
        state["current_step"] = "identify_columns"
        return state
    
    def _identify_key_columns(self, state: MetadataExtractionState) -> MetadataExtractionState:
        """识别关键列（设备ID和时间列）"""
        df = state["dataframe"]
        
        # 构建提示词
        columns_info = []
        for col in df.columns:
            sample_values = df[col].dropna().head(5).astype(str).tolist()
            columns_info.append({
                "name": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
                "sample_values": sample_values
            })
        
        prompt = f"""
        请分析以下数据集的列信息，识别每列的业务含义，特别需要识别：
        1. 设备ID列（通常包含设备标识符、编号等）
        2. 时间列（时间戳、日期等）
        3. 其他业务含义列
        
        列信息：
        {json.dumps(columns_info, ensure_ascii=False, indent=2)}
        
        请返回JSON格式的分析结果，包含每列的：
        - name: 列名
        - business_meaning: 业务含义描述
        - is_device_id: 是否为设备ID列
        - is_timestamp: 是否为时间列
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="你是一个数据分析专家，擅长识别数据集中各列的业务含义。"),
                HumanMessage(content=prompt)
            ])
            
            # 解析响应
            columns_analysis = json.loads(response.content)
            state["columns_metadata"] = columns_analysis
            
            state["messages"].append({
                "role": "assistant",
                "content": f"列分析完成: {response.content}"
            })
            
        except Exception as e:
            logger.error(f"列识别失败: {e}")
            # 使用默认分析
            state["columns_metadata"] = [
                {
                    "name": col,
                    "business_meaning": "待分析",
                    "is_device_id": False,
                    "is_timestamp": False
                }
                for col in df.columns
            ]
        
        state["current_step"] = "extract_time_info"
        return state
    
    def _extract_time_information(self, state: MetadataExtractionState) -> MetadataExtractionState:
        """提取时间信息"""
        df = state["dataframe"]
        
        # 查找时间列
        time_columns = [
            col_info["name"] for col_info in state["columns_metadata"]
            if col_info.get("is_timestamp", False)
        ]
        
        if time_columns:
            time_col = time_columns[0]  # 使用第一个时间列
            try:
                # 尝试解析时间
                time_series = pd.to_datetime(df[time_col], errors='coerce')
                time_series = time_series.dropna()
                
                if not time_series.empty:
                    state["time_range_start"] = time_series.min()
                    state["time_range_end"] = time_series.max()
                    
                    # 计算采样率
                    if len(time_series) > 1:
                        time_diff = time_series.diff().dropna()
                        median_interval = time_diff.median()
                        state["sampling_rate"] = str(median_interval)
                
            except Exception as e:
                logger.warning(f"时间信息提取失败: {e}")
        
        state["current_step"] = "generate_description"
        return state
    
    def _generate_dataset_description(self, state: MetadataExtractionState) -> MetadataExtractionState:
        """生成数据集描述"""
        df = state["dataframe"]
        
        # 构建描述提示词
        dataset_info = {
            "file_name": Path(state["file_path"]).name,
            "shape": df.shape,
            "columns": [col["name"] for col in state["columns_metadata"]],
            "time_range": {
                "start": state.get("time_range_start"),
                "end": state.get("time_range_end")
            },
            "sampling_rate": state.get("sampling_rate"),
            "user_input": state.get("user_input")
        }
        
        prompt = f"""
        请为以下数据集生成一个简要的描述，描述应该包括：
        1. 这是什么类型的数据集
        2. 描述了什么内容/系统的运行数据
        3. 时间范围跨度
        4. 时间采样率
        
        数据集信息：
        {json.dumps(dataset_info, default=str, ensure_ascii=False, indent=2)}
        
        请用中文生成一个简洁明了的描述。
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="你是一个数据分析专家，擅长为数据集生成准确的描述。"),
                HumanMessage(content=prompt)
            ])
            
            state["dataset_description"] = response.content
            
        except Exception as e:
            logger.error(f"描述生成失败: {e}")
            state["dataset_description"] = f"数据集包含{df.shape[0]}行{df.shape[1]}列数据"
        
        state["current_step"] = "analyze_quality"
        return state
    
    def _analyze_data_quality(self, state: MetadataExtractionState) -> MetadataExtractionState:
        """分析数据质量"""
        df = state["dataframe"]
        
        # 计算质量指标
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        missing_ratio = missing_cells / total_cells if total_cells > 0 else 0
        
        duplicate_rows = df.duplicated().sum()
        completeness = 1 - missing_ratio
        
        # 质量评分（简单算法）
        quality_score = completeness * 0.6 + (1 - duplicate_rows / df.shape[0]) * 0.4
        quality_score = max(0, min(1, quality_score)) * 100
        
        # 识别质量问题
        issues = []
        recommendations = []
        
        if missing_ratio > 0.1:
            issues.append(f"缺失值比例较高: {missing_ratio:.2%}")
            recommendations.append("建议检查数据收集过程，处理缺失值")
        
        if duplicate_rows > 0:
            issues.append(f"存在重复行: {duplicate_rows}行")
            recommendations.append("建议去除重复数据")
        
        state["quality_metrics"] = {
            "total_rows": int(df.shape[0]),
            "total_columns": int(df.shape[1]),
            "missing_value_ratio": float(missing_ratio),
            "duplicate_rows": int(duplicate_rows),
            "data_completeness": float(completeness),
            "quality_score": float(quality_score),
            "quality_issues": issues,
            "recommendations": recommendations
        }
        
        state["current_step"] = "suggest_tags"
        return state
    
    def _suggest_tags_and_domains(self, state: MetadataExtractionState) -> MetadataExtractionState:
        """建议标签和应用领域"""
        
        # 基于列名和描述建议标签
        columns = [col["name"] for col in state["columns_metadata"]]
        description = state.get("dataset_description", "")
        
        prompt = f"""
        基于以下数据集信息，请建议合适的标签和应用领域：
        
        数据集描述: {description}
        列名: {', '.join(columns)}
        
        请返回JSON格式的建议，包含：
        - industry: 所属行业
        - tags: 相关标签列表
        - analysis_domains: 可用于分析的领域列表
        - applicable_algorithms: 可能适用的算法列表
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="你是一个数据科学专家，擅长为数据集分类和标记。"),
                HumanMessage(content=prompt)
            ])
            
            suggestions = json.loads(response.content)
            state["suggested_industry"] = suggestions.get("industry")
            state["suggested_tags"] = suggestions.get("tags", [])
            state["suggested_domains"] = suggestions.get("analysis_domains", [])
            state["suggested_algorithms"] = suggestions.get("applicable_algorithms", [])
            
        except Exception as e:
            logger.error(f"标签建议失败: {e}")
            state["suggested_tags"] = ["数据分析"]
            state["suggested_domains"] = ["通用分析"]
            state["suggested_algorithms"] = ["统计分析"]
        
        state["current_step"] = "await_user_input"
        return state
    
    def _await_user_input(self, state: MetadataExtractionState) -> MetadataExtractionState:
        """等待用户输入（在实际应用中，这里会暂停等待用户确认）"""
        state["awaiting_user_input"] = True
        state["current_step"] = "finalize_metadata"
        return state
    
    def _finalize_metadata(self, state: MetadataExtractionState) -> MetadataExtractionState:
        """完成元数据提取"""
        state["awaiting_user_input"] = False
        state["current_step"] = "completed"
        
        logger.info(f"元数据提取完成: {state['dataset_id']}")
        return state 