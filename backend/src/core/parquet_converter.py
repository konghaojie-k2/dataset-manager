#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parquet 转换器

将 CSV/Excel 文件转换为 Parquet 格式，提高读取性能和减少存储空间。
"""

from pathlib import Path
from loguru import logger
import pandas as pd


class ParquetConverter:
    """Parquet 转换器
    
    Parquet 格式的优势：
    - 列式存储，读取特定列时更快
    - 压缩率高，节省存储空间
    - 支持谓词下推，减少数据扫描量
    - 保持数据类型
    """
    
    def __init__(self):
        """初始化转换器"""
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    def convert_to_parquet(
        self,
        file_path: Path,
        compression: str = "snappy",
        delete_original: bool = False
    ) -> Path:
        """转换为 Parquet 格式
        
        Args:
            file_path: 原始文件路径
            compression: 压缩算法 (snappy/gzip/brotli/lz4)
            delete_original: 是否删除原始文件
            
        Returns:
            Parquet 文件路径
        """
        try:
            logger.info(f"开始转换为 Parquet: {file_path}")
            
            # 读取原始文件
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
            
            # 生成 Parquet 文件路径
            parquet_path = file_path.with_suffix('.parquet')
            
            # 保存为 Parquet
            df.to_parquet(parquet_path, compression=compression, index=False)
            
            # 计算压缩率
            original_size = file_path.stat().st_size
            compressed_size = parquet_path.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            logger.info(
                f"Parquet 转换成功: {parquet_path}\n"
                f"原始大小: {original_size / 1024 / 1024:.2f} MB\n"
                f"压缩后大小: {compressed_size / 1024 / 1024:.2f} MB\n"
                f"压缩率: {compression_ratio:.2f}%"
            )
            
            # 删除原始文件
            if delete_original:
                file_path.unlink()
                logger.info(f"已删除原始文件: {file_path}")
            
            return parquet_path
            
        except Exception as e:
            logger.error(f"Parquet 转换失败: {e}")
            raise
    
    def read_parquet(self, parquet_path: Path, columns: list = None) -> pd.DataFrame:
        """读取 Parquet 文件
        
        Args:
            parquet_path: Parquet 文件路径
            columns: 要读取的列（可选）
            
        Returns:
            DataFrame
        """
        try:
            logger.info(f"读取 Parquet 文件: {parquet_path}")
            
            if columns:
                df = pd.read_parquet(parquet_path, columns=columns)
            else:
                df = pd.read_parquet(parquet_path)
            
            logger.info(f"成功读取 Parquet 文件: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Parquet 读取失败: {e}")
            raise