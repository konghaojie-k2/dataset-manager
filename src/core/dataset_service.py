"""数据集应用服务层"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import UploadFile
from loguru import logger

from ..schemas.dataset import (
    DatasetMetadata, 
    MetadataExtractionRequest,
    TagUpdateRequest
)
from .dataset_repository import DatasetRepository
from .file_service import FileService
from .metadata_service import MetadataService


class DatasetService:
    """数据集应用服务层
    
    协调各个领域服务，实现完整的业务流程
    """
    
    def __init__(
        self, 
        upload_dir: Path,
        metadata_dir: Path
    ):
        """初始化服务
        
        Args:
            upload_dir: 上传目录
            metadata_dir: 元数据存储目录
        """
        # 初始化各个领域服务
        self.repository = DatasetRepository(metadata_dir)
        self.file_service = FileService(upload_dir)
        self.metadata_service = MetadataService()
        
        logger.info("数据集应用服务初始化完成")
    
    async def upload_dataset(self, file: UploadFile, user_input: Optional[str] = None) -> str:
        """上传数据集
        
        Args:
            file: 上传的文件
            user_input: 用户输入的额外信息
            
        Returns:
            str: 数据集ID
        """
        try:
            # 1. 上传文件
            file_id, file_path, file_info = await self.file_service.upload_file(file)
            
            # 2. 创建数据集元数据
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
            
            # 3. 保存初始元数据
            self.repository.save(dataset)
            
            logger.info(f"数据集上传成功: {dataset.id}")
            
            # 4. 异步触发元数据提取
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
            # 1. 获取数据集
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                raise ValueError(f"数据集不存在: {dataset_id}")
            
            # 2. 更新状态
            self.repository.update_status(dataset_id, "extracting_metadata")
            
            # 3. 提取CSV文件
            file_path = Path(dataset.file_path)
            csv_files = self.file_service.extract_csv_files(file_path)
            
            if not csv_files:
                raise ValueError("未找到可处理的CSV文件")
            
            # 4. 使用第一个CSV文件进行分析
            csv_file = csv_files[0]
            df = self.file_service.load_csv_data(csv_file)
            
            # 5. 提取元数据
            extraction_result = await self.metadata_service.extract_metadata(
                dataset_id=dataset_id,
                file_path=csv_file,
                dataframe=df,
                user_input=user_input
            )
            
            # 6. 更新数据集元数据
            updated_dataset = self.metadata_service.update_dataset_metadata(dataset, extraction_result)
            self.repository.save(updated_dataset)
            
            # 7. 清理临时文件
            self.file_service.file_processor.cleanup_extracted_files(file_path)
            
            logger.info(f"元数据提取完成: {dataset_id}")
            return extraction_result
            
        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            # 更新状态为失败
            if self.repository.exists(dataset_id):
                self.repository.update_status(dataset_id, "extraction_failed")
            raise
    
    def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """获取数据集元数据
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[DatasetMetadata]: 数据集元数据
        """
        return self.repository.get_by_id(dataset_id)
    
    def list_datasets(self) -> List[DatasetMetadata]:
        """列出所有数据集
        
        Returns:
            List[DatasetMetadata]: 数据集列表
        """
        return self.repository.list_all()
    
    def update_tags(self, request: TagUpdateRequest) -> DatasetMetadata:
        """更新数据集标签
        
        Args:
            request: 标签更新请求
            
        Returns:
            DatasetMetadata: 更新后的数据集元数据
        """
        dataset = self.repository.get_by_id(request.dataset_id)
        if not dataset:
            raise ValueError(f"数据集不存在: {request.dataset_id}")
        
        # 更新标签
        dataset.tags = request.tags
        dataset.industry = request.industry
        dataset.analysis_domains = request.analysis_domains
        dataset.applicable_algorithms = request.applicable_algorithms
        
        # 保存更新
        self.repository.save(dataset)
        
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
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                return False
            
            # 删除文件
            file_path = Path(dataset.file_path)
            self.file_service.delete_file(file_path)
            
            # 删除元数据
            success = self.repository.delete(dataset_id)
            
            if success:
                logger.info(f"数据集删除成功: {dataset_id}")
            
            return success
            
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
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                return None
            
            # 提取CSV文件
            file_path = Path(dataset.file_path)
            csv_files = self.file_service.extract_csv_files(file_path)
            
            if not csv_files:
                return None
            
            # 加载数据预览
            df = self.file_service.load_csv_data(csv_files[0], sample_rows=rows)
            
            return {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "data": df.to_dict('records'),
                "dtypes": df.dtypes.to_dict()
            }
            
        except Exception as e:
            logger.error(f"获取数据预览失败: {e}")
            return None 