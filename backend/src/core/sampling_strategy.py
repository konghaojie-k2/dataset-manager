#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能采样策略"""

from pathlib import Path
from typing import Dict, Any
from loguru import logger


class SamplingStrategy:
    """智能采样策略
    
    根据文件大小自动确定采样大小和处理策略。
    """
    
    @staticmethod
    def get_sample_size(file_size: int, config) -> int:
        """根据文件大小确定采样大小
        
        Args:
            file_size: 文件大小（字节）
            config: 配置对象
            
        Returns:
            int: 采样行数
        """
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb < 100:
            # 小数据集：采样 1000 行
            sample_size = config.sample_small_size
            logger.info(f"小数据集 ({file_size_mb:.2f}MB)，采样 {sample_size} 行")
            return sample_size
        elif file_size_mb < 1000:
            # 中等数据集：采样 10000 行
            sample_size = config.sample_medium_size
            logger.info(f"中等数据集 ({file_size_mb:.2f}MB)，采样 {sample_size} 行")
            return sample_size
        else:
            # 大数据集：采样 100000 行
            sample_size = config.sample_large_size
            logger.info(f"大数据集 ({file_size_mb:.2f}MB)，采样 {sample_size} 行")
            return sample_size
    
    @staticmethod
    def should_use_streaming(file_size: int, config) -> bool:
        """判断是否需要流式处理
        
        Args:
            file_size: 文件大小（字节）
            config: 配置对象
            
        Returns:
            bool: 是否使用流式处理
        """
        # 超过 1GB 使用流式处理
        should_stream = file_size > 1024 * 1024 * 1024
        file_size_mb = file_size / (1024 * 1024)
        
        if should_stream:
            logger.info(f"大文件 ({file_size_mb:.2f}MB)，启用流式处理")
        else:
            logger.info(f"文件大小 ({file_size_mb:.2f}MB)，使用普通加载")
        
        return should_stream
    
    @staticmethod
    def get_memory_usage_estimate(file_size: int, sample_size: int) -> Dict[str, Any]:
        """估算内存使用情况
        
        Args:
            file_size: 文件大小（字节）
            sample_size: int: 采样行数
            
        Returns:
            dict: 内存估算信息
        """
        file_size_mb = file_size / (1024 * 1024)
        
        # 假设 CSV 文件的内存占用约为文件大小的 3-5 倍
        full_data_memory_mb = file_size_mb * 4
        
        # 采样数据的内存占用
        sample_ratio = min(1.0, sample_size / (file_size_mb * 1000))  # 估算总行数
        sample_memory_mb = full_data_memory_mb * sample_ratio
        
        # 使用 Dask/Polars 的内存占用（流式处理）
        streaming_memory_mb = min(100, file_size_mb * 0.1)  # 流式处理内存占用较小
        
        return {
            "file_size_mb": file_size_mb,
            "full_data_memory_mb": full_data_memory_mb,
            "sample_memory_mb": sample_memory_mb,
            "streaming_memory_mb": streaming_memory_mb,
            "recommended_approach": "streaming" if file_size_mb > 1000 else "sampling"
        }