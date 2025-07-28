# 数据管理系统

一个基于 FastAPI + Next.js 的现代化数据管理系统。

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

### 前端启动
```bash
cd frontend
npm install
npm run dev
```
访问: http://localhost:3000

### 后端启动
```bash
cd backend
uv sync
uv run python start_dev.py
```
访问: http://localhost:8000
API文档: http://localhost:8000/docs

### 使用批处理文件（Windows）
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
