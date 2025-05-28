"""
工作流状态定义模块

定义数据分析工作流中的状态结构，参考DeerFlow的状态管理模式
"""

from typing import Dict, Any, List, Optional, Union
from typing_extensions import TypedDict
from pathlib import Path
from datetime import datetime


class AnalysisState(TypedDict):
    """分析工作流状态
    
    参考DeerFlow的状态管理模式，包含完整的工作流状态信息
    """
    
    # 基础信息
    session_id: Optional[str]
    workflow_type: Optional[str]  # "full", "quick", "insight", "custom"
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # 输入数据
    file_path: Optional[Union[str, Path]]
    dataset_name: Optional[str]
    analysis_goals: List[str]
    user_requirements: Optional[str]  # 用户的具体需求描述
    
    # 数据信息
    data_info: Optional[Dict[str, Any]]
    column_analyses: Optional[Dict[str, Any]]
    statistical_summary: Optional[Dict[str, Any]]
    data_quality_report: Optional[Dict[str, Any]]
    correlation_matrix: Optional[Dict[str, Any]]
    outliers_info: Optional[Dict[str, Any]]
    
    # 分析结果
    basic_analysis: Optional[str]
    detailed_analysis: Optional[str]
    insights: Optional[str]
    recommendations: Optional[str]
    executive_summary: Optional[str]  # 执行摘要
    
    # 工业数据分析结果
    device_time_identification: Optional[str]  # 设备列和时间列识别结果
    business_meaning_analysis: Optional[str]   # 业务含义分析结果
    control_relationships_analysis: Optional[str]  # 控制原理分析结果
    correlation_analysis: Optional[Dict[str, Any]]  # 相关性分析结果
    
    # 可视化相关
    visualizations: Optional[List[Dict[str, Any]]]
    chart_suggestions: Optional[List[str]]
    
    # 工作流控制
    current_step: str
    completed_steps: List[str]
    failed_steps: List[str]
    errors: List[str]
    warnings: List[str]
    progress: Optional[float]  # 进度百分比 0-100
    
    # 配置
    llm_config: Optional[Dict[str, Any]]
    analysis_config: Optional[Dict[str, Any]]
    workflow_config: Optional[Dict[str, Any]]
    
    # 性能指标
    execution_time: Optional[float]  # 总执行时间（秒）
    step_times: Optional[Dict[str, float]]  # 各步骤执行时间
    memory_usage: Optional[Dict[str, Any]]  # 内存使用情况
    
    # 元数据
    metadata: Optional[Dict[str, Any]]  # 额外的元数据信息
    tags: Optional[List[str]]  # 标签
    version: Optional[str]  # 状态版本


class WorkflowConfig(TypedDict):
    """工作流配置"""
    
    # 基础配置
    workflow_type: str
    max_retries: int
    timeout: Optional[int]
    
    # 分析配置
    enable_detailed_analysis: bool
    enable_visualization: bool
    enable_insights: bool
    max_columns_to_analyze: int
    
    # LLM配置
    llm_type: str
    temperature: float
    max_tokens: int
    
    # 输出配置
    output_format: str  # "json", "markdown", "html"
    include_charts: bool
    include_raw_data: bool


class StepResult(TypedDict):
    """单步执行结果"""
    
    step_name: str
    status: str  # "success", "failed", "skipped"
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    result: Optional[Any]
    error: Optional[str]
    metadata: Optional[Dict[str, Any]]


def create_initial_state(
    file_path: Union[str, Path],
    dataset_name: str,
    analysis_goals: List[str] = None,
    workflow_type: str = "full",
    user_requirements: str = None
) -> AnalysisState:
    """创建初始状态
    
    Args:
        file_path: 数据文件路径
        dataset_name: 数据集名称
        analysis_goals: 分析目标列表
        workflow_type: 工作流类型
        user_requirements: 用户需求描述
        
    Returns:
        AnalysisState: 初始化的状态对象
    """
    now = datetime.now()
    
    return AnalysisState(
        # 基础信息
        session_id=f"session_{now.strftime('%Y%m%d_%H%M%S')}",
        workflow_type=workflow_type,
        created_at=now,
        updated_at=now,
        
        # 输入数据
        file_path=str(file_path) if isinstance(file_path, Path) else file_path,
        dataset_name=dataset_name,
        analysis_goals=analysis_goals or ["基础数据分析"],
        user_requirements=user_requirements,
        
        # 数据信息
        data_info=None,
        column_analyses=None,
        statistical_summary=None,
        data_quality_report=None,
        correlation_matrix=None,
        outliers_info=None,
        
        # 分析结果
        basic_analysis=None,
        detailed_analysis=None,
        insights=None,
        recommendations=None,
        executive_summary=None,
        
        # 工业数据分析结果
        device_time_identification=None,
        business_meaning_analysis=None,
        control_relationships_analysis=None,
        correlation_analysis=None,
        
        # 可视化相关
        visualizations=None,
        chart_suggestions=None,
        
        # 工作流控制
        current_step="initialized",
        completed_steps=[],
        failed_steps=[],
        errors=[],
        warnings=[],
        progress=0.0,
        
        # 配置
        llm_config=None,
        analysis_config=None,
        workflow_config=None,
        
        # 性能指标
        execution_time=None,
        step_times={},
        memory_usage=None,
        
        # 元数据
        metadata={},
        tags=[],
        version="1.0"
    )


def update_state_progress(state: AnalysisState, step_name: str, progress: float) -> AnalysisState:
    """更新状态进度
    
    Args:
        state: 当前状态
        step_name: 当前步骤名称
        progress: 进度百分比
        
    Returns:
        AnalysisState: 更新后的状态
    """
    state["current_step"] = step_name
    state["progress"] = progress
    state["updated_at"] = datetime.now()
    
    return state 