#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据推荐服务

基于数据特征和用户需求推荐合适的数据集
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import numpy as np


class DataRecommendationService:
    """智能数据推荐服务"""
    
    def __init__(self):
        logger.info("智能数据推荐服务初始化完成")
    
    async def recommend(
        self,
        query: str,
        datasets: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """推荐合适的数据集
        
        Args:
            query: 用户需求描述
            datasets: 数据集列表
            top_k: 返回数量
            
        Returns:
            推荐结果
        """
        logger.info(f"开始推荐: {query}")
        
        # 1. 解析需求
        requirements = self._parse_requirements(query)
        
        # 2. 评分每个数据集
        scored = []
        for ds in datasets:
            score = self._calculate_score(ds, requirements)
            scored.append({
                **ds,
                "match_score": score,
                "match_reasons": self._get_match_reasons(ds, requirements)
            })
        
        # 3. 排序返回
        scored.sort(key=lambda x: x["match_score"], reverse=True)
        
        return scored[:top_k]
    
    def _parse_requirements(self, query: str) -> Dict[str, Any]:
        """解析用户需求"""
        query_lower = query.lower()
        
        requirements = {
            "industries": [],
            "data_types": [],
            "keywords": [],
            "min_quality": 0,
            "size_preference": None  # small, medium, large
        }
        
        # 行业关键词
        industry_keywords = {
            "半导体": ["semiconductor", "芯片", "晶圆"],
            "制造": ["manufacturing", "生产", "factory"],
            "能源": ["energy", "电力", "power"],
            "金融": ["finance", "金融", "银行"],
            "医疗": ["medical", "医疗", "health"],
            "零售": ["retail", "零售", "销售"],
        }
        
        for industry, keywords in industry_keywords.items():
            if any(kw in query_lower for kw in keywords):
                requirements["industries"].append(industry)
        
        # 数据类型
        if any(kw in query_lower for kw in ["时间序列", "时序", "time series"]):
            requirements["data_types"].append("time_series")
        if any(kw in query_lower for kw in ["日志", "log"]):
            requirements["data_types"].append("log")
        if any(kw in query_lower for kw in ["交易", "交易记录", "transaction"]):
            requirements["data_types"].append("transaction")
        if any(kw in query_lower for kw in ["用户", "user", "客户"]):
            requirements["data_types"].append("user")
        
        # 数据规模
        if any(kw in query_lower for kw in ["小", "少量", "small"]):
            requirements["size_preference"] = "small"
        elif any(kw in query_lower for kw in ["大", "大量", "big", "large"]):
            requirements["size_preference"] = "large"
        
        # 关键词
        requirements["keywords"] = query.split()
        
        return requirements
    
    def _calculate_score(
        self,
        dataset: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> float:
        """计算匹配分数"""
        score = 0.0
        
        # 行业匹配
        dataset_industry = dataset.get("industry", "")
        if dataset_industry in requirements["industries"]:
            score += 30
        
        # 数据类型匹配
        dataset_tags = dataset.get("tags", [])
        for dtype in requirements["data_types"]:
            if any(dtype in str(tag).lower() for tag in dataset_tags):
                score += 20
        
        # 质量分数
        quality = dataset.get("quality_score", 0)
        score += quality * 0.3  # 最高 30 分
        
        # 关键词匹配
        keywords = requirements["keywords"]
        searchable_text = (
            dataset.get("name", "") + " " +
            dataset.get("description", "") + " " +
            " ".join(dataset.get("tags", []))
        ).lower()
        
        for kw in keywords:
            if kw.lower() in searchable_text:
                score += 5
        
        return min(100, score)
    
    def _get_match_reasons(
        self,
        dataset: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> List[str]:
        """获取匹配原因"""
        reasons = []
        
        # 行业匹配
        if dataset.get("industry") in requirements["industries"]:
            reasons.append(f"行业匹配: {dataset.get('industry')}")
        
        # 数据类型匹配
        dataset_tags = dataset.get("tags", [])
        for dtype in requirements["data_types"]:
            if any(dtype in str(tag).lower() for tag in dataset_tags):
                reasons.append(f"数据类型匹配: {dtype}")
        
        # 质量
        quality = dataset.get("quality_score", 0)
        if quality > 80:
            reasons.append(f"数据质量高: {quality:.0f}分")
        
        return reasons


# 导出
data_recommendation_service = DataRecommendationService()

__all__ = ['DataRecommendationService', 'data_recommendation_service']
