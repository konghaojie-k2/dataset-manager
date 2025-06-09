# 数据集管理系统工程概述

## 项目基本信息

**项目名称**: Dataset Manager (数据集管理系统)  
**技术栈**: Python FastAPI + 原生JavaScript  
**数据库**: SQLite (混合存储策略)  
**AI集成**: DeepSeek API + LangGraph工作流  
**包管理**: uv包管理器  
**版本**: 0.1.0  

## 核心功能模块

### 1. 数据集管理
- **文件上传**: 支持CSV和ZIP文件，最大100MB
- **数据预览**: 提供数据集内容预览功能
- **元数据提取**: 自动分析数据集结构和统计信息
- **文件下载**: 支持数据集文件下载
- **数据集删除**: 完整的数据集删除管理

### 2. 智能分析系统
- **业务分析**: 
  - 识别设备ID列和时间列
  - 分析业务语义和控制关系
  - 生成业务理解报告
- **质量分析**:
  - 评估数据完整性、准确性、一致性和及时性
  - 生成质量评分和改进建议
- **报告生成**: 支持Markdown格式的详细分析报告

### 3. 标签系统 ⭐
- **标签管理**: 创建、编辑、删除标签
- **标签分类**: 支持标签分类管理
- **数据集标签**: 为数据集添加和管理标签
- **标签搜索**: 支持模糊搜索和热门标签展示
- **数据同步**: 标签数据库与数据集数据库双向同步

## 技术架构

### 后端架构
```
FastAPI应用
├── 核心业务层 (src/core/)
│   ├── dataset_service.py     # 数据集服务层
│   ├── dataset_repository.py  # 数据集仓储层
│   ├── tag_service.py         # 标签服务层
│   ├── tag_repository.py      # 标签仓储层
│   ├── file_service.py        # 文件管理服务
│   └── metadata_service.py    # 元数据处理服务
├── 服务器层 (src/server/)
│   ├── app.py                 # FastAPI应用入口
│   ├── routes.py              # 数据集路由
│   └── api/v1/tags.py         # 标签API路由
├── AI工作流 (src/graph/)
│   ├── workflow.py            # LangGraph工作流定义
│   └── nodes.py               # 工作流节点
└── 配置管理 (src/config/)
    └── settings.py            # 应用配置
```

### 前端架构
```
原生JavaScript模块化设计
├── main.js          # 主应用入口和状态管理
├── datasets.js      # 数据集管理模块
├── tags.js          # 标签管理模块
├── api.js           # API请求封装
├── utils.js         # 工具函数库
├── analysis.js      # 分析功能模块
├── upload.js        # 文件上传模块
└── pagination.js    # 分页组件
```

### 存储策略
- **SQLite数据库**: 存储结构化元数据（数据集信息、标签、列信息）
- **JSON文件**: 存储复杂的分析结果和报告
- **文件系统**: 存储上传的数据集文件
- **内存缓存**: 提高数据访问性能

## 数据库设计

### 主要表结构

#### 数据集表 (datasets)
```sql
CREATE TABLE datasets (
    id TEXT PRIMARY KEY,              -- 数据集唯一标识
    name TEXT NOT NULL,               -- 数据集名称
    description TEXT,                 -- 数据集描述
    file_path TEXT NOT NULL,          -- 文件路径
    file_size INTEGER NOT NULL,       -- 文件大小
    upload_time TIMESTAMP NOT NULL,   -- 上传时间
    tags TEXT,                        -- 标签JSON数组 ⭐
    industry TEXT,                    -- 行业分类
    processing_status TEXT DEFAULT 'uploaded', -- 处理状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 标签表 (tags)
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,        -- 标签名称
    description TEXT,                 -- 标签描述
    color TEXT,                       -- 标签颜色
    category TEXT,                    -- 标签分类
    usage_count INTEGER DEFAULT 0,    -- 使用次数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 数据集标签关联表 (dataset_tags)
```sql
CREATE TABLE dataset_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT NOT NULL,         -- 数据集ID
    tag_name TEXT NOT NULL,           -- 标签名称
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
);
```

## 重要修复记录

### 🔧 标签系统数据同步修复 (2025-06-09)

#### 问题描述
- **现象**: 标签保存成功但主页面不显示更新
- **根本原因**: 标签数据库与数据集数据库数据不同步
- **影响**: 用户体验差，数据一致性问题

#### 问题分析
1. 标签系统使用独立的标签数据库存储标签信息
2. 数据集列表API从数据集数据库获取数据
3. 两个数据库之间缺乏同步机制
4. 前端保存逻辑存在重复渲染和数据竞争

#### 解决方案

**1. 后端数据同步机制**
```python
# 在 src/core/tag_repository.py 中添加
def _sync_dataset_tags_to_dataset_db(self, dataset_id: str, tag_names: List[str]) -> None:
    """同步标签到数据集数据库"""
    dataset_db_path = self.db_path.parent / "datasets.db"
    
    if dataset_db_path.exists():
        with sqlite3.connect(dataset_db_path) as conn:
            cursor = conn.cursor()
            tags_json = json.dumps(tag_names, ensure_ascii=False)
            cursor.execute("""
                UPDATE datasets 
                SET tags = ?, updated_at = ?
                WHERE id = ?
            """, (tags_json, datetime.now(), dataset_id))
            conn.commit()
```

**2. 前端逻辑优化**
```javascript
// 简化 saveDatasetTags 方法，移除重复操作
async saveDatasetTags(datasetId) {
    const selectedTags = Tags.getSelectedTags(tagSelector);
    await Tags.updateDatasetTags(datasetId, selectedTags);
    this.closeTagEditModal();
    await App.refreshDatasets(); // 只保留一次刷新
    UI.showMessage('标签保存成功', CONFIG.MESSAGE.TYPES.SUCCESS);
}
```

#### 修复效果
- ✅ 标签更新后立即在主页面显示
- ✅ 数据库数据保持一致性
- ✅ 前端逻辑更加简洁
- ✅ 用户体验显著改善

### 🔧 JavaScript错误修复

#### 修复内容
1. **API响应安全检查**: 添加对`response`和`response.data`的存在性检查
2. **数组安全访问**: 使用`(this.allTags || [])`防止undefined错误
3. **DOM元素安全检查**: 在操作DOM前检查元素存在性
4. **this上下文修复**: 使用`const self = this`保存上下文引用
5. **API响应结构统一**: 处理不同API返回的响应结构差异

## 项目目录结构

```
dataset-manager/
├── src/                          # 后端源码
│   ├── core/                     # 核心业务逻辑
│   │   ├── dataset_service.py    # 数据集服务层
│   │   ├── dataset_repository.py # 数据集仓储层
│   │   ├── tag_service.py        # 标签服务层 ⭐
│   │   ├── tag_repository.py     # 标签仓储层 ⭐
│   │   ├── file_service.py       # 文件管理服务
│   │   ├── metadata_service.py   # 元数据处理服务
│   │   └── database_repository.py # 数据库基础仓储
│   ├── server/                   # 服务器配置
│   │   ├── app.py               # FastAPI应用入口
│   │   ├── routes.py            # 数据集路由
│   │   ├── middleware.py        # 中间件
│   │   ├── dependencies.py      # 依赖注入
│   │   └── api/v1/
│   │       └── tags.py          # 标签API路由 ⭐
│   ├── graph/                    # LangGraph工作流
│   │   ├── workflow.py          # 工作流定义
│   │   ├── nodes.py             # 工作流节点
│   │   └── builder.py           # 工作流构建器
│   ├── llms/                     # LLM集成
│   │   ├── factory.py           # LLM工厂
│   │   └── deepseek.py          # DeepSeek集成
│   ├── schemas/                  # 数据模型定义
│   │   ├── dataset.py           # 数据集模型
│   │   └── tag.py               # 标签模型 ⭐
│   ├── tools/                    # 工具模块
│   │   └── report_manager.py    # 报告管理器
│   ├── prompts/                  # AI提示词模板
│   │   └── templates/           # 提示词模板文件
│   ├── config/                   # 配置管理
│   │   └── settings.py          # 应用配置
│   └── utils/                    # 工具函数
├── web/                          # 前端资源
│   ├── assets/
│   │   ├── js/                  # JavaScript文件
│   │   │   ├── main.js          # 主应用入口
│   │   │   ├── datasets.js      # 数据集管理 ⭐
│   │   │   ├── tags.js          # 标签管理 ⭐
│   │   │   ├── api.js           # API封装
│   │   │   ├── utils.js         # 工具函数
│   │   │   ├── analysis.js      # 分析功能
│   │   │   ├── upload.js        # 文件上传
│   │   │   ├── config.js        # 前端配置
│   │   │   ├── pagination.js    # 分页组件
│   │   │   ├── quality.js       # 质量分析
│   │   │   ├── reports.js       # 报告管理
│   │   │   └── markdown.js      # Markdown处理
│   │   └── css/                 # 样式文件
│   │       ├── main.css         # 主样式
│   │       ├── tags.css         # 标签样式 ⭐
│   │       └── components.css   # 组件样式
│   ├── static/                  # 静态资源
│   └── index.html               # 主页面
├── metadata/                     # 元数据存储
│   ├── datasets.db              # 主数据库 ⭐
│   └── analysis_results/        # 分析结果JSON文件
├── uploads/                      # 上传文件存储
├── reports/                      # 分析报告存储
├── logs/                        # 日志文件
├── tests/                       # 测试文件
├── docs/                        # 文档目录
├── examples/                    # 示例文件
├── config/                      # 配置文件
├── pyproject.toml               # Python项目配置
├── uv.lock                      # 依赖锁定文件
├── main.py                      # 应用入口
├── start_dev.py                 # 开发服务器启动脚本
└── README.md                    # 项目说明
```

## 开发规范

### 后端开发规范
- **包管理**: 使用uv包管理器 (`uv add package_name`)
- **路径处理**: 使用pathlib库处理文件路径
- **日志系统**: 使用loguru库记录日志
- **注释规范**: 所有注释和文档使用中文，代码使用英文
- **错误处理**: 统一的异常处理和日志记录

### 前端开发规范
- **框架选择**: 原生JavaScript，无框架依赖
- **模块化**: 每个功能模块独立文件
- **API调用**: 统一的API封装和错误处理
- **响应式设计**: 支持移动端和桌面端
- **代码风格**: 使用ES6+语法，统一的命名规范

### 数据库规范
- **主数据库**: SQLite作为主要数据存储
- **辅助存储**: JSON文件存储复杂分析结果
- **约束设计**: 使用外键约束确保数据一致性
- **索引优化**: 为常用查询字段创建索引

## 环境配置

### 必需环境变量
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### Python环境要求
- Python >= 3.11
- 使用uv管理依赖和虚拟环境

### 启动方式
```bash
# 开发环境启动
uv run python start_dev.py

# 访问地址
http://127.0.0.1:8000

# API文档
http://127.0.0.1:8000/docs
```

## 系统配置

### 文件上传限制
- **支持格式**: CSV, ZIP
- **最大文件大小**: 100MB
- **存储位置**: `uploads/` 目录

### AI分析配置
- **模型提供商**: DeepSeek
- **推理模型**: deepseek-chat
- **基础模型**: deepseek-chat
- **视觉模型**: deepseek-chat
- **温度参数**: 0.1

### 数据处理配置
- **采样行数**: 1000行
- **预览行数**: 10行
- **分页大小**: 10条/页

## 关键特性

### 🔥 混合存储策略
- SQLite存储结构化数据，支持高效查询
- JSON文件存储分析结果，保持数据灵活性
- 内存缓存提高访问性能

### 🔥 智能工作流
- 基于LangGraph的可扩展工作流引擎
- 支持业务分析和质量分析两大工作流
- 可视化的分析进度和结果展示

### 🔥 标签系统
- 完整的标签生命周期管理
- 支持标签分类和搜索
- 双数据库同步机制确保数据一致性

### 🔥 响应式设计
- 原生JavaScript实现，无框架依赖
- 模块化架构，易于维护和扩展
- 移动端友好的响应式界面

## 扩展建议

### 短期优化
1. **用户系统**: 添加用户认证和权限管理
2. **批量操作**: 支持批量上传和分析
3. **数据可视化**: 集成图表库展示分析结果
4. **性能优化**: 添加Redis缓存

### 长期规划
1. **微服务架构**: 拆分为独立的微服务
2. **容器化部署**: Docker容器化部署
3. **分布式存储**: 支持分布式文件存储
4. **实时分析**: 支持流式数据分析

## 注意事项

### ⚠️ 重要提醒
1. **标签系统**: 已修复数据同步问题，标签更新会同时更新两个数据库
2. **文件上传**: 确保uploads目录有写入权限
3. **AI分析**: 需要有效的DeepSeek API密钥
4. **数据库**: 生产环境建议迁移到PostgreSQL
5. **前端缓存**: 静态资源有版本控制，修改后需清除浏览器缓存

### 🐛 已知问题
- 大文件上传可能超时（>100MB）
- 复杂数据集分析耗时较长
- 并发分析任务可能影响性能

### 📝 维护建议
- 定期清理临时文件和日志
- 监控数据库大小和性能
- 备份重要的分析结果
- 更新AI模型和提示词模板

---

**最后更新**: 2025-06-09  
**文档版本**: 1.0  
**维护者**: AI Assistant  

> 这份文档记录了数据集管理系统的完整架构和重要修复记录，特别是标签系统的数据同步机制修复。下次接手的Agent可以通过这份文档快速了解项目结构和关键技术点。 