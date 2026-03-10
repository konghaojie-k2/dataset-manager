#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据转换服务

提供常用的数据转换功能
"""

from typing import Dict, Any, List, Optional, Callable
from loguru import logger
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class DataTransformationService:
    """智能数据转换服务"""
    
    def __init__(self):
        self.transformations = {
            "pivot": self._pivot_table,
            "unpivot": self._unpivot_table,
            "aggregate": self._aggregate,
            "filter": self._filter,
            "sort": self._sort,
            "join": self._join,
            "merge": self._merge,
            "deduplicate": self._deduplicate,
            "resample": self._resample_time,
            "normalize": self._normalize,
            "encode": self._encode_categorical,
            "bin": self._create_bins,
            "add_column": self._add_calculated_column,
            "date_features": self._extract_date_features,
        }
        logger.info("智能数据转换服务初始化完成")
    
    async def transform(
        self,
        dataframe: pd.DataFrame,
        transformation: str,
        **params
    ) -> Dict[str, Any]:
        """执行数据转换
        
        Args:
            dataframe: 数据框
            transformation: 转换类型
            **params: 转换参数
            
        Returns:
            转换结果
        """
        logger.info(f"执行转换: {transformation}")
        
        transformer = self.transformations.get(transformation)
        if not transformer:
            raise ValueError(f"不支持的转换类型: {transformation}")
        
        result_df = await transformer(dataframe, **params)
        
        return {
            "transformation": transformation,
            "original_shape": dataframe.shape,
            "result_shape": result_df.shape,
            "result": result_df
        }
    
    async def _pivot_table(
        self,
        df: pd.DataFrame,
        index: str,
        columns: str,
        values: str,
        aggfunc: str = "sum"
    ) -> pd.DataFrame:
        """透视表"""
        return df.pivot_table(
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc,
            fill_value=0
        )
    
    async def _unpivot_table(
        self,
        df: pd.DataFrame,
        id_vars: List[str],
        value_vars: List[str],
        var_name: str = "variable",
        value_name: str = "value"
    ) -> pd.DataFrame:
        """逆透视"""
        return pd.melt(
            df,
            id_vars=id_vars,
            value_vars=value_vars,
            var_name=var_name,
            value_name=value_name
        )
    
    async def _aggregate(
        self,
        df: pd.DataFrame,
        group_by: List[str],
        aggregations: Dict[str, str]
    ) -> pd.DataFrame:
        """聚合"""
        return df.groupby(group_by).agg(aggregations).reset_index()
    
    async def _filter(
        self,
        df: pd.DataFrame,
        conditions: Dict[str, Any]
    ) -> pd.DataFrame:
        """过滤"""
        result = df.copy()
        for col, value in conditions.items():
            if isinstance(value, dict):
                op = value.get("op", "==")
                val = value.get("value")
                if op == "==":
                    result = result[result[col] == val]
                elif op == "!=":
                    result = result[result[col] != val]
                elif op == ">":
                    result = result[result[col] > val]
                elif op == "<":
                    result = result[result[col] < val]
                elif op == ">=":
                    result = result[result[col] >= val]
                elif op == "<=":
                    result = result[result[col] <= val]
                elif op == "in":
                    result = result[result[col].isin(val)]
                elif op == "contains":
                    result = result[result[col].astype(str).str.contains(val)]
            else:
                result = result[result[col] == value]
        return result
    
    async def _sort(
        self,
        df: pd.DataFrame,
        by: List[str],
        ascending: List[bool] = None
    ) -> pd.DataFrame:
        """排序"""
        if ascending is None:
            ascending = [True] * len(by)
        return df.sort_values(by=by, ascending=ascending)
    
    async def _join(
        self,
        df: pd.DataFrame,
        other: pd.DataFrame,
        on: str,
        how: str = "inner"
    ) -> pd.DataFrame:
        """连接"""
        return df.merge(other, on=on, how=how)
    
    async def _merge(
        self,
        df: pd.DataFrame,
        other: pd.DataFrame,
        left_on: str,
        right_on: str,
        how: str = "inner"
    ) -> pd.DataFrame:
        """合并"""
        return df.merge(other, left_on=left_on, right_on=right_on, how=how)
    
    async def _deduplicate(
        self,
        df: pd.DataFrame,
        subset: List[str] = None,
        keep: str = "first"
    ) -> pd.DataFrame:
        """去重"""
        return df.drop_duplicates(subset=subset, keep=keep)
    
    async def _resample_time(
        self,
        df: pd.DataFrame,
        date_column: str,
        freq: str = "D"
    ) -> pd.DataFrame:
        """时间重采样"""
        df = df.set_index(date_column)
        return df.resample(freq).sum().reset_index()
    
    async def _normalize(
        self,
        df: pd.DataFrame,
        columns: List[str],
        method: str = "minmax"
    ) -> pd.DataFrame:
        """归一化"""
        result = df.copy()
        
        if method == "minmax":
            for col in columns:
                min_val = result[col].min()
                max_val = result[col].max()
                if max_val > min_val:
                    result[col] = (result[col] - min_val) / (max_val - min_val)
        
        elif method == "zscore":
            for col in columns:
                mean_val = result[col].mean()
                std_val = result[col].std()
                if std_val > 0:
                    result[col] = (result[col] - mean_val) / std_val
        
        return result
    
    async def _encode_categorical(
        self,
        df: pd.DataFrame,
        columns: List[str],
        method: str = "onehot"
    ) -> pd.DataFrame:
        """编码分类变量"""
        result = df.copy()
        
        if method == "label":
            for col in columns:
                result[f"{col}_encoded"] = pd.Categorical(result[col]).codes
        
        elif method == "onehot":
            for col in columns:
                dummies = pd.get_dummies(result[col], prefix=col)
                result = pd.concat([result, dummies], axis=1)
        
        return result
    
    async def _create_bins(
        self,
        df: pd.DataFrame,
        column: str,
        bins: int = 5,
        labels: List[str] = None
    ) -> pd.DataFrame:
        """分箱"""
        result = df.copy()
        result[f"{column}_binned"] = pd.cut(
            result[column],
            bins=bins,
            labels=labels
        )
        return result
    
    async def _add_calculated_column(
        self,
        df: pd.DataFrame,
        new_column: str,
        expression: str
    ) -> pd.DataFrame:
        """添加计算列"""
        result = df.copy()
        # 简单表达式解析
        result[new_column] = result.eval(expression)
        return result
    
    async def _extract_date_features(
        self,
        df: pd.DataFrame,
        date_column: str
    ) -> pd.DataFrame:
        """提取日期特征"""
        result = df.copy()
        dates = pd.to_datetime(result[date_column])
        
        result[f"{date_column}_year"] = dates.dt.year
        result[f"{date_column}_month"] = dates.dt.month
        result[f"{date_column}_day"] = dates.dt.day
        result[f"{date_column}_hour"] = dates.dt.hour
        result[f"{date_column}_weekday"] = dates.dt.dayofweek
        result[f"{date_column}_quarter"] = dates.dt.quarter
        result[f"{date_column}_is_weekend"] = dates.dt.dayofweek.isin([5, 6]).astype(int)
        
        return result
    
    def get_available_transformations(self) -> List[str]:
        """获取可用的转换类型"""
        return list(self.transformations.keys())


# 导出
data_transformation_service = DataTransformationService()

__all__ = ['DataTransformationService', 'data_transformation_service']
