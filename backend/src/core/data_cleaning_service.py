#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据清洗服务

自动识别并清洗数据中的问题
"""

from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import pandas as pd
import numpy as np
import re


class DataCleaningService:
    """智能数据清洗服务"""
    
    def __init__(self):
        logger.info("智能数据清洗服务初始化完成")
    
    async def clean(
        self,
        dataframe: pd.DataFrame,
        auto_detect: bool = True
    ) -> Dict[str, Any]:
        """清洗数据
        
        Args:
            dataframe: 数据框
            auto_detect: 是否自动检测问题
            
        Returns:
            清洗结果
        """
        logger.info("开始数据清洗")
        
        df = dataframe.copy()
        issues_found = []
        fixes_applied = []
        
        # 1. 检测并处理缺失值
        missing_issues, missing_fixes = self._handle_missing_values(df)
        issues_found.extend(missing_issues)
        fixes_applied.extend(missing_fixes)
        
        # 2. 检测并处理重复行
        duplicate_issues, duplicate_fixes = self._handle_duplicates(df)
        issues_found.extend(duplicate_issues)
        fixes_applied.extend(duplicate_fixes)
        
        # 3. 检测并处理异常值
        outlier_issues, outlier_fixes = self._handle_outliers(df)
        issues_found.extend(outlier_issues)
        fixes_applied.extend(outlier_fixes)
        
        # 4. 标准化数据格式
        format_issues, format_fixes = self._standardize_formats(df)
        issues_found.extend(format_issues)
        fixes_applied.extend(format_fixes)
        
        # 5. 处理不一致的数据
        consistency_issues, consistency_fixes = self._handle_inconsistency(df)
        issues_found.extend(consistency_issues)
        fixes_applied.extend(consistency_fixes)
        
        return {
            "original_rows": len(dataframe),
            "cleaned_rows": len(df),
            "issues_found": issues_found,
            "fixes_applied": fixes_applied,
            "cleaned_data": df,
            "summary": self._create_cleaning_summary(issues_found, fixes_applied)
        }
    
    def _handle_missing_values(self, df: pd.DataFrame) -> Tuple[List, List]:
        """处理缺失值"""
        issues = []
        fixes = []
        
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_ratio = null_count / len(df)
            
            if null_count == 0:
                continue
            
            issue = f"列 '{col}' 存在 {null_count} 个缺失值 ({null_ratio:.1%})"
            issues.append({
                "type": "missing_values",
                "column": col,
                "count": int(null_count),
                "description": issue
            })
            
            # 根据数据类型选择填充方式
            if pd.api.types.is_numeric_dtype(df[col]):
                # 数值型用均值填充
                mean_value = df[col].mean()
                df[col].fillna(mean_value, inplace=True)
                fix = f"列 '{col}' 用均值 {mean_value:.2f} 填充"
                fixes.append({"type": "fillna", "column": col, "method": "mean"})
            else:
                # 分类用众数填充
                mode_value = df[col].mode()
                if len(mode_value) > 0:
                    df[col].fillna(mode_value[0], inplace=True)
                    fixes.append({"type": "fillna", "column": col, "method": "mode"})
        
        return issues, fixes
    
    def _handle_duplicates(self, df: pd.DataFrame) -> Tuple[List, List]:
        """处理重复行"""
        issues = []
        fixes = []
        
        duplicate_count = df.duplicated().sum()
        
        if duplicate_count > 0:
            issues.append({
                "type": "duplicates",
                "count": int(duplicate_count),
                "description": f"存在 {duplicate_count} 行重复数据"
            })
            
            df.drop_duplicates(inplace=True)
            fixes.append({
                "type": "drop_duplicates",
                "count": int(duplicate_count)
            })
        
        return issues, fixes
    
    def _handle_outliers(self, df: pd.DataFrame) -> Tuple[List, List]:
        """处理异常值"""
        issues = []
        fixes = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # 使用 IQR 方法检测异常值
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            
            if outliers > 0:
                issues.append({
                    "type": "outliers",
                    "column": col,
                    "count": int(outliers),
                    "description": f"列 '{col}' 存在 {outliers} 个异常值"
                })
                
                # 用边界值替换异常值
                df[col] = df[col].clip(lower_bound, upper_bound)
                fixes.append({
                    "type": "clip_outliers",
                    "column": col,
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound)
                })
        
        return issues, fixes
    
    def _standardize_formats(self, df: pd.DataFrame) -> Tuple[List, List]:
        """标准化数据格式"""
        issues = []
        fixes = []
        
        # 1. 去除首尾空格
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            if df[col].dtype == 'object':
                before = df[col].astype(str).str.strip()
                changed = (before != df[col].astype(str)).sum()
                if changed > 0:
                    df[col] = before
                    issues.append({
                        "type": "whitespace",
                        "column": col,
                        "count": int(changed),
                        "description": f"列 '{col}' 有 {changed} 个值包含首尾空格"
                    })
                    fixes.append({
                        "type": "strip_whitespace",
                        "column": col
                    })
        
        # 2. 标准化日期格式
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    converted = pd.to_datetime(df[col], errors='coerce')
                    if converted.notna().sum() > 0:
                        df[col] = converted
                        issues.append({
                            "type": "date_format",
                            "column": col,
                            "description": f"列 '{col}' 日期格式已标准化"
                        })
                        fixes.append({
                            "type": "standardize_date",
                            "column": col
                        })
                except:
                    pass
        
        return issues, fixes
    
    def _handle_inconsistency(self, df: pd.DataFrame) -> Tuple[List, List]:
        """处理数据不一致"""
        issues = []
        fixes = []
        
        # 1. 统一大小写
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            # 检查是否看起来像需要统一大小写的数据（如性别、状态）
            unique_values = df[col].dropna().unique()
            if len(unique_values) <= 10:
                # 转为小写检查
                lower_values = [str(v).lower().strip() for v in unique_values]
                if len(lower_values) != len(set(lower_values)):
                    # 有不一致的大小写
                    df[col] = df[col].astype(str).str.lower().str.strip()
                    issues.append({
                        "type": "case_inconsistency",
                        "column": col,
                        "description": f"列 '{col}' 大小写已统一为小写"
                    })
                    fixes.append({
                        "type": "normalize_case",
                        "column": col
                    })
        
        return issues, fixes
    
    def _create_cleaning_summary(self, issues: List, fixes: List) -> str:
        """创建清洗摘要"""
        if not issues:
            return "数据已经很干净，无需清洗 ✓"
        
        parts = []
        parts.append(f"发现 {len(issues)} 个问题，应用 {len(fixes)} 个修复")
        
        issue_types = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        for issue_type, count in issue_types.items():
            parts.append(f"- {issue_type}: {count} 个")
        
        return "，".join(parts)


# 导出
data_cleaning_service = DataCleaningService()

__all__ = ['DataCleaningService', 'data_cleaning_service']
