#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""智能搜索服务 - 基于结构化字段和LLM排序（增强版）"""

from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from .filter_executor import FilterExecutor


class SmartSearchService:
    """智能搜索服务（增强版）

    使用FilterExecutor应用LLM生成的动态过滤条件
    对于小规模数据（<500个数据集），性能完全够用
    """

    def __init__(self, repository):
        """初始化搜索服务

        Args:
            repository: 数据集仓储（SupabaseDatasetRepository或DatasetRepository）
        """
        self.repository = repository
        self.filter_executor = FilterExecutor()
        logger.info("智能搜索服务初始化完成（增强版）")

    async def search_datasets(
        self,
        filters: Dict[str, Any],
        sort_preference: str = "相关性优先",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """智能搜索数据集

        Args:
            filters: 过滤条件（LLM生成的动态过滤条件）
            sort_preference: 排序偏好（质量优先/相关性优先/最新优先）
            limit: 返回数量

        Returns:
            List[Dict]: 搜索结果
        """
        logger.info(f"智能搜索: filters={filters}, sort={sort_preference}, limit={limit}")

        # 1. 获取所有数据集（对于<500个数据集，全量加载很快）
        all_datasets = await self.repository.list_all()
        logger.info(f"加载数据集: {len(all_datasets)}个")

        # 2. 使用FilterExecutor应用动态过滤（替换硬编码逻辑）
        filtered_datasets = self.filter_executor.apply_filters(all_datasets, filters)

        logger.info(f"过滤结果: {len(filtered_datasets)}/{len(all_datasets)}")

        # 3. 排序
        sorted_datasets = self._sort_datasets(filtered_datasets, sort_preference)

        # 4. 限制返回数量
        results = sorted_datasets[:limit]

        # 5. 转换为响应格式
        formatted_results = self._format_results(results)

        logger.info(f"返回结果: {len(formatted_results)}个")

        return formatted_results

    def _sort_datasets(
        self,
        datasets: List[Any],
        sort_preference: str
    ) -> List[Any]:
        """排序数据集

        Args:
            datasets: 数据集列表
            sort_preference: 排序偏好

        Returns:
            List: 排序后的数据集
        """
        if sort_preference == "质量优先":
            # 按质量分数降序
            return sorted(
                datasets,
                key=lambda d: (
                    d.quality_analysis_results.get("overall_score", 0)
                    if d.quality_analysis_results else 0
                ),
                reverse=True
            )

        elif sort_preference == "最新优先":
            # 按上传时间降序
            return sorted(
                datasets,
                key=lambda d: d.upload_time or datetime.min,
                reverse=True
            )

        else:  # 相关性优先或其他
            # 保持原有顺序（可以后续用LLM重排序）
            return datasets

    def _format_results(self, datasets: List[Any]) -> List[Dict[str, Any]]:
        """格式化搜索结果

        Args:
            datasets: 数据集列表

        Returns:
            List[Dict]: 格式化的结果
        """
        results = []
        for dataset in datasets:
            # 提取质量信息
            quality_score = None
            quality_level = None
            if dataset.quality_analysis_results:
                quality_score = dataset.quality_analysis_results.get("overall_score")
                quality_level = dataset.quality_analysis_results.get("quality_level")

            results.append({
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description or "",
                "tags": dataset.tags or [],
                "industry": dataset.industry,
                "file_size": dataset.file_size,
                "upload_time": dataset.upload_time.isoformat() if dataset.upload_time else None,
                "processing_status": dataset.processing_status,
                # 质量信息
                "quality_score": quality_score,
                "quality_level": quality_level,
                # 相关性分数（占位符，可以后续用LLM计算）
                "relevance_score": 1.0,
            })

        return results
