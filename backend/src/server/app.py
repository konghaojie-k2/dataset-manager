"""FastAPI应用核心配置"""

import matplotlib
matplotlib.use('Agg')  # 设置matplotlib后端
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 中文字体支持
plt.rcParams['axes.unicode_minus'] = False  # 负号正常显示

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from loguru import logger

from src.config.settings import get_settings, setup_logging
from src.core.dataset_service_factory import create_dataset_service
from src.core.tag_service import TagService
from .routes import router
from .api.v1.reports import router as reports_router
from .api.v1.tags import router as tags_router
from .api.v1.version_control import router as version_control_router
from .api.v1.lineage import router as lineage_router
from .api.v1.chat import router as chat_router
from .dependencies import set_dataset_service, set_tag_service
from .middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware


# 全局配置
config = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    
    # 启动时初始化
    setup_logging(config)
    logger.info("数据管理系统启动中...")
    
    # 检查DeepSeek API密钥
    if not config.deepseek_api_key:
        logger.warning("未设置DeepSeek API密钥，请设置环境变量 DATASET_MANAGER_DEEPSEEK_API_KEY")
        raise HTTPException(
            status_code=500, 
            detail="DeepSeek API密钥未配置，请设置环境变量 DATASET_MANAGER_DEEPSEEK_API_KEY"
        )
    
    # 初始化数据集服务（自动选择Supabase或本地存储）
    dataset_service_instance = create_dataset_service()
    
    # 设置依赖注入
    set_dataset_service(dataset_service_instance)
    
    # 初始化标签服务
    tag_service_instance = TagService(metadata_dir=config.metadata_dir)
    set_tag_service(tag_service_instance)
    
    # 更新路由模块中的服务实例（向后兼容）
    from . import routes
    routes.dataset_service = dataset_service_instance
    routes.tag_service = tag_service_instance
    
    logger.info("数据管理系统启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("数据管理系统关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    # 创建FastAPI应用
    app = FastAPI(
        title=config.app_name,
        description="基于LangGraph的智能数据管理系统",
        version=config.version,
        lifespan=lifespan
    )

    # 添加中间件
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境中应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(router)
    app.include_router(reports_router)
    app.include_router(tags_router)
    app.include_router(version_control_router)
    app.include_router(lineage_router)
    app.include_router(chat_router)  # 聊天路由

    # 静态文件服务（如果有前端文件）
    web_dir = Path("web")
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir / "static")), name="static")
        app.mount("/assets", StaticFiles(directory=str(web_dir / "assets")), name="assets")

    @app.get("/")
    async def root():
        """根路径 - 返回前端页面"""
        web_index = Path("web/index.html")
        if web_index.exists():
            return FileResponse(str(web_index))
        else:
            return {
                "message": "欢迎使用数据管理系统",
                "version": config.version,
                "docs": "/docs",
                "health": "/api/v1/health"
            }
    
    @app.get("/api")
    async def api_info():
        """API信息"""
        return {
            "message": "欢迎使用数据管理系统API",
            "version": config.version,
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    return app


# 创建应用实例
app = create_app() 