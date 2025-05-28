"""数据集仓储层"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from ..schemas.dataset import DatasetMetadata


class DatasetRepository:
    """数据集仓储，负责数据持久化"""
    
    def __init__(self, metadata_dir: Path):
        """初始化仓储
        
        Args:
            metadata_dir: 元数据存储目录
        """
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._cache: Dict[str, DatasetMetadata] = {}
        
        # 加载已有数据
        self._load_all()
        
        logger.info(f"数据集仓储初始化完成，加载了 {len(self._cache)} 个数据集")
    
    def _load_all(self):
        """加载所有元数据"""
        try:
            for metadata_file in self.metadata_dir.glob("*.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_dict = json.load(f)
                    dataset = DatasetMetadata(**metadata_dict)
                    self._cache[dataset.id] = dataset
        except Exception as e:
            logger.error(f"加载元数据失败: {e}")
    
    def save(self, dataset: DatasetMetadata) -> None:
        """保存数据集元数据
        
        Args:
            dataset: 数据集元数据
        """
        try:
            # 更新缓存
            self._cache[dataset.id] = dataset
            
            # 保存到文件
            metadata_file = self.metadata_dir / f"{dataset.id}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(
                    dataset.model_dump(mode='json'), 
                    f, 
                    ensure_ascii=False, 
                    indent=2,
                    default=str
                )
            logger.debug(f"元数据已保存: {metadata_file}")
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            raise
    
    def get_by_id(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """根据ID获取数据集
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[DatasetMetadata]: 数据集元数据
        """
        return self._cache.get(dataset_id)
    
    def list_all(self) -> List[DatasetMetadata]:
        """获取所有数据集
        
        Returns:
            List[DatasetMetadata]: 数据集列表
        """
        return list(self._cache.values())
    
    def delete(self, dataset_id: str) -> bool:
        """删除数据集
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 从缓存中移除
            if dataset_id in self._cache:
                del self._cache[dataset_id]
            
            # 删除文件
            metadata_file = self.metadata_dir / f"{dataset_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            logger.info(f"数据集元数据删除成功: {dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除数据集元数据失败: {e}")
            return False
    
    def exists(self, dataset_id: str) -> bool:
        """检查数据集是否存在
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            bool: 是否存在
        """
        return dataset_id in self._cache
    
    def update_status(self, dataset_id: str, status: str) -> None:
        """更新数据集状态
        
        Args:
            dataset_id: 数据集ID
            status: 新状态
        """
        if dataset_id in self._cache:
            self._cache[dataset_id].processing_status = status
            self.save(self._cache[dataset_id]) 