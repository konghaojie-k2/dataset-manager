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
    load_data,
    basic_analysis,
    detailed_analysis,
    generate_insights,
    create_recommendations
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
        workflow.add_node("load_data", load_data)
        workflow.add_node("basic_analysis", basic_analysis)
        workflow.add_node("detailed_analysis", detailed_analysis)
        workflow.add_node("generate_insights", generate_insights)
        workflow.add_node("create_recommendations", create_recommendations)
        
        # 设置入口点
        workflow.set_entry_point("load_data")
        
        # 添加边（定义节点之间的连接）
        workflow.add_edge("load_data", "basic_analysis")
        workflow.add_edge("basic_analysis", "detailed_analysis")
        workflow.add_edge("detailed_analysis", "generate_insights")
        workflow.add_edge("generate_insights", "create_recommendations")
        workflow.add_edge("create_recommendations", END)
        
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
        workflow.add_node("load_data", load_data)
        workflow.add_node("basic_analysis", basic_analysis)
        workflow.add_node("create_recommendations", create_recommendations)
        
        # 设置入口点
        workflow.set_entry_point("load_data")
        
        # 添加边
        workflow.add_edge("load_data", "basic_analysis")
        workflow.add_edge("basic_analysis", "create_recommendations")
        workflow.add_edge("create_recommendations", END)
        
        # 编译工作流
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("简化分析工作流构建完成")
        return self.graph
    
    def build_custom_workflow(self, nodes_config: Dict[str, Any]) -> StateGraph:
        """构建自定义工作流
        
        Args:
            nodes_config: 节点配置，包含要包含的节点和连接关系
            
        Returns:
            StateGraph: 编译后的自定义工作流图
        """
        logger.info("开始构建自定义分析工作流")
        
        # 创建状态图
        workflow = StateGraph(AnalysisState)
        
        # 可用节点映射
        available_nodes = {
            "load_data": load_data,
            "basic_analysis": basic_analysis,
            "detailed_analysis": detailed_analysis,
            "generate_insights": generate_insights,
            "create_recommendations": create_recommendations
        }
        
        # 添加配置中指定的节点
        nodes_to_add = nodes_config.get("nodes", ["load_data", "basic_analysis", "create_recommendations"])
        for node_name in nodes_to_add:
            if node_name in available_nodes:
                workflow.add_node(node_name, available_nodes[node_name])
                logger.debug(f"添加节点: {node_name}")
        
        # 设置入口点
        entry_point = nodes_config.get("entry_point", "load_data")
        workflow.set_entry_point(entry_point)
        
        # 添加边
        edges = nodes_config.get("edges", [])
        for edge in edges:
            if len(edge) == 2:
                from_node, to_node = edge
                if to_node == "END":
                    workflow.add_edge(from_node, END)
                else:
                    workflow.add_edge(from_node, to_node)
                logger.debug(f"添加边: {from_node} -> {to_node}")
        
        # 编译工作流
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("自定义分析工作流构建完成")
        return self.graph
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """获取工作流信息
        
        Returns:
            Dict[str, Any]: 工作流信息
        """
        if not self.graph:
            return {"status": "未构建", "nodes": [], "edges": []}
        
        # 获取图的基本信息
        nodes = list(self.graph.nodes.keys()) if hasattr(self.graph, 'nodes') else []
        
        return {
            "status": "已构建",
            "nodes": nodes,
            "checkpointer": "MemorySaver",
            "compiled": True
        }


class WorkflowTemplates:
    """工作流模板类"""
    
    @staticmethod
    def get_full_analysis_template() -> Dict[str, Any]:
        """获取完整分析模板配置
        
        Returns:
            Dict[str, Any]: 完整分析工作流配置
        """
        return {
            "name": "完整分析工作流",
            "description": "包含所有分析步骤的完整工作流",
            "nodes": [
                "load_data",
                "basic_analysis", 
                "detailed_analysis",
                "generate_insights",
                "create_recommendations"
            ],
            "entry_point": "load_data",
            "edges": [
                ("load_data", "basic_analysis"),
                ("basic_analysis", "detailed_analysis"),
                ("detailed_analysis", "generate_insights"),
                ("generate_insights", "create_recommendations"),
                ("create_recommendations", "END")
            ]
        }
    
    @staticmethod
    def get_quick_analysis_template() -> Dict[str, Any]:
        """获取快速分析模板配置
        
        Returns:
            Dict[str, Any]: 快速分析工作流配置
        """
        return {
            "name": "快速分析工作流",
            "description": "仅包含基础分析的快速工作流",
            "nodes": [
                "load_data",
                "basic_analysis",
                "create_recommendations"
            ],
            "entry_point": "load_data",
            "edges": [
                ("load_data", "basic_analysis"),
                ("basic_analysis", "create_recommendations"),
                ("create_recommendations", "END")
            ]
        }
    
    @staticmethod
    def get_insight_focused_template() -> Dict[str, Any]:
        """获取洞察导向模板配置
        
        Returns:
            Dict[str, Any]: 洞察导向工作流配置
        """
        return {
            "name": "洞察导向工作流",
            "description": "专注于深度洞察生成的工作流",
            "nodes": [
                "load_data",
                "detailed_analysis",
                "generate_insights",
                "create_recommendations"
            ],
            "entry_point": "load_data",
            "edges": [
                ("load_data", "detailed_analysis"),
                ("detailed_analysis", "generate_insights"),
                ("generate_insights", "create_recommendations"),
                ("create_recommendations", "END")
            ]
        }


# 创建全局构建器实例
workflow_builder = AnalysisWorkflowBuilder() 