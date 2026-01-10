#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supabase数据集仓储层
提供与Supabase Database交互的功能，替代本地SQLite + JSON存储
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger

from ..schemas.dataset import DatasetMetadata
from .supabase_client import (
    direct_supabase_query,
    direct_supabase_insert,
    direct_supabase_update,
    direct_supabase_delete,
    get_supabase_service
)


class SupabaseDatasetRepository:
    """Supabase数据集仓储，负责数据持久化到Supabase

    使用Supabase Database存储所有数据：
    - datasets表：存储数据集元数据
    - analysis_results表：存储分析结果（JSONB格式）
    """

    def __init__(self):
        """初始化仓储"""
        self.service = get_supabase_service()

        if not self.service.available:
            logger.error("Supabase服务不可用，仓储初始化失败")
            raise ValueError("Supabase服务不可用")

        # 内存缓存（可选，用于提高性能）
        self._cache: Dict[str, DatasetMetadata] = {}

        logger.info("Supabase数据集仓储初始化完成")

    def _dataset_to_dict(self, dataset: DatasetMetadata) -> Dict[str, Any]:
        """将DatasetMetadata对象转换为字典

        Args:
            dataset: 数据集元数据

        Returns:
            字典格式的数据
        """
        data = {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "file_path": dataset.file_path,
            "file_size": dataset.file_size,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "column_names": dataset.column_names,
            "column_types": dataset.column_types,
            "industry": dataset.industry,
            "tags": dataset.tags or [],
            "processing_status": dataset.processing_status,
            "uploaded_at": dataset.uploaded_at.isoformat() if isinstance(dataset.uploaded_at, datetime) else dataset.uploaded_at,
            "last_modified": dataset.last_modified.isoformat() if isinstance(dataset.last_modified, datetime) else dataset.last_modified,
            "is_duplicate": dataset.is_duplicate,
            "parent_dataset_id": dataset.parent_dataset_id,
            "version_number": dataset.version_number,
            "storage_strategy": dataset.storage_strategy,
            "file_hash": dataset.file_hash,
            "content_hash": dataset.content_hash,
            "compression_info": dataset.compression_info,
            "preview_data": dataset.preview_data,
            "data_source": dataset.data_source,
            "data_quality_score": dataset.data_quality_score,
            "metadata_version": dataset.metadata_version,
            # 分析结果字段
            "device_time_identification": dataset.device_time_identification,
            "business_meaning_analysis": dataset.business_meaning_analysis,
            "control_relationships_analysis": dataset.control_relationships_analysis,
            "basic_analysis": dataset.basic_analysis,
            "detailed_analysis": dataset.detailed_analysis,
            "insights": dataset.insights or [],
            "recommendations": dataset.recommendations,
            "quality_analysis_results": dataset.quality_analysis_results,
            "business_analysis_results": dataset.business_analysis_results
        }

        # 过滤None值
        return {k: v for k, v in data.items() if v is not None}

    def _dict_to_dataset(self, data: Dict[str, Any]) -> DatasetMetadata:
        """将字典转换为DatasetMetadata对象

        Args:
            data: 字典格式的数据

        Returns:
            DatasetMetadata对象
        """
        return DatasetMetadata(**data)

    def save(self, dataset: DatasetMetadata) -> None:
        """保存数据集元数据

        Args:
            dataset: 数据集元数据
        """
        try:
            # 确保业务分析结果被正确构建
            dataset._build_business_analysis_results()

            # 转换为字典
            dataset_dict = self._dataset_to_dict(dataset)

            # 检查是否已存在
            existing = self._get_raw_by_id(dataset.id)

            if existing:
                # 更新现有记录
                result = direct_supabase_update(
                    table="datasets",
                    data=dataset_dict,
                    filters={"id": dataset.id},
                    use_service_key=True
                )
                logger.info(f"数据集已更新: {dataset.id}")
            else:
                # 插入新记录
                result = direct_supabase_insert(
                    table="datasets",
                    data=dataset_dict,
                    use_service_key=True
                )
                logger.info(f"数据集已保存: {dataset.id}")

            # 更新内存缓存
            self._cache[dataset.id] = dataset

        except Exception as e:
            logger.error(f"保存数据集元数据失败: {e}")
            raise

    def _get_raw_by_id(self, dataset_id: str) -> Optional[Dict]:
        """获取原始数据（字典格式）

        Args:
            dataset_id: 数据集ID

        Returns:
            原始数据字典
        """
        try:
            results = direct_supabase_query(
                table="datasets",
                filters={"id": dataset_id},
                limit=1,
                use_service_key=True
            )

            return results[0] if results else None

        except Exception as e:
            logger.error(f"获取数据集原始数据失败: {e}")
            return None

    def get_by_id(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """根据ID获取数据集

        Args:
            dataset_id: 数据集ID

        Returns:
            Optional[DatasetMetadata]: 数据集元数据
        """
        try:
            # 先检查内存缓存
            if dataset_id in self._cache:
                return self._cache[dataset_id]

            # 从数据库获取
            data = self._get_raw_by_id(dataset_id)

            if not data:
                return None

            # 转换为DatasetMetadata对象
            dataset = self._dict_to_dataset(data)

            # 更新缓存
            self._cache[dataset_id] = dataset

            return dataset

        except Exception as e:
            logger.error(f"获取数据集失败: {e}")
            return None

    def list_all(self) -> List[DatasetMetadata]:
        """获取所有数据集

        Returns:
            List[DatasetMetadata]: 数据集列表
        """
        try:
            results = direct_supabase_query(
                table="datasets",
                order_by="uploaded_at",
                order_desc=True,
                limit=1000,
                use_service_key=True
            )

            return [self._dict_to_dataset(data) for data in results]

        except Exception as e:
            logger.error(f"列出数据集失败: {e}")
            return []

    def list_with_filters(
        self,
        limit: int = 100,
        offset: int = 0,
        industry: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[DatasetMetadata]:
        """带筛选条件的数据集列表

        Args:
            limit: 限制数量
            offset: 偏移量
            industry: 行业筛选
            tags: 标签筛选

        Returns:
            List[DatasetMetadata]: 数据集列表
        """
        try:
            filters = {}
            or_filters = None

            if industry:
                filters["industry"] = industry

            if tags:
                # Supabase Postgres支持数组操作
                or_filters = ",".join([f"tags.cs.{tag}" for tag in tags])

            results = direct_supabase_query(
                table="datasets",
                filters=filters if filters else None,
                or_filters=or_filters,
                order_by="uploaded_at",
                order_desc=True,
                limit=limit,
                offset=offset,
                use_service_key=True
            )

            return [self._dict_to_dataset(data) for data in results]

        except Exception as e:
            logger.error(f"筛选数据集失败: {e}")
            return []

    def delete(self, dataset_id: str) -> bool:
        """删除数据集

        Args:
            dataset_id: 数据集ID

        Returns:
            bool: 是否删除成功
        """
        try:
            success = direct_supabase_delete(
                table="datasets",
                filters={"id": dataset_id},
                use_service_key=True
            )

            # 从缓存中移除
            if dataset_id in self._cache:
                del self._cache[dataset_id]

            if success:
                logger.info(f"数据集删除成功: {dataset_id}")

            return success

        except Exception as e:
            logger.error(f"删除数据集失败: {e}")
            return False

    def exists(self, dataset_id: str) -> bool:
        """检查数据集是否存在

        Args:
            dataset_id: 数据集ID

        Returns:
            bool: 是否存在
        """
        try:
            # 检查缓存
            if dataset_id in self._cache:
                return True

            # 检查数据库
            data = self._get_raw_by_id(dataset_id)
            return data is not None

        except Exception as e:
            logger.error(f"检查数据集存在性失败: {e}")
            return False

    def update_status(self, dataset_id: str, status: str) -> None:
        """更新数据集状态

        Args:
            dataset_id: 数据集ID
            status: 新状态
        """
        try:
            # 更新缓存
            if dataset_id in self._cache:
                self._cache[dataset_id].processing_status = status
                self.save(self._cache[dataset_id])
            else:
                # 从数据库加载，更新状态，再保存
                dataset = self.get_by_id(dataset_id)
                if dataset:
                    dataset.processing_status = status
                    self.save(dataset)

        except Exception as e:
            logger.error(f"更新数据集状态失败: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取仓储统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            all_datasets = self.list_all()

            total_count = len(all_datasets)
            total_size = sum(d.file_size or 0 for d in all_datasets)

            status_counts = {}
            for dataset in all_datasets:
                status = dataset.processing_status or "unknown"
                status_counts[status] = status_counts.get(status, 0) + 1

            return {
                "total_datasets": total_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "status_counts": status_counts,
                "storage_strategy": "supabase_database",
                "cache_size": len(self._cache)
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def clear_cache(self) -> None:
        """清空内存缓存"""
        self._cache.clear()
        logger.info("内存缓存已清空")

    def save_business_analysis_results(self, dataset_id: str, business_results: Dict) -> None:
        """保存业务分析结果

        注意：在Supabase中，分析结果直接存储在datasets表的JSONB字段中

        Args:
            dataset_id: 数据集ID
            business_results: 业务分析结果
        """
        try:
            dataset = self.get_by_id(dataset_id)
            if dataset:
                dataset.business_analysis_results = business_results
                dataset._build_business_analysis_results()
                self.save(dataset)
                logger.info(f"业务分析结果已保存: {dataset_id}")

        except Exception as e:
            logger.error(f"保存业务分析结果失败: {e}")
            raise

    def save_quality_analysis_results(self, dataset_id: str, quality_results: Dict) -> None:
        """保存质量分析结果

        注意：在Supabase中，分析结果直接存储在datasets表的JSONB字段中

        Args:
            dataset_id: 数据集ID
            quality_results: 质量分析结果
        """
        try:
            dataset = self.get_by_id(dataset_id)
            if dataset:
                dataset.quality_analysis_results = quality_results
                self.save(dataset)
                logger.info(f"质量分析结果已保存: {dataset_id}")

        except Exception as e:
            logger.error(f"保存质量分析结果失败: {e}")
            raise

    def get_business_analysis_results(self, dataset_id: str) -> Optional[Dict]:
        """获取业务分析结果

        Args:
            dataset_id: 数据集ID

        Returns:
            Optional[Dict]: 业务分析结果
        """
        try:
            dataset = self.get_by_id(dataset_id)
            if dataset:
                return dataset.business_analysis_results
            return None

        except Exception as e:
            logger.error(f"获取业务分析结果失败: {e}")
            return None

    def get_quality_analysis_results(self, dataset_id: str) -> Optional[Dict]:
        """获取质量分析结果

        Args:
            dataset_id: 数据集ID

        Returns:
            Optional[Dict]: 质量分析结果
        """
        try:
            dataset = self.get_by_id(dataset_id)
            if dataset:
                return dataset.quality_analysis_results
            return None

        except Exception as e:
            logger.error(f"获取质量分析结果失败: {e}")
            return None

    def get_analysis_results(self, dataset_id: str) -> List[Dict[str, Any]]:
        """获取数据集的分析结果列表

        为了兼容性，此方法返回一个统一格式的列表

        Args:
            dataset_id: 数据集ID

        Returns:
            List[Dict[str, Any]]: 分析结果列表
        """
        try:
            dataset = self.get_by_id(dataset_id)
            if not dataset:
                return []

            results = []

            # 业务分析结果
            if dataset.business_analysis_results:
                results.append({
                    "dataset_id": dataset_id,
                    "analysis_type": "business_analysis",
                    "results": dataset.business_analysis_results,
                    "created_at": dataset.last_modified.isoformat() if dataset.last_modified else datetime.now().isoformat()
                })

            # 质量分析结果
            if dataset.quality_analysis_results:
                results.append({
                    "dataset_id": dataset_id,
                    "analysis_type": "quality_analysis",
                    "results": dataset.quality_analysis_results,
                    "created_at": dataset.last_modified.isoformat() if dataset.last_modified else datetime.now().isoformat()
                })

            return results

        except Exception as e:
            logger.error(f"获取分析结果列表失败: {e}")
            return []
