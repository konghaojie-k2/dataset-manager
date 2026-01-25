#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LLM意图分析服务（增强版）"""

from typing import Dict, List, Any, Optional
from loguru import logger
import json
import re

from ..llms.llms import get_reasoning_llm
from .metadata_discovery import MetadataSchemaDiscovery


# ===== 意图分析提示词模板 =====

INTENT_ANALYSIS_TEMPLATE = """请分析用户查询的意图，提取关键信息：

用户查询：{query}

请识别：
1. **主要意图**：搜索、预览、获取详情、其他
2. **关键词**：搜索的主要关键词
3. **过滤条件**：
   - 标签过滤
   - 行业过滤
   - 时间范围
4. **实体**：提到的具体数据集名称、ID等

返回结构化的意图分析结果。
"""


SEARCH_DATASETS_TEMPLATE = """根据用户的查询意图搜索数据集：

查询：{query}
意图分析：{intent_analysis}

请执行搜索并返回最相关的数据集。
"""


class IntentAnalysisService:
    """LLM意图分析服务（增强版）"""

    def __init__(self):
        """初始化意图分析服务"""
        self.llm = get_reasoning_llm()
        self.metadata_discovery = MetadataSchemaDiscovery()
        logger.info("LLM意图分析服务初始化完成（增强版）")

    async def analyze_intent(self, user_message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """分析用户查询意图，提取过滤条件

        Args:
            user_message: 用户查询
            context: 会话上下文（可选）

        Returns:
            Dict[str, Any]: 意图分析结果，包含filters和sort_preference
        """
        logger.info(f"开始分析用户意图: {user_message}")

        # 获取可过滤字段（动态）
        filterable_fields = self.metadata_discovery.format_schema_for_llm()

        prompt = self._build_intent_prompt(user_message, filterable_fields, context)

        try:
            try:
                response = await self.llm.ainvoke(prompt)
            except Exception as invoke_error:
                # 记录错误并返回默认意图，而不是重新抛出异常
                logger.error(f"LLM调用失败: {invoke_error}")
                return self._get_default_intent()

            # 获取响应内容
            # response.content 可能是字符串或dict（API错误时）
            response_content = response.content

            # 处理LangChain响应对象的类型
            if hasattr(response, 'response_metadata') and response.response_metadata:
                # 检查是否有错误信息在response_metadata中（安全检查）
                try:
                    if isinstance(response.response_metadata, dict) and 'error' in response.response_metadata:
                        # 使用get方法安全访问，避免KeyError
                        error_msg = response.response_metadata.get('error', 'Unknown error')
                        logger.error(f"LLM API错误: {error_msg}")
                        return self._get_default_intent()
                except (KeyError, TypeError, AttributeError):
                    # 如果访问出错，继续处理，不中断流程
                    pass

            # 如果content是dict类型（API错误响应）
            if isinstance(response_content, dict):
                if 'error' in response_content:
                    logger.error(f"LLM返回错误响应: {response_content.get('error', 'Unknown error')}")
                    return self._get_default_intent()
                # 尝试将dict转为JSON字符串
                import json
                response_content = json.dumps(response_content)

            # 确保content是字符串
            if not isinstance(response_content, str):
                logger.error(f"意外的响应类型: {type(response_content)}, content={response_content}")
                return self._get_default_intent()

            logger.debug(f"LLM原始响应: {response_content[:500]}...")

            intent_data = self._parse_json_response(response_content)

            # 清理None值
            if "filters" in intent_data:
                intent_data["filters"] = {
                    k: v for k, v in intent_data["filters"].items()
                    if v is not None and v != "" and v != []
                }

            logger.info(f"意图分析完成: filters={intent_data.get('filters')}, sort={intent_data.get('sort_preference')}")
            return intent_data

        except KeyError as e:
            logger.error(f"KeyError during intent analysis: {e}", exc_info=True)
            return self._get_default_intent()
        except Exception as e:
            logger.error(f"意图分析失败: {e}", exc_info=True)
            return self._get_default_intent()

    def _build_intent_prompt(self, user_message: str, filterable_fields: str, context: Optional[Dict] = None) -> str:
        """构建增强的意图分析提示词

        Args:
            user_message: 用户消息
            filterable_fields: 可过滤字段（格式化的字符串）
            context: 会话上下文

        Returns:
            str: 完整的提示词
        """
        # 构建上下文字符串（使用 .format() 避免 f-string 中的 $ 符号问题）
        context_str = ""
        if context and context.get("mentioned_entities"):
            mentioned = context["mentioned_entities"]
            context_str = "\n## 会话上下文\n已知信息: {}".format(json.dumps(mentioned, ensure_ascii=False, indent=2))

        # 使用 .format() 而不是 f-string，避免 $ 符号被解释为格式化说明符
        return """你是一位专业的工业数据集搜索专家。请分析用户的查询，生成精确的过滤条件。

## 用户查询
{}

{}

## 可用的过滤字段（动态）
{}

## 输出格式（JSON）

严格按照以下格式输出：

```json
{{
  "filters": {{
    "字段路径": "值或比较表达式",
    ...
  }},
  "sort_preference": "质量优先 | 相关性优先 | 最新优先",
  "clarification_needed": false,
  "clarification_reason": null,
  "clarification_message": null,
  "confidence": 0.85
}}
```

## 过滤语法示例

1. **精确匹配**: {{"industry": "semiconductor"}}
2. **数值范围**: {{"file_size": {{"$gte": 1000, "$lte": 1000000}}}}
3. **包含匹配**: {{"tags": {{"$in": ["传感器", "sensor"]}}}}
4. **嵌套字段**: {{"quality_analysis_results.overall_score": {{"$gte": 80}}}}
5. **布尔值**: {{"is_derived_data": false}}
6. **重复数据**: {{"version_type": "duplicate"}} 或 {{"source_dataset_ids": {{"$exists": true}}}}

## 可用操作符

- `$gte`: 大于等于
- `$lte`: 小于等于
- `$gt`: 大于
- `$lt`: 小于
- `$in`: 包含于列表
- `$nin`: 不包含于列表
- `$exists`: 字段存在
- `$ne`: 不等于
- `$eq`: 等于

## 分析要点

1. **理解语义**:
   - "质量好的数据集" → quality_analysis_results.overall_score >= 80
   - "有重复数据的数据集" → version_type = "duplicate"
   - "派生数据" → is_derived_data = true
   - "大规模数据" → file_size >= 某个阈值

2. **行业关键词特殊处理**（重要）:
   - 当用户提到行业关键词（如"半导体"、"化工"、"能源"等）时，**必须同时生成两个过滤条件**:
     - `industry` 字段检查
     - `tags` 字段的 `$in` 检查
   - 例如："半导体行业的数据集" → 应该生成 industry 和 tags 两个过滤条件
   - 因为数据集可能只在 tags 中标记了行业，而不一定填写了 industry 字段

3. **嵌套字段**: 支持访问嵌套结构（如quality_analysis_results.overall_score）

4. **隐式需求**: 不要过度解读，但推断合理的隐含条件

5. **澄清判断**: 当查询过于模糊（如"质量好一点"）且缺少关键信息时，设置clarification_needed=true

## 示例

查询："我要半导体行业质量比较好的传感器数据"
输出：
{{
  "filters": {{
    "industry": "semiconductor",
    "tags": {{"$in": ["半导体", "semiconductor", "传感器", "sensor"]}},
    "quality_analysis_results.overall_score": {{"$gte": 80}}
  }},
  "sort_preference": "质量优先",
  "clarification_needed": false,
  "confidence": 0.9
}}

查询："半导体行业的数据集"
输出：
{{
  "filters": {{
    "industry": "semiconductor",
    "tags": {{"$in": ["半导体", "semiconductor"]}}
  }},
  "sort_preference": "相关性优先",
  "clarification_needed": false,
  "confidence": 0.95
}}

查询："有重复数据的数据集"
输出：
{{
  "filters": {{
    "version_type": "duplicate"
  }},
  "sort_preference": "相关性优先",
  "clarification_needed": false,
  "confidence": 0.95
}}

现在请分析并输出JSON。""".format(user_message, context_str, filterable_fields)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析LLM的JSON响应

        Args:
            response: LLM返回的文本

        Returns:
            Dict: 解析后的意图数据
        """
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

            # 解析失败，返回默认值
            logger.warning(f"无法解析LLM响应为JSON: {response[:200]}...")
            return self._get_default_intent()

    def _get_default_intent(self) -> Dict[str, Any]:
        """返回默认意图（降级方案）

        当LLM分析失败时使用

        Returns:
            Dict: 默认的意图数据
        """
        return {
            "filters": {},
            "sort_preference": "相关性优先",
            "clarification_needed": False,
            "clarification_reason": None,
            "clarification_message": None,
            "confidence": 0.0
        }

    # ===== 提示词辅助方法 =====

    @staticmethod
    def get_intent_analysis_prompt(query: str) -> str:
        """获取意图分析提示词（简化版）

        Args:
            query: 用户查询

        Returns:
            str: 格式化的提示词
        """
        return INTENT_ANALYSIS_TEMPLATE.format(query=query)

    @staticmethod
    def get_search_datasets_prompt(query: str, intent_analysis: str = "") -> str:
        """获取搜索数据集提示词

        Args:
            query: 用户查询
            intent_analysis: 意图分析结果（可选）

        Returns:
            str: 格式化的提示词
        """
        return SEARCH_DATASETS_TEMPLATE.format(
            query=query,
            intent_analysis=intent_analysis or "未提供"
        )
