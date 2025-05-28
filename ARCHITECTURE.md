# 项目架构说明

## 目录结构

```
src/
├── config/                 # 配置管理
│   ├── __init__.py
│   └── settings.py         # 应用配置和环境变量管理
├── llms/                   # 语言模型接口
│   ├── __init__.py
│   ├── base.py            # 基础LLM抽象类
│   └── deepseek.py        # DeepSeek实现
├── prompts/               # 提示词模板
│   ├── __init__.py
│   ├── metadata_prompts.py # 元数据分析提示词
│   └── analysis_prompts.py # 数据分析提示词
├── tools/                 # 工具和实用函数
│   ├── __init__.py
│   ├── data_analyzer.py   # 数据分析工具
│   ├── file_processor.py  # 文件处理工具
│   └── visualization_tools.py # 可视化工具
├── graph/                 # LangGraph工作流
│   ├── __init__.py
│   ├── state.py          # 工作流状态定义
│   └── analysis_workflow.py # 分析工作流实现
├── utils/                 # 通用工具函数
│   ├── __init__.py
│   └── helpers.py        # 辅助函数
├── mcp/                   # MCP (Model Context Protocol) 服务器
│   ├── __init__.py
│   ├── servers.py        # MCP服务器管理器
│   ├── connectors.py     # 数据源连接器
│   └── tools.py          # 外部工具注册表
├── server/                # 服务器层
│   ├── __init__.py
│   ├── app.py            # FastAPI应用配置
│   ├── routes.py         # API路由
│   ├── dependencies.py  # 依赖注入
│   └── middleware.py     # 中间件
├── core/                  # 核心业务逻辑
│   ├── __init__.py
│   ├── dataset_service.py    # 应用服务层
│   ├── dataset_repository.py # 仓储层
│   ├── file_service.py      # 文件管理服务
│   └── metadata_service.py  # 元数据处理服务
├── schemas/               # 数据结构定义
│   ├── __init__.py
│   ├── dataset.py        # 数据集相关结构
│   ├── analysis.py       # 分析相关结构
│   └── mcp.py            # MCP服务器相关结构
├── agents/                # LangGraph代理
└── __init__.py            # 主模块入口
```

## 模块说明

### 1. config/ - 配置管理
- **settings.py**: 使用Pydantic管理应用配置，支持环境变量
- 统一的配置加载和日志设置

### 2. llms/ - 语言模型接口
- **base.py**: 定义统一的LLM接口抽象类
- **deepseek.py**: DeepSeek API的具体实现
- 支持异步调用和错误处理

### 3. prompts/ - 提示词模板
- **metadata_prompts.py**: 元数据分析相关的提示词模板
- **analysis_prompts.py**: 数据分析相关的提示词模板
- 模板化管理，便于维护和优化

### 4. tools/ - 工具模块
- **data_analyzer.py**: 数据分析核心工具类
- **file_processor.py**: 文件处理和验证工具
- **visualization_tools.py**: 数据可视化工具
- 提供可重用的数据处理功能

### 5. graph/ - LangGraph工作流
- **state.py**: 定义工作流状态结构
- **analysis_workflow.py**: 实现完整的数据分析工作流
- 基于LangGraph的状态机模式

### 6. server/ - 服务器层
- **app.py**: FastAPI应用核心配置和生命周期管理
- **routes.py**: API路由定义
- **dependencies.py**: 依赖注入管理
- **middleware.py**: 请求日志和安全中间件
- 统一的服务器配置和请求处理

### 7. core/ - 核心业务逻辑
- **dataset_service.py**: 应用服务层，协调各个领域服务
- **dataset_repository.py**: 仓储层，负责数据持久化和缓存
- **file_service.py**: 文件管理服务，处理文件上传和操作
- **metadata_service.py**: 元数据处理服务，负责元数据提取和更新
- 采用分层架构，职责分离清晰

### 8. mcp/ - MCP服务器模块
- **servers.py**: MCP服务器管理器，负责管理多个MCP服务器实例
- **connectors.py**: 数据源连接器，支持数据库、API等外部数据源
- **tools.py**: 外部工具注册表，管理可调用的外部工具
- 提供与外部系统的集成能力

### 9. utils/ - 通用工具
- **helpers.py**: 通用辅助函数
- 文件大小格式化、JSON序列化等

## 设计原则

### 1. 模块化设计
- 每个模块职责单一，便于测试和维护
- 清晰的依赖关系，避免循环依赖

### 2. 配置管理
- 统一的配置管理，支持环境变量
- 类型安全的配置验证

### 3. 异步支持
- 全面支持异步操作
- 提高并发性能

### 4. 错误处理
- 统一的错误处理机制
- 详细的日志记录

### 5. 可扩展性
- 插件化的LLM接口
- 模板化的提示词管理
- 工作流的可配置性

## 使用示例

### 1. 基础配置
```python
from dataset_manager.config import get_settings

settings = get_settings()
```

### 2. 使用LLM
```python
from dataset_manager.llms import DeepSeekLLM

llm = DeepSeekLLM(api_key="your_api_key")
response = await llm.generate("分析这个数据集")
```

### 3. 数据分析
```python
from dataset_manager.tools import DataAnalyzer

analyzer = DataAnalyzer()
analyzer.load_data(file_path)
results = analyzer.get_full_analysis()
```

### 4. 工作流执行
```python
from dataset_manager.graph import AnalysisWorkflow
from dataset_manager.llms import DeepSeekLLM

llm = DeepSeekLLM(api_key="your_api_key")
workflow = AnalysisWorkflow(llm)
results = await workflow.run_analysis(file_path)
```

## 迁移说明

### 已完成的重构
1. ✅ 配置管理从 `utils/config.py` 迁移到 `config/settings.py`
2. ✅ 创建了标准的LLM接口和DeepSeek实现
3. ✅ 提示词模板化管理
4. ✅ 工具模块重新组织
5. ✅ LangGraph工作流标准化
6. ✅ 删除重复的 `core/file_handler.py`，统一使用 `tools/FileProcessor`
7. ✅ 简化目录结构，删除多余的 `dataset_manager` 嵌套层级
8. ✅ 重构 `api` 为 `server`，增加中间件、依赖注入等服务器功能
9. ✅ 重构 `core` 模块，采用分层架构：应用服务层、仓储层、领域服务层
10. ✅ 新增 `mcp` 模块，提供MCP服务器集成能力

### 保持兼容的模块
- `server/` - 服务器层已重构，提供更完整的服务器功能
- `core/` - 核心业务逻辑已重构为分层架构：
  - DatasetService: 应用服务层，协调业务流程
  - DatasetRepository: 仓储层，负责数据持久化
  - FileService: 文件管理服务
  - MetadataService: 元数据处理服务
- `mcp/` - 新增MCP服务器模块：
  - MCPServerManager: 服务器管理器
  - DatabaseConnector/APIConnector: 数据源连接器
  - ExternalToolsRegistry: 外部工具注册表
- `schemas/` - 数据结构定义（原models/，避免与LLM models混淆）
- `agents/` - 现有代理保持不变

### 下一步优化
1. 逐步迁移现有代理到新的工作流模式
2. 完善测试覆盖
3. 添加更多可视化功能
4. 优化提示词模板 