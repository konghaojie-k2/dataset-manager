"""服务器依赖注入"""

from typing import Optional
from fastapi import HTTPException, Depends
from loguru import logger

from ..core.dataset_service import DatasetService
from ..core.tag_service import TagService


# 全局服务实例
_dataset_service: Optional[DatasetService] = None
_tag_service: Optional[TagService] = None


def set_dataset_service(service: DatasetService):
    """设置数据集服务实例"""
    global _dataset_service
    _dataset_service = service
    logger.info("数据集服务实例已设置")


def set_tag_service(service: TagService):
    """设置标签服务实例"""
    global _tag_service
    _tag_service = service
    logger.info("标签服务实例已设置")


def get_dataset_service() -> DatasetService:
    """获取数据集服务实例
    
    Returns:
        DatasetService: 数据集服务实例
        
    Raises:
        HTTPException: 当服务未初始化时
    """
    if _dataset_service is None:
        logger.error("数据集服务未初始化")
        raise HTTPException(status_code=500, detail="数据集服务未初始化")
    return _dataset_service


def get_tag_service() -> TagService:
    """获取标签服务实例
    
    Returns:
        TagService: 标签服务实例
        
    Raises:
        HTTPException: 当服务未初始化时
    """
    if _tag_service is None:
        logger.error("标签服务未初始化")
        raise HTTPException(status_code=500, detail="标签服务未初始化")
    return _tag_service


def get_current_user():
    """获取当前用户（占位符，未来可扩展用户认证）
    
    Returns:
        dict: 用户信息
    """
    # 这里可以添加JWT token验证等逻辑
    return {"user_id": "anonymous", "username": "匿名用户"}


def check_api_key(api_key: str = None):
    """检查API密钥（占位符，未来可扩展API认证）
    
    Args:
        api_key: API密钥
        
    Returns:
        bool: 是否有效
    """
    # 这里可以添加API密钥验证逻辑
    return True 