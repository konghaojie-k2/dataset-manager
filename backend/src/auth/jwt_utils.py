#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JWT工具类"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from loguru import logger

from ..config.settings import get_settings


class JWTManager:
    """JWT管理器"""
    
    def __init__(self):
        """初始化JWT管理器"""
        settings = get_settings()
        self.secret_key = settings.jwt_secret or "your-secret-key-change-this"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 30
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """创建访问令牌
        
        Args:
            data: 要编码的数据
            
        Returns:
            str: JWT令牌
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"创建访问令牌: user_id={data.get('user_id')}")
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌
        
        Args:
            data: 要编码的数据
            
        Returns:
            str: JWT令牌
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"创建刷新令牌: user_id={data.get('user_id')}")
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 解码后的数据
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"令牌无效: {e}")
            return None
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """验证令牌
        
        Args:
            token: JWT令牌
            token_type: 令牌类型（access或refresh）
            
        Returns:
            Optional[Dict[str, Any]]: 验证通过后的数据
        """
        payload = self.decode_token(token)
        if not payload:
            return None
        
        if payload.get("type") != token_type:
            logger.warning(f"令牌类型不匹配: 期望{token_type}, 实际{payload.get('type')}")
            return None
        
        return payload


# 全局JWT管理器实例
jwt_manager = JWTManager()