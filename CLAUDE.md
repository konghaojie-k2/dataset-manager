# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern data management system featuring **LLM-driven intelligent data analysis** and **data lineage management**. The system uses LangGraph for agent orchestration and DeepSeek LLMs for intelligent analysis.

### Architecture Overview

The system is built around **LangGraph Agents** that autonomously analyze data:

```
┌─────────────────────────────┐
│  Agent Chat UI (Port 3000)  │
│  - Data set management       │
│  - File upload → FastAPI     │
│  - Agent chat interface      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Port 8000 (统一入口)                    │
│  ┌───────────────────────────────────┐  │
│  │ FastAPI Extension                 │  │
│  │ - File upload/download           │  │
│  │ - Analysis results API           │  │
│  │ - Lineage/Tags management        │  │
│  └───────────────────────────────────┘  │
│              │                           │
│  ┌───────────▼───────────────────────┐  │
│  │ LangGraph Agents                  │  │
│  │ - data_processing_agent           │  │
│  │ - query_agent                      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Key Technologies
- **Backend**: FastAPI + LangGraph + LangChain + DeepSeek LLM
- **Frontend**: agent-chat-ui (Next.js + TypeScript + Tailwind CSS)
- **Agent Framework**: LangGraph with React Agents
- **Package Management**: uv (Python) with Aliyun mirror, pnpm (Node.js)
- **LLM**: DeepSeek API for intelligent analysis

### Key Features
- **Autonomous Analysis**: Agents automatically decide what analysis to perform after file upload
- **Real-time Progress**: SSE streaming of analysis progress
- **Dynamic Results**: Different analyses displayed based on data characteristics
- **Data Lineage**: Track upstream/downstream dataset relationships

## Common Commands

### Backend Development

```bash
cd backend

# Install dependencies (using uv with Aliyun mirror)
uv sync

# Run unified server (LangGraph + FastAPI Extension)
uv run python start_unified.py

# Run with LangGraph dev server only
langgraph dev

# Run specific Python script (Windows - no && chaining)
cd "C:\CODE\dataset-manager\backend"
uv run python script_name.py

# Run tests (when tests exist)
uv run pytest
```

### Frontend Development

```bash
cd agent-chat-ui

# Install dependencies
pnpm install

# Run development server (port 3000)
pnpm dev

# Build for production
pnpm build

# Lint code
pnpm lint
```

### Environment Setup

**Backend (`.env`):**
```bash
# Required for LLM analysis
DATASET_MANAGER_DEEPSEEK_API_KEY=sk-xxx
DATASET_MANAGER_DEEPSEEK_BASE_URL=https://api.deepseek.com/v1/

# Optional: Supabase cloud storage
DATASET_MANAGER_SUPABASE_URL=xxx
DATASET_MANAGER_SUPABASE_SERVICE_KEY=xxx
```

**Frontend (`.env.local`):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_DATA_PROCESSING_AGENT=data_processing_agent
NEXT_PUBLIC_QUERY_AGENT=query_agent
```

## Architecture

### Backend Structure

```
backend/
├── langgraph.json           # LangGraph configuration
├── start_unified.py         # Unified server startup script
├── fastapi_extension.py     # Port 8000 FastAPI Extension
│
├── src/
│   ├── agents/              # LangGraph Agent definitions
│   │   ├── data_processing/ # Data Processing Agent (autonomous analysis)
│   │   │   ├── graph.py     # Agent graph definition
│   │   │   ├── tools.py     # Analysis tools (business, quality, enhanced)
│   │   │   └── prompts.py   # Chinese system prompts
│   │   ├── query/           # Query Agent (search, preview)
│   │   │   ├── graph.py     # Agent graph definition
│   │   │   ├── tools.py     # Query tools
│   │   │   └── prompts.py   # Chinese system prompts
│   │   └── shared/
│   │       └── llm.py       # LLM factory (DeepSeek via ChatOpenAI)
│   │
│   ├── core/                # Core business logic (preserved)
│   │   ├── dataset_service.py
│   │   ├── lineage_manager.py
│   │   └── tag_service.py
│   │
│   ├── graph/               # LangGraph workflows (preserved)
│   │   ├── workflow.py       # Industrial analysis workflow
│   │   └── data_quality_workflow.py
│   │
│   ├── server/              # FastAPI routes
│   │   ├── routes.py        # Main API routes
│   │   └── api/v1/          # API v1 endpoints
│   │       ├── lineage.py   # Data lineage endpoints
│   │       ├── tags.py      # Tag management
│   │       └── version_control.py
│   │
│   ├── tools/               # Analysis utilities
│   │   ├── data_analyzer.py
│   │   └── report_manager.py
│   │
│   └── config/
│       └── settings.py      # Configuration
```

### Frontend Structure (agent-chat-ui)

```
agent-chat-ui/src/
├── app/
│   └── page.tsx             # Main page (split layout)
├── components/
│   ├── analysis/            # Analysis components
│   │   ├── AnalysisProgressPanel.tsx  # Real-time progress display
│   │   └── DynamicResultView.tsx      # Dynamic result display
│   ├── dataset/             # Dataset management
│   │   ├── DatasetList.tsx            # Dataset list with search
│   │   ├── DatasetUpload.tsx          # Drag-drop upload
│   │   └── TagManager.tsx             # Tag management
│   ├── visualization/      # Visualization
│   │   └── LineageGraph.tsx           # Lineage visualization
│   ├── ui/                 # UI components
│   │   ├── badge.tsx
│   │   └── markdown-renderer.tsx
│   └── thread/              # Agent chat interface
│
└── lib/
    └── api-extension.ts     # API client for FastAPI + LangGraph
```

## Key Architectural Patterns

### LangGraph Agents

**Data Processing Agent** (`src/agents/data_processing/`)
- **Purpose**: Autonomous analysis after file upload
- **Workflow**:
  1. Scan data features (100 rows sample)
  2. Decide which analyses to perform (business/quality/enhanced)
  3. Emit progress events via SSE
  4. Return complete analysis results
- **Tools**: `scan_dataset`, `analyze_business`, `analyze_quality`, `analyze_enhanced`, `emit_progress`

**Query Agent** (`src/agents/query/`)
- **Purpose**: Dataset search, preview, and Q&A
- **Tools**: `search_datasets`, `get_dataset_preview`, `get_dataset_details`, `analyze_intent`

### Unified Server Architecture

`start_unified.py` runs both services concurrently:
- **LangGraph dev server** (port 2024) - Agent execution
- **FastAPI Extension** (port 8000) - API gateway + file operations

### API Endpoints

**FastAPI Extension (Port 8000):**
```
POST   /api/v1/datasets/upload
GET    /api/v1/datasets
GET    /api/v1/datasets/{id}/download
GET    /api/v1/datasets/{id}/preview
PUT    /api/v1/datasets/{id}/tags

GET    /api/v1/datasets/{id}/business-analysis-results
GET    /api/v1/datasets/{id}/quality-analysis-results
GET    /api/v1/datasets/{id}/enhanced-analysis-results
GET    /api/v1/datasets/{id}/analysis-results    # All results

POST   /api/agents/data_processing_agent/analyze
POST   /api/agents/query_agent/query
GET    /api/analysis/{id}/progress              # SSE stream

GET    /api/v1/lineage/{id}/graph
GET    /api/v1/lineage/{id}/upstream
GET    /api/v1/lineage/{id}/downstream
```

### Analysis Pipeline Flow

```
File Upload (DatasetUpload.tsx)
    ↓
datasetAPI.uploadAndAnalyze()
    ↓
POST /api/v1/datasets/upload
    ↓
POST /api/agents/data_processing_agent/analyze
    ↓
LangGraph Agent:
  - scan_dataset → Analyze first 100 rows
  - Decision: "This is industrial data"
  - analyze_business → Business analysis
  - analyze_quality → Quality analysis
  - emit_progress → SSE events
    ↓
Frontend receives progress via SSE
    ↓
GET /api/v1/datasets/{id}/analysis-results
    ↓
DynamicResultView displays results
```

## Important Development Notes

### Python Requirements
- **Always use UTF-8 encoding** at the top of every Python file:
  ```python
  #!/usr/bin/env python3
  # -*- coding: utf-8 -*-
  ```
- **Use uv** for Python package management (Aliyun mirror configured)
- **Windows environment**: No `&&` chaining. Use separate commands or batch files
- **Delete temporary test files** after completion

### Agent Development
- Agents use `create_react_agent()` from LangGraph
- Tools are defined with `@tool` decorator and Pydantic schemas
- System prompts are in Chinese for professional analysis
- Lazy imports in tools to avoid circular dependencies

### Frontend Development
- Uses Next.js 15 with App Router
- shadcn/ui components via `@radix-ui`
- Tailwind CSS v4 for styling
- TypeScript for type safety

### Error Handling
- Frontend API client includes timeout handling
- Backend uses `loguru` for logging
- SSE progress streaming for real-time feedback

### File Processing
- Supports CSV and ZIP files
- Large files sampled (configurable via `DATASET_MANAGER_SAMPLE_ROWS`)
- Temporary extraction files cleaned up after processing

## Testing

Currently minimal test files exist. When adding tests:
- Use `pytest` for backend testing
- Place tests in `backend/tests/` directory
- Follow pattern: `test_<module_name>.py`

## API Documentation

When backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- LangGraph Studio: `http://localhost:2024` (when running)

## Quick Start

1. **Start Backend:**
   ```bash
   cd backend
   uv run python start_unified.py
   ```

2. **Start Frontend:**
   ```bash
   cd agent-chat-ui
   pnpm dev
   ```

3. **Access Application:**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - LangGraph Studio: http://localhost:2024

## Data Flow Example

1. User uploads CSV via `DatasetUpload.tsx`
2. File uploaded to `/api/v1/datasets/upload`
3. Agent analysis triggered: `/api/agents/data_processing_agent/analyze`
4. Agent scans data → decides analysis type → executes analysis
5. Progress streamed via `/api/analysis/{id}/progress`
6. Frontend displays progress in `AnalysisProgressPanel.tsx`
7. On completion, results fetched via `/api/v1/datasets/{id}/analysis-results`
8. Results displayed in `DynamicResultView.tsx`
