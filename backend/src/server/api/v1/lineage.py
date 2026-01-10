#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据血缘关系API路由

提供数据集血缘关系管理的API端点:
1. 建立血缘关系
2. 查询血缘链
3. 获取可视化数据
4. 删除血缘关系
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from loguru import logger

from src.schemas.dataset import DataLineageUpdateRequest
from src.core.lineage_manager import DataLineageManager


router = APIRouter(prefix="/lineage", tags=["数据血缘关系"])
lineage_manager = DataLineageManager()


@router.post("/establish", response_model=Dict[str, Any])
async def establish_lineage_relationship(request: DataLineageUpdateRequest):
    """建立数据血缘关系

    Args:
        request: 血缘关系更新请求

    Returns:
        Dict: 操作结果
    """
    try:
        logger.info(
            f"建立血缘关系请求: {request.dataset_id} <- {request.source_dataset_ids}"
        )

        result = lineage_manager.establish_lineage_relationship(
            dataset_id=request.dataset_id,
            source_dataset_ids=request.source_dataset_ids,
            transformation_type=request.transformation_type,
            transformation_description=request.transformation_description
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"建立血缘关系API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chain/{dataset_id}", response_model=Dict[str, Any])
async def get_lineage_chain(dataset_id: str):
    """获取数据集血缘链

    Args:
        dataset_id: 数据集ID

    Returns:
        Dict: 血缘链信息，包括上游和下游
    """
    try:
        logger.info(f"查询血缘链请求: {dataset_id}")

        lineage_chain = lineage_manager.get_lineage_chain(dataset_id)

        if "error" in lineage_chain:
            raise HTTPException(status_code=404, detail=lineage_chain["error"])

        return lineage_chain

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询血缘链API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualization/{dataset_id}", response_model=Dict[str, Any])
async def get_lineage_visualization(dataset_id: str):
    """获取血缘关系可视化数据

    Args:
        dataset_id: 数据集ID

    Returns:
        Dict: 可视化数据（节点和边）
    """
    try:
        logger.info(f"获取血缘可视化数据请求: {dataset_id}")

        viz_data = lineage_manager.get_lineage_visualization_data(dataset_id)

        if "error" in viz_data:
            raise HTTPException(status_code=404, detail=viz_data["error"])

        return viz_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取血缘可视化数据API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{dataset_id}", response_model=Dict[str, Any])
async def delete_lineage_relationship(dataset_id: str):
    """删除数据血缘关系

    Args:
        dataset_id: 数据集ID

    Returns:
        Dict: 操作结果
    """
    try:
        logger.info(f"删除血缘关系请求: {dataset_id}")

        result = lineage_manager.delete_lineage_relationship(dataset_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除血缘关系API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upstream/{dataset_id}", response_model=Dict[str, Any])
async def get_upstream_datasets(dataset_id: str, max_depth: int = 5):
    """获取上游数据集

    Args:
        dataset_id: 数据集ID
        max_depth: 最大追溯深度

    Returns:
        Dict: 上游数据集列表
    """
    try:
        logger.info(f"查询上游数据集请求: {dataset_id}, 深度: {max_depth}")

        # 使用lineage_manager的内部方法
        from src.core.lineage_manager import DataLineageManager
        manager = DataLineageManager()

        upstream = manager._trace_upstream(dataset_id, max_depth=max_depth)

        return {
            "dataset_id": dataset_id,
            "upstream_count": len(upstream),
            "upstream_datasets": upstream
        }

    except Exception as e:
        logger.error(f"查询上游数据集API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/downstream/{dataset_id}", response_model=Dict[str, Any])
async def get_downstream_datasets(dataset_id: str, max_depth: int = 5):
    """获取下游派生数据集

    Args:
        dataset_id: 数据集ID
        max_depth: 最大追溯深度

    Returns:
        Dict: 下游数据集列表
    """
    try:
        logger.info(f"查询下游数据集请求: {dataset_id}, 深度: {max_depth}")

        # 使用lineage_manager的内部方法
        from src.core.lineage_manager import DataLineageManager
        manager = DataLineageManager()

        downstream = manager._trace_downstream(dataset_id, max_depth=max_depth)

        return {
            "dataset_id": dataset_id,
            "downstream_count": len(downstream),
            "downstream_datasets": downstream
        }

    except Exception as e:
        logger.error(f"查询下游数据集API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
