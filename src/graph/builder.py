"""
工作流构建器模块

负责构建和配置数据分析工作流，定义节点之间的连接关系
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from .state import AnalysisState
from .nodes import (
    load_data_node,
    basic_analysis_node,
    detailed_analysis_node,
    generate_insights_node,
    create_recommendations_node,
    identify_device_time_columns_node,
    analyze_business_meaning_node,
    analyze_control_relationships_node
)


class AnalysisWorkflowBuilder:
    """分析工作流构建器"""
    
    def __init__(self):
        """初始化构建器"""
        self.graph = None
        self.checkpointer = MemorySaver()
        logger.info("工作流构建器初始化完成")
    
    def build_workflow(self) -> StateGraph:
        """构建完整的分析工作流
        
        Returns:
            StateGraph: 编译后的工作流图
        """
        logger.info("开始构建分析工作流")
        
        # 创建状态图
        workflow = StateGraph(AnalysisState)
        
        # 添加节点
        workflow.add_node("load_data_step", load_data_node)
        workflow.add_node("basic_analysis_step", basic_analysis_node)
        workflow.add_node("detailed_analysis_step", detailed_analysis_node)
        workflow.add_node("generate_insights_step", generate_insights_node)
        workflow.add_node("create_recommendations_step", create_recommendations_node)
        
        # 设置入口点
        workflow.set_entry_point("load_data_step")
        
        # 添加边（定义节点之间的连接）
        workflow.add_edge("load_data_step", "basic_analysis_step")
        workflow.add_edge("basic_analysis_step", "detailed_analysis_step")
        workflow.add_edge("detailed_analysis_step", "generate_insights_step")
        workflow.add_edge("generate_insights_step", "create_recommendations_step")
        workflow.add_edge("create_recommendations_step", END)
        
        # 编译工作流
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("分析工作流构建完成")
        return self.graph
    
    def build_simple_workflow(self) -> StateGraph:
        """构建简化的分析工作流（仅基础分析）
        
        Returns:
            StateGraph: 编译后的简化工作流图
        """
        logger.info("开始构建简化分析工作流")
        
        # 创建状态图
        workflow = StateGraph(AnalysisState)
        
        # 添加节点
        workflow.add_node("load_data_step", load_data_node)
        workflow.add_node("basic_analysis_step", basic_analysis_node)
        workflow.add_node("create_recommendations_step", create_recommendations_node)
        
        # 设置入口点
        workflow.set_entry_point("load_data_step")
        
        # 添加边
        workflow.add_edge("load_data_step", "basic_analysis_step")
        workflow.add_edge("basic_analysis_step", "create_recommendations_step")
        workflow.add_edge("create_recommendations_step", END)
        
        # 编译工作流
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("简化分析工作流构建完成")
        return self.graph
    
    def build_custom_workflow(self, template: Dict[str, Any]) -> StateGraph:
        """根据模板构建自定义工作流
        
        Args:
            template: 工作流模板
            
        Returns:
            StateGraph: 编译后的工作流图
        """
        try:
            logger.info(f"开始构建自定义工作流: {template.get('name', 'Unknown')}")
            
            # 创建状态图
            workflow = StateGraph(AnalysisState)
            
            # 添加节点
            for node_name, node_func in template["nodes"].items():
                workflow.add_node(node_name, node_func)
            
            # 添加边
            for edge in template["edges"]:
                if len(edge) == 2:
                    workflow.add_edge(edge[0], edge[1])
                elif len(edge) == 3:
                    workflow.add_conditional_edges(edge[0], edge[1], edge[2])
            
            # 设置入口点
            workflow.set_entry_point(template["entry_point"])
            
            # 设置结束点
            for finish_node in template["finish_nodes"]:
                workflow.add_edge(finish_node, END)
            
            # 编译工作流
            compiled_workflow = workflow.compile(
                checkpointer=self.checkpointer,
                interrupt_before=template.get("interrupt_before", []),
                interrupt_after=template.get("interrupt_after", [])
            )
            
            logger.info("自定义工作流构建完成")
            return compiled_workflow
            
        except Exception as e:
            logger.error(f"自定义工作流构建失败: {e}")
            raise

    def build_industrial_analysis_workflow(self) -> StateGraph:
        """构建工业数据分析工作流
        
        专门用于工业数据的设备识别、业务含义分析和控制原理分析
        
        Returns:
            StateGraph: 编译后的工作流图
        """
        try:
            logger.info("开始构建工业数据分析工作流")
            
            # 创建状态图
            workflow = StateGraph(AnalysisState)
            
            # 添加节点
            workflow.add_node("load_data_step", load_data_node)
            workflow.add_node("basic_analysis_step", basic_analysis_node)
            workflow.add_node("detailed_analysis_step", detailed_analysis_node)
            workflow.add_node("identify_device_time_columns_step", identify_device_time_columns_node)
            workflow.add_node("analyze_business_meaning_step", analyze_business_meaning_node)
            workflow.add_node("analyze_control_relationships_step", analyze_control_relationships_node)
            workflow.add_node("generate_insights_step", generate_insights_node)
            workflow.add_node("create_recommendations_step", create_recommendations_node)
            
            # 设置工作流路径
            workflow.set_entry_point("load_data_step")
            
            # 添加边 - 顺序执行
            workflow.add_edge("load_data_step", "basic_analysis_step")
            workflow.add_edge("basic_analysis_step", "detailed_analysis_step")
            workflow.add_edge("detailed_analysis_step", "identify_device_time_columns_step")
            workflow.add_edge("identify_device_time_columns_step", "analyze_business_meaning_step")
            workflow.add_edge("analyze_business_meaning_step", "analyze_control_relationships_step")
            workflow.add_edge("analyze_control_relationships_step", "generate_insights_step")
            workflow.add_edge("generate_insights_step", "create_recommendations_step")
            
            # 设置结束点
            workflow.add_edge("create_recommendations_step", END)
            
            # 编译工作流
            compiled_workflow = workflow.compile(
                checkpointer=self.checkpointer,
                interrupt_before=[],
                interrupt_after=[]
            )
            
            logger.info("工业数据分析工作流构建完成")
            return compiled_workflow
            
        except Exception as e:
            logger.error(f"工业数据分析工作流构建失败: {e}")
            raise

    def get_workflow_info(self) -> Dict[str, Any]:
        """获取工作流构建器信息
        
        Returns:
            Dict[str, Any]: 构建器信息
        """
        return {
            "available_workflows": [
                "full_analysis",
                "simple_analysis", 
                "custom_analysis",
                "industrial_analysis"
            ],
            "checkpointer_enabled": self.checkpointer is not None,
            "default_config": {
                "max_iterations": 100,
                "timeout": 3600
            }
        }


class WorkflowTemplates:
    """工作流模板类
    
    提供预定义的工作流模板
    """
    
    @staticmethod
    def get_full_analysis_template() -> Dict[str, Any]:
        """获取完整分析模板"""
        return {
            "name": "full_analysis",
            "description": "完整的数据分析工作流",
            "nodes": {
                "load_data_step": load_data_node,
                "basic_analysis_step": basic_analysis_node,
                "detailed_analysis_step": detailed_analysis_node,
                "generate_insights_step": generate_insights_node,
                "create_recommendations_step": create_recommendations_node
            },
            "edges": [
                ("load_data_step", "basic_analysis_step"),
                ("basic_analysis_step", "detailed_analysis_step"),
                ("detailed_analysis_step", "generate_insights_step"),
                ("generate_insights_step", "create_recommendations_step")
            ],
            "entry_point": "load_data_step",
            "finish_nodes": ["create_recommendations_step"]
        }
    
    @staticmethod
    def get_quick_analysis_template() -> Dict[str, Any]:
        """获取快速分析模板"""
        return {
            "name": "quick_analysis",
            "description": "快速数据分析工作流",
            "nodes": {
                "load_data_step": load_data_node,
                "basic_analysis_step": basic_analysis_node,
                "generate_insights_step": generate_insights_node
            },
            "edges": [
                ("load_data_step", "basic_analysis_step"),
                ("basic_analysis_step", "generate_insights_step")
            ],
            "entry_point": "load_data_step",
            "finish_nodes": ["generate_insights_step"]
        }
    
    @staticmethod
    def get_insight_focused_template() -> Dict[str, Any]:
        """获取洞察导向模板"""
        return {
            "name": "insight_focused",
            "description": "专注于洞察生成的工作流",
            "nodes": {
                "load_data_step": load_data_node,
                "basic_analysis_step": basic_analysis_node,
                "detailed_analysis_step": detailed_analysis_node,
                "generate_insights_step": generate_insights_node
            },
            "edges": [
                ("load_data_step", "basic_analysis_step"),
                ("basic_analysis_step", "detailed_analysis_step"),
                ("detailed_analysis_step", "generate_insights_step")
            ],
            "entry_point": "load_data_step",
            "finish_nodes": ["generate_insights_step"]
        }

    @staticmethod
    def get_industrial_analysis_template() -> Dict[str, Any]:
        """获取工业数据分析模板"""
        return {
            "name": "industrial_analysis",
            "description": "专门用于工业数据的分析工作流",
            "nodes": {
                "load_data_step": load_data_node,
                "basic_analysis_step": basic_analysis_node,
                "detailed_analysis_step": detailed_analysis_node,
                "identify_device_time_columns_step": identify_device_time_columns_node,
                "analyze_business_meaning_step": analyze_business_meaning_node,
                "analyze_control_relationships_step": analyze_control_relationships_node,
                "generate_insights_step": generate_insights_node,
                "create_recommendations_step": create_recommendations_node
            },
            "edges": [
                ("load_data_step", "basic_analysis_step"),
                ("basic_analysis_step", "detailed_analysis_step"),
                ("detailed_analysis_step", "identify_device_time_columns_step"),
                ("identify_device_time_columns_step", "analyze_business_meaning_step"),
                ("analyze_business_meaning_step", "analyze_control_relationships_step"),
                ("analyze_control_relationships_step", "generate_insights_step"),
                ("generate_insights_step", "create_recommendations_step")
            ],
            "entry_point": "load_data_step",
            "finish_nodes": ["create_recommendations_step"]
        }


# 创建全局构建器实例
workflow_builder = AnalysisWorkflowBuilder() 