#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强分析节点模块

提供新的分析功能:
1. 工业领域和业务数据类型识别
2. 重要列识别(关键观测量和控制量)
3. 数据血缘关系管理
"""

from typing import Dict, Any, List
from pathlib import Path
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

from ..state import AnalysisState
from ..tools.data_analyzer import DataAnalyzer
from ..tools.data_quality_analyzer import DataQualityAnalyzer
from ..llms import get_basic_llm
from ..schemas.dataset import DatasetMetadata, ColumnMetadata
from ..prompts.loader import prompt_loader


class EnhancedAnalysisNodes:
    """增强分析节点类"""

    def __init__(self):
        """初始化增强分析节点"""
        self.data_analyzer = DataAnalyzer()
        self.quality_analyzer = DataQualityAnalyzer()
        self._llm = None
        logger.info("增强分析节点初始化完成")

    @property
    def llm(self):
        """获取LLM实例（延迟初始化）"""
        if self._llm is None:
            self._llm = get_basic_llm()
        return self._llm

    def identify_domain_and_type_node(self, state: AnalysisState) -> AnalysisState:
        """识别工业领域和业务数据类型节点

        Args:
            state: 当前状态

        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始识别工业领域和业务数据类型")

            # 获取数据基本信息
            data_info = state.get("data_info", {})
            columns_info = data_info.get("columns", [])
            basic_stats = state.get("basic_analysis", {})

            # 准备提示词参数
            dataset_name = state.get("dataset_name", "未知数据集")
            column_names = ", ".join(columns_info)
            column_types = str(data_info.get("dtypes", {}))
            sample_data = str(data_info.get("sample_data", {}))[:1000]  # 限制长度
            statistics = str(basic_stats)[:2000]  # 限制长度

            # 加载并格式化提示词
            try:
                template = prompt_loader.get_prompt_template("domain_identification")
                prompt = template.format(
                    dataset_name=dataset_name,
                    column_names=column_names,
                    column_types=column_types,
                    sample_data=sample_data,
                    statistics=statistics
                )
            except Exception as e:
                logger.warning(f"加载提示词模板失败: {e}，使用备用提示词")
                prompt = self._get_fallback_domain_prompt(
                    dataset_name, column_names, column_types, sample_data, statistics
                )

            # 调用LLM
            response = self.llm.invoke([
                SystemMessage(content="你是一位资深的工业数据分析专家。请严格按照JSON格式输出结果，不要添加任何额外文字。"),
                HumanMessage(content=prompt)
            ])

            # 解析结果
            result = self._parse_json_response(response.content)

            # 更新状态
            state["industrial_domain"] = result.get("industrial_domain", {})
            state["business_data_types"] = result.get("business_data_types", [])
            state["domain_specific_insights"] = result.get("domain_specific_insights", {})
            state["completed_steps"].append("identify_domain_and_type")

            logger.info(f"领域识别完成: {result.get('industrial_domain', {}).get('primary', '未知')}")
            logger.info(f"业务类型: {[t.get('type') for t in result.get('business_data_types', [])]}")

        except Exception as e:
            error_msg = f"领域识别失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)

        return state

    def identify_important_columns_node(self, state: AnalysisState) -> AnalysisState:
        """识别重要列节点（关键观测量和控制量）

        Args:
            state: 当前状态

        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始识别重要列")

            # 获取数据信息
            data_info = state.get("data_info", {})
            dataset_name = state.get("dataset_name", "未知数据集")
            industrial_domain = state.get("industrial_domain", {}).get("primary", "未知")
            business_data_types = [t.get("type", "") for t in state.get("business_data_types", [])]

            # 获取列详细信息
            columns_info = self._prepare_columns_info(data_info)

            # 获取相关性分析
            correlation_matrix = state.get("correlation_analysis", {})

            # 获取统计摘要
            statistical_summary = state.get("basic_analysis", "")

            # 加载并格式化提示词
            try:
                template = prompt_loader.get_prompt_template("important_columns_identification")
                prompt = template.format(
                    dataset_name=dataset_name,
                    industrial_domain=industrial_domain,
                    business_data_types=", ".join(business_data_types),
                    columns_info=columns_info,
                    correlation_matrix=str(correlation_matrix)[:1500],
                    statistical_summary=str(statistical_summary)[:1500]
                )
            except Exception as e:
                logger.warning(f"加载提示词模板失败: {e}，使用备用提示词")
                prompt = self._get_fallback_columns_prompt(
                    dataset_name, industrial_domain, business_data_types,
                    columns_info, correlation_matrix, statistical_summary
                )

            # 调用LLM
            response = self.llm.invoke([
                SystemMessage(content="你是一位经验丰富的工业数据科学家。请严格按照JSON格式输出结果。"),
                HumanMessage(content=prompt)
            ])

            # 解析结果
            result = self._parse_json_response(response.content)

            # 更新状态
            state["important_columns_analysis"] = result
            state["completed_steps"].append("identify_important_columns")

            # 记录关键发现
            key_measurements = result.get("key_measurement_variables", [])
            control_vars = result.get("control_variables", [])

            logger.info(f"识别到 {len(key_measurements)} 个关键观测量")
            logger.info(f"识别到 {len(control_vars)} 个控制量")

        except Exception as e:
            error_msg = f"重要列识别失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)

        return state

    def update_metadata_with_enhanced_info_node(self, state: AnalysisState) -> AnalysisState:
        """使用增强分析信息更新元数据节点

        Args:
            state: 当前状态

        Returns:
            AnalysisState: 更新后的状态
        """
        try:
            logger.info("开始更新元数据")

            # 获取现有元数据
            metadata: DatasetMetadata = state.get("metadata")
            if not metadata:
                logger.warning("未找到元数据，跳过更新")
                return state

            # 更新工业领域和业务类型信息
            metadata.industrial_domain = state.get("industrial_domain")
            metadata.business_data_types = state.get("business_data_types")
            metadata.domain_specific_insights = state.get("domain_specific_insights")

            # 更新重要列信息
            important_columns_analysis = state.get("important_columns_analysis", {})
            metadata.important_columns_analysis = important_columns_analysis

            # 更新列的重要性和类型标记
            self._update_column_metadata(metadata, important_columns_analysis)

            # 更新industry字段（向后兼容）
            if metadata.industrial_domain:
                metadata.industry = metadata.industrial_domain.get("primary", metadata.industry)

            # 更新状态
            state["metadata"] = metadata
            state["completed_steps"].append("update_metadata_enhanced")

            logger.info("元数据更新完成")

        except Exception as e:
            error_msg = f"元数据更新失败: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)

        return state

    def _prepare_columns_info(self, data_info: Dict) -> str:
        """准备列信息字符串

        Args:
            data_info: 数据信息字典

        Returns:
            str: 格式化的列信息
        """
        columns = data_info.get("columns", [])
        dtypes = data_info.get("dtypes", {})
        null_counts = data_info.get("null_counts", {})
        unique_counts = data_info.get("unique_counts", {})

        info_lines = []
        for col in columns:
            info_lines.append(
                f"- {col}: type={dtypes.get(col, 'unknown')}, "
                f"nulls={null_counts.get(col, 0)}, "
                f"unique={unique_counts.get(col, 0)}"
            )

        return "\n".join(info_lines)

    def _update_column_metadata(
        self,
        metadata: DatasetMetadata,
        important_columns_analysis: Dict
    ) -> None:
        """更新列元数据的重要性和类型标记

        Args:
            metadata: 数据集元数据
            important_columns_analysis: 重要列分析结果
        """
        # 提取关键观测量和控制量列表
        key_measurements = important_columns_analysis.get("key_measurement_variables", [])
        control_vars = important_columns_analysis.get("control_variables", [])

        # 构建映射字典
        key_measurement_scores = {
            m["column_name"]: m["importance_score"]
            for m in key_measurements
        }
        control_var_names = {c["column_name"] for c in control_vars}

        # 更新列元数据
        for col in metadata.columns:
            # 更新关键观测量标记
            if col.name in key_measurement_scores:
                col.is_key_measurement = True
                col.importance_score = key_measurement_scores[col.name]

            # 更新控制量标记
            if col.name in control_var_names:
                col.is_control_variable = True
                if col.importance_score == 0.0:
                    # 如果没有重要性评分，从控制量信息中获取
                    for cv in control_vars:
                        if cv["column_name"] == col.name:
                            col.importance_score = cv.get("importance_score", 0.7)
                            break

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """解析LLM返回的JSON响应

        Args:
            response_text: LLM返回的文本

        Returns:
            Dict: 解析后的字典
        """
        import json
        import re

        # 尝试提取JSON部分
        json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # 尝试直接解析
            json_text = response_text.strip()

        # 解析JSON
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始文本: {response_text[:500]}")
            return {}

    def _get_fallback_domain_prompt(
        self,
        dataset_name: str,
        column_names: str,
        column_types: str,
        sample_data: str,
        statistics: str
    ) -> str:
        """备用领域识别提示词"""
        return f"""
请分析数据集 "{dataset_name}" 的工业领域和业务数据类型。

列名: {column_names}
数据类型: {column_types}
样本数据: {sample_data}
统计信息: {statistics}

请从以下领域中选择：半导体、化工、能源、汽车、食品、医药、钢铁、纺织、电子制造、通用制造
业务类型：设备运行数据、生产数据、质量检测数据、设备日志、维护记录、工艺参数、能源消耗、环境监测

请严格按照JSON格式输出。
"""

    def _get_fallback_columns_prompt(
        self,
        dataset_name: str,
        industrial_domain: str,
        business_data_types: List[str],
        columns_info: str,
        correlation_matrix: Any,
        statistical_summary: Any
    ) -> str:
        """备用重要列识别提示词"""
        return f"""
请分析数据集 "{dataset_name}" 中的重要列。

领域: {industrial_domain}
业务类型: {', '.join(business_data_types)}
列信息:
{columns_info}

请识别:
1. 关键观测量（反映系统状态的核心指标）
2. 控制量（可调节的参数）

请严格按照JSON格式输出。
"""
