#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速数据处理器 - Dask + Polars 统一接口

提供统一的数据处理接口，自动选择最佳引擎：
- 小数据集：Pandas（全量加载）
- 中等数据集：Dask（并行处理）
- 大数据集：Polars Lazy API（极致性能）

默认使用智能引擎选择，无需手动指定。
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from loguru import logger
from abc import ABC, abstractmethod

from ..config.settings import get_settings
from .sampling_strategy import SamplingStrategy
from .engine_selector import EngineSelector, EngineType


class BaseDataEngine(ABC):
    """数据引擎基类
    
    定义所有引擎必须实现的接口，确保统一的使用方式。
    """
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data = None
        self._shape = None
        self._engine_type = "base"
    
    @abstractmethod
    def load_data(self, sample_size: Optional[int] = None):
        """加载数据
        
        Args:
            sample_size: 采样行数（可选）
            
        Returns:
            加载的数据
        """
        pass
    
    @abstractmethod
    def get_shape(self) -> tuple:
        """获取数据形状
        
        Returns:
            tuple: (行数, 列数)
        """
        pass
    
    @abstractmethod
    def get_columns(self) -> list:
        """获取列名
        
        Returns:
            list: 列名列表
        """
        pass
    
    @abstractmethod
    def get_dtypes(self) -> dict:
        """获取数据类型
        
        Returns:
            dict: {列名: 数据类型}
        """
        pass
    
    @abstractmethod
    def get_null_counts(self) -> dict:
        """获取空值数量
        
        Returns:
            dict: {列名: 空值数量}
        """
        pass
    
    @abstractmethod
    def describe(self) -> Dict[str, Any]:
        """获取统计摘要
        
        Returns:
            dict: 统计摘要
        """
        pass
    
    @abstractmethod
    def get_column_sample(self, column: str, n: int = 10) -> list:
        """获取列样本
        
        Args:
            column: 列名
            n: 样本数量
            
        Returns:
            list: 样本值列表
        """
        pass
    
    @abstractmethod
    def get_unique_count(self, column: str) -> int:
        """获取唯一值数量
        
        Args:
            column: 列名
            
        Returns:
            int: 唯一值数量
        """
        pass
    
    @abstractmethod
    def close(self):
        """关闭引擎，释放资源"""
        pass


class PandasEngine(BaseDataEngine):
    """Pandas 引擎（小数据集，<100MB）
    
    特点：
    - 全量加载到内存
    - 成熟的生态系统
    - 易于调试
    - 适合小数据集快速分析
    """
    
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self._engine_type = EngineType.PANDAS
    
    def load_data(self, sample_size: Optional[int] = None):
        """加载数据
        
        Args:
            sample_size: 采样行数（可选）
            
        Returns:
            DataFrame: 加载的数据
        """
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    if sample_size:
                        self.data = pd.read_csv(self.file_path, encoding=encoding, nrows=sample_size)
                    else:
                        self.data = pd.read_csv(self.file_path, encoding=encoding)
                    logger.info(f"Pandas 引擎加载成功: {self.data.shape}, 编码: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if self.data is None:
                raise ValueError("无法识别文件编码格式")
            
            return self.data
        except Exception as e:
            logger.error(f"Pandas 加载失败: {e}")
            raise
    
    def get_shape(self) -> tuple:
        """获取数据形状"""
        if self.data is None:
            raise ValueError("请先加载数据")
        return self.data.shape
    
    def get_columns(self) -> list:
        """获取列名"""
        if self.data is None:
            raise ValueError("请先加载数据")
        return self.data.columns.tolist()
    
    def get_dtypes(self) -> dict:
        """获取数据类型"""
        if self.data is None:
            raise ValueError("请先加载数据")
        return {col: str(dtype) for col, dtype in self.data.dtypes.items()}
    
    def get_null_counts(self) -> dict:
        """获取空值数量"""
        if self.data is None:
            raise ValueError("请先加载数据")
        return {col: int(count) for col, count in self.data.isnull().sum().to_dict().items()}
    
    def describe(self) -> Dict[str, Any]:
        """获取统计摘要"""
        if self.data is None:
            raise ValueError("请先加载数据")
        
        # 数值型列
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        numeric_summary = {}
        if len(numeric_cols) > 0:
            desc = self.data[numeric_cols].describe()
            numeric_summary = {
                col: {stat: float(val) if pd.notna(val) else None 
                      for stat, val in desc[col].items()}
                for col in desc.columns
            }
        
        # 分类型列
        categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns
        categorical_summary = {}
        for col in categorical_cols:
            value_counts = self.data[col].value_counts().head(10)
            mode_val = self.data[col].mode().iloc[0] if not self.data[col].mode().empty else None
            
            categorical_summary[col] = {
                "unique_count": int(self.data[col].nunique()),
                "top_values": {str(k): int(v) for k, v in value_counts.to_dict().items()},
                "mode": str(mode_val) if mode_val is not None else None
            }
        
        return {
            "numeric_summary": numeric_summary,
            "categorical_summary": categorical_summary,
            "correlation_matrix": {}
        }
    
    def get_column_sample(self, column: str, n: int = 10) -> list:
        """获取列样本"""
        if self.data is None:
            raise ValueError("请先加载数据")
        return [str(val) for val in self.data[column].dropna().head(n).tolist()]
    
    def get_unique_count(self, column: str) -> int:
        """获取唯一值数量"""
        if self.data is None:
            raise ValueError("请先加载数据")
        return int(self.data[column].nunique())
    
    def close(self):
        """关闭引擎"""
        self.data = None
        logger.info("Pandas 引擎已关闭")


class DaskEngine(BaseDataEngine):
    """Dask 引擎（中大数据集，100MB-10GB）
    
    特点：
    - 并行计算（多核 CPU）
    - 分块处理（不占用全部内存）
    - 与 Pandas API 几乎一致
    - 适合中等到大尺寸数据集
    """
    
    def __init__(self, file_path: Path, chunk_size: int = 10000):
        super().__init__(file_path)
        self.chunk_size = chunk_size
        self._ddf = None
        self._engine_type = EngineType.DASK
    
    def load_data(self, sample_size: Optional[int] = None):
        """加载数据
        
        Args:
            sample_size: 采样行数（可选）
            
        Returns:
            Dask DataFrame 或 Pandas DataFrame（采样）
        """
        try:
            import dask.dataframe as dd
            
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    self._ddf = dd.read_csv(
                        str(self.file_path),
                        encoding=encoding,
                        blocksize=self.chunk_size * 1024  # 每块的字节数
                    )
                    logger.info(f"Dask 引擎加载成功，编码: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if self._ddf is None:
                raise ValueError("无法识别文件编码格式")
            
            # 如果需要采样，加载数据到内存
            if sample_size:
                self.data = self._ddf.head(sample_size)
                logger.info(f"Dask 引擎采样 {sample_size} 行")
            else:
                self.data = None  # 延迟加载
            
            return self._ddf
        except ImportError:
            logger.error("Dask 未安装，请运行: uv add dask[complete]")
            raise
        except Exception as e:
            logger.error(f"Dask 加载失败: {e}")
            raise
    
    def get_shape(self) -> tuple:
        """获取数据形状"""
        if self._ddf is None:
            self.load_data()
        return (len(self._ddf), len(self._ddf.columns))
    
    def get_columns(self) -> list:
        """获取列名"""
        if self._ddf is None:
            self.load_data()
        return self._ddf.columns.tolist()
    
    def get_dtypes(self) -> dict:
        """获取数据类型"""
        if self._ddf is None:
            self.load_data()
        return {col: str(dtype) for col, dtype in self._ddf.dtypes.items()}
    
    def get_null_counts(self) -> dict:
        """获取空值数量（并行计算）"""
        if self._ddf is None:
            self.load_data()
        null_counts = self._ddf.isnull().sum().compute()
        return {col: int(count) for col, count in null_counts.items()}
    
    def describe(self) -> Dict[str, Any]:
        """获取统计摘要（并行计算）"""
        if self._ddf is None:
            self.load_data()
        
        # 数值型列
        numeric_cols = self._ddf.select_dtypes(include=[np.number]).columns
        numeric_summary = {}
        if len(numeric_cols) > 0:
            desc = self._ddf[numeric_cols].describe().compute()
            numeric_summary = {
                col: {stat: float(val) if pd.notna(val) else None 
                      for stat, val in desc[col].items()}
                for col in desc.columns
            }
        
        return {
            "numeric_summary": numeric_summary,
            "categorical_summary": {},
            "correlation_matrix": {}
        }
    
    def get_column_sample(self, column: str, n: int = 10) -> list:
        """获取列样本"""
        if self._ddf is None:
            self.load_data()
        sample = self._ddf[column].head(n).compute()
        return [str(val) for val in sample]
    
    def get_unique_count(self, column: str) -> int:
        """获取唯一值数量（并行计算）"""
        if self._ddf is None:
            self.load_data()
        return int(self._ddf[column].nunique().compute())
    
    def close(self):
        """关闭引擎"""
        self._ddf = None
        self.data = None
        logger.info("Dask 引擎已关闭")


class PolarsEngine(BaseDataEngine):
    """Polars 引擎（大数据集，>1GB）
    
    特点：
    - Rust 编写，极致性能
    - Lazy API（延迟执行，查询优化）
    - 低内存占用（流式处理）
    - 多线程并行处理
    """
    
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self._lazy_df = None
        self._engine_type = EngineType.POLARS
    
    def load_data(self, sample_size: Optional[int] = None):
        """加载数据
        
        Args:
            sample_size: 采样行数（可选）
            
        Returns:
            LazyFrame 或 DataFrame（采样）
        """
        try:
            import polars as pl
            
            # 使用 Lazy API（延迟执行）
            self._lazy_df = pl.scan_csv(str(self.file_path))
            logger.info(f"Polars 引擎加载成功")
            
            # 如果需要采样
            if sample_size:
                self.data = self._lazy_df.head(sample_size).collect()
                logger.info(f"Polars 引擎采样 {sample_size} 行")
            else:
                self.data = None  # 延迟加载
            
            return self._lazy_df
        except ImportError:
            logger.error("Polars 未安装，请运行: uv add polars")
            raise
        except Exception as e:
            logger.error(f"Polars 加载失败: {e}")
            raise
    
    def get_shape(self) -> tuple:
        """获取数据形状"""
        if self._lazy_df is None:
            self.load_data()
        try:
            import polars as pl
            return (self._lazy_df.select(pl.len()).collect().item(), 
                    len(self._lazy_df.columns))
        except Exception as e:
            logger.error(f"Polars 获取形状失败: {e}")
            # 降级策略：使用采样数据
            if self.data is not None:
                return self.data.shape
            raise
    
    def get_columns(self) -> list:
        """获取列名"""
        if self._lazy_df is None:
            self.load_data()
        return self._lazy_df.columns
    
    def get_dtypes(self) -> dict:
        """获取数据类型"""
        if self._lazy_df is None:
            self.load_data()
        try:
            schema = self._lazy_df.collect_schema()
            return {name: str(dtype) for name, dtype in schema.items()}
        except Exception as e:
            logger.error(f"Polars 获取数据类型失败: {e}")
            # 降级策略：使用采样数据
            if self.data is not None:
                return {col: str(dtype) for col, dtype in self.data.schema.items()}
            raise
    
    def get_null_counts(self) -> dict:
        """获取空值数量（流式计算）"""
        if self._lazy_df is None:
            self.load_data()
        try:
            null_counts = self._lazy_df.null_count().collect()
            return null_counts.to_dict(as_py=False)
        except Exception as e:
            logger.error(f"Polars 获取空值数量失败: {e}")
            # 降级策略：使用采样数据
            if self.data is not None:
                return {col: int(self.data[col].null_count()) for col in self.data.columns}
            raise
    
    def describe(self) -> Dict[str, Any]:
        """获取统计摘要（流式计算）"""
        if self._lazy_df is None:
            self.load_data()
        
        try:
            import polars as pl
            
            # 数值型列
            numeric_cols = [col for col, dtype in self.get_dtypes().items() 
                           if 'int' in dtype or 'float' in dtype]
            numeric_summary = {}
            if len(numeric_cols) > 0:
                desc = self._lazy_df.select(numeric_cols).describe().collect()
                # 转换为字典格式
                for col in numeric_cols:
                    try:
                        col_data = desc.select(col).row(0)
                        numeric_summary[col] = col_data
                    except Exception as e:
                        logger.warning(f"Polars 描述列 {col} 失败: {e}")
            
            return {
                "numeric_summary": numeric_summary,
                "categorical_summary": {},
                "correlation_matrix": {}
            }
        except Exception as e:
            logger.error(f"Polars 描述失败: {e}")
            # 降级策略：使用采样数据
            if self.data is not None:
                return {
                    "numeric_summary": {},
                    "categorical_summary": {},
                    "correlation_matrix": {}
                }
            raise
    
    def get_column_sample(self, column: str, n: int = 10) -> list:
        """获取列样本"""
        if self._lazy_df is None:
            self.load_data()
        try:
            import polars as pl
            sample = self._lazy_df.select(column).head(n).collect()
            return [str(val) for val in sample[column]]
        except Exception as e:
            logger.error(f"Polars 获取列样本失败: {e}")
            # 降级策略：使用采样数据
            if self.data is not None:
                return [str(val) for val in self.data[column].head(n)]
            raise
    
    def get_unique_count(self, column: str) -> int:
        """获取唯一值数量（流式计算）"""
        if self._lazy_df is None:
            self.load_data()
        try:
            import polars as pl
            return int(self._lazy_df.select(column).unique().select(pl.len()).collect().item())
        except Exception as e:
            logger.error(f"Polars 获取唯一值数量失败: {e}")
            # 降级策略：使用采样数据
            if self.data is not None:
                return int(self.data[column].n_unique())
            raise
    
    def close(self):
        """关闭引擎"""
        self._lazy_df = None
        self.data = None
        logger.info("Polars 引擎已关闭")


class FastDataProcessor:
    """快速数据处理器 - 统一接口
    
    自动选择最佳引擎（默认行为）：
    - 小数据集：Pandas
    - 中等数据集：Dask
    - 大数据集：Polars 或 Dask
    
    使用示例：
        # 自动选择引擎（推荐）
        processor = FastDataProcessor(file_path)
        
        # 强制使用特定引擎
        processor = FastDataProcessor(file_path, engine_type="dask")
    """
    
    def __init__(self, file_path: Path, engine_type: Optional[str] = None):
        """初始化处理器
        
        Args:
            file_path: 文件路径
            engine_type: 引擎类型 (pandas/dask/polars/auto)，None 则自动选择
                         默认为 None，即自动选择
        """
        self.file_path = file_path
        self.engine_type = engine_type
        self.engine = None
        self.config = get_settings()
        
        # 获取文件大小
        self.file_size = file_path.stat().st_size
        
        # 自动选择引擎（默认行为）
        if engine_type is None or engine_type == EngineType.AUTO:
            self.engine_type = EngineSelector.select_engine(
                self.file_size, file_path, self.config
            )
        elif not EngineSelector.validate_engine(engine_type):
            logger.warning(f"不支持的引擎类型: {engine_type}，使用自动选择")
            self.engine_type = EngineSelector.select_engine(
                self.file_size, file_path, self.config
            )
        
        # 初始化引擎
        self._init_engine()
    
    def _init_engine(self):
        """初始化引擎"""
        try:
            if self.engine_type == EngineType.PANDAS:
                self.engine = PandasEngine(self.file_path)
            elif self.engine_type == EngineType.DASK:
                self.engine = DaskEngine(
                    self.file_path,
                    chunk_size=self.config.dask_chunk_size
                )
            elif self.engine_type == EngineType.POLARS:
                self.engine = PolarsEngine(self.file_path)
            else:
                raise ValueError(f"不支持的引擎类型: {self.engine_type}")
            
            logger.info(f"引擎初始化成功: {self.engine_type}")
        except Exception as e:
            logger.error(f"引擎初始化失败: {e}")
            raise
    
    def load_sample(self) -> Any:
        """加载采样数据（用于快速预览）
        
        Returns:
            采样后的数据
        """
        sample_size = SamplingStrategy.get_sample_size(self.file_size, self.config)
        logger.info(f"加载采样数据: {sample_size} 行")
        return self.engine.load_data(sample_size=sample_size)
    
    def load_full(self) -> Any:
        """加载完整数据（用于深度分析）
        
        注意：
        - 对于大文件，使用流式处理，不占用全部内存
        - 只有在真正需要数据时才执行 .compute() 或 .collect()
        
        Returns:
            完整数据（延迟加载）
        """
        logger.info("加载完整数据（流式处理）")
        return self.engine.load_data(sample_size=None)
    
    def get_basic_info(self) -> Dict[str, Any]:
        """获取基础信息（快速，使用采样）
        
        Returns:
            基础信息字典
        """
        # 加载采样数据
        self.load_sample()
        
        return {
            "shape": self.engine.get_shape(),
            "columns": self.engine.get_columns(),
            "dtypes": self.engine.get_dtypes(),
            "null_counts": self.engine.get_null_counts(),
            "file_size": self.file_size,
            "file_size_mb": round(self.file_size / (1024 * 1024), 2),
            "engine_type": self.engine_type
        }
    
    def get_column_analysis(self, column: str) -> Dict[str, Any]:
        """获取列分析（快速，使用采样）
        
        Args:
            column: 列名
            
        Returns:
            列分析结果
        """
        dtypes = self.engine.get_dtypes()
        dtype = dtypes.get(column, "unknown")
        
        return {
            "name": column,
            "dtype": dtype,
            "null_count": self.engine.get_null_counts().get(column, 0),
            "unique_count": self.engine.get_unique_count(column),
            "sample_values": self.engine.get_column_sample(column, n=10)
        }
    
    def get_statistical_summary(self) -> Dict[str, Any]:
        """获取统计摘要（并行计算）
        
        Returns:
            统计摘要
        """
        return self.engine.describe()
    
    def close(self):
        """关闭处理器，释放资源"""
        if self.engine:
            self.engine.close()
            self.engine = None
        logger.info("数据处理器已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 便捷函数
def create_fast_processor(file_path: Path, engine_type: Optional[str] = None) -> FastDataProcessor:
    """创建快速数据处理器
    
    Args:
        file_path: 文件路径
        engine_type: 引擎类型 (pandas/dask/polars/auto)，None 则自动选择
                     默认为 None，即自动选择
        
    Returns:
        FastDataProcessor 实例
    """
    return FastDataProcessor(file_path, engine_type)