"""数据集相关的数据结构定义"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path


class ColumnMetadata(BaseModel):
    """列元数据"""
    name: str = Field(description="列名")
    data_type: str = Field(description="数据类型")
    business_meaning: str = Field(description="业务含义")
    is_device_id: bool = Field(default=False, description="是否为设备ID列")
    is_timestamp: bool = Field(default=False, description="是否为时间列")
    null_count: int = Field(description="空值数量")
    unique_count: int = Field(description="唯一值数量")
    sample_values: List[str] = Field(description="样本值")


class DataQualityMetrics(BaseModel):
    """数据质量指标"""
    total_rows: int = Field(description="总行数")
    total_columns: int = Field(description="总列数")
    missing_value_ratio: float = Field(description="缺失值比例")
    duplicate_rows: int = Field(description="重复行数")
    data_completeness: float = Field(description="数据完整性")
    quality_score: float = Field(description="质量评分")
    quality_issues: List[str] = Field(description="质量问题列表")
    recommendations: List[str] = Field(description="改进建议")


class DatasetMetadata(BaseModel):
    """数据集元数据"""
    id: str = Field(description="数据集ID")
    name: str = Field(description="数据集名称")
    description: str = Field(description="数据集描述")
    file_path: str = Field(description="文件路径")
    file_size: int = Field(description="文件大小(字节)")
    upload_time: datetime = Field(description="上传时间")
    
    # 数据基本信息
    time_range_start: Optional[datetime] = Field(None, description="时间范围开始")
    time_range_end: Optional[datetime] = Field(None, description="时间范围结束")
    sampling_rate: Optional[str] = Field(None, description="采样率")
    
    # 列信息
    columns: List[ColumnMetadata] = Field(description="列元数据")
    
    # 标签
    tags: List[str] = Field(default_factory=list, description="标签列表")
    industry: Optional[str] = Field(None, description="行业")
    analysis_domains: List[str] = Field(default_factory=list, description="分析领域")
    applicable_algorithms: List[str] = Field(default_factory=list, description="适用算法")
    
    # 数据质量
    quality_metrics: Optional[DataQualityMetrics] = Field(None, description="数据质量指标")
    
    # 工业数据分析结果
    device_time_identification: Optional[str] = Field(None, description="设备列和时间列识别结果")
    business_meaning_analysis: Optional[str] = Field(None, description="业务含义分析结果")
    control_relationships_analysis: Optional[str] = Field(None, description="控制原理分析结果")
    basic_analysis: Optional[str] = Field(None, description="基础分析结果")
    detailed_analysis: Optional[str] = Field(None, description="详细分析结果")
    insights: List[str] = Field(default_factory=list, description="数据洞察")
    recommendations: Optional[str] = Field(None, description="分析建议")
    
    # 数据质量分析结果
    quality_analysis_results: Optional[Dict[str, Any]] = Field(None, description="数据质量分析结果")
    
    # 状态
    processing_status: str = Field(default="uploaded", description="处理状态")
    metadata_extracted: bool = Field(default=False, description="元数据是否已提取")


class UploadRequest(BaseModel):
    """上传请求"""
    file_name: str = Field(description="文件名")
    file_size: int = Field(description="文件大小")


class MetadataExtractionRequest(BaseModel):
    """元数据提取请求"""
    dataset_id: str = Field(description="数据集ID")
    user_input: Optional[str] = Field(None, description="用户输入的额外信息")


class TagUpdateRequest(BaseModel):
    """标签更新请求"""
    dataset_id: str = Field(description="数据集ID")
    tags: List[str] = Field(description="标签列表")
    industry: Optional[str] = Field(None, description="行业")
    analysis_domains: List[str] = Field(default_factory=list, description="分析领域")
    applicable_algorithms: List[str] = Field(default_factory=list, description="适用算法") 