#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据集服务工厂
根据配置创建本地存储或Supabase存储的服务实例
"""

from pathlib import Path
from typing import Union
from loguru import logger

from src.config.settings import get_settings
from src.core.dataset_service import DatasetService
from src.core.dataset_repository import DatasetRepository
from src.core.file_service import FileService
from src.core.supabase_dataset_repository import SupabaseDatasetRepository
from src.core.supabase_file_service import SupabaseFileService


def create_dataset_service() -> DatasetService:
    """
    根据配置创建数据集服务

    如果Supabase配置可用，使用Supabase存储
    否则使用本地文件系统存储

    Returns:
        DatasetService: 数据集服务实例
    """
    settings = get_settings()

    # 检查是否可以使用Supabase
    use_supabase = all([
        settings.supabase_url,
        settings.supabase_service_key
    ])

    if use_supabase:
        logger.info("使用Supabase存储")
        try:
            # 创建Supabase服务
            repository = SupabaseDatasetRepository()
            file_service = SupabaseFileService()

            # 创建DatasetService并注入Supabase组件
            service = DatasetService(
                upload_dir=settings.upload_dir,  # 保留用于本地缓存
                metadata_dir=settings.metadata_dir  # 保留用于兼容性
            )

            # 替换为Supabase组件
            service.repository = repository
            service.file_service = file_service

            logger.info("✅ Supabase数据集服务创建成功")
            return service

        except Exception as e:
            logger.error(f"❌ Supabase服务创建失败，回退到本地存储: {e}")
            # 回退到本地存储
            use_supabase = False

    if not use_supabase:
        logger.info("使用本地文件系统存储")
        # 使用本地存储
        repository = DatasetRepository(settings.metadata_dir)
        file_service = FileService(settings.upload_dir)

        service = DatasetService(
            upload_dir=settings.upload_dir,
            metadata_dir=settings.metadata_dir
        )

        # 使用默认的本地组件
        service.repository = repository
        service.file_service = file_service

        logger.info("✅ 本地存储数据集服务创建成功")
        return service
