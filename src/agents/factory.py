"""
Agent 工厂模块

参考 DeerFlow 的简洁设计，提供统一的 Agent 创建接口
"""

from typing import List, Callable, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool

from ..llms import get_llm_by_type
from ..config import LLMType
from ..prompts import apply_prompt_template


# Agent 类型到 LLM 类型的映射
AGENT_LLM_MAP = {
    "metadata": LLMType.REASONING,
    "analysis": LLMType.REASONING, 
    "insight": LLMType.REASONING,
    "basic": LLMType.BASIC,
    "vision": LLMType.VISION
}


def create_agent(
    agent_name: str, 
    agent_type: str, 
    tools: List[BaseTool], 
    prompt_template: str
):
    """工厂函数：创建具有一致配置的 Agent
    
    Args:
        agent_name: Agent 名称
        agent_type: Agent 类型（用于选择 LLM）
        tools: 工具列表
        prompt_template: 提示词模板
        
    Returns:
        创建的 React Agent
    """
    # 获取对应的 LLM 类型
    llm_type = AGENT_LLM_MAP.get(agent_type, LLMType.BASIC)
    
    # 创建 React Agent
    return create_react_agent(
        name=agent_name,
        model=get_llm_by_type(llm_type),
        tools=tools,
        prompt=lambda state: apply_prompt_template(prompt_template, state),
    )


def create_metadata_agent(tools: List[BaseTool] = None) -> Any:
    """创建元数据提取 Agent
    
    Args:
        tools: 工具列表
        
    Returns:
        元数据提取 Agent
    """
    prompt_template = """
    你是一个专业的数据分析师，专门负责提取和分析数据集的元数据信息。
    
    你的任务是：
    1. 分析数据结构和列信息
    2. 识别关键列（设备ID、时间列等）
    3. 提取时间范围信息
    4. 生成数据集描述
    5. 分析数据质量
    6. 建议标签和领域分类
    
    请基于提供的数据信息进行分析，并返回结构化的元数据。
    
    当前状态: {state}
    """
    
    return create_agent(
        agent_name="metadata_extractor",
        agent_type="metadata", 
        tools=tools or [],
        prompt_template=prompt_template
    )


def create_analysis_agent(tools: List[BaseTool] = None) -> Any:
    """创建数据分析 Agent
    
    Args:
        tools: 工具列表
        
    Returns:
        数据分析 Agent
    """
    prompt_template = """
    你是一个资深的数据科学家，专门负责深度数据分析。
    
    你的任务是：
    1. 执行统计分析
    2. 检测异常值和模式
    3. 进行相关性分析
    4. 识别数据趋势
    5. 提供数据洞察
    
    请使用提供的工具进行分析，并生成详细的分析报告。
    
    当前状态: {state}
    """
    
    return create_agent(
        agent_name="data_analyzer",
        agent_type="analysis",
        tools=tools or [],
        prompt_template=prompt_template
    )


def create_insight_agent(tools: List[BaseTool] = None) -> Any:
    """创建洞察生成 Agent
    
    Args:
        tools: 工具列表
        
    Returns:
        洞察生成 Agent
    """
    prompt_template = """
    你是一个商业分析专家，专门负责从数据中提取商业洞察。
    
    你的任务是：
    1. 分析业务模式和趋势
    2. 识别关键业务指标
    3. 提供可操作的建议
    4. 生成商业价值洞察
    5. 预测潜在机会和风险
    
    请基于分析结果生成有价值的商业洞察和建议。
    
    当前状态: {state}
    """
    
    return create_agent(
        agent_name="insight_generator",
        agent_type="insight",
        tools=tools or [],
        prompt_template=prompt_template
    )


def create_basic_agent(tools: List[BaseTool] = None) -> Any:
    """创建基础任务 Agent
    
    Args:
        tools: 工具列表
        
    Returns:
        基础任务 Agent
    """
    prompt_template = """
    你是一个通用的数据助手，负责处理基础的数据任务。
    
    请根据用户的需求，使用提供的工具完成相应的任务。
    
    当前状态: {state}
    """
    
    return create_agent(
        agent_name="basic_assistant",
        agent_type="basic",
        tools=tools or [],
        prompt_template=prompt_template
    )


# 预定义的 Agent 创建函数映射
AGENT_CREATORS = {
    "metadata": create_metadata_agent,
    "analysis": create_analysis_agent,
    "insight": create_insight_agent,
    "basic": create_basic_agent
}


def get_agent(agent_type: str, tools: List[BaseTool] = None) -> Any:
    """获取指定类型的 Agent
    
    Args:
        agent_type: Agent 类型
        tools: 工具列表
        
    Returns:
        创建的 Agent
        
    Raises:
        ValueError: 如果 Agent 类型不支持
    """
    if agent_type not in AGENT_CREATORS:
        raise ValueError(f"不支持的 Agent 类型: {agent_type}")
    
    creator = AGENT_CREATORS[agent_type]
    return creator(tools)


def get_available_agents() -> List[str]:
    """获取可用的 Agent 类型列表
    
    Returns:
        可用的 Agent 类型列表
    """
    return list(AGENT_CREATORS.keys()) 