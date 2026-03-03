"""FastAPI路由模块"""

from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from loguru import logger

from src.schemas.dataset import (
    DatasetMetadata,
    MetadataExtractionRequest,
    TagUpdateRequest
)
from src.core.dataset_service import DatasetService
from .dependencies import get_dataset_service
from pydantic import BaseModel


# 创建路由器
router = APIRouter(prefix="/api/v1", tags=["datasets"])

# 全局服务实例（在应用启动时初始化）
dataset_service: Optional[DatasetService] = None


@router.post("/datasets/upload", response_model=dict)
async def upload_dataset(
    file: UploadFile = File(...),
    user_input: Optional[str] = Form(None),
    service: DatasetService = Depends(get_dataset_service)
):
    """上传数据集
    
    Args:
        file: 上传的文件（CSV或ZIP）
        user_input: 用户输入的额外信息
        service: 数据集服务
        
    Returns:
        dict: 上传结果
    """
    try:
        logger.info(f"开始上传数据集: {file.filename}")
        
        dataset_id = await service.upload_dataset(file, user_input)
        
        return {
            "success": True,
            "message": "数据集上传成功",
            "dataset_id": dataset_id
        }
        
    except Exception as e:
        logger.error(f"数据集上传失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/datasets", response_model=List[DatasetMetadata])
async def list_datasets(
    service: DatasetService = Depends(get_dataset_service)
):
    """获取数据集列表
    
    Args:
        service: 数据集服务
        
    Returns:
        List[DatasetMetadata]: 数据集列表
    """
    try:
        datasets = await service.list_datasets()
        return datasets
        
    except Exception as e:
        logger.error(f"获取数据集列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}", response_model=DatasetMetadata)
async def get_dataset(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service)
):
    """获取数据集详情
    
    Args:
        dataset_id: 数据集ID
        service: 数据集服务
        
    Returns:
        DatasetMetadata: 数据集元数据
    """
    try:
        dataset = service.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/preview")
async def get_dataset_preview(
    dataset_id: str,
    rows: int = 10,
    service: DatasetService = Depends(get_dataset_service)
):
    """获取数据集预览

    Args:
        dataset_id: 数据集ID
        rows: 预览行数
        service: 数据集服务

    Returns:
        dict: 数据预览
    """
    try:
        preview = service.get_dataset_preview(dataset_id, rows)
        if not preview:
            raise HTTPException(status_code=404, detail="数据集不存在或无法预览")

        return preview

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据预览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/download")
async def download_dataset(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service)
):
    """下载数据集文件

    Args:
        dataset_id: 数据集ID
        service: 数据集服务

    Returns:
        FileResponse: 文件下载响应
    """
    try:
        logger.info(f"开始下载数据集: {dataset_id}")

        # 获取数据集信息
        dataset = service.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")

        # 获取文件路径
        file_path = service.get_dataset_file_path(dataset_id)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="数据集文件不存在")

        # 确定文件名
        filename = dataset.name
        if not filename.endswith(file_path.suffix):
            filename += file_path.suffix

        # 确定媒体类型
        media_type = "application/octet-stream"
        if file_path.suffix.lower() == ".csv":
            media_type = "text/csv"
        elif file_path.suffix.lower() == ".zip":
            media_type = "application/zip"

        logger.info(f"下载数据集文件: {filename}")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载数据集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasets/{dataset_id}/extract-metadata")
async def extract_metadata(
    dataset_id: str,
    request: MetadataExtractionRequest,
    service: DatasetService = Depends(get_dataset_service)
):
    """提取数据集元数据
    
    Args:
        dataset_id: 数据集ID
        request: 元数据提取请求
        service: 数据集服务
        
    Returns:
        dict: 提取结果
    """
    try:
        if request.dataset_id != dataset_id:
            raise HTTPException(status_code=400, detail="数据集ID不匹配")
        
        result = await service.extract_metadata(dataset_id, request.user_input)
        
        return {
            "success": True,
            "message": "元数据提取完成",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"元数据提取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/datasets/{dataset_id}/tags", response_model=DatasetMetadata)
async def update_dataset_tags(
    dataset_id: str,
    request: TagUpdateRequest,
    service: DatasetService = Depends(get_dataset_service)
):
    """更新数据集标签
    
    Args:
        dataset_id: 数据集ID
        request: 标签更新请求
        service: 数据集服务
        
    Returns:
        DatasetMetadata: 更新后的数据集元数据
    """
    try:
        if request.dataset_id != dataset_id:
            raise HTTPException(status_code=400, detail="数据集ID不匹配")
        
        updated_dataset = service.update_tags(request)
        return updated_dataset
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/industrial-analysis")
async def get_industrial_analysis(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service)
):
    """获取工业数据分析结果
    
    Args:
        dataset_id: 数据集ID
        service: 数据集服务
        
    Returns:
        dict: 工业数据分析结果
    """
    try:
        dataset = service.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        # 构建工业分析结果
        industrial_analysis = {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "processing_status": dataset.processing_status,
            "device_time_identification": dataset.device_time_identification,
            "business_meaning_analysis": dataset.business_meaning_analysis,
            "control_relationships_analysis": dataset.control_relationships_analysis,
            "basic_analysis": dataset.basic_analysis,
            "detailed_analysis": dataset.detailed_analysis,
            "insights": dataset.insights,
            "recommendations": dataset.recommendations,
            "analysis_completed": all([
                dataset.device_time_identification,
                dataset.business_meaning_analysis,
                dataset.control_relationships_analysis
            ])
        }
        
        return industrial_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工业数据分析结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service)
):
    """删除数据集
    
    Args:
        dataset_id: 数据集ID
        service: 数据集服务
        
    Returns:
        dict: 删除结果
    """
    try:
        success = service.delete_dataset(dataset_id)
        if not success:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        return {
            "success": True,
            "message": "数据集删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除数据集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查
    
    Returns:
        dict: 健康状态
    """
    return {
        "status": "healthy",
        "service": "dataset-manager"
    }


@router.post("/datasets/{dataset_id}/start-business-analysis")
async def start_business_analysis(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service)
):
    """启动业务分析
    
    Args:
        dataset_id: 数据集ID
        service: 数据集服务
        
    Returns:
        dict: 启动结果
    """
    try:
        result = await service.start_business_analysis(dataset_id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动业务分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasets/{dataset_id}/start-quality-analysis")
async def start_quality_analysis(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service)
):
    """启动质量分析
    
    Args:
        dataset_id: 数据集ID
        service: 数据集服务
        
    Returns:
        dict: 启动结果
    """
    try:
        result = await service.start_quality_analysis(dataset_id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动质量分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasets/{dataset_id}/start-enhanced-analysis")
async def start_enhanced_analysis(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service)
):
    """启动增强分析（领域识别+重要列识别）

    使用LLM驱动的智能分析，识别:
    1. 工业领域（半导体、化工、能源等）
    2. 业务数据类型（设备运行、生产数据、日志等）
    3. 重要列（关键观测量、控制量）

    Args:
        dataset_id: 数据集ID
        service: 数据集服务

    Returns:
        dict: 分析结果
    """
    try:
        result = await service.start_enhanced_analysis(dataset_id)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动增强分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/business-analysis-results")
async def get_business_analysis_results(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service)
):
    """获取业务分析结果
    
    Args:
        dataset_id: 数据集ID
        service: 数据集服务
        
    Returns:
        dict: 业务分析结果
    """
    try:
        results = await service.get_business_analysis_results(dataset_id)
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取业务分析结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/quality-analysis-results")
async def get_quality_analysis_results(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service)
):
    """获取质量分析结果
    
    Args:
        dataset_id: 数据集ID
        service: 数据集服务
        
    Returns:
        dict: 质量分析结果
    """
    try:
        results = await service.get_quality_analysis_results(dataset_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取质量分析结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 请求模型定义 =====

class CompressionMethodRequest(BaseModel):
    """压缩方法请求"""
    method: str = "gzip"  # gzip, bzip2, xz


# ===== Parquet 转换端点 =====

@router.post("/datasets/{dataset_id}/convert-parquet")
async def convert_to_parquet(
    dataset_id: str,
    compression: str = "snappy",
    service: DatasetService = Depends(get_dataset_service)
):
    """转换为 Parquet 格式
    
    Args:
        dataset_id: 数据集ID
        compression: 压缩算法 (snappy/gzip/brotli/lz4)
        service: 数据集服务
        
    Returns:
        转换结果
    """
    try:
        from ..core.parquet_converter import ParquetConverter
        
        # 获取数据集
        dataset = service.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        # 转换
        converter = ParquetConverter()
        parquet_path = converter.convert_to_parquet(
            Path(dataset.file_path),
            compression=compression
        )
        
        # 更新元数据
        dataset.parquet_path = str(parquet_path)
        service.repository.save(dataset)
        
        # 计算压缩率
        original_size = Path(dataset.file_path).stat().st_size
        compressed_size = parquet_path.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        logger.info(f"Parquet 转换成功: {dataset_id}")
        
        return {
            "success": True,
            "message": "Parquet 转换成功",
            "dataset_id": dataset_id,
            "parquet_path": str(parquet_path),
            "original_size_mb": round(original_size / 1024 / 1024, 2),
            "compressed_size_mb": round(compressed_size / 1024 / 1024, 2),
            "compression_ratio": round(compression_ratio, 2)
        }
        
    except ValueError as e:
        logger.error(f"Parquet 转换失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Parquet 转换失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 文件压缩端点 =====

@router.post("/datasets/{dataset_id}/compress")
async def compress_dataset(
    dataset_id: str,
    request: CompressionMethodRequest,
    service: DatasetService = Depends(get_dataset_service)
):
    """压缩数据集文件
    
    Args:
        dataset_id: 数据集ID
        request: 压缩方法请求
        service: 数据集服务
        
    Returns:
        压缩结果
    """
    try:
        from ..core.file_compressor import FileCompressor
        
        # 获取数据集
        dataset = service.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        # 压缩
        compressor = FileCompressor()
        compressed_path = compressor.compress_file(
            Path(dataset.file_path),
            method=request.method
        )
        
        # 更新元数据
        dataset.compressed_path = str(compressed_path)
        service.repository.save(dataset)
        
        # 计算压缩率
        original_size = Path(dataset.file_path).stat().st_size
        compressed_size = compressed_path.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        logger.info(f"文件压缩成功: {dataset_id}")
        
        return {
            "success": True,
            "message": "文件压缩成功",
            "dataset_id": dataset_id,
            "compressed_path": str(compressed_path),
            "compression_method": request.method,
            "original_size_mb": round(original_size / 1024 / 1024, 2),
            "compressed_size_mb": round(compressed_size / 1024 / 1024, 2),
            "compression_ratio": round(compression_ratio, 2)
        }
        
    except ValueError as e:
        logger.error(f"文件压缩失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文件压缩失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))