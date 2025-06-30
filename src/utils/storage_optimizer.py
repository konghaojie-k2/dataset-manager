"""存储优化器

实现数据去重存储策略，确保相同数据只保存一份物理文件
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger

from ..schemas.dataset import DatasetMetadata


class StorageOptimizer:
    """存储优化器 - 实现数据去重存储"""
    
    def __init__(self, upload_dir: Path):
        """初始化存储优化器
        
        Args:
            upload_dir: 上传目录
        """
        self.upload_dir = Path(upload_dir)
        
        # 创建去重存储目录结构
        self.dedupe_dir = self.upload_dir / "dedupe"  # 去重存储目录
        self.refs_dir = self.upload_dir / "refs"     # 引用目录
        
        self.dedupe_dir.mkdir(exist_ok=True)
        self.refs_dir.mkdir(exist_ok=True)
        
        logger.info("存储优化器初始化完成")
    
    def optimize_duplicate_storage(self, 
                                 new_dataset: DatasetMetadata,
                                 original_dataset: DatasetMetadata) -> Dict[str, str]:
        """优化重复数据存储
        
        Args:
            new_dataset: 新上传的数据集
            original_dataset: 原始数据集
            
        Returns:
            Dict[str, str]: 优化结果信息
        """
        try:
            new_file_path = Path(new_dataset.file_path)
            original_file_path = Path(original_dataset.file_path)
            
            # 检查原始文件是否已经在去重目录中
            if not self._is_in_dedupe_storage(original_file_path):
                # 将原始文件移动到去重存储
                dedupe_file_path = self._move_to_dedupe_storage(original_file_path, original_dataset.content_hash)
                # 为原始数据集创建引用
                self._create_file_reference(original_dataset.id, dedupe_file_path)
                
                logger.info(f"原始文件移动到去重存储: {dedupe_file_path}")
            else:
                dedupe_file_path = self._get_dedupe_file_path(original_dataset.content_hash)
            
            # 删除新上传的重复文件
            if new_file_path.exists():
                new_file_path.unlink()
                logger.info(f"删除重复文件: {new_file_path}")
            
            # 为新数据集创建引用
            self._create_file_reference(new_dataset.id, dedupe_file_path)
            
            return {
                "status": "optimized",
                "action": "duplicate_removed",
                "dedupe_file": str(dedupe_file_path),
                "saved_space": new_dataset.file_size,
                "message": f"重复数据已优化，节省空间 {new_dataset.file_size} 字节"
            }
            
        except Exception as e:
            logger.error(f"优化重复数据存储失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def get_actual_file_path(self, dataset_id: str) -> Optional[Path]:
        """获取数据集的实际文件路径
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[Path]: 实际文件路径
        """
        try:
            ref_file = self.refs_dir / f"{dataset_id}.ref"
            
            if ref_file.exists():
                # 从引用文件读取实际路径
                with open(ref_file, 'r', encoding='utf-8') as f:
                    actual_path = f.read().strip()
                return Path(actual_path)
            
            # 如果没有引用文件，可能是直接存储
            return None
            
        except Exception as e:
            logger.error(f"获取实际文件路径失败: {e}")
            return None
    
    def cleanup_orphaned_files(self) -> Dict[str, int]:
        """清理孤立文件
        
        Returns:
            Dict[str, int]: 清理统计信息
        """
        try:
            # 获取所有引用的文件
            referenced_files = set()
            for ref_file in self.refs_dir.glob("*.ref"):
                try:
                    with open(ref_file, 'r', encoding='utf-8') as f:
                        referenced_files.add(f.read().strip())
                except Exception as e:
                    logger.warning(f"读取引用文件失败: {ref_file}, {e}")
            
            # 检查去重目录中的孤立文件
            orphaned_count = 0
            freed_space = 0
            
            for dedupe_file in self.dedupe_dir.iterdir():
                if dedupe_file.is_file() and str(dedupe_file) not in referenced_files:
                    try:
                        file_size = dedupe_file.stat().st_size
                        dedupe_file.unlink()
                        orphaned_count += 1
                        freed_space += file_size
                        logger.info(f"删除孤立文件: {dedupe_file}")
                    except Exception as e:
                        logger.error(f"删除孤立文件失败: {dedupe_file}, {e}")
            
            return {
                "orphaned_files_removed": orphaned_count,
                "space_freed": freed_space,
                "total_referenced_files": len(referenced_files)
            }
            
        except Exception as e:
            logger.error(f"清理孤立文件失败: {e}")
            return {"error": str(e)}
    
    def get_storage_statistics(self) -> Dict[str, any]:
        """获取存储统计信息
        
        Returns:
            Dict[str, any]: 存储统计信息
        """
        try:
            # 统计去重存储
            dedupe_files = list(self.dedupe_dir.glob("*"))
            dedupe_total_size = sum(f.stat().st_size for f in dedupe_files if f.is_file())
            
            # 统计引用文件
            ref_files = list(self.refs_dir.glob("*.ref"))
            
            # 统计常规上传文件
            regular_files = []
            regular_total_size = 0
            for item in self.upload_dir.iterdir():
                if item.is_file() and item.suffix not in ['.ref']:
                    regular_files.append(item)
                    regular_total_size += item.stat().st_size
            
            return {
                "dedupe_storage": {
                    "files_count": len(dedupe_files),
                    "total_size": dedupe_total_size,
                    "directory": str(self.dedupe_dir)
                },
                "references": {
                    "count": len(ref_files),
                    "directory": str(self.refs_dir)
                },
                "regular_storage": {
                    "files_count": len(regular_files),
                    "total_size": regular_total_size
                },
                "total_physical_size": dedupe_total_size + regular_total_size,
                "space_efficiency": {
                    "dedupe_ratio": len(ref_files) / max(len(dedupe_files), 1),
                    "estimated_savings": max(0, len(ref_files) - len(dedupe_files)) * (dedupe_total_size / max(len(dedupe_files), 1))
                }
            }
            
        except Exception as e:
            logger.error(f"获取存储统计信息失败: {e}")
            return {"error": str(e)}
    
    def _is_in_dedupe_storage(self, file_path: Path) -> bool:
        """检查文件是否已在去重存储中"""
        return str(file_path).startswith(str(self.dedupe_dir))
    
    def _move_to_dedupe_storage(self, source_path: Path, content_hash: str) -> Path:
        """将文件移动到去重存储
        
        Args:
            source_path: 源文件路径
            content_hash: 内容哈希值
            
        Returns:
            Path: 去重存储中的文件路径
        """
        # 使用内容哈希作为文件名，保留原始扩展名
        file_extension = source_path.suffix
        dedupe_filename = f"{content_hash}{file_extension}"
        dedupe_file_path = self.dedupe_dir / dedupe_filename
        
        # 移动文件
        shutil.move(str(source_path), str(dedupe_file_path))
        
        return dedupe_file_path
    
    def _get_dedupe_file_path(self, content_hash: str) -> Path:
        """根据内容哈希获取去重文件路径"""
        # 查找匹配的文件（可能有不同扩展名）
        for file_path in self.dedupe_dir.glob(f"{content_hash}.*"):
            return file_path
        
        # 如果没找到，返回默认路径
        return self.dedupe_dir / content_hash
    
    def _create_file_reference(self, dataset_id: str, actual_file_path: Path):
        """创建文件引用
        
        Args:
            dataset_id: 数据集ID
            actual_file_path: 实际文件路径
        """
        ref_file = self.refs_dir / f"{dataset_id}.ref"
        
        with open(ref_file, 'w', encoding='utf-8') as f:
            f.write(str(actual_file_path))
        
        logger.debug(f"创建文件引用: {dataset_id} -> {actual_file_path}")
    
    def remove_dataset_reference(self, dataset_id: str) -> bool:
        """删除数据集引用
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            ref_file = self.refs_dir / f"{dataset_id}.ref"
            if ref_file.exists():
                ref_file.unlink()
                logger.info(f"删除数据集引用: {dataset_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"删除数据集引用失败: {dataset_id}, {e}")
            return False


# 全局存储优化器实例
storage_optimizer = None

def get_storage_optimizer(upload_dir: Path) -> StorageOptimizer:
    """获取存储优化器实例"""
    global storage_optimizer
    if storage_optimizer is None:
        storage_optimizer = StorageOptimizer(upload_dir)
    return storage_optimizer 