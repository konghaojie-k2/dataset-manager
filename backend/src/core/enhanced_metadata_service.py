#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强语义元数据服务 (AI-Native)

功能：
1. 自动生成字段语义描述
2. 数据分布统计（枚举值、范围、均值等）
3. 数据质量评分
4. Agent 可查询的结构化元数据
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger


class EnhancedMetadataService:
    """增强语义元数据服务 - AI-Native"""
    
    def __init__(self):
        logger.info("增强语义元数据服务初始化完成")
    
    async def analyze_dataset(
        self,
        dataset_id: str,
        dataframe: pd.DataFrame,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """全面分析数据集，生成增强语义元数据
        
        Args:
            dataset_id: 数据集ID
            dataframe: 数据框
            sample_size: 采样大小
            
        Returns:
            Dict: 增强语义元数据
        """
        logger.info(f"开始增强元数据分析: {dataset_id}")
        
        # 采样进行分析
        sample_df = dataframe.head(sample_size) if len(dataframe) > sample_size else dataframe
        
        # 1. 基础统计
        basic_stats = self._analyze_basic_statistics(sample_df, dataframe)
        
        # 2. 字段语义分析
        column_semantics = self._analyze_column_semantics(sample_df)
        
        # 3. 数据分布分析
        distributions = self._analyze_distributions(sample_df)
        
        # 4. 数据质量评分
        quality_score = self._calculate_quality_score(dataframe)
        
        # 5. 数据理解摘要
        understanding = self._generate_data_understanding(sample_df, column_semantics)
        
        result = {
            "dataset_id": dataset_id,
            "total_rows": len(dataframe),
            "total_columns": len(dataframe.columns),
            "basic_statistics": basic_stats,
            "column_semantics": column_semantics,
            "distributions": distributions,
            "quality_score": quality_score,
            "data_understanding": understanding,
            "agent_queryable": {
                # Agent 可直接查询的字段
                "quick_summary": self._generate_quick_summary(basic_stats, quality_score),
                "searchable_text": self._generate_searchable_text(column_semantics, understanding),
                "key_fields": self._extract_key_fields(column_semantics)
            }
        }
        
        logger.info(f"增强元数据分析完成: {dataset_id}")
        return result
    
    def _analyze_basic_statistics(self, sample_df: pd.DataFrame, full_df: pd.DataFrame) -> Dict[str, Any]:
        """分析基础统计信息"""
        stats = {
            "row_count": len(full_df),
            "column_count": len(full_df.columns),
            "memory_usage_mb": full_df.memory_usage(deep=True).sum() / 1024 / 1024,
            "column_types": {},
            "numeric_columns": [],
            "categorical_columns": [],
            "datetime_columns": [],
            "text_columns": []
        }
        
        for col in full_df.columns:
            dtype = str(full_df[col].dtype)
            stats["column_types"][col] = dtype
            
            if pd.api.types.is_numeric_dtype(full_df[col]):
                stats["numeric_columns"].append(col)
            elif pd.api.types.is_datetime64_any_dtype(full_df[col]):
                stats["datetime_columns"].append(col)
            elif full_df[col].dtype == 'object':
                # 判断是分类还是文本
                unique_ratio = full_df[col].nunique() / len(full_df[col])
                if unique_ratio < 0.1:  # 低基数视为分类
                    stats["categorical_columns"].append(col)
                else:
                    stats["text_columns"].append(col)
        
        return stats
    
    def _analyze_column_semantics(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """分析字段语义"""
        semantics = []
        
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "semantic_type": self._infer_semantic_type(col, df[col]),
                "business_description": self._generate_business_description(col, df[col]),
                "null_count": int(df[col].isnull().sum()),
                "null_ratio": float(df[col].isnull().sum() / len(df[col])),
                "unique_count": int(df[col].nunique()),
                "unique_ratio": float(df[col].nunique() / len(df[col]))
            }
            
            # 数值型字段额外统计
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info["min"] = float(df[col].min()) if not df[col].isnull().all() else None
                col_info["max"] = float(df[col].max()) if not df[col].isnull().all() else None
                col_info["mean"] = float(df[col].mean()) if not df[col].isnull().all() else None
                col_info["median"] = float(df[col].median()) if not df[col].isnull().all() else None
                col_info["std"] = float(df[col].std()) if not df[col].isnull().all() else None
            
            # 分类字段统计
            if df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col]):
                top_values = df[col].value_counts().head(10)
                col_info["top_values"] = {str(k): int(v) for k, v in top_values.items()}
            
            semantics.append(col_info)
        
        return semantics
    
    def _infer_semantic_type(self, col_name: str, series: pd.Series) -> str:
        """推断字段语义类型"""
        col_lower = col_name.lower()
        
        # ID 类
        if any(kw in col_lower for kw in ['id', 'no', 'number', 'code']):
            return "identifier"
        
        # 时间类
        if any(kw in col_lower for kw in ['time', 'date', 'day', 'hour', 'minute', 'second', 'timestamp']):
            return "timestamp"
        
        # 金额/数值类
        if any(kw in col_lower for kw in ['amount', 'price', 'cost', 'money', 'salary', 'revenue', 'profit']):
            return "currency"
        
        # 数量类
        if any(kw in col_lower for kw in ['count', 'num', 'quantity', 'qty', 'total']):
            return "quantity"
        
        # 百分比类
        if any(kw in col_lower for kw in ['rate', 'ratio', 'percent', 'percentage']):
            return "percentage"
        
        # 状态类
        if any(kw in col_lower for kw in ['status', 'state', 'flag', 'is_', 'has_', 'enable', 'active']):
            return "status"
        
        # 名称类
        if any(kw in col_lower for kw in ['name', 'title', 'desc', 'description', 'remark', 'note']):
            return "name"
        
        # 分类/类型类
        if any(kw in col_lower for kw in ['type', 'kind', 'category', 'class', 'group', 'level']):
            return "category"
        
        # 位置类
        if any(kw in col_lower for kw in ['city', 'country', 'region', 'province', 'address', 'location', 'lat', 'lon']):
            return "location"
        
        # 设备类
        if any(kw in col_lower for kw in ['device', 'machine', 'equipment', 'sensor', 'station']):
            return "device"
        
        # 用户类
        if any(kw in col_lower for kw in ['user', 'customer', 'client', 'member', 'employee']):
            return "user"
        
        return "general"
    
    def _generate_business_description(self, col_name: str, series: pd.Series) -> str:
        """生成业务描述"""
        semantic_type = self._infer_semantic_type(col_name, series)
        
        descriptions = {
            "identifier": f"{col_name} - 唯一标识符",
            "timestamp": f"{col_name} - 时间戳",
            "currency": f"{col_name} - 金额字段",
            "quantity": f"{col_name} - 数量字段",
            "percentage": f"{col_name} - 百分比",
            "status": f"{col_name} - 状态字段",
            "name": f"{col_name} - 名称/描述",
            "category": f"{col_name} - 分类字段",
            "location": f"{col_name} - 位置信息",
            "device": f"{col_name} - 设备信息",
            "user": f"{col_name} - 用户信息",
            "general": f"{col_name} - 通用字段"
        }
        
        return descriptions.get(semantic_type, f"{col_name} - 通用字段")
    
    def _analyze_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析数据分布"""
        distributions = {}
        
        for col in df.select_dtypes(include=[np.number]).columns:
            try:
                hist, bin_edges = np.histogram(df[col].dropna(), bins=10)
                distributions[col] = {
                    "type": "histogram",
                    "bins": bin_edges.tolist(),
                    "counts": hist.tolist()
                }
            except:
                pass
        
        return distributions
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算数据质量评分"""
        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = df.notna().sum().sum()
        
        # 完整性评分
        completeness = non_null_cells / total_cells
        
        # 重复性评分
        duplicate_ratio = df.duplicated().sum() / len(df)
        uniqueness = 1 - duplicate_ratio
        
        # 一致性评分（检查数据类型是否一致）
        consistency = 1.0
        type_issues = 0
        for col in df.columns:
            if df[col].dtype == 'object':
                # 检查是否有混合类型
                try:
                    pd.to_numeric(df[col].dropna().head(100))
                    type_issues += 1
                except:
                    pass
        
        if len(df.columns) > 0:
            consistency = 1 - (type_issues / len(df.columns))
        
        # 综合评分
        overall = (completeness * 0.4 + uniqueness * 0.3 + consistency * 0.3) * 100
        
        return {
            "overall_score": round(overall, 2),
            "completeness": round(completeness * 100, 2),
            "uniqueness": round(uniqueness * 100, 2),
            "consistency": round(consistency * 100, 2),
            "duplicate_rows": int(df.duplicated().sum()),
            "null_cells": int(total_cells - non_null_cells)
        }
    
    def _generate_data_understanding(
        self,
        df: pd.DataFrame,
        column_semantics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成数据理解摘要"""
        
        # 生成一句话摘要
        row_count = len(df)
        col_count = len(df.columns)
        
        # 识别主要数据类型
        numeric_cols = [c for c in column_semantics if c.get('semantic_type') in ['currency', 'quantity', 'percentage']]
        categorical_cols = [c for c in column_semantics if c.get('semantic_type') in ['category', 'status']]
        time_cols = [c for c in column_semantics if c.get('semantic_type') == 'timestamp']
        
        # 生成摘要
        summary_parts = []
        summary_parts.append(f"包含 {row_count} 行 {col_count} 列数据")
        
        if numeric_cols:
            summary_parts.append(f"包含 {len(numeric_cols)} 个数值型字段")
        if categorical_cols:
            summary_parts.append(f"包含 {len(categorical_cols)} 个分类字段")
        if time_cols:
            summary_parts.append(f"包含 {len(time_cols)} 个时间字段")
        
        summary = "，".join(summary_parts) + "。"
        
        # 建议用途
        suggested_uses = []
        if numeric_cols:
            suggested_uses.extend(["统计分析", "机器学习", "预测模型"])
        if categorical_cols:
            suggested_uses.extend(["分类分析", "用户分群"])
        if time_cols:
            suggested_uses.extend(["趋势分析", "时间序列分析"])
        
        # 潜在问题
        issues = []
        null_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        if null_ratio > 0.1:
            issues.append(f"数据缺失率较高 ({null_ratio:.1%})")
        
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            issues.append(f"存在 {duplicate_count} 行重复数据")
        
        return {
            "summary": summary,
            "suggested_uses": list(set(suggested_uses)),
            "potential_issues": issues,
            "main_column_types": {
                "numeric": len(numeric_cols),
                "categorical": len(categorical_cols),
                "datetime": len(time_cols)
            }
        }
    
    def _generate_quick_summary(self, basic_stats: Dict, quality_score: Dict) -> str:
        """生成快速摘要（Agent 快速读取）"""
        return (
            f"数据集包含 {basic_stats['row_count']} 行 {basic_stats['column_count']} 列，"
            f"数据质量评分 {quality_score['overall_score']} 分，"
            f"包含 {len(basic_stats['numeric_columns'])} 个数值列和 "
            f"{len(basic_stats['categorical_columns'])} 个分类列。"
        )
    
    def _generate_searchable_text(self, column_semantics: List[Dict], understanding: Dict) -> str:
        """生成可搜索文本"""
        parts = []
        
        # 列信息
        for col in column_semantics:
            parts.append(col['name'])
            parts.append(col.get('semantic_type', ''))
            parts.append(col.get('business_description', ''))
        
        # 理解信息
        parts.extend(understanding.get('suggested_uses', []))
        parts.extend(understanding.get('potential_issues', []))
        
        return ' '.join(parts)
    
    def _extract_key_fields(self, column_semantics: List[Dict]) -> List[Dict]:
        """提取关键字段（用于 Agent 快速了解结构）"""
        key_fields = []
        
        for col in column_semantics:
            # 选择有代表性的字段
            if col.get('semantic_type') in ['identifier', 'timestamp', 'currency']:
                key_fields.append({
                    "name": col['name'],
                    "type": col['semantic_type'],
                    "description": col.get('business_description', '')
                })
        
        # 如果关键字段太少，补充一些
        if len(key_fields) < 3:
            for col in column_semantics[:5]:
                if col['name'] not in [k['name'] for k in key_fields]:
                    key_fields.append({
                        "name": col['name'],
                        "type": col.get('semantic_type', 'general'),
                        "description": col.get('business_description', '')
                    })
        
        return key_fields[:5]


# 导出服务
enhanced_metadata_service = EnhancedMetadataService()

__all__ = ['EnhancedMetadataService', 'enhanced_metadata_service']
