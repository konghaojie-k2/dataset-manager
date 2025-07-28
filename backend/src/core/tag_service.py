#!/usr/bin/env python3
"""
标签服务层

提供标签管理的业务逻辑
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger

from ..schemas.tag import Tag, TagCreateRequest, TagUpdateRequest, TagListResponse, TagCategory
from .tag_repository import TagRepository


class TagService:
    """标签服务"""
    
    def __init__(self, metadata_dir: Path):
        """初始化标签服务
        
        Args:
            metadata_dir: 元数据存储目录
        """
        self.metadata_dir = Path(metadata_dir)
        
        # 初始化标签仓储
        db_path = self.metadata_dir / "datasets.db"
        self.tag_repository = TagRepository(db_path)
        
        logger.info("标签服务初始化完成")
    
    def create_tag(self, request: TagCreateRequest) -> Tag:
        """创建标签
        
        Args:
            request: 创建标签请求
            
        Returns:
            Tag: 创建的标签
        """
        try:
            tag = Tag(
                name=request.name.strip(),
                description=request.description,
                color=request.color or "#007bff",
                category=request.category
            )
            
            created_tag = self.tag_repository.create_tag(tag)
            logger.info(f"标签已创建: {created_tag.name}")
            
            return created_tag
            
        except Exception as e:
            logger.error(f"创建标签失败: {e}")
            raise
    
    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """获取标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Optional[Tag]: 标签对象
        """
        return self.tag_repository.get_tag_by_id(tag_id)
    
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """根据名称获取标签
        
        Args:
            name: 标签名称
            
        Returns:
            Optional[Tag]: 标签对象
        """
        return self.tag_repository.get_tag_by_name(name)
    
    def list_tags(self, category: Optional[str] = None, limit: Optional[int] = None) -> TagListResponse:
        """获取标签列表
        
        Args:
            category: 标签分类过滤
            limit: 限制数量
            
        Returns:
            TagListResponse: 标签列表响应
        """
        try:
            tags = self.tag_repository.list_tags(category=category, limit=limit)
            
            return TagListResponse(
                tags=tags,
                total=len(tags)
            )
            
        except Exception as e:
            logger.error(f"获取标签列表失败: {e}")
            return TagListResponse(tags=[], total=0)
    
    def update_tag(self, tag_id: int, request: TagUpdateRequest) -> Optional[Tag]:
        """更新标签
        
        Args:
            tag_id: 标签ID
            request: 更新标签请求
            
        Returns:
            Optional[Tag]: 更新后的标签
        """
        try:
            # 构建更新字段
            updates = {}
            if request.name is not None:
                updates['name'] = request.name.strip()
            if request.description is not None:
                updates['description'] = request.description
            if request.color is not None:
                updates['color'] = request.color
            if request.category is not None:
                updates['category'] = request.category
            
            if not updates:
                return self.tag_repository.get_tag_by_id(tag_id)
            
            updated_tag = self.tag_repository.update_tag(tag_id, updates)
            
            if updated_tag:
                logger.info(f"标签已更新: {updated_tag.name}")
            
            return updated_tag
            
        except Exception as e:
            logger.error(f"更新标签失败: {e}")
            raise
    
    def delete_tag(self, tag_id: int) -> bool:
        """删除标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 先获取标签信息用于日志
            tag = self.tag_repository.get_tag_by_id(tag_id)
            if not tag:
                return False
            
            success = self.tag_repository.delete_tag(tag_id)
            
            if success:
                logger.info(f"标签已删除: {tag.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除标签失败: {e}")
            return False
    
    def get_categories(self) -> List[TagCategory]:
        """获取标签分类列表
        
        Returns:
            List[TagCategory]: 分类列表
        """
        try:
            return self.tag_repository.get_categories()
            
        except Exception as e:
            logger.error(f"获取标签分类失败: {e}")
            return []
    
    def update_dataset_tags(self, dataset_id: str, tag_names: List[str]) -> List[str]:
        """更新数据集标签
        
        Args:
            dataset_id: 数据集ID
            tag_names: 标签名称列表
            
        Returns:
            List[str]: 更新后的标签列表
        """
        try:
            # 清理标签名称
            cleaned_tag_names = [name.strip() for name in tag_names if name.strip()]
            
            # 更新数据集标签
            self.tag_repository.update_dataset_tags(dataset_id, cleaned_tag_names)
            
            logger.info(f"数据集标签已更新: {dataset_id} -> {cleaned_tag_names}")
            
            return cleaned_tag_names
            
        except Exception as e:
            logger.error(f"更新数据集标签失败: {e}")
            raise
    
    def get_dataset_tags(self, dataset_id: str) -> List[str]:
        """获取数据集标签
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            List[str]: 标签名称列表
        """
        try:
            return self.tag_repository.get_dataset_tags(dataset_id)
            
        except Exception as e:
            logger.error(f"获取数据集标签失败: {e}")
            return []
    
    def search_tags(self, query: str, limit: int = 20) -> List[Tag]:
        """搜索标签
        
        Args:
            query: 搜索关键词
            limit: 限制数量
            
        Returns:
            List[Tag]: 匹配的标签列表
        """
        try:
            # 获取所有标签
            all_tags = self.tag_repository.list_tags()
            
            # 简单的名称匹配搜索
            query_lower = query.lower()
            matched_tags = []
            
            for tag in all_tags:
                if (query_lower in tag.name.lower() or 
                    (tag.description and query_lower in tag.description.lower()) or
                    (tag.category and query_lower in tag.category.lower())):
                    matched_tags.append(tag)
                    
                    if len(matched_tags) >= limit:
                        break
            
            # 按使用次数排序
            matched_tags.sort(key=lambda x: x.usage_count, reverse=True)
            
            return matched_tags
            
        except Exception as e:
            logger.error(f"搜索标签失败: {e}")
            return []
    
    def get_popular_tags(self, limit: int = 10) -> List[Tag]:
        """获取热门标签
        
        Args:
            limit: 限制数量
            
        Returns:
            List[Tag]: 热门标签列表
        """
        try:
            return self.tag_repository.list_tags(limit=limit)
            
        except Exception as e:
            logger.error(f"获取热门标签失败: {e}")
            return [] 