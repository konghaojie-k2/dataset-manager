#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""安全过滤执行器 - 执行LLM生成的过滤条件"""

from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime


class FilterExecutor:
    """安全过滤执行器

    安全地执行LLM生成的过滤条件，防止代码注入
    """

    # 允许的操作符白名单
    ALLOWED_OPERATORS = {"$gte", "$lte", "$gt", "$lt", "$in", "$nin", "$exists", "$ne", "$eq", "$regex", "$options"}

    def __init__(self):
        logger.info("安全过滤执行器初始化完成")

    def apply_filters(self, datasets: List[Any], filters: Dict[str, Any], use_or_logic: bool = True) -> List[Any]:
        """应用过滤条件到数据集列表

        Args:
            datasets: 数据集列表（DatasetMetadata对象）
            filters: LLM生成的过滤条件
                例: {
                    "industry": "semiconductor",
                    "file_size": {"$gte": 1000},
                    "tags": {"$in": ["传感器", "sensor"]}
                }
            use_or_logic: 是否使用 OR 逻辑（默认 True）
                - True: 只要任一条件满足即可（适用于行业/标签等语义相关字段）
                - False: 所有条件都必须满足（严格模式）

        Returns:
            List: 过滤后的数据集列表
        """
        logger.info(f"应用过滤条件: {len(filters)}个条件, {len(datasets)}个数据集, OR逻辑={use_or_logic}")

        if not filters:
            return datasets

        filtered = []
        for dataset in datasets:
            try:
                if use_or_logic:
                    # OR 逻辑：任一条件满足即可
                    if self._matches_filters_or(dataset, filters):
                        filtered.append(dataset)
                else:
                    # AND 逻辑：所有条件都必须满足
                    if self._matches_filters(dataset, filters):
                        filtered.append(dataset)
            except Exception as e:
                logger.warning(f"过滤数据集 {dataset.id} 时出错: {e}")
                continue

        logger.info(f"过滤结果: {len(filtered)}/{len(datasets)}个数据集")
        return filtered

    def _matches_filters(self, dataset: Any, filters: Dict[str, Any]) -> bool:
        """检查单个数据集是否匹配所有过滤条件（AND 逻辑）

        Args:
            dataset: 数据集对象（DatasetMetadata）
            filters: 过滤条件

        Returns:
            bool: 是否匹配（所有条件都必须满足）
        """
        logger.debug(f"检查数据集（AND）: {dataset.name} (ID: {dataset.id})")

        for field_path, condition in filters.items():
            # 处理特殊字段
            if field_path == "columns.count":
                value = len(dataset.columns) if dataset.columns else 0
            else:
                value = self._get_nested_value(dataset, field_path)

            # 调试日志：显示每个字段的值和条件
            logger.debug(f"  字段: {field_path}, 值: {value}, 条件: {condition}")

            if not self._evaluate_condition(value, condition):
                logger.debug(f"  ❌ 不匹配: {field_path}")
                return False

        logger.debug(f"  ✅ 匹配成功: {dataset.name}")
        return True

    def _matches_filters_or(self, dataset: Any, filters: Dict[str, Any]) -> bool:
        """检查单个数据集是否匹配任一过滤条件（OR 逻辑）

        Args:
            dataset: 数据集对象（DatasetMetadata）
            filters: 过滤条件

        Returns:
            bool: 是否匹配（任一条件满足即可）
        """
        logger.debug(f"检查数据集（OR）: {dataset.name} (ID: {dataset.id})")

        matched = False
        for field_path, condition in filters.items():
            # 处理特殊字段
            if field_path == "columns.count":
                value = len(dataset.columns) if dataset.columns else 0
            else:
                value = self._get_nested_value(dataset, field_path)

            # 调试日志：显示每个字段的值和条件
            logger.debug(f"  字段: {field_path}, 值: {value}, 条件: {condition}")

            if self._evaluate_condition(value, condition):
                logger.debug(f"  ✅ 匹配: {field_path}")
                matched = True
            else:
                logger.debug(f"  ❌ 不匹配: {field_path}")

        if matched:
            logger.debug(f"  ✅ 数据集匹配成功: {dataset.name}")
        else:
            logger.debug(f"  ❌ 数据集不匹配: {dataset.name}")

        return matched

    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """安全获取嵌套属性值

        Args:
            obj: 对象（DatasetMetadata或Dict）
            path: 字段路径，例: "quality_analysis_results.overall_score"

        Returns:
            Any: 字段值，如果不存在返回None

        Example:
            >>> _get_nested_value(dataset, "industry")
            "semiconductor"
            >>> _get_nested_value(dataset, "quality_analysis_results.overall_score")
            85.5
        """
        keys = path.split(".")
        value = obj

        for key in keys:
            if value is None:
                return None

            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = getattr(value, key, None)

            if value is None:
                return None

        return value

    def _evaluate_condition(self, value: Any, condition: Any) -> bool:
        """评估条件是否满足

        Args:
            value: 字段实际值
            condition: 条件（可以是简单值或操作符表达式）

        Returns:
            bool: 是否满足条件

        Examples:
            >>> _evaluate_condition("semiconductor", "semiconductor")  # 简单匹配
            True
            >>> _evaluate_condition(1000, {"$gte": 500})  # 大于等于
            True
            >>> _evaluate_condition(["传感器", "sensor"], {"$in": ["传感器"]})  # 包含
            True
            >>> _evaluate_condition("Temperature", {"$regex": "temp", "$options": "i"})  # 正则匹配
            True
        """
        import re

        # 简单值匹配
        if not isinstance(condition, dict):
            return value == condition

        # 操作符匹配
        # 首先提取 $regex 和 $options（它们需要一起处理）
        regex_pattern = None
        regex_options = ""
        other_conditions = {}

        for op, cond_value in condition.items():
            if op == "$regex":
                regex_pattern = cond_value
            elif op == "$options":
                regex_options = cond_value
            else:
                other_conditions[op] = cond_value

        # 处理正则表达式匹配
        if regex_pattern is not None:
            if value is None or not isinstance(value, str):
                return False

            try:
                flags = 0
                if "i" in regex_options:
                    flags |= re.IGNORECASE

                if not re.search(regex_pattern, value, flags):
                    return False
            except re.error as e:
                logger.error(f"正则表达式错误: {e}, pattern: {regex_pattern}")
                return False

        # 处理其他操作符
        for op, cond_value in other_conditions.items():
            if op not in self.ALLOWED_OPERATORS:
                logger.error(f"不允许的操作符: {op}")
                return False

            if op == "$gte":  # 大于等于
                if value is None or not (value >= cond_value):
                    return False
            elif op == "$lte":  # 小于等于
                if value is None or not (value <= cond_value):
                    return False
            elif op == "$gt":  # 大于
                if value is None or not (value > cond_value):
                    return False
            elif op == "$lt":  # 小于
                if value is None or not (value < cond_value):
                    return False
            elif op == "$in":  # 包含于列表
                # 如果 value 是列表，检查是否有任一元素在 cond_value 中
                if isinstance(value, list):
                    if not any(item in cond_value for item in value):
                        return False
                else:
                    if value not in cond_value:
                        return False
            elif op == "$nin":  # 不包含于列表
                # 如果 value 是列表，检查是否所有元素都不在 cond_value 中
                if isinstance(value, list):
                    if any(item in cond_value for item in value):
                        return False
                else:
                    if value in cond_value:
                        return False
            elif op == "$exists":  # 字段存在
                if value is None:
                    return False
            elif op == "$ne":  # 不等于
                if value == cond_value:
                    return False
            elif op == "$eq":  # 等于
                if value != cond_value:
                    return False

        return True
