"""MCP相关的数据结构定义"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MCPServerType(str, Enum):
    """MCP服务器类型枚举"""
    DATABASE = "database"
    API = "api"
    FILE_SYSTEM = "file_system"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    CUSTOM = "custom"


class MCPServerStatus(str, Enum):
    """MCP服务器状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"


class MCPServerConfig(BaseModel):
    """MCP服务器配置模型"""
    name: str = Field(description="服务器名称")
    type: MCPServerType = Field(description="服务器类型")
    description: Optional[str] = Field(None, description="服务器描述")
    
    # 连接配置
    config: Dict[str, Any] = Field(default_factory=dict, description="连接配置")
    
    # 认证配置
    auth_config: Optional[Dict[str, Any]] = Field(None, description="认证配置")
    
    # 超时设置
    timeout: int = Field(default=30, description="超时时间(秒)")
    retry_count: int = Field(default=3, description="重试次数")
    
    # 是否自动启动
    auto_start: bool = Field(default=False, description="是否自动启动")


class MCPServerInfo(BaseModel):
    """MCP服务器信息模型"""
    name: str = Field(description="服务器名称")
    type: MCPServerType = Field(description="服务器类型")
    status: MCPServerStatus = Field(description="服务器状态")
    description: Optional[str] = Field(None, description="服务器描述")
    
    # 时间信息
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(None, description="启动时间")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")
    
    # 统计信息
    total_requests: int = Field(default=0, description="总请求数")
    successful_requests: int = Field(default=0, description="成功请求数")
    failed_requests: int = Field(default=0, description="失败请求数")
    
    # 错误信息
    last_error: Optional[str] = Field(None, description="最后错误信息")
    
    # 可用工具
    available_tools: List[str] = Field(default_factory=list, description="可用工具列表")


class MCPToolSchema(BaseModel):
    """MCP工具模式模型"""
    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    parameters: Dict[str, Any] = Field(description="参数模式")
    required_parameters: List[str] = Field(default_factory=list, description="必需参数")
    return_type: Optional[str] = Field(None, description="返回类型")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="使用示例")


class MCPToolCall(BaseModel):
    """MCP工具调用模型"""
    server_name: str = Field(description="服务器名称")
    tool_name: str = Field(description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="调用参数")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")


class MCPToolResult(BaseModel):
    """MCP工具调用结果模型"""
    call_id: str = Field(description="调用ID")
    server_name: str = Field(description="服务器名称")
    tool_name: str = Field(description="工具名称")
    
    # 执行信息
    success: bool = Field(description="是否成功")
    execution_time: float = Field(description="执行时间(秒)")
    timestamp: datetime = Field(description="执行时间戳")
    
    # 结果数据
    result: Optional[Any] = Field(None, description="执行结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class DatabaseConnectionConfig(BaseModel):
    """数据库连接配置模型"""
    type: str = Field(description="数据库类型")
    host: str = Field(description="主机地址")
    port: int = Field(description="端口")
    database: str = Field(description="数据库名")
    username: str = Field(description="用户名")
    password: str = Field(description="密码")
    
    # 连接池配置
    max_connections: int = Field(default=10, description="最大连接数")
    min_connections: int = Field(default=1, description="最小连接数")
    
    # SSL配置
    ssl_enabled: bool = Field(default=False, description="是否启用SSL")
    ssl_config: Optional[Dict[str, Any]] = Field(None, description="SSL配置")


class APIConnectionConfig(BaseModel):
    """API连接配置模型"""
    base_url: str = Field(description="基础URL")
    auth_type: str = Field(default="none", description="认证类型")
    
    # 认证信息
    api_key: Optional[str] = Field(None, description="API密钥")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    token: Optional[str] = Field(None, description="访问令牌")
    
    # 请求配置
    default_headers: Dict[str, str] = Field(default_factory=dict, description="默认请求头")
    timeout: int = Field(default=30, description="请求超时(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    
    # 限流配置
    rate_limit: Optional[int] = Field(None, description="速率限制(请求/秒)")


class MCPHealthCheck(BaseModel):
    """MCP健康检查模型"""
    server_name: str = Field(description="服务器名称")
    status: str = Field(description="健康状态")
    response_time: float = Field(description="响应时间(毫秒)")
    timestamp: datetime = Field(description="检查时间")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    
    # 连接信息
    connection_status: str = Field(description="连接状态")
    last_successful_connection: Optional[datetime] = Field(None, description="最后成功连接时间")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")


class MCPMetrics(BaseModel):
    """MCP指标模型"""
    server_name: str = Field(description="服务器名称")
    
    # 请求统计
    total_requests: int = Field(description="总请求数")
    successful_requests: int = Field(description="成功请求数")
    failed_requests: int = Field(description="失败请求数")
    
    # 性能指标
    average_response_time: float = Field(description="平均响应时间(毫秒)")
    min_response_time: float = Field(description="最小响应时间(毫秒)")
    max_response_time: float = Field(description="最大响应时间(毫秒)")
    
    # 时间范围
    start_time: datetime = Field(description="统计开始时间")
    end_time: datetime = Field(description="统计结束时间")
    
    # 工具使用统计
    tool_usage: Dict[str, int] = Field(default_factory=dict, description="工具使用次数")
    
    # 错误统计
    error_types: Dict[str, int] = Field(default_factory=dict, description="错误类型统计") 