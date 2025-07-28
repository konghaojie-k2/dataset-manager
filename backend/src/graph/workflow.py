"""
数据分析工作流实现模块

参考DeerFlow架构，提供完整的工作流实现和便捷接口
"""

from typing import Dict, Any, Optional, AsyncGenerator
from langgraph.graph import StateGraph
from loguru import logger
from datetime import datetime
import time

from .state import AnalysisState, create_initial_state, update_state_progress
from .builder import AnalysisWorkflowBuilder, WorkflowTemplates


class DataAnalysisWorkflow:
    """数据分析工作流主类
    
    参考DeerFlow的工作流设计，提供完整的数据分析流程
    """
    
    def __init__(self, workflow_type: str = "full"):
        """初始化工作流
        
        Args:
            workflow_type: 工作流类型 ("full", "quick", "insight", "industrial", "custom")
        """
        self.workflow_type = workflow_type
        self.builder = AnalysisWorkflowBuilder()
        self.graph = None
        self._build_workflow()
        
        logger.info(f"数据分析工作流初始化完成，类型: {workflow_type}")
    
    def _build_workflow(self):
        """根据类型构建工作流"""
        if self.workflow_type == "full":
            self.graph = self.builder.build_workflow()
        elif self.workflow_type == "quick":
            self.graph = self.builder.build_simple_workflow()
        elif self.workflow_type == "industrial":
            self.graph = self.builder.build_industrial_analysis_workflow()
        else:
            # 使用模板构建自定义工作流
            template = WorkflowTemplates.get_full_analysis_template()
            if self.workflow_type == "insight":
                template = WorkflowTemplates.get_insight_focused_template()
            elif self.workflow_type == "quick":
                template = WorkflowTemplates.get_quick_analysis_template()
            elif self.workflow_type == "industrial":
                template = WorkflowTemplates.get_industrial_analysis_template()
            
            self.graph = self.builder.build_custom_workflow(template)
    
    async def run_analysis(
        self,
        file_path: str,
        dataset_name: str,
        analysis_goals: list = None,
        user_requirements: str = None,
        config: Dict[str, Any] = None
    ) -> AnalysisState:
        """运行完整的数据分析流程
        
        Args:
            file_path: 数据文件路径
            dataset_name: 数据集名称
            analysis_goals: 分析目标列表
            user_requirements: 用户需求描述
            config: 额外配置
            
        Returns:
            AnalysisState: 最终分析状态
        """
        logger.info(f"开始运行数据分析工作流: {dataset_name}")
        start_time = time.time()
        
        # 创建初始状态
        state = create_initial_state(
            file_path=file_path,
            dataset_name=dataset_name,
            analysis_goals=analysis_goals,
            workflow_type=self.workflow_type,
            user_requirements=user_requirements
        )
        
        # 添加配置
        if config:
            state["workflow_config"] = config
        
        try:
            # 运行工作流
            final_state = await self.graph.ainvoke(
                state,
                config={"configurable": {"thread_id": state["session_id"]}}
            )
            
            # 计算执行时间
            execution_time = time.time() - start_time
            final_state["execution_time"] = execution_time
            final_state["progress"] = 100.0
            
            logger.info(f"数据分析工作流完成，耗时: {execution_time:.2f}秒")
            return final_state
            
        except Exception as e:
            error_msg = f"工作流执行失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["current_step"] = "failed"
            return state
    
    async def run_analysis_stream(
        self,
        file_path: str,
        dataset_name: str,
        analysis_goals: list = None,
        user_requirements: str = None,
        config: Dict[str, Any] = None
    ) -> AsyncGenerator[AnalysisState, None]:
        """流式运行数据分析（实时返回中间结果）
        
        Args:
            file_path: 数据文件路径
            dataset_name: 数据集名称
            analysis_goals: 分析目标列表
            user_requirements: 用户需求描述
            config: 额外配置
            
        Yields:
            AnalysisState: 每个步骤的状态更新
        """
        logger.info(f"开始流式运行数据分析工作流: {dataset_name}")
        
        # 创建初始状态
        state = create_initial_state(
            file_path=file_path,
            dataset_name=dataset_name,
            analysis_goals=analysis_goals,
            workflow_type=self.workflow_type,
            user_requirements=user_requirements
        )
        
        if config:
            state["workflow_config"] = config
        
        try:
            # 流式执行工作流
            async for step_state in self.graph.astream(
                state,
                config={"configurable": {"thread_id": state["session_id"]}}
            ):
                yield step_state
                
        except Exception as e:
            error_msg = f"流式工作流执行失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["current_step"] = "failed"
            yield state
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """获取工作流信息"""
        return {
            "workflow_type": self.workflow_type,
            "builder_info": self.builder.get_workflow_info(),
            "graph_compiled": self.graph is not None
        }


# 全局工作流实例
_workflow_instances = {}

def get_workflow(workflow_type: str = "full") -> DataAnalysisWorkflow:
    """获取工作流实例（单例模式）
    
    Args:
        workflow_type: 工作流类型
        
    Returns:
        DataAnalysisWorkflow: 工作流实例
    """
    if workflow_type not in _workflow_instances:
        _workflow_instances[workflow_type] = DataAnalysisWorkflow(workflow_type)
    
    return _workflow_instances[workflow_type]


# 便捷函数
async def run_full_analysis(
    file_path: str,
    dataset_name: str,
    analysis_goals: list = None,
    user_requirements: str = None,
    config: Dict[str, Any] = None
) -> AnalysisState:
    """运行完整数据分析
    
    Args:
        file_path: 数据文件路径
        dataset_name: 数据集名称
        analysis_goals: 分析目标列表
        user_requirements: 用户需求描述
        config: 额外配置
        
    Returns:
        AnalysisState: 分析结果状态
    """
    workflow = get_workflow("full")
    return await workflow.run_analysis(
        file_path=file_path,
        dataset_name=dataset_name,
        analysis_goals=analysis_goals,
        user_requirements=user_requirements,
        config=config
    )


async def run_quick_analysis(
    file_path: str,
    dataset_name: str,
    analysis_goals: list = None,
    user_requirements: str = None,
    config: Dict[str, Any] = None
) -> AnalysisState:
    """运行快速数据分析
    
    Args:
        file_path: 数据文件路径
        dataset_name: 数据集名称
        analysis_goals: 分析目标列表
        user_requirements: 用户需求描述
        config: 额外配置
        
    Returns:
        AnalysisState: 分析结果状态
    """
    workflow = get_workflow("quick")
    return await workflow.run_analysis(
        file_path=file_path,
        dataset_name=dataset_name,
        analysis_goals=analysis_goals,
        user_requirements=user_requirements,
        config=config
    )


async def run_insight_analysis(
    file_path: str,
    dataset_name: str,
    analysis_goals: list = None,
    user_requirements: str = None,
    config: Dict[str, Any] = None
) -> AnalysisState:
    """运行洞察导向分析
    
    Args:
        file_path: 数据文件路径
        dataset_name: 数据集名称
        analysis_goals: 分析目标列表
        user_requirements: 用户需求描述
        config: 额外配置
        
    Returns:
        AnalysisState: 分析结果状态
    """
    workflow = get_workflow("insight")
    return await workflow.run_analysis(
        file_path=file_path,
        dataset_name=dataset_name,
        analysis_goals=analysis_goals,
        user_requirements=user_requirements,
        config=config
    )


async def run_industrial_analysis(
    file_path: str,
    dataset_name: str,
    analysis_goals: list = None,
    user_requirements: str = None,
    config: Dict[str, Any] = None
) -> AnalysisState:
    """运行工业数据分析
    
    专门用于工业数据的设备识别、业务含义分析和控制原理分析
    
    Args:
        file_path: 数据文件路径
        dataset_name: 数据集名称
        analysis_goals: 分析目标列表
        user_requirements: 用户需求描述
        config: 额外配置
        
    Returns:
        AnalysisState: 分析结果状态
    """
    workflow = get_workflow("industrial")
    return await workflow.run_analysis(
        file_path=file_path,
        dataset_name=dataset_name,
        analysis_goals=analysis_goals,
        user_requirements=user_requirements,
        config=config
    )


async def run_analysis_stream(
    file_path: str,
    dataset_name: str,
    workflow_type: str = "full",
    analysis_goals: list = None,
    user_requirements: str = None,
    config: Dict[str, Any] = None
) -> AsyncGenerator[AnalysisState, None]:
    """流式运行数据分析
    
    Args:
        file_path: 数据文件路径
        dataset_name: 数据集名称
        workflow_type: 工作流类型
        analysis_goals: 分析目标列表
        user_requirements: 用户需求描述
        config: 额外配置
        
    Yields:
        AnalysisState: 每个步骤的状态更新
    """
    workflow = get_workflow(workflow_type)
    async for state in workflow.run_analysis_stream(
        file_path=file_path,
        dataset_name=dataset_name,
        analysis_goals=analysis_goals,
        user_requirements=user_requirements,
        config=config
    ):
        yield state


def clear_workflow_cache():
    """清理工作流缓存"""
    global _workflow_instances
    _workflow_instances.clear()
    logger.info("工作流缓存已清理")


def get_available_workflows() -> Dict[str, str]:
    """获取可用的工作流类型
    
    Returns:
        Dict[str, str]: 工作流类型和描述的映射
    """
    return {
        "full": "完整数据分析工作流",
        "quick": "快速数据分析工作流", 
        "insight": "洞察导向分析工作流",
        "industrial": "工业数据分析工作流"
    } 