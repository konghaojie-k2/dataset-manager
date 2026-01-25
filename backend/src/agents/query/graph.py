#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Agent - 数据查询助手

负责数据集搜索、预览、回答用户问题
"""

from langchain.agents import create_agent
from loguru import logger
import os
from src.llms import get_reasoning_llm
from src.agents.query.tools import QUERY_TOOLS
from src.agents.query.prompts import SYSTEM_PROMPT
from src.config.settings import get_settings, setup_logging

# 初始化日志系统（LangGraph Agent 在独立进程中运行）
try:
    config = get_settings()
    setup_logging(config)
    logger.info("Query Agent 日志系统已初始化")
except Exception as e:
    logger.warning(f"日志系统初始化失败: {e}，使用默认日志配置")


os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = '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'
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_PROJECT"] = "default"  # 可选，默认为 "default"


# ===== Agent 状态定义 =====

# 直接使用默认的 AgentState，不添加自定义字段


# ===== 创建 Agent Graph =====

def create_graph():
    """创建 Query Agent 图

    使用 LangChain 1.0+ 的 create_agent 创建一个 React Agent，
    该 Agent 可以帮助用户搜索、预览和了解数据集。
    """
    # 获取 LLM（使用统一的 LLM 管理模块）
    llm = get_reasoning_llm()

    # 创建 Agent（LangChain 1.0+ 推荐方式）
    graph = create_agent(
        model=llm,
        tools=QUERY_TOOLS,
        system_prompt=SYSTEM_PROMPT
    )

    logger.info("Query Agent 创建完成")
    return graph


# ===== 导出 graph（langgraph dev 会自动加载）=====

graph = create_graph()


# ===== 便捷函数 =====

async def query_datasets(user_query: str):
    """查询数据集（便捷函数）

    Args:
        user_query: 用户查询

    Returns:
        查询结果
    """
    from langchain_core.messages import HumanMessage

    logger.info(f"查询数据集: {user_query}")

    # 运行 Agent
    initial_state = {
        "messages": [HumanMessage(content=user_query)]
    }

    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"query_{hash(user_query)}"}}
    )

    logger.info(f"查询完成")
    return result


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        logger.info("测试 Query Agent")
        logger.info(f"Graph 类型: {type(graph)}")
        logger.info("Agent 创建成功")

    asyncio.run(test())
