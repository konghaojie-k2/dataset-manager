#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Processing Agent 工具集

包含数据扫描、业务分析、质量分析、增强分析等工具
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from loguru import logger

# 延迟导入以避免循环依赖


# ===== 工具输入 Schema 定义 =====

class ScanDatasetInput(BaseModel):
    """数据集扫描输入"""
    dataset_id: str = Field(description="数据集ID")


class AnalyzeBusinessInput(BaseModel):
    """业务分析输入"""
    dataset_id: str = Field(description="数据集ID")


class AnalyzeQualityInput(BaseModel):
    """质量分析输入"""
    dataset_id: str = Field(description="数据集ID")


class AnalyzeEnhancedInput(BaseModel):
    """增强分析输入"""
    dataset_id: str = Field(description="数据集ID")


class EmitProgressInput(BaseModel):
    """进度事件输入"""
    dataset_id: str = Field(description="数据集ID")
    current_step: str = Field(description="当前步骤描述")
    progress: int = Field(description="进度百分比（0-100）")
    steps_completed: str = Field(description="已完成的步骤列表，用逗号分隔，例如：'扫描数据, 业务分析, 质量分析'")
    steps_remaining: Optional[str] = Field(default=None, description="待完成的步骤列表，用逗号分隔，例如：'生成报告'")
    intermediate_result: Optional[str] = Field(default=None, description="中间结果（JSON字符串）")


# ===== 工具实现 =====

@tool("scan_dataset", args_schema=ScanDatasetInput)
async def scan_dataset_tool(dataset_id: str) -> str:
    """
    扫描数据集特征

    快速扫描数据集，获取基础信息：
    - 列的数量和名称
    - 列的数据类型分布
    - 数据规模（行数）
    - 初步的数据质量情况

    这是分析的第一步，结果将用于决定后续执行哪些分析。

    Args:
        dataset_id: 数据集ID

    Returns:
        JSON 字符串格式的扫描结果
    """
    logger.info(f"[Agent Tool] 扫描数据集: {dataset_id}")

    try:
        # 延迟导入以避免循环依赖
        from ...core.dataset_service_factory import create_dataset_service
        from ...tools.data_analyzer import DataAnalyzer
        import json

        dataset_service = create_dataset_service()
        dataset = dataset_service.get_dataset(dataset_id)

        if not dataset:
            return json.dumps({
                "error": "数据集不存在",
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        # 使用 DataAnalyzer 加载数据
        file_path = dataset.file_path
        data_analyzer = DataAnalyzer()

        # 只加载前 100 行进行快速扫描
        from pathlib import Path
        data_analyzer.data = data_analyzer.load_data(
            Path(file_path),
            nrows=100  # 只加载前100行
        )

        # 获取基础信息
        basic_info = data_analyzer.get_basic_info()
        columns_info = data_analyzer.get_columns_info()

        # 分析列类型
        data_types = {
            "numeric": 0,
            "categorical": 0,
            "datetime": 0,
            "other": 0
        }

        column_names = []
        has_timestamp = False
        has_device_column = False

        for col_info in columns_info:
            column_names.append(col_info["name"])
            dtype = col_info.get("dtype", "object")

            if "int" in dtype or "float" in dtype:
                data_types["numeric"] += 1
            elif "datetime" in dtype or "time" in dtype.lower():
                data_types["datetime"] += 1
                has_timestamp = True
            else:
                data_types["categorical"] += 1

            # 检测设备列（包含设备、device、equipment等关键词）
            col_name_lower = col_info["name"].lower()
            if any(keyword in col_name_lower for keyword in ["设备", "device", "equipment", "机组", "unit"]):
                has_device_column = True

        # 检查是否有缺失值
        has_missing = False
        for col_info in columns_info:
            if col_info.get("null_count", 0) > 0:
                has_missing = True
                break

        result = {
            "dataset_id": dataset_id,
            "columns": column_names,
            "column_count": len(column_names),
            "row_count": basic_info.get("shape", [0, 0])[0],
            "data_types": data_types,
            "has_missing": has_missing,
            "has_timestamp": has_timestamp,
            "has_device_column": has_device_column
        }

        logger.info(f"[Agent Tool] 数据集扫描完成: {dataset_id} - {result['column_count']}列, {result['row_count']}行")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Agent Tool] 扫描数据集失败: {e}")
        import json
        return json.dumps({
            "error": str(e),
            "dataset_id": dataset_id
        }, ensure_ascii=False)


@tool("analyze_business", args_schema=AnalyzeBusinessInput)
async def analyze_business_tool(dataset_id: str) -> str:
    """
    启动业务分析

    执行工业数据分析，包括：
    - 设备列和时间列识别
    - 业务含义分析
    - 控制逻辑分析

    适用于包含设备或时间相关列的工业/运营数据。

    Args:
        dataset_id: 数据集ID

    Returns:
        JSON 字符串格式的分析结果
    """
    logger.info(f"[Agent Tool] 启动业务分析: {dataset_id}")

    try:
        from ...core.dataset_service_factory import create_dataset_service
        from ...core.business_analysis_service import BusinessAnalysisService
        from pathlib import Path
        import json

        dataset_service = create_dataset_service()

        # 获取数据集
        dataset = dataset_service.get_dataset(dataset_id)
        if not dataset:
            return json.dumps({
                "error": "数据集不存在",
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        # 如果已有业务分析结果，直接返回
        if dataset.device_time_identification and dataset.business_meaning_analysis:
            device_columns_str = ""
            time_columns_str = ""

            if hasattr(dataset, 'columns_metadata') and dataset.columns_metadata:
                device_names = [col['name'] for col in dataset.columns_metadata if col.get('is_device_id')]
                time_names = [col['name'] for col in dataset.columns_metadata if col.get('is_timestamp')]

                device_columns_str = ", ".join(device_names) if device_names else "无"
                time_columns_str = ", ".join(time_names) if time_names else "无"

            result = {
                "dataset_id": dataset_id,
                "status": "completed",
                "device_columns": device_columns_str,
                "time_columns": time_columns_str,
                "business_meaning": dataset.business_meaning_analysis or "",
                "control_logic": dataset.control_relationships_analysis or "",
            }
            return json.dumps(result, ensure_ascii=False)

        # 执行业务分析
        file_path = Path(dataset.file_path)
        if not file_path.exists():
            return json.dumps({
                "error": "数据文件不存在",
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        business_service = BusinessAnalysisService()
        analysis_result = await business_service.run_business_analysis(
            file_path=file_path,
            dataset_name=dataset.name,
            user_requirements=""
        )

        # 检查是否有错误
        if analysis_result.get("errors"):
            return json.dumps({
                "error": "; ".join(analysis_result["errors"]),
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        # 更新数据集元数据
        dataset.device_time_identification = analysis_result.get("device_time_identification", "")
        dataset.business_meaning_analysis = analysis_result.get("business_meaning_analysis", "")
        dataset.control_relationships_analysis = analysis_result.get("control_relationships_analysis", "")
        
        # 更新列元数据（从 data_info 中提取）
        data_info = analysis_result.get("data_info", {})
        if data_info and "columns" in data_info:
            from ...schemas.dataset import ColumnMetadata
            columns_metadata = []
            for col_name in data_info["columns"]:
                dtype = data_info.get("dtypes", {}).get(col_name, "unknown")
                null_count = data_info.get("null_counts", {}).get(col_name, 0)
                
                columns_metadata.append(ColumnMetadata(
                    name=col_name,
                    data_type=dtype,
                    business_meaning=f"列 {col_name}",
                    is_device_id="id" in col_name.lower() or "device" in col_name.lower(),
                    is_timestamp="time" in col_name.lower() or "date" in col_name.lower(),
                    null_count=null_count,
                    unique_count=0,
                    sample_values=[]
                ))
            dataset.columns = columns_metadata

        # 更新状态
        dataset.processing_status = "business_completed"
        dataset_service.repository.save(dataset)

        # 提取设备列和时间列
        device_columns_str = ""
        time_columns_str = ""
        if hasattr(dataset, 'columns_metadata') and dataset.columns_metadata:
            device_names = [col['name'] for col in dataset.columns_metadata if col.get('is_device_id')]
            time_names = [col['name'] for col in dataset.columns_metadata if col.get('is_timestamp')]
            device_columns_str = ", ".join(device_names) if device_names else "无"
            time_columns_str = ", ".join(time_names) if time_names else "无"

        logger.info(f"[Agent Tool] 业务分析完成: {dataset_id}")
        result_data = {
            "dataset_id": dataset_id,
            "status": "completed",
            "device_columns": device_columns_str,
            "time_columns": time_columns_str,
            "business_meaning": dataset.business_meaning_analysis or "",
            "control_logic": dataset.control_relationships_analysis or "",
        }
        return json.dumps(result_data, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Agent Tool] 业务分析失败: {e}", exc_info=True)
        import json
        return json.dumps({
            "error": str(e),
            "dataset_id": dataset_id
        }, ensure_ascii=False)


@tool("analyze_quality", args_schema=AnalyzeQualityInput)
async def analyze_quality_tool(dataset_id: str) -> str:
    """
    启动质量分析

    执行数据质量分析，包括：
    - 完整性检查（缺失值）
    - 准确性检查（异常值）
    - 一致性检查（格式一致性）
    - 时效性检查（时间合理性）

    适用于所有数据集，特别推荐给有质量问题的数据。

    Args:
        dataset_id: 数据集ID

    Returns:
        JSON 字符串格式的分析结果
    """
    logger.info(f"[Agent Tool] 启动质量分析: {dataset_id}")

    try:
        from ...core.dataset_service_factory import create_dataset_service
        import json

        dataset_service = create_dataset_service()

        # 先获取数据集，检查是否已有质量分析结果
        dataset = dataset_service.get_dataset(dataset_id)
        if not dataset:
            return json.dumps({
                "error": "数据集不存在",
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        # 如果已有质量分析结果，直接返回
        if hasattr(dataset, 'quality_analysis_report') and dataset.quality_analysis_report:
            report = dataset.quality_analysis_report
            return json.dumps({
                "dataset_id": dataset_id,
                "status": "completed",
                "overall_score": report.get('overall_score', 0),
                "quality_level": report.get('quality_level', 'unknown'),
                "completeness": report.get('completeness', 0),
                "accuracy": report.get('accuracy', 0),
                "consistency": report.get('consistency', 0),
                "timeliness": report.get('timeliness', 0),
                "key_issues": "\n".join(report.get('key_issues', [])),
                "recommendations": "\n".join(report.get('recommendations', [])),
            }, ensure_ascii=False)

        # 执行质量分析
        file_path = Path(dataset.file_path)
        if not file_path.exists():
            return json.dumps({
                "error": "数据文件不存在",
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        from ...core.business_analysis_service import BusinessAnalysisService
        business_service = BusinessAnalysisService()
        analysis_result = await business_service.run_quality_analysis(
            dataset_id=dataset_id,
            file_path=file_path,
            user_requirements="进行全面的数据质量分析，重点关注时间序列数据的连续性和参数数据的合理性"
        )

        # 检查是否有错误
        if analysis_result.get("errors"):
            return json.dumps({
                "error": "; ".join(analysis_result["errors"]),
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        # 更新数据集元数据
        report = analysis_result.get("report", {})
        dataset.quality_analysis_report = report
        dataset.processing_status = "quality_completed"
        dataset_service.repository.save(dataset)

        logger.info(f"[Agent Tool] 质量分析完成: {dataset_id}")
        return json.dumps({
            "dataset_id": dataset_id,
            "status": analysis_result.get("status", "completed"),
            "overall_score": report.get('overall_score', 0),
            "quality_level": report.get('quality_level', 'unknown'),
            "completeness": report.get('completeness', 0),
            "accuracy": report.get('accuracy', 0),
            "consistency": report.get('consistency', 0),
            "timeliness": report.get('timeliness', 0),
            "key_issues": "\n".join(report.get('key_issues', [])),
            "recommendations": "\n".join(report.get('recommendations', [])),
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Agent Tool] 质量分析失败: {e}")
        import json
        return json.dumps({
            "error": str(e),
            "dataset_id": dataset_id
        }, ensure_ascii=False)


@tool("analyze_enhanced", args_schema=AnalyzeEnhancedInput)
async def analyze_enhanced_tool(dataset_id: str) -> str:
    """
    启动增强分析（领域识别+重要列识别）

    使用 LLM 驱动的智能分析，识别：
    - 工业领域（半导体、化工、能源等）
    - 业务数据类型（设备运行、生产数据、日志等）
    - 重要列（关键观测量、控制变量）

    适用于需要深入了解数据领域和重要性的场景。

    Args:
        dataset_id: 数据集ID

    Returns:
        JSON 字符串格式的分析结果
    """
    logger.info(f"[Agent Tool] 启动增强分析: {dataset_id}")

    try:
        from ...core.dataset_service_factory import create_dataset_service
        import json

        dataset_service = create_dataset_service()

        # 先获取数据集，检查是否已有增强分析结果
        dataset = dataset_service.get_dataset(dataset_id)
        if not dataset:
            return json.dumps({
                "error": "数据集不存在",
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        # 如果已有增强分析结果，直接返回
        if hasattr(dataset, 'industrial_domain') and dataset.industrial_domain:
            # 格式化工业领域
            industrial_domain = dataset.industrial_domain.get('primary', '未知') if isinstance(dataset.industrial_domain, dict) else dataset.industrial_domain

            # 格式化业务数据类型 - 转为字符串
            business_data_types_str = ""
            if hasattr(dataset, 'business_data_types') and dataset.business_data_types:
                if isinstance(dataset.business_data_types, list):
                    business_data_types_str = ", ".join(dataset.business_data_types)
                elif isinstance(dataset.business_data_types, dict):
                    business_data_types_str = dataset.business_data_types.get('primary', '未知')

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

            return json.dumps({
                "dataset_id": dataset_id,
                "status": "completed",
                "industrial_domain": industrial_domain,
                "business_data_types": business_data_types_str,
                "important_columns": important_columns,
            }, ensure_ascii=False)

        # 执行增强分析
        file_path = Path(dataset.file_path)
        if not file_path.exists():
            return json.dumps({
                "error": "数据文件不存在",
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        from ...core.business_analysis_service import BusinessAnalysisService
        business_service = BusinessAnalysisService()
        analysis_result = await business_service.run_enhanced_analysis(
            file_path=file_path,
            dataset_name=dataset.name,
            user_requirements=""
        )

        # 检查是否有错误
        if analysis_result.get("errors"):
            return json.dumps({
                "error": "; ".join(analysis_result["errors"]),
                "dataset_id": dataset_id
            }, ensure_ascii=False)

        # 更新数据集元数据
        dataset.industrial_domain = analysis_result.get("industrial_domain")
        dataset.business_data_types = analysis_result.get("business_data_types")
        dataset.domain_specific_insights = analysis_result.get("domain_specific_insights")
        dataset.important_columns_analysis = analysis_result.get("important_columns_analysis")

        # 更新industry字段（向后兼容）
        if dataset.industrial_domain and isinstance(dataset.industrial_domain, dict):
            dataset.industry = dataset.industrial_domain.get("primary", dataset.industry)

        # 更新列元数据
        if analysis_result.get("important_columns_analysis"):
            important_cols = analysis_result["important_columns_analysis"]
            key_measurements = important_cols.get("key_measurement_variables", [])
            control_vars = important_cols.get("control_variables", [])
            
            # 更新列的重要性和类型标记
            if dataset.columns:
                for col in dataset.columns:
                    # 检查是否是关键观测量
                    if any(km.get("column_name") == col.name for km in key_measurements):
                        col.business_meaning = f"{col.business_meaning} [关键观测量]"
                    # 检查是否是控制变量
                    if any(cv.get("column_name") == col.name for cv in control_vars):
                        col.business_meaning = f"{col.business_meaning} [控制变量]"

        dataset.processing_status = "enhanced_completed"
        dataset_service.repository.save(dataset)

        # 获取更新后的数据集以获取完整结果
        dataset = dataset_service.get_dataset(dataset_id)

        if hasattr(dataset, 'industrial_domain') and dataset.industrial_domain:
            # 格式化工业领域
            industrial_domain = dataset.industrial_domain.get('primary', '未知') if isinstance(dataset.industrial_domain, dict) else dataset.industrial_domain

            # 格式化业务数据类型 - 转为字符串
            business_data_types_str = ""
            if hasattr(dataset, 'business_data_types') and dataset.business_data_types:
                if isinstance(dataset.business_data_types, list):
                    business_data_types_str = ", ".join(dataset.business_data_types)
                elif isinstance(dataset.business_data_types, dict):
                    business_data_types_str = dataset.business_data_types.get('primary', '未知')

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

            logger.info(f"[Agent Tool] 增强分析完成: {dataset_id}")
            return json.dumps({
                "dataset_id": dataset_id,
                "status": result.get("status"),
                "industrial_domain": industrial_domain,
                "business_data_types": business_data_types_str,
                "important_columns": important_columns,
            }, ensure_ascii=False)

        return json.dumps({
            "dataset_id": dataset_id,
            "status": result.get("status"),
            "message": "增强分析已完成"
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Agent Tool] 增强分析失败: {e}")
        import json
        return json.dumps({
            "error": str(e),
            "dataset_id": dataset_id
        }, ensure_ascii=False)


@tool("emit_progress", args_schema=EmitProgressInput)
async def emit_progress_tool(
    dataset_id: str,
    current_step: str,
    progress: int,
    steps_completed: str,
    steps_remaining: Optional[str] = None,
    intermediate_result: Optional[str] = None
) -> str:
    """
    发送分析进度事件到前端

    这个工具会将进度信息推送给前端，让用户实时感知分析进度。
    进度事件会通过 WebSocket 或 Server-Sent Events 发送给订阅的前端组件。

    Args:
        dataset_id: 数据集ID
        current_step: 当前步骤描述（如"正在执行业务分析..."）
        progress: 进度百分比（0-100）
        steps_completed: 已完成的步骤列表（逗号分隔的字符串）
        steps_remaining: 待完成的步骤列表（逗号分隔的字符串，可选）
        intermediate_result: 中间结果（JSON字符串，可选）

    Returns:
        JSON 字符串格式的进度事件确认
    """
    logger.info(f"[Agent Tool] 发送进度事件: {dataset_id} - {current_step} ({progress}%)")

    import json

    # TODO: 实现 WebSocket 或 SSE 推送
    # 这里暂时使用日志记录，后续会实现实际的进度推送
    progress_event = {
        "type": "analysis_progress",
        "dataset_id": dataset_id,
        "current_step": current_step,
        "progress": progress,
        "steps_completed": steps_completed,
        "steps_remaining": steps_remaining or "无",
        "intermediate_result": intermediate_result or "{}"
    }

    logger.info(f"[Progress Event] {progress_event}")

    return json.dumps({
        "status": "progress_sent",
        "dataset_id": dataset_id,
        "event_summary": f"步骤: {current_step}, 进度: {progress}%"
    }, ensure_ascii=False)


# ===== 工具列表 =====

DATA_PROCESSING_TOOLS = [
    scan_dataset_tool,
    analyze_business_tool,
    analyze_quality_tool,
    analyze_enhanced_tool,
    emit_progress_tool
]
