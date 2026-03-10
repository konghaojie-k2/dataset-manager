# 数据集管理系统 - 开发计划 (AI-Native 优先)

**创建时间：** 2026-03-10
**更新：** 2026-03-10 - 调整优先级，AI-Native 功能优先

---

## 📊 项目现状分析

### 技术架构

```
前端 (agent-chat-ui) - Next.js + TypeScript + Tailwind  端口: 3000
                               ↓
后端 (backend) - FastAPI + LangGraph + LangChain       端口: 8000
```

### 当前完成度

| 模块 | 完成度 | 状态 |
|------|--------|------|
| 后端核心服务 | 100% | ✅ |
| 大数据优化 (Dask/Polars) | 100% | ✅ |
| 钉钉 OAuth | 100% | ✅ |
| 前端基础 UI | 100% | ✅ |
| 智能查询 Agent | 100% | ✅ |
| 数据集上传/浏览 | 100% | ✅ |
| Parquet 转换 | 100% | ⚠️ (缺前端) |
| 文件压缩 | 100% | ⚠️ (缺前端) |

---

## 🎯 开发计划（AI-Native 优先）

### 阶段一：AI-Native 核心功能（高优先级）

#### 1.1 增强语义元数据

**目标：** 让 Agent 快速理解数据内容

**文件：** `backend/src/core/enhanced_metadata_service.py`

**功能：**
- [ ] 自动生成字段语义描述
- [ ] 数据分布统计（枚举值、范围、均值等）
- [ ] 数据质量评分（完整性、准确性、一致性）
- [ ] 存储在元数据中，可被 Agent 查询

**预计工时：** 3-4 小时

#### 1.2 Agent 工具化

**目标：** 将数据集操作封装为 Agent 可调用的工具

**文件：** `backend/src/agents/dataset_tools/`

**工具清单：**
| 工具名 | 功能 | 预计工时 |
|--------|------|----------|
| `search_datasets` | 语义搜索数据集 | 2h |
| `get_dataset_schema` | 获取数据结构 | 1h |
| `analyze_data_quality` | 分析数据质量 | 2h |
| `get_data_lineage` | 获取数据血缘 | 1h |
| `query_with_llm` | 自然语言查询 | 3h |

#### 1.3 自然语言查询层

**目标：** Agent 不写 SQL，直接用自然语言查询

**文件：** `backend/src/agents/query/`

**功能：**
- [ ] LLM 理解自然语言意图
- [ ] 自动转换为数据查询
- [ ] 返回自然语言结果

**预计工时：** 3-4 小时

#### 1.4 自动数据理解

**目标：** 上传数据后自动生成理解报告

**文件：** `backend/src/core/data_understanding_service.py`

**功能：**
- [ ] 数据摘要（一句话描述）
- [ ] 关键洞察（发现规律）
- [ ] 建议用途（适合做什么）
- [ ] 潜在问题（缺失值、异常值）

**预计工时：** 2-3 小时

---

### 阶段二：前端功能补全（中优先级）

#### 2.1 Parquet 转换对话框

**文件：** `agent-chat-ui/src/components/dataset/ConvertDialog.tsx`

**预计工时：** 2-3 小时

#### 2.2 文件压缩对话框

**文件：** `agent-chat-ui/src/components/dataset/CompressDialog.tsx`

**预计工时：** 2-3 小时

#### 2.3 DatasetCard 操作菜单

**预计工时：** 1-2 小时

---

### 阶段三：测试和验证（低优先级）

- 后端单元测试
- API 集成测试
- 性能对比测试

---

## 📋 详细任务清单

### Sprint 1: AI-Native 核心

| 任务 ID | 描述 | 预估工时 | 优先级 |
|---------|------|----------|--------|
| TASK-101 | 增强语义元数据服务 | 3-4h | P0 |
| TASK-102 | search_datasets 工具 | 2h | P0 |
| TASK-103 | get_dataset_schema 工具 | 1h | P0 |
| TASK-104 | analyze_data_quality 工具 | 2h | P0 |
| TASK-105 | get_data_lineage 工具 | 1h | P0 |
| TASK-106 | 自然语言查询层 | 3-4h | P0 |
| TASK-107 | 自动数据理解服务 | 2-3h | P0 |

### Sprint 2: 前端功能

| 任务 ID | 描述 | 预估工时 | 优先级 |
|---------|------|----------|--------|
| TASK-001 | ConvertDialog | 2-3h | P1 |
| TASK-005 | CompressDialog | 2-3h | P1 |
| TASK-009 | DatasetCard 操作菜单 | 1-2h | P1 |

---

## 🔧 技术栈

- **后端：** FastAPI + LangGraph + LangChain + DeepSeek LLM
- **前端：** Next.js + TypeScript + Tailwind CSS + shadcn/ui
- **大数据：** Dask + Polars + PyArrow

---

## 📝 备注

本开发计划由 AI 助手基于项目当前状态分析生成。
项目地址: https://github.com/konghaojie-k2/dataset-manager
