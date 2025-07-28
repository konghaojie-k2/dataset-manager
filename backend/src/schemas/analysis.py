"""分析相关的数据结构定义"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AnalysisType(str, Enum):
    """分析类型枚举"""
    BASIC = "basic"
    STATISTICAL = "statistical"
    CORRELATION = "correlation"
    ANOMALY = "anomaly"
    TREND = "trend"
    CLUSTERING = "clustering"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class AnalysisStatus(str, Enum):
    """分析状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisRequest(BaseModel):
    """分析请求模型"""
    dataset_id: str = Field(description="数据集ID")
    analysis_type: AnalysisType = Field(description="分析类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="分析参数")
    columns: Optional[List[str]] = Field(None, description="指定分析的列")
    user_requirements: Optional[str] = Field(None, description="用户需求描述")


class AnalysisResult(BaseModel):
    """分析结果模型"""
    id: str = Field(description="分析结果ID")
    dataset_id: str = Field(description="数据集ID")
    analysis_type: AnalysisType = Field(description="分析类型")
    status: AnalysisStatus = Field(description="分析状态")
    
    # 时间信息
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 结果数据
    results: Dict[str, Any] = Field(default_factory=dict, description="分析结果")
    summary: Optional[str] = Field(None, description="结果摘要")
    insights: List[str] = Field(default_factory=list, description="洞察列表")
    recommendations: List[str] = Field(default_factory=list, description="建议列表")
    
    # 可视化
    charts: List[Dict[str, Any]] = Field(default_factory=list, description="图表列表")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")


class StatisticalSummary(BaseModel):
    """统计摘要模型"""
    column_name: str = Field(description="列名")
    data_type: str = Field(description="数据类型")
    count: int = Field(description="总数")
    null_count: int = Field(description="空值数")
    unique_count: int = Field(description="唯一值数")
    
    # 数值型统计
    mean: Optional[float] = Field(None, description="均值")
    median: Optional[float] = Field(None, description="中位数")
    std: Optional[float] = Field(None, description="标准差")
    min_value: Optional[Union[float, str]] = Field(None, description="最小值")
    max_value: Optional[Union[float, str]] = Field(None, description="最大值")
    
    # 分位数
    q25: Optional[float] = Field(None, description="25%分位数")
    q75: Optional[float] = Field(None, description="75%分位数")
    
    # 分类型统计
    mode: Optional[str] = Field(None, description="众数")
    top_values: List[Dict[str, Any]] = Field(default_factory=list, description="高频值")


class CorrelationMatrix(BaseModel):
    """相关性矩阵模型"""
    columns: List[str] = Field(description="列名列表")
    matrix: List[List[float]] = Field(description="相关性矩阵")
    method: str = Field(default="pearson", description="相关性计算方法")


class AnomalyDetectionResult(BaseModel):
    """异常检测结果模型"""
    column_name: str = Field(description="列名")
    method: str = Field(description="检测方法")
    anomaly_count: int = Field(description="异常值数量")
    anomaly_ratio: float = Field(description="异常值比例")
    anomaly_indices: List[int] = Field(description="异常值索引")
    threshold: Optional[float] = Field(None, description="阈值")


class TrendAnalysisResult(BaseModel):
    """趋势分析结果模型"""
    time_column: str = Field(description="时间列")
    value_column: str = Field(description="值列")
    trend_direction: str = Field(description="趋势方向: up/down/stable")
    trend_strength: float = Field(description="趋势强度")
    seasonal_pattern: Optional[str] = Field(None, description="季节性模式")
    change_points: List[Dict[str, Any]] = Field(default_factory=list, description="变化点")


class ModelTrainingRequest(BaseModel):
    """模型训练请求"""
    dataset_id: str = Field(description="数据集ID")
    model_type: str = Field(description="模型类型")
    target_column: str = Field(description="目标列")
    feature_columns: List[str] = Field(description="特征列")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模型参数")
    validation_split: float = Field(default=0.2, description="验证集比例")


class ModelTrainingResult(BaseModel):
    """模型训练结果"""
    id: str = Field(description="模型ID")
    dataset_id: str = Field(description="数据集ID")
    model_type: str = Field(description="模型类型")
    status: AnalysisStatus = Field(description="训练状态")
    
    # 性能指标
    metrics: Dict[str, float] = Field(default_factory=dict, description="性能指标")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="特征重要性")
    
    # 模型信息
    model_path: Optional[str] = Field(None, description="模型文件路径")
    created_at: datetime = Field(description="创建时间")
    training_time: Optional[float] = Field(None, description="训练时间(秒)")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息") 