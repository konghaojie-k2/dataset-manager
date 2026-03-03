#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引擎选择器"""

from pathlib import Path
from typing import Literal, Optional, Dict, Any
from loguru import logger


class EngineType:
    """引擎类型"""
    PANDAS = "pandas"
    DASK = "dask"
    POLARS = "polars"
    AUTO = "auto"  # 自动选择


class EngineSelector:
    """引擎选择器
    
    根据文件大小自动选择最佳的数据处理引擎。
    默认策略：
    - 小数据集 (<100MB): Pandas（全量加载）
    - 中等数据集 (100MB-1GB): Dask（并行处理）
    - 大数据集 (>1GB): Polars Lazy API（极致性能）或 Dask
    """
    
    @staticmethod
    def select_engine(
        file_size: int,
        file_path: Path,
        config,
        force_engine: Optional[str] = None
    ) -> str:
        """选择最佳引擎
        
        Args:
            file_size: 文件大小（字节）
            file_path: 文件路径
            config: 配置对象
            force_engine: 强制使用指定引擎 (pandas/dask/polars/auto)
            
        Returns:
            str: 引擎类型 (pandas/dask/polars)
        """
        file_size_mb = file_size / (1024 * 1024)
        
        # 如果指定了强制引擎，直接使用
        if force_engine and force_engine != EngineType.AUTO:
            if force_engine not in [EngineType.PANDAS, EngineType.DASK, EngineType.POLARS]:
                logger.warning(f"不支持的引擎类型: {force_engine}，使用自动选择")
            else:
                logger.info(f"强制使用引擎: {force_engine}")
                return force_engine
        
        # 自动选择策略
        if file_size_mb < 100:
            # 小数据集：使用 pandas
            engine = EngineType.PANDAS
            logger.info(f"小数据集 ({file_size_mb:.2f}MB)，使用 Pandas 引擎")
        elif file_size_mb < 1000:
            # 中等数据集：使用 Dask 或 Pandas
            if config.prefer_dask:
                engine = EngineType.DASK
                logger.info(f"中等数据集 ({file_size_mb:.2f}MB)，使用 Dask 引擎")
            else:
                engine = EngineType.PANDAS
                logger.info(f"中等数据集 ({file_size_mb:.2f}MB)，使用 Pandas 引擎")
        else:
            # 大数据集：使用 Dask 或 Polars
            if config.prefer_polars:
                engine = EngineType.POLARS
                logger.info(f"大数据集 ({file_size_mb:.2f}MB)，使用 Polars 引擎")
            elif config.prefer_dask:
                engine = EngineType.DASK
                logger.info(f"大数据集 ({file_size_mb:.2f}MB)，使用 Dask 引擎")
            else:
                # 默认使用 Dask（更稳定）
                engine = EngineType.DASK
                logger.info(f"大数据集 ({file_size_mb:.2f}MB)，使用 Dask 引擎（默认）")
        
        return engine
    
    @staticmethod
    def validate_engine(engine_type: str) -> bool:
        """验证引擎类型是否有效
        
        Args:
            engine_type: 引擎类型
            
        Returns:
            bool: 是否有效
        """
        return engine_type in [EngineType.PANDAS, EngineType.DASK, EngineType.POLARS, EngineType.AUTO]
    
    @staticmethod
    def get_engine_capabilities(engine_type: str) -> Dict[str, Any]:
        """获取引擎能力说明
        
        Args:
            engine_type: 引擎类型
            
        Returns:
            dict: 引擎能力信息
        """
        capabilities = {
            EngineType.PANDAS: {
                "name": "Pandas",
                "best_for": "小数据集 (<100MB)",
                "memory_usage": "高（全量加载）",
                "performance": "快（小数据）",
                "features": [
                    "全量加载到内存",
                    "成熟的生态系统",
                    "易于调试",
                    "丰富的分析功能"
                ],
                "limitations": [
                    "内存限制",
                    "单线程处理",
                    "不适合大文件"
                ]
            },
            EngineType.DASK: {
                "name": "Dask",
                "best_for": "中大数据集 (100MB-10GB)",
                "memory_usage": "低（分块处理）",
                "performance": "快（并行计算）",
                "features": [
                    "并行计算",
                    "分块处理",
                    "与 Pandas API 兼容",
                    "支持分布式"
                ],
                "limitations": [
                    "学习曲线",
                    "部分功能受限",
                    "调试较困难"
                ]
            },
            EngineType.POLARS: {
                "name": "Polars",
                "best_for": "大数据集 (>1GB)",
                "memory_usage": "极低（流式处理）",
                "performance": "极快（Rust 编写）",
                "features": [
                    "极致性能",
                    "低内存占用",
                    "Lazy API（查询优化）",
                    "多线程处理"
                ],
                "limitations": [
                    "生态系统较新",
                    "API 与 Pandas 不同",
                    "部分功能缺失"
                ]
            }
        }
        
        return capabilities.get(engine_type, {})
