"""数据集服务相关的工具函数"""

from typing import Dict, List, Optional, Any
import numpy as np
from loguru import logger

from ..schemas.dataset import DatasetMetadata


def convert_numpy_types(data: Any) -> Any:
    """递归转换numpy类型为Python原生类型
    
    Args:
        data: 包含numpy类型的数据
        
    Returns:
        Any: 转换后的数据
    """
    if isinstance(data, dict):
        return {key: convert_numpy_types(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_types(item) for item in data]
    elif isinstance(data, np.bool_):
        return bool(data)
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    else:
        return data


def build_base_results(dataset: DatasetMetadata) -> Dict[str, Any]:
    """构建基础结果结构
    
    Args:
        dataset: 数据集元数据
        
    Returns:
        Dict[str, Any]: 基础结果结构
    """
    return {
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "analysis_time": dataset.upload_time.isoformat()
    }


def extract_column_info(dataset: DatasetMetadata) -> List[Dict[str, Any]]:
    """提取列信息
    
    Args:
        dataset: 数据集元数据
        
    Returns:
        List[Dict[str, Any]]: 列信息列表
    """
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


def extract_schema_mapping(dataset: DatasetMetadata) -> List[Dict[str, Any]]:
    """提取Schema映射
    
    Args:
        dataset: 数据集元数据
        
    Returns:
        List[Dict[str, Any]]: Schema映射列表
    """
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


def safe_update_dataset_status(repository, dataset_id: str, status: str) -> None:
    """安全地更新数据集状态（用于错误处理）
    
    Args:
        repository: 数据集仓库实例
        dataset_id: 数据集ID
        status: 新状态
    """
    try:
        dataset = repository.get_by_id(dataset_id)
        if dataset:
            dataset.processing_status = status
            repository.save(dataset)
    except Exception as e:
        logger.warning(f"更新数据集状态失败: {e}")
        # 不抛出异常，避免掩盖原始错误


def get_dataset_with_validation(repository, dataset_id: str, required_status: List[str], 
                               operation_name: str, update_status: Optional[str] = None) -> DatasetMetadata:
    """获取数据集并验证状态
    
    Args:
        repository: 数据集仓库实例
        dataset_id: 数据集ID
        required_status: 要求的状态列表
        operation_name: 操作名称（用于错误信息）
        update_status: 可选的新状态，如果提供则更新数据集状态
        
    Returns:
        DatasetMetadata: 验证通过的数据集
        
    Raises:
        ValueError: 数据集不存在或状态不符合要求
    """
    dataset = repository.get_by_id(dataset_id)
    if not dataset:
        raise ValueError(f"数据集不存在: {dataset_id}")
    
    if dataset.processing_status not in required_status:
        if update_status:
            raise ValueError(f"数据集状态不允许启动{operation_name}: {dataset.processing_status}")
        else:
            raise ValueError(f"{operation_name}尚未完成，当前状态: {dataset.processing_status}")
    
    # 如果需要更新状态
    if update_status:
        dataset.processing_status = update_status
        repository.save(dataset)
    
    return dataset


def get_dataset_by_id(repository, dataset_id: str, operation_name: str = "操作") -> DatasetMetadata:
    """获取数据集（简单版本，只检查存在性）
    
    Args:
        repository: 数据集仓库实例
        dataset_id: 数据集ID
        operation_name: 操作名称（用于错误信息）
        
    Returns:
        DatasetMetadata: 数据集元数据
        
    Raises:
        ValueError: 数据集不存在
    """
    dataset = repository.get_by_id(dataset_id)
    if not dataset:
        raise ValueError(f"数据集不存在: {dataset_id}")
    return dataset 