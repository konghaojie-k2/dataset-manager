#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph Agent 工具定义

将增强元数据功能封装为 Agent 可调用的工具
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool


# ==================== 工具输入模型 ====================

class SearchDatasetsInput(BaseModel):
    """搜索数据集输入"""
    query: str = Field(description="搜索关键词，如'销售数据'、'用户行为'")
    tags: Optional[List[str]] = Field(default=None, description="标签筛选")
    industry: Optional[str] = Field(default=None, description="行业筛选")
    limit: int = Field(default=10, description="返回结果数量")


class GetSchemaInput(BaseModel):
    """获取数据集结构输入"""
    dataset_id: str = Field(description="数据集ID")
    include_semantics: bool = Field(default=True, description="是否包含语义信息")


class GetQualityInput(BaseModel):
    """获取数据集质量输入"""
    dataset_id: str = Field(description="数据集ID")


class GetLineageInput(BaseModel):
    """获取数据血缘输入"""
    dataset_id: str = Field(description="数据集ID")
    direction: str = Field(default="both", description="查询方向: upstream, downstream, both")


class NLQueryInput(BaseModel):
    """自然语言查询输入"""
    dataset_id: str = Field(description="数据集ID")
    question: str = Field(description="自然语言问题，如'数据有多少行？'、'销售额最高的产品是什么？'")


class AnalyzeMetadataInput(BaseModel):
    """分析元数据输入"""
    dataset_id: str = Field(description="数据集ID")
    sample_size: int = Field(default=1000, description="采样大小")


# ==================== Agent 工具实现 ====================

class DatasetAgentToolkit:
    """数据集 Agent 工具包"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def search_datasets(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        industry: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """搜索数据集
        
        用这个工具来查找相关的数据集。
        
        Args:
            query: 搜索关键词
            tags: 标签筛选
            industry: 行业筛选
            limit: 返回数量
            
        Returns:
            搜索结果描述
        """
        import httpx
        
        params = {"limit": limit}
        if query:
            params["q"] = query
        if tags:
            params["tags"] = ",".join(tags)
        if industry:
            params["industry"] = industry
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/metadata/search",
                    params=params,
                    timeout=30.0
                )
                data = response.json()
                
                if data.get("total", 0) == 0:
                    return f"没有找到匹配的数据集。"
                
                results = data.get("results", [])
                lines = [f"找到 {data['total']} 个相关数据集：\n"]
                
                for i, ds in enumerate(results[:5], 1):
                    lines.append(f"{i}. **{ds['name']}**")
                    if ds.get("description"):
                        lines.append(f"   {ds['description'][:100]}")
                    if ds.get("tags"):
                        lines.append(f"   标签: {', '.join(ds['tags'])}")
                    if ds.get("quality_score"):
                        lines.append(f"   质量评分: {ds['quality_score']:.1f}")
                    lines.append("")
                
                return "\n".join(lines)
                
            except Exception as e:
                return f"搜索失败: {str(e)}"
    
    async def get_dataset_schema(
        self,
        dataset_id: str,
        include_semantics: bool = True
    ) -> str:
        """获取数据集结构
        
        用这个工具来了解数据集的列结构。
        
        Args:
            dataset_id: 数据集ID
            include_semantics: 是否包含语义信息
            
        Returns:
            数据集结构描述
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/metadata/schema/{dataset_id}",
                    params={"include_semantics": include_semantics},
                    timeout=30.0
                )
                data = response.json()
                
                lines = [f"# 数据集: {data.get('name', dataset_id)}\n"]
                
                if data.get("description"):
                    lines.append(f"{data['description']}\n")
                
                # 关键字段
                if data.get("key_fields"):
                    lines.append("## 关键字段")
                    for field in data["key_fields"]:
                        lines.append(f"- **{field['name']}** ({field['type']}): {field.get('description', '')}")
                    lines.append("")
                
                # 所有列
                if data.get("columns"):
                    lines.append(f"## 全部列 ({len(data['columns'])} 个)")
                    for col in data["columns"]:
                        dtype = col.get("data_type", "unknown")
                        meaning = col.get("business_meaning", "")
                        lines.append(f"- {col['name']}: {dtype} {f'- {meaning}' if meaning else ''}")
                
                return "\n".join(lines)
                
            except Exception as e:
                return f"获取结构失败: {str(e)}"
    
    async def get_dataset_quality(self, dataset_id: str) -> str:
        """获取数据集质量
        
        用这个工具来了解数据质量状况。
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            质量评分描述
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/metadata/quality/{dataset_id}",
                    timeout=30.0
                )
                data = response.json()
                
                quality = data.get("quality_score", {})
                lines = [f"# 数据质量报告\n"]
                
                lines.append(f"**综合评分: {quality.get('overall_score', 0):.1f}/100**\n")
                
                lines.append("## 各项指标")
                lines.append(f"- 完整性: {quality.get('completeness', 0):.1f}%")
                lines.append(f"- 唯一性: {quality.get('uniqueness', 0):.1f}%")
                lines.append(f"- 一致性: {quality.get('consistency', 0):.1f}%")
                
                if quality.get("issues"):
                    lines.append("\n## 发现的问题")
                    for issue in quality["issues"]:
                        lines.append(f"- {issue}")
                
                if quality.get("recommendations"):
                    lines.append("\n## 建议")
                    for rec in quality["recommendations"]:
                        lines.append(f"- {rec}")
                
                return "\n".join(lines)
                
            except Exception as e:
                return f"获取质量失败: {str(e)}"
    
    async def get_data_lineage(
        self,
        dataset_id: str,
        direction: str = "both"
    ) -> str:
        """获取数据血缘
        
        用这个工具来了解数据的来源和去向。
        
        Args:
            dataset_id: 数据集ID
            direction: upstream, downstream, both
            
        Returns:
            血缘关系描述
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/lineage/{dataset_id}",
                    params={"direction": direction},
                    timeout=30.0
                )
                data = response.json()
                
                lines = [f"# 数据血缘: {dataset_id}\n"]
                
                if data.get("upstream"):
                    lines.append("## 上游数据")
                    for ds in data["upstream"]:
                        lines.append(f"- {ds.get('name', ds.get('id'))}")
                
                if data.get("downstream"):
                    lines.append("\n## 下游数据")
                    for ds in data["downstream"]:
                        lines.append(f"- {ds.get('name', ds.get('id'))}")
                
                if not data.get("upstream") and not data.get("downstream"):
                    lines.append("未找到血缘关系")
                
                return "\n".join(lines)
                
            except Exception as e:
                return f"获取血缘失败: {str(e)}"
    
    async def query_with_nl(
        self,
        dataset_id: str,
        question: str
    ) -> str:
        """自然语言查询
        
        用这个工具来用自然语言查询数据内容。
        
        Args:
            dataset_id: 数据集ID
            question: 问题，如'数据有多少行？'
            
        Returns:
            查询结果
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/metadata/query",
                    json={
                        "dataset_id": dataset_id,
                        "question": question,
                        "include_preview": True
                    },
                    timeout=60.0
                )
                data = response.json()
                
                lines = [f"**问题**: {question}\n"]
                lines.append(f"**回答**: {data.get('answer', '无法回答')}\n")
                
                if data.get("data_preview"):
                    lines.append("\n**数据预览**:")
                    # 简化显示
                    preview = data["data_preview"][:2]
                    for row in preview:
                        lines.append(f"- {row}")
                
                return "\n".join(lines)
                
            except Exception as e:
                return f"查询失败: {str(e)}"


# 创建全局工具实例
dataset_toolkit = DatasetAgentToolkit()


# ==================== LangGraph 工具函数 ====================

@tool(args_schema=SearchDatasetsInput)
def search_datasets_tool(
    query: str,
    tags: Optional[List[str]] = None,
    industry: Optional[str] = None,
    limit: int = 10
) -> str:
    """搜索相关数据集
    
    当用户想要查找数据集时使用此工具。
    """
    import asyncio
    return asyncio.run(dataset_toolkit.search_datasets(query, tags, industry, limit))


@tool(args_schema=GetSchemaInput)
def get_dataset_schema_tool(
    dataset_id: str,
    include_semantics: bool = True
) -> str:
    """获取数据集结构
    
    当需要了解数据集有哪些列时使用此工具。
    """
    import asyncio
    return asyncio.run(dataset_toolkit.get_dataset_schema(dataset_id, include_semantics))


@tool(args_schema=GetQualityInput)
def get_dataset_quality_tool(dataset_id: str) -> str:
    """获取数据质量报告
    
    当需要了解数据质量时使用此工具。
    """
    import asyncio
    return asyncio.run(dataset_toolkit.get_dataset_quality(dataset_id))


@tool(args_schema=GetLineageInput)
def get_data_lineage_tool(
    dataset_id: str,
    direction: str = "both"
) -> str:
    """获取数据血缘关系
    
    当需要了解数据来源和去向时使用此工具。
    """
    import asyncio
    return asyncio.run(dataset_toolkit.get_data_lineage(dataset_id, direction))


@tool(args_schema=NLQueryInput)
def query_with_nl_tool(
    dataset_id: str,
    question: str
) -> str:
    """自然语言查询
    
    当用户用自然语言提问关于数据的问题时使用此工具。
    """
    import asyncio
    return asyncio.run(dataset_toolkit.query_with_nl(dataset_id, question))


# 导出所有工具
DATASET_TOOLS = [
    search_datasets_tool,
    get_dataset_schema_tool,
    get_dataset_quality_tool,
    get_data_lineage_tool,
    query_with_nl_tool
]

__all__ = [
    'DatasetAgentToolkit',
    'dataset_toolkit',
    'DATASET_TOOLS',
    'SearchDatasetsInput',
    'GetSchemaInput',
    'GetQualityInput',
    'GetLineageInput',
    'NLQueryInput'
]
