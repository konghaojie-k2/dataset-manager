"""数据集应用服务层"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import UploadFile
from loguru import logger

from ..schemas.dataset import (
    DatasetMetadata, 
    MetadataExtractionRequest,
    TagUpdateRequest,
    ColumnMetadata
)
from .dataset_repository import DatasetRepository
from .file_service import FileService
from .metadata_service import MetadataService
from ..graph.workflow import run_industrial_analysis
from ..tools.report_manager import report_manager
from ..utils import (
    convert_numpy_types,
    build_base_results,
    extract_column_info,
    extract_schema_mapping,
    safe_update_dataset_status,
    get_dataset_with_validation,
    get_dataset_by_id
)


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
            
            # 2. 获取基础列信息（用于前端显示）
            basic_columns = []
            try:
                # 尝试提取CSV文件并获取列信息
                csv_files = self.file_service.extract_csv_files(file_path)
                if csv_files:
                    # 只读取前几行来获取列名，不加载全部数据
                    df_sample = self.file_service.load_csv_data(csv_files[0], sample_rows=5)
                    if df_sample is not None:
                        # 创建基础的ColumnMetadata对象
                        for col_name in df_sample.columns:
                            basic_columns.append(ColumnMetadata(
                                name=col_name,
                                data_type=str(df_sample[col_name].dtype),
                                business_meaning="",  # 业务分析时填充
                                is_device_id=False,  # 业务分析时确定
                                is_timestamp=False,  # 业务分析时确定
                                null_count=0,  # 业务分析时计算
                                unique_count=0,  # 业务分析时计算
                                sample_values=[]  # 业务分析时填充
                            ))
                        logger.info(f"成功获取基础列信息: {len(basic_columns)} 列")
                    
                    # 清理临时文件
                    self.file_service.file_processor.cleanup_extracted_files(file_path)
                        
            except Exception as e:
                logger.warning(f"获取基础列信息失败: {e}")
                # 不影响上传流程，继续执行
            
            # 3. 创建数据集元数据
            dataset = DatasetMetadata(
                id=file_id,
                name=file.filename,
                description="",  # 将由LLM生成
                file_path=str(file_path),
                file_size=file_info['file_size'],
                upload_time=datetime.now(),
                columns=basic_columns,  # 使用获取到的基础列信息
                processing_status="uploaded"
            )
            
            # 4. 保存初始元数据
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
            dataset = get_dataset_by_id(self.repository, dataset_id, "元数据提取")
            
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
            
            # 从data_info中提取列信息并转换为columns_metadata格式
            data_info = extraction_result.get("basic_info", {})
            if data_info and "columns" in data_info:
                columns_metadata = []
                for col_name in data_info["columns"]:
                    # 从dtypes中获取数据类型
                    dtype = data_info.get("dtypes", {}).get(col_name, "unknown")
                    null_count = data_info.get("null_counts", {}).get(col_name, 0)
                    
                    columns_metadata.append({
                        "name": col_name,
                        "dtype": dtype,
                        "business_meaning": f"列 {col_name}",
                        "is_device_id": "id" in col_name.lower() or "device" in col_name.lower(),
                        "is_timestamp": "time" in col_name.lower() or "date" in col_name.lower(),
                        "null_count": null_count,
                        "unique_count": 0,  # 暂时设为0，可以从column_analyses中获取
                        "sample_values": []
                    })
                
                # 添加columns_metadata到extraction_result
                extraction_result["columns_metadata"] = columns_metadata
            
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
        # 使用复用的数据集获取方法
        dataset = get_dataset_by_id(self.repository, request.dataset_id, "标签更新")
        
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
            # 使用复用的数据集获取方法
            dataset = get_dataset_by_id(self.repository, dataset_id, "数据预览")
            
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
            
            # 1. 获取数据集并验证状态，同时更新为分析中状态
            dataset = get_dataset_with_validation(
                self.repository,
                dataset_id,
                ["uploaded"],
                "业务分析",
                update_status="business_analyzing"
            )
            
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
            
            # 从data_info中提取列信息并转换为columns_metadata格式
            data_info = extraction_result.get("basic_info", {})
            if data_info and "columns" in data_info:
                columns_metadata = []
                for col_name in data_info["columns"]:
                    # 从dtypes中获取数据类型
                    dtype = data_info.get("dtypes", {}).get(col_name, "unknown")
                    null_count = data_info.get("null_counts", {}).get(col_name, 0)
                    
                    columns_metadata.append({
                        "name": col_name,
                        "dtype": dtype,
                        "business_meaning": f"列 {col_name}",
                        "is_device_id": "id" in col_name.lower() or "device" in col_name.lower(),
                        "is_timestamp": "time" in col_name.lower() or "date" in col_name.lower(),
                        "null_count": null_count,
                        "unique_count": 0,  # 暂时设为0，可以从column_analyses中获取
                        "sample_values": []
                    })
                
                # 添加columns_metadata到extraction_result
                extraction_result["columns_metadata"] = columns_metadata
            
            # 更新数据集元数据
            updated_dataset = self.metadata_service.update_dataset_metadata(dataset, extraction_result)
            
            # 更新状态为业务分析完成
            updated_dataset.processing_status = "business_completed"
            
            # 保存更新后的数据集
            self.repository.save(updated_dataset)
            
            # 保存业务分析结果到分离存储
            try:
                business_results = {
                    "device_time_identification": extraction_result.get("device_time_identification"),
                    "business_meaning_analysis": extraction_result.get("business_meaning_analysis"),
                    "control_relationships_analysis": extraction_result.get("control_relationships_analysis"),
                    "basic_analysis": extraction_result.get("basic_analysis"),
                    "detailed_analysis": extraction_result.get("detailed_analysis"),
                    "insights": extraction_result.get("insights", []),
                    "recommendations": extraction_result.get("recommendations"),
                    "column_analyses": extraction_result.get("column_analyses", {}),
                    "columns_metadata": extraction_result.get("columns_metadata", [])
                }
                # 过滤掉None值
                business_results = {k: v for k, v in business_results.items() if v is not None}
                
                self.repository.save_business_analysis_results(dataset_id, business_results)
                logger.info(f"业务分析结果已保存到分离存储: {dataset_id}")
            except Exception as e:
                logger.warning(f"保存业务分析结果到分离存储失败: {e}")
            
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
            # 安全地更新状态为失败
            safe_update_dataset_status(self.repository, dataset_id, "analysis_failed")
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
            
            # 1. 获取数据集并验证状态，同时更新为分析中状态
            dataset = get_dataset_with_validation(
                self.repository,
                dataset_id,
                ["business_completed"],
                "质量分析",
                update_status="quality_analyzing"
            )
            
            # 4. 启动数据质量分析工作流
            logger.info(f"开始执行质量分析: {dataset_id}")
            
            # 导入数据质量分析工作流
            from ..graph.data_quality_workflow import DataQualityWorkflow
            from ..schemas.data_quality import QualityAnalysisRequest
            from ..llms import get_reasoning_llm
            
            # 创建LLM实例
            llm = get_reasoning_llm()
            
            # 创建工作流实例
            workflow = DataQualityWorkflow(llm)
            
            # 创建分析请求
            request = QualityAnalysisRequest(
                dataset_id=dataset_id,
                user_requirements="进行全面的数据质量分析，重点关注时间序列数据的连续性和参数数据的合理性"
            )
            
            # 执行分析工作流
            response = await workflow.run_analysis(request)
            
            if response.status == "completed" and response.report:
                # 5. 重新获取数据集以确保最新状态
                dataset = self.repository.get_by_id(dataset_id)
                if not dataset:
                    raise ValueError(f"数据集不存在: {dataset_id}")
                
                # 更新状态为质量分析完成
                dataset.processing_status = "quality_completed"
                
                # 保存质量分析结果
                quality_results = {
                    "overall_score": response.report.overall_score,
                    "quality_level": response.report.quality_level.value,
                    "time_columns": [col.dict() for col in response.report.time_columns],
                    "parameter_columns": [col.dict() for col in response.report.parameter_columns],
                    "category_columns": [col.dict() for col in response.report.category_columns],
                    "key_issues": response.report.key_issues,
                    "recommendations": response.report.recommendations,
                    "summary": response.report.summary,
                    "analysis_time": response.report.created_at.isoformat(),
                    "processing_time": response.processing_time
                }
                
                # 更新数据集的质量分析结果
                dataset.quality_analysis_results = quality_results
                self.repository.save(dataset)
                
                # 保存质量分析结果到分离存储
                try:
                    self.repository.save_quality_analysis_results(dataset_id, quality_results)
                    logger.info(f"质量分析结果已保存到分离存储: {dataset_id}")
                except Exception as e:
                    logger.warning(f"保存质量分析结果到分离存储失败: {e}")
                
                # 保存质量分析结果为MD文件
                try:
                    from ..tools.report_manager import ReportManager
                    report_manager = ReportManager()
                    saved_files = report_manager.save_quality_analysis_report(
                        dataset_id=dataset_id,
                        dataset_name=dataset.name,
                        quality_results=quality_results
                    )
                    logger.info(f"质量分析报告已保存为MD文件: {len(saved_files)} 个文件")
                except Exception as e:
                    logger.warning(f"保存质量分析报告文件失败: {e}")
                    # 不影响主流程，继续执行
                
                logger.info(f"质量分析完成: {dataset_id}, 整体得分: {response.report.overall_score:.1f}")
                
                return {
                    "success": True,
                    "message": "质量分析完成",
                    "dataset_id": dataset_id,
                    "status": "quality_completed",
                    "overall_score": response.report.overall_score,
                    "quality_level": response.report.quality_level.value,
                    "processing_time": response.processing_time
                }
            else:
                # 分析失败
                dataset.processing_status = "quality_failed"
                self.repository.save(dataset)
                
                error_msg = response.error_message or "质量分析失败"
                logger.error(f"质量分析失败: {dataset_id}, 错误: {error_msg}")
                
                return {
                    "success": False,
                    "message": f"质量分析失败: {error_msg}",
                    "dataset_id": dataset_id,
                    "status": "quality_failed"
                }
            
        except Exception as e:
            logger.error(f"启动质量分析失败: {e}")
            # 安全地更新状态为失败
            safe_update_dataset_status(self.repository, dataset_id, "quality_failed")
            raise
    


    async def get_business_analysis_results(self, dataset_id: str) -> Dict[str, Any]:
        """获取业务分析结果
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Dict[str, Any]: 业务分析结果
        """
        try:
            # 使用复用的验证方法
            dataset = get_dataset_with_validation(
                self.repository,
                dataset_id, 
                ["business_completed", "quality_analyzing", "quality_completed"],
                "业务分析"
            )
            
            # 从分离存储获取业务分析结果
            business_results = self.repository.get_business_analysis_results(dataset_id)
            
            # 构建业务分析结果
            results = build_base_results(dataset)
            
            if business_results:
                results.update({
                    "columns": extract_column_info(dataset),
                    "business_meaning": business_results.get("business_meaning_analysis", "暂无业务含义分析结果"),
                    "control_logic": business_results.get("control_relationships_analysis", "暂无控制逻辑分析结果"),
                    "schema_mapping": extract_schema_mapping(dataset),
                    "device_time_identification": business_results.get("device_time_identification"),
                    "basic_analysis": business_results.get("basic_analysis"),
                    "detailed_analysis": business_results.get("detailed_analysis"),
                    "insights": business_results.get("insights", []),
                    "recommendations": business_results.get("recommendations"),
                    "column_analyses": business_results.get("column_analyses", {}),
                    "columns_metadata": business_results.get("columns_metadata", [])
                })
            else:
                # 兼容旧数据：从dataset对象获取
                results.update({
                    "columns": extract_column_info(dataset),
                    "business_meaning": dataset.business_meaning_analysis or "暂无业务含义分析结果",
                    "control_logic": dataset.control_relationships_analysis or "暂无控制逻辑分析结果",
                    "schema_mapping": extract_schema_mapping(dataset)
                })
            
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
            # 使用复用的验证方法
            dataset = get_dataset_with_validation(
                self.repository,
                dataset_id,
                ["quality_completed"],
                "质量分析"
            )
            
            # 从分离存储获取质量分析结果
            quality_results = self.repository.get_quality_analysis_results(dataset_id)
            
            # 构建基础结果
            results = build_base_results(dataset)
            
            # 返回实际的质量分析结果
            if quality_results:
                # 转换numpy类型为Python原生类型
                quality_results = convert_numpy_types(quality_results)
                results.update(quality_results)
            elif dataset.quality_analysis_results:
                # 兼容旧数据：从dataset对象获取
                quality_results = convert_numpy_types(dataset.quality_analysis_results)
                results.update(quality_results)
            else:
                # 如果没有质量分析结果，返回默认结果
                results.update({
                    "overall_score": 85,  # 示例评分
                    "quality_level": "good",
                    "time_columns": [],
                    "parameter_columns": [],
                    "category_columns": [],
                    "key_issues": ["暂无质量分析结果"],
                    "recommendations": ["请重新运行质量分析"],
                    "summary": {
                        "column_breakdown": {
                            "time_columns": 0,
                            "parameter_columns": 0,
                            "category_columns": 0
                        }
                    }
                })
            
            return results
            
        except Exception as e:
            logger.error(f"获取质量分析结果失败: {e}")
            raise
    

    
 