#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""意图澄清服务 - 集成A2UI表单生成"""

from typing import Dict, List, Any, Optional
from loguru import logger
import json

from ..schemas.chat import A2UISchema
from .a2ui_form_service import A2UIFormService
from .intent_analysis import IntentAnalysisService


class ClarificationService:
    """意图澄清服务 - 集成A2UI表单生成"""
    
    def __init__(self):
        """初始化澄清服务"""
        self.intent_service = IntentAnalysisService()
        self.a2ui_form_service = A2UIFormService()
        logger.info("意图澄清服务初始化完成")
    
    def _should_clarify(
        self,
        intent_result: Dict[str, Any],
        confidence_threshold: float = 0.6
    ) -> bool:
        """判断是否需要澄清
        
        Args:
            intent_result: 意图分析结果
            confidence_threshold: 置信度阈值，低于此值需要澄清
        
        Returns:
            bool: 是否需要澄清
        """
        # 检查明确标记的澄清需求
        if intent_result.get("clarification_needed", False):
            return True
        
        # 检查置信度
        confidence = intent_result.get("confidence", 1.0)
        if confidence < confidence_threshold:
            logger.info(f"置信度较低 ({confidence})，需要澄清")
            return True
        
        # 检查过滤条件是否为空或过于宽泛
        filters = intent_result.get("filters", {})
        if not filters or len(filters) == 0:
            logger.info("过滤条件为空，可能需要澄清")
            return True
        
        return False
    
    async def clarify_intent(
        self,
        query: str,
        intent_result: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行意图澄清
        
        如果意图分析结果不够清晰，生成A2UI表单供用户填写。
        
        Args:
            query: 用户原始查询
            intent_result: 意图识别工具的JSON输出（可选，如果没有则重新分析）
            session_context: 会话上下文（用于预填表单）
        
        Returns:
            Dict: 澄清结果，包含：
            - needs_clarification: 是否需要澄清
            - form_schema: A2UI表单Schema（如果需要澄清）
            - message: 澄清消息
            - intent: 意图分析结果
        """
        logger.info(f"开始意图澄清: query={query}")
        
        # 1. 如果没有提供意图分析结果，先进行分析
        if intent_result is None:
            logger.info("未提供意图分析结果，先进行意图分析...")
            intent_dict = await self.intent_service.analyze_intent(query, context=session_context or {})
        else:
            try:
                intent_dict = json.loads(intent_result) if isinstance(intent_result, str) else intent_result
            except json.JSONDecodeError:
                logger.warning("意图分析结果格式错误，重新分析...")
                intent_dict = await self.intent_service.analyze_intent(query, context=session_context or {})
        
        # 2. 判断是否需要澄清
        needs_clarification = self._should_clarify(intent_dict)
        
        if not needs_clarification:
            logger.info("意图清晰，无需澄清")
            return {
                "needs_clarification": False,
                "message": "意图清晰，可以直接进行搜索",
                "intent": intent_dict
            }
        
        # 3. 需要澄清，生成A2UI表单
        logger.info("意图不够清晰，生成澄清表单...")
        
        try:
            form_schema = await self.a2ui_form_service.generate_clarification_form(
                user_query=query,
                intent=intent_dict,
                session_context=session_context
            )
            
            clarification_reason = intent_dict.get("clarification_reason", "查询不够明确")
            clarification_message = "请完善信息"
            
            logger.info(f"澄清表单生成成功: {len(form_schema.fields)}个字段")
            
            return {
                "needs_clarification": True,
                "form_schema": form_schema.model_dump(mode='json'),
                "message": clarification_message,
                "clarification_reason": clarification_reason,
                "intent": intent_dict
            }
            
        except Exception as e:
            logger.error(f"生成澄清表单失败: {e}", exc_info=True)
            # 降级：返回简单的澄清消息
            return {
                "needs_clarification": True,
                "message": f"您的查询可能需要更多信息。请提供：行业、标签、数据质量要求等。",
                "clarification_reason": "表单生成失败，使用默认提示",
                "intent": intent_dict
            }
