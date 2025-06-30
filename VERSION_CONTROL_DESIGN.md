# 版本控制系统设计文档

## 📋 概述

本文档详细描述了数据集管理系统的版本控制设计方案，解决了用户提出的两个核心问题：

1. **数据源版本管理** - 如何识别同一份数据并进行版本标记
2. **数据报告版本管理** - JSON、报告和数据库的版本管理

## 🎯 设计目标

### 核心需求
- **数据去重**: 准确识别重复上传的数据
- **版本追踪**: 完整的版本历史记录
- **空间优化**: 避免重复存储，节省存储空间
- **报告版本化**: 分析结果和报告的版本管理
- **易于维护**: 清理旧版本，保持系统清洁

## 🏗️ 架构设计

### 整体架构

```
版本控制系统
├── 数据源版本管理
│   ├── 文件哈希计算 (SHA256)
│   ├── 内容哈希计算 (数据标准化)
│   ├── 重复检测机制
│   └── 版本关系管理
├── 报告版本管理
│   ├── JSON分析结果版本化
│   ├── Markdown报告版本化
│   ├── 版本历史记录
│   └── 自动清理机制
└── API接口层
    ├── 版本查询接口
    ├── 重复检测接口
    └── 版本清理接口
```

## 📊 数据源版本管理

### 1. 数据唯一性识别

#### 1.1 双重哈希机制

**文件哈希 (file_hash)**
- 算法: SHA256
- 用途: 检测完全相同的文件
- 计算: 对整个文件二进制内容计算哈希

**内容哈希 (content_hash)**
- 算法: SHA256
- 用途: 检测数据内容相同但格式不同的文件
- 计算: 
  1. 提取CSV数据到DataFrame
  2. 标准化数据格式（列排序、精度统一、时间格式统一）
  3. 计算标准化后的哈希值

#### 1.2 重复检测策略

```python
def detect_duplicate_data(new_file_hash, new_content_hash, existing_datasets):
    for dataset in existing_datasets:
        # 精确匹配：文件哈希完全相同
        if dataset.file_hash == new_file_hash:
            return dataset, "file_duplicate"
        
        # 内容匹配：数据内容相同但文件可能不同
        if dataset.content_hash == new_content_hash:
            return dataset, "content_duplicate"
    
    return None, "original"
```

### 2. 版本类型定义

| 版本类型 | 说明 | 版本号策略 | 存储策略 |
|----------|------|------------|----------|
| **original** | 原始版本 | 1.0 | 完整存储 |
| **updated** | 更新版本 | 递增 (1.1, 1.2...) | 完整存储 |
| **duplicate** | 重复数据 | 继承原版本号 | 引用存储 |

### 3. 数据库表结构

```sql
-- 在datasets表中新增版本控制字段
ALTER TABLE datasets ADD COLUMN file_hash TEXT;           -- 文件哈希值
ALTER TABLE datasets ADD COLUMN content_hash TEXT;        -- 内容哈希值
ALTER TABLE datasets ADD COLUMN version TEXT DEFAULT '1.0'; -- 版本号
ALTER TABLE datasets ADD COLUMN parent_version_id TEXT;   -- 父版本ID
ALTER TABLE datasets ADD COLUMN version_type TEXT DEFAULT 'original'; -- 版本类型
ALTER TABLE datasets ADD COLUMN version_notes TEXT;       -- 版本说明
```

### 4. 版本管理策略

#### 4.1 上传时处理流程

1. 文件上传
2. 计算文件哈希
3. 计算内容哈希
4. 检测重复数据
5. 根据结果创建版本
6. 保存版本信息

#### 4.2 版本号规则

- **主版本号**: 数据内容发生重大变化时递增
- **次版本号**: 数据格式或轻微内容变化时递增
- **重复标记**: 重复数据继承原版本号，通过version_type区分

### 5. 空间优化策略

#### 5.1 重复数据处理

**策略选择**:
1. **引用模式**: 重复数据不重复存储文件，只创建数据库记录
2. **软链接模式**: 创建文件系统软链接指向原始文件
3. **完整存储模式**: 完整存储但标记为重复（便于独立管理）

**当前实现**: 采用完整存储模式，便于后续独立管理和分析

#### 5.2 定期清理机制

```python
def cleanup_old_versions(dataset_id, keep_versions=5):
    """保留最新的N个版本，删除旧版本"""
    version_history = get_version_history(dataset_id)
    if len(version_history) > keep_versions:
        # 保留最新版本，删除旧版本
        old_versions = version_history[keep_versions:]
        for version in old_versions:
            delete_version(version.id)
```

## 📄 报告版本管理

### 1. 版本化存储结构

```
metadata/analysis_results/
├── versions/                    # 版本化存储
│   └── {dataset_id}/
│       ├── business/           # 业务分析版本
│       │   ├── 20250612_142010.json
│       │   ├── 20250612_143520.json
│       │   └── ...
│       └── quality/            # 质量分析版本
│           ├── 20250612_142030.json
│           └── ...
├── current/                     # 当前版本引用
│   ├── {dataset_id}_business.json
│   └── {dataset_id}_quality.json
├── business/                    # 兼容性保留
└── quality/

reports/
├── versions/                    # 报告文件版本
│   └── {dataset_id}/
│       ├── industrial/
│       │   ├── report_20250612_142010/
│       │   │   ├── 01_设备时间列识别.md
│       │   │   ├── 02_业务含义分析.md
│       │   │   └── metadata.json
│       │   └── ...
│       └── quality/
└── current/                     # 当前版本引用
```

### 2. 版本管理功能

#### 2.1 分析结果版本化

```python
class ReportVersionManager:
    def save_analysis_result_version(self, dataset_id, analysis_type, result_data, version=None):
        """保存分析结果版本"""
        # 生成版本号（时间戳格式）
        version = version or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存版本化数据
        versioned_data = {
            "dataset_id": dataset_id,
            "analysis_type": analysis_type,
            "version": version,
            "created_at": datetime.now().isoformat(),
            "data": result_data
        }
        
        # 保存到版本目录
        version_file = f"versions/{dataset_id}/{analysis_type}/{version}.json"
        save_json(version_file, versioned_data)
        
        # 更新当前版本引用
        update_current_version(dataset_id, analysis_type, version)
```

#### 2.2 报告文件版本化

```python
def save_report_version(self, dataset_id, report_type, report_files, version=None):
    """保存报告文件版本"""
    version = version or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 创建版本目录
    version_dir = f"versions/{dataset_id}/{report_type}/{version}/"
    
    # 保存报告文件
    for filename, content in report_files.items():
        save_file(f"{version_dir}/{filename}", content)
    
    # 保存版本元数据
    metadata = {
        "dataset_id": dataset_id,
        "report_type": report_type,
        "version": version,
        "created_at": datetime.now().isoformat(),
        "files": list(report_files.keys())
    }
    save_json(f"{version_dir}/metadata.json", metadata)
```

### 3. 版本清理策略

#### 3.1 自动清理规则

- **保留数量**: 默认保留最新5个版本
- **清理周期**: 可配置定期清理或手动触发
- **清理策略**: 按创建时间排序，删除最旧的版本

#### 3.2 清理实现

```python
def cleanup_old_versions(self, dataset_id, keep_versions=5):
    """清理旧版本"""
    # JSON版本清理
    for analysis_type in ['business', 'quality']:
        versions = get_analysis_result_versions(dataset_id, analysis_type)
        if len(versions) > keep_versions:
            old_versions = versions[keep_versions:]
            for version in old_versions:
                delete_version_file(version['file_path'])
    
    # 报告版本清理
    for report_type in ['industrial', 'quality']:
        versions = get_report_versions(dataset_id, report_type)
        if len(versions) > keep_versions:
            old_versions = versions[keep_versions:]
            for version in old_versions:
                delete_directory(version['directory'])
```

## 🔧 API接口设计

### 1. 数据集版本管理API

```http
# 获取版本历史
GET /api/v1/version-control/datasets/{dataset_id}/versions

# 获取重复数据集
GET /api/v1/version-control/datasets/{dataset_id}/duplicates

# 清理旧版本
DELETE /api/v1/version-control/datasets/{dataset_id}/versions/cleanup?keep_versions=5
```

### 2. 报告版本管理API

```http
# 获取分析结果版本列表
GET /api/v1/version-control/reports/{dataset_id}/{analysis_type}/versions

# 获取指定版本的分析结果
GET /api/v1/version-control/reports/{dataset_id}/{analysis_type}/versions/{version}

# 获取报告文件版本列表
GET /api/v1/version-control/reports/{dataset_id}/{report_type}/report-versions

# 清理报告版本
DELETE /api/v1/version-control/reports/{dataset_id}/versions/cleanup?keep_versions=5
```

### 3. 统计信息API

```http
# 获取版本控制统计信息
GET /api/v1/version-control/statistics
```

## 💡 使用场景

### 1. 数据上传场景

**场景**: 用户上传数据文件

**流程**:
1. 计算文件哈希和内容哈希
2. 检测是否存在重复数据
3. 根据检测结果确定版本类型
4. 创建相应的版本记录
5. 提供重复提示（如果存在）

**用户体验**:
- 重复数据自动检测并提示
- 版本关系清晰可见
- 存储空间优化

### 2. 分析结果管理

**场景**: AI分析生成新的结果

**流程**:
1. 保存分析结果到版本化存储
2. 自动生成版本号
3. 更新当前版本引用
4. 清理过期版本（可选）

**用户体验**:
- 分析结果有完整历史记录
- 可以回溯到任意版本
- 自动管理存储空间

### 3. 版本清理管理

**场景**: 定期系统维护

**流程**:
1. 识别有多个版本的数据集
2. 按保留策略清理旧版本
3. 更新统计信息
4. 生成清理报告

**系统优势**:
- 自动化维护
- 可配置的清理策略
- 完整的操作日志

## 📈 性能优化

### 1. 哈希计算优化

- **分块读取**: 避免大文件内存溢出
- **缓存机制**: 相同文件避免重复计算
- **异步计算**: 不阻塞用户界面

### 2. 存储优化

- **压缩存储**: JSON文件可启用压缩
- **延迟加载**: 版本列表按需加载详细信息
- **索引优化**: 数据库查询性能优化

### 3. 网络优化

- **增量传输**: 只传输变化的数据
- **缓存策略**: 合理设置HTTP缓存
- **分页加载**: 大量版本数据分页显示

## 🔮 未来扩展

### 1. 短期优化

- **差异比较**: 版本间的详细差异对比
- **分支管理**: 支持数据的分支和合并
- **批量操作**: 批量版本管理操作

### 2. 中期扩展

- **分布式存储**: 跨节点的版本管理
- **云端同步**: 与云存储的版本同步
- **协作功能**: 多用户协作的版本管理

### 3. 长期规划

- **AI增强**: 智能版本推荐和清理
- **区块链**: 版本历史的不可篡改记录
- **时间旅行**: 完整的数据时间线恢复

## 📋 配置选项

### 1. 版本控制配置

```python
# src/config/settings.py
class Settings:
    # 版本控制设置
    version_control_enabled: bool = True
    duplicate_detection_enabled: bool = True
    auto_cleanup_enabled: bool = True
    default_keep_versions: int = 5
    
    # 哈希计算设置
    hash_algorithm: str = "sha256"
    content_hash_precision: int = 6  # 数值精度
    
    # 清理策略设置
    cleanup_schedule: str = "weekly"  # daily, weekly, monthly
    cleanup_threshold: int = 10  # 版本数超过阈值时自动清理
```

### 2. 用户配置选项

```javascript
// 前端配置
const VERSION_CONFIG = {
    // 显示设置
    showVersionHistory: true,
    showDuplicateWarning: true,
    
    // 操作设置
    autoCleanupPrompt: true,
    confirmVersionDeletion: true,
    
    // 显示限制
    maxVersionsDisplay: 20,
    maxHistoryDepth: 50
};
```

## 🎉 总结

### 解决的核心问题

✅ **数据源版本管理**:
- 通过双重哈希机制准确识别重复数据
- 基于时间戳的版本标记系统
- 灵活的存储空间优化策略

✅ **数据报告版本管理**:
- JSON分析结果的完整版本化
- Markdown报告文件的版本管理
- 数据库记录的版本追踪

✅ **系统优势**:
- 自动化的版本管理流程
- 高效的存储空间利用
- 完整的API接口支持
- 灵活的配置和扩展能力

这个版本控制系统为数据集管理系统提供了完整的版本管理能力，既解决了用户提出的具体问题，又为系统的长期发展奠定了坚实基础。 