"""元数据处理服务"""

from pathlib import Path
from typing import Dict, Any
import pandas as pd
from loguru import logger

from ..agents import create_metadata_agent
from ..schemas.dataset import DatasetMetadata, ColumnMetadata, DataQualityMetrics


class MetadataService:
    """元数据处理服务"""
    
    def __init__(self):
        """初始化元数据服务"""
        # 使用新的简洁 agent 工厂创建元数据代理
        self.metadata_agent = create_metadata_agent()
        
        logger.info("元数据处理服务初始化完成")
    
    async def extract_metadata(
        self, 
        dataset_id: str, 
        file_path: Path, 
        dataframe: pd.DataFrame,
        user_input: str = None
    ) -> Dict[str, Any]:
        """提取数据集元数据
        
        Args:
            dataset_id: 数据集ID
            file_path: 文件路径
            dataframe: 数据框
            user_input: 用户输入的额外信息
            
        Returns:
            Dict[str, Any]: 提取结果
        """
        try:
            logger.info(f"开始提取元数据: {dataset_id}")
            
            # 暂时返回基础的元数据信息，后续可以集成新的 agent
            # TODO: 集成新的简洁 agent 接口
            basic_info = self._extract_basic_metadata(dataframe, file_path)
            
            logger.info(f"元数据提取完成: {dataset_id}")
            return basic_info
            
        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            raise
    
    def _extract_basic_metadata(self, dataframe: pd.DataFrame, file_path: Path) -> Dict[str, Any]:
        """提取基础元数据信息
        
        Args:
            dataframe: 数据框
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 基础元数据
        """
        # 基础统计信息
        columns_metadata = []
        for col in dataframe.columns:
            columns_metadata.append({
                "name": col,
                "dtype": str(dataframe[col].dtype),
                "business_meaning": f"列 {col}",
                "is_device_id": "id" in col.lower() or "device" in col.lower(),
                "is_timestamp": "time" in col.lower() or "date" in col.lower(),
                "null_count": int(dataframe[col].isnull().sum()),
                "unique_count": int(dataframe[col].nunique()),
                "sample_values": dataframe[col].dropna().head(3).astype(str).tolist()
            })
        
        return {
            "dataset_description": f"数据集包含 {dataframe.shape[0]} 行 {dataframe.shape[1]} 列",
            "time_range_start": None,
            "time_range_end": None,
            "sampling_rate": None,
            "columns_metadata": columns_metadata,
            "quality_metrics": {
                "total_rows": dataframe.shape[0],
                "total_columns": dataframe.shape[1],
                "missing_value_ratio": float(dataframe.isnull().sum().sum() / (dataframe.shape[0] * dataframe.shape[1])),
                "duplicate_rows": int(dataframe.duplicated().sum()),
                "data_completeness": float((dataframe.notna().sum().sum()) / (dataframe.shape[0] * dataframe.shape[1])),
                "quality_score": float(min(100, max(0, (1 - dataframe.isnull().sum().sum() / (dataframe.shape[0] * dataframe.shape[1])) * 100))),
                "quality_issues": self._identify_quality_issues(dataframe),
                "recommendations": self._generate_recommendations(dataframe)
            },
            "suggested_tags": ["数据分析", "数据集"],
            "suggested_industry": "通用",
            "suggested_domains": ["数据科学"],
            "suggested_algorithms": ["统计分析", "机器学习"]
        }
    
    def update_dataset_metadata(
        self, 
        dataset: DatasetMetadata, 
        extraction_result: Dict[str, Any]
    ) -> DatasetMetadata:
        """从提取结果更新数据集元数据
        
        Args:
            dataset: 数据集元数据
            extraction_result: 提取结果
            
        Returns:
            DatasetMetadata: 更新后的数据集元数据
        """
        try:
            # 更新基本信息
            basic_info = extraction_result.get("basic_info", {})
            dataset.description = extraction_result.get("dataset_description", basic_info.get("description", ""))
            dataset.time_range_start = extraction_result.get("time_range_start")
            dataset.time_range_end = extraction_result.get("time_range_end")
            dataset.sampling_rate = extraction_result.get("sampling_rate")
            
            # 更新列信息
            columns_metadata = extraction_result.get("columns_metadata", [])
            if not columns_metadata and basic_info.get("columns"):
                # 从basic_info中提取列信息
                columns_metadata = []
                for col_name in basic_info["columns"]:
                    columns_metadata.append({
                        "name": col_name,
                        "dtype": "unknown",
                        "business_meaning": f"列 {col_name}",
                        "is_device_id": "id" in col_name.lower() or "device" in col_name.lower(),
                        "is_timestamp": "time" in col_name.lower() or "date" in col_name.lower(),
                        "null_count": 0,
                        "unique_count": 0,
                        "sample_values": []
                    })
            
            dataset.columns = [
                ColumnMetadata(
                    name=col["name"],
                    data_type=col.get("dtype", "unknown"),
                    business_meaning=col.get("business_meaning", ""),
                    is_device_id=col.get("is_device_id", False),
                    is_timestamp=col.get("is_timestamp", False),
                    null_count=col.get("null_count", 0),
                    unique_count=col.get("unique_count", 0),
                    sample_values=col.get("sample_values", [])
                )
                for col in columns_metadata
            ]
            
            # 更新数据质量
            quality_data = extraction_result.get("quality_metrics", {})
            if quality_data:
                dataset.quality_metrics = DataQualityMetrics(**quality_data)
            
            # 更新工业数据分析结果
            dataset.device_time_identification = extraction_result.get("device_time_identification")
            dataset.business_meaning_analysis = extraction_result.get("business_meaning_analysis")
            dataset.control_relationships_analysis = extraction_result.get("control_relationships_analysis")
            dataset.basic_analysis = extraction_result.get("basic_analysis")
            dataset.detailed_analysis = extraction_result.get("detailed_analysis")
            dataset.insights = extraction_result.get("insights", [])
            dataset.recommendations = extraction_result.get("recommendations")
            
            # 更新建议的标签
            suggested_tags = extraction_result.get("suggested_tags", [])
            if not suggested_tags:
                suggested_tags = dataset.tags or []
            dataset.tags = suggested_tags
            dataset.industry = extraction_result.get("suggested_industry", dataset.industry)
            dataset.analysis_domains = extraction_result.get("suggested_domains", dataset.analysis_domains or [])
            dataset.applicable_algorithms = extraction_result.get("suggested_algorithms", dataset.applicable_algorithms or [])
            
            # 更新状态
            dataset.processing_status = "metadata_extracted"
            dataset.metadata_extracted = True
            
            logger.info(f"数据集元数据更新完成: {dataset.id}")
            return dataset
            
        except Exception as e:
            logger.error(f"更新数据集元数据失败: {e}")
            raise
    
    def _identify_quality_issues(self, dataframe: pd.DataFrame) -> list:
        """识别数据质量问题
        
        Args:
            dataframe: 数据框
            
        Returns:
            list: 质量问题列表
        """
        issues = []
        
        # 检查缺失值
        missing_ratio = dataframe.isnull().sum().sum() / (dataframe.shape[0] * dataframe.shape[1])
        if missing_ratio > 0.1:
            issues.append(f"数据缺失率较高: {missing_ratio:.2%}")
        
        # 检查重复行
        duplicate_count = dataframe.duplicated().sum()
        if duplicate_count > 0:
            issues.append(f"存在 {duplicate_count} 行重复数据")
        
        # 检查列名问题
        if any(' ' in col for col in dataframe.columns):
            issues.append("部分列名包含空格")
        
        # 检查数据类型一致性
        for col in dataframe.select_dtypes(include=['object']).columns:
            if dataframe[col].dtype == 'object':
                # 检查是否应该是数值型
                try:
                    pd.to_numeric(dataframe[col].dropna().head(100))
                    issues.append(f"列 '{col}' 可能应该是数值型")
                except:
                    pass
        
        return issues
    
    def _generate_recommendations(self, dataframe: pd.DataFrame) -> list:
        """生成数据质量改进建议
        
        Args:
            dataframe: 数据框
            
        Returns:
            list: 改进建议列表
        """
        recommendations = []
        
        # 缺失值处理建议
        missing_ratio = dataframe.isnull().sum().sum() / (dataframe.shape[0] * dataframe.shape[1])
        if missing_ratio > 0.05:
            recommendations.append("建议处理缺失值：删除、填充或插值")
        
        # 重复数据处理建议
        duplicate_count = dataframe.duplicated().sum()
        if duplicate_count > 0:
            recommendations.append("建议删除重复行数据")
        
        # 数据类型优化建议
        if len(dataframe.select_dtypes(include=['object']).columns) > 0:
            recommendations.append("建议检查并优化数据类型")
        
        # 列名规范化建议
        if any(' ' in col or col != col.strip() for col in dataframe.columns):
            recommendations.append("建议规范化列名（去除空格、统一命名风格）")
        
        # 数据量建议
        if len(dataframe) < 100:
            recommendations.append("数据量较小，建议增加更多样本")
        elif len(dataframe) > 1000000:
            recommendations.append("数据量较大，建议考虑采样或分批处理")
        
        return recommendations 