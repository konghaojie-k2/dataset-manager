#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""元数据Schema发现器 - 暴露完整元数据结构给LLM"""

from typing import Dict, List, Any
from loguru import logger


class MetadataSchemaDiscovery:
    """元数据Schema发现器

    自动发现并暴露DatasetMetadata的所有可过滤字段
    """

    def __init__(self):
        """初始化发现器"""
        self._field_schema = self._build_field_schema()
        logger.info(f"元数据Schema发现器初始化完成，共{len(self._field_schema)}个可过滤字段")

    def get_filterable_fields(self) -> Dict[str, Dict[str, Any]]:
        """获取所有可过滤字段的Schema

        Returns:
            Dict: 字段Schema字典
            {
                "industry": {
                    "type": "string",
                    "path": "industry",
                    "description": "行业领域",
                    "examples": ["semiconductor", "chemical"]
                },
                "quality_analysis_results.overall_score": {
                    "type": "float",
                    "path": "quality_analysis_results.overall_score",
                    "description": "质量评分 (0-100)",
                    "examples": [85.5, 92.0]
                }
            }
        """
        return self._field_schema

    def _build_field_schema(self) -> Dict[str, Dict[str, Any]]:
        """构建字段Schema

        通过分析DatasetMetadata的结构，自动生成可过滤字段的清单
        """
        schema = {}

        # 基本信息
        basic_fields = {
            "name": {"type": "string", "description": "数据集名称"},
            "description": {"type": "string", "description": "数据集描述"},
            "industry": {"type": "string", "description": "行业领域",
                         "examples": ["semiconductor", "chemical", "energy", "manufacturing"]},
            "tags": {"type": "array", "description": "标签列表"},
            "file_size": {"type": "integer", "description": "文件大小(字节)"},
            "upload_time": {"type": "datetime", "description": "上传时间"},
            "processing_status": {"type": "string", "description": "处理状态",
                                  "examples": ["uploaded", "business_analyzing", "business_completed",
                                              "quality_analyzing", "quality_completed"]},
            "metadata_extracted": {"type": "boolean", "description": "元数据是否已提取"},
        }

        # 版本控制字段
        version_fields = {
            "version": {"type": "string", "description": "版本号"},
            "version_type": {"type": "string", "description": "版本类型",
                             "examples": ["original", "updated", "duplicate"]},
            "parent_version_id": {"type": "string", "description": "父版本ID"},
            "is_derived_data": {"type": "boolean", "description": "是否为派生数据"},
            "transformation_type": {"type": "string", "description": "转换类型",
                                    "examples": ["filter", "aggregate", "join", "derive", "feature_engineering"]},
            "source_dataset_ids": {"type": "array", "description": "源数据集ID列表"},
        }

        # 数据基本信息
        data_info_fields = {
            "sampling_rate": {"type": "string", "description": "采样率"},
            "analysis_domains": {"type": "array", "description": "分析领域"},
            "applicable_algorithms": {"type": "array", "description": "适用算法"},
        }

        # 质量指标（嵌套）
        quality_fields = {
            "quality_metrics.quality_score": {"type": "float", "description": "质量评分 (0-100)"},
            "quality_metrics.missing_value_ratio": {"type": "float", "description": "缺失值比例 (0-1)"},
            "quality_metrics.duplicate_rows": {"type": "integer", "description": "重复行数"},
            "quality_metrics.data_completeness": {"type": "float", "description": "数据完整性 (0-1)"},
            "quality_analysis_results.overall_score": {"type": "float", "description": "质量评分 (0-100)"},
            "quality_analysis_results.quality_level": {"type": "string", "description": "质量等级",
                                                        "examples": ["excellent", "good", "fair", "poor"]},
        }

        # 业务分析（嵌套）
        business_fields = {
            "industrial_domain.primary": {"type": "string", "description": "主要工业领域"},
            "business_data_types": {"type": "array", "description": "业务数据类型列表"},
        }

        # 列信息（通过数量过滤）
        column_info_fields = {
            "columns.count": {"type": "integer", "description": "列数量"},
        }

        # 合并所有字段
        schema.update(basic_fields)
        schema.update(version_fields)
        schema.update(data_info_fields)
        schema.update(quality_fields)
        schema.update(business_fields)
        schema.update(column_info_fields)

        return schema

    def format_schema_for_llm(self) -> str:
        """格式化Schema为LLM可读的文本

        Returns:
            str: 格式化的字段描述
        """
        schema = self.get_filterable_fields()

        lines = []
        for field_path, field_def in schema.items():
            desc = field_def["description"]
            type_info = field_def["type"]

            # 添加示例
            examples = ""
            if "examples" in field_def:
                examples = f" (例: {', '.join(str(e) for e in field_def['examples'])})"

            lines.append(f"- **{field_path}** ({type_info}): {desc}{examples}")

        return "\n".join(lines)

    def get_field_examples(self) -> Dict[str, Any]:
        """获取字段示例值，用于表单预填

        Returns:
            Dict: 字段示例值
        """
        return {
            "industry": ["semiconductor", "chemical", "energy", "manufacturing"],
            "processing_status": ["uploaded", "business_completed", "quality_completed"],
            "version_type": ["original", "updated", "duplicate"],
            "transformation_type": ["filter", "aggregate", "join", "derive", "feature_engineering"],
            "quality_analysis_results.quality_level": ["excellent", "good", "fair", "poor"],
        }
