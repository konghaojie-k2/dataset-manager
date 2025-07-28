"""通用工具函数"""

import json
from typing import Any, List
from pathlib import Path


def format_size(size_bytes: int) -> str:
    """格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        str: 格式化后的大小字符串
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f}{size_names[i]}"


def safe_json_serialize(obj: Any) -> str:
    """安全的JSON序列化
    
    Args:
        obj: 要序列化的对象
        
    Returns:
        str: JSON字符串
    """
    def default_serializer(o):
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        elif hasattr(o, '__dict__'):
            return o.__dict__
        else:
            return str(o)
    
    return json.dumps(obj, default=default_serializer, ensure_ascii=False, indent=2)


def validate_file_extension(file_path: Path, allowed_extensions: List[str]) -> bool:
    """验证文件扩展名
    
    Args:
        file_path: 文件路径
        allowed_extensions: 允许的扩展名列表
        
    Returns:
        bool: 是否为允许的扩展名
    """
    return file_path.suffix.lower() in [ext.lower() for ext in allowed_extensions] 