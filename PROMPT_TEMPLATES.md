# 提示词模板使用指南

本文档介绍如何使用和管理工业数据分析系统中的提示词模板。

## 概述

为了方便后续的修改和优化，我们将所有的提示词从代码中提取到外部的 Markdown 文件中。这样可以：

- ✅ 无需修改代码即可优化提示词
- ✅ 支持版本控制和协作编辑
- ✅ 提供结构化的模板管理
- ✅ 便于A/B测试和效果对比

## 提示词模板文件位置

所有提示词模板文件位于 `src/prompts/templates/` 目录下：

### 工业数据分析专用模板

1. **设备列和时间列识别** - `device_time_identification.md`
   - 用于识别工业数据中的设备相关列和时间列
   - 变量：`dataset_name`, `total_columns`, `columns_info`

2. **业务含义分析** - `business_meaning_analysis.md`
   - 用于分析各列在工业业务中的具体含义和价值
   - 变量：`dataset_name`, `user_requirements`, `columns_business_info`

3. **控制原理分析** - `control_relationships_analysis.md`
   - 用于分析列之间的控制原理和因果关系
   - 变量：`dataset_name`, `user_requirements`, `device_time_identification`, `business_meaning_analysis`, `correlation_analysis`, `columns_info`

4. **建议生成** - `recommendations.md`
   - 用于生成数据分析建议和行动计划
   - 变量：`analysis_context`

### 通用分析模板

- `statistical_analysis.md` - 统计分析提示词
- `business_insight.md` - 商业洞察提示词
- `visualization_analysis.md` - 可视化建议提示词
- `modeling_analysis.md` - 建模建议提示词

## 模板文件结构

每个模板文件都采用标准的 YAML Front Matter + Markdown 格式：

```markdown
---
name: "模板名称"
type: "模板类型"
category: "分类"
version: "版本号"
description: "模板描述"
variables:
  - 变量1
  - 变量2
tags:
  - "标签1"
  - "标签2"
author: "作者"
created_date: "创建日期"
---

# 提示词标题

## 系统角色
定义AI的角色和专业背景

## 分析任务
描述具体的分析任务

### 数据信息
{变量名} - 动态内容占位符

## 分析要求
详细的分析要求和输出格式

## 输出要求
对输出质量和格式的要求
```

## 如何修改提示词

### 1. 直接编辑模板文件

```bash
# 编辑设备识别提示词
vim src/prompts/templates/device_time_identification.md

# 编辑业务含义分析提示词
vim src/prompts/templates/business_meaning_analysis.md
```

### 2. 修改后自动生效

提示词模板支持热重载，修改后无需重启服务即可生效。

### 3. 版本管理

建议在修改提示词时：
- 更新模板文件头部的版本号
- 在 Git 中提交变更记录
- 记录修改原因和预期效果

## 代码中的使用方式

### 在节点中使用提示词模板

```python
from ..prompts.analysis_prompts import AnalysisPrompts

class AnalysisNodes:
    def __init__(self):
        self.analysis_prompts = AnalysisPrompts()
    
    async def identify_device_time_columns_node(self, state):
        # 使用外部模板
        prompt = self.analysis_prompts.get_device_time_identification_prompt(
            dataset_name=state.get('dataset_name'),
            total_columns=len(columns_info),
            columns_info=columns_info_str
        )
        
        messages = [
            SystemMessage(content="系统角色描述"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.reasoning_llm.ainvoke(messages)
        return response.content
```

### 可用的提示词方法

```python
# 工业数据分析专用
prompts.get_device_time_identification_prompt(dataset_name, total_columns, columns_info)
prompts.get_business_meaning_analysis_prompt(dataset_name, user_requirements, columns_business_info)
prompts.get_control_relationships_analysis_prompt(dataset_name, user_requirements, device_time_identification, business_meaning_analysis, correlation_analysis, columns_info)
prompts.get_recommendations_prompt(analysis_context)

# 通用分析
prompts.get_statistical_analysis_prompt(data_info)
prompts.get_business_insight_prompt(analysis_results)
prompts.get_visualization_prompt(data_summary)
prompts.get_modeling_prompt(analysis_goal, data_features)
```

## 备用机制

如果模板文件加载失败，系统会自动使用内置的备用提示词，确保功能正常运行。

## 最佳实践

### 1. 提示词优化原则

- **明确性**：指令清晰明确，避免歧义
- **结构化**：使用标准格式，便于AI理解
- **专业性**：结合领域知识，提供专业指导
- **可扩展**：预留扩展空间，支持新需求

### 2. 测试和验证

- 修改后进行充分测试
- 对比修改前后的效果
- 收集用户反馈
- 持续迭代优化

### 3. 文档维护

- 及时更新版本信息
- 记录重要变更
- 维护变量说明
- 保持格式一致

## 故障排除

### 常见问题

1. **模板加载失败**
   - 检查文件路径是否正确
   - 验证YAML格式是否有效
   - 查看日志错误信息

2. **变量替换错误**
   - 确认变量名拼写正确
   - 检查变量是否在模板中定义
   - 验证传入的参数类型

3. **提示词效果不佳**
   - 分析AI输出质量
   - 调整提示词结构
   - 增加示例和约束

### 调试方法

```python
# 查看可用模板
prompts.list_available_templates()

# 重新加载模板
prompts.reload_templates()

# 查看生成的提示词
prompt = prompts.get_device_time_identification_prompt(...)
print(prompt)
```

## 贡献指南

欢迎贡献新的提示词模板或改进现有模板：

1. Fork 项目
2. 创建新的模板文件或修改现有文件
3. 遵循模板格式规范
4. 添加必要的测试
5. 提交 Pull Request

---

通过外部化提示词模板，我们实现了更灵活、可维护的工业数据分析系统。如有问题或建议，请及时反馈。 