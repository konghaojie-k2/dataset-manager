# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern data management system built with FastAPI (backend) and Next.js (frontend), featuring **LLM-driven intelligent data analysis** and **data lineage management**. The system integrates LangGraph for workflow orchestration and uses DeepSeek LLMs for industrial domain identification and business analysis.

### Key Technologies
- **Backend**: FastAPI + LangChain + LangGraph + Supabase (optional cloud storage)
- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Package Management**: uv (Python) configured with Aliyun mirror
- **LLM**: DeepSeek API for intelligent analysis

## Common Commands

### Backend Development
```bash
cd backend

# Install dependencies (using uv with Aliyun mirror)
uv sync

# Run development server
uv run python start_dev.py

# Run specific Python script (Windows - no && chaining)
cd "C:\CODE\dataset-manager\backend"
uv run python script_name.py

# Run tests (when tests exist)
uv run pytest
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Run development server (port 3003)
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```

### Environment Setup
1. Copy `backend/.env.example` to `backend/.env`
2. Set required environment variables:
   - `DATASET_MANAGER_DEEPSEEK_API_KEY` - Required for LLM analysis
   - `DATASET_MANAGER_SUPABASE_URL` - Optional, for cloud storage
   - `DATASET_MANAGER_SUPABASE_SERVICE_KEY` - Optional, for Supabase access

## Architecture

### Backend Structure

```
backend/src/
├── core/                    # Core business logic
│   ├── dataset_service.py   # Main service orchestrating business workflows
│   ├── dataset_service_factory.py  # Factory for local/Supabase storage
│   ├── dataset_repository.py        # Local file-based repository
│   ├── supabase_dataset_repository.py  # Supabase-based repository
│   ├── file_service.py      # Local file operations
│   ├── supabase_file_service.py     # Supabase storage operations
│   ├── lineage_manager.py   # Data lineage tracking
│   ├── chat_service.py      # Chat interface service
│   └── tag_service.py       # Tag management
├── graph/                   # LangGraph workflow definitions
│   ├── workflow.py          # Main industrial analysis workflow
│   ├── state.py             # Workflow state management
│   ├── builder.py           # Workflow builder
│   ├── enhanced_nodes.py    # Enhanced analysis nodes
│   └── data_quality_workflow.py  # Data quality analysis
├── server/                  # FastAPI application
│   ├── app.py              # Application factory with middleware
│   ├── routes.py           # Main API routes
│   ├── api/v1/             # API v1 endpoints
│   │   ├── chat.py         # Chat endpoints
│   │   ├── lineage.py      # Data lineage endpoints
│   │   ├── tags.py         # Tag management
│   │   └── version_control.py  # Version control
│   └── dependencies.py     # Dependency injection
├── schemas/                 # Pydantic models
│   ├── dataset.py          # Dataset schemas
│   ├── chat.py             # Chat schemas
│   └── data_quality.py     # Quality analysis schemas
├── config/                  # Configuration
│   └── settings.py         # Settings with env variable loading
├── llms/                    # LLM initialization
│   └── llms.py             # DeepSeek LLM factory
├── tools/                   # Utility tools
│   ├── data_analyzer.py    # Data analysis utilities
│   ├── report_manager.py   # Report generation (MD files)
│   └── file_processor.py   # File processing (CSV/ZIP)
└── utils/                   # Helper utilities
    ├── version_control.py   # Version control logic
    └── helpers.py          # Common helpers
```

### Frontend Structure

```
frontend/src/
├── app/                     # Next.js app directory
├── components/              # React components
│   ├── chat/               # Chat interface components
│   ├── DataManagerLayout.tsx
│   ├── EnhancedDatasetList.tsx
│   ├── LineageVisualization.tsx
│   └── MetadataConfirmForm.tsx
├── lib/
│   └── api.ts              # API client with error handling
└── types/                  # TypeScript type definitions
    ├── dataset.ts
    ├── chat.ts
    └── a2ui.ts
```

## Key Architectural Patterns

### Storage Abstraction (Factory Pattern)
The system supports both local filesystem and Supabase cloud storage through a factory pattern:
- `DatasetServiceFactory` in `core/dataset_service_factory.py` chooses storage backend
- Both implementations share the same `DatasetRepository` and `FileService` interfaces
- Configure via `DATASET_MANAGER_SUPABASE_URL` and `DATASET_MANAGER_SUPABASE_SERVICE_KEY`

### Workflow Orchestration (LangGraph)
- Industrial data analysis is orchestrated through LangGraph workflows in `graph/workflow.py`
- Workflows support multiple analysis types: industrial, quality, business, and enhanced analysis
- State management through `AnalysisState` in `graph/state.py`
- Nodes can be added/modified in `graph/builder.py`

### Analysis Pipeline
1. **Upload** → Files stored (local or Supabase)
2. **Business Analysis** → `start_business_analysis()` → LangGraph workflow
3. **Quality Analysis** → `start_quality_analysis()` → DataQualityWorkflow
4. **Enhanced Analysis** → `start_enhanced_analysis()` → Domain + column importance identification

### Data Lineage
- `LineageManager` tracks upstream/downstream relationships
- Supports transformation types: filter, aggregate, join, transform
- Visualization data provided for frontend rendering

### Version Control
- Automatic duplicate detection via file/content hashing
- Three storage strategies: `full` (complete copy), `reference` (pointer only), `reject` (block upload)
- Configure via `DATASET_MANAGER_DUPLICATE_STORAGE_STRATEGY`

## Important Development Notes

### Python Requirements
- **Always use UTF-8 encoding** at the top of every Python file:
  ```python
  #!/usr/bin/env python3
  # -*- coding: utf-8 -*-
  ```
- **Use uv** for Python package management (configured with Aliyun mirror)
- **Windows environment**: No `&&` chaining in commands. Use separate commands or batch files
- **Delete temporary test files** after completion

### LLM Integration
- DeepSeek API is required for intelligent analysis features
- Configure `DATASET_MANAGER_DEEPSEEK_API_KEY` in `.env`
- LLM calls are made through `llms/llms.py` factory
- Analysis prompts are in `prompts/templates/` directory

### Error Handling
- Frontend API client includes 30s timeout and user-friendly error messages
- Backend uses `loguru` for logging
- Dataset status transitions are tracked: `uploaded` → `business_analyzing` → `business_completed` → `quality_analyzing` → `quality_completed`

### File Processing
- Supports CSV and ZIP files
- Large files are sampled (configurable via `DATASET_MANAGER_SAMPLE_ROWS`)
- Temporary extraction files are cleaned up after processing

## Testing

Currently no test files exist. When adding tests:
- Use `pytest` for backend testing
- Place tests in `backend/tests/` directory
- Follow the pattern: `test_<module_name>.py`

## API Documentation

When backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Frontend Configuration

- Next.js runs on port 3003 (configured in `package.json`)
- API proxy through Next.js: backend at `/api/v1` routes to `http://localhost:8000/api/v1`
- Configure `NEXT_PUBLIC_API_URL` in `.env.local` if needed
