"""版本控制API路由

提供数据集和报告的版本管理API接口
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from loguru import logger

from src.server.dependencies import get_dataset_service
from src.schemas.dataset import DatasetMetadata
from src.utils.version_control import version_controller
from src.utils.report_version_manager import get_report_version_manager
from src.config.settings import get_settings

router = APIRouter(prefix="/api/v1/version-control", tags=["版本控制"])


@router.get("/datasets/{dataset_id}/versions")
async def get_dataset_version_history(dataset_id: str = Path(..., description="数据集ID")):
    """获取数据集版本历史
    
    Args:
        dataset_id: 数据集ID
        
    Returns:
        Dict: 版本历史信息
    """
    try:
        dataset_service = get_dataset_service()
        
        # 检查数据集是否存在
        dataset = dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail=f"数据集不存在: {dataset_id}")
        
        # 获取版本历史
        version_history = dataset_service.get_version_history(dataset_id)
        
        # 获取重复数据集
        duplicates = dataset_service.get_duplicate_datasets(dataset_id)
        
        return {
            "dataset_id": dataset_id,
            "version_history": version_history,
            "duplicates": duplicates,
            "total_versions": len(version_history),
            "total_duplicates": len(duplicates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集版本历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本历史失败: {str(e)}")


@router.get("/datasets/{dataset_id}/duplicates")
async def get_duplicate_datasets(dataset_id: str = Path(..., description="数据集ID")):
    """获取重复数据集
    
    Args:
        dataset_id: 数据集ID
        
    Returns:
        Dict: 重复数据集信息
    """
    try:
        dataset_service = get_dataset_service()
        duplicates = dataset_service.get_duplicate_datasets(dataset_id)
        
        return {
            "dataset_id": dataset_id,
            "duplicates": duplicates,
            "total_duplicates": len(duplicates)
        }
        
    except Exception as e:
        logger.error(f"获取重复数据集失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取重复数据集失败: {str(e)}")


@router.delete("/datasets/{dataset_id}/versions/cleanup")
async def cleanup_dataset_versions(
    dataset_id: str = Path(..., description="数据集ID"),
    keep_versions: int = Query(5, ge=1, le=20, description="保留版本数量")
):
    """清理数据集旧版本
    
    Args:
        dataset_id: 数据集ID
        keep_versions: 保留版本数量
        
    Returns:
        Dict: 清理结果
    """
    try:
        dataset_service = get_dataset_service()
        cleaned_count = dataset_service.cleanup_old_versions(dataset_id, keep_versions)
        
        return {
            "dataset_id": dataset_id,
            "cleaned_versions": cleaned_count,
            "keep_versions": keep_versions,
            "message": f"已清理 {cleaned_count} 个旧版本"
        }
        
    except Exception as e:
        logger.error(f"清理数据集版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理版本失败: {str(e)}")


@router.get("/reports/{dataset_id}/{analysis_type}/versions")
async def get_analysis_result_versions(
    dataset_id: str = Path(..., description="数据集ID"),
    analysis_type: str = Path(..., description="分析类型", regex="^(business|quality)$")
):
    """获取分析结果版本列表
    
    Args:
        dataset_id: 数据集ID
        analysis_type: 分析类型 (business 或 quality)
        
    Returns:
        Dict: 分析结果版本列表
    """
    try:
        settings = get_settings()
        report_manager = get_report_version_manager(
            settings.metadata_dir, 
            Path("reports")
        )
        
        versions = report_manager.get_analysis_result_versions(dataset_id, analysis_type)
        
        return {
            "dataset_id": dataset_id,
            "analysis_type": analysis_type,
            "versions": versions,
            "total_versions": len(versions)
        }
        
    except Exception as e:
        logger.error(f"获取分析结果版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析结果版本失败: {str(e)}")


@router.get("/reports/{dataset_id}/{analysis_type}/versions/{version}")
async def get_analysis_result_version(
    dataset_id: str = Path(..., description="数据集ID"),
    analysis_type: str = Path(..., description="分析类型", regex="^(business|quality)$"),
    version: str = Path(..., description="版本号")
):
    """获取指定版本的分析结果
    
    Args:
        dataset_id: 数据集ID
        analysis_type: 分析类型
        version: 版本号
        
    Returns:
        Dict: 分析结果数据
    """
    try:
        settings = get_settings()
        report_manager = get_report_version_manager(
            settings.metadata_dir, 
            Path("reports")
        )
        
        result_data = report_manager.load_analysis_result_version(
            dataset_id, analysis_type, version
        )
        
        if result_data is None:
            raise HTTPException(status_code=404, detail="指定版本的分析结果不存在")
        
        return {
            "dataset_id": dataset_id,
            "analysis_type": analysis_type,
            "version": version,
            "data": result_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析结果版本数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析结果失败: {str(e)}")


@router.get("/reports/{dataset_id}/{report_type}/report-versions")
async def get_report_file_versions(
    dataset_id: str = Path(..., description="数据集ID"),
    report_type: str = Path(..., description="报告类型", regex="^(industrial|quality)$")
):
    """获取报告文件版本列表
    
    Args:
        dataset_id: 数据集ID
        report_type: 报告类型 (industrial 或 quality)
        
    Returns:
        Dict: 报告文件版本列表
    """
    try:
        settings = get_settings()
        report_manager = get_report_version_manager(
            settings.metadata_dir, 
            Path("reports")
        )
        
        versions = report_manager.get_report_versions(dataset_id, report_type)
        
        return {
            "dataset_id": dataset_id,
            "report_type": report_type,
            "versions": versions,
            "total_versions": len(versions)
        }
        
    except Exception as e:
        logger.error(f"获取报告文件版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取报告文件版本失败: {str(e)}")


@router.delete("/reports/{dataset_id}/versions/cleanup")
async def cleanup_report_versions(
    dataset_id: str = Path(..., description="数据集ID"),
    keep_versions: int = Query(5, ge=1, le=20, description="保留版本数量")
):
    """清理报告旧版本
    
    Args:
        dataset_id: 数据集ID
        keep_versions: 保留版本数量
        
    Returns:
        Dict: 清理结果
    """
    try:
        settings = get_settings()
        report_manager = get_report_version_manager(
            settings.metadata_dir, 
            Path("reports")
        )
        
        cleaned_count = report_manager.cleanup_old_versions(dataset_id, keep_versions)
        
        return {
            "dataset_id": dataset_id,
            "cleaned_versions": cleaned_count,
            "keep_versions": keep_versions,
            "message": f"已清理 {cleaned_count} 个旧版本"
        }
        
    except Exception as e:
        logger.error(f"清理报告版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理报告版本失败: {str(e)}")


@router.get("/statistics")
async def get_version_statistics():
    """获取版本控制统计信息
    
    Returns:
        Dict: 统计信息
    """
    try:
        dataset_service = get_dataset_service()
        
        # 获取所有数据集
        all_datasets = dataset_service.list_datasets()
        
        # 统计版本信息
        version_stats = {
            "total_datasets": len(all_datasets),
            "version_types": {"original": 0, "updated": 0, "duplicate": 0},
            "datasets_with_versions": 0,
            "total_versions": 0
        }
        
        datasets_with_versions = set()
        
        for dataset in all_datasets:
            # 统计版本类型
            version_type = getattr(dataset, 'version_type', 'original')
            if version_type in version_stats["version_types"]:
                version_stats["version_types"][version_type] += 1
            
            # 获取版本历史
            version_history = dataset_service.get_version_history(dataset.id)
            if len(version_history) > 1:
                datasets_with_versions.add(dataset.id)
            
            version_stats["total_versions"] += len(version_history)
        
        version_stats["datasets_with_versions"] = len(datasets_with_versions)
        
        # 获取报告版本统计
        settings = get_settings()
        report_manager = get_report_version_manager(
            settings.metadata_dir, 
            Path("reports")
        )
        
        report_stats = {
            "business_analysis_versions": 0,
            "quality_analysis_versions": 0,
            "industrial_report_versions": 0,
            "quality_report_versions": 0
        }
        
        # 这里可以添加更详细的报告版本统计逻辑
        
        return {
            "dataset_versions": version_stats,
            "report_versions": report_stats,
            "generated_at": logger.info("版本统计信息获取完成")
        }
        
    except Exception as e:
        logger.error(f"获取版本统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}") 