"""数据管理系统主应用"""

import matplotlib
matplotlib.use('Agg')  # 设置matplotlib后端
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 中文字体支持
plt.rcParams['axes.unicode_minus'] = False  # 负号正常显示

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from loguru import logger

from src.dataset_manager.utils.config import load_config, setup_logging
from src.dataset_manager.core.dataset_service import DatasetService
from src.dataset_manager.api.routes import router, dataset_service


# 全局配置
config = load_config()


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
    
    # 初始化数据集服务
    global dataset_service
    from src.dataset_manager.api.routes import dataset_service as ds
    ds = DatasetService(
        upload_dir=config.upload_dir,
        metadata_dir=config.metadata_dir,
        deepseek_api_key=config.deepseek_api_key
    )
    
    # 将服务实例设置为全局变量
    import src.dataset_manager.api.routes as routes_module
    routes_module.dataset_service = ds
    
    logger.info("数据管理系统启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("数据管理系统关闭")


# 创建FastAPI应用
app = FastAPI(
    title=config.app_name,
    description="基于LangGraph的智能数据管理系统",
    version=config.version,
    lifespan=lifespan
)

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

# 静态文件服务（如果有前端文件）
web_dir = Path("web")
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用数据管理系统",
        "version": config.version,
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )
