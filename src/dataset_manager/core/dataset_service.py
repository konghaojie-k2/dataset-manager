"""数据集服务核心模块"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from loguru import logger

from ..models.dataset import (
    DatasetMetadata, 
    ColumnMetadata, 
    DataQualityMetrics,
    MetadataExtractionRequest,
    TagUpdateRequest
)
from ..core.file_handler import FileHandler
from ..agents.metadata_agent import MetadataExtractionAgent


class DatasetService:
    """数据集服务"""
    
    def __init__(
        self, 
        upload_dir: Path,
        metadata_dir: Path,
        deepseek_api_key: str
    ):
        """初始化服务
        
        Args:
            upload_dir: 上传目录
            metadata_dir: 元数据存储目录
            deepseek_api_key: DeepSeek API密钥
        """
        self.upload_dir = Path(upload_dir)
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.file_handler = FileHandler(self.upload_dir)
        self.metadata_agent = MetadataExtractionAgent(deepseek_api_key)
        
        # 内存中的数据集缓存
        self.datasets_cache: Dict[str, DatasetMetadata] = {}
        
        # 加载已有的元数据
        self._load_existing_metadata()
        
        logger.info("数据集服务初始化完成")
    
    def _load_existing_metadata(self):
        """加载已有的元数据"""
        try:
            for metadata_file in self.metadata_dir.glob("*.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_dict = json.load(f)
                    dataset = DatasetMetadata(**metadata_dict)
                    self.datasets_cache[dataset.id] = dataset
            
            logger.info(f"加载了 {len(self.datasets_cache)} 个数据集的元数据")
        except Exception as e:
            logger.error(f"加载元数据失败: {e}")
    
    def _save_metadata(self, dataset: DatasetMetadata):
        """保存元数据到文件
        
        Args:
            dataset: 数据集元数据
        """
        try:
            metadata_file = self.metadata_dir / f"{dataset.id}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(
                    dataset.model_dump(mode='json'), 
                    f, 
                    ensure_ascii=False, 
                    indent=2,
                    default=str
                )
            logger.info(f"元数据已保存: {metadata_file}")
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            raise
    
    async def upload_dataset(self, file, user_input: Optional[str] = None) -> str:
        """上传数据集
        
        Args:
            file: 上传的文件
            user_input: 用户输入的额外信息
            
        Returns:
            str: 数据集ID
        """
        try:
            # 保存文件
            file_id, file_path = await self.file_handler.save_uploaded_file(file)
            
            # 获取文件信息
            file_info = self.file_handler.get_file_info(file_path)
            
            # 创建数据集元数据
            dataset = DatasetMetadata(
                id=file_id,
                name=file.filename,
                description="",  # 将由LLM生成
                file_path=str(file_path),
                file_size=file_info['file_size'],
                upload_time=datetime.now(),
                columns=[],
                processing_status="uploaded"
            )
            
            # 缓存数据集
            self.datasets_cache[dataset.id] = dataset
            
            # 保存初始元数据
            self._save_metadata(dataset)
            
            logger.info(f"数据集上传成功: {dataset.id}")
            
            # 异步触发元数据提取
            await self.extract_metadata(dataset.id, user_input)
            
            return dataset.id
            
        except Exception as e:
            logger.error(f"数据集上传失败: {e}")
            raise
    
    async def extract_metadata(self, dataset_id: str, user_input: Optional[str] = None) -> Dict[str, Any]:
        """提取数据集元数据
        
        Args:
            dataset_id: 数据集ID
            user_input: 用户输入的额外信息
            
        Returns:
            Dict[str, Any]: 提取结果
        """
        try:
            # 获取数据集
            dataset = self.datasets_cache.get(dataset_id)
            if not dataset:
                raise ValueError(f"数据集不存在: {dataset_id}")
            
            # 更新状态
            dataset.processing_status = "extracting_metadata"
            self._save_metadata(dataset)
            
            # 提取CSV文件
            file_path = Path(dataset.file_path)
            csv_files = self.file_handler.extract_csv_files(file_path)
            
            if not csv_files:
                raise ValueError("未找到可处理的CSV文件")
            
            # 使用第一个CSV文件进行分析
            csv_file = csv_files[0]
            
            # 加载数据
            df = self.file_handler.load_csv_data(csv_file)
            
            # 使用LangGraph代理提取元数据
            extraction_result = await self.metadata_agent.extract_metadata(
                dataset_id=dataset_id,
                file_path=csv_file,
                dataframe=df,
                user_input=user_input
            )
            
            # 更新数据集元数据
            await self._update_dataset_from_extraction(dataset, extraction_result)
            
            # 清理临时文件
            self.file_handler.cleanup_extracted_files(file_path)
            
            logger.info(f"元数据提取完成: {dataset_id}")
            return extraction_result
            
        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            # 更新状态为失败
            if dataset_id in self.datasets_cache:
                self.datasets_cache[dataset_id].processing_status = "extraction_failed"
                self._save_metadata(self.datasets_cache[dataset_id])
            raise
    
    async def _update_dataset_from_extraction(
        self, 
        dataset: DatasetMetadata, 
        extraction_result: Dict[str, Any]
    ):
        """从提取结果更新数据集元数据
        
        Args:
            dataset: 数据集元数据
            extraction_result: 提取结果
        """
        try:
            # 更新基本信息
            dataset.description = extraction_result.get("dataset_description", "")
            dataset.time_range_start = extraction_result.get("time_range_start")
            dataset.time_range_end = extraction_result.get("time_range_end")
            dataset.sampling_rate = extraction_result.get("sampling_rate")
            
            # 更新列信息
            columns_metadata = extraction_result.get("columns_metadata", [])
            dataset.columns = [
                ColumnMetadata(
                    name=col["name"],
                    data_type=col.get("dtype", "unknown"),
                    business_meaning=col.get("business_meaning", ""),
                    is_device_id=col.get("is_device_id", False),
                    is_timestamp=col.get("is_timestamp", False),
                    null_count=col.get("null_count", 0),
                    unique_count=col.get("unique_count", 0),
                    sample_values=col.get("sample_values", [])
                )
                for col in columns_metadata
            ]
            
            # 更新数据质量
            quality_data = extraction_result.get("quality_metrics", {})
            if quality_data:
                dataset.quality_metrics = DataQualityMetrics(**quality_data)
            
            # 更新建议的标签
            dataset.tags = extraction_result.get("suggested_tags", [])
            dataset.industry = extraction_result.get("suggested_industry")
            dataset.analysis_domains = extraction_result.get("suggested_domains", [])
            dataset.applicable_algorithms = extraction_result.get("suggested_algorithms", [])
            
            # 更新状态
            dataset.processing_status = "metadata_extracted"
            dataset.metadata_extracted = True
            
            # 保存更新
            self._save_metadata(dataset)
            
        except Exception as e:
            logger.error(f"更新数据集元数据失败: {e}")
            raise
    
    def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """获取数据集元数据
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[DatasetMetadata]: 数据集元数据
        """
        return self.datasets_cache.get(dataset_id)
    
    def list_datasets(self) -> List[DatasetMetadata]:
        """列出所有数据集
        
        Returns:
            List[DatasetMetadata]: 数据集列表
        """
        return list(self.datasets_cache.values())
    
    def update_tags(self, request: TagUpdateRequest) -> DatasetMetadata:
        """更新数据集标签
        
        Args:
            request: 标签更新请求
            
        Returns:
            DatasetMetadata: 更新后的数据集元数据
        """
        dataset = self.datasets_cache.get(request.dataset_id)
        if not dataset:
            raise ValueError(f"数据集不存在: {request.dataset_id}")
        
        # 更新标签
        dataset.tags = request.tags
        dataset.industry = request.industry
        dataset.analysis_domains = request.analysis_domains
        dataset.applicable_algorithms = request.applicable_algorithms
        
        # 保存更新
        self._save_metadata(dataset)
        
        logger.info(f"标签更新完成: {request.dataset_id}")
        return dataset
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """删除数据集
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            dataset = self.datasets_cache.get(dataset_id)
            if not dataset:
                return False
            
            # 删除文件
            file_path = Path(dataset.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # 清理提取的文件
            self.file_handler.cleanup_extracted_files(file_path)
            
            # 删除元数据文件
            metadata_file = self.metadata_dir / f"{dataset_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            # 从缓存中移除
            del self.datasets_cache[dataset_id]
            
            logger.info(f"数据集删除成功: {dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"数据集删除失败: {e}")
            return False
    
    def get_dataset_preview(self, dataset_id: str, rows: int = 10) -> Optional[Dict[str, Any]]:
        """获取数据集预览
        
        Args:
            dataset_id: 数据集ID
            rows: 预览行数
            
        Returns:
            Optional[Dict[str, Any]]: 数据预览
        """
        try:
            dataset = self.datasets_cache.get(dataset_id)
            if not dataset:
                return None
            
            # 提取CSV文件
            file_path = Path(dataset.file_path)
            csv_files = self.file_handler.extract_csv_files(file_path)
            
            if not csv_files:
                return None
            
            # 加载数据预览
            df = self.file_handler.load_csv_data(csv_files[0], sample_rows=rows)
            
            return {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "data": df.to_dict('records'),
                "dtypes": df.dtypes.to_dict()
            }
            
        except Exception as e:
            logger.error(f"获取数据预览失败: {e}")
            return None 