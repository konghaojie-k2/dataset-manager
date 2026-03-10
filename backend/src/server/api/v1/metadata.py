#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强元数据 API 端点

提供 Agent 可查询的增强语义元数据接口
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from loguru import logger

from ...core.enhanced_metadata_service import enhanced_metadata_service
from ...core.dataset_repository import DatasetRepository

router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])


class EnhancedMetadataRequest(BaseModel):
    dataset_id: str
    sample_size: Optional[int] = 1000


class DatasetSchemaRequest(BaseModel):
    dataset_id: str
    include_semantics: Optional[bool] = True


class NaturalLanguageQueryRequest(BaseModel):
    dataset_id: str
    question: str
    include_preview: Optional[bool] = True


@router.post("/analyze")
async def analyze_dataset_metadata(request: EnhancedMetadataRequest) -> Dict[str, Any]:
    """分析数据集，生成增强语义元数据
    
    Args:
        dataset_id: 数据集ID
        sample_size: 采样大小
        
    Returns:
        增强语义元数据
    """
    try:
        # 获取数据集
        dataset_repo = DatasetRepository()
        dataset = await dataset_repo.get_by_id(request.dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # 获取数据文件
        from ...core.file_service import FileService
        file_service = FileService()
        file_path = await file_service.get_dataset_file(request.dataset_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # 加载数据
        import pandas as pd
        if str(file_path).endswith('.csv'):
            df = pd.read_csv(file_path)
        elif str(file_path).endswith('.parquet'):
            df = pd.read_parquet(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # 分析
        result = await enhanced_metadata_service.analyze_dataset(
            dataset_id=request.dataset_id,
            dataframe=df,
            sample_size=request.sample_size
        )
        
        return result
        
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/{dataset_id}")
async def get_dataset_schema(
    dataset_id: str,
    include_semantics: bool = True
) -> Dict[str, Any]:
    """获取数据集结构信息
    
    Args:
        dataset_id: 数据集ID
        include_semantics: 是否包含语义信息
        
    Returns:
        数据集结构
    """
    try:
        # 获取数据集
        dataset_repo = DatasetRepository()
        dataset = await dataset_repo.get_by_id(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # 构建结构信息
        schema = {
            "dataset_id": dataset_id,
            "name": dataset.name,
            "description": dataset.description,
            "columns": []
        }
        
        # 添加列信息
        if dataset.columns:
            for col in dataset.columns:
                col_info = {
                    "name": col.name,
                    "data_type": col.data_type,
                    "business_meaning": col.business_meaning,
                    "is_device_id": col.is_device_id,
                    "is_timestamp": col.is_timestamp,
                    "null_count": col.null_count,
                    "unique_count": col.unique_count
                }
                schema["columns"].append(col_info)
        
        # 如果需要语义信息，进行分析
        if include_semantics:
            from ...core.file_service import FileService
            file_service = FileService()
            file_path = await file_service.get_dataset_file(dataset_id)
            
            if file_path:
                import pandas as pd
                try:
                    if str(file_path).endswith('.csv'):
                        df = pd.read_csv(file_path, nrows=1000)
                    elif str(file_path).endswith('.parquet'):
                        df = pd.read_parquet(file_path)
                    
                    # 分析语义
                    semantics = enhanced_metadata_service._analyze_column_semantics(df)
                    schema["column_semantics"] = semantics
                    schema["key_fields"] = enhanced_metadata_service._extract_key_fields(semantics)
                except Exception as e:
                    logger.warning(f"语义分析失败: {e}")
        
        return schema
        
    except Exception as e:
        logger.error(f"获取结构失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/{dataset_id}")
async def get_dataset_quality(dataset_id: str) -> Dict[str, Any]:
    """获取数据集质量评分
    
    Args:
        dataset_id: 数据集ID
        
    Returns:
        质量评分详情
    """
    try:
        # 获取数据集
        dataset_repo = DatasetRepository()
        dataset = await dataset_repo.get_by_id(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # 如果有质量指标，直接返回
        if dataset.quality_metrics:
            return {
                "dataset_id": dataset_id,
                "quality_score": {
                    "overall_score": dataset.quality_metrics.quality_score,
                    "completeness": dataset.quality_metrics.data_completeness * 100,
                    "uniqueness": (1 - dataset.quality_metrics.duplicate_rows / max(1, dataset.quality_metrics.total_rows)) * 100,
                    "issues": dataset.quality_metrics.quality_issues,
                    "recommendations": dataset.quality_metrics.recommendations
                }
            }
        
        # 否则进行实时分析
        from ...core.file_service import FileService
        file_service = FileService()
        file_path = await file_service.get_dataset_file(dataset_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        import pandas as pd
        if str(file_path).endswith('.csv'):
            df = pd.read_csv(file_path)
        elif str(file_path).endswith('.parquet'):
            df = pd.read_parquet(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        quality = enhanced_metadata_service._calculate_quality_score(df)
        
        return {
            "dataset_id": dataset_id,
            "quality_score": quality
        }
        
    except Exception as e:
        logger.error(f"获取质量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_datasets(
    q: Optional[str] = None,
    tags: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """语义搜索数据集
    
    Args:
        q: 搜索关键词
        tags: 标签（逗号分隔）
        industry: 行业
        limit: 返回数量
        
    Returns:
        搜索结果
    """
    try:
        dataset_repo = DatasetRepository()
        
        # 构建查询条件
        filters = {}
        if q:
            filters["search"] = q
        if tags:
            filters["tags"] = tags.split(",")
        if industry:
            filters["industry"] = industry
        
        # 搜索
        results = await dataset_repo.search(filters, limit=limit)
        
        return {
            "query": q,
            "total": len(results),
            "results": [
                {
                    "id": ds.id,
                    "name": ds.name,
                    "description": ds.description,
                    "tags": ds.tags,
                    "industry": ds.industry,
                    "quality_score": ds.quality_metrics.quality_score if ds.quality_metrics else None
                }
                for ds in results
            ]
        }
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_with_nl(request: NaturalLanguageQueryRequest) -> Dict[str, Any]:
    """自然语言查询
    
    Args:
        dataset_id: 数据集ID
        question: 自然语言问题
        include_preview: 是否包含数据预览
        
    Returns:
        查询结果
    """
    try:
        # 1. 获取数据集结构
        schema = await get_dataset_schema(request.dataset_id, include_semantics=True)
        
        # 2. 获取数据样本
        from ...core.file_service import FileService
        file_service = FileService()
        file_path = await file_service.get_dataset_file(request.dataset_id)
        
        sample_data = None
        if file_path and request.include_preview:
            import pandas as pd
            try:
                if str(file_path).endswith('.csv'):
                    sample_data = pd.read_csv(file_path, nrows=10).to_dict(orient="records")
                elif str(file_path).endswith('.parquet'):
                    sample_data = pd.read_parquet(file_path, nrows=10).to_dict(orient="records")
            except Exception as e:
                logger.warning(f"读取样本失败: {e}")
        
        # 3. 使用 LLM 生成回答
        from ...core.nl_query_service import natural_language_query_service
        
        result = await natural_language_query_service.query(
            dataset_id=request.dataset_id,
            question=request.question,
            schema_info=schema,
            sample_data=sample_data
        )
        
        return {
            "question": request.question,
            "answer": result.get("answer", "无法回答该问题"),
            "schema": schema,
            "data_preview": sample_data[:3] if sample_data else None
        }
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
