#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Agent 工具集

包含数据集搜索、预览、意图分析等工具
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from loguru import logger
import json

# 延迟导入以避免循环依赖


# ===== 工具输入 Schema 定义 =====

class SearchDatasetsInput(BaseModel):
    """搜索数据集输入（LLM增强的智能搜索工具）"""
    query: str = Field(description="用户原始查询")
    intent_result: Optional[str] = Field(default=None, description="意图识别工具的JSON输出（可选）")
    tags: Optional[List[str]] = Field(default=None, description="标签过滤（可选，向后兼容）")
    industry: Optional[str] = Field(default=None, description="行业过滤（可选，向后兼容）")
    limit: int = Field(default=10, description="返回结果数量限制（可选）")


class GetDatasetPreviewInput(BaseModel):
    """数据集预览输入"""
    dataset_id: str = Field(description="数据集ID")
    rows: int = Field(default=10, description="预览行数")


class GetDatasetDetailsInput(BaseModel):
    """获取数据集详情输入"""
    dataset_id: str = Field(description="数据集ID")


class AnalyzeIntentInput(BaseModel):
    """意图分析输入"""
    query: str = Field(description="用户查询")


class SearchAnalysisResultsInput(BaseModel):
    """搜索分析结果输入（LLM增强的深层次分析）"""
    query: str = Field(description="用户原始查询")
    intent_result: Optional[str] = Field(default=None, description="意图识别工具的JSON输出（可选）")
    limit: int = Field(default=10, description="返回结果数量限制（可选）")


class ClarifyIntentInput(BaseModel):
    """意图澄清输入"""
    query: str = Field(description="用户原始查询")
    intent_result: Optional[str] = Field(default=None, description="意图识别工具的JSON输出（可选）")
    session_context: Optional[str] = Field(default=None, description="会话上下文的JSON字符串（可选，用于预填表单）")


# ===== 工具实现 =====

@tool("search_datasets", args_schema=SearchDatasetsInput)
async def search_datasets_tool(
    query: str,
    intent_result: Optional[str] = None,
    tags: Optional[List[str]] = None,
    industry: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    LLM增强的智能数据集搜索工具（Subagent模式）
    
    根据用户query智能判断返回类型（数量、列表、消息等），使用LLM进行语义理解和结果生成。
    支持接收意图识别工具的输出，也可以直接使用用户query。
    
    Args:
        query: 用户原始查询
        intent_result: 意图识别工具的JSON输出（可选）
        tags: 标签列表（可选，向后兼容）
        industry: 行业（可选，向后兼容）
        limit: 返回结果数量限制（可选）
    
    Returns:
        JSON 字符串，根据查询类型返回不同格式：
        - count类型: {"type": "count", "value": 数字, "message": "消息"}
        - list类型: {"type": "list", "datasets": [数据集列表], "count": 数量}
        - not_found类型: {"type": "not_found", "message": "未找到消息"}
        - message类型: {"type": "message", "message": "自定义消息"}
    """
    logger.info(f"[Agent Tool] LLM增强搜索: query={query}, intent_result={'provided' if intent_result else 'none'}")

    try:
        from ...core.dataset_service_factory import create_dataset_service
        from ...core.search_service import SearchService
        
        dataset_service = create_dataset_service()
        search_service = SearchService()

        # 1. 获取所有数据集（异步调用）
        all_datasets = await dataset_service.list_datasets()
        logger.info(f"[Agent Tool] 数据库中共有 {len(all_datasets)} 个数据集")
        
        # 2. 使用SearchService进行LLM增强搜索
        try:
            llm_result = await search_service.search(query, all_datasets, intent_result)
            # 处理搜索结果
            final_result = search_service.process_search_result(llm_result, all_datasets, query, limit)
            return json.dumps(final_result, ensure_ascii=False)
            
        except Exception as llm_error:
            logger.warning(f"[Agent Tool] LLM调用失败，降级到传统搜索: {llm_error}")
            # 降级到传统关键词匹配逻辑
            fallback_result = search_service.fallback_keyword_search(
                query, all_datasets, tags, industry, limit
            )
            return json.dumps(fallback_result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Agent Tool] 搜索数据集失败: {e}", exc_info=True)
        return json.dumps({
            "type": "message",
            "message": f"搜索失败: {str(e)}",
            "error": str(e),
            "query": query
        }, ensure_ascii=False)


@tool("get_dataset_preview", args_schema=GetDatasetPreviewInput)
async def get_dataset_preview_tool(
    dataset_id: str,
    rows: int = 10
) -> str:
    """
    获取数据集预览

    返回数据集的前N行数据，用于快速查看数据结构和内容。

    Args:
        dataset_id: 数据集ID
        rows: 预览行数（默认10行）

    Returns:
        JSON 字符串，包含以下字段：
        - shape: 数据形状 (行数, 列数)
        - columns: 列名列表
        - data: 数据样本（列表）
        - dtypes: 数据类型字典
    """
    logger.info(f"[Agent Tool] 获取数据集预览: {dataset_id}, rows={rows}")

    try:
        from ...core.dataset_service_factory import create_dataset_service
        dataset_service = create_dataset_service()
        preview = dataset_service.get_dataset_preview(dataset_id, rows)

        if preview is None:
            return json.dumps({
                "error": "无法获取预览",
                "message": "数据集可能不存在或格式不支持",
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        logger.info(f"[Agent Tool] 数据集预览获取成功: {dataset_id}")
        return json.dumps(preview, ensure_ascii=False, default=str)

    except Exception as e:
        logger.error(f"[Agent Tool] 获取数据集预览失败: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "dataset_id": dataset_id
        }, ensure_ascii=False)


@tool("get_dataset_details", args_schema=GetDatasetDetailsInput)
async def get_dataset_details_tool(dataset_id: str) -> str:
    """
    获取数据集详细信息

    获取数据集的完整元数据信息，包括：
    - 基础信息（名称、描述、标签）
    - 数据统计（行数、列数、文件大小）
    - 分析状态（是否已分析、分析类型）
    - 分析结果（如果有）

    Args:
        dataset_id: 数据集ID

    Returns:
        JSON 字符串，包含数据集详细信息字典
    """
    logger.info(f"[Agent Tool] 获取数据集详情: {dataset_id}")

    try:
        from ...core.dataset_service_factory import create_dataset_service
        dataset_service = create_dataset_service()
        dataset = dataset_service.get_dataset(dataset_id)

        if not dataset:
            return json.dumps({
                "error": "数据集不存在",
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        # 检查是否有业务分析结果
        has_business_analysis = bool(
            dataset.business_meaning_analysis or
            dataset.control_relationships_analysis
        )

        # 检查是否有质量分析结果
        has_quality_analysis = bool(
            hasattr(dataset, 'quality_analysis_results') and
            dataset.quality_analysis_results
        )

        # 检查是否有增强分析结果
        has_enhanced_analysis = bool(
            hasattr(dataset, 'industrial_domain') and
            dataset.industrial_domain
        )

        # 构建详细信息
        details = {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "tags": dataset.tags or [],
            "industrial_domain": dataset.industrial_domain or dataset.industry,
            "file_size": dataset.file_size,
            "upload_time": dataset.upload_time.isoformat() if dataset.upload_time else None,
            "processing_status": dataset.processing_status,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "has_business_analysis": has_business_analysis,
            "has_quality_analysis": has_quality_analysis,
            "has_enhanced_analysis": has_enhanced_analysis,
        }

        logger.info(f"[Agent Tool] 数据集详情获取成功: {dataset_id}")
        return json.dumps(details, ensure_ascii=False, default=str)

    except Exception as e:
        logger.error(f"[Agent Tool] 获取数据集详情失败: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "dataset_id": dataset_id
        }, ensure_ascii=False)


@tool("analyze_intent", args_schema=AnalyzeIntentInput)
async def analyze_intent_tool(query: str) -> str:
    """
    分析用户查询意图

    识别用户查询的真实意图，提取关键实体和过滤条件。

    Args:
        query: 用户查询文本

    Returns:
        JSON 字符串，包含以下字段：
        - primary_intent: 主要意图（search, preview, details, other）
        - keywords: 提取的关键词
        - filters: 过滤条件
        - entities: 识别的实体（数据集名称、ID等）
    """
    logger.info(f"[Agent Tool] 分析查询意图: {query}")

    try:
        from ...core.intent_analysis import IntentAnalysisService
        intent_service = IntentAnalysisService()

        # 使用 LLM 分析意图
        intent = await intent_service.analyze_intent(query, context={})

        logger.info(f"[Agent Tool] 意图分析完成: filters={intent.get('filters')}, sort={intent.get('sort_preference')}")
        return json.dumps(intent, ensure_ascii=False, default=str)

    except Exception as e:
        logger.error(f"[Agent Tool] 意图分析失败: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "query": query
        }, ensure_ascii=False)


@tool("search_analysis_results", args_schema=SearchAnalysisResultsInput)
async def search_analysis_results_tool(
    query: str,
    intent_result: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    LLM增强的分析结果搜索工具（深层次分析）
    
    在数据集的分析结果中进行深层次的语义搜索，包括业务含义、控制关系、洞察、建议等。
    支持接收意图识别工具的输出，也可以直接使用用户query。
    
    Args:
        query: 用户原始查询
        intent_result: 意图识别工具的JSON输出（可选）
        limit: 返回结果数量限制（可选）
    
    Returns:
        JSON 字符串，根据查询类型返回不同格式：
        - analysis类型: {"type": "analysis", "matched_datasets": [匹配结果], "count": 数量, "summary": "摘要"}
        - not_found类型: {"type": "not_found", "message": "未找到消息"}
        - message类型: {"type": "message", "message": "自定义消息"}
    """
    logger.info(f"[Agent Tool] LLM增强分析结果搜索: query={query}, intent_result={'provided' if intent_result else 'none'}")

    try:
        from ...core.dataset_service_factory import create_dataset_service
        from ...core.analysis_search_service import AnalysisSearchService
        
        dataset_service = create_dataset_service()
        analysis_search_service = AnalysisSearchService()

        # 1. 获取所有数据集（需要包含分析结果，异步调用）
        all_datasets = await dataset_service.list_datasets()
        logger.info(f"[Agent Tool] 数据库中共有 {len(all_datasets)} 个数据集")
        
        # 2. 使用AnalysisSearchService进行LLM增强搜索
        try:
            llm_result = await analysis_search_service.search(query, all_datasets, intent_result)
            # 处理搜索结果
            final_result = analysis_search_service.process_search_result(llm_result, all_datasets, query, limit)
            return json.dumps(final_result, ensure_ascii=False)
            
        except Exception as llm_error:
            logger.warning(f"[Agent Tool] LLM调用失败，降级到传统搜索: {llm_error}")
            # 降级到传统关键词匹配逻辑
            fallback_result = analysis_search_service.fallback_keyword_search(
                query, all_datasets, limit
            )
            return json.dumps(fallback_result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Agent Tool] 搜索分析结果失败: {e}", exc_info=True)
        return json.dumps({
            "type": "message",
            "message": f"搜索失败: {str(e)}",
            "error": str(e),
            "query": query
        }, ensure_ascii=False)


@tool("clarify_intent", args_schema=ClarifyIntentInput)
async def clarify_intent_tool(
    query: str,
    intent_result: Optional[str] = None,
    session_context: Optional[str] = None
) -> str:
    """
    意图澄清工具（集成A2UI表单生成）
    
    如果Agent认为意图识别结果不够清晰，调用此工具生成A2UI表单供用户填写。
    表单会在前端动态显示，用户填写后可以重新进行搜索。
    
    Args:
        query: 用户原始查询
        intent_result: 意图识别工具的JSON输出（可选，如果没有则重新分析）
        session_context: 会话上下文的JSON字符串（可选，用于预填表单）
    
    Returns:
        JSON 字符串，包含：
        - needs_clarification: 是否需要澄清（bool）
        - form_schema: A2UI表单Schema（如果需要澄清）
        - message: 澄清消息
        - clarification_reason: 澄清原因
        - intent: 意图分析结果
    """
    logger.info(f"[Agent Tool] 意图澄清: query={query}, intent_result={'provided' if intent_result else 'none'}")

    try:
        from ...core.clarification_service import ClarificationService
        
        clarification_service = ClarificationService()
        
        # 解析会话上下文
        context_dict = None
        if session_context:
            try:
                context_dict = json.loads(session_context) if isinstance(session_context, str) else session_context
            except json.JSONDecodeError:
                logger.warning("会话上下文格式错误，忽略")
        
        # 执行意图澄清
        clarification_result = await clarification_service.clarify_intent(
            query=query,
            intent_result=intent_result,
            session_context=context_dict
        )
        
        logger.info(f"[Agent Tool] 意图澄清完成: needs_clarification={clarification_result.get('needs_clarification')}")
        return json.dumps(clarification_result, ensure_ascii=False, default=str)

    except Exception as e:
        logger.error(f"[Agent Tool] 意图澄清失败: {e}", exc_info=True)
        return json.dumps({
            "needs_clarification": False,
            "message": f"意图澄清失败: {str(e)}",
            "error": str(e),
            "query": query
        }, ensure_ascii=False)


# ===== 工具列表 =====

QUERY_TOOLS = [
    search_datasets_tool,
    search_analysis_results_tool,
    get_dataset_preview_tool,
    get_dataset_details_tool,
    analyze_intent_tool,
    clarify_intent_tool
]
