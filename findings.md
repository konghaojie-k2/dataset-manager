# Findings & Decisions

## Requirements

### 用户核心需求
- 支持上传和处理大文件（最大 10GB）
- 引擎智能选择是默认选项（无需手动指定）
- 优化性能，使大文件也能快速预览和分析
- 保持现有功能的准确性

### 功能需求
- 根据文件大小自动选择最佳引擎
- 快速预览（5-10秒）
- 后台完整分析（异步）
- 支持 Parquet 转换（按需）
- 支持文件压缩（按需）
- 实时进度推送

### 性能需求
- 上传响应时间：≤10秒（1GB 文件）
- 内存占用：≤原来的 10%
- 支持 10GB 文件处理
- 分析速度：≥5倍提升

### 技术需求
- 使用 Dask 进行并行处理（中等数据集）
- 使用 Polars 进行极致性能（大数据集）
- 智能采样策略
- 流式处理大文件
- 保持向后兼容性

## Research Findings

### 现有代码分析
- data_analyzer.py: 使用 pandas.read_csv() 全量加载，内存占用大
- data_quality_analyzer.py: 逐列处理，适合并行化
- business_analysis_service.py: LLM 分析只需要采样数据
- 所有分析都是同步的，缺乏异步支持

### 技术方案对比
| 方案 | 优点 | 缺点 | 适用场景 |
|------|-----|-------|---------|
| Pandas | 成熟、易用、生态丰富 | 内存限制、单线程 | 小数据集（<100MB） |
| Dask | 并行计算、分块处理、兼容 Pandas | 学习曲线、调试困难 | 中大数据集（100MB-10GB） |
| Polars | 极致性能、低内存、Lazy API | 生态较新、API 不同 | 大数据集（>1GB） |

### 引擎选择策略
- **小数据集（<100MB）**: Pandas（全量加载，速度快）
- **中等数据集（100MB-1GB）**: Dask（并行处理，内存效率高）
- **大数据集（>1GB）**: Dask 或 Polars（流式处理，低内存占用）

### 采样策略
- **小数据集**: 采样 1000 行
- **中等数据集**: 采样 10000 行
- **大数据集**: 采样 100000 行
- 采样数据用于：快速预览、LLM 分析、初步统计
- 完整数据用于：深度分析、质量检查

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| 引擎智能选择作为默认行为 | 用户体验最好，无需手动指定引擎类型 |
| 使用 FastDataProcessor 统一接口 | 封装引擎选择逻辑，简化使用 |
| 保持现有 API 向后兼容 | 不破坏现有代码，渐进式迁移 |
| 采样数据用于 LLM 分析 | LLM 不需要全量数据，采样足够且快速 |
| Parquet 转换和文件压缩作为按需功能 | 不是所有用户都需要，避免不必要的资源消耗 |
| 使用上下文管理器自动释放资源 | 防止内存泄漏，确保资源清理 |
| 延迟加载（Dask/Polars Lazy） | 只在真正需要时才计算，节省资源 |

### 引擎能力对比
| 特性 | Pandas | Dask | Polars |
|------|-------|------|-------|
| 全量加载 | ✅ | ❌ | ❌ |
| 并行计算 | ❌ | ✅ | ✅ |
| 流式处理 | ❌ | ✅ | ✅ |
| Lazy API | ❌ | ❌ | ✅ |
| 内存占用 | 高 | 低 | 极低 |
| 性能 | 快（小数据） | 快（中大数据） | 极快（大数据） |
| 学习曲线 | 低 | 中 | 中 |
| 生态系统 | 成熟 | 较新 | 新 |

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| uv sync 下载超时 | 切换到官方 PyPI 源 |
| 文件修改冲突 | 重新读取文件后再编辑 |
| 依赖安装时间较长 | 下载大文件（Dask、Polars、PyArrow），预计需要较长时间 |

## Resources

### 相关文档
- Dask 文档: https://docs.dask.org/
- Polars 文档: https://pola.rs/
- Pandas 文档: https://pandas.pydata.org/

### 项目文件
- 核心模块: `src/core/fast_data_processor.py`
- 引擎选择: `src/core/engine_selector.py`
- 采样策略: `src/core/sampling_strategy.py`
- Parquet 转换器: `src/core/parquet_converter.py`
- 文件压缩器: `src/core/file_compressor.py`

### 配置文件
- `src/config/settings.py`: 大数据处理配置
- `.env`: 环境变量配置

## Visual/Browser Findings

- 无（本任务不涉及视觉内容）

---

**REMINDER: The 2-Action Rule**
After every 2 view/browser/search operations, you MUST update this file.
*This prevents visual information from being lost*