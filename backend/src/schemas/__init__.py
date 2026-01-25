"""数据结构定义包 (Schemas)

提供项目中所有数据结构的定义：
- dataset: 数据集相关结构
- analysis: 分析相关结构

使用 Pydantic 定义类型安全的数据结构，避免与 LLM models 混淆
"""

# 数据集相关结构
from .dataset import (
    DatasetMetadata,
    ColumnMetadata,
    DataQualityMetrics,
    UploadRequest,
    MetadataExtractionRequest,
    TagUpdateRequest
)

# 标签相关结构
from .tag import (
    Tag,
    TagCreateRequest,
    TagUpdateRequest as TagUpdateRequestModel,
    TagListResponse,
    DatasetTagUpdateRequest,
    TagCategory
)

# 分析相关结构
from .analysis import (
    AnalysisType,
    AnalysisStatus,
    AnalysisRequest,
    AnalysisResult,
    StatisticalSummary,
    CorrelationMatrix,
    AnomalyDetectionResult,
    TrendAnalysisResult,
    ModelTrainingRequest,
    ModelTrainingResult
)

# 数据质量相关结构
from .data_quality import (
    QualityLevel,
    ColumnType,
    TimeQualityIssue,
    TimeColumnQuality,
    ParameterQualityIssue,
    ParameterColumnQuality,
    CategoryQualityIssue,
    CategoryColumnQuality,
    DataQualityReport,
    QualityAnalysisRequest,
    QualityAnalysisResponse
)

__all__ = [
    # 数据集结构
    "DatasetMetadata",
    "ColumnMetadata", 
    "DataQualityMetrics",
    "UploadRequest",
    "MetadataExtractionRequest",
    "TagUpdateRequest",
    
    # 标签结构
    "Tag",
    "TagCreateRequest",
    "TagUpdateRequestModel",
    "TagListResponse",
    "DatasetTagUpdateRequest",
    "TagCategory",
    
    # 分析结构
    "AnalysisType",
    "AnalysisStatus", 
    "AnalysisRequest",
    "AnalysisResult",
    "StatisticalSummary",
    "CorrelationMatrix",
    "AnomalyDetectionResult",
    "TrendAnalysisResult",
    "ModelTrainingRequest",
    "ModelTrainingResult",
    
    # 数据质量结构
    "QualityLevel",
    "ColumnType",
    "TimeQualityIssue",
    "TimeColumnQuality",
    "ParameterQualityIssue",
    "ParameterColumnQuality",
    "CategoryQualityIssue",
    "CategoryColumnQuality",
    "DataQualityReport",
    "QualityAnalysisRequest",
    "QualityAnalysisResponse",
] 