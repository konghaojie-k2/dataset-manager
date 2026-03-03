#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件压缩器

支持多种压缩格式，用于减少存储空间。
"""

from pathlib import Path
import gzip
import shutil
from loguru import logger


class FileCompressor:
    """文件压缩器
    
    支持的压缩格式：
    - gzip: 速度快，压缩率中等
    - bzip2: 压缩率高，速度较慢
    - xz: 压缩率最高，速度最慢
    """
    
    def __init__(self):
        """初始化压缩器"""
        self.supported_methods = ['gzip', 'bzip2', 'xz']
    
    def compress_file(
        self,
        file_path: Path,
        method: str = "gzip",
        delete_original: bool = False
    ) -> Path:
        """压缩文件
        
        Args:
            file_path: 文件路径
            method: 压缩方法 (gzip/bzip2/xz)
            delete_original: 是否删除原始文件
            
        Returns:
            压缩文件路径
        """
        try:
            logger.info(f"开始压缩文件: {file_path}")
            
            if method not in self.supported_methods:
                raise ValueError(f"不支持的压缩方法: {method}")
            
            # 生成压缩文件路径
            if method == 'gzip':
                compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            else:
                compressed_path = file_path.with_suffix(f'{file_path.suffix}.{method}')
            
            # 执行压缩
            if method == 'gzip':
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            
            # 计算压缩率
            original_size = file_path.stat().st_size
            compressed_size = compressed_path.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            logger.info(
                f"文件压缩成功: {compressed_path}\n"
                f"原始大小: {original_size / 1024 / 1024:.2f} MB\n"
                f"压缩后大小: {compressed_size / 1024 / 1024:.2f} MB\n"
                f"压缩率: {compression_ratio:.2f}%"
            )
            
            # 删除原始文件
            if delete_original:
                file_path.unlink()
                logger.info(f"已删除原始文件: {file_path}")
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"文件压缩失败: {e}")
            raise
    
    def decompress_file(
        self,
        compressed_path: Path,
        output_path: Path = None
    ) -> Path:
        """解压文件
        
        Args:
            compressed_path: 压缩文件路径
            output_path: 输出路径（可选）
            
        Returns:
            解压文件路径
        """
        try:
            logger.info(f"开始解压文件: {compressed_path}")
            
            # 确定输出路径
            if output_path is None:
                # 移除压缩后缀
                if compressed_path.suffix == '.gz':
                    output_path = compressed_path.with_suffix('')
                else:
                    output_path = compressed_path.with_suffix('')
                    if output_path.suffix.startswith('.'):
                        output_path = output_path.with_suffix('')
            
            # 执行解压
            if compressed_path.suffix == '.gz':
                with gzip.open(compressed_path, 'rb') as f_in:
                    with open(output_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"文件解压成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"文件解压失败: {e}")
            raise