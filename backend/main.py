"""数据管理系统主应用"""

from src.server import app
from src.config.settings import get_settings

# 全局配置
config = get_settings()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )
