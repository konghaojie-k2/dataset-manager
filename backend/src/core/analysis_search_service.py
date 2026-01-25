#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LLM增强的分析结果搜索服务（深层次分析）"""

from typing import Dict, List, Any, Optional
from loguru import logger
import json
import re

from ..llms.llms import get_reasoning_llm
from ..schemas.dataset import DatasetMetadata


# ===== 提示词模板 =====

def _build_analysis_search_prompt(
    query: str,
    analysis_results_info: List[Dict[str, Any]],
    intent_result: Optional[str] = None
) -> str:
    """构建LLM分析结果搜索提示词
    
    Args:
        query: 用户原始查询
        analysis_results_info: 分析结果信息列表（格式化后的）
        intent_result: 意图识别结果（可选）
    
    Returns:
        str: 完整的提示词
    """
    # 格式化分析结果列表
    results_str = json.dumps(analysis_results_info, ensure_ascii=False, indent=2)
    
    # 构建意图分析部分
    intent_section = ""
    if intent_result:
        try:
            intent_data = json.loads(intent_result)
            intent_section = f"""
## 意图分析结果
```json
{json.dumps(intent_data, ensure_ascii=False, indent=2)}
```
"""
        except json.JSONDecodeError:
            intent_section = f"""
## 意图分析结果（原始）
{intent_result}
"""
    
    prompt = f"""你是一个数据分析专家。根据用户查询，从数据集的分析结果中进行深层次的语义搜索和分析。

## 用户查询
{query}
{intent_section}
## 可用分析结果列表
共 {len(analysis_results_info)} 个数据集的分析结果：

```json
{results_str}
```

## 任务
根据用户查询，在分析结果中进行深层次的语义搜索：

1. **理解查询意图**：分析用户想要了解什么（业务含义、控制关系、数据质量、洞察、建议等）
2. **语义匹配**：在分析结果的内容中进行语义匹配，不仅仅是关键词匹配
3. **提取相关信息**：从匹配的分析结果中提取最相关的信息片段
4. **综合分析**：如果涉及多个数据集的分析结果，进行对比和综合分析

## 分析结果类型说明
- **business_meaning_analysis**: 业务含义分析，描述数据的业务意义
- **control_relationships_analysis**: 控制原理分析，描述变量间的控制关系
- **basic_analysis**: 基础分析，数据的基本统计和特征
- **detailed_analysis**: 详细分析，深入的数据分析结果
- **insights**: 数据洞察，关键发现和见解
- **recommendations**: 分析建议，基于分析结果的建议
- **quality_analysis_results**: 质量分析结果，数据质量评估

## 输出格式（JSON）
严格按照以下JSON格式输出：

{{
  "type": "analysis" | "not_found" | "message",
  "matched_datasets": [
    {{
      "dataset_id": "数据集ID",
      "dataset_name": "数据集名称",
      "analysis_type": "匹配的分析类型（business_meaning/control_relationships/insights等）",
      "matched_content": "匹配的内容片段",
      "relevance_score": 0.95,
      "reasoning": "为什么这个分析结果匹配"
    }}
  ],
  "count": 匹配数量,
  "summary": "综合分析摘要（如果有多个匹配结果）",
  "message": "消息内容"
}}

## 重要提示
- 进行语义理解，不仅仅是关键词匹配
- 提取最相关的分析内容片段，不要返回整个分析结果
- 如果找到多个相关结果，进行对比和综合分析
- 如果没有找到匹配的分析结果，使用 "not_found" 类型
- 确保返回的dataset_id在可用分析结果列表中存在

现在请分析用户查询并在分析结果中进行深层次搜索，返回JSON结果。"""
    
    return prompt


# ===== 分析结果搜索服务 =====

class AnalysisSearchService:
    """LLM增强的分析结果搜索服务（深层次分析）"""
    
    def __init__(self):
        """初始化分析结果搜索服务"""
        self.llm = get_reasoning_llm()
        logger.info("LLM增强分析结果搜索服务初始化完成")
    
    def _format_analysis_results_info(
        self, 
        datasets: List[DatasetMetadata]
    ) -> List[Dict[str, Any]]:
        """格式化分析结果信息
        
        Args:
            datasets: 数据集列表（需要包含分析结果）
        
        Returns:
            List[Dict]: 格式化后的分析结果信息列表
        """
        analysis_results_info = []
        
        for ds in datasets:
            # 提取各种分析结果
            analysis_data = {
                "dataset_id": ds.id,
                "dataset_name": ds.name,
                "industry": ds.industrial_domain or ds.industry or "",
            }
            
            # 业务分析结果
            if ds.business_meaning_analysis:
                if isinstance(ds.business_meaning_analysis, str):
                    analysis_data["business_meaning_analysis"] = ds.business_meaning_analysis[:500]  # 限制长度
                else:
                    analysis_data["business_meaning_analysis"] = str(ds.business_meaning_analysis)[:500]
            
            if ds.control_relationships_analysis:
                if isinstance(ds.control_relationships_analysis, str):
                    analysis_data["control_relationships_analysis"] = ds.control_relationships_analysis[:500]
                else:
                    analysis_data["control_relationships_analysis"] = str(ds.control_relationships_analysis)[:500]
            
            if ds.basic_analysis:
                if isinstance(ds.basic_analysis, str):
                    analysis_data["basic_analysis"] = ds.basic_analysis[:500]
                else:
                    analysis_data["basic_analysis"] = str(ds.basic_analysis)[:500]
            
            if ds.detailed_analysis:
                if isinstance(ds.detailed_analysis, str):
                    analysis_data["detailed_analysis"] = ds.detailed_analysis[:500]
                else:
                    analysis_data["detailed_analysis"] = str(ds.detailed_analysis)[:500]
            
            # 洞察和建议
            if ds.insights:
                analysis_data["insights"] = ds.insights[:10]  # 限制数量
            
            if ds.recommendations:
                if isinstance(ds.recommendations, str):
                    analysis_data["recommendations"] = ds.recommendations[:500]
                else:
                    analysis_data["recommendations"] = str(ds.recommendations)[:500]
            
            # 质量分析结果（摘要）
            if ds.quality_analysis_results:
                if isinstance(ds.quality_analysis_results, dict):
                    # 只提取关键信息
                    quality_summary = {
                        "overall_score": ds.quality_analysis_results.get("overall_score"),
                        "quality_level": ds.quality_analysis_results.get("quality_level"),
                        "key_issues": ds.quality_analysis_results.get("key_issues", [])[:5]  # 限制数量
                    }
                    analysis_data["quality_analysis_results"] = quality_summary
                else:
                    analysis_data["quality_analysis_results"] = str(ds.quality_analysis_results)[:500]
            
            # 只包含有分析结果的数据集
            has_analysis = any([
                analysis_data.get("business_meaning_analysis"),
                analysis_data.get("control_relationships_analysis"),
                analysis_data.get("basic_analysis"),
                analysis_data.get("detailed_analysis"),
                analysis_data.get("insights"),
                analysis_data.get("recommendations"),
                analysis_data.get("quality_analysis_results")
            ])
            
            if has_analysis:
                analysis_results_info.append(analysis_data)
        
        return analysis_results_info
    
    def _parse_llm_result(self, response: str) -> Dict[str, Any]:
        """解析LLM返回的搜索结果
        
        Args:
            response: LLM返回的文本
        
        Returns:
            Dict: 解析后的结果，如果解析失败返回默认值
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
            return {
                "type": "message",
                "message": "LLM返回格式错误，无法解析结果"
            }
    
    async def search(
        self,
        query: str,
        datasets: List[DatasetMetadata],
        intent_result: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行LLM增强的分析结果搜索
        
        Args:
            query: 用户原始查询
            datasets: 所有数据集列表（需要包含分析结果）
            intent_result: 意图识别结果（可选）
        
        Returns:
            Dict: 搜索结果，包含type字段（analysis/not_found/message）
        """
        logger.info(f"开始LLM增强分析结果搜索: query={query}, datasets_count={len(datasets)}")
        
        # 格式化分析结果信息
        analysis_results_info = self._format_analysis_results_info(datasets)
        
        if not analysis_results_info:
            logger.warning("没有找到包含分析结果的数据集")
            return {
                "type": "not_found",
                "message": "没有找到包含分析结果的数据集",
                "query": query
            }
        
        # 构建LLM提示词
        prompt = _build_analysis_search_prompt(query, analysis_results_info, intent_result)
        
        # 调用LLM进行推理
        try:
            logger.info("调用LLM进行深层次分析结果搜索...")
            response = await self.llm.ainvoke(prompt)
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            logger.debug(f"LLM原始响应: {response_content[:500]}...")
            
            # 解析LLM返回结果
            llm_result = self._parse_llm_result(response_content)
            
            logger.info(f"LLM分析结果搜索完成: type={llm_result.get('type')}")
            return llm_result
            
        except Exception as e:
            logger.error(f"LLM调用失败: {e}", exc_info=True)
            raise
    
    def process_search_result(
        self,
        llm_result: Dict[str, Any],
        all_datasets: List[DatasetMetadata],
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """处理LLM返回的搜索结果，转换为最终格式
        
        Args:
            llm_result: LLM返回的结果字典
            all_datasets: 所有数据集列表
            query: 用户查询
            limit: 结果数量限制
        
        Returns:
            Dict: 格式化的最终结果
        """
        result_type = llm_result.get("type", "message")
        
        if result_type == "analysis":
            # 分析结果类型：返回匹配的分析结果
            matched_datasets = llm_result.get("matched_datasets", [])
            if not matched_datasets:
                return {
                    "type": "not_found",
                    "message": "未找到匹配的分析结果",
                    "query": query
                }
            
            # 限制返回数量
            matched_datasets = matched_datasets[:limit]
            
            # 创建ID到数据集的映射，用于获取完整信息
            id_to_dataset = {ds.id: ds for ds in all_datasets}
            
            # 丰富匹配结果的信息
            enriched_results = []
            for match in matched_datasets:
                dataset_id = match.get("dataset_id")
                if dataset_id in id_to_dataset:
                    ds = id_to_dataset[dataset_id]
                    enriched_result = {
                        "dataset_id": dataset_id,
                        "dataset_name": match.get("dataset_name", ds.name),
                        "analysis_type": match.get("analysis_type", "unknown"),
                        "matched_content": match.get("matched_content", ""),
                        "relevance_score": match.get("relevance_score", 0.0),
                        "reasoning": match.get("reasoning", ""),
                        # 添加数据集基本信息
                        "dataset_info": {
                            "industry": ds.industrial_domain or ds.industry,
                            "tags": ds.tags or [],
                            "processing_status": ds.processing_status
                        }
                    }
                    enriched_results.append(enriched_result)
            
            count = llm_result.get("count", len(enriched_results))
            summary = llm_result.get("summary", "")
            
            return {
                "type": "analysis",
                "matched_datasets": enriched_results,
                "count": len(enriched_results),
                "total_matched": count,
                "summary": summary,
                "query": query
            }
        
        elif result_type == "not_found":
            # 未找到类型
            message = llm_result.get("message", "未找到相关的分析结果")
            return {
                "type": "not_found",
                "message": message,
                "query": query
            }
        
        else:
            # 消息类型或其他
            message = llm_result.get("message", "查询完成")
            return {
                "type": "message",
                "message": message,
                "query": query,
                "raw_result": llm_result
            }
    
    def fallback_keyword_search(
        self,
        query: str,
        all_datasets: List[DatasetMetadata],
        limit: int = 10
    ) -> Dict[str, Any]:
        """降级搜索：传统关键词匹配逻辑（在分析结果中搜索）
        
        Args:
            query: 用户查询
            all_datasets: 所有数据集列表
            limit: 结果数量限制
        
        Returns:
            Dict: JSON格式的搜索结果
        """
        logger.info("使用传统关键词匹配搜索分析结果")
        
        query_lower = query.lower().strip()
        query_keywords = query_lower.split()
        
        matched_results = []
        
        for ds in all_datasets:
            match_info = {
                "dataset_id": ds.id,
                "dataset_name": ds.name,
                "analysis_type": [],
                "matched_content": [],
                "relevance_score": 0.0
            }
            
            # 在各个分析结果字段中搜索
            if ds.business_meaning_analysis:
                content = str(ds.business_meaning_analysis).lower()
                if any(keyword in content for keyword in query_keywords):
                    match_info["analysis_type"].append("business_meaning")
                    # 提取匹配的片段
                    for keyword in query_keywords:
                        if keyword in content:
                            idx = content.find(keyword)
                            snippet = str(ds.business_meaning_analysis)[max(0, idx-50):idx+200]
                            match_info["matched_content"].append(snippet)
                            break
            
            if ds.control_relationships_analysis:
                content = str(ds.control_relationships_analysis).lower()
                if any(keyword in content for keyword in query_keywords):
                    match_info["analysis_type"].append("control_relationships")
                    for keyword in query_keywords:
                        if keyword in content:
                            idx = content.find(keyword)
                            snippet = str(ds.control_relationships_analysis)[max(0, idx-50):idx+200]
                            match_info["matched_content"].append(snippet)
                            break
            
            if ds.insights:
                for insight in ds.insights:
                    if any(keyword in insight.lower() for keyword in query_keywords):
                        match_info["analysis_type"].append("insights")
                        match_info["matched_content"].append(insight)
                        break
            
            if ds.recommendations:
                content = str(ds.recommendations).lower()
                if any(keyword in content for keyword in query_keywords):
                    match_info["analysis_type"].append("recommendations")
                    for keyword in query_keywords:
                        if keyword in content:
                            idx = content.find(keyword)
                            snippet = str(ds.recommendations)[max(0, idx-50):idx+200]
                            match_info["matched_content"].append(snippet)
                            break
            
            # 如果有匹配，添加到结果中
            if match_info["analysis_type"]:
                match_info["relevance_score"] = len(match_info["analysis_type"]) / 10.0  # 简单的相关性评分
                matched_results.append(match_info)
        
        # 按相关性排序
        matched_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        if not matched_results:
            return {
                "type": "not_found",
                "message": "未找到匹配的分析结果",
                "query": query
            }
        
        # 限制返回数量
        matched_results = matched_results[:limit]
        
        return {
            "type": "analysis",
            "matched_datasets": matched_results,
            "count": len(matched_results),
            "total_matched": len(matched_results),
            "query": query,
            "fallback": True  # 标记这是降级搜索
        }
