#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据可视化服务

生成数据的可视化描述和建议
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import pandas as pd
import numpy as np


class DataVisualizationService:
    """数据可视化服务"""
    
    def __init__(self):
        logger.info("数据可视化服务初始化完成")
    
    async def analyze(
        self,
        dataframe: pd.DataFrame,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """分析数据并生成可视化建议
        
        Args:
            dataframe: 数据框
            sample_size: 采样大小
            
        Returns:
            可视化建议
        """
        logger.info("开始可视化分析")
        
        sample_df = dataframe.head(sample_size) if len(dataframe) > sample_size else dataframe
        
        # 1. 分析数值列
        numeric_visualizations = self._analyze_numeric(sample_df)
        
        # 2. 分析分类列
        categorical_visualizations = self._analyze_categorical(sample_df)
        
        # 3. 分析时间列
        temporal_visualizations = self._analyze_temporal(sample_df)
        
        # 4. 分析关系
        relationship_visualizations = self._analyze_relationships(sample_df)
        
        # 5. 生成推荐
        recommendations = self._generate_recommendations(
            numeric_visualizations,
            categorical_visualizations,
            temporal_visualizations,
            relationship_visualizations
        )
        
        return {
            "numeric_visualizations": numeric_visualizations,
            "categorical_visualizations": categorical_visualizations,
            "temporal_visualizations": temporal_visualizations,
            "relationship_visualizations": relationship_visualizations,
            "recommendations": recommendations,
            "dashboard_layout": self._suggest_dashboard_layout(
                numeric_visualizations,
                categorical_visualizations,
                temporal_visualizations
            )
        }
    
    def _analyze_numeric(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """分析数值列"""
        visualizations = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            stats = df[col].describe()
            
            viz = {
                "column": col,
                "type": "numeric",
                "suggested_chart": "histogram",
                "description": f"数值分布，范围 {stats['min']:.2f} - {stats['max']:.2f}",
                "chart_options": {
                    "type": "histogram",
                    "x": col,
                    "bins": 20
                }
            }
            
            # 根据分布特征建议图表
            if stats['std'] == 0:
                viz["suggested_chart"] = "value_card"
                viz["description"] = f"常量值: {stats['mean']}"
            elif abs(stats['skew']) > 1:
                viz["suggested_chart"] = "box_plot"
                viz["description"] = "存在偏态分布，建议用箱线图查看异常值"
            
            visualizations.append(viz)
        
        return visualizations
    
    def _analyze_categorical(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """分析分类列"""
        visualizations = []
        
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        
        for col in cat_cols:
            unique_count = df[col].nunique()
            top_values = df[col].value_counts().head(5)
            
            if unique_count <= 10:
                # 类别少，建议用饼图或条形图
                viz = {
                    "column": col,
                    "type": "categorical",
                    "suggested_chart": "pie_chart" if unique_count <= 5 else "bar_chart",
                    "description": f"{unique_count} 个类别",
                    "chart_options": {
                        "type": "bar_chart",
                        "x": col,
                        "y": "count"
                    },
                    "top_values": {str(k): int(v) for k, v in top_values.items()}
                }
            else:
                # 类别多，建议用词云或条形图
                viz = {
                    "column": col,
                    "type": "categorical",
                    "suggested_chart": "wordcloud" if unique_count < 100 else "bar_chart",
                    "description": f"{unique_count} 个唯一值",
                    "chart_options": {
                        "type": "bar_chart",
                        "x": col,
                        "y": "count",
                        "limit": 10
                    }
                }
            
            visualizations.append(viz)
        
        return visualizations
    
    def _analyze_temporal(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """分析时间列"""
        visualizations = []
        
        date_cols = df.select_dtypes(include=['datetime64']).columns
        
        for col in date_cols:
            try:
                min_date = df[col].min()
                max_date = df[col].max()
                date_range = (max_date - min_date).days
                
                if date_range <= 1:
                    # 一天内，按小时
                    freq = "hour"
                    suggested = "line_chart"
                elif date_range <= 31:
                    # 一个月内，按天
                    freq = "day"
                    suggested = "line_chart"
                elif date_range <= 365:
                    # 一年内，按月
                    freq = "month"
                    suggested = "line_chart"
                else:
                    # 多年，按年
                    freq = "year"
                    suggested = "line_chart"
                
                viz = {
                    "column": col,
                    "type": "temporal",
                    "suggested_chart": suggested,
                    "description": f"时间范围: {min_date} 至 {max_date} ({date_range} 天)",
                    "chart_options": {
                        "type": "line_chart",
                        "x": col,
                        "y": "count",
                        "freq": freq
                    }
                }
                
                visualizations.append(viz)
            except:
                pass
        
        return visualizations
    
    def _analyze_relationships(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """分析关系"""
        visualizations = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) >= 2:
            # 计算相关性
            corr_matrix = df[numeric_cols].corr()
            
            # 找出高相关性
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr = abs(corr_matrix.iloc[i, j])
                    if corr > 0.5:
                        visualizations.append({
                            "columns": [corr_matrix.columns[i], corr_matrix.columns[j]],
                            "correlation": float(corr_matrix.iloc[i, j]),
                            "suggested_chart": "scatter_plot",
                            "description": f"相关性: {corr_matrix.iloc[i, j]:.2f}"
                        })
        
        return visualizations
    
    def _generate_recommendations(
        self,
        numeric: List,
        categorical: List,
        temporal: List,
        relationships: List
    ) -> List[str]:
        """生成推荐"""
        recommendations = []
        
        # 数值可视化推荐
        if numeric:
            recommendations.append(f"数值列建议使用直方图或箱线图展示分布（共 {len(numeric)} 个）")
        
        # 分类可视化推荐
        if categorical:
            recommendations.append(f"分类列建议使用饼图或条形图展示占比（共 {len(categorical)} 个）")
        
        # 时间可视化推荐
        if temporal:
            recommendations.append("时间序列建议使用折线图展示趋势")
        
        # 关系可视化推荐
        if relationships:
            recommendations.append(f"发现 {len(relationships)} 组高相关列，建议使用散点图")
        
        return recommendations
    
    def _suggest_dashboard_layout(
        self,
        numeric: List,
        categorical: List,
        temporal: List
    ) -> Dict[str, Any]:
        """建议仪表盘布局"""
        layout = {
            "sections": []
        }
        
        # 时间序列区域
        if temporal:
            layout["sections"].append({
                "type": "temporal",
                "title": "时间趋势",
                "charts": [
                    {
                        "type": "line_chart",
                        "columns": [t["column"] for t in temporal[:2]]
                    }
                ]
            })
        
        # 数值分布区域
        if numeric:
            layout["sections"].append({
                "type": "numeric",
                "title": "数值分布",
                "charts": [
                    {
                        "type": "histogram",
                        "columns": [n["column"] for n in numeric[:4]]
                    }
                ]
            })
        
        # 分类统计区域
        if categorical:
            layout["sections"].append({
                "type": "categorical",
                "title": "分类统计",
                "charts": [
                    {
                        "type": "pie_chart",
                        "column": categorical[0]["column"]
                    }
                ]
            })
        
        return layout


# 导出
data_visualization_service = DataVisualizationService()

__all__ = ['DataVisualizationService', 'data_visualization_service']
