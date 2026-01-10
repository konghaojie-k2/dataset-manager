#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supabase客户端服务
提供与Supabase交互的核心功能
"""

import httpx
from typing import Any, Dict, List, Optional
from loguru import logger
from supabase import Client, create_client

from src.config.settings import get_settings


class SupabaseService:
    """Supabase服务类"""

    def __init__(self):
        """初始化Supabase服务"""
        self.settings = get_settings()
        self.client: Optional[Client] = None
        self.admin_client: Optional[Client] = None

        # 初始化客户端
        self._init_clients()

    def _init_clients(self):
        """初始化Supabase客户端"""
        supabase_url = self.settings.supabase_url
        anon_key = self.settings.supabase_anon_key or self.settings.supabase_key
        service_key = self.settings.supabase_service_key

        if not supabase_url:
            logger.warning("Supabase URL未配置，Supabase功能将不可用")
            return

        # 初始化客户端（使用Anon Key）
        if anon_key:
            try:
                self.client = create_client(
                    supabase_url=supabase_url,
                    supabase_key=anon_key
                )
                logger.info("Supabase客户端初始化成功")
            except Exception as e:
                logger.error(f"Supabase客户端初始化失败: {e}")
        else:
            logger.warning("Supabase Anon Key未配置")

        # 初始化管理员客户端（使用Service Key）
        if service_key:
            try:
                self.admin_client = create_client(
                    supabase_url=supabase_url,
                    supabase_key=service_key
                )
                logger.info("Supabase管理员客户端初始化成功")
            except Exception as e:
                logger.error(f"Supabase管理员客户端初始化失败: {e}")
        else:
            logger.warning("Supabase Service Key未配置")

    @property
    def client_available(self) -> bool:
        """检查客户端是否可用"""
        return self.client is not None

    @property
    def admin_client_available(self) -> bool:
        """检查管理员客户端是否可用"""
        return self.admin_client is not None

    @property
    def available(self) -> bool:
        """检查Supabase服务是否可用"""
        return self.client_available or self.admin_client_available


# 全局HTTP客户端（用于直接HTTP调用）
_global_http_client: Optional[httpx.AsyncClient] = None


async def get_global_async_http_client() -> httpx.AsyncClient:
    """获取全局异步HTTP客户端"""
    global _global_http_client

    if _global_http_client is None:
        settings = get_settings()
        timeout = httpx.Timeout(60.0, connect=10.0)
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)

        _global_http_client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            http2=True  # 启用HTTP/2以获得更好的性能
        )
        logger.info("全局异步HTTP客户端初始化成功")

    return _global_http_client


async def close_global_async_http_client():
    """关闭全局异步HTTP客户端"""
    global _global_http_client

    if _global_http_client is not None:
        await _global_http_client.aclose()
        _global_http_client = None
        logger.info("全局异步HTTP客户端已关闭")


async def direct_supabase_query(
    table: str,
    select: str = "*",
    filters: Optional[Dict[str, Any]] = None,
    or_filters: Optional[str] = None,
    order_by: Optional[str] = None,
    order_desc: bool = True,
    limit: int = 100,
    offset: int = 0,
    use_service_key: bool = True
) -> List[Dict]:
    """
    直接通过HTTP调用Supabase REST API

    这种方式可以复用HTTP/2连接，性能更好

    Args:
        table: 表名
        select: 查询字段
        filters: 过滤条件字典
        or_filters: OR过滤条件字符串
        order_by: 排序字段
        order_desc: 是否降序
        limit: 限制返回数量
        offset: 偏移量
        use_service_key: 是否使用Service Key

    Returns:
        查询结果列表
    """
    try:
        settings = get_settings()

        if not settings.supabase_url:
            logger.error("Supabase URL未配置")
            return []

        client = await get_global_async_http_client()

        # 构建URL
        base_url = settings.supabase_url.rstrip('/')
        url = f"{base_url}/rest/v1/{table}"

        # 构建查询参数
        params = {"select": select}
        if limit:
            params["limit"] = str(limit)
        if offset:
            params["offset"] = str(offset)
        if order_by:
            params["order"] = f"{order_by}.{'desc' if order_desc else 'asc'}"

        # 添加过滤条件
        if filters:
            for key, value in filters.items():
                # 处理布尔值：Supabase需要小写的true/false
                if isinstance(value, bool):
                    params[key] = f"eq.{str(value).lower()}"
                else:
                    params[key] = f"eq.{value}"

        # 添加OR过滤条件
        if or_filters:
            params["or"] = f"({or_filters})"

        # 构建请求头
        api_key = settings.supabase_service_key if use_service_key else (settings.supabase_anon_key or settings.supabase_key)
        if not api_key:
            logger.error("Supabase API Key未配置")
            return []

        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        # 发送请求
        response = await client.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"直接查询失败: {response.status_code} - {response.text}")
            return []

    except Exception as e:
        logger.error(f"直接查询异常: {e}")
        return []


async def direct_supabase_insert(
    table: str,
    data: Dict[str, Any] | List[Dict[str, Any]],
    use_service_key: bool = True
) -> Optional[Dict[str, Any]]:
    """
    直接通过HTTP插入数据到Supabase

    Args:
        table: 表名
        data: 插入的数据（字典或字典列表）
        use_service_key: 是否使用Service Key

    Returns:
        插入结果
    """
    try:
        settings = get_settings()

        if not settings.supabase_url:
            logger.error("Supabase URL未配置")
            return None

        client = await get_global_async_http_client()

        # 构建URL
        base_url = settings.supabase_url.rstrip('/')
        url = f"{base_url}/rest/v1/{table}"

        # 构建请求头
        api_key = settings.supabase_service_key if use_service_key else (settings.supabase_anon_key or settings.supabase_key)
        if not api_key:
            logger.error("Supabase API Key未配置")
            return None

        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        # 发送请求
        response = await client.post(url, json=data, headers=headers)

        if response.status_code in [200, 201]:
            result = response.json()
            if isinstance(result, list):
                return result[0] if result else None
            return result
        else:
            logger.error(f"插入失败: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"插入异常: {e}")
        return None


async def direct_supabase_update(
    table: str,
    data: Dict[str, Any],
    filters: Dict[str, Any],
    use_service_key: bool = True
) -> Optional[List[Dict[str, Any]]]:
    """
    直接通过HTTP更新Supabase数据

    Args:
        table: 表名
        data: 更新的数据
        filters: 过滤条件
        use_service_key: 是否使用Service Key

    Returns:
        更新结果
    """
    try:
        settings = get_settings()

        if not settings.supabase_url:
            logger.error("Supabase URL未配置")
            return None

        client = await get_global_async_http_client()

        # 构建URL
        base_url = settings.supabase_url.rstrip('/')
        url = f"{base_url}/rest/v1/{table}"

        # 构建请求头
        api_key = settings.supabase_service_key if use_service_key else (settings.supabase_anon_key or settings.supabase_key)
        if not api_key:
            logger.error("Supabase API Key未配置")
            return None

        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        # 构建查询参数
        params = {}
        for key, value in filters.items():
            if isinstance(value, bool):
                params[key] = f"eq.{str(value).lower()}"
            else:
                params[key] = f"eq.{value}"

        # 发送请求
        response = await client.patch(url, json=data, params=params, headers=headers)

        if response.status_code in [200, 204]:
            if response.status_code == 204:
                return []
            return response.json()
        else:
            logger.error(f"更新失败: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"更新异常: {e}")
        return None


async def direct_supabase_delete(
    table: str,
    filters: Dict[str, Any],
    use_service_key: bool = True
) -> bool:
    """
    直接通过HTTP删除Supabase数据

    Args:
        table: 表名
        filters: 过滤条件
        use_service_key: 是否使用Service Key

    Returns:
        是否成功
    """
    try:
        settings = get_settings()

        if not settings.supabase_url:
            logger.error("Supabase URL未配置")
            return False

        client = await get_global_async_http_client()

        # 构建URL
        base_url = settings.supabase_url.rstrip('/')
        url = f"{base_url}/rest/v1/{table}"

        # 构建请求头
        api_key = settings.supabase_service_key if use_service_key else (settings.supabase_anon_key or settings.supabase_key)
        if not api_key:
            logger.error("Supabase API Key未配置")
            return False

        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 构建查询参数
        params = {}
        for key, value in filters.items():
            if isinstance(value, bool):
                params[key] = f"eq.{str(value).lower()}"
            else:
                params[key] = f"eq.{value}"

        # 发送请求
        response = await client.delete(url, params=params, headers=headers)

        if response.status_code in [200, 204]:
            return True
        else:
            logger.error(f"删除失败: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"删除异常: {e}")
        return False


# 全局服务实例
_supabase_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """获取Supabase服务实例（单例模式）"""
    global _supabase_service

    if _supabase_service is None:
        _supabase_service = SupabaseService()

    return _supabase_service
