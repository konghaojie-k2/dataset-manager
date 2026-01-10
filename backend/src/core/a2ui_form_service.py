#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A2UI动态表单生成服务"""

from typing import Dict, List, Any, Optional
from loguru import logger
import json

from ..llms.llms import get_reasoning_llm
from .metadata_discovery import MetadataSchemaDiscovery
from ..schemas.chat import A2UISchema, A2UIField, A2UIAction


class A2UIFormService:
    """A2UI动态表单生成服务"""

    def __init__(self):
        self.llm = get_reasoning_llm()
        self.metadata_discovery = MetadataSchemaDiscovery()
        logger.info("A2UI表单生成服务初始化完成")

    async def generate_clarification_form(
        self,
        user_query: str,
        intent: Dict[str, Any],
        session_context: Optional[Dict[str, Any]] = None
    ) -> A2UISchema:
        """生成澄清表单

        Args:
            user_query: 用户原始查询
            intent: 意图分析结果
            session_context: 会话上下文（用于预填）

        Returns:
            A2UISchema: 表单Schema
        """
        logger.info(f"生成澄清表单: query='{user_query}'")

        # 获取可过滤字段和示例
        filterable_fields = self.metadata_discovery.get_filterable_fields()
        field_examples = self.metadata_discovery.get_field_examples()

        # 构建提示词
        prompt = self._build_form_prompt(user_query, intent, filterable_fields, field_examples, session_context)

        try:
            response = await self.llm.ainvoke(prompt)

            # 获取响应内容
            response_content = response.content

            # 处理LangChain响应对象的类型
            if hasattr(response, 'response_metadata') and response.response_metadata:
                # 检查是否有错误信息在response_metadata中（安全检查）
                try:
                    if isinstance(response.response_metadata, dict) and 'error' in response.response_metadata:
                        # 使用get方法安全访问，避免KeyError
                        error_msg = response.response_metadata.get('error', 'Unknown error')
                        logger.error(f"LLM API错误: {error_msg}")
                        return self._get_default_form()
                except (KeyError, TypeError, AttributeError):
                    # 如果访问出错，继续处理，不中断流程
                    pass

            # 如果content是dict类型（API错误响应）
            if isinstance(response_content, dict):
                if 'error' in response_content:
                    logger.error(f"LLM返回错误响应: {response_content.get('error', 'Unknown error')}")
                    return self._get_default_form()
                # 尝试将dict转为JSON字符串
                response_content = json.dumps(response_content)

            # 确保content是字符串
            if not isinstance(response_content, str):
                logger.error(f"意外的响应类型: {type(response_content)}, content={response_content}")
                return self._get_default_form()

            logger.debug(f"LLM原始响应: {response_content[:500]}...")

            form_schema_dict = self._parse_json_response(response_content)

            # 转换为A2UISchema对象
            form_schema = self._convert_to_a2ui_schema(form_schema_dict)

            # 智能预填
            form_schema = self._apply_smart_prefill(form_schema, session_context)

            logger.info(f"表单生成完成: {len(form_schema.fields)}个字段")
            return form_schema

        except KeyError as e:
            logger.error(f"KeyError during form generation: {e}", exc_info=True)
            return self._get_default_form()
        except Exception as e:
            logger.error(f"表单生成失败: {e}", exc_info=True)
            return self._get_default_form()

    def _build_form_prompt(
        self,
        user_query: str,
        intent: Dict,
        filterable_fields: Dict,
        field_examples: Dict,
        session_context: Optional[Dict]
    ) -> str:
        """构建表单生成提示词"""

        # 格式化可过滤字段
        fields_str = ""
        for field_path, field_def in filterable_fields.items():
            fields_str += f"- **{field_path}** ({field_def['type']}): {field_def['description']}\n"

        # 格式化上下文
        context_str = ""
        if session_context and session_context.get("mentioned_entities"):
            mentioned = session_context["mentioned_entities"]
            context_str = f"## 会话上下文（用于预填）\n```json\n{json.dumps(mentioned, ensure_ascii=False, indent=2)}\n```\n"

        return f"""你是一位专业的用户界面设计师。用户查询不够明确，需要生成一个澄清表单。

## 用户查询
{user_query}

## 意图分析结果
- 置信度: {intent.get('confidence', 0)}
- 初步过滤: {intent.get('filters', {})}
- 澄清原因: {intent.get('clarification_reason', '查询过于模糊')}

## 可用的过滤字段
{fields_str}
{context_str}

## 任务
生成一个A2UI表单Schema，帮助用户澄清需求。表单应该：
1. **简洁**: 只问3-5个最关键的问题
2. **智能**: 根据上下文预填已有信息
3. **友好**: 提供合理的默认选项
4. **合理**: 根据用户查询的实际需求选择字段

## 输出格式（JSON）

```json
{{
  "version": "1.0",
  "form_type": "search_refinement",
  "title": "表单标题",
  "description": "表单描述",
  "fields": [
    {{
      "name": "industry",
      "type": "select",
      "label": "行业领域",
      "placeholder": "请选择行业",
      "options": [
        {{"value": "semiconductor", "label": "半导体"}},
        {{"value": "chemical", "label": "化工"}},
        {{"value": "energy", "label": "能源"}}
      ],
      "required": true,
      "default": "semiconductor"
    }}
  ],
  "actions": [
    {{"id": "submit", "type": "submit", "label": "搜索", "primary": true}},
    {{"id": "cancel", "type": "cancel", "label": "取消", "primary": false}}
  ]
}}
```

## 字段类型选择指南

- **text**: 自由文本输入（如关键词）
- **select**: 单选枚举值（如行业、状态）
- **multiselect**: 多选（如标签）
- **range**: 数值范围（如质量分数80-100）
- **toggle**: 布尔值（如是/否）

## 常见场景示例

### 场景1: "质量好一点的数据集"
需要澄清：
- 行业（select）
- 质量分数范围（range）
- 数据规模（range）

### 场景2: "我要数据质量高的"
需要澄清：
- 行业（select）
- 质量等级（select: excellent/good/fair/poor）

现在请根据用户查询生成表单Schema。
"""

    def _convert_to_a2ui_schema(self, schema_dict: Dict[str, Any]) -> A2UISchema:
        """将字典转换为A2UISchema对象"""
        try:
            # 转换字段
            fields = []
            for field_dict in schema_dict.get("fields", []):
                fields.append(A2UIField(**field_dict))

            # 转换操作
            actions = []
            for action_dict in schema_dict.get("actions", []):
                actions.append(A2UIAction(**action_dict))

            # 构建完整schema
            return A2UISchema(
                version=schema_dict.get("version", "1.0"),
                form_type=schema_dict.get("form_type", "search_refinement"),
                title=schema_dict.get("title", "请完善搜索条件"),
                description=schema_dict.get("description", ""),
                fields=fields,
                actions=actions
            )
        except Exception as e:
            logger.error(f"转换A2UI Schema失败: {e}")
            return self._get_default_form()

    def _apply_smart_prefill(
        self,
        form_schema: A2UISchema,
        session_context: Optional[Dict]
    ) -> A2UISchema:
        """应用智能预填

        策略：
        1. 从会话上下文中提取已知实体
        2. 从最近的搜索历史中推断偏好
        3. 自动填充到表单字段
        """
        if not session_context:
            return form_schema

        mentioned_entities = session_context.get("mentioned_entities", {})
        recent_searches = session_context.get("recent_searches", [])

        # 为每个字段尝试预填
        for field in form_schema.fields:
            # 检查是否在已提实体中
            if field.name in mentioned_entities:
                # 对于select类型，需要检查值是否在options中
                if field.type == "select" and field.options:
                    option_values = [opt.get("value") for opt in field.options]
                    if mentioned_entities[field.name] in option_values:
                        field.default = mentioned_entities[field.name]
                elif field.type == "toggle":
                    # 布尔值
                    field.default = bool(mentioned_entities[field.name])
                else:
                    field.default = mentioned_entities[field.name]
                continue

            # 从最近搜索中推断
            if recent_searches:
                for search in reversed(recent_searches):  # 最优先
                    if field.name in search:
                        if field.type == "select" and field.options:
                            option_values = [opt.get("value") for opt in field.options]
                            if search[field.name] in option_values:
                                field.default = search[field.name]
                        else:
                            field.default = search[field.name]
                        break

        return form_schema

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析LLM的JSON响应"""
        import re

        try:
            # 尝试直接解析JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON块（支持```json...```格式）
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # 尝试查找纯JSON（查找最外层{}）
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            # 解析失败
            logger.warning(f"无法解析LLM响应为JSON: {response[:200]}...")
            return {}

    def _get_default_form(self) -> A2UISchema:
        """返回默认表单（降级方案）"""
        return A2UISchema(
            version="1.0",
            form_type="search_refinement",
            title="请完善搜索条件",
            description="请提供更多细节以帮助我找到合适的数据集",
            fields=[
                A2UIField(
                    name="industry",
                    type="select",
                    label="行业领域",
                    placeholder="请选择行业",
                    options=[
                        {"value": "semiconductor", "label": "半导体"},
                        {"value": "chemical", "label": "化工"},
                        {"value": "energy", "label": "能源"},
                        {"value": "manufacturing", "label": "制造"}
                    ],
                    required=False
                ),
                A2UIField(
                    name="quality_analysis_results.overall_score",
                    type="select",
                    label="质量要求",
                    placeholder="请选择质量要求",
                    options=[
                        {"value": "90", "label": "高质量 (90+)"},
                        {"value": "80", "label": "良好 (80+)"},
                        {"value": "70", "label": "一般 (70+)"}
                    ],
                    required=False
                )
            ],
            actions=[
                A2UIAction(id="submit", type="submit", label="搜索", primary=True),
                A2UIAction(id="cancel", type="cancel", label="取消", primary=False)
            ]
        )
