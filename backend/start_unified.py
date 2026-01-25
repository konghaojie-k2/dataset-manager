#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一启动脚本 - 同时启动 LangGraph 和 FastAPI Extension

LangGraph dev server 在 port 2024
FastAPI Extension 在 port 8000
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

# 修复 Windows 控制台中文乱码问题
if sys.platform == "win32":
    # 设置控制台输出为 UTF-8
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
    # 尝试设置控制台代码页为 UTF-8（需要 Windows 10 1903+）
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except:
        pass

# 设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"

from loguru import logger

# 配置 loguru 使用 UTF-8 编码
logger.remove()  # 移除默认的 handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    enqueue=True  # 异步写入，避免编码问题
)


async def start_langgraph():
    """启动 LangGraph dev server (Port 2024)"""
    backend_dir = Path(__file__).parent

    logger.info("启动 LangGraph dev server (Port 2024)...")

    # 检查 langgraph CLI 是否存在
    import shutil
    langgraph_exe = shutil.which("langgraph")

    # 设置环境变量禁用自动打开浏览器
    env = os.environ.copy()
    env["BROWSER"] = "none"
    # 设置 UTF-8 编码
    env["PYTHONIOENCODING"] = "utf-8"

    if langgraph_exe:
        # 使用系统 langgraph CLI
        cmd = [langgraph_exe, "dev"]
    else:
        # 使用 uv 运行 langgraph
        cmd = ["uv", "run", "langgraph", "dev"]

    # 使用 subprocess 启动 langgraph dev（不等待）
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(backend_dir),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        env=env
    )

    logger.info(f"LangGraph dev server 已启动 (PID: {process.pid})")
    # 不等待进程结束，让它在后台运行


async def start_fastapi():
    """启动 FastAPI Extension (Port 8000)"""
    import uvicorn
    from fastapi_extension import extension_app

    logger.info("启动 FastAPI Extension (Port 8000)...")

    server_config = uvicorn.Config(
        extension_app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        lifespan="on"
    )

    server = uvicorn.Server(server_config)
    await server.serve()


async def main():
    """同时启动两个服务"""
    logger.info("=" * 60)
    logger.info("Dataset Manager - 统一服务器启动")
    logger.info("=" * 60)
    logger.info("LangGraph Agent Server: http://localhost:2024")
    logger.info("FastAPI Extension:      http://localhost:8000")
    logger.info("API 文档:              http://localhost:8000/docs")
    logger.info("=" * 60)

    # 同时运行两个服务
    await asyncio.gather(
        start_langgraph(),
        start_fastapi()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
