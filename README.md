# 数据管理系统

基于LangGraph的智能数据管理系统，支持CSV数据上传、自动元数据提取、数据质量分析和标签管理。

## 🚀 功能特性

### 核心功能
- **数据上传**: 支持CSV文件和ZIP压缩包上传
- **智能元数据提取**: 使用LangGraph + DeepSeek AI自动分析数据
- **列识别**: 自动识别设备ID列、时间列和业务含义
- **数据质量分析**: 自动评估数据质量并提供改进建议
- **标签管理**: AI建议标签、行业分类和适用算法
- **人机交互**: 支持用户输入额外信息指导分析

### 技术特点
- **LangGraph工作流**: 使用最新的LangGraph API构建智能代理
- **DeepSeek集成**: 集成DeepSeek大语言模型进行数据分析
- **FastAPI后端**: 高性能异步API服务
- **现代前端**: 响应式Web界面，支持拖拽上传
- **完整日志**: 使用loguru进行结构化日志记录

## 📋 系统要求

- Python 3.11+
- DeepSeek API密钥

## 🛠️ 安装部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd dataset-manager
```

### 2. 安装依赖
```bash
# 使用uv安装依赖（推荐）
uv sync

# 或使用pip
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
# 设置DeepSeek API密钥（必需）
export DATASET_MANAGER_DEEPSEEK_API_KEY=your_deepseek_api_key

# 可选配置
export DATASET_MANAGER_DEBUG=true
export DATASET_MANAGER_HOST=127.0.0.1
export DATASET_MANAGER_PORT=8000
export DATASET_MANAGER_UPLOAD_DIR=./uploads
export DATASET_MANAGER_METADATA_DIR=./metadata
export DATASET_MANAGER_LOGS_DIR=./logs
```

### 4. 启动服务

#### 开发环境
```bash
python start_dev.py
```

#### 生产环境
```bash
python main.py
```

## 🌐 访问系统

- **Web界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

## 📖 使用指南

### 1. 上传数据集
1. 访问Web界面
2. 点击"选择文件"或拖拽文件到上传区域
3. 支持的格式：`.csv` 或 `.zip`（包含CSV文件）
4. 可选：输入数据集的额外信息
5. 系统自动开始元数据提取

### 2. 查看分析结果
- **数据集列表**: 查看所有已上传的数据集
- **处理状态**: 实时显示处理进度
- **元数据信息**: 查看AI提取的元数据
- **数据质量**: 查看质量评分和改进建议
- **标签管理**: 查看和编辑AI建议的标签

### 3. API使用
```python
import requests

# 上传文件
files = {'file': open('data.csv', 'rb')}
data = {'user_input': '这是设备运行数据'}
response = requests.post('http://localhost:8000/api/v1/datasets/upload', 
                        files=files, data=data)

# 获取数据集列表
response = requests.get('http://localhost:8000/api/v1/datasets')
datasets = response.json()

# 获取数据预览
response = requests.get(f'http://localhost:8000/api/v1/datasets/{dataset_id}/preview')
preview = response.json()
```

## 🏗️ 系统架构

### 核心组件
```
├── src/dataset_manager/
│   ├── schemas/         # 数据结构定义
│   │   ├── dataset.py         # 数据集相关结构
│   │   ├── analysis.py        # 分析相关结构
│   │   └── mcp.py             # MCP服务器相关结构
│   ├── core/           # 核心业务逻辑
│   │   ├── file_handler.py      # 文件处理
│   │   └── dataset_service.py   # 数据集服务
│   ├── agents/         # LangGraph代理
│   │   └── metadata_agent.py    # 元数据提取代理
│   ├── api/            # API路由
│   │   └── routes.py            # FastAPI路由
│   └── utils/          # 工具模块
│       └── config.py            # 配置管理
├── web/                # 前端文件
├── uploads/            # 上传文件存储
├── metadata/           # 元数据存储
└── logs/              # 日志文件
```

### LangGraph工作流
```
数据上传 → 结构分析 → 列识别 → 时间信息提取 → 描述生成 → 质量分析 → 标签建议 → 用户确认 → 完成
```

## 🔧 配置说明

### 环境变量
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATASET_MANAGER_DEEPSEEK_API_KEY` | DeepSeek API密钥 | 必需 |
| `DATASET_MANAGER_DEBUG` | 调试模式 | `false` |
| `DATASET_MANAGER_HOST` | 服务器地址 | `0.0.0.0` |
| `DATASET_MANAGER_PORT` | 服务器端口 | `8000` |
| `DATASET_MANAGER_UPLOAD_DIR` | 上传目录 | `uploads` |
| `DATASET_MANAGER_METADATA_DIR` | 元数据目录 | `metadata` |
| `DATASET_MANAGER_LOGS_DIR` | 日志目录 | `logs` |
| `DATASET_MANAGER_MAX_FILE_SIZE` | 最大文件大小 | `104857600` (100MB) |

## 🧪 开发指南

### 项目结构
- 使用`pathlib`处理文件路径
- 使用`loguru`进行日志记录
- 使用`pydantic`进行数据验证
- 使用`FastAPI`构建API服务
- 使用`LangGraph`构建AI工作流

### 添加新功能
1. 在`schemas/`中定义数据结构
2. 在`core/`中实现业务逻辑
3. 在`agents/`中扩展AI代理
4. 在`api/`中添加API端点
5. 更新前端界面

## 📝 API文档

### 主要端点
- `POST /api/v1/datasets/upload` - 上传数据集
- `GET /api/v1/datasets` - 获取数据集列表
- `GET /api/v1/datasets/{id}` - 获取数据集详情
- `GET /api/v1/datasets/{id}/preview` - 数据预览
- `POST /api/v1/datasets/{id}/extract-metadata` - 提取元数据
- `PUT /api/v1/datasets/{id}/tags` - 更新标签
- `DELETE /api/v1/datasets/{id}` - 删除数据集

详细API文档请访问: http://localhost:8000/docs

## 🐛 故障排除

### 常见问题
1. **API密钥错误**: 确保设置了正确的DeepSeek API密钥
2. **文件上传失败**: 检查文件格式和大小限制
3. **元数据提取失败**: 查看日志文件了解详细错误信息
4. **端口占用**: 修改`DATASET_MANAGER_PORT`环境变量

### 日志查看
```bash
# 查看应用日志
tail -f logs/dataset_manager.log

# 查看错误日志
tail -f logs/error.log
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - AI工作流框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [DeepSeek](https://www.deepseek.com/) - 大语言模型服务
- [Loguru](https://github.com/Delgan/loguru) - Python日志库
