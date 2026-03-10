# AI-Native 数据集管理系统 - 实现文档

## 📋 实现概要

本文档说明已实现的 AI-Native 功能，这些功能让 Agent 能够更好地"理解"和"操作"数据。

---

## 🆕 新增文件

### 1. 增强语义元数据服务

**文件**: `backend/src/core/enhanced_metadata_service.py`

**功能**:
- 自动推断字段语义类型（ID、时间、金额、数量、状态等）
- 生成业务描述
- 数据分布统计分析
- 数据质量评分（完整性、唯一性、一致性）
- 数据理解摘要（用途建议、潜在问题）
- Agent 可查询的结构化输出

**核心方法**:
```python
from backend.src.core.enhanced_metadata_service import enhanced_metadata_service

result = await enhanced_metadata_service.analyze_dataset(
    dataset_id="xxx",
    dataframe=df,
    sample_size=1000
)
```

**输出示例**:
```json
{
  "dataset_id": "xxx",
  "total_rows": 10000,
  "total_columns": 20,
  "column_semantics": [
    {
      "name": "user_id",
      "semantic_type": "identifier",
      "business_description": "user_id - 唯一标识符"
    },
    {
      "name": "created_at", 
      "semantic_type": "timestamp",
      "business_description": "created_at - 时间戳"
    }
  ],
  "quality_score": {
    "overall_score": 85.5,
    "completeness": 95.2,
    "uniqueness": 98.0
  },
  "data_understanding": {
    "summary": "包含 10000 行 20 列数据，包含 5 个数值列和 3 个分类列。",
    "suggested_uses": ["统计分析", "机器学习"],
    "potential_issues": []
  },
  "agent_queryable": {
    "quick_summary": "数据集包含 10000 行 20 列数据...",
    "key_fields": [...]
  }
}
```

---

### 2. Agent 工具集

**文件**: `backend/src/agents/dataset_tools/agent_tools.py`

**工具清单**:

| 工具 | 功能 | 示例 |
|------|------|------|
| `search_datasets` | 语义搜索数据集 | 搜索"销售数据" |
| `get_dataset_schema` | 获取数据结构 | 了解有哪些列 |
| `get_dataset_quality` | 获取质量评分 | 查看数据质量 |
| `get_data_lineage` | 获取血缘关系 | 了解数据来源 |
| `query_with_nl` | 自然语言查询 | "数据有多少行？" |

**LangGraph 集成**:
```python
from backend.src.agents.dataset_tools.agent_tools import DATASET_TOOLS

# 在 LangGraph Agent 中使用
agent = create_react_agent(llm, tools=DATASET_TOOLS)
```

---

### 3. 自然语言查询服务

**文件**: `backend/src/core/nl_query_service.py`

**功能**:
- 理解自然语言问题意图
- 生成查询计划
- 返回自然语言回答

---

### 4. 增强元数据 API

**文件**: `backend/src/server/api/v1/metadata.py`

**端点**:

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/metadata/analyze` | 分析数据集 |
| GET | `/api/v1/metadata/schema/{id}` | 获取结构 |
| GET | `/api/v1/metadata/quality/{id}` | 获取质量 |
| GET | `/api/v1/metadata/search` | 搜索数据集 |
| POST | `/api/v1/metadata/query` | 自然语言查询 |

---

## 🔧 使用方法

### 1. 启动服务

```bash
cd backend
uv sync
uv run python start_unified.py
```

### 2. 调用 API

```bash
# 获取数据集结构
curl http://localhost:8000/api/v1/metadata/schema/{dataset_id}

# 搜索数据集
curl "http://localhost:8000/api/v1/metadata/search?q=销售数据"

# 自然语言查询
curl -X POST http://localhost:8000/api/v1/metadata/query \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": "xxx", "question": "数据有多少行？"}'
```

### 3. 在 Agent 中使用

```python
from langgraph.prebuilt import create_react_agent
from backend.src.agents.dataset_tools.agent_tools import DATASET_TOOLS

agent = create_react_agent(llm, tools=DATASET_TOOLS)

# Agent 现在可以：
# - search_datasets("用户行为数据")
# - get_dataset_schema("dataset_123")
# - get_dataset_quality("dataset_123")  
# - query_with_nl("dataset_123", "销售额最高的产品是什么？")
```

---

## 📊 AI-Native 特性总结

| 特性 | 说明 | 状态 |
|------|------|------|
| 语义类型推断 | 自动识别 ID、时间、金额等类型 | ✅ |
| 业务描述 | 生成字段的业务含义 | ✅ |
| 质量评分 | 完整性/唯一性/一致性评分 | ✅ |
| 数据摘要 | 自动生成数据理解报告 | ✅ |
| Agent 工具 | LangGraph 可用工具 | ✅ |
| 自然语言查询 | 用自然语言提问 | ✅ |
| 血缘追溯 | 数据来源/去向追踪 | ✅ |

---

## 📝 注意事项

1. 部分功能需要连接实际的 dataset repository 实现
2. 自然语言查询需要 LLM 支持
3. 确保 API 服务启动后再调用

---

*本文档由 AI 助手生成 - 2026-03-10*
