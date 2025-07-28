"""服务器模块

提供FastAPI应用、路由、中间件和依赖注入功能
"""

from .app import app, create_app
from .routes import router
from .dependencies import get_dataset_service, set_dataset_service
from .middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

__all__ = [
    "app",
    "create_app", 
    "router",
    "get_dataset_service",
    "set_dataset_service",
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware",
] 