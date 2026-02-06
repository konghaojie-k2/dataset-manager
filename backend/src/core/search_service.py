#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LLM增强的智能搜索服务（Subagent模式）"""

from typing import Dict, List, Any, Optional
from loguru import logger
import json
import re

from ..llms.llms import get_reasoning_llm
from ..schemas.dataset import DatasetMetadata


# ===== 提示词模板 =====

def _build_search_prompt(
    query: str,
    datasets_info: List[Dict[str, Any]],
    intent_result: Optional[str] = None
) -> str:
    """构建LLM搜索提示词
    
    Args:
        query: 用户原始查询
        datasets_info: 数据集信息列表（格式化后的）
        intent_result: 意图识别结果（可选）
    
    Returns:
        str: 完整的提示词
    """
    # 格式化数据集列表
    datasets_str = json.dumps(datasets_info, ensure_ascii=False, indent=2)
    
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
    
    prompt = f"""你是一个数据集查询助手。根据用户查询，从可用数据集中找到答案。

## 用户查询
{query}
{intent_section}
## 可用数据集列表
共 {len(datasets_info)} 个数据集：

```json
{datasets_str}
```

## 任务
根据用户查询的类型，决定返回什么格式的结果：

1. **统计问题**（如"有几个数据集"、"总数是多少"、"有多少个"）：
   - 返回：{{"type": "count", "value": 数字, "message": "共有X个数据集"}}

2. **搜索问题**（如"找半导体数据集"、"XX相关的"、"搜索XX"）：
   - 如果有匹配：{{"type": "list", "datasets": [数据集ID列表], "count": 数量}}
   - 如果没有匹配：{{"type": "not_found", "message": "未找到相关数据集"}}

3. **其他问题**：
   - 根据具体情况返回合适的格式，可以使用 "message" 类型

## 输出格式（JSON）
严格按照以下JSON格式输出：

{{
  "type": "count" | "list" | "not_found" | "message",
  "value": 数字（如果是count类型）,
  "datasets": ["dataset_id1", "dataset_id2", ...]（如果是list类型，只返回ID列表）,
  "count": 数量（如果是list类型）,
  "message": "消息内容",
  "reasoning": "推理过程（可选）"
}}

## 重要提示
- 对于统计问题，直接返回数量，不需要返回数据集列表
- 对于搜索问题，只返回匹配的数据集ID列表，不要返回完整数据集信息
- 如果没有找到匹配的数据集，使用 "not_found" 类型
- 确保返回的dataset_id在可用数据集列表中存在

现在请分析用户查询并返回JSON结果。"""
    
    return prompt


# ===== 搜索服务 =====

class SearchService:
    """LLM增强的智能搜索服务（Subagent模式）"""
    
    def __init__(self):
        """初始化搜索服务"""
        self.llm = get_reasoning_llm()
        logger.debug("LLM增强搜索服务初始化完成")
    
    def _format_datasets_info(self, datasets: List[DatasetMetadata]) -> List[Dict[str, Any]]:
        """格式化数据集信息（只包含关键字段，减少token消耗）
        
        Args:
            datasets: 数据集列表
        
        Returns:
            List[Dict]: 格式化后的数据集信息列表
        """
        datasets_info = []
        for ds in datasets:
            datasets_info.append({
                "id": ds.id,
                "name": ds.name,
                "description": ds.description or "",
                "tags": ds.tags or [],
                "industry": ds.industrial_domain or ds.industry or "",
                "processing_status": ds.processing_status or ""
            })
        return datasets_info
    
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
        """执行LLM增强的智能搜索
        
        Args:
            query: 用户原始查询
            datasets: 所有数据集列表
            intent_result: 意图识别结果（可选）
        
        Returns:
            Dict: 搜索结果，包含type字段（count/list/not_found/message）
        """
        logger.debug(f"开始LLM增强搜索: query={query}, datasets_count={len(datasets)}")
        
        # 处理空数据库情况
        if not datasets:
            logger.warning("数据库中没有数据集")
            return {
                "type": "message",
                "message": "数据库中没有数据集",
                "count": 0,
                "query": query
            }
        
        # 格式化数据集信息
        datasets_info = self._format_datasets_info(datasets)
        
        # 对于统计查询，如果数据集数量很大，可以直接计算，不调用LLM
        is_statistical_query = any(keyword in query.lower() for keyword in ["几个", "多少", "总数", "数量", "count", "how many"])
        if is_statistical_query and len(datasets) > 100:
            logger.debug(f"统计查询且数据集较多，直接返回数量: {len(datasets)}")
            return {
                "type": "count",
                "value": len(datasets),
                "message": f"共有 {len(datasets)} 个数据集",
                "query": query
            }
        
        # 构建LLM提示词
        prompt = _build_search_prompt(query, datasets_info, intent_result)
        
        # 调用LLM进行推理
        try:
            logger.debug("调用LLM进行智能搜索...")
            response = await self.llm.ainvoke(prompt)
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            logger.debug(f"LLM原始响应: {response_content[:500]}...")
            
            # 解析LLM返回结果
            llm_result = self._parse_llm_result(response_content)
            
            logger.debug(f"LLM搜索完成: type={llm_result.get('type')}")
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
        
        if result_type == "count":
            # 统计类型：返回数量
            value = llm_result.get("value", len(all_datasets))
            message = llm_result.get("message", f"共有 {value} 个数据集")
            return {
                "type": "count",
                "value": value,
                "message": message,
                "query": query
            }
        
        elif result_type == "list":
            # 列表类型：返回匹配的数据集列表
            dataset_ids = llm_result.get("datasets", [])
            
            # 确保dataset_ids是列表格式
            if not isinstance(dataset_ids, list):
                logger.warning(f"LLM返回的datasets不是列表格式: {type(dataset_ids)}, value: {dataset_ids}")
                dataset_ids = []
            
            # 清理数据集ID格式（去除空格，转换为字符串）
            dataset_ids = [str(ds_id).strip() for ds_id in dataset_ids if ds_id]
            
            logger.debug(f"处理搜索结果: type=list, dataset_ids={dataset_ids}, count={len(dataset_ids)}")
            
            if not dataset_ids:
                logger.warning(f"LLM返回的datasets列表为空，返回not_found")
                return {
                    "type": "not_found",
                    "message": "未找到匹配的数据集",
                    "query": query
                }
            
            # 创建ID到数据集的映射
            id_to_dataset = {ds.id: ds for ds in all_datasets}
            logger.debug(f"可用数据集总数: {len(all_datasets)}, ID映射表大小: {len(id_to_dataset)}")
            logger.debug(f"可用数据集ID列表（前10个）: {list(id_to_dataset.keys())[:10]}")
            logger.debug(f"LLM返回的数据集ID: {dataset_ids}")
            
            # 获取匹配的数据集
            matched_datasets = []
            not_found_ids = []
            for dataset_id in dataset_ids[:limit]:
                logger.debug(f"检查数据集ID: {dataset_id}, 类型: {type(dataset_id)}")
                # 尝试多种匹配方式
                matched_ds = None
                if dataset_id in id_to_dataset:
                    matched_ds = id_to_dataset[dataset_id]
                else:
                    # 尝试字符串匹配（去除空格、大小写不敏感）
                    dataset_id_clean = str(dataset_id).strip()
                    for ds_id, ds in id_to_dataset.items():
                        if str(ds_id).strip().lower() == dataset_id_clean.lower():
                            matched_ds = ds
                            logger.debug(f"通过字符串匹配找到数据集: {dataset_id} -> {ds_id}")
                            break
                
                if matched_ds:
                    ds = matched_ds
                    try:
                        # 处理industry字段：industrial_domain可能是字典
                        industry_value = ds.industry
                        if ds.industrial_domain:
                            if isinstance(ds.industrial_domain, dict):
                                industry_value = ds.industrial_domain.get("industry", ds.industry) or ds.industry
                            else:
                                industry_value = ds.industrial_domain
                        
                        # 获取row_count和column_count
                        row_count = None
                        column_count = None
                        if ds.quality_metrics:
                            row_count = ds.quality_metrics.total_rows
                            column_count = ds.quality_metrics.total_columns
                        else:
                            # 如果没有quality_metrics，从columns获取column_count
                            column_count = len(ds.columns) if ds.columns else 0
                        
                        matched_datasets.append({
                            "id": ds.id,
                            "name": ds.name,
                            "description": ds.description,
                            "tags": ds.tags or [],
                            "industry": industry_value,
                            "file_size": ds.file_size,
                            "upload_time": ds.upload_time.isoformat() if ds.upload_time else None,
                            "processing_status": ds.processing_status,
                            "row_count": row_count,
                            "column_count": column_count,
                        })
                        logger.debug(f"成功匹配数据集: {ds.id} - {ds.name}")
                    except Exception as e:
                        logger.error(f"构建matched_dataset时出错: {e}", exc_info=True)
                        not_found_ids.append(dataset_id)
                else:
                    not_found_ids.append(dataset_id)
                    logger.warning(f"数据集ID {dataset_id} 不在可用数据集列表中，可用ID: {list(id_to_dataset.keys())[:5]}")
            
            if not_found_ids:
                logger.warning(f"以下数据集ID未找到: {not_found_ids}")
            
            count = llm_result.get("count", len(matched_datasets))
            message = llm_result.get("message", f"找到{len(matched_datasets)}个匹配的数据集")
            
            # 如果匹配到了数据集，返回结果；否则返回not_found
            if matched_datasets:
                logger.info(f"成功匹配 {len(matched_datasets)} 个数据集")
                return {
                    "type": "list",
                    "datasets": matched_datasets,
                    "count": len(matched_datasets),
                    "total_matched": count,
                    "message": message,
                    "query": query
                }
            else:
                logger.warning(f"LLM返回了数据集ID列表，但所有ID都不在可用数据集中")
                return {
                    "type": "not_found",
                    "message": "未找到匹配的数据集",
                    "query": query,
                    "reasoning": f"LLM返回了数据集ID列表 {dataset_ids}，但这些ID不在可用数据集列表中"
                }
        
        elif result_type == "not_found":
            # 未找到类型
            message = llm_result.get("message", "未找到相关数据集")
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
        tags: Optional[List[str]] = None,
        industry: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """降级搜索：传统关键词匹配逻辑
        
        Args:
            query: 用户查询
            all_datasets: 所有数据集列表
            tags: 标签过滤（可选）
            industry: 行业过滤（可选）
            limit: 结果数量限制
        
        Returns:
            Dict: JSON格式的搜索结果
        """
        logger.debug("使用传统关键词匹配搜索")
        
        datasets = all_datasets
        
        # 标签过滤
        if tags:
            normalized_tags = {
                tag.strip().lower() if isinstance(tag, str) else str(tag).strip().lower()
                for tag in tags
            }
            
            filtered_datasets = []
            for ds in datasets:
                if not ds.tags:
                    continue
                
                ds_tags_normalized = {
                    tag.strip().lower() if isinstance(tag, str) else str(tag).strip().lower()
                    for tag in ds.tags
                }
                
                if normalized_tags & ds_tags_normalized:
                    filtered_datasets.append(ds)
            
            datasets = filtered_datasets
        
        # 行业过滤
        if industry:
            datasets = [
                ds for ds in datasets
                if ds.industrial_domain and industry.lower() in str(ds.industrial_domain).lower()
            ]
        
        # 关键词匹配
        if query and query.strip():
            query_lower = query.lower().strip()
            query_keywords = query_lower.split()
            
            datasets = [
                ds for ds in datasets
                if any(
                    keyword in ds.name.lower() or
                    keyword in (ds.description or "").lower() or
                    (ds.tags and any(keyword in tag.lower() for tag in ds.tags))
                    for keyword in query_keywords
                )
            ]
        
        # 转换为返回格式
        results = []
        for ds in datasets[:limit]:
            results.append({
                "id": ds.id,
                "name": ds.name,
                "description": ds.description,
                "tags": ds.tags or [],
                "industry": ds.industrial_domain or ds.industry,
                "file_size": ds.file_size,
                "upload_time": ds.upload_time.isoformat() if ds.upload_time else None,
                "processing_status": ds.processing_status,
                "row_count": ds.quality_metrics.total_rows if ds.quality_metrics else None,
                "column_count": ds.quality_metrics.total_columns if ds.quality_metrics else (len(ds.columns) if ds.columns else 0),
            })
        
        if not results:
            return {
                "type": "not_found",
                "message": "未找到匹配的数据集",
                "query": query
            }
        
        return {
            "type": "list",
            "datasets": results,
            "count": len(results),
            "total_matched": len(datasets),
            "query": query,
            "fallback": True  # 标记这是降级搜索
        }
