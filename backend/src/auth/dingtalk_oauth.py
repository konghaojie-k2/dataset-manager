#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""钉钉OAuth2.0认证模块"""

import json
import hmac
import hashlib
import base64
import time
from typing import Dict, Optional, Any
from datetime import datetime
from loguru import logger
import httpx

from ..config.settings import get_settings


class DingTalkConfig:
    """钉钉OAuth配置"""
    
    def __init__(self):
        """初始化配置"""
        settings = get_settings()
        self.app_key = settings.dingtalk_app_key
        self.app_secret = settings.dingtalk_app_secret
        self.redirect_uri = settings.dingtalk_redirect_uri
        self.enabled = settings.dingtalk_enabled
        
        if self.enabled and (not self.app_key or not self.app_secret):
            logger.warning("钉钉登录已启用但配置不完整，请检查 DINGTALK_APP_KEY 和 DINGTALK_APP_SECRET")
    
    def get_auth_url(self, state: Optional[str] = None) -> str:
        """获取钉钉授权URL
        
        Args:
            state: 状态参数，用于防止CSRF攻击
            
        Returns:
            str: 授权URL
        """
        if not self.enabled:
            raise ValueError("钉钉登录未启用")
        
        if state is None:
            state = str(int(time.time()))
        
        # 构建授权URL（使用新统一API）
        url = (
            f"https://login.dingtalk.com/oauth2/auth?"
            f"client_id={self.app_key}&"
            f"response_type=code&"
            f"scope=openid&"
            f"state={state}&"
            f"redirect_uri={self.redirect_uri}&"
            f"prompt=consent"
        )
        
        logger.debug(f"生成钉钉授权URL: {url}")
        return url


class DingTalkLogin:
    """钉钉登录管理类"""
    
    def __init__(self, config: Optional[DingTalkConfig] = None):
        """初始化登录管理器
        
        Args:
            config: 钉钉配置，如果不提供则使用默认配置
        """
        self.config = config or DingTalkConfig()
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def get_access_token(self, auth_code: str) -> str:
        """使用授权码获取访问令牌
        
        Args:
            auth_code: 授权码
            
        Returns:
            str: 访问令牌
        """
        if not self.config.enabled:
            raise ValueError("钉钉登录未启用")
        
        # 构建请求体
        data = {
            "clientId": self.config.app_key,
            "clientSecret": self.config.app_secret,
            "code": auth_code,
            "grantType": "authorization_code"
        }
        
        try:
            # 调用钉钉API获取token（使用新统一API）
            response = await self.http_client.post(
                "https://api.dingtalk.com/v1.0/oauth2/userAccessToken",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            access_token = result.get("accessToken")
            
            if not access_token:
                raise ValueError(f"获取access_token失败: {result}")
            
            logger.info("成功获取钉钉访问令牌")
            return access_token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"获取钉钉访问令牌失败: {e.response.text}")
            raise ValueError(f"HTTP请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"获取钉钉访问令牌异常: {e}")
            raise
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """获取用户信息
        
        Args:
            access_token: 访问令牌
            
        Returns:
            Dict[str, Any]: 用户信息
        """
        if not self.config.enabled:
            raise ValueError("钉钉登录未启用")
        
        try:
            # 调用钉钉API获取用户信息（使用新统一API）
            response = await self.http_client.get(
                "https://api.dingtalk.com/v1.0/contact/users/me",
                headers={
                    "x-acs-dingtalk-access-token": access_token,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            
            user_data = response.json()
            
            # 提取用户信息
            user_info = {
                "unionid": user_data.get("unionId"),
                "userid": user_data.get("userId"),
                "username": user_data.get("nick") or user_data.get("userName") or "钉钉用户",
                "email": user_data.get("email"),
                "mobile": user_data.get("mobile"),
                "avatar": user_data.get("avatar"),
                "stateCode": user_data.get("stateCode")
            }
            
            logger.info(f"成功获取用户信息: {user_info['username']}")
            return user_info
            
        except httpx.HTTPStatusError as e:
            logger.error(f"获取用户信息失败: {e.response.text}")
            raise ValueError(f"HTTP请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"获取用户信息异常: {e}")
            raise
    
    async def login(self, auth_code: str) -> Dict[str, Any]:
        """完整的登录流程
        
        Args:
            auth_code: 授权码
            
        Returns:
            Dict[str, Any]: 用户信息（包含钉钉ID）
        """
        # 获取访问令牌
        access_token = await self.get_access_token(auth_code)
        
        # 获取用户信息
        user_info = await self.get_user_info(access_token)
        
        # 返回用户信息（供后续处理）
        return {
            "dingtalk_id": user_info.get("unionid") or user_info.get("userid"),
            "username": user_info.get("username"),
            "email": user_info.get("email"),
            "avatar": user_info.get("avatar"),
            "mobile": user_info.get("mobile")
        }
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()