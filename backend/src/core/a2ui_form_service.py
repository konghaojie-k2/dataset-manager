#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2UI动态表单生成服务"""

from typing import Dict, List, Any, Optional
from loguru import logger
import json
import uuid

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

        form_id = str(uuid.uuid4())[:8]

        filterable_fields = self.metadata_discovery.get_filterable_fields()
        field_examples = self.metadata_discovery.get_field_examples()

        prompt = self._build_form_prompt(user_query, intent, filterable_fields, field_examples, session_context)

        try:
            response = await self.llm.ainvoke(prompt)
            response_content = response.content

            if hasattr(response, 'response_metadata') and response.response_metadata:
                try:
                    if isinstance(response.response_metadata, dict) and 'error' in response.response_metadata:
                        error_msg = response.response_metadata.get('error', 'Unknown error')
                        logger.error(f"LLM API错误: {error_msg}")
                        return self._get_default_form()
                except (KeyError, TypeError, AttributeError):
                    pass

            if isinstance(response_content, dict):
                if 'error' in response_content:
                    logger.error(f"LLM返回错误响应: {response_content.get('error', 'Unknown error')}")
                    return self._get_default_form()
                response_content = json.dumps(response_content)

            if not isinstance(response_content, str):
                logger.error(f"意外的响应类型: {type(response_content)}, content={response_content}")
                return self._get_default_form()

            logger.debug(f"LLM原始响应: {response_content[:500]}...")

            form_schema_dict = self._parse_json_response(response_content)
            form_schema = self._convert_to_a2ui_schema(form_schema_dict, form_id)
            form_schema = self._apply_smart_prefill(form_schema, session_context)

            logger.info(f"表单生成完成: form_id={form_id}, {len(form_schema.fields)}个字段")
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

        fields_str = ""
        for field_path, field_def in filterable_fields.items():
            fields_str += f"- **{field_path}** ({field_def['type']}): {field_def['description']}\n"

        context_str = ""
        if session_context and session_context.get("mentioned_entities"):
            mentioned = session_context["mentioned_entities"]
            context_str = f"## 会话上下文（用于预填）\n```json\n{json.dumps(mentioned, ensure_ascii=False, indent=2)}\n```\n"

        return f"""你是一位专业的用户界面设计师。用户查询不够明确，需要生成一个澄清表单。

## 用户查询
{user_query}

## 意图分析结果
- 置信度: {intent.get('confidence', 0)}
- 初步过滤: {json.dumps(intent.get('filters', {}))}
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
  "form_type": "search_refinement",
  "title": "请告诉我们您需要什么样的数据集",
  "description": "",
  "fields": [
    {{
      "name": "industry",
      "type": "select",
      "label": "您关注哪个行业？",
      "placeholder": "请选择行业",
      "options": [
        {{"value": "semiconductor", "label": "半导体"}},
        {{"value": "chemical", "label": "化工"}},
        {{"value": "energy", "label": "能源"}},
        {{"value": "manufacturing", "label": "制造业"}}
      ],
      "required": true,
      "default": null
    }}
  ],
  "actions": [
    {{"id": "submit", "type": "submit", "label": "搜索数据集", "primary": true}},
    {{"id": "cancel", "type": "cancel", "label": "取消", "primary": false}}
  ]
}}
```

## 字段类型选择指南

- **text**: 自由文本输入（如关键词搜索）
- **select**: 单选枚举值（如行业、状态）
- **multiselect**: 多选（如标签、数据类型多选）
- **range**: 数值范围（如质量分数80-100）
- **toggle**: 布尔值（如是/否）

## 常见场景示例

### 场景1: "质量好一点的数据集"
需要澄清：
- 行业（select）- 必填
- 质量分数范围（range）- 可选

### 场景2: "我要数据"
需要澄清：
- 行业（select）- 必填
- 数据类型（multiselect）- 可多选
- 处理状态（select）- 可选

现在请根据用户查询生成表单Schema。只输出JSON，不要有其他文字。
"""

    def _convert_to_a2ui_schema(self, schema_dict: Dict[str, Any], form_id: str = "default") -> A2UISchema:
        """将字典转换为A2UISchema对象"""
        try:
            fields = []
            for field_dict in schema_dict.get("fields", []):
                fields.append(A2UIField(**field_dict))

            actions = []
            for action_dict in schema_dict.get("actions", []):
                actions.append(A2UIAction(**action_dict))

            return A2UISchema(
                version="1.0",
                form_id=form_id,
                form_type=schema_dict.get("form_type", "search_refinement"),
                title=schema_dict.get("title", "请完善搜索条件"),
                description=schema_dict.get("description", ""),
                fields=fields,
                actions=actions
            )
        except Exception as e:
            logger.error(f"转换A2UI Schema失败: {e}")
            return self._get_default_form(form_id)

    def _apply_smart_prefill(
        self,
        form_schema: A2UISchema,
        session_context: Optional[Dict]
    ) -> A2UISchema:
        """应用智能预填"""
        if not session_context:
            return form_schema

        mentioned_entities = session_context.get("mentioned_entities", {})
        recent_searches = session_context.get("recent_searches", [])

        if not isinstance(mentioned_entities, dict):
            mentioned_entities = {}
        if not isinstance(recent_searches, list):
            recent_searches = []

        for field in form_schema.fields:
            if not isinstance(field.name, str):
                continue

            if field.name in mentioned_entities:
                value = mentioned_entities[field.name]
                if field.type == "select" and field.options:
                    option_values = [opt.get("value") for opt in field.options]
                    if value in option_values:
                        field.default = value
                elif field.type == "toggle":
                    field.default = bool(value)
                elif field.type == "multiselect":
                    if isinstance(value, list):
                        field.default = value
                elif not isinstance(value, dict):
                    field.default = value
                continue

            if recent_searches:
                for search in reversed(recent_searches):
                    if not isinstance(search, dict):
                        continue
                    if field.name in search:
                        value = search[field.name]
                        if field.type == "select" and field.options:
                            option_values = [opt.get("value") for opt in field.options]
                            if value in option_values:
                                field.default = value
                        elif not isinstance(value, dict):
                            field.default = value
                        break

        return form_schema

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析LLM的JSON响应"""
        import re

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            logger.warning(f"无法解析LLM响应为JSON: {response[:200]}...")
            return {}

    def _get_default_form(self, form_id: str = "default") -> A2UISchema:
        """返回默认表单（降级方案）"""
        return A2UISchema(
            version="1.0",
            form_id=form_id,
            form_type="search_refinement",
            title="请完善搜索条件",
            description="",
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
                    required=True
                ),
                A2UIField(
                    name="quality_min_score",
                    type="range",
                    label="最低质量分数",
                    placeholder="拖动选择",
                    required=False,
                    default=70
                )
            ],
            actions=[
                A2UIAction(id="submit", type="submit", label="搜索", primary=True),
                A2UIAction(id="cancel", type="cancel", label="取消", primary=False)
            ]
        )
