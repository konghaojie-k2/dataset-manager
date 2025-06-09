"""标签相关的数据结构定义"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Tag(BaseModel):
    """标签实体"""
    id: Optional[int] = Field(None, description="标签ID")
    name: str = Field(description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    color: Optional[str] = Field("#007bff", description="标签颜色")
    category: Optional[str] = Field(None, description="标签分类")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    usage_count: int = Field(0, description="使用次数")


class TagCreateRequest(BaseModel):
    """创建标签请求"""
    name: str = Field(description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    color: Optional[str] = Field("#007bff", description="标签颜色")
    category: Optional[str] = Field(None, description="标签分类")


class TagUpdateRequest(BaseModel):
    """更新标签请求"""
    name: Optional[str] = Field(None, description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    color: Optional[str] = Field(None, description="标签颜色")
    category: Optional[str] = Field(None, description="标签分类")


class TagListResponse(BaseModel):
    """标签列表响应"""
    tags: List[Tag] = Field(description="标签列表")
    total: int = Field(description="总数量")


class DatasetTagUpdateRequest(BaseModel):
    """数据集标签更新请求"""
    dataset_id: str = Field(description="数据集ID")
    tag_names: List[str] = Field(description="标签名称列表")


class TagCategory(BaseModel):
    """标签分类"""
    name: str = Field(description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    color: Optional[str] = Field("#6c757d", description="分类颜色")
    tag_count: int = Field(0, description="该分类下的标签数量") 