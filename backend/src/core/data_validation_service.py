#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证服务

验证数据是否符合预期的 schema 和规则
"""

from typing import Dict, Any, List, Optional, Callable
from loguru import logger
import pandas as pd
import re


class DataValidationService:
    """数据验证服务"""
    
    def __init__(self):
        self.rules = {}
        logger.info("数据验证服务初始化完成")
    
    async def validate(
        self,
        dataframe: pd.DataFrame,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证数据是否符合 schema
        
        Args:
            dataframe: 数据框
            schema: 期望的 schema
            
        Returns:
            验证结果
        """
        logger.info("开始数据验证")
        
        errors = []
        warnings = []
        
        # 1. 验证列
        column_errors, column_warnings = self._validate_columns(dataframe, schema)
        errors.extend(column_errors)
        warnings.extend(column_warnings)
        
        # 2. 验证数据类型
        type_errors = self._validate_types(dataframe, schema)
        errors.extend(type_errors)
        
        # 3. 验证约束
        constraint_errors = self._validate_constraints(dataframe, schema)
        errors.extend(constraint_errors)
        
        # 4. 计算验证分数
        score = self._calculate_validation_score(
            total_columns=len(dataframe.columns),
            errors=len(errors),
            warnings=len(warnings)
        )
        
        return {
            "is_valid": len(errors) == 0,
            "score": score,
            "errors": errors,
            "warnings": warnings,
            "summary": self._create_summary(errors, warnings)
        }
    
    def _validate_columns(
        self,
        df: pd.DataFrame,
        schema: Dict[str, Any]
    ) -> tuple:
        """验证列"""
        errors = []
        warnings = []
        
        required_columns = schema.get("required_columns", [])
        allowed_columns = schema.get("allowed_columns", [])
        
        # 检查必需列
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"缺少必需列: {col}")
        
        # 检查额外列
        if allowed_columns:
            extra_columns = set(df.columns) - set(allowed_columns)
            if extra_columns:
                warnings.append(f"存在额外列: {list(extra_columns)}")
        
        return errors, warnings
    
    def _validate_types(self, df: pd.DataFrame, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """验证数据类型"""
        errors = []
        
        column_types = schema.get("column_types", {})
        
        for col, expected_type in column_types.items():
            if col not in df.columns:
                continue
            
            actual_type = str(df[col].dtype)
            
            if expected_type == "number":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"列 '{col}' 应为数值型，当前为 {actual_type}")
            
            elif expected_type == "string":
                if df[col].dtype != 'object':
                    errors.append(f"列 '{col}' 应为字符串型，当前为 {actual_type}")
            
            elif expected_type == "datetime":
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    errors.append(f"列 '{col}' 应为日期时间型，当前为 {actual_type}")
            
            elif expected_type == "boolean":
                if df[col].dtype != 'bool' and df[col].dtype != 'object':
                    errors.append(f"列 '{col}' 应为布尔型，当前为 {actual_type}")
        
        return errors
    
    def _validate_constraints(
        self,
        df: pd.DataFrame,
        schema: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证约束"""
        errors = []
        
        constraints = schema.get("constraints", {})
        
        # 非空约束
        not_null_columns = constraints.get("not_null", [])
        for col in not_null_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    errors.append(f"列 '{col}' 存在 {null_count} 个空值")
        
        # 唯一约束
        unique_columns = constraints.get("unique", [])
        for col in unique_columns:
            if col in df.columns:
                duplicate_count = df[col].duplicated().sum()
                if duplicate_count > 0:
                    errors.append(f"列 '{col}' 存在 {duplicate_count} 个重复值")
        
        # 范围约束
        range_constraints = constraints.get("range", {})
        for col, range_info in range_constraints.items():
            if col not in df.columns:
                continue
            
            min_val = range_info.get("min")
            max_val = range_info.get("max")
            
            if min_val is not None:
                below_min = (df[col] < min_val).sum()
                if below_min > 0:
                    errors.append(f"列 '{col}' 有 {below_min} 个值小于最小值 {min_val}")
            
            if max_val is not None:
                above_max = (df[col] > max_val).sum()
                if above_max > 0:
                    errors.append(f"列 '{col}' 有 {above_max} 个值大于最大值 {max_val}")
        
        # 枚举约束
        enum_constraints = constraints.get("enum", {})
        for col, allowed_values in enum_constraints.items():
            if col not in df.columns:
                continue
            
            invalid_values = ~df[col].isin(allowed_values)
            invalid_count = invalid_values.sum()
            if invalid_count > 0:
                errors.append(f"列 '{col}' 有 {invalid_count} 个值不在允许范围内")
        
        return errors
    
    def _calculate_validation_score(
        self,
        total_columns: int,
        errors: int,
        warnings: int
    ) -> float:
        """计算验证分数"""
        if total_columns == 0:
            return 0.0
        
        base_score = 100.0
        base_score -= errors * 10  # 每个错误扣 10 分
        base_score -= warnings * 2  # 每个警告扣 2 分
        
        return max(0, base_score)
    
    def _create_summary(self, errors: List, warnings: List) -> str:
        """创建摘要"""
        if not errors and not warnings:
            return "数据验证通过 ✓"
        
        parts = []
        if errors:
            parts.append(f"{len(errors)} 个错误")
        if warnings:
            parts.append(f"{len(warnings)} 个警告")
        
        return f"数据验证未通过: {', '.join(parts)}"


# 预定义验证规则
VALIDATION_RULES = {
    "email": lambda x: bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(x))),
    "phone": lambda x: bool(re.match(r'^1[3-9]\d{9}$', str(x))),
    "url": lambda x: bool(re.match(r'^https?://', str(x))),
    "date": lambda x: pd.notna(pd.to_datetime(x, errors='coerce')),
}


# 导出
data_validation_service = DataValidationService()

__all__ = ['DataValidationService', 'data_validation_service', 'VALIDATION_RULES']
