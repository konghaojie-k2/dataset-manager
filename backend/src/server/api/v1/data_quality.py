"""数据质量分析API端点"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from loguru import logger

from ....schemas.data_quality import (
    QualityAnalysisRequest, QualityAnalysisResponse, DataQualityReport,
    ColumnType
)
from ....core.business_analysis_service import BusinessAnalysisService
from ....core.dataset_service_factory import create_dataset_service
from pathlib import Path

router = APIRouter(prefix="/data-quality", tags=["数据质量"])

# 全局业务分析服务实例
_business_service = None


def get_business_service() -> BusinessAnalysisService:
    """获取业务分析服务实例"""
    global _business_service
    if _business_service is None:
        _business_service = BusinessAnalysisService()
    return _business_service


@router.post("/analyze", response_model=QualityAnalysisResponse)
async def analyze_data_quality(
    request: QualityAnalysisRequest,
    business_service: BusinessAnalysisService = Depends(get_business_service)
) -> QualityAnalysisResponse:
    """
    分析数据质量
    
    执行完整的数据质量分析流程：
    1. 加载数据
    2. 检测列类型
    3. 分析各类型列的质量
    4. 生成质量报告和建议
    """
    try:
        logger.info(f"收到数据质量分析请求: {request.dataset_id}")
        
        # 获取数据集
        dataset_service = create_dataset_service()
        dataset = dataset_service.get_dataset(request.dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail=f"数据集不存在: {request.dataset_id}")
        
        # 获取文件路径
        file_path = Path(dataset.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"数据文件不存在: {file_path}")
        
        # 运行质量分析
        analysis_result = await business_service.run_quality_analysis(
            dataset_id=request.dataset_id,
            file_path=file_path,
            user_requirements=request.user_requirements or ""
        )
        
        if analysis_result.get("status") != "completed":
            raise HTTPException(status_code=500, detail=f"质量分析失败: {analysis_result.get('errors', [])}")
        
        # 转换为响应格式
        report = analysis_result.get("report", {})
        from ....schemas.data_quality import QualityReport
        quality_report = QualityReport(
            overall_score=report.get("overall_score", 0),
            quality_level=report.get("quality_level", "unknown"),
            completeness=report.get("completeness", 0),
            accuracy=report.get("accuracy", 0),
            consistency=report.get("consistency", 0),
            timeliness=report.get("timeliness", 0),
            key_issues=report.get("key_issues", []),
            recommendations=report.get("recommendations", []),
            parameter_columns=[],
            time_series_columns=[]
        )
        
        import uuid
        response = QualityAnalysisResponse(
            request_id=str(uuid.uuid4()),
            dataset_id=request.dataset_id,
            status="completed",
            report=quality_report
        )
        
        logger.info(f"数据质量分析完成: {response.request_id}, 状态: {response.status}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"数据质量分析失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/analyze-async")
async def analyze_data_quality_async(
    request: QualityAnalysisRequest,
    background_tasks: BackgroundTasks,
    business_service: BusinessAnalysisService = Depends(get_business_service)
) -> Dict[str, str]:
    """
    异步分析数据质量
    
    启动后台任务进行数据质量分析，立即返回任务ID
    """
    try:
        import uuid
        task_id = str(uuid.uuid4())
        
        logger.info(f"启动异步数据质量分析任务: {task_id}")
        
        # 添加后台任务
        background_tasks.add_task(
            _run_async_analysis,
            task_id,
            request,
            business_service
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "数据质量分析任务已启动"
        }
        
    except Exception as e:
        error_msg = f"启动异步分析失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/column-types/{dataset_id}")
async def detect_column_types(
    dataset_id: str
) -> Dict[str, Any]:
    """
    检测数据集的列类型
    
    自动分析数据集中各列的类型（时间列、参数列、类目列）
    """
    try:
        logger.info(f"检测列类型: {dataset_id}")
        
        from ....tools.data_quality_analyzer import DataQualityAnalyzer
        from pathlib import Path
        
        # 创建分析器并加载数据
        analyzer = DataQualityAnalyzer()
        file_path = Path(f"uploads/{dataset_id}.csv")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"数据文件不存在: {dataset_id}")
        
        analyzer.load_data(file_path)
        
        # 检测列类型
        column_types = analyzer.auto_detect_column_types()
        
        # 转换为字符串格式
        column_types_str = {col: col_type.value for col, col_type in column_types.items()}
        
        # 获取基本统计信息
        basic_info = {
            "total_columns": len(analyzer.data.columns),
            "total_rows": len(analyzer.data),
            "column_types_count": {
                "time": sum(1 for t in column_types.values() if t == ColumnType.TIME),
                "parameter": sum(1 for t in column_types.values() if t == ColumnType.PARAMETER),
                "category": sum(1 for t in column_types.values() if t == ColumnType.CATEGORY)
            }
        }
        
        return {
            "dataset_id": dataset_id,
            "column_types": column_types_str,
            "basic_info": basic_info
        }
        
    except Exception as e:
        error_msg = f"列类型检测失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/report/{analysis_id}")
async def get_quality_report(analysis_id: str) -> Dict[str, Any]:
    """
    获取数据质量分析报告
    
    根据分析ID获取完整的质量分析报告
    """
    try:
        logger.info(f"获取质量报告: {analysis_id}")
        
        # 这里应该从数据库或缓存中获取报告
        # 暂时返回示例响应
        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "message": "报告获取功能待实现，需要集成数据存储"
        }
        
    except Exception as e:
        error_msg = f"获取质量报告失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """健康检查"""
    return {
        "status": "healthy",
        "service": "data-quality-api",
        "message": "数据质量分析服务运行正常"
    }


async def _run_async_analysis(
    task_id: str,
    request: QualityAnalysisRequest,
    business_service: BusinessAnalysisService
):
    """运行异步分析任务"""
    try:
        logger.info(f"开始执行异步分析任务: {task_id}")
        
        # 获取数据集
        dataset_service = create_dataset_service()
        dataset = dataset_service.get_dataset(request.dataset_id)
        if not dataset:
            raise ValueError(f"数据集不存在: {request.dataset_id}")
        
        # 获取文件路径
        file_path = Path(dataset.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
        
        # 运行质量分析
        analysis_result = await business_service.run_quality_analysis(
            dataset_id=request.dataset_id,
            file_path=file_path,
            user_requirements=request.user_requirements or ""
        )
        
        # 这里应该将结果保存到数据库或缓存
        logger.info(f"异步分析任务完成: {task_id}, 状态: {analysis_result.get('status')}")
        
        # TODO: 保存结果到数据库
        # TODO: 发送通知给用户
        
    except Exception as e:
        logger.error(f"异步分析任务失败: {task_id}, 错误: {str(e)}")
        # TODO: 更新任务状态为失败 