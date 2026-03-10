#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据理解 API 端点

提供自动数据理解和洞察生成
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loguru import logger
import pandas as pd

from ...core.data_understanding_service import data_understanding_service

router = APIRouter(prefix="/api/v1/understand", tags=["data-understanding"])


class UnderstandRequest(BaseModel):
    dataset_id: str
    sample_size: Optional[int] = 1000


@router.post("/{dataset_id}")
async def understand_dataset(
    dataset_id: str,
    sample_size: int = 1000
) -> Dict[str, Any]:
    """理解数据集
    
    自动分析数据并生成洞察报告
    
    Args:
        dataset_id: 数据集ID
        sample_size: 采样大小
        
    Returns:
        理解报告
    """
    try:
        # 获取数据集文件
        from ...core.file_service import FileService
        file_service = FileService()
        file_path = await file_service.get_dataset_file(dataset_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # 加载数据
        if str(file_path).endswith('.csv'):
            df = pd.read_csv(file_path)
        elif str(file_path).endswith('.parquet'):
            df = pd.read_parquet(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # 分析
        result = await data_understanding_service.understand(df, sample_size)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"理解分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}/insights")
async def get_dataset_insights(
    dataset_id: str,
    sample_size: int = 1000
) -> Dict[str, Any]:
    """获取数据集洞察
    
    Args:
        dataset_id: 数据集ID
        sample_size: 采样大小
        
    Returns:
        洞察列表
    """
    try:
        from ...core.file_service import FileService
        file_service = FileService()
        file_path = await file_service.get_dataset_file(dataset_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        if str(file_path).endswith('.csv'):
            df = pd.read_csv(file_path)
        elif str(file_path).endswith('.parquet'):
            df = pd.read_parquet(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        result = await data_understanding_service.understand(df, sample_size)
        
        return {
            "dataset_id": dataset_id,
            "insights": result.get("insights", []),
            "recommendations": result.get("recommendations", []),
            "summary": result.get("natural_language", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取洞察失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}/summary")
async def get_dataset_summary(dataset_id: str) -> Dict[str, Any]:
    """获取数据集摘要（快速）
    
    Args:
        dataset_id: 数据集ID
        
    Returns:
        摘要信息
    """
    try:
        from ...core.file_service import FileService
        file_service = FileService()
        file_path = await file_service.get_dataset_file(dataset_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        if str(file_path).endswith('.csv'):
            df = pd.read_csv(file_path, nrows=100)
        elif str(file_path).endswith('.parquet'):
            df = pd.read_parquet(file_path, nrows=100)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        return {
            "dataset_id": dataset_id,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "preview": df.head(5).to_dict(orient="records")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
