"""
数据分析工作流图模块

基于LangGraph构建的数据分析工作流，参考DeerFlow的架构设计
包含节点定义、工作流构建器和状态管理
"""

# 状态相关
from .state import (
    AnalysisState,
    WorkflowConfig,
    StepResult,
    create_initial_state,
    update_state_progress
)

# 节点相关
from .nodes import (
    AnalysisNodes,
    analysis_nodes,
    load_data_node,
    basic_analysis_node,
    detailed_analysis_node,
    generate_insights_node,
    create_recommendations_node,
    identify_device_time_columns_node,
    analyze_business_meaning_node,
    analyze_control_relationships_node
)

# 构建器相关
from .builder import (
    AnalysisWorkflowBuilder,
    WorkflowTemplates,
    workflow_builder
)

# 工作流相关
from .workflow import (
    DataAnalysisWorkflow,
    get_workflow,
    run_full_analysis,
    run_quick_analysis,
    run_insight_analysis,
    run_industrial_analysis,
    run_analysis_stream,
    clear_workflow_cache,
    get_available_workflows
)

__all__ = [
    # 状态管理
    "AnalysisState",
    "WorkflowConfig", 
    "StepResult",
    "create_initial_state",
    "update_state_progress",
    
    # 节点
    "AnalysisNodes",
    "analysis_nodes",
    "load_data_node",
    "basic_analysis_node",
    "detailed_analysis_node", 
    "generate_insights_node",
    "create_recommendations_node",
    "identify_device_time_columns_node",
    "analyze_business_meaning_node",
    "analyze_control_relationships_node",
    
    # 构建器
    "AnalysisWorkflowBuilder",
    "WorkflowTemplates",
    "workflow_builder",
    
    # 工作流
    "DataAnalysisWorkflow",
    "get_workflow",
    "run_full_analysis",
    "run_quick_analysis", 
    "run_insight_analysis",
    "run_industrial_analysis",
    "run_analysis_stream",
    "clear_workflow_cache",
    "get_available_workflows",
] 