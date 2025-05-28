#!/usr/bin/env python3
"""
报告管理API接口

提供分析报告的查看、下载、导出等功能
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from loguru import logger

from ....tools.report_manager import report_manager


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/", summary="获取报告列表")
async def list_reports(
    report_type: str = Query("industrial", description="报告类型 (industrial, general)"),
    limit: int = Query(50, description="返回数量限制"),
    offset: int = Query(0, description="偏移量")
) -> Dict[str, Any]:
    """获取报告列表
    
    Args:
        report_type: 报告类型
        limit: 返回数量限制
        offset: 偏移量
        
    Returns:
        Dict[str, Any]: 报告列表和统计信息
    """
    try:
        logger.info(f"获取报告列表: type={report_type}, limit={limit}, offset={offset}")
        
        # 获取所有报告
        all_reports = report_manager.list_reports(report_type)
        
        # 分页
        total = len(all_reports)
        reports = all_reports[offset:offset + limit]
        
        # 获取统计信息
        statistics = report_manager.get_report_statistics()
        
        return {
            "reports": reports,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            },
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error(f"获取报告列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取报告列表失败: {e}")


@router.get("/{dataset_id}", summary="获取指定数据集的报告详情")
async def get_dataset_reports(dataset_id: str) -> Dict[str, Any]:
    """获取指定数据集的报告详情
    
    Args:
        dataset_id: 数据集ID
        
    Returns:
        Dict[str, Any]: 报告详情
    """
    try:
        logger.info(f"获取数据集报告详情: {dataset_id}")
        
        # 获取所有工业报告
        all_reports = report_manager.list_reports("industrial")
        
        # 筛选指定数据集的报告
        dataset_reports = [
            report for report in all_reports 
            if report["dataset_id"] == dataset_id
        ]
        
        if not dataset_reports:
            raise HTTPException(status_code=404, detail=f"未找到数据集 {dataset_id} 的报告")
        
        # 获取最新的报告
        latest_report = dataset_reports[0]
        
        # 读取元数据文件获取详细信息
        metadata_file = Path(latest_report["metadata_file"])
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return {
                "dataset_id": dataset_id,
                "dataset_name": latest_report["dataset_name"],
                "analysis_timestamp": latest_report["analysis_timestamp"],
                "files": metadata.get("files", {}),
                "analysis_summary": metadata.get("analysis_summary", {}),
                "data_info": metadata.get("data_info", {}),
                "directory": latest_report["directory"]
            }
        else:
            return {
                "dataset_id": dataset_id,
                "dataset_name": latest_report["dataset_name"],
                "analysis_timestamp": latest_report["analysis_timestamp"],
                "files_count": latest_report["files_count"],
                "completed_steps": latest_report["completed_steps"],
                "directory": latest_report["directory"]
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集报告详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取报告详情失败: {e}")


@router.get("/{dataset_id}/files", summary="获取报告文件列表")
async def list_report_files(dataset_id: str) -> Dict[str, Any]:
    """获取指定数据集的报告文件列表
    
    Args:
        dataset_id: 数据集ID
        
    Returns:
        Dict[str, Any]: 文件列表
    """
    try:
        logger.info(f"获取报告文件列表: {dataset_id}")
        
        # 获取数据集报告详情
        report_detail = await get_dataset_reports(dataset_id)
        
        # 获取目录中的所有文件
        directory = Path(report_detail["directory"])
        if not directory.exists():
            raise HTTPException(status_code=404, detail="报告目录不存在")
        
        files = []
        for file_path in directory.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified_at": file_path.stat().st_mtime,
                    "extension": file_path.suffix,
                    "is_markdown": file_path.suffix.lower() == ".md",
                    "is_metadata": file_path.name.startswith("metadata_")
                })
        
        # 按文件名排序
        files.sort(key=lambda x: x["name"])
        
        return {
            "dataset_id": dataset_id,
            "directory": str(directory),
            "files": files,
            "total_files": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {e}")


@router.get("/{dataset_id}/download/{file_name}", summary="下载报告文件")
async def download_report_file(dataset_id: str, file_name: str) -> FileResponse:
    """下载指定的报告文件
    
    Args:
        dataset_id: 数据集ID
        file_name: 文件名
        
    Returns:
        FileResponse: 文件下载响应
    """
    try:
        logger.info(f"下载报告文件: {dataset_id}/{file_name}")
        
        # 获取报告详情
        report_detail = await get_dataset_reports(dataset_id)
        
        # 构建文件路径
        file_path = Path(report_detail["directory"]) / file_name
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_name}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"不是有效的文件: {file_name}")
        
        # 确定媒体类型
        media_type = "text/markdown" if file_path.suffix.lower() == ".md" else "application/octet-stream"
        
        return FileResponse(
            path=str(file_path),
            filename=file_name,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载报告文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载文件失败: {e}")


@router.get("/{dataset_id}/view/{file_name}", summary="在线查看报告文件内容")
async def view_report_file(dataset_id: str, file_name: str) -> Dict[str, Any]:
    """在线查看报告文件内容
    
    Args:
        dataset_id: 数据集ID
        file_name: 文件名
        
    Returns:
        Dict[str, Any]: 文件内容
    """
    try:
        logger.info(f"查看报告文件: {dataset_id}/{file_name}")
        
        # 获取报告详情
        report_detail = await get_dataset_reports(dataset_id)
        
        # 构建文件路径
        file_path = Path(report_detail["directory"]) / file_name
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_name}")
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
        
        # 获取文件信息
        file_stat = file_path.stat()
        
        return {
            "dataset_id": dataset_id,
            "file_name": file_name,
            "content": content,
            "file_info": {
                "size": file_stat.st_size,
                "modified_at": file_stat.st_mtime,
                "extension": file_path.suffix,
                "is_markdown": file_path.suffix.lower() == ".md"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查看报告文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"查看文件失败: {e}")


@router.post("/{dataset_id}/export", summary="导出报告归档")
async def export_report_archive(
    dataset_id: str,
    export_format: str = Query("zip", description="导出格式 (zip, tar)")
) -> FileResponse:
    """导出报告归档文件
    
    Args:
        dataset_id: 数据集ID
        export_format: 导出格式
        
    Returns:
        FileResponse: 归档文件下载响应
    """
    try:
        logger.info(f"导出报告归档: {dataset_id}, format={export_format}")
        
        # 创建归档文件
        archive_path = report_manager.export_report_archive(dataset_id, export_format)
        
        if not archive_path:
            raise HTTPException(status_code=404, detail=f"未找到数据集 {dataset_id} 的报告")
        
        # 确定媒体类型
        media_type = "application/zip" if export_format == "zip" else "application/gzip"
        
        return FileResponse(
            path=str(archive_path),
            filename=archive_path.name,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出报告归档失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出归档失败: {e}")


@router.get("/statistics/overview", summary="获取报告统计概览")
async def get_report_statistics() -> Dict[str, Any]:
    """获取报告统计概览
    
    Returns:
        Dict[str, Any]: 统计信息
    """
    try:
        logger.info("获取报告统计概览")
        
        statistics = report_manager.get_report_statistics()
        
        return {
            "statistics": statistics,
            "timestamp": statistics.get("last_updated")
        }
        
    except Exception as e:
        logger.error(f"获取报告统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {e}")


@router.delete("/cleanup", summary="清理旧报告")
async def cleanup_old_reports(
    days: int = Query(30, description="保留天数")
) -> Dict[str, Any]:
    """清理旧报告
    
    Args:
        days: 保留天数
        
    Returns:
        Dict[str, Any]: 清理结果
    """
    try:
        logger.info(f"清理旧报告: 保留 {days} 天")
        
        cleaned_count = report_manager.cleanup_old_reports(days)
        
        return {
            "message": f"清理完成，共清理 {cleaned_count} 个旧报告",
            "cleaned_count": cleaned_count,
            "retention_days": days
        }
        
    except Exception as e:
        logger.error(f"清理旧报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {e}") 