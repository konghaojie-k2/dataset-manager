"""数据集仓储层 - 混合存储策略"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from ..schemas.dataset import DatasetMetadata
from .database_repository import DatabaseRepository


class DatasetRepository:
    """数据集仓储，负责数据持久化
    
    采用混合存储策略：
    - SQLite: 存储结构化元数据，支持高效查询
    - JSON: 存储分析结果和复杂数据，保持灵活性
    """
    
    def __init__(self, metadata_dir: Path):
        """初始化仓储
        
        Args:
            metadata_dir: 元数据存储目录
        """
        self.metadata_dir = Path(metadata_dir)
        # 延迟初始化：只在目录不存在时创建，使用线程池避免阻塞
        if not self.metadata_dir.exists():
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            _executor = ThreadPoolExecutor(max_workers=1)
            try:
                loop = asyncio.get_running_loop()
                loop.run_in_executor(_executor, lambda: self.metadata_dir.mkdir(parents=True, exist_ok=True))
            except RuntimeError:
                self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化SQLite数据库仓储
        db_path = self.metadata_dir / "datasets.db"
        self.db_repository = DatabaseRepository(db_path)
        
        # JSON文件存储目录（用于存储分析结果）
        self.json_dir = self.metadata_dir / "analysis_results"
        if not self.json_dir.exists():
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            _executor = ThreadPoolExecutor(max_workers=1)
            try:
                loop = asyncio.get_running_loop()
                loop.run_in_executor(_executor, lambda: self.json_dir.mkdir(exist_ok=True))
            except RuntimeError:
                self.json_dir.mkdir(exist_ok=True)
        
        # 分离存储目录
        self.business_analysis_dir = self.json_dir / "business"
        self.quality_analysis_dir = self.json_dir / "quality"
        if not self.business_analysis_dir.exists():
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            _executor = ThreadPoolExecutor(max_workers=1)
            try:
                loop = asyncio.get_running_loop()
                loop.run_in_executor(_executor, lambda: self.business_analysis_dir.mkdir(exist_ok=True))
            except RuntimeError:
                self.business_analysis_dir.mkdir(exist_ok=True)
        if not self.quality_analysis_dir.exists():
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            _executor = ThreadPoolExecutor(max_workers=1)
            try:
                loop = asyncio.get_running_loop()
                loop.run_in_executor(_executor, lambda: self.quality_analysis_dir.mkdir(exist_ok=True))
            except RuntimeError:
                self.quality_analysis_dir.mkdir(exist_ok=True)
        
        # 内存缓存（可选，用于提高性能）
        self._cache: Dict[str, DatasetMetadata] = {}
        
        logger.info(f"混合存储仓储初始化完成，数据库: {db_path}")
    
    def save(self, dataset: DatasetMetadata) -> None:
        """保存数据集元数据
        
        Args:
            dataset: 数据集元数据
        """
        try:
            # 0. 确保业务分析结果被正确构建
            dataset._build_business_analysis_results()
            
            # 1. 保存结构化数据到SQLite
            self.db_repository.save_dataset(dataset)
            
            # 2. 保存分析结果到JSON文件（如果有的话）
            self._save_analysis_results_to_json(dataset)
            
            # 3. 更新内存缓存
            self._cache[dataset.id] = dataset
            
            logger.debug(f"数据集元数据已保存（混合存储）: {dataset.id}")
            
        except Exception as e:
            logger.error(f"保存数据集元数据失败: {e}")
            raise
    
    def _save_analysis_results_to_json(self, dataset: DatasetMetadata) -> None:
        """保存分析结果到JSON文件
        
        Args:
            dataset: 数据集元数据
        """
        try:
            # 提取分析结果
            analysis_results = {
                "device_time_identification": dataset.device_time_identification,
                "business_meaning_analysis": dataset.business_meaning_analysis,
                "control_relationships_analysis": dataset.control_relationships_analysis,
                "basic_analysis": dataset.basic_analysis,
                "detailed_analysis": dataset.detailed_analysis,
                "insights": dataset.insights,
                "recommendations": dataset.recommendations,
                "quality_analysis_results": dataset.quality_analysis_results
            }
            
            # 只有当有分析结果时才保存JSON文件
            if any(v for v in analysis_results.values() if v is not None):
                json_file = self.json_dir / f"{dataset.id}_analysis.json"
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "dataset_id": dataset.id,
                        "dataset_name": dataset.name,
                        "analysis_timestamp": datetime.now().isoformat(),
                        "analysis_results": analysis_results
                    }, f, ensure_ascii=False, indent=2, default=str)
                
                # 在数据库中记录分析结果文件引用
                self.db_repository.save_analysis_result(
                    dataset_id=dataset.id,
                    analysis_type="industrial_analysis",
                    result_file_path=str(json_file)
                )
                
                logger.debug(f"分析结果已保存到JSON: {json_file}")
                
        except Exception as e:
            logger.warning(f"保存分析结果到JSON失败: {e}")
            # 不影响主流程
    
    def save_business_analysis_results(self, dataset_id: str, business_results: Dict) -> None:
        """保存业务分析结果到独立文件
        
        Args:
            dataset_id: 数据集ID
            business_results: 业务分析结果
        """
        try:
            business_file = self.business_analysis_dir / f"{dataset_id}_business_analysis.json"
            
            with open(business_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "dataset_id": dataset_id,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "business_analysis_results": business_results
                }, f, ensure_ascii=False, indent=2, default=str)
            
            # 在数据库中记录分析结果文件引用
            self.db_repository.save_analysis_result(
                dataset_id=dataset_id,
                analysis_type="business_analysis",
                result_file_path=str(business_file)
            )
            
            logger.debug(f"业务分析结果已保存: {business_file}")
            
        except Exception as e:
            logger.error(f"保存业务分析结果失败: {e}")
            raise
    
    def save_quality_analysis_results(self, dataset_id: str, quality_results: Dict) -> None:
        """保存质量分析结果到独立文件
        
        Args:
            dataset_id: 数据集ID
            quality_results: 质量分析结果
        """
        try:
            quality_file = self.quality_analysis_dir / f"{dataset_id}_quality_analysis.json"
            
            with open(quality_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "dataset_id": dataset_id,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "quality_analysis_results": quality_results
                }, f, ensure_ascii=False, indent=2, default=str)
            
            # 在数据库中记录分析结果文件引用
            self.db_repository.save_analysis_result(
                dataset_id=dataset_id,
                analysis_type="quality_analysis",
                result_file_path=str(quality_file)
            )
            
            logger.debug(f"质量分析结果已保存: {quality_file}")
            
        except Exception as e:
            logger.error(f"保存质量分析结果失败: {e}")
            raise
    
    def get_business_analysis_results(self, dataset_id: str) -> Optional[Dict]:
        """获取业务分析结果
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[Dict]: 业务分析结果
        """
        try:
            business_file = self.business_analysis_dir / f"{dataset_id}_business_analysis.json"
            
            if business_file.exists():
                with open(business_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get("business_analysis_results")
            
            # 兼容旧格式：从统一文件中读取
            return self._get_legacy_business_analysis_results(dataset_id)
            
        except Exception as e:
            logger.error(f"获取业务分析结果失败: {e}")
            return None
    
    def get_quality_analysis_results(self, dataset_id: str) -> Optional[Dict]:
        """获取质量分析结果
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[Dict]: 质量分析结果
        """
        try:
            quality_file = self.quality_analysis_dir / f"{dataset_id}_quality_analysis.json"
            
            if quality_file.exists():
                with open(quality_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get("quality_analysis_results")
            
            # 兼容旧格式：从统一文件中读取
            return self._get_legacy_quality_analysis_results(dataset_id)
            
        except Exception as e:
            logger.error(f"获取质量分析结果失败: {e}")
            return None
    
    def _get_legacy_business_analysis_results(self, dataset_id: str) -> Optional[Dict]:
        """从旧格式文件中获取业务分析结果（兼容性方法）
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[Dict]: 业务分析结果
        """
        try:
            legacy_file = self.json_dir / f"{dataset_id}_analysis.json"
            
            if legacy_file.exists():
                with open(legacy_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                analysis_results = data.get("analysis_results", {})
                
                # 提取业务分析相关字段
                business_results = {
                    "device_time_identification": analysis_results.get("device_time_identification"),
                    "business_meaning_analysis": analysis_results.get("business_meaning_analysis"),
                    "control_relationships_analysis": analysis_results.get("control_relationships_analysis"),
                    "basic_analysis": analysis_results.get("basic_analysis"),
                    "detailed_analysis": analysis_results.get("detailed_analysis"),
                    "insights": analysis_results.get("insights", []),
                    "recommendations": analysis_results.get("recommendations")
                }
                
                # 过滤掉None值
                return {k: v for k, v in business_results.items() if v is not None}
            
            return None
            
        except Exception as e:
            logger.warning(f"从旧格式文件获取业务分析结果失败: {e}")
            return None
    
    def _get_legacy_quality_analysis_results(self, dataset_id: str) -> Optional[Dict]:
        """从旧格式文件中获取质量分析结果（兼容性方法）
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[Dict]: 质量分析结果
        """
        try:
            legacy_file = self.json_dir / f"{dataset_id}_analysis.json"
            
            if legacy_file.exists():
                with open(legacy_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                analysis_results = data.get("analysis_results", {})
                return analysis_results.get("quality_analysis_results")
            
            return None
            
        except Exception as e:
            logger.warning(f"从旧格式文件获取质量分析结果失败: {e}")
            return None
    
    def get_by_id(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """根据ID获取数据集
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[DatasetMetadata]: 数据集元数据
        """
        try:
            # 1. 先检查内存缓存
            if dataset_id in self._cache:
                return self._cache[dataset_id]
            
            # 2. 从SQLite获取基本元数据
            dataset = self.db_repository.get_dataset_by_id(dataset_id)
            
            if not dataset:
                return None
            
            # 3. 从JSON文件加载分析结果
            self._load_analysis_results_from_json(dataset)
            
            # 4. 更新缓存
            self._cache[dataset_id] = dataset
            
            return dataset
            
        except Exception as e:
            logger.error(f"获取数据集失败: {e}")
            return None
    
    def _load_analysis_results_from_json(self, dataset: DatasetMetadata) -> None:
        """从JSON文件加载分析结果
        
        Args:
            dataset: 数据集元数据
        """
        try:
            json_file = self.json_dir / f"{dataset.id}_analysis.json"
            
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                analysis_results = data.get("analysis_results", {})
                
                # 将分析结果加载到数据集对象中
                dataset.device_time_identification = analysis_results.get("device_time_identification")
                dataset.business_meaning_analysis = analysis_results.get("business_meaning_analysis")
                dataset.control_relationships_analysis = analysis_results.get("control_relationships_analysis")
                dataset.basic_analysis = analysis_results.get("basic_analysis")
                dataset.detailed_analysis = analysis_results.get("detailed_analysis")
                dataset.insights = analysis_results.get("insights", [])
                dataset.recommendations = analysis_results.get("recommendations")
                dataset.quality_analysis_results = analysis_results.get("quality_analysis_results")

                # 重新构建业务分析结果组合对象
                dataset._build_business_analysis_results()

                logger.debug(f"分析结果已从JSON加载: {json_file}")
                
        except Exception as e:
            logger.warning(f"从JSON加载分析结果失败: {e}")
            # 不影响主流程
    
    async def list_all(self) -> List[DatasetMetadata]:
        """获取所有数据集（异步版本，避免阻塞调用）
        
        Returns:
            List[DatasetMetadata]: 数据集列表
        """
        try:
            import asyncio
            # 使用 asyncio.to_thread 在线程中执行阻塞的数据库查询
            datasets = await asyncio.to_thread(
                self.db_repository.list_datasets,
                limit=10000,
                offset=0
            )
            
            # 为了显示正确的状态，需要加载质量分析结果
            for dataset in datasets:
                try:
                    json_file = self.json_dir / f"{dataset.id}_analysis.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        analysis_results = data.get("analysis_results", {})
                        # 只加载质量分析结果，用于状态显示
                        dataset.quality_analysis_results = analysis_results.get("quality_analysis_results")
                except Exception as e:
                    logger.warning(f"加载数据集 {dataset.id} 的质量分析结果失败: {e}")
                    # 不影响主流程，继续处理其他数据集
            
            return datasets
            
        except Exception as e:
            logger.error(f"列出数据集失败: {e}", exc_info=True)
            return []
    
    def list_with_filters(
        self, 
        limit: int = 100, 
        offset: int = 0,
        industry: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[DatasetMetadata]:
        """带筛选条件的数据集列表
        
        Args:
            limit: 限制数量
            offset: 偏移量
            industry: 行业筛选
            tags: 标签筛选
            
        Returns:
            List[DatasetMetadata]: 数据集列表
        """
        try:
            return self.db_repository.list_datasets(
                limit=limit,
                offset=offset,
                industry=industry,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"筛选数据集失败: {e}")
            return []
    
    def delete(self, dataset_id: str) -> bool:
        """删除数据集
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 1. 从SQLite删除
            db_success = self.db_repository.delete_dataset(dataset_id)
            
            # 2. 删除JSON文件
            json_file = self.json_dir / f"{dataset_id}_analysis.json"
            if json_file.exists():
                json_file.unlink()
                logger.debug(f"分析结果JSON文件已删除: {json_file}")
            
            # 3. 从缓存中移除
            if dataset_id in self._cache:
                del self._cache[dataset_id]
            
            if db_success:
                logger.info(f"数据集删除成功（混合存储）: {dataset_id}")
            
            return db_success
            
        except Exception as e:
            logger.error(f"删除数据集失败: {e}")
            return False
    
    def exists(self, dataset_id: str) -> bool:
        """检查数据集是否存在
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            bool: 是否存在
        """
        try:
            # 检查缓存
            if dataset_id in self._cache:
                return True
            
            # 检查数据库
            dataset = self.db_repository.get_dataset_by_id(dataset_id)
            return dataset is not None
            
        except Exception as e:
            logger.error(f"检查数据集存在性失败: {e}")
            return False
    
    def update_status(self, dataset_id: str, status: str) -> None:
        """更新数据集状态
        
        Args:
            dataset_id: 数据集ID
            status: 新状态
        """
        try:
            # 更新缓存
            if dataset_id in self._cache:
                self._cache[dataset_id].processing_status = status
                # 保存到数据库
                self.save(self._cache[dataset_id])
            else:
                # 从数据库加载，更新状态，再保存
                dataset = self.get_by_id(dataset_id)
                if dataset:
                    dataset.processing_status = status
                    self.save(dataset)
                    
        except Exception as e:
            logger.error(f"更新数据集状态失败: {e}")
    
    def get_statistics(self) -> Dict[str, any]:
        """获取仓储统计信息
        
        Returns:
            Dict[str, any]: 统计信息
        """
        try:
            # 获取数据库统计
            db_stats = self.db_repository.get_statistics()
            
            # 获取JSON文件统计
            json_files = list(self.json_dir.glob("*_analysis.json"))
            json_total_size = sum(f.stat().st_size for f in json_files)
            
            return {
                **db_stats,
                "json_analysis_files": len(json_files),
                "json_total_size_mb": round(json_total_size / (1024 * 1024), 2),
                "storage_strategy": "hybrid_sqlite_json",
                "cache_size": len(self._cache)
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def clear_cache(self) -> None:
        """清空内存缓存"""
        self._cache.clear()
        logger.info("内存缓存已清空")
    
    def get_analysis_results(self, dataset_id: str) -> List[Dict[str, any]]:
        """获取数据集的分析结果列表
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            List[Dict[str, any]]: 分析结果列表
        """
        return self.db_repository.get_analysis_results(dataset_id) 