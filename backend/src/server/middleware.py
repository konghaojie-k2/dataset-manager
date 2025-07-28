"""服务器中间件"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]
        
        # 记录请求开始
        start_time = time.time()
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - 开始处理请求"
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"状态码: {response.status_code}, 耗时: {process_time:.3f}s"
            )
            
            # 添加请求ID到响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录错误
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"请求处理失败: {str(e)}, 耗时: {process_time:.3f}s"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response 