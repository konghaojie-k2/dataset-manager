"""数据质量评估相关的数据结构定义"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class QualityLevel(str, Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"  # 90-100分
    GOOD = "good"           # 70-89分
    FAIR = "fair"           # 50-69分
    POOR = "poor"           # 0-49分


class ColumnType(str, Enum):
    """列类型枚举"""
    TIME = "time"           # 时间列
    PARAMETER = "parameter" # 参数列
    CATEGORY = "category"   # 类目列


class TimeQualityIssue(BaseModel):
    """时间列质量问题"""
    issue_type: str = Field(description="问题类型")
    description: str = Field(description="问题描述")
    affected_rows: List[int] = Field(description="受影响的行索引")
    severity: str = Field(description="严重程度: high/medium/low")


class TimeColumnQuality(BaseModel):
    """时间列数据质量分析结果"""
    column_name: str = Field(description="列名")
    
    # 格式一致性
    format_consistency: Dict[str, Any] = Field(description="格式一致性分析")
    detected_formats: List[str] = Field(description="检测到的时间格式")
    format_consistency_score: float = Field(description="格式一致性得分 0-100")
    
    # 范围合理性
    time_range: Dict[str, Any] = Field(description="时间范围信息")
    range_validity_score: float = Field(description="范围合理性得分 0-100")
    
    # 连续性分析
    continuity_analysis: Dict[str, Any] = Field(description="连续性分析")
    continuity_score: float = Field(description="连续性得分 0-100")
    
    # 精度识别
    precision_info: Dict[str, Any] = Field(description="时间精度信息")
    precision_consistency_score: float = Field(description="精度一致性得分 0-100")
    
    # 异常值
    anomalies: List[TimeQualityIssue] = Field(description="异常时间值")
    anomaly_score: float = Field(description="异常值得分 0-100")
    
    # 综合评分
    overall_score: float = Field(description="综合质量得分 0-100")
    quality_level: QualityLevel = Field(description="质量等级")
    recommendations: List[str] = Field(description="改进建议")


class ParameterQualityIssue(BaseModel):
    """参数列质量问题"""
    issue_type: str = Field(description="问题类型")
    description: str = Field(description="问题描述")
    affected_rows: List[int] = Field(description="受影响的行索引")
    severity: str = Field(description="严重程度: high/medium/low")
    suggested_action: str = Field(description="建议操作")


class ParameterColumnQuality(BaseModel):
    """参数列数据质量分析结果"""
    column_name: str = Field(description="列名")
    
    # 数值范围合理性
    range_analysis: Dict[str, Any] = Field(description="数值范围分析")
    range_validity_score: float = Field(description="范围合理性得分 0-100")
    
    # 数据分布
    distribution_analysis: Dict[str, Any] = Field(description="数据分布分析")
    distribution_score: float = Field(description="分布合理性得分 0-100")
    
    # 异常值检测
    outlier_analysis: Dict[str, Any] = Field(description="异常值分析")
    outlier_score: float = Field(description="异常值得分 0-100")
    
    # 精度和单位一致性
    precision_analysis: Dict[str, Any] = Field(description="精度分析")
    unit_consistency: Dict[str, Any] = Field(description="单位一致性分析")
    precision_score: float = Field(description="精度一致性得分 0-100")
    
    # 缺失值模式
    missing_pattern: Dict[str, Any] = Field(description="缺失值模式分析")
    completeness_score: float = Field(description="完整性得分 0-100")
    
    # 质量问题
    issues: List[ParameterQualityIssue] = Field(description="发现的质量问题")
    
    # 综合评分
    overall_score: float = Field(description="综合质量得分 0-100")
    quality_level: QualityLevel = Field(description="质量等级")
    recommendations: List[str] = Field(description="改进建议")


class CategoryQualityIssue(BaseModel):
    """类目列质量问题"""
    issue_type: str = Field(description="问题类型")
    description: str = Field(description="问题描述")
    affected_values: List[str] = Field(description="受影响的值")
    severity: str = Field(description="严重程度: high/medium/low")
    suggested_mapping: Optional[Dict[str, str]] = Field(None, description="建议的映射关系")


class CategoryColumnQuality(BaseModel):
    """类目列数据质量分析结果"""
    column_name: str = Field(description="列名")
    
    # 类别一致性
    consistency_analysis: Dict[str, Any] = Field(description="类别一致性分析")
    consistency_score: float = Field(description="一致性得分 0-100")
    
    # 编码规范
    encoding_analysis: Dict[str, Any] = Field(description="编码规范分析")
    encoding_score: float = Field(description="编码规范得分 0-100")
    
    # 类别分布
    distribution_analysis: Dict[str, Any] = Field(description="类别分布分析")
    distribution_score: float = Field(description="分布合理性得分 0-100")
    
    # 异常类别
    anomaly_analysis: Dict[str, Any] = Field(description="异常类别分析")
    anomaly_score: float = Field(description="异常类别得分 0-100")
    
    # 层级结构
    hierarchy_analysis: Optional[Dict[str, Any]] = Field(None, description="层级结构分析")
    hierarchy_score: float = Field(description="层级结构得分 0-100")
    
    # 质量问题
    issues: List[CategoryQualityIssue] = Field(description="发现的质量问题")
    
    # 综合评分
    overall_score: float = Field(description="综合质量得分 0-100")
    quality_level: QualityLevel = Field(description="质量等级")
    recommendations: List[str] = Field(description="改进建议")


class DataQualityReport(BaseModel):
    """数据质量分析报告"""
    dataset_id: str = Field(description="数据集ID")
    analysis_id: str = Field(description="分析ID")
    created_at: datetime = Field(description="创建时间")
    
    # 列级别分析结果
    time_columns: List[TimeColumnQuality] = Field(default_factory=list, description="时间列质量分析")
    parameter_columns: List[ParameterColumnQuality] = Field(default_factory=list, description="参数列质量分析")
    category_columns: List[CategoryColumnQuality] = Field(default_factory=list, description="类目列质量分析")
    
    # 整体评分
    overall_score: float = Field(description="整体数据质量得分 0-100")
    quality_level: QualityLevel = Field(description="整体质量等级")
    
    # 摘要信息
    summary: Dict[str, Any] = Field(description="质量分析摘要")
    key_issues: List[str] = Field(description="关键问题列表")
    recommendations: List[str] = Field(description="整体改进建议")
    
    # 统计信息
    total_columns: int = Field(description="总列数")
    analyzed_columns: int = Field(description="已分析列数")
    high_quality_columns: int = Field(description="高质量列数")
    low_quality_columns: int = Field(description="低质量列数")


class QualityAnalysisRequest(BaseModel):
    """数据质量分析请求"""
    dataset_id: str = Field(description="数据集ID")
    column_types: Optional[Dict[str, ColumnType]] = Field(None, description="列类型映射")
    analysis_config: Dict[str, Any] = Field(default_factory=dict, description="分析配置")
    user_requirements: Optional[str] = Field(None, description="用户特殊要求")


class QualityAnalysisResponse(BaseModel):
    """数据质量分析响应"""
    request_id: str = Field(description="请求ID")
    status: str = Field(description="分析状态")
    report: Optional[DataQualityReport] = Field(None, description="质量报告")
    error_message: Optional[str] = Field(None, description="错误信息")
    processing_time: Optional[float] = Field(None, description="处理时间(秒)") 