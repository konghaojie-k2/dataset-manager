#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Processing Agent - 智能自主分析 Agent

负责数据集分析、业务分析、质量分析等任务。
文件上传后自动分析数据特征，自主决定执行哪些分析。
"""

from langchain.agents import create_agent
from loguru import logger

from src.llms import get_reasoning_llm
from src.agents.data_processing.tools import DATA_PROCESSING_TOOLS
from src.agents.data_processing.prompts import SYSTEM_PROMPT
from src.config.settings import get_settings, setup_logging

# 初始化日志系统（LangGraph Agent 在独立进程中运行）
try:
    config = get_settings()
    setup_logging(config)
    logger.info("Data Processing Agent 日志系统已初始化")
except Exception as e:
    logger.warning(f"日志系统初始化失败: {e}，使用默认日志配置")


# ===== Agent 状态定义 =====

# 直接使用默认的 AgentState，不添加自定义字段
# 如果需要在工具之间共享数据，请在工具内部处理
# 不要在 AgentState 中添加列表或字典类型字段，会导致序列化错误


# ===== 创建 Agent Graph =====

def create_graph():
    """创建 Data Processing Agent 图

    使用 LangChain 1.0+ 的 create_agent 创建一个 React Agent，
    该 Agent 可以自主决定调用哪些工具来完成数据分析任务。
    """
    # 获取 LLM（使用统一的 LLM 管理模块）
    llm = get_reasoning_llm()

    # 创建 Agent（LangChain 1.0+ 推荐方式）
    graph = create_agent(
        model=llm,
        tools=DATA_PROCESSING_TOOLS,
        system_prompt=SYSTEM_PROMPT
    )

    logger.info("Data Processing Agent 创建完成")
    return graph


# ===== 导出 graph（langgraph dev 会自动加载）=====

graph = create_graph()


# ===== 便捷函数 =====

async def analyze_dataset(dataset_id: str, user_message: str = ""):
    """分析数据集（便捷函数）

    Args:
        dataset_id: 数据集ID
        user_message: 用户可选的额外消息

    Returns:
        分析结果
    """
    from langchain_core.messages import HumanMessage

    logger.info(f"开始分析数据集: {dataset_id}")

    # 创建初始消息
    if user_message:
        message = f"{user_message}\n\n请分析数据集 {dataset_id}"
    else:
        message = f"请分析数据集 {dataset_id}"

    # 运行 Agent
    initial_state = {
        "messages": [HumanMessage(content=message)]
    }

    # TODO: 使用流式执行以支持实时进度反馈
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"analysis_{dataset_id}"}}
    )

    logger.info(f"数据集分析完成: {dataset_id}")
    return result


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        logger.info("测试 Data Processing Agent")
        logger.info(f"Graph 类型: {type(graph)}")
        logger.info("Agent 创建成功")

    asyncio.run(test())
