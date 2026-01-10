#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据血缘关系管理模块

提供数据集血缘关系的管理功能:
1. 建立数据集间的派生关系
2. 记录数据转换过程
3. 查询血缘关系（上游/下游）
4. 可视化血缘链
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger
from datetime import datetime

from ..schemas.dataset import DatasetMetadata, DataLineageUpdateRequest
from ..config.settings import get_settings
from .database_repository import DatabaseRepository


class DataLineageManager:
    """数据血缘关系管理器"""

    def __init__(self):
        """初始化血缘关系管理器"""
        settings = get_settings()
        db_path = settings.metadata_dir / "datasets.db"
        self.db = DatabaseRepository(db_path)
        logger.info("数据血缘关系管理器初始化完成")

    def establish_lineage_relationship(
        self,
        dataset_id: str,
        source_dataset_ids: List[str],
        transformation_type: str,
        transformation_description: str
    ) -> Dict[str, Any]:
        """建立血缘关系

        Args:
            dataset_id: 目标数据集ID（派生数据）
            source_dataset_ids: 源数据集ID列表
            transformation_type: 转换类型
            transformation_description: 转换描述

        Returns:
            Dict: 操作结果
        """
        try:
            logger.info(f"开始建立血缘关系: {dataset_id} <- {source_dataset_ids}")

            # 获取目标数据集
            target_dataset = self.db.get_dataset_by_id(dataset_id)
            if not target_dataset:
                raise ValueError(f"目标数据集不存在: {dataset_id}")

            # 验证源数据集存在
            for source_id in source_dataset_ids:
                source_dataset = self.db.get_dataset_by_id(source_id)
                if not source_dataset:
                    logger.warning(f"源数据集不存在: {source_id}")
                    raise ValueError(f"源数据集不存在: {source_id}")

            # 更新目标数据集的血缘信息
            target_dataset.source_dataset_ids = source_dataset_ids
            target_dataset.transformation_type = transformation_type
            target_dataset.transformation_description = transformation_description
            target_dataset.is_derived_data = True

            # 保存到数据库
            self.db.update_dataset(dataset_id, target_dataset)

            logger.info(f"血缘关系建立成功: {dataset_id} 派生自 {len(source_dataset_ids)} 个数据集")

            return {
                "success": True,
                "message": "血缘关系建立成功",
                "lineage_info": {
                    "target_dataset": dataset_id,
                    "source_datasets": source_dataset_ids,
                    "transformation_type": transformation_type,
                    "created_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"建立血缘关系失败: {e}")
            return {
                "success": False,
                "message": f"建立血缘关系失败: {e}",
                "lineage_info": None
            }

    def get_lineage_chain(self, dataset_id: str) -> Dict[str, Any]:
        """获取完整血缘链

        Args:
            dataset_id: 数据集ID

        Returns:
            Dict: 血缘链信息，包括上游和下游
        """
        try:
            logger.info(f"查询血缘链: {dataset_id}")

            # 获取当前数据集
            current_dataset = self.db.get_dataset_by_id(dataset_id)
            if not current_dataset:
                raise ValueError(f"数据集不存在: {dataset_id}")

            # 构建血缘链
            lineage_chain = {
                "current_dataset": {
                    "id": current_dataset.id,
                    "name": current_dataset.name,
                    "is_derived": current_dataset.is_derived_data,
                    "transformation_type": current_dataset.transformation_type,
                    "transformation_description": current_dataset.transformation_description
                },
                "upstream": self._trace_upstream(dataset_id, max_depth=5),
                "downstream": self._trace_downstream(dataset_id, max_depth=5),
                "generated_at": datetime.now().isoformat()
            }

            return lineage_chain

        except Exception as e:
            logger.error(f"查询血缘链失败: {e}")
            return {
                "error": str(e),
                "upstream": [],
                "downstream": []
            }

    def _trace_upstream(
        self,
        dataset_id: str,
        visited: Optional[set] = None,
        max_depth: int = 5,
        current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """追溯上游数据源

        Args:
            dataset_id: 当前数据集ID
            visited: 已访问的数据集ID集合
            max_depth: 最大追溯深度
            current_depth: 当前深度

        Returns:
            List[Dict]: 上游数据集列表
        """
        if visited is None:
            visited = set()

        if current_depth >= max_depth or dataset_id in visited:
            return []

        visited.add(dataset_id)
        upstream_results = []

        try:
            dataset = self.db.get_dataset_by_id(dataset_id)
            if not dataset or not dataset.source_dataset_ids:
                return upstream_results

            for source_id in dataset.source_dataset_ids:
                source_dataset = self.db.get_dataset_by_id(source_id)
                if source_dataset:
                    node_info = {
                        "id": source_dataset.id,
                        "name": source_dataset.name,
                        "depth": current_depth + 1,
                        "transformation": dataset.transformation_type,
                        "transformation_description": dataset.transformation_description
                    }
                    upstream_results.append(node_info)

                    # 递归追溯
                    upstream_results.extend(
                        self._trace_upstream(
                            source_id,
                            visited,
                            max_depth,
                            current_depth + 1
                        )
                    )

        except Exception as e:
            logger.error(f"追溯上游失败: {e}")

        return upstream_results

    def _trace_downstream(
        self,
        dataset_id: str,
        visited: Optional[set] = None,
        max_depth: int = 5,
        current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """追溯下游派生数据

        Args:
            dataset_id: 当前数据集ID
            visited: 已访问的数据集ID集合
            max_depth: 最大追溯深度
            current_depth: 当前深度

        Returns:
            List[Dict]: 下游数据集列表
        """
        if visited is None:
            visited = set()

        if current_depth >= max_depth or dataset_id in visited:
            return []

        visited.add(dataset_id)
        downstream_results = []

        try:
            # 查询所有将当前数据集作为源的数据集
            all_datasets = self.db.list_datasets()

            for dataset in all_datasets:
                if dataset.source_dataset_ids and dataset_id in dataset.source_dataset_ids:
                    node_info = {
                        "id": dataset.id,
                        "name": dataset.name,
                        "depth": current_depth + 1,
                        "transformation": dataset.transformation_type,
                        "transformation_description": dataset.transformation_description
                    }
                    downstream_results.append(node_info)

                    # 递归追溯
                    downstream_results.extend(
                        self._trace_downstream(
                            dataset.id,
                            visited,
                            max_depth,
                            current_depth + 1
                        )
                    )

        except Exception as e:
            logger.error(f"追溯下游失败: {e}")

        return downstream_results

    def get_lineage_visualization_data(self, dataset_id: str) -> Dict[str, Any]:
        """获取血缘关系可视化数据

        Args:
            dataset_id: 数据集ID

        Returns:
            Dict: 可视化数据（节点和边）
        """
        try:
            lineage_chain = self.get_lineage_chain(dataset_id)

            nodes = []
            edges = []
            node_set = set()

            # 添加当前节点
            current = lineage_chain["current_dataset"]
            nodes.append({
                "id": current["id"],
                "label": current["name"],
                "type": "current",
                "is_derived": current["is_derived"]
            })
            node_set.add(current["id"])

            # 添加上游节点
            for upstream in lineage_chain["upstream"]:
                if upstream["id"] not in node_set:
                    nodes.append({
                        "id": upstream["id"],
                        "label": upstream["name"],
                        "type": "source",
                        "depth": upstream["depth"]
                    })
                    node_set.add(upstream["id"])

            # 添加下游节点
            for downstream in lineage_chain["downstream"]:
                if downstream["id"] not in node_set:
                    nodes.append({
                        "id": downstream["id"],
                        "label": downstream["name"],
                        "type": "derived",
                        "depth": downstream["depth"]
                    })
                    node_set.add(downstream["id"])

            # 构建边（关系）
            # 这里需要根据血缘关系重建边的连接
            # 简化处理：直接连接当前节点与上下游
            for upstream in lineage_chain["upstream"]:
                edges.append({
                    "from": upstream["id"],
                    "to": current["id"],
                    "label": upstream["transformation"],
                    "type": "derivation"
                })

            for downstream in lineage_chain["downstream"]:
                edges.append({
                    "from": current["id"],
                    "to": downstream["id"],
                    "label": downstream["transformation"],
                    "type": "derivation"
                })

            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "generated_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"生成可视化数据失败: {e}")
            return {
                "nodes": [],
                "edges": [],
                "error": str(e)
            }

    def delete_lineage_relationship(self, dataset_id: str) -> Dict[str, Any]:
        """删除血缘关系

        Args:
            dataset_id: 数据集ID

        Returns:
            Dict: 操作结果
        """
        try:
            dataset = self.db.get_dataset_by_id(dataset_id)
            if not dataset:
                raise ValueError(f"数据集不存在: {dataset_id}")

            # 清除血缘信息
            dataset.source_dataset_ids = []
            dataset.transformation_type = None
            dataset.transformation_description = None
            dataset.is_derived_data = False

            # 保存到数据库
            self.db.update_dataset(dataset_id, dataset)

            logger.info(f"血缘关系已删除: {dataset_id}")

            return {
                "success": True,
                "message": "血缘关系删除成功"
            }

        except Exception as e:
            logger.error(f"删除血缘关系失败: {e}")
            return {
                "success": False,
                "message": f"删除血缘关系失败: {e}"
            }
