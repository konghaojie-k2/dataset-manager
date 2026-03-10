#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Native 功能集成示例

展示如何使用增强语义元数据服务
"""

import asyncio
import pandas as pd
from pathlib import Path

from backend.src.core.enhanced_metadata_service import EnhancedMetadataService
from backend.src.core.nl_query_service import NaturalLanguageQueryService


async def demo_enhanced_metadata():
    """演示增强元数据服务"""
    
    # 创建示例数据
    data = {
        'user_id': [1, 2, 3, 4, 5],
        'user_name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 28, 32],
        'salary': [5000, 6000, 7000, 5500, 6500],
        'department': ['Sales', 'Engineer', 'Sales', 'HR', 'Engineer'],
        'created_at': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        'is_active': [True, True, False, True, True]
    }
    df = pd.DataFrame(data)
    
    # 初始化服务
    metadata_service = EnhancedMetadataService()
    
    # 分析数据集
    result = await metadata_service.analyze_dataset(
        dataset_id="demo_dataset",
        dataframe=df,
        sample_size=1000
    )
    
    print("=" * 50)
    print("增强语义元数据示例")
    print("=" * 50)
    print(f"\n数据集: {result['dataset_id']}")
    print(f"行数: {result['total_rows']}")
    print(f"列数: {result['total_columns']}")
    
    print("\n字段语义:")
    for col in result['column_semantics'][:3]:
        print(f"  - {col['name']}: {col['semantic_type']} - {col['business_description']}")
    
    print("\n质量评分:")
    quality = result['quality_score']
    print(f"  综合评分: {quality['overall_score']}")
    print(f"  完整性: {quality['completeness']}%")
    print(f"  唯一性: {quality['uniqueness']}%")
    
    print("\n数据理解:")
    understanding = result['data_understanding']
    print(f"  摘要: {understanding['summary']}")
    print(f"  建议用途: {', '.join(understanding['suggested_uses'])}")
    
    print("\nAgent 可查询:")
    agent_q = result['agent_queryable']
    print(f"  快速摘要: {agent_q['quick_summary']}")
    print(f"  关键字段: {[f['name'] for f in agent_q['key_fields']]}")
    
    return result


async def demo_nl_query():
    """演示自然语言查询"""
    
    # 示例结构信息
    schema_info = {
        "dataset_id": "demo",
        "name": "用户数据",
        "columns": [
            {"name": "user_id", "data_type": "int", "semantic_type": "identifier"},
            {"name": "user_name", "data_type": "str", "semantic_type": "name"},
            {"name": "age", "data_type": "int", "semantic_type": "quantity"},
            {"name": "salary", "data_type": "float", "semantic_type": "currency"},
            {"name": "department", "data_type": "str", "semantic_type": "category"},
        ]
    }
    
    sample_data = [
        {"user_id": 1, "user_name": "Alice", "age": 25, "salary": 5000, "department": "Sales"},
        {"user_id": 2, "user_name": "Bob", "age": 30, "salary": 6000, "department": "Engineer"},
        {"user_id": 3, "user_name": "Charlie", "age": 35, "salary": 7000, "department": "Sales"},
    ]
    
    # 初始化服务
    nl_service = NaturalLanguageQueryService()
    
    # 测试不同类型的问题
    questions = [
        "数据有多少行？",
        "平均薪资是多少？",
        "列出所有数据"
    ]
    
    print("\n" + "=" * 50)
    print("自然语言查询示例")
    print("=" * 50)
    
    for question in questions:
        result = await nl_service.query(
            dataset_id="demo",
            question=question,
            schema_info=schema_info,
            sample_data=sample_data
        )
        
        print(f"\n问题: {question}")
        print(f"回答: {result['answer']}")
        print(f"操作类型: {result['intent']['operation']}")


async def main():
    """主函数"""
    print("\n🚀 AI-Native 数据集管理功能演示\n")
    
    # 演示增强元数据
    await demo_enhanced_metadata()
    
    # 演示自然语言查询
    await demo_nl_query()
    
    print("\n" + "=" * 50)
    print("演示完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
