#!/usr/bin/env python3
"""开发环境启动脚本"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动开发服务器"""
    
    # 加载环境变量
    from dotenv import load_dotenv
    
    # 首先加载项目根目录的.env文件
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 已加载环境变量文件: {env_file}")
    else:
        print(f"⚠️  环境变量文件不存在: {env_file}")
    
    # 设置环境变量（开发环境默认值）
    os.environ.setdefault("DATASET_MANAGER_DEBUG", "true")
    os.environ.setdefault("DATASET_MANAGER_HOST", "127.0.0.1")
    os.environ.setdefault("DATASET_MANAGER_PORT", "8000")
    
    # 检查DeepSeek API密钥
    if not os.getenv("DATASET_MANAGER_DEEPSEEK_API_KEY"):
        print("⚠️  警告: 未设置DeepSeek API密钥")
        print("请设置环境变量: DATASET_MANAGER_DEEPSEEK_API_KEY")
        print("或者在命令行中运行:")
        print("export DATASET_MANAGER_DEEPSEEK_API_KEY=your_api_key")
        print()
        
        # 提示用户输入API密钥
        api_key = input("请输入DeepSeek API密钥 (或按Enter跳过): ").strip()
        if api_key:
            os.environ["DATASET_MANAGER_DEEPSEEK_API_KEY"] = api_key
        else:
            print("❌ 没有API密钥，系统将无法正常工作")
            return
    
    print("🚀 启动数据管理系统...")
    print(f"📍 访问地址: http://{os.getenv('DATASET_MANAGER_HOST', '127.0.0.1')}:{os.getenv('DATASET_MANAGER_PORT', '8000')}")
    print(f"📚 API文档: http://{os.getenv('DATASET_MANAGER_HOST', '127.0.0.1')}:{os.getenv('DATASET_MANAGER_PORT', '8000')}/docs")
    print()
    
    # 启动服务器
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=os.getenv("DATASET_MANAGER_HOST", "127.0.0.1"),
        port=int(os.getenv("DATASET_MANAGER_PORT", "8000")),
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 