#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Extension - Port 8000 统一入口

功能：
- 直接处理文件上传
- 保留现有 API 端点
- 反向代理 LangGraph Agent
- WebSocket/SSE 流式进度推送
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
from loguru import logger
from typing import Optional
import asyncio
import json

from src.config.settings import get_settings, setup_logging
from src.core.dataset_service_factory import create_dataset_service
from src.server.dependencies import set_dataset_service, set_tag_service
from src.core.tag_service import TagService

config = get_settings()

# 初始化日志系统
setup_logging(config)
logger.info("FastAPI Extension 启动，日志系统已初始化")

# 初始化数据集服务
dataset_service = create_dataset_service()
tag_service = TagService(config.metadata_dir)

# 设置全局服务实例（供依赖注入使用）
set_dataset_service(dataset_service)
set_tag_service(tag_service)

# ===== 创建 FastAPI 应用 =====

def create_extension_app() -> FastAPI:
    """创建 FastAPI 扩展应用"""

    app = FastAPI(
        title="Dataset Manager API",
        description="数据集管理统一 API 入口 - FastAPI Extension + LangGraph Agents",
        version="2.0.0"
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3003"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ===== 注册现有路由 =====

    # 导入数据集路由（保留上传端点）- 从 routes.py 导入
    # 注意：routes.py 中的路由已经包含 /api/v1 前缀，所以不需要再加 prefix
    try:
        from src.server.routes import router as datasets_router
        app.include_router(datasets_router)  # 不添加 prefix，因为路由本身已包含
        logger.info("数据集路由已注册")
    except Exception as e:
        logger.warning(f"数据集路由导入失败: {e}")

    # 导入其他保留的路由
    try:
        from src.server.api.v1.reports import router as reports_router
        from src.server.api.v1.lineage import router as lineage_router
        from src.server.api.v1.tags import router as tags_router
        from src.server.api.v1.version_control import router as version_control_router

        app.include_router(reports_router)  # 不添加 prefix
        app.include_router(lineage_router)
        app.include_router(tags_router)
        app.include_router(version_control_router)
        logger.info("其他路由已注册")
    except Exception as e:
        logger.warning(f"部分路由导入失败: {e}")

    # ===== 静态文件服务 =====

    # 分析报告 MD 文件
    reports_dir = Path("uploads/reports")
    if reports_dir.exists():
        app.mount("/reports", StaticFiles(directory=str(reports_dir)), name="reports")
        logger.info(f"报告静态文件挂载: {reports_dir}")

    # ===== 健康检查端点 =====

    @app.get("/health")
    async def health():
        """健康检查"""
        return {
            "status": "ok",
            "service": "fastapi-extension",
            "langgraph_url": "http://localhost:2024",
            "version": "2.0.0"
        }

    # ===== Agent 分析触发端点 =====

    @app.post("/api/agents/data_processing_agent/analyze")
    async def trigger_data_processing_agent(
        dataset_id: str,
        background_tasks: BackgroundTasks
    ):
        """
        触发 Data Processing Agent 进行自动分析

        这是文件上传后自动调用的端点，Agent 将自主决定执行哪些分析。
        """
        from src.agents.data_processing import analyze_dataset

        # 后台执行分析
        async def run_analysis():
            try:
                logger.info(f"后台启动 Data Processing Agent 分析: {dataset_id}")
                await analyze_dataset(dataset_id)
                logger.info(f"Data Processing Agent 分析完成: {dataset_id}")
            except Exception as e:
                logger.error(f"Data Processing Agent 分析失败: {e}")

        background_tasks.add_task(run_analysis)

        return {
            "status": "triggered",
            "dataset_id": dataset_id,
            "message": "Agent 分析已启动，请通过 WebSocket 订阅进度"
        }

    @app.post("/api/agents/query_agent/query")
    async def trigger_query_agent(query: str):
        """
        触发 Query Agent 进行数据查询

        用于处理用户的数据集搜索和查询请求。
        """
        from src.agents.query import query_datasets

        result = await query_datasets(query)
        return result

    # ===== WebSocket/SSE 进度推送端点 =====

    # 内存存储进度订阅
    progress_subscribers = {}

    @app.get("/api/analysis/{dataset_id}/progress")
    async def get_analysis_progress(dataset_id: str):
        """
        获取分析进度的 SSE 端点

        前端可以通过 EventSource 订阅此端点以获取实时进度更新。
        """

        async def progress_stream():
            """SSE 进度流"""
            try:
                # 发送初始连接消息
                yield f"event: connected\ndata: {{'dataset_id': '{dataset_id}'}}\n\n"

                # 模拟进度更新（实际应该从 Agent 接收）
                for i in range(0, 101, 10):
                    await asyncio.sleep(1)
                    progress_data = {
                        "type": "analysis_progress",
                        "dataset_id": dataset_id,
                        "current_step": f"分析步骤 {i//25 + 1}",
                        "progress": i,
                        "steps_completed": [f"步骤 {j}" for j in range(i // 25)] if i > 0 else [],
                        "steps_remaining": [f"步骤 {j}" for j in range((i // 25) + 1, 5)]
                    }
                    yield f"event: progress\ndata: {json.dumps(progress_data)}\n\n"

                # 发送完成消息
                yield f"event: complete\ndata: {{'dataset_id': '{dataset_id}', 'status': 'completed'}}\n\n"

            except asyncio.CancelledError:
                logger.info(f"进度流被取消: {dataset_id}")
            except Exception as e:
                logger.error(f"进度流错误: {e}")
                yield f"event: error\ndata: {{'error': '{str(e)}'}}\n\n"

        return StreamingResponse(
            progress_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    # ===== 获取分析结果端点 =====

    @app.get("/api/v1/datasets/{dataset_id}/business-analysis-results")
    async def get_business_analysis_results(dataset_id: str):
        """
        获取业务分析结果

        返回数据集的业务分析结果，包括设备列、时间列、业务含义等。
        """
        try:
            dataset_service = create_dataset_service()
            dataset = dataset_service.get_dataset(dataset_id)

            if not dataset:
                raise HTTPException(status_code=404, detail="数据集不存在")

            # 从 dataset 中提取业务分析结果
            device_columns = []
            time_columns = []

            if hasattr(dataset, 'columns_metadata') and dataset.columns_metadata:
                for col in dataset.columns_metadata:
                    if col.get('is_device_id'):
                        device_columns.append({
                            "name": col['name'],
                            "confidence": "high"
                        })
                    if col.get('is_timestamp'):
                        time_columns.append(col['name'])

            return {
                "dataset_id": dataset_id,
                "device_columns": device_columns,
                "time_columns": time_columns,
                "business_meaning": dataset.business_meaning_analysis or "",
                "control_logic": dataset.control_relationships_analysis or "",
                "status": "completed" if dataset.business_meaning_analysis else "pending"
            }
        except Exception as e:
            logger.error(f"获取业务分析结果失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/datasets/{dataset_id}/quality-analysis-results")
    async def get_quality_analysis_results(dataset_id: str):
        """
        获取质量分析结果

        返回数据集的质量分析结果，包括质量评分、各维度评分、关键问题和建议等。
        """
        try:
            dataset_service = create_dataset_service()
            dataset = dataset_service.get_dataset(dataset_id)

            if not dataset:
                raise HTTPException(status_code=404, detail="数据集不存在")

            # 从 dataset 中获取质量分析报告
            if hasattr(dataset, 'quality_analysis_report') and dataset.quality_analysis_report:
                report = dataset.quality_analysis_report
                return {
                    "dataset_id": dataset_id,
                    "overall_score": report.get('overall_score', 0),
                    "quality_level": report.get('quality_level', 'unknown'),
                    "completeness": report.get('completeness', 0),
                    "accuracy": report.get('accuracy', 0),
                    "consistency": report.get('consistency', 0),
                    "timeliness": report.get('timeliness', 0),
                    "key_issues": report.get('key_issues', []),
                    "recommendations": report.get('recommendations', []),
                    "status": "completed"
                }

            return {
                "dataset_id": dataset_id,
                "status": "pending",
                "message": "质量分析尚未执行"
            }
        except Exception as e:
            logger.error(f"获取质量分析结果失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/datasets/{dataset_id}/enhanced-analysis-results")
    async def get_enhanced_analysis_results(dataset_id: str):
        """
        获取增强分析结果

        返回数据集的增强分析结果，包括工业领域识别、业务数据类型、重要列识别等。
        """
        try:
            dataset_service = create_dataset_service()
            dataset = dataset_service.get_dataset(dataset_id)

            if not dataset:
                raise HTTPException(status_code=404, detail="数据集不存在")

            # 格式化工业领域
            industrial_domain = None
            if hasattr(dataset, 'industrial_domain') and dataset.industrial_domain:
                if isinstance(dataset.industrial_domain, dict):
                    industrial_domain = dataset.industrial_domain.get('primary', '未知')
                else:
                    industrial_domain = dataset.industrial_domain

            # 格式化业务数据类型
            business_data_types = []
            if hasattr(dataset, 'business_data_types') and dataset.business_data_types:
                if isinstance(dataset.business_data_types, list):
                    business_data_types = dataset.business_data_types
                elif isinstance(dataset.business_data_types, dict):
                    business_data_types = [dataset.business_data_types.get('primary', '未知')]

            # 构建重要列描述
            important_columns = ""
            if hasattr(dataset, 'important_columns_analysis') and dataset.important_columns_analysis:
                analysis = dataset.important_columns_analysis
                key_measurements = analysis.get('key_measurement_variables', [])
                control_vars = analysis.get('control_variables', [])

                parts = []
                if key_measurements:
                    parts.append("### 关键观测量\n")
                    for km in key_measurements:
                        parts.append(f"- **{km.get('column_name', 'N/A')}**: {km.get('reasoning', 'N/A')}")

                if control_vars:
                    parts.append("\n### 控制变量\n")
                    for cv in control_vars:
                        parts.append(f"- **{cv.get('column_name', 'N/A')}**: {cv.get('reasoning', 'N/A')}")

                important_columns = "\n".join(parts)

            return {
                "dataset_id": dataset_id,
                "industrial_domain": industrial_domain,
                "business_data_types": business_data_types,
                "important_columns": important_columns,
                "status": "completed" if industrial_domain else "pending"
            }
        except Exception as e:
            logger.error(f"获取增强分析结果失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/datasets/{dataset_id}/analysis-results")
    async def get_all_analysis_results(dataset_id: str):
        """
        获取所有分析结果

        返回数据集的所有分析结果，包括基础信息、业务分析、质量分析、增强分析等。
        """
        try:
            dataset_service = create_dataset_service()
            dataset = dataset_service.get_dataset(dataset_id)

            if not dataset:
                raise HTTPException(status_code=404, detail="数据集不存在")

            # 基础信息
            basic_info = {
                "row_count": dataset.row_count if hasattr(dataset, 'row_count') else 0,
                "column_count": dataset.column_count if hasattr(dataset, 'column_count') else 0,
                "file_size": dataset.file_size,
                "upload_time": dataset.upload_time.isoformat() if dataset.upload_time else None,
            }

            # 业务分析结果
            business_analysis = None
            if dataset.business_meaning_analysis or dataset.control_relationships_analysis:
                device_columns = []
                time_columns = []
                if hasattr(dataset, 'columns_metadata') and dataset.columns_metadata:
                    for col in dataset.columns_metadata:
                        if col.get('is_device_id'):
                            device_columns.append({"name": col['name'], "confidence": "high"})
                        if col.get('is_timestamp'):
                            time_columns.append(col['name'])

                business_analysis = {
                    "device_columns": device_columns,
                    "time_columns": time_columns,
                    "business_meaning": dataset.business_meaning_analysis or "",
                    "control_logic": dataset.control_relationships_analysis or "",
                }

            # 质量分析结果
            quality_analysis = None
            if hasattr(dataset, 'quality_analysis_report') and dataset.quality_analysis_report:
                report = dataset.quality_analysis_report
                quality_analysis = {
                    "overall_score": report.get('overall_score', 0),
                    "quality_level": report.get('quality_level', 'unknown'),
                    "completeness": report.get('completeness', 0),
                    "accuracy": report.get('accuracy', 0),
                    "consistency": report.get('consistency', 0),
                    "timeliness": report.get('timeliness', 0),
                    "key_issues": report.get('key_issues', []),
                    "recommendations": report.get('recommendations', []),
                }

            # 增强分析结果
            enhanced_analysis = None
            if hasattr(dataset, 'industrial_domain') and dataset.industrial_domain:
                industrial_domain = dataset.industrial_domain.get('primary', '未知') if isinstance(dataset.industrial_domain, dict) else dataset.industrial_domain

                business_data_types = []
                if hasattr(dataset, 'business_data_types') and dataset.business_data_types:
                    if isinstance(dataset.business_data_types, list):
                        business_data_types = dataset.business_data_types
                    elif isinstance(dataset.business_data_types, dict):
                        business_data_types = [dataset.business_data_types.get('primary', '未知')]

                important_columns = ""
                if hasattr(dataset, 'important_columns_analysis') and dataset.important_columns_analysis:
                    analysis = dataset.important_columns_analysis
                    key_measurements = analysis.get('key_measurement_variables', [])
                    control_vars = analysis.get('control_variables', [])

                    parts = []
                    if key_measurements:
                        parts.append("### 关键观测量\n")
                        for km in key_measurements:
                            parts.append(f"- **{km.get('column_name', 'N/A')}**: {km.get('reasoning', 'N/A')}")

                    if control_vars:
                        parts.append("\n### 控制变量\n")
                        for cv in control_vars:
                            parts.append(f"- **{cv.get('column_name', 'N/A')}**: {cv.get('reasoning', 'N/A')}")

                    important_columns = "\n".join(parts)

                enhanced_analysis = {
                    "industrial_domain": industrial_domain,
                    "business_data_types": business_data_types,
                    "important_columns": important_columns,
                }

            return {
                "dataset_id": dataset_id,
                "basic_info": basic_info,
                "business_analysis": business_analysis,
                "quality_analysis": quality_analysis,
                "enhanced_analysis": enhanced_analysis,
            }
        except Exception as e:
            logger.error(f"获取所有分析结果失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ===== LangGraph 反向代理端点 =====

    @app.api_route("/api/langgraph/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def proxy_to_langgraph(path: str, request):
        """
        反向代理到 LangGraph 服务器

        将对 /api/langgraph/* 的请求代理到 LangGraph dev server (port 2024)
        """
        import httpx

        langgraph_url = "http://localhost:2024"
        url = f"{langgraph_url}/{path}"

        # 转发请求
        body = await request.body()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=request.method,
                    url=url,
                    headers=dict(request.headers),
                    content=body,
                    timeout=60.0
                )

                return StreamingResponse(
                    response.aiter_bytes(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            except httpx.RequestError as e:
                logger.error(f"LangGraph 代理错误: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"无法连接到 LangGraph 服务器: {e}"
                )

    logger.info("FastAPI Extension 应用创建完成")
    return app


# ===== 应用实例 =====

extension_app = create_extension_app()
