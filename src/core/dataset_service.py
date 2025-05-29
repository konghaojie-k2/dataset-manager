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
from ..graph.workflow import run_industrial_analysis
from ..tools.report_manager import report_manager


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
            
            # 移除自动触发元数据提取，改为手动触发
            # await self.extract_metadata(dataset.id, user_input)
            
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
            logger.info(f"开始提取数据集元数据: {dataset_id}")
            
            # 1. 获取数据集
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                raise ValueError(f"数据集不存在: {dataset_id}")
            
            # 2. 获取文件路径
            file_path = Path(dataset.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"数据文件不存在: {file_path}")
            
            # 3. 运行工业数据分析工作流
            analysis_result = await run_industrial_analysis(
                file_path=file_path,
                dataset_name=dataset.name,
                user_requirements=user_input or ""
            )
            
            # 4. 检查分析是否成功
            if not analysis_result or analysis_result.get("errors"):
                logger.error(f"工业数据分析失败: {analysis_result.get('errors', [])}")
                raise RuntimeError("工业数据分析失败")
            
            # 5. 提取分析结果
            extraction_result = {
                "basic_info": analysis_result.get("data_info", {}),
                "statistical_summary": analysis_result.get("statistical_summary", {}),
                "device_time_identification": analysis_result.get("device_time_identification", ""),
                "business_meaning_analysis": analysis_result.get("business_meaning_analysis", ""),
                "control_relationships_analysis": analysis_result.get("control_relationships_analysis", ""),
                "basic_analysis": analysis_result.get("basic_analysis", ""),
                "detailed_analysis": analysis_result.get("detailed_analysis", ""),
                "insights": analysis_result.get("insights", []),
                "recommendations": analysis_result.get("recommendations", ""),
                "column_analyses": analysis_result.get("column_analyses", {}),
                "completed_steps": analysis_result.get("completed_steps", []),
                "errors": analysis_result.get("errors", [])
            }
            
            # 6. 更新数据集元数据
            updated_dataset = self.metadata_service.update_dataset_metadata(dataset, extraction_result)
            
            # 7. 添加工业分析特定的元数据
            if extraction_result.get("device_time_identification"):
                updated_dataset.tags = updated_dataset.tags or []
                if "工业数据" not in updated_dataset.tags:
                    updated_dataset.tags.append("工业数据")
                if "设备监控" not in updated_dataset.tags:
                    updated_dataset.tags.append("设备监控")
            
            # 8. 保存更新后的数据集
            self.repository.save(updated_dataset)
            
            # 9. 保存分析结果为MD文件
            try:
                saved_files = report_manager.save_industrial_analysis_report(
                    dataset_id=dataset_id,
                    dataset_name=dataset.name,
                    analysis_results=extraction_result
                )
                logger.info(f"分析报告已保存为MD文件: {len(saved_files)} 个文件")
                
                # 将文件路径信息添加到返回结果中
                extraction_result["saved_report_files"] = {
                    key: str(path) for key, path in saved_files.items()
                }
            except Exception as e:
                logger.warning(f"保存分析报告文件失败: {e}")
                # 不影响主流程，继续执行
            
            # 10. 清理临时文件
            self.file_service.file_processor.cleanup_extracted_files(file_path)
            
            logger.info(f"数据集元数据提取完成: {dataset_id}")
            return extraction_result
            
        except Exception as e:
            logger.error(f"提取数据集元数据失败: {e}")
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
            
            # 将dtypes转换为字符串，避免JSON序列化问题
            dtypes_dict = {}
            for col, dtype in df.dtypes.items():
                dtypes_dict[col] = str(dtype)
            
            return {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "data": df.to_dict('records'),
                "dtypes": dtypes_dict  # 使用转换后的字符串字典
            }
            
        except Exception as e:
            logger.error(f"获取数据预览失败: {e}")
            return None
    
    async def start_business_analysis(self, dataset_id: str) -> Dict[str, Any]:
        """启动业务分析
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Dict[str, Any]: 启动结果
        """
        try:
            logger.info(f"开始启动业务分析: {dataset_id}")
            
            # 1. 获取数据集
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                raise ValueError(f"数据集不存在: {dataset_id}")
            
            # 2. 检查当前状态
            if dataset.processing_status != "uploaded":
                raise ValueError(f"数据集状态不允许启动业务分析: {dataset.processing_status}")
            
            # 3. 更新状态为业务分析中
            dataset.processing_status = "business_analyzing"
            self.repository.save(dataset)
            
            # 4. 实际执行业务分析逻辑
            logger.info(f"开始执行业务分析: {dataset_id}")
            
            # 获取文件路径
            file_path = Path(dataset.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"数据文件不存在: {file_path}")
            
            # 运行工业数据分析工作流
            analysis_result = await run_industrial_analysis(
                file_path=file_path,
                dataset_name=dataset.name,
                user_requirements=""
            )
            
            # 检查分析是否成功
            if not analysis_result or analysis_result.get("errors"):
                logger.error(f"业务分析失败: {analysis_result.get('errors', [])}")
                dataset.processing_status = "analysis_failed"
                self.repository.save(dataset)
                raise RuntimeError("业务分析失败")
            
            # 提取分析结果
            extraction_result = {
                "basic_info": analysis_result.get("data_info", {}),
                "statistical_summary": analysis_result.get("statistical_summary", {}),
                "device_time_identification": analysis_result.get("device_time_identification", ""),
                "business_meaning_analysis": analysis_result.get("business_meaning_analysis", ""),
                "control_relationships_analysis": analysis_result.get("control_relationships_analysis", ""),
                "basic_analysis": analysis_result.get("basic_analysis", ""),
                "detailed_analysis": analysis_result.get("detailed_analysis", ""),
                "insights": analysis_result.get("insights", []),
                "recommendations": analysis_result.get("recommendations", ""),
                "column_analyses": analysis_result.get("column_analyses", {}),
                "completed_steps": analysis_result.get("completed_steps", []),
                "errors": analysis_result.get("errors", [])
            }
            
            # 更新数据集元数据
            updated_dataset = self.metadata_service.update_dataset_metadata(dataset, extraction_result)
            
            # 更新状态为业务分析完成
            updated_dataset.processing_status = "business_completed"
            
            # 保存更新后的数据集
            self.repository.save(updated_dataset)
            
            # 保存分析结果为MD文件
            try:
                saved_files = report_manager.save_industrial_analysis_report(
                    dataset_id=dataset_id,
                    dataset_name=dataset.name,
                    analysis_results=extraction_result
                )
                logger.info(f"分析报告已保存为MD文件: {len(saved_files)} 个文件")
            except Exception as e:
                logger.warning(f"保存分析报告文件失败: {e}")
            
            # 清理临时文件
            self.file_service.file_processor.cleanup_extracted_files(file_path)
            
            logger.info(f"业务分析完成: {dataset_id}")
            return {
                "success": True,
                "message": "业务分析已完成",
                "dataset_id": dataset_id,
                "status": "business_completed"
            }
            
        except Exception as e:
            logger.error(f"业务分析失败: {e}")
            # 更新状态为失败
            dataset = self.repository.get_by_id(dataset_id)
            if dataset:
                dataset.processing_status = "analysis_failed"
                self.repository.save(dataset)
            raise
    
    async def start_quality_analysis(self, dataset_id: str) -> Dict[str, Any]:
        """启动质量分析
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Dict[str, Any]: 启动结果
        """
        try:
            logger.info(f"开始启动质量分析: {dataset_id}")
            
            # 1. 获取数据集
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                raise ValueError(f"数据集不存在: {dataset_id}")
            
            # 2. 检查当前状态
            if dataset.processing_status != "business_completed":
                raise ValueError(f"数据集状态不允许启动质量分析: {dataset.processing_status}")
            
            # 3. 更新状态为质量分析中
            dataset.processing_status = "quality_analyzing"
            self.repository.save(dataset)
            
            # 4. 异步执行质量分析（这里先返回成功状态，实际分析在后台进行）
            # TODO: 实现异步质量分析逻辑
            
            logger.info(f"质量分析已启动: {dataset_id}")
            return {
                "success": True,
                "message": "质量分析已启动",
                "dataset_id": dataset_id,
                "status": "quality_analyzing"
            }
            
        except Exception as e:
            logger.error(f"启动质量分析失败: {e}")
            raise
    
    async def get_business_analysis_results(self, dataset_id: str) -> Dict[str, Any]:
        """获取业务分析结果
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Dict[str, Any]: 业务分析结果
        """
        try:
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                raise ValueError(f"数据集不存在: {dataset_id}")
            
            # 检查是否有业务分析结果
            if dataset.processing_status not in ["business_completed", "quality_analyzing", "quality_completed"]:
                raise ValueError("业务分析尚未完成")
            
            # 构建业务分析结果
            results = {
                "dataset_id": dataset_id,
                "dataset_name": dataset.name,
                "analysis_time": dataset.upload_time,
                "columns": self._extract_column_info(dataset),
                "business_meaning": dataset.business_meaning_analysis or "暂无业务含义分析结果",
                "control_logic": dataset.control_relationships_analysis or "暂无控制逻辑分析结果",
                "schema_mapping": self._extract_schema_mapping(dataset)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"获取业务分析结果失败: {e}")
            raise
    
    async def get_quality_analysis_results(self, dataset_id: str) -> Dict[str, Any]:
        """获取质量分析结果
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Dict[str, Any]: 质量分析结果
        """
        try:
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                raise ValueError(f"数据集不存在: {dataset_id}")
            
            # 检查是否有质量分析结果
            if dataset.processing_status != "quality_completed":
                raise ValueError("质量分析尚未完成")
            
            # 构建质量分析结果
            results = {
                "dataset_id": dataset_id,
                "dataset_name": dataset.name,
                "analysis_time": dataset.upload_time,
                "overall_score": 85,  # 示例评分
                "quality_metrics": [
                    {"name": "完整性", "score": 90},
                    {"name": "准确性", "score": 85},
                    {"name": "一致性", "score": 80}
                ],
                "detailed_analysis": dataset.detailed_analysis or "暂无详细质量分析结果",
                "recommendations": self._extract_recommendations(dataset)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"获取质量分析结果失败: {e}")
            raise
    
    def _extract_column_info(self, dataset) -> List[Dict[str, Any]]:
        """提取列信息"""
        columns = []
        if hasattr(dataset, 'columns') and dataset.columns:
            for col in dataset.columns:
                # 如果是ColumnMetadata对象，提取name属性
                if hasattr(col, 'name'):
                    column_name = col.name
                    column_type = getattr(col, 'business_meaning', '').lower()
                    # 根据业务含义判断列类型
                    if 'device' in column_type or 'equipment' in column_type:
                        col_type = "device"
                    elif 'time' in column_type or 'timestamp' in column_type or 'date' in column_type:
                        col_type = "time"
                    else:
                        col_type = "business"
                    
                    columns.append({
                        "name": column_name,
                        "type": col_type,
                        "description": getattr(col, 'business_meaning', f"{column_name}列的业务描述")
                    })
                # 如果是字符串，直接使用
                elif isinstance(col, str):
                    columns.append({
                        "name": col,
                        "type": "business",
                        "description": f"{col}列的业务描述"
                    })
        return columns
    
    def _extract_schema_mapping(self, dataset) -> List[Dict[str, Any]]:
        """提取Schema映射"""
        mappings = []
        if hasattr(dataset, 'columns') and dataset.columns:
            for col in dataset.columns:
                # 如果是ColumnMetadata对象，提取属性
                if hasattr(col, 'name'):
                    column_name = col.name
                    chinese_name = getattr(col, 'chinese_name', f"{column_name}_中文")
                    data_type = getattr(col, 'data_type', '数值型')
                    description = getattr(col, 'business_meaning', f"{column_name}的业务描述")
                    
                    mappings.append({
                        "original_name": column_name,
                        "chinese_name": chinese_name,
                        "data_type": data_type,
                        "description": description
                    })
                # 如果是字符串，创建默认映射
                elif isinstance(col, str):
                    mappings.append({
                        "original_name": col,
                        "chinese_name": f"{col}_中文",
                        "data_type": "数值型",
                        "description": f"{col}的业务描述"
                    })
        return mappings
    
    def _extract_recommendations(self, dataset) -> List[Dict[str, Any]]:
        """提取建议列表"""
        return [
            {
                "type": "数据清洗",
                "content": "建议处理缺失值和异常值"
            },
            {
                "type": "格式规范",
                "content": "建议统一时间格式"
            }
        ] 