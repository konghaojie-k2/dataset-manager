#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""认证API路由"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from src.config.settings import get_settings
from src.auth.dingtalk_oauth import DingTalkConfig, DingTalkLogin
from src.auth.user_service import UserService
from src.auth.jwt_utils import jwt_manager
from src.schemas.user import UserCreate, UserResponse, UserLoginResponse


router = APIRouter(prefix="/auth", tags=["认证"])


class AuthUrlRequest(BaseModel):
    """获取授权URL请求"""
    state: Optional[str] = Field(None, description="状态参数")


class AuthUrlResponse(BaseModel):
    """授权URL响应"""
    auth_url: str = Field(..., description="授权URL")


class CallbackRequest(BaseModel):
    """回调请求"""
    code: str = Field(..., description="授权码")
    state: Optional[str] = Field(None, description="状态参数")


@router.get("/dingtalk/url", response_model=AuthUrlResponse)
async def get_dingtalk_auth_url():
    """获取钉钉授权URL"""
    try:
        settings = get_settings()
        
        if not settings.dingtalk_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="钉钉登录未启用"
            )
        
        config = DingTalkConfig()
        auth_url = config.get_auth_url()
        
        logger.info("生成钉钉授权URL")
        return AuthUrlResponse(auth_url=auth_url)
        
    except Exception as e:
        logger.error(f"获取钉钉授权URL失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/dingtalk/callback", response_model=UserLoginResponse)
async def dingtalk_callback(request: CallbackRequest):
    """钉钉OAuth回调处理（接收前端POST请求）"""
    try:
        settings = get_settings()
        
        if not settings.dingtalk_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="钉钉登录未启用"
            )
        
        # 使用钉钉登录管理器
        async with DingTalkLogin() as dingtalk:
            # 完成登录流程
            user_info = await dingtalk.login(code)
            logger.info(f"钉钉用户登录成功: {user_info}")
            
            # 获取或创建用户
            user_service = UserService(settings.metadata_dir / "myauth.db")
            
            # 检查用户是否已存在
            existing_user = user_service.get_user_by_dingtalk_id(user_info["dingtalk_id"])
            
            if existing_user:
                # 更新用户信息
                from ..schemas.user import UserUpdate
                update_data = UserUpdate(
                    username=user_info.get("username"),
                    email=user_info.get("email"),
                    avatar=user_info.get("avatar")
                )
                user = user_service.update_user(existing_user.id, update_data)
                logger.info(f"更新用户信息: {existing_user.id}")
            else:
                # 创建新用户
                create_data = UserCreate(
                    username=user_info.get("username"),
                    email=user_info.get("email"),
                    dingtalk_id=user_info["dingtalk_id"],
                    avatar=user_info.get("avatar")
                )
                user = user_service.create_user(create_data)
                logger.info(f"创建新用户: {user.id}")
            
            # 生成JWT令牌
            access_token = jwt_manager.create_access_token({
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            })
            
            return UserLoginResponse(
                access_token=access_token,
                token_type="bearer",
                user=user
            )
            
    except ValueError as e:
        logger.error(f"钉钉登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"钉钉回调处理异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )


@router.get("/dingtalk/redirect")
async def dingtalk_redirect(code: str, state: Optional[str] = None):
    """钉钉OAuth重定向（用于浏览器重定向到前端）"""
    try:
        settings = get_settings()
        
        # 重定向到前端回调页面，携带code参数
        frontend_url = f"{settings.dingtalk_redirect_uri}?code={code}"
        if state:
            frontend_url += f"&state={state}"
        
        logger.info(f"重定向到前端: {frontend_url}")
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error(f"重定向失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重定向失败"
        )