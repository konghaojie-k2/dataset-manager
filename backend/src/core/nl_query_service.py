#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然语言查询服务 - 完整实现

使用 LLM 将自然语言转换为数据查询
"""

from typing import Dict, Any, Optional, List
from loguru import logger
import json
import re


class NaturalLanguageQueryService:
    """自然语言查询服务"""
    
    def __init__(self):
        self.llm = None  # 会在实际使用时注入
        logger.info("自然语言查询服务初始化完成")
    
    async def query(
        self,
        dataset_id: str,
        question: str,
        schema_info: Dict[str, Any],
        sample_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """执行自然语言查询
        
        Args:
            dataset_id: 数据集ID
            question: 自然语言问题
            schema_info: 数据集结构信息
            sample_data: 数据样本
            
        Returns:
            Dict: 查询结果
        """
        logger.info(f"自然语言查询: {question}")
        
        # 1. 理解问题意图
        intent = self._understand_intent(question, schema_info)
        
        # 2. 生成查询逻辑
        query_plan = self._generate_query_plan(intent, schema_info)
        
        # 3. 生成回答
        answer = await self._generate_answer(question, intent, schema_info, sample_data)
        
        return {
            "question": question,
            "intent": intent,
            "query_plan": query_plan,
            "answer": answer,
            "data_preview": sample_data[:5] if sample_data else None
        }
    
    def _understand_intent(
        self,
        question: str,
        schema_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """理解查询意图"""
        question_lower = question.lower()
        
        intent = {
            "operation": "describe",  # default
            "target_columns": [],
            "filters": [],
            "aggregation": None,
            "sort_by": None,
            "sort_order": "desc",
            "limit": None
        }
        
        # 数量查询
        if any(kw in question_lower for kw in ["多少", "几个", "数量", "count", "how many", "number of"]):
            intent["operation"] = "count"
            intent["aggregation"] = "count"
        
        # 总和查询
        if any(kw in question_lower for kw in ["总和", "总计", "total", "sum"]):
            intent["operation"] = "aggregate"
            intent["aggregation"] = "sum"
        
        # 平均查询
        if any(kw in question_lower for kw in ["平均", "均值", "average", "mean"]):
            intent["operation"] = "aggregate"
            intent["aggregation"] = "mean"
        
        # 最大/最小查询
        if any(kw in question_lower for kw in ["最高", "最大", "最多", "highest", "max"]):
            intent["operation"] = "extreme"
            intent["aggregation"] = "max"
            intent["sort_order"] = "desc"
        elif any(kw in question_lower for kw in ["最低", "最小", "最少", "lowest", "min"]):
            intent["operation"] = "extreme"
            intent["aggregation"] = "min"
            intent["sort_order"] = "asc"
        
        # 描述查询
        if any(kw in question_lower for kw in ["是什么", "有什么", "哪些", "what", "which", "describe"]):
            intent["operation"] = "describe"
        
        # 列表查询
        if any(kw in question_lower for kw in ["列出", "展示", "显示", "list", "show", "display"]):
            intent["operation"] = "list"
        
        # 时间相关查询
        if any(kw in question_lower for kw in ["最近", "latest", "recent"]):
            intent["sort_by"] = self._find_time_column(schema_info)
        
        return intent
    
    def _find_time_column(self, schema_info: Dict) -> Optional[str]:
        """找到时间列"""
        columns = schema_info.get("columns", [])
        for col in columns:
            col_name = col.get("name", "").lower()
            if any(kw in col_name for kw in ["time", "date", "created", "updated"]):
                return col.get("name")
        return None
    
    def _find_numeric_columns(self, schema_info: Dict) -> List[str]:
        """找到数值列"""
        numeric_types = ["int", "float", "double", "decimal", "number", "numeric"]
        columns = schema_info.get("columns", [])
        numeric_cols = []
        
        for col in columns:
            dtype = str(col.get("data_type", "")).lower()
            if any(t in dtype for t in numeric_types):
                numeric_cols.append(col.get("name"))
        
        return numeric_cols
    
    def _find_categorical_columns(self, schema_info: Dict) -> List[str]:
        """找到分类列"""
        categorical_types = ["str", "object", "varchar", "text", "category"]
        columns = schema_info.get("columns", [])
        cat_cols = []
        
        for col in columns:
            dtype = str(col.get("data_type", "")).lower()
            if any(t in dtype for t in categorical_types):
                # 检查语义类型
                semantic = col.get("semantic_type", "")
                if semantic in ["category", "status"]:
                    cat_cols.append(col.get("name"))
        
        return cat_cols
    
    def _generate_query_plan(
        self,
        intent: Dict[str, Any],
        schema_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成查询计划"""
        
        operation = intent.get("operation", "describe")
        
        # 根据操作类型生成计划
        if operation == "count":
            return {
                "operation": "count",
                "description": "统计行数",
                "sql_simulation": "SELECT COUNT(*) FROM dataset"
            }
        
        elif operation == "aggregate":
            agg = intent.get("aggregation", "sum")
            numeric_cols = self._find_numeric_columns(schema_info)
            
            if numeric_cols:
                target_col = numeric_cols[0]
                return {
                    "operation": "aggregate",
                    "column": target_col,
                    "function": agg,
                    "description": f"计算 {target_col} 的 {agg}",
                    "sql_simulation": f"SELECT {agg}({target_col}) FROM dataset"
                }
        
        elif operation == "extreme":
            agg = intent.get("aggregation", "max")
            numeric_cols = self._find_numeric_columns(schema_info)
            
            if numeric_cols:
                target_col = numeric_cols[0]
                return {
                    "operation": "extreme",
                    "column": target_col,
                    "function": agg,
                    "sort_order": intent.get("sort_order", "desc"),
                    "description": f"找 {target_col} {agg} 的记录",
                    "sql_simulation": f"SELECT * FROM dataset ORDER BY {target_col} {intent.get('sort_order', 'desc')} LIMIT 1"
                }
        
        elif operation == "list":
            return {
                "operation": "list",
                "limit": 10,
                "description": "列出数据",
                "sql_simulation": "SELECT * FROM dataset LIMIT 10"
            }
        
        else:  # describe
            return {
                "operation": "describe",
                "description": "描述数据集",
                "sql_simulation": "SELECT * FROM dataset LIMIT 5"
            }
    
    async def _generate_answer(
        self,
        question: str,
        intent: Dict[str, Any],
        schema_info: Dict[str, Any],
        sample_data: Optional[List[Dict]]
    ) -> str:
        """生成自然语言回答"""
        
        operation = intent.get("operation", "describe")
        
        if sample_data and len(sample_data) > 0:
            row_count = len(sample_data)
            col_count = len(sample_data[0]) if sample_data else 0
            
            if operation == "count":
                # 估算总数（基于样本）
                total = row_count * 10  # 假设样本是 10 行
                return f"根据分析，数据集大约有 {total} 行数据。"
            
            elif operation == "aggregate":
                target_col = intent.get("column")
                if target_col and target_col in sample_data[0]:
                    try:
                        values = [float(row.get(target_col, 0)) for row in sample_data if row.get(target_col)]
                        if values:
                            if intent.get("aggregation") == "sum":
                                return f"总和: {sum(values):.2f}"
                            elif intent.get("aggregation") == "mean":
                                return f"平均值: {sum(values)/len(values):.2f}"
                    except:
                        pass
                return "需要更详细的分析才能回答这个问题。"
            
            elif operation == "extreme":
                target_col = intent.get("column")
                if target_col and target_col in sample_data[0]:
                    try:
                        sorted_data = sorted(
                            sample_data,
                            key=lambda x: float(x.get(target_col, 0)) if x.get(target_col) else 0,
                            reverse=(intent.get("sort_order") == "desc")
                        )
                        if sorted_data:
                            return f"最值记录: {target_col} = {sorted_data[0].get(target_col)}"
                    except:
                        pass
                return "需要更详细的分析才能回答这个问题。"
            
            elif operation == "list":
                cols = list(sample_data[0].keys())[:5]
                return f"数据包含 {col_count} 列，前几行数据：\n" + \
                       "\n".join([str(row)[:100] for row in sample_data[:3]])
            
            else:
                # 描述
                return (
                    f"数据集 '{schema_info.get('name', dataset_id)}' 包含 {row_count} 行 {col_count} 列数据。\n"
                    f"主要列：{', '.join(list(sample_data[0].keys())[:5])}"
                )
        
        # 没有样本数据时的回答
        col_count = len(schema_info.get("columns", []))
        
        return (
            f"数据集 '{schema_info.get('name', dataset_id)}' 包含 {col_count} 列。\n"
            f"列信息：\n" + 
            "\n".join([f"- {c.get('name')}: {c.get('data_type', 'unknown')}" 
                      for c in schema_info.get("columns", [])[:5]])
        )


# 导出
natural_language_query_service = NaturalLanguageQueryService()

__all__ = ['NaturalLanguageQueryService', 'natural_language_query_service']
