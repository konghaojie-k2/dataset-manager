# AGENTS

<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

How to use skills:
- Invoke: Bash("openskills read <skill-name>")
- The skill content will load with detailed instructions on how to complete the task
- Base directory provided in output for resolving bundled resources (references/, scripts/, assets/)

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
- Each skill invocation is stateless
</usage>

<available_skills>

<skill>
<name>langgraph-agent-ui</name>
<description>Full-stack LangGraph Agent application template with integrated Agent Chat UI frontend. Use when building AI agent applications that require: (1) LangGraph backend with autonomous agent orchestration, (2) Next.js frontend with chat interface, (3) Real-time streaming responses, (4) File upload and data processing capabilities, (5) FastAPI business logic integration.</description>
<location>global</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>

---

## Build / Lint / Test Commands

### Backend Commands

```bash
cd backend

# Install dependencies (using uv with Aliyun mirror)
uv sync

# Run unified server (LangGraph + FastAPI)
uv run python start_unified.py

# Run with LangGraph dev server only
langgraph dev

# Run specific Python script
cd "C:\CODE\dataset-manager\backend"
uv run python script_name.py

# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/test_file.py

# Run single test function
uv run pytest tests/test_file.py::test_function_name

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Frontend Commands

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

# Lint and fix
pnpm lint --fix
```

---

## Code Style Guidelines

### Python (Backend)

**Encoding:**
- All Python files MUST include UTF-8 encoding at the top:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
```

**Imports:**
- Use absolute imports with `src.` prefix (e.g., `from src.core.dataset_service import DatasetService`)
- Group imports: standard library → third-party → local application
- Sort imports alphabetically within groups
- Use lazy imports in LangGraph tools to avoid circular dependencies

**Types:**
- Use type hints for all function parameters and return values
- Use `typing` module: `Dict`, `List`, `Optional`, `Any`, `Union`
- Prefer Pydantic models over dictionaries for structured data

**Naming:**
- `PascalCase` for classes: `DatasetService`, `DataAnalyzer`
- `snake_case` for functions and variables: `upload_dataset`, `file_path`
- `SCREAMING_SNAKE_CASE` for constants: `MAX_FILE_SIZE`
- Private methods/attributes prefixed with `_`: `_internal_method`

**Error Handling:**
- Use `try/except` with specific exception types
- Log errors with `loguru.logger` before re-raising
- Raise descriptive `ValueError` or custom exceptions for validation errors
- Avoid bare `except:` clauses

**Logging:**
- Use `from loguru import logger`
- Use appropriate levels: `logger.info()`, `logger.warning()`, `logger.error()`, `logger.debug()`
- Include relevant context in log messages

**Documentation:**
- Use docstrings for all public classes and functions
- Write docstrings in Chinese for business logic
- Include Args and Returns sections for functions with parameters

### TypeScript (Frontend)

**Naming:**
- `PascalCase` for components: `DatasetUpload.tsx`, `AnalysisProgressPanel.tsx`
- `camelCase` for functions and variables: `handleUpload`, `datasetList`
- Use descriptive names: avoid abbreviations except well-known ones

**Types:**
- Use TypeScript interfaces for component props
- Avoid `any` type; use `unknown` when type is uncertain
- Use proper typing for async operations

**Components:**
- Use functional components with hooks
- Place components in `components/` directory organized by feature
- Use shadcn/ui components from `@/components/ui`

---

## Environment Setup

**Backend (.env):**
```bash
DATASET_MANAGER_DEEPSEEK_API_KEY=sk-xxx
DATASET_MANAGER_DEEPSEEK_BASE_URL=https://api.deepseek.com/v1/
DATASET_MANAGER_SUPABASE_URL=xxx
DATASET_MANAGER_SUPABASE_SERVICE_KEY=xxx
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## Important Notes

- Use `uv` for Python package management (Aliyun mirror configured)
- **Windows environment**: No `&&` chaining in commands
- Delete temporary test files after completion
- Run `uv run pytest` to verify changes before committing
