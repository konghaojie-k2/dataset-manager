# 数据管理系统

一个基于 FastAPI + Next.js 的现代化数据管理系统，**集成LLM驱动的智能数据分析和血缘关系管理**。

## ✨ 最新功能 (v1.0.0)

### 🤖 智能数据分析
- ✅ **工业领域自动识别**: 10个领域（半导体、化工、能源等）
- ✅ **业务数据类型识别**: 8种类型（设备运行、生产数据、日志等）
- ✅ **重要列智能识别**: 关键观测量 + 控制量 + 控制回路分析

### 🔗 数据血缘管理
- ✅ **完整血缘追溯**: 上游/下游数据关系查询
- ✅ **可视化血缘图**: 层次化展示数据流向
- ✅ **转换记录**: 支持过滤/聚合/连接等转换类型

### 📝 用户友好界面
- ✅ **元数据确认表单**: 编辑和修正AI识别结果
- ✅ **血缘关系可视化**: 交互式血缘图展示
- ✅ **实时分析反馈**: 快速分析进度显示

**详情请查看**: [NEW_FEATURES_UPDATE.md](./NEW_FEATURES_UPDATE.md) | [快速启动: README_QUICKSTART.md](./README_QUICKSTART.md)

## 项目结构

```
dataset-manager/
├── frontend/           # Next.js 前端应用
├── backend/           # FastAPI 后端应用
│   ├── src/          # 源代码
│   ├── config/       # 配置文件
│   ├── tests/        # 测试文件
│   └── examples/     # 示例代码
├── uploads/          # 文件上传目录
├── metadata/         # 元数据存储
└── logs/            # 日志文件
```

## 快速启动

### 方式一：Docker 部署（推荐）

```bash
# 1. 准备配置文件
cp backend/config/example.env backend/config/.env
nano backend/config/.env  # 设置API密钥等配置

# 2. 构建并启动服务
docker compose up -d --build

# 3. 查看服务状态
docker compose ps
```

**访问服务：**
- 前端: http://localhost:3000
- 后端API文档: http://localhost:8000/docs

详细说明请参考 [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

### 方式二：本地开发

#### 前端启动
```bash
cd frontend
npm install
npm run dev
```
访问: http://localhost:3000

#### 后端启动
```bash
cd backend
uv sync
uv run python start_dev.py
```
访问: http://localhost:8000
API文档: http://localhost:8000/docs

#### 使用批处理文件（Windows）
- 启动前端: 双击 `start-frontend.bat`
- 启动后端: 双击 `start-backend.bat`

## 环境配置

在 `backend/config/` 目录下创建 `.env` 文件，基于 `example.env` 模板：

```env
DATASET_MANAGER_DEEPSEEK_API_KEY=your_api_key_here
DATASET_MANAGER_DEBUG=true
DATASET_MANAGER_HOST=127.0.0.1
DATASET_MANAGER_PORT=8000
```

## 技术栈

- **前端**: Next.js + TypeScript + Tailwind CSS
- **后端**: FastAPI + LangChain + LangGraph
- **包管理**: uv (Python) + npm (Node.js)
