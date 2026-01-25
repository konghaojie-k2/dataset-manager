#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查日志文件位置的脚本
"""

import os
from pathlib import Path
from src.config.settings import get_settings

def main():
    """显示日志文件位置"""
    settings = get_settings()
    
    print("=" * 60)
    print("日志文件位置信息")
    print("=" * 60)
    
    # 日志目录
    logs_dir = settings.logs_dir
    print(f"\n📁 日志目录: {logs_dir.absolute()}")
    print(f"   路径是否存在: {'✅ 是' if logs_dir.exists() else '❌ 否'}")
    
    # 主要日志文件
    log_file = logs_dir / "dataset_manager.log"
    print(f"\n📄 主日志文件: {log_file.absolute()}")
    print(f"   文件是否存在: {'✅ 是' if log_file.exists() else '❌ 否'}")
    if log_file.exists():
        size = log_file.stat().st_size
        print(f"   文件大小: {size:,} 字节 ({size / 1024:.2f} KB)")
    
    # 错误日志文件
    error_log_file = logs_dir / "error.log"
    print(f"\n📄 错误日志文件: {error_log_file.absolute()}")
    print(f"   文件是否存在: {'✅ 是' if error_log_file.exists() else '❌ 否'}")
    if error_log_file.exists():
        size = error_log_file.stat().st_size
        print(f"   文件大小: {size:,} 字节 ({size / 1024:.2f} KB)")
    
    # 环境变量配置
    env_logs_dir = os.getenv("DATASET_MANAGER_LOGS_DIR")
    print(f"\n🔧 环境变量配置:")
    if env_logs_dir:
        print(f"   DATASET_MANAGER_LOGS_DIR: {env_logs_dir}")
    else:
        print(f"   DATASET_MANAGER_LOGS_DIR: (未设置，使用默认值)")
    
    # 列出日志目录中的所有文件
    if logs_dir.exists():
        print(f"\n📋 日志目录中的所有文件:")
        files = list(logs_dir.glob("*"))
        if files:
            for file in sorted(files):
                if file.is_file():
                    size = file.stat().st_size
                    print(f"   - {file.name} ({size:,} 字节)")
                else:
                    print(f"   - {file.name}/ (目录)")
        else:
            print("   (目录为空)")
    
    print("\n" + "=" * 60)
    print("💡 提示:")
    print("   1. 日志文件位置可以通过环境变量 DATASET_MANAGER_LOGS_DIR 配置")
    print("   2. 主日志文件包含所有 INFO 级别及以上的日志")
    print("   3. 错误日志文件只包含 ERROR 级别的日志")
    print("   4. 日志文件每天轮转，保留30天")
    print("=" * 60)

if __name__ == "__main__":
    main()
