#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""聊天服务 - 数据集搜索和对话编排（增强版）"""

from typing import Dict, List, Optional, Any
from loguru import logger
import uuid
from datetime import datetime

from ..schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSession,
    MessageRole,
    ResponseType,
    SearchIntent
)
from ..schemas.dataset import DatasetMetadata
from .dataset_service import DatasetService
from .intent_analysis import IntentAnalysisService
from .smart_search import SmartSearchService
from .a2ui_form_service import A2UIFormService
from .form_context_manager import FormContextManager


class ChatService:
    """聊天服务 - 协调LLM、搜索、A2UI生成（增强版）"""

    def __init__(self, dataset_service: DatasetService):
        """初始化聊天服务

        Args:
            dataset_service: 数据集服务实例
        """
        self.dataset_service = dataset_service
        self.sessions: Dict[str, ChatSession] = {}

        # 初始化LLM意图分析服务
        self.intent_service = IntentAnalysisService()

        # 初始化智能搜索服务
        self.smart_search = SmartSearchService(dataset_service.repository)

        # 初始化A2UI表单生成服务
        self.a2ui_form_service = A2UIFormService()

        # 初始化表单上下文管理器
        self.context_manager = FormContextManager()

        logger.info("聊天服务初始化完成（增强版：动态过滤+A2UI表单）")

    def _get_or_create_session(self, session_id: str) -> ChatSession:
        """获取或创建会话

        Args:
            session_id: 会话ID

        Returns:
            ChatSession: 会话对象
        """
        if session_id == "new" or not session_id:
            session_id = str(uuid.uuid4())

        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id=session_id)
            logger.info(f"创建新会话: {session_id}")

        return self.sessions[session_id]

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """处理用户消息（增强版）

        Args:
            request: 聊天请求

        Returns:
            ChatResponse: 聊天响应
        """
        try:
            # 1. 获取或创建会话
            session = self._get_or_create_session(request.session_id)

            # 2. 添加用户消息到历史
            session.add_message(MessageRole.USER, request.content)

            # 3. 使用LLM分析意图（带上下文）
            intent = await self.intent_service.analyze_intent(
                request.content,
                context=session.current_context
            )

            # 4. 提取实体并更新上下文
            entities = self.context_manager.extract_entities_from_message(
                request.content,
                intent
            )
            self.context_manager.update_session_context(session, entities)

            # 5. 判断是否需要澄清
            if intent.get("clarification_needed"):
                logger.info(f"需要澄清: {intent.get('clarification_reason')}")

                # 生成A2UI表单
                form_schema = await self.a2ui_form_service.generate_clarification_form(
                    user_query=request.content,
                    intent=intent,
                    session_context=session.current_context
                )

                return ChatResponse(
                    type=ResponseType.CLARIFICATION_NEEDED,
                    message=intent.get("clarification_message", "请提供更多细节"),
                    a2ui_form=form_schema.model_dump(),
                    session_id=session.session_id
                )

            # 6. 执行搜索（使用动态过滤 + 混合模式）
            datasets = await self.smart_search.search_datasets(
                filters=intent.get("filters", {}),
                sort_preference=intent.get("sort_preference", "相关性优先"),
                limit=10
            )

            # 混合模式：如果结构化过滤没有结果，使用 LLM 语义搜索
            if len(datasets) == 0:
                logger.info("结构化过滤无结果，启用 LLM 语义搜索")
                datasets = await self._semantic_search(
                    user_query=request.content,
                    filters=intent.get("filters", {}),
                    limit=10
                )

            # 7. 添加搜索结果到历史
            session.add_search_result(request.content, datasets)

            # 8. 添加助手回复到历史
            response_message = self._build_response_message(intent, datasets)

            session.add_message(MessageRole.ASSISTANT, response_message)

            # 9. 构建响应
            return ChatResponse(
                type=ResponseType.SEARCH_RESULTS,
                message=response_message,
                datasets=datasets,
                session_id=session.session_id,
                total_results=len(datasets),
                search_query=request.content
            )

        except KeyError as e:
            logger.error(f"KeyError in process_message: {e}", exc_info=True)
            # 返回一个友好的错误响应
            return ChatResponse(
                type=ResponseType.ERROR,
                message=f"处理消息时出错，请重试。错误详情: {str(e)}",
                session_id=request.session_id if request.session_id != 'new' else 'unknown',
                datasets=[]
            )
        except Exception as e:
            logger.error(f"Error in process_message: {e}", exc_info=True)
            return ChatResponse(
                type=ResponseType.ERROR,
                message=f"处理消息时出错，请重试。错误详情: {str(e)}",
                session_id=request.session_id if request.session_id != 'new' else 'unknown',
                datasets=[]
            )

    def _build_response_message(
        self,
        intent: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> str:
        """构建响应消息

        Args:
            intent: 意图分析结果
            results: 搜索结果

        Returns:
            str: 响应消息
        """
        if not results:
            return "未找到匹配的数据集。尝试使用不同的关键词或提供更多细节。"

        message = f"找到 {len(results)} 个匹配的数据集\n\n"

        # 添加排序说明
        sort_pref = intent.get("sort_preference", "相关性优先")
        if sort_pref == "质量优先":
            message += "已按质量评分排序。\n\n"
        elif sort_pref == "最新优先":
            message += "已按上传时间排序。\n\n"

        # 添加简要说明
        message += "点击任意数据集查看详细信息。"

        return message

    async def _analyze_intent_simple(self, user_message: str, session: ChatSession) -> SearchIntent:
        """简单的意图分析（Phase 1实现）

        Args:
            user_message: 用户消息
            session: 会话对象

        Returns:
            SearchIntent: 搜索意图
        """
        logger.info(f"分析用户意图: {user_message}")

        # 提取关键词
        keywords = self._extract_keywords(user_message)

        # 检查是否需要澄清
        if len(keywords) < 2:
            return SearchIntent(
                search_query=user_message,
                needs_clarification=True,
                clarification_reason="您的查询过于宽泛，建议提供更多具体信息",
                confidence=0.3
            )

        # 构建搜索查询
        search_query = " ".join(keywords)

        # 提取过滤条件
        filters = self._extract_filters(user_message)

        return SearchIntent(
            search_query=search_query,
            entities={"keywords": keywords},
            filters=filters,
            needs_clarification=False,
            confidence=0.7
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词

        Args:
            text: 输入文本

        Returns:
            List[str]: 关键词列表
        """
        # 常见停用词
        stopwords = {"的", "了", "是", "我", "你", "他", "她", "它", "们", "在", "有", "和", "或",
                    "想要", "需要", "找", "搜索", "查询", "显示", "给我", "看一下", "看看"}

        # 简单分词（按空格和常见标点）
        import re
        words = re.findall(r'[\w]+', text)

        # 过滤停用词和短词
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]

        return keywords[:5]  # 最多返回5个关键词

    def _extract_filters(self, text: str) -> Dict[str, Any]:
        """提取过滤条件

        Args:
            text: 输入文本

        Returns:
            Dict: 过滤条件
        """
        filters = {}

        # 行业关键词映射
        industry_keywords = {
            "半导体": "semiconductor",
            "化工": "chemical",
            "能源": "energy",
            "汽车": "automotive",
            "食品": "food",
            "医药": "pharmaceutical"
        }

        # 数据类型关键词映射
        data_type_keywords = {
            "传感器": "sensor",
            "生产": "production",
            "质量": "quality",
            "设备": "equipment",
            "温度": "temperature",
            "压力": "pressure"
        }

        # 检测行业
        for cn, en in industry_keywords.items():
            if cn in text:
                filters["industry"] = en
                break

        # 检测数据类型
        detected_tags = []
        for cn, en in data_type_keywords.items():
            if cn in text:
                detected_tags.append(cn)

        if detected_tags:
            filters["tags"] = detected_tags

        return filters

    async def _search_datasets_simple(
        self,
        query: str,
        filters: Dict[str, Any],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """简单的数据集搜索（Phase 1实现）

        Args:
            query: 搜索查询
            filters: 过滤条件
            top_k: 返回结果数量

        Returns:
            List[Dict]: 匹配的数据集列表
        """
        logger.info(f"搜索数据集: query={query}, filters={filters}")

        # 获取所有数据集
        all_datasets = self.dataset_service.repository.list_all()

        # 计算相关性评分
        scored_datasets = []
        for dataset in all_datasets:
            score = self._calculate_relevance_score(dataset, query, filters)
            if score > 0:
                scored_datasets.append((dataset, score))

        # 按评分排序
        scored_datasets.sort(key=lambda x: x[1], reverse=True)

        # 返回top_k结果
        results = []
        for dataset, score in scored_datasets[:top_k]:
            results.append({
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "tags": dataset.tags,
                "industry": dataset.industry,
                "file_size": dataset.file_size,
                "upload_time": dataset.upload_time.isoformat(),
                "processing_status": dataset.processing_status,
                "relevance_score": score
            })

        logger.info(f"搜索完成: 找到 {len(results)} 个结果")
        return results

    async def _semantic_search(
        self,
        user_query: str,
        filters: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """LLM语义搜索 - 当结构化过滤无结果时使用

        1. 获取所有数据集元数据
        2. 构建LLM prompt，包含所有数据集信息
        3. LLM进行语义匹配并排序
        4. 返回最相关的数据集

        Args:
            user_query: 用户查询
            filters: 之前的过滤条件（用于上下文）
            limit: 返回结果数量

        Returns:
            List[Dict]: 匹配的数据集列表
        """
        logger.info(f"开始LLM语义搜索: query='{user_query}', filters={filters}")

        # 1. 获取所有数据集
        all_datasets = self.dataset_service.repository.list_all()

        if not all_datasets:
            logger.warning("没有可用的数据集进行语义搜索")
            return []

        # 2. 格式化数据集信息为LLM可读的格式
        datasets_info = []
        for dataset in all_datasets:
            info = {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "tags": dataset.tags,
                "industry": dataset.industry,
                "processing_status": dataset.processing_status
            }

            # 添加行数和列数信息
            if dataset.quality_metrics:
                info["row_count"] = dataset.quality_metrics.total_rows
                info["column_count"] = dataset.quality_metrics.total_columns
            else:
                info["column_count"] = len(dataset.columns) if dataset.columns else 0

            # 添加质量分析结果（如果有）
            if dataset.quality_analysis_results:
                info["quality_score"] = dataset.quality_analysis_results.get("overall_score")

            # 添加业务分析结果（如果有）
            if dataset.industrial_domain:
                info["industrial_domain"] = dataset.industrial_domain

            # 添加列信息（前5列作为示例）
            if dataset.columns and len(dataset.columns) > 0:
                info["sample_columns"] = [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "business_meaning": col.business_meaning
                    }
                    for col in dataset.columns[:5]
                ]

            datasets_info.append(info)

        # 3. 构建LLM提示词
        prompt = self._build_semantic_search_prompt(user_query, datasets_info, filters, limit)

        try:
            # 4. 调用LLM进行语义匹配
            response = await self.intent_service.llm.ainvoke(prompt)
            response_content = response.content

            # 确保是字符串
            if isinstance(response_content, dict):
                import json
                response_content = json.dumps(response_content)

            if not isinstance(response_content, str):
                logger.error(f"意外的响应类型: {type(response_content)}")
                return []

            logger.debug(f"LLM语义搜索响应: {response_content[:500]}...")

            # 5. 解析LLM响应
            matched_ids = self._parse_semantic_search_response(response_content)

            # 6. 根据ID获取完整数据集信息
            results = []
            id_to_dataset = {ds.id: ds for ds in all_datasets}

            for dataset_id in matched_ids[:limit]:
                if dataset_id in id_to_dataset:
                    dataset = id_to_dataset[dataset_id]
                    results.append({
                        "id": dataset.id,
                        "name": dataset.name,
                        "description": dataset.description,
                        "tags": dataset.tags,
                        "industry": dataset.industry,
                        "file_size": dataset.file_size,
                        "upload_time": dataset.upload_time.isoformat(),
                        "processing_status": dataset.processing_status,
                        "relevance_score": 1.0  # LLM已经排序，默认高分
                    })

            logger.info(f"LLM语义搜索完成: 找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"LLM语义搜索失败: {e}", exc_info=True)
            return []

    def _build_semantic_search_prompt(
        self,
        user_query: str,
        datasets_info: List[Dict],
        filters: Dict[str, Any],
        limit: int
    ) -> str:
        """构建语义搜索提示词

        Args:
            user_query: 用户查询
            datasets_info: 数据集信息列表
            filters: 之前的过滤条件
            limit: 返回数量限制

        Returns:
            str: 完整的LLM提示词
        """
        import json

        # 格式化数据集列表
        datasets_text = ""
        for i, info in enumerate(datasets_info, 1):
            datasets_text += f"\n{i}. **{info['name']}** (ID: {info['id']})\n"
            datasets_text += f"   - 描述: {info['description']}\n"
            datasets_text += f"   - 标签: {', '.join(info['tags']) if info['tags'] else '无'}\n"
            if info.get('industry'):
                datasets_text += f"   - 行业: {info['industry']}\n"
            if info.get('sample_columns'):
                cols = [c['name'] for c in info['sample_columns']]
                datasets_text += f"   - 数据列示例: {', '.join(cols)}\n"

        # 格式化之前的过滤条件
        filters_text = ""
        if filters:
            filters_text = f"\n之前的结构化过滤条件: {json.dumps(filters, ensure_ascii=False)}"

        return """你是一位专业的工业数据集语义搜索专家。用户查询没有通过结构化过滤找到结果，现在需要你进行语义理解，找出最相关的数据集。

## 用户查询
{}

## 可用数据集列表
{}

## 任务
1. **语义理解**: 深入理解用户查询的真实意图，不要局限于字面匹配
   - 例如：用户问"温度测点"可能是在找包含"温度"、"sensor"、"测点"等关键词的数据集
   - 例如：用户问"半导体数据"应该匹配标签中有"半导体"或"semiconductor"的数据集

2. **多维度匹配**: 从以下维度判断相关性
   - 数据集名称和描述
   - 标签（tags）和行业（industry）
   - 数据列名称（sample_columns）
   - 业务领域（industrial_domain）

3. **排序推荐**: 按相关性从高到低排序，返回前{}个最相关的数据集ID

## 输出格式（JSON）

严格按照以下格式输出：

```json
{{
  "reasoning": "你的推理过程，解释为什么选择这些数据集",
  "matched_dataset_ids": ["dataset_id_1", "dataset_id_2", "..."]
}}
```

## 示例

用户查询: "带有温度测点的数据集"
数据集:
1. 生产设备数据 (列: 设备ID, 温度, 压力, 速度)
2. 传感器数据 (列: sensor_id, temperature, humidity)
3. 销售数据 (列: 产品, 价格, 数量)

输出:
```json
{{
  "reasoning": "用户查找温度测点数据。数据集1包含'温度'列，数据集2包含'temperature'列，都与温度测量相关。数据集3是销售数据，不相关。",
  "matched_dataset_ids": ["dataset_1_id", "dataset_2_id"]
}}
```

现在请分析并输出JSON。""".format(user_query, datasets_text, limit, filters_text)

    def _parse_semantic_search_response(self, response: str) -> List[str]:
        """解析LLM语义搜索响应

        Args:
            response: LLM返回的文本

        Returns:
            List[str]: 匹配的数据集ID列表
        """
        import json
        import re

        try:
            # 尝试直接解析JSON
            data = json.loads(response)
            return data.get("matched_dataset_ids", [])

        except json.JSONDecodeError:
            # 尝试提取JSON块（支持```json...```格式）
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    return data.get("matched_dataset_ids", [])
                except json.JSONDecodeError:
                    pass

            # 尝试查找纯JSON（查找最外层{}）
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data.get("matched_dataset_ids", [])
                except json.JSONDecodeError:
                    pass

            # 解析失败
            logger.warning(f"无法解析LLM语义搜索响应为JSON: {response[:200]}...")
            return []

    def _calculate_relevance_score(
        self,
        dataset: DatasetMetadata,
        query: str,
        filters: Dict[str, Any]
    ) -> float:
        """计算相关性评分

        Args:
            dataset: 数据集
            query: 搜索查询
            filters: 过滤条件

        Returns:
            float: 相关性评分 (0-1)
        """
        score = 0.0
        query_lower = query.lower()

        # 1. 名称匹配 (权重: 0.4)
        if query_lower in dataset.name.lower():
            score += 0.4

        # 2. 描述匹配 (权重: 0.3)
        if query_lower in dataset.description.lower():
            score += 0.3

        # 3. 标签匹配 (权重: 0.2)
        for tag in dataset.tags:
            if query_lower in tag.lower():
                score += 0.2
                break

        # 4. 关键词匹配 (权重: 0.1)
        keywords = query.split()
        for keyword in keywords:
            if keyword.lower() in dataset.name.lower():
                score += 0.1

        # 5. 过滤条件匹配
        if "industry" in filters:
            if dataset.industry and filters["industry"].lower() in dataset.industry.lower():
                score += 0.3

        if "tags" in filters:
            for filter_tag in filters["tags"]:
                if filter_tag in dataset.tags:
                    score += 0.2

        return min(score, 1.0)  # 限制最大为1.0

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史

        Args:
            session_id: 会话ID

        Returns:
            List[Dict]: 消息历史
        """
        if session_id not in self.sessions:
            return []

        session = self.sessions[session_id]
        return [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages
        ]

    def clear_session(self, session_id: str):
        """清除会话

        Args:
            session_id: 会话ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"清除会话: {session_id}")
