"""配置管理模块"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger


class AppConfig(BaseModel):
    """应用配置"""
    
    # 基础配置
    app_name: str = Field(default="Dataset Manager", description="应用名称")
    version: str = Field(default="0.1.0", description="版本号")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器地址")
    port: int = Field(default=8000, description="服务器端口")
    
    # 目录配置
    upload_dir: Path = Field(default=Path("uploads"), description="上传目录")
    metadata_dir: Path = Field(default=Path("metadata"), description="元数据目录")
    logs_dir: Path = Field(default=Path("logs"), description="日志目录")
    
    # DeepSeek API配置
    deepseek_api_key: Optional[str] = Field(default=None, description="DeepSeek API密钥")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", description="DeepSeek API基础URL")
    
    # 文件处理配置
    max_file_size: int = Field(default=100 * 1024 * 1024, description="最大文件大小(字节)")  # 100MB
    allowed_extensions: list = Field(default=[".csv", ".zip"], description="允许的文件扩展名")
    
    # 数据处理配置
    sample_rows: int = Field(default=1000, description="数据采样行数")
    preview_rows: int = Field(default=10, description="预览行数")
    
    class Config:
        env_prefix = "DATASET_MANAGER_"


def load_config() -> AppConfig:
    """加载配置
    
    Returns:
        AppConfig: 应用配置
    """
    config = AppConfig()
    
    # 从环境变量加载配置
    config.debug = os.getenv("DATASET_MANAGER_DEBUG", "false").lower() == "true"
    config.host = os.getenv("DATASET_MANAGER_HOST", config.host)
    config.port = int(os.getenv("DATASET_MANAGER_PORT", str(config.port)))
    
    # 目录配置
    upload_dir = os.getenv("DATASET_MANAGER_UPLOAD_DIR")
    if upload_dir:
        config.upload_dir = Path(upload_dir)
    
    metadata_dir = os.getenv("DATASET_MANAGER_METADATA_DIR")
    if metadata_dir:
        config.metadata_dir = Path(metadata_dir)
    
    logs_dir = os.getenv("DATASET_MANAGER_LOGS_DIR")
    if logs_dir:
        config.logs_dir = Path(logs_dir)
    
    # API配置
    config.deepseek_api_key = os.getenv("DATASET_MANAGER_DEEPSEEK_API_KEY")
    deepseek_base_url = os.getenv("DATASET_MANAGER_DEEPSEEK_BASE_URL")
    if deepseek_base_url:
        config.deepseek_base_url = deepseek_base_url
    
    # 文件处理配置
    max_file_size = os.getenv("DATASET_MANAGER_MAX_FILE_SIZE")
    if max_file_size:
        config.max_file_size = int(max_file_size)
    
    sample_rows = os.getenv("DATASET_MANAGER_SAMPLE_ROWS")
    if sample_rows:
        config.sample_rows = int(sample_rows)
    
    preview_rows = os.getenv("DATASET_MANAGER_PREVIEW_ROWS")
    if preview_rows:
        config.preview_rows = int(preview_rows)
    
    # 创建必要的目录
    config.upload_dir.mkdir(parents=True, exist_ok=True)
    config.metadata_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"配置加载完成: {config.model_dump()}")
    return config


def setup_logging(config: AppConfig):
    """设置日志
    
    Args:
        config: 应用配置
    """
    # 移除默认处理器
    logger.remove()
    
    # 控制台日志
    log_level = "DEBUG" if config.debug else "INFO"
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 文件日志
    log_file = config.logs_dir / "dataset_manager.log"
    logger.add(
        sink=str(log_file),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    # 错误日志
    error_log_file = config.logs_dir / "error.log"
    logger.add(
        sink=str(error_log_file),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成") 