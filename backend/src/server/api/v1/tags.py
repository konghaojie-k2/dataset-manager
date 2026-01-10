"""标签管理API路由"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from loguru import logger

from src.schemas.tag import (
    Tag,
    TagCreateRequest,
    TagUpdateRequest as TagUpdateRequestModel,
    TagListResponse,
    DatasetTagUpdateRequest,
    TagCategory
)
from src.core.tag_service import TagService
from src.server.dependencies import get_tag_service


# 创建路由器
router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


@router.post("/", response_model=Tag)
async def create_tag(
    request: TagCreateRequest,
    service: TagService = Depends(get_tag_service)
):
    """创建标签
    
    Args:
        request: 创建标签请求
        service: 标签服务
        
    Returns:
        Tag: 创建的标签
    """
    try:
        logger.info(f"创建标签: {request.name}")
        
        tag = service.create_tag(request)
        
        return tag
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=TagListResponse)
async def list_tags(
    category: Optional[str] = Query(None, description="标签分类过滤"),
    limit: Optional[int] = Query(None, description="限制数量"),
    service: TagService = Depends(get_tag_service)
):
    """获取标签列表
    
    Args:
        category: 标签分类过滤
        limit: 限制数量
        service: 标签服务
        
    Returns:
        TagListResponse: 标签列表响应
    """
    try:
        response = service.list_tags(category=category, limit=limit)
        return response
        
    except Exception as e:
        logger.error(f"获取标签列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_tags(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, description="限制数量"),
    service: TagService = Depends(get_tag_service)
):
    """搜索标签
    
    Args:
        q: 搜索关键词
        limit: 限制数量
        service: 标签服务
        
    Returns:
        List[Tag]: 匹配的标签列表
    """
    try:
        tags = service.search_tags(q, limit)
        return {"tags": tags, "total": len(tags)}
        
    except Exception as e:
        logger.error(f"搜索标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular")
async def get_popular_tags(
    limit: int = Query(10, description="限制数量"),
    service: TagService = Depends(get_tag_service)
):
    """获取热门标签
    
    Args:
        limit: 限制数量
        service: 标签服务
        
    Returns:
        List[Tag]: 热门标签列表
    """
    try:
        tags = service.get_popular_tags(limit)
        return {"tags": tags, "total": len(tags)}
        
    except Exception as e:
        logger.error(f"获取热门标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=List[TagCategory])
async def get_categories(
    service: TagService = Depends(get_tag_service)
):
    """获取标签分类列表
    
    Args:
        service: 标签服务
        
    Returns:
        List[TagCategory]: 分类列表
    """
    try:
        categories = service.get_categories()
        return categories
        
    except Exception as e:
        logger.error(f"获取标签分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tag_id}", response_model=Tag)
async def get_tag(
    tag_id: int,
    service: TagService = Depends(get_tag_service)
):
    """获取标签详情
    
    Args:
        tag_id: 标签ID
        service: 标签服务
        
    Returns:
        Tag: 标签对象
    """
    try:
        tag = service.get_tag(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")
        
        return tag
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{tag_id}", response_model=Tag)
async def update_tag(
    tag_id: int,
    request: TagUpdateRequestModel,
    service: TagService = Depends(get_tag_service)
):
    """更新标签
    
    Args:
        tag_id: 标签ID
        request: 更新标签请求
        service: 标签服务
        
    Returns:
        Tag: 更新后的标签
    """
    try:
        tag = service.update_tag(tag_id, request)
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")
        
        return tag
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int,
    service: TagService = Depends(get_tag_service)
):
    """删除标签
    
    Args:
        tag_id: 标签ID
        service: 标签服务
        
    Returns:
        dict: 删除结果
    """
    try:
        success = service.delete_tag(tag_id)
        if not success:
            raise HTTPException(status_code=404, detail="标签不存在")
        
        return {
            "success": True,
            "message": "标签删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/datasets/{dataset_id}")
async def update_dataset_tags(
    dataset_id: str,
    request: DatasetTagUpdateRequest,
    service: TagService = Depends(get_tag_service)
):
    """更新数据集标签
    
    Args:
        dataset_id: 数据集ID
        request: 数据集标签更新请求
        service: 标签服务
        
    Returns:
        dict: 更新结果
    """
    try:
        if request.dataset_id != dataset_id:
            raise HTTPException(status_code=400, detail="数据集ID不匹配")
        
        updated_tags = service.update_dataset_tags(dataset_id, request.tag_names)
        
        return {
            "success": True,
            "message": "数据集标签更新成功",
            "tags": updated_tags
        }
        
    except Exception as e:
        logger.error(f"更新数据集标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}")
async def get_dataset_tags(
    dataset_id: str,
    service: TagService = Depends(get_tag_service)
):
    """获取数据集标签
    
    Args:
        dataset_id: 数据集ID
        service: 标签服务
        
    Returns:
        dict: 数据集标签
    """
    try:
        tags = service.get_dataset_tags(dataset_id)
        
        return {
            "dataset_id": dataset_id,
            "tags": tags
        }
        
    except Exception as e:
        logger.error(f"获取数据集标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 