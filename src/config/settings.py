"""配置管理模块"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量文件
load_dotenv()


class Settings(BaseModel):
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
    
    # LLM配置
    deepseek_api_key: Optional[str] = Field(default=None, description="DeepSeek API密钥")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", description="DeepSeek API基础URL")
    
    # LLM模型配置
    reasoning_model: str = Field(default="deepseek-chat", description="推理模型")
    basic_model: str = Field(default="deepseek-chat", description="基础模型")
    vision_model: str = Field(default="deepseek-chat", description="视觉模型")
    
    # LLM参数配置
    llm_temperature: float = Field(default=0.1, description="LLM温度参数")
    llm_max_tokens: Optional[int] = Field(default=None, description="LLM最大token数")
    
    # 文件处理配置
    max_file_size: int = Field(default=100 * 1024 * 1024, description="最大文件大小(字节)")  # 100MB
    allowed_extensions: list = Field(default=[".csv", ".zip"], description="允许的文件扩展名")
    
    # 版本控制配置
    version_control_enabled: bool = Field(default=True, description="是否启用版本控制")
    duplicate_detection_enabled: bool = Field(default=True, description="是否启用重复检测")
    duplicate_storage_strategy: str = Field(default="reject", description="重复数据存储策略: full, reference, reject")
    auto_cleanup_enabled: bool = Field(default=True, description="是否启用自动清理")
    default_keep_versions: int = Field(default=5, description="默认保留版本数量")
    
    # 数据处理配置
    sample_rows: int = Field(default=1000, description="数据采样行数")
    preview_rows: int = Field(default=10, description="预览行数")
    
    class Config:
        env_prefix = "DATASET_MANAGER_"


def get_settings() -> Settings:
    """获取配置实例
    
    Returns:
        Settings: 应用配置
    """
    config = Settings()
    
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
    
    # LLM配置
    config.deepseek_api_key = os.getenv("DATASET_MANAGER_DEEPSEEK_API_KEY")
    deepseek_base_url = os.getenv("DATASET_MANAGER_DEEPSEEK_BASE_URL")
    if deepseek_base_url:
        config.deepseek_base_url = deepseek_base_url
    
    # LLM模型配置
    reasoning_model = os.getenv("DATASET_MANAGER_REASONING_MODEL")
    if reasoning_model:
        config.reasoning_model = reasoning_model
    
    basic_model = os.getenv("DATASET_MANAGER_BASIC_MODEL")
    if basic_model:
        config.basic_model = basic_model
    
    vision_model = os.getenv("DATASET_MANAGER_VISION_MODEL")
    if vision_model:
        config.vision_model = vision_model
    
    # LLM参数配置
    llm_temperature = os.getenv("DATASET_MANAGER_LLM_TEMPERATURE")
    if llm_temperature:
        config.llm_temperature = float(llm_temperature)
    
    llm_max_tokens = os.getenv("DATASET_MANAGER_LLM_MAX_TOKENS")
    if llm_max_tokens:
        config.llm_max_tokens = int(llm_max_tokens)
    
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


def setup_logging(config: Settings):
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