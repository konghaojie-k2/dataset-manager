#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supabase文件存储服务
提供文件上传到Supabase Storage的功能
"""

import mimetypes
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from loguru import logger
from fastapi import UploadFile

from src.core.supabase_client import get_supabase_service


class SupabaseFileService:
    """Supabase文件存储服务"""

    def __init__(self):
        """初始化文件存储服务"""
        self.service = get_supabase_service()
        self.bucket_name = self.service.settings.storage_bucket_name

    def _get_content_type(self, filename: str) -> str:
        """获取文件的Content-Type"""
        content_type, _ = mimetypes.guess_type(filename)
        if content_type:
            return content_type

        # 默认类型映射
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".csv": "text/csv",
            ".zip": "application/zip",
            ".json": "application/json",
            ".txt": "text/plain",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
        }
        return mime_types.get(ext, "application/octet-stream")

    def _is_valid_filename(self, filename: str) -> bool:
        """验证文件名是否有效"""
        if not filename:
            return False

        ext = Path(filename).suffix.lower()
        allowed_extensions = self.service.settings.allowed_extensions
        return ext in allowed_extensions

    async def upload_file(
        self,
        file: UploadFile,
        file_path: Optional[str] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        上传文件到Supabase Storage

        Args:
            file: 上传的文件
            file_path: 存储路径（可选）

        Returns:
            (file_id, storage_path, file_info)

        Raises:
            ValueError: 如果文件无效或上传失败
        """
        if not self.service.available:
            raise ValueError("Supabase服务不可用")

        if not self.service.admin_client_available:
            raise ValueError("Supabase管理员客户端不可用，无法上传文件")

        # 验证文件
        if not self._is_valid_filename(file.filename):
            raise ValueError(f"不支持的文件格式: {file.filename}")

        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)

        # 检查文件大小
        max_size = self.service.settings.storage_max_file_size
        if file_size > max_size:
            raise ValueError(f"文件过大: {file_size} > {max_size}")

        # 生成文件ID
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        stored_filename = f"{file_id}{file_extension}"

        # 构建存储路径
        storage_path = f"{file_path}/{stored_filename}" if file_path else stored_filename

        # 获取Content-Type
        content_type = self._get_content_type(file.filename)

        try:
            # 上传到Supabase Storage（使用admin_client绕过RLS）
            storage_client = self.service.admin_client
            storage_client.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "upsert": False
                }
            )

            logger.info(f"文件上传成功: {storage_path}")

            # 获取公共URL
            file_url = storage_client.storage.from_(self.bucket_name).get_public_url(storage_path)

            # 构建文件信息
            file_info = {
                "file_id": file_id,
                "original_name": file.filename,
                "stored_name": stored_filename,
                "storage_path": storage_path,
                "file_size": file_size,
                "file_type": content_type,
                "file_extension": file_extension,
                "file_url": file_url,
                "bucket": self.bucket_name
            }

            return file_id, storage_path, file_info

        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise ValueError(f"文件上传失败: {e}")

    async def delete_file(self, storage_path: str) -> bool:
        """
        从Supabase Storage删除文件

        Args:
            storage_path: 存储路径

        Returns:
            是否成功
        """
        if not self.service.admin_client_available:
            logger.error("Supabase管理员客户端不可用")
            return False

        try:
            storage_client = self.service.admin_client
            storage_client.storage.from_(self.bucket_name).remove([storage_path])
            logger.info(f"文件删除成功: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False

    async def get_file_url(self, storage_path: str) -> Optional[str]:
        """
        获取文件的公共URL

        Args:
            storage_path: 存储路径

        Returns:
            文件URL
        """
        if not self.service.available:
            logger.error("Supabase服务不可用")
            return None

        try:
            client = self.service.client or self.service.admin_client
            return client.storage.from_(self.bucket_name).get_public_url(storage_path)

        except Exception as e:
            logger.error(f"获取文件URL失败: {e}")
            return None

    async def file_exists(self, storage_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            storage_path: 存储路径

        Returns:
            是否存在
        """
        if not self.service.admin_client_available:
            return False

        try:
            storage_client = self.service.admin_client
            # 尝试获取文件元数据
            storage_client.storage.from_(self.bucket_name).get_metadata(storage_path)
            return True

        except Exception:
            return False

    async def download_file(self, storage_path: str) -> Optional[bytes]:
        """
        从Supabase Storage下载文件

        Args:
            storage_path: 存储路径

        Returns:
            文件内容
        """
        if not self.service.admin_client_available:
            logger.error("Supabase管理员客户端不可用")
            return None

        try:
            storage_client = self.service.admin_client
            # 使用HTTP直接下载
            import httpx
            file_url = storage_client.storage.from_(self.bucket_name).get_public_url(storage_path)

            async with httpx.AsyncClient() as client:
                response = await client.get(file_url)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"下载文件失败: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"下载文件异常: {e}")
            return None

    async def list_files(self, path: Optional[str] = None) -> list:
        """
        列出Storage中的文件

        Args:
            path: 路径前缀

        Returns:
            文件列表
        """
        if not self.service.admin_client_available:
            logger.error("Supabase管理员客户端不可用")
            return []

        try:
            storage_client = self.service.admin_client
            result = storage_client.storage.from_(self.bucket_name).list(path=path or "")
            return result

        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return []

    async def move_file(self, from_path: str, to_path: str) -> bool:
        """
        移动文件

        Args:
            from_path: 源路径
            to_path: 目标路径

        Returns:
            是否成功
        """
        if not self.service.admin_client_available:
            logger.error("Supabase管理员客户端不可用")
            return False

        try:
            storage_client = self.service.admin_client
            storage_client.storage.from_(self.bucket_name).move(from_path, to_path)
            logger.info(f"文件移动成功: {from_path} -> {to_path}")
            return True

        except Exception as e:
            logger.error(f"文件移动失败: {e}")
            return False

    async def create_signed_url(
        self,
        storage_path: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        创建临时签名URL（用于私有文件）

        Args:
            storage_path: 存储路径
            expires_in: 有效期（秒）

        Returns:
            签名URL
        """
        if not self.service.admin_client_available:
            logger.error("Supabase管理员客户端不可用")
            return None

        try:
            storage_client = self.service.admin_client
            result = storage_client.storage.from_(self.bucket_name).create_signed_url(
                storage_path,
                expires_in
            )
            return result.signed_url

        except Exception as e:
            logger.error(f"创建签名URL失败: {e}")
            return None
