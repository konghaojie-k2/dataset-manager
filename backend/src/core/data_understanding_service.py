#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据理解服务

自动分析数据并生成洞察报告
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from loguru import logger


class DataUnderstandingService:
    """智能数据理解服务"""
    
    def __init__(self):
        logger.info("智能数据理解服务初始化完成")
    
    async def understand(
        self,
        dataframe: pd.DataFrame,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """全面理解数据集
        
        Args:
            dataframe: 数据框
            sample_size: 采样大小
            
        Returns:
            Dict: 理解报告
        """
        logger.info("开始数据理解分析")
        
        sample_df = dataframe.head(sample_size) if len(dataframe) > sample_size else dataframe
        
        # 1. 基础理解
        basic = self._understand_basics(sample_df, dataframe)
        
        # 2. 内容理解
        content = self._understand_content(sample_df)
        
        # 3. 质量理解
        quality = self._understand_quality(sample_df)
        
        # 4. 关系理解
        relationships = self._understand_relationships(sample_df)
        
        # 5. 生成洞察
        insights = self._generate_insights(basic, content, quality, relationships)
        
        # 6. 生成建议
        recommendations = self._generate_recommendations(basic, content, quality)
        
        return {
            "summary": self._create_summary(basic, content),
            "basic_info": basic,
            "content_analysis": content,
            "quality_analysis": quality,
            "relationships": relationships,
            "insights": insights,
            "recommendations": recommendations,
            "natural_language": self._generate_natural_language(basic, content, insights)
        }
    
    def _understand_basics(self, sample_df: pd.DataFrame, full_df: pd.DataFrame) -> Dict[str, Any]:
        """理解基础信息"""
        return {
            "row_count": len(full_df),
            "column_count": len(full_df.columns),
            "memory_mb": full_df.memory_usage(deep=True).sum() / 1024 / 1024,
            "column_names": list(full_df.columns),
            "dtypes": {col: str(full_df[col].dtype) for col in full_df.columns}
        }
    
    def _understand_content(self, sample_df: pd.DataFrame) -> Dict[str, Any]:
        """理解数据内容"""
        content = {
            "numeric_summary": {},
            "categorical_summary": {},
            "temporal_summary": {},
            "text_samples": []
        }
        
        for col in sample_df.columns:
            if pd.api.types.is_numeric_dtype(sample_df[col]):
                content["numeric_summary"][col] = {
                    "min": float(sample_df[col].min()) if not sample_df[col].isnull().all() else None,
                    "max": float(sample_df[col].max()) if not sample_df[col].isnull().all() else None,
                    "mean": float(sample_df[col].mean()) if not sample_df[col].isnull().all() else None,
                    "std": float(sample_df[col].std()) if not sample_df[col].isnull().all() else None,
                }
            
            elif sample_df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(sample_df[col]):
                top_values = sample_df[col].value_counts().head(5)
                content["categorical_summary"][col] = {
                    "unique_count": int(sample_df[col].nunique()),
                    "top_values": {str(k): int(v) for k, v in top_values.items()}
                }
            
            elif pd.api.types.is_datetime64_any_dtype(sample_df[col]):
                content["temporal_summary"][col] = {
                    "min": str(sample_df[col].min()),
                    "max": str(sample_df[col].max()),
                    "range_days": (sample_df[col].max() - sample_df[col].min()).days if not sample_df[col].isnull().all() else None
                }
        
        return content
    
    def _understand_quality(self, sample_df: pd.DataFrame) -> Dict[str, Any]:
        """理解数据质量"""
        total_cells = sample_df.shape[0] * sample_df.shape[1]
        null_cells = sample_df.isnull().sum().sum()
        
        return {
            "completeness": 1 - (null_cells / total_cells),
            "null_by_column": {col: int(sample_df[col].isnull().sum()) for col in sample_df.columns},
            "duplicate_rows": int(sample_df.duplicated().sum()),
            "empty_columns": [col for col in sample_df.columns if sample_df[col].isnull().all()]
        }
    
    def _understand_relationships(self, sample_df: pd.DataFrame) -> Dict[str, Any]:
        """理解数据关系"""
        numeric_cols = sample_df.select_dtypes(include=[np.number]).columns
        
        relationships = {
            "correlations": {}
        }
        
        if len(numeric_cols) > 1:
            corr_matrix = sample_df[numeric_cols].corr()
            # 找出高相关性的列对
            high_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    if abs(corr_matrix.iloc[i, j]) > 0.7:
                        high_corr.append({
                            "col1": corr_matrix.columns[i],
                            "col2": corr_matrix.columns[j],
                            "correlation": float(corr_matrix.iloc[i, j])
                        })
            relationships["high_correlations"] = high_corr
        
        return relationships
    
    def _generate_insights(
        self,
        basic: Dict,
        content: Dict,
        quality: Dict,
        relationships: Dict
    ) -> List[str]:
        """生成洞察"""
        insights = []
        
        # 数据量洞察
        row_count = basic.get("row_count", 0)
        if row_count < 100:
            insights.append("数据量较小，可能不足以进行深度分析")
        elif row_count > 1000000:
            insights.append("数据量较大，建议使用采样或分布式处理")
        
        # 列数洞察
        col_count = basic.get("column_count", 0)
        if col_count > 50:
            insights.append("列数较多，数据结构较复杂")
        elif col_count < 5:
            insights.append("列数较少，数据结构相对简单")
        
        # 质量洞察
        completeness = quality.get("completeness", 1)
        if completeness < 0.8:
            insights.append(f"数据完整性较低 ({completeness:.1%})，建议处理缺失值")
        
        # 数值洞察
        numeric_cols = content.get("numeric_summary", {})
        if numeric_cols:
            for col, stats in numeric_cols.items():
                if stats.get("std", 0) == 0:
                    insights.append(f"列 '{col}' 所有值相同，无变异")
        
        # 分类洞察
        categorical_cols = content.get("categorical_summary", {})
        for col, summary in categorical_cols.items():
            unique = summary.get("unique_count", 0)
            total = basic.get("row_count", 1)
            if unique == total:
                insights.append(f"列 '{col}' 每个值都是唯一的，可能是ID列")
        
        # 关系洞察
        high_corr = relationships.get("high_correlations", [])
        if high_corr:
            for corr in high_corr[:3]:
                insights.append(
                    f"列 '{corr['col1']}' 和 '{corr['col2']}' 高度相关 ("
                    f"{corr['correlation']:.2f})"
                )
        
        return insights
    
    def _generate_recommendations(
        self,
        basic: Dict,
        content: Dict,
        quality: Dict
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 数据量建议
        row_count = basic.get("row_count", 0)
        if row_count < 1000:
            recommendations.append("建议收集更多数据以获得更有意义的分析结果")
        
        # 数据类型建议
        for col, dtype in basic.get("dtypes", {}).items():
            if dtype == 'object':
                # 检查是否应该是数值
                if col.lower() in ['age', 'year', 'month', 'day', 'hour', 'count', 'num']:
                    recommendations.append(f"列 '{col}' 可能是数值型，建议转换数据类型")
        
        # 缺失值建议
        null_by_col = quality.get("null_by_column", {})
        for col, null_count in null_by_col.items():
            if null_count > 0:
                ratio = null_count / basic.get("row_count", 1)
                if ratio > 0.3:
                    recommendations.append(f"列 '{col}' 缺失值较多 ({ratio:.1%})，建议处理")
        
        return recommendations
    
    def _create_summary(self, basic: Dict, content: Dict) -> str:
        """创建摘要"""
        row_count = basic.get("row_count", 0)
        col_count = basic.get("column_count", 0)
        
        numeric_count = len(content.get("numeric_summary", {}))
        categorical_count = len(content.get("categorical_summary", {}))
        temporal_count = len(content.get("temporal_summary", {}))
        
        return (
            f"数据集包含 {row_count:,} 行 {col_count} 列，"
            f"其中 {numeric_count} 个数值列、{categorical_count} 个分类列、"
            f"{temporal_count} 个时间列。"
        )
    
    def _generate_natural_language(
        self,
        basic: Dict,
        content: Dict,
        insights: List[str]
    ) -> str:
        """生成自然语言描述"""
        parts = []
        
        # 基础描述
        parts.append(self._create_summary(basic, content))
        
        # 内容描述
        numeric_cols = list(content.get("numeric_summary", {}).keys())
        if numeric_cols:
            parts.append(f"主要数值字段包括：{', '.join(numeric_cols[:5])}。")
        
        # 洞察总结
        if insights:
            parts.append(f"关键发现：{insights[0]}")
        
        return " ".join(parts)


# 导出
data_understanding_service = DataUnderstandingService()

__all__ = ['DataUnderstandingService', 'data_understanding_service']
