"""版本控制工具

提供数据集版本管理功能，包括：
- 文件哈希计算和验证
- 数据内容哈希计算
- 版本检测和创建
- 版本历史管理
"""

import hashlib
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from loguru import logger

from ..schemas.dataset import DatasetMetadata
from ..tools.file_processor import FileProcessor


class VersionController:
    """版本控制器"""
    
    def __init__(self):
        self.file_processor = FileProcessor()
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值(SHA256)
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件哈希值
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # 分块读取，避免大文件内存溢出
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            file_hash = sha256_hash.hexdigest()
            logger.debug(f"文件哈希计算完成: {file_path} -> {file_hash[:16]}...")
            return file_hash
            
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            raise
    
    def calculate_content_hash(self, file_path: Path) -> str:
        """计算数据内容哈希值
        
        基于数据的实际内容计算哈希，忽略文件格式差异
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 内容哈希值
        """
        try:
            # 提取CSV数据
            csv_files = self.file_processor.extract_csv_files(file_path)
            if not csv_files:
                logger.warning(f"无法提取CSV文件: {file_path}")
                return self.calculate_file_hash(file_path)
            
            # 加载数据
            df = self.file_processor.load_csv_data(csv_files[0])
            if df is None:
                logger.warning(f"无法加载CSV数据: {csv_files[0]}")
                return self.calculate_file_hash(file_path)
            
            # 计算数据内容哈希
            content_hash = self._calculate_dataframe_hash(df)
            
            # 清理临时文件
            self.file_processor.cleanup_extracted_files(file_path)
            
            logger.debug(f"数据内容哈希计算完成: {file_path} -> {content_hash[:16]}...")
            return content_hash
            
        except Exception as e:
            logger.error(f"计算数据内容哈希失败: {e}")
            # 降级使用文件哈希
            return self.calculate_file_hash(file_path)
    
    def _calculate_dataframe_hash(self, df: pd.DataFrame) -> str:
        """计算DataFrame的哈希值
        
        Args:
            df: DataFrame对象
            
        Returns:
            str: DataFrame哈希值
        """
        try:
            # 标准化数据格式
            df_normalized = df.copy()
            
            # 处理列名（排序确保一致性）
            df_normalized = df_normalized.reindex(sorted(df_normalized.columns), axis=1)
            
            # 处理数值类型，确保精度一致
            for col in df_normalized.select_dtypes(include=['float64', 'float32']).columns:
                df_normalized[col] = df_normalized[col].round(6)
            
            # 处理时间类型，统一格式
            for col in df_normalized.select_dtypes(include=['datetime64']).columns:
                df_normalized[col] = df_normalized[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 转换为字符串并计算哈希
            content_str = df_normalized.to_string(index=False)
            content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
            
            return content_hash
            
        except Exception as e:
            logger.error(f"计算DataFrame哈希失败: {e}")
            raise
    
    def detect_duplicate_data(self, 
                            new_file_hash: str, 
                            new_content_hash: str,
                            existing_datasets: List[DatasetMetadata]) -> Optional[DatasetMetadata]:
        """检测重复数据
        
        Args:
            new_file_hash: 新文件的文件哈希
            new_content_hash: 新文件的内容哈希
            existing_datasets: 现有数据集列表
            
        Returns:
            Optional[DatasetMetadata]: 找到的重复数据集，如果没有则返回None
        """
        try:
            for dataset in existing_datasets:
                # 精确匹配：文件哈希完全相同
                if dataset.file_hash and dataset.file_hash == new_file_hash:
                    logger.info(f"发现完全相同的文件: {dataset.id}")
                    return dataset
                
                # 内容匹配：数据内容相同但文件可能不同（格式差异等）
                if dataset.content_hash and dataset.content_hash == new_content_hash:
                    logger.info(f"发现相同内容的数据: {dataset.id}")
                    return dataset
            
            logger.debug("未发现重复数据")
            return None
            
        except Exception as e:
            logger.error(f"检测重复数据失败: {e}")
            return None
    
    def create_version_info(self, 
                          file_path: Path,
                          parent_dataset: Optional[DatasetMetadata] = None,
                          version_notes: Optional[str] = None) -> Dict[str, Any]:
        """创建版本信息
        
        Args:
            file_path: 文件路径
            parent_dataset: 父版本数据集
            version_notes: 版本说明
            
        Returns:
            Dict[str, Any]: 版本信息
        """
        try:
            # 计算哈希值
            file_hash = self.calculate_file_hash(file_path)
            content_hash = self.calculate_content_hash(file_path)
            
            # 确定版本类型和版本号
            if parent_dataset is None:
                # 原始版本
                version_type = "original"
                version = "1.0"
                parent_version_id = None
            else:
                # 判断是否为重复数据
                if parent_dataset.file_hash == file_hash:
                    version_type = "duplicate"
                    version = parent_dataset.version
                    parent_version_id = parent_dataset.id
                elif parent_dataset.content_hash == content_hash:
                    version_type = "duplicate"
                    version = parent_dataset.version
                    parent_version_id = parent_dataset.id
                else:
                    # 更新版本
                    version_type = "updated"
                    # 版本号递增
                    try:
                        major, minor = map(int, parent_dataset.version.split('.'))
                        version = f"{major}.{minor + 1}"
                    except:
                        version = "2.0"
                    parent_version_id = parent_dataset.id
            
            version_info = {
                "file_hash": file_hash,
                "content_hash": content_hash,
                "version": version,
                "parent_version_id": parent_version_id,
                "version_type": version_type,
                "version_notes": version_notes or f"版本 {version}"
            }
            
            logger.info(f"版本信息创建完成: {version_type} v{version}")
            return version_info
            
        except Exception as e:
            logger.error(f"创建版本信息失败: {e}")
            raise
    
    def get_version_history(self, 
                          dataset_id: str,
                          repository) -> List[Dict[str, Any]]:
        """获取版本历史
        
        Args:
            dataset_id: 数据集ID
            repository: 数据集仓储
            
        Returns:
            List[Dict[str, Any]]: 版本历史列表
        """
        try:
            all_datasets = repository.list_all()
            version_history = []
            
            # 找到所有相关版本
            target_dataset = repository.get_by_id(dataset_id)
            if not target_dataset:
                return []
            
            # 构建版本树
            version_map = {}
            for dataset in all_datasets:
                if (dataset.content_hash == target_dataset.content_hash or 
                    dataset.parent_version_id == dataset_id or
                    dataset.id == dataset_id):
                    
                    version_info = {
                        "id": dataset.id,
                        "name": dataset.name,
                        "version": dataset.version,
                        "version_type": dataset.version_type,
                        "upload_time": dataset.upload_time,
                        "file_size": dataset.file_size,
                        "version_notes": dataset.version_notes,
                        "parent_version_id": dataset.parent_version_id
                    }
                    version_history.append(version_info)
            
            # 按版本号和时间排序
            version_history.sort(key=lambda x: (x["version"], x["upload_time"]))
            
            logger.info(f"获取版本历史完成: {len(version_history)} 个版本")
            return version_history
            
        except Exception as e:
            logger.error(f"获取版本历史失败: {e}")
            return []
    
    def cleanup_old_versions(self, 
                           dataset_id: str,
                           repository,
                           keep_versions: int = 5) -> int:
        """清理旧版本
        
        Args:
            dataset_id: 数据集ID
            repository: 数据集仓储
            keep_versions: 保留版本数量
            
        Returns:
            int: 清理的版本数量
        """
        try:
            version_history = self.get_version_history(dataset_id, repository)
            
            if len(version_history) <= keep_versions:
                logger.info(f"版本数量 {len(version_history)} <= 保留数量 {keep_versions}，无需清理")
                return 0
            
            # 保留最新的版本
            versions_to_keep = sorted(version_history, 
                                    key=lambda x: x["upload_time"], 
                                    reverse=True)[:keep_versions]
            keep_ids = {v["id"] for v in versions_to_keep}
            
            # 删除旧版本
            cleaned_count = 0
            for version in version_history:
                if version["id"] not in keep_ids:
                    try:
                        repository.delete(version["id"])
                        cleaned_count += 1
                        logger.info(f"删除旧版本: {version['id']} v{version['version']}")
                    except Exception as e:
                        logger.error(f"删除版本失败: {version['id']}, {e}")
            
            logger.info(f"版本清理完成: 删除 {cleaned_count} 个旧版本")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧版本失败: {e}")
            return 0


# 全局版本控制器实例
version_controller = VersionController() 