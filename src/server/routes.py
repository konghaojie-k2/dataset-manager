"""FastAPI路由模块"""

from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from loguru import logger

from ..schemas.dataset import (
    DatasetMetadata,
    MetadataExtractionRequest,
    TagUpdateRequest
)
from ..core.dataset_service import DatasetService
from .dependencies import get_dataset_service


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
        datasets = service.list_datasets()
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