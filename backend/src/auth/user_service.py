#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户服务"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from ..schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    """用户服务类"""
    
    def __init__(self, db_path: Path):
        """初始化用户服务
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        logger.info(f"用户服务初始化: {self.db_path}")
    
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """创建用户
        
        Args:
            user_data: 用户创建数据
            
        Returns:
            UserResponse: 创建的用户
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 检查用户是否已存在
                if user_data.dingtalk_id:
                    cursor.execute(
                        "SELECT id FROM users WHERE dingtalk_id = ?",
                        (user_data.dingtalk_id,)
                    )
                    if cursor.fetchone():
                        logger.info(f"钉钉用户已存在: {user_data.dingtalk_id}")
                        return self.get_user_by_dingtalk_id(user_data.dingtalk_id)
                
                if user_data.email:
                    cursor.execute(
                        "SELECT id FROM users WHERE email = ?",
                        (user_data.email,)
                    )
                    if cursor.fetchone():
                        raise ValueError(f"邮箱已注册: {user_data.email}")
                
                # 插入新用户
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, dingtalk_id, avatar)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_data.username,
                    user_data.email,
                    user_data.password_hash,
                    user_data.dingtalk_id,
                    user_data.avatar
                ))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"用户创建成功: {user_id}")
                return self.get_user_by_id(user_id)
                
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserResponse]: 用户信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return UserResponse(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    dingtalk_id=row['dingtalk_id'],
                    avatar=row['avatar'],
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def get_user_by_dingtalk_id(self, dingtalk_id: str) -> Optional[UserResponse]:
        """根据钉钉ID获取用户
        
        Args:
            dingtalk_id: 钉钉ID
            
        Returns:
            Optional[UserResponse]: 用户信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM users WHERE dingtalk_id = ?",
                    (dingtalk_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return UserResponse(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    dingtalk_id=row['dingtalk_id'],
                    avatar=row['avatar'],
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """根据邮箱获取用户
        
        Args:
            email: 邮箱
            
        Returns:
            Optional[UserResponse]: 用户信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM users WHERE email = ?",
                    (email,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return UserResponse(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    dingtalk_id=row['dingtalk_id'],
                    avatar=row['avatar'],
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        """更新用户信息
        
        Args:
            user_id: 用户ID
            user_data: 更新数据
            
        Returns:
            Optional[UserResponse]: 更新后的用户信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 构建更新语句
                update_fields = []
                update_values = []
                
                if user_data.username is not None:
                    update_fields.append("username = ?")
                    update_values.append(user_data.username)
                
                if user_data.email is not None:
                    update_fields.append("email = ?")
                    update_values.append(user_data.email)
                
                if user_data.avatar is not None:
                    update_fields.append("avatar = ?")
                    update_values.append(user_data.avatar)
                
                if user_data.is_active is not None:
                    update_fields.append("is_active = ?")
                    update_values.append(user_data.is_active)
                
                if not update_fields:
                    return self.get_user_by_id(user_id)
                
                update_fields.append("updated_at = ?")
                update_values.append(datetime.now().isoformat())
                update_values.append(user_id)
                
                cursor.execute(
                    f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?",
                    update_values
                )
                conn.commit()
                
                logger.info(f"用户更新成功: {user_id}")
                return self.get_user_by_id(user_id)
                
        except Exception as e:
            logger.error(f"更新用户失败: {e}")
            raise