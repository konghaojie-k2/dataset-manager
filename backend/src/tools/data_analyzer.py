"""数据分析工具"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from loguru import logger

from ..core.fast_data_processor import create_fast_processor, FastDataProcessor


class DataAnalyzer:
    """数据分析工具类（已优化）"""
    
    def __init__(self):
        """初始化数据分析器"""
        self.data: Optional[pd.DataFrame] = None  # 保留兼容性
        self.processor: Optional[FastDataProcessor] = None
        self.analysis_results: Dict[str, Any] = {}
    
    def load_data(self, file_path: Path, nrows: Optional[int] = None, engine_type: Optional[str] = None) -> pd.DataFrame:
        """加载数据（使用 FastDataProcessor）
        
        Args:
            file_path: 文件路径
            nrows: 采样行数（可选）
            engine_type: 引擎类型（可选，自动选择）
            
        Returns:
            pd.DataFrame: 加载的数据
        """
        try:
            # 创建快速处理器
            self.processor = create_fast_processor(file_path, engine_type)
            
            # 加载数据
            if nrows:
                self.data = self.processor.load_sample()
            else:
                # 完整数据可能很大，只加载采样用于兼容性
                self.data = self.processor.load_sample()
            
            logger.info(f"成功加载数据，引擎: {self.processor.engine_type}")
            return self.data
            
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            raise
    
    def close(self):
        """关闭处理器，释放资源"""
        if self.processor:
            self.processor.close()
            self.processor = None
        self.data = None
        logger.info("DataAnalyzer 已关闭")
    
    def get_basic_info(self) -> Dict[str, Any]:
        """获取基础信息（使用 FastDataProcessor）
        
        Returns:
            Dict[str, Any]: 基础信息
        """
        if self.processor is None:
            raise ValueError("请先加载数据")
        
        # 使用 processor 的基础信息
        processor_info = self.processor.get_basic_info()
        
        # 构建兼容的返回格式
        info = {
            "shape": processor_info["shape"],
            "columns": processor_info["columns"],
            "dtypes": processor_info["dtypes"],
            "memory_usage": int(self.data.memory_usage(deep=True).sum()) if self.data is not None else 0,
            "null_counts": processor_info["null_counts"],
            "null_percentages": {col: float((count / processor_info["shape"][0]) * 100) if processor_info["shape"][0] > 0 else 0
                                    for col, count in processor_info["null_counts"].items()},
            "file_size": processor_info["file_size"],
            "file_size_mb": processor_info["file_size_mb"],
            "engine_type": processor_info["engine_type"]
        }
        
        self.analysis_results["basic_info"] = info
        return info
    
    def get_statistical_summary(self) -> Dict[str, Any]:
        """获取统计摘要（使用 FastDataProcessor）
        
        Returns:
            Dict[str, Any]: 统计摘要
        """
        if self.processor is None:
            raise ValueError("请先加载数据")
        
        # 使用 processor 的统计摘要
        processor_summary = self.processor.get_statistical_summary()
        
        # 添加分类型列的统计信息（基于 self.data）
        if self.data is not None:
            categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns
            categorical_summary = processor_summary.get("categorical_summary", {})
            
            for col in categorical_cols:
                if col not in categorical_summary:
                    value_counts = self.data[col].value_counts().head(10)
                    mode_val = self.data[col].mode().iloc[0] if not self.data[col].mode().empty else None
                    
                    categorical_summary[col] = {
                        "unique_count": int(self.data[col].nunique()),
                        "top_values": {str(k): int(v) for k, v in value_counts.to_dict().items()},
                        "mode": str(mode_val) if mode_val is not None else None
                    }
            
            processor_summary["categorical_summary"] = categorical_summary
        
        self.analysis_results["statistical_summary"] = processor_summary
        return processor_summary
    
    def detect_outliers(self, method: str = "iqr") -> Dict[str, Any]:
        """检测异常值
        
        Args:
            method: 检测方法 ('iqr', 'zscore')
            
        Returns:
            Dict[str, Any]: 异常值检测结果
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        outliers = {}
        
        for col in numeric_cols:
            if method == "iqr":
                Q1 = self.data[col].quantile(0.25)
                Q3 = self.data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_mask = (self.data[col] < lower_bound) | (self.data[col] > upper_bound)
                
            elif method == "zscore":
                z_scores = np.abs((self.data[col] - self.data[col].mean()) / self.data[col].std())
                outlier_mask = z_scores > 3
            
            outliers[col] = {
                "count": int(outlier_mask.sum()),
                "percentage": float((outlier_mask.sum() / len(self.data)) * 100),
                "indices": [int(idx) for idx in self.data[outlier_mask].index.tolist()]
            }
        
        self.analysis_results["outliers"] = outliers
        return outliers
    
    def analyze_data_quality(self) -> Dict[str, Any]:
        """分析数据质量
        
        Returns:
            Dict[str, Any]: 数据质量分析结果
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        quality_report = {
            "completeness": {
                "total_cells": int(self.data.size),
                "missing_cells": int(self.data.isnull().sum().sum()),
                "completeness_rate": float((1 - self.data.isnull().sum().sum() / self.data.size) * 100)
            },
            "uniqueness": {},
            "consistency": {},
            "validity": {}
        }
        
        # 唯一性分析
        for col in self.data.columns:
            unique_rate = self.data[col].nunique() / len(self.data) * 100
            quality_report["uniqueness"][col] = {
                "unique_count": int(self.data[col].nunique()),
                "unique_rate": float(unique_rate),
                "is_potential_key": bool(unique_rate > 95)
            }
        
        # 一致性分析（检查数据格式）
        for col in self.data.select_dtypes(include=['object']).columns:
            # 检查字符串长度变化
            str_lengths = self.data[col].dropna().astype(str).str.len()
            quality_report["consistency"][col] = {
                "length_variance": float(str_lengths.var()) if pd.notna(str_lengths.var()) else 0.0,
                "length_range": (int(str_lengths.min()), int(str_lengths.max())),
                "has_mixed_case": bool(self.data[col].dropna().astype(str).apply(
                    lambda x: x != x.lower() and x != x.upper()
                ).any())
            }
        
        self.analysis_results["data_quality"] = quality_report
        return quality_report
    
    def get_column_analysis(self, column_name: str) -> Dict[str, Any]:
        """获取单列详细分析（使用 FastDataProcessor）
        
        Args:
            column_name: 列名
            
        Returns:
            Dict[str, Any]: 列分析结果
        """
        if self.processor is None:
            raise ValueError("请先加载数据")
        
        # 使用 processor 的列分析
        processor_col_info = self.processor.get_column_analysis(column_name)
        
        # 构建兼容的返回格式（包含详细的统计信息）
        analysis = processor_col_info.copy()
        
        # 添加额外的统计信息（基于 self.data）
        if self.data is not None and column_name in self.data.columns:
            col_data = self.data[column_name]
            
            # 计算唯一值百分比
            analysis["unique_percentage"] = float((col_data.nunique() / len(col_data)) * 100) if len(col_data) > 0 else 0.0
            
            # 数值型列的额外分析
            if pd.api.types.is_numeric_dtype(col_data):
                analysis.update({
                    "mean": float(col_data.mean()) if pd.notna(col_data.mean()) else None,
                    "median": float(col_data.median()) if pd.notna(col_data.median()) else None,
                    "std": float(col_data.std()) if pd.notna(col_data.std()) else None,
                    "min": float(col_data.min()) if pd.notna(col_data.min()) else None,
                    "max": float(col_data.max()) if pd.notna(col_data.max()) else None,
                    "skewness": float(col_data.skew()) if pd.notna(col_data.skew()) else None,
                    "kurtosis": float(col_data.kurtosis()) if pd.notna(col_data.kurtosis()) else None
                })
            # 分类型列的额外分析
            else:
                value_counts = col_data.value_counts()
                mode_val = col_data.mode().iloc[0] if not col_data.mode().empty else None
                avg_length = col_data.dropna().astype(str).str.len().mean()
                
                analysis.update({
                    "top_values": {str(k): int(v) for k, v in value_counts.head(10).to_dict().items()},
                    "mode": str(mode_val) if mode_val is not None else None,
                    "avg_length": float(avg_length) if pd.notna(avg_length) else 0.0
                })
        
        return analysis
    
    def get_correlation_analysis(self, threshold: float = 0.5) -> Dict[str, Any]:
        """获取相关性分析
        
        Args:
            threshold: 相关性阈值
            
        Returns:
            Dict[str, Any]: 相关性分析结果
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {"message": "数值型列少于2个，无法进行相关性分析"}
        
        corr_matrix = self.data[numeric_cols].corr()
        
        # 找出高相关性的列对
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= threshold:
                    high_corr_pairs.append({
                        "column1": corr_matrix.columns[i],
                        "column2": corr_matrix.columns[j],
                        "correlation": corr_value
                    })
        
        analysis = {
            "correlation_matrix": corr_matrix.to_dict(),
            "high_correlations": high_corr_pairs,
            "summary": {
                "total_pairs": len(high_corr_pairs),
                "avg_correlation": np.mean([abs(pair["correlation"]) for pair in high_corr_pairs]) if high_corr_pairs else 0
            }
        }
        
        self.analysis_results["correlation_analysis"] = analysis
        return analysis
    
    def get_full_analysis(self) -> Dict[str, Any]:
        """获取完整分析报告
        
        Returns:
            Dict[str, Any]: 完整分析报告
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        logger.info("开始完整数据分析...")
        
        # 执行所有分析
        self.get_basic_info()
        self.get_statistical_summary()
        self.detect_outliers()
        self.analyze_data_quality()
        self.get_correlation_analysis()
        
        # 添加总结信息
        self.analysis_results["summary"] = {
            "total_rows": len(self.data),
            "total_columns": len(self.data.columns),
            "numeric_columns": len(self.data.select_dtypes(include=[np.number]).columns),
            "categorical_columns": len(self.data.select_dtypes(include=['object', 'category']).columns),
            "missing_data_percentage": (self.data.isnull().sum().sum() / self.data.size) * 100,
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
        logger.info("数据分析完成")
        return self.analysis_results