#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务分析服务 - 封装业务分析、质量分析、增强分析的核心逻辑

从旧工作流中提取的核心业务逻辑，供 Agent tools 和 dataset_service 直接调用
"""

from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

from ..tools.data_analyzer import DataAnalyzer
from ..tools.data_quality_analyzer import DataQualityAnalyzer
from ..llms import get_reasoning_llm
from ..schemas.data_quality import QualityAnalysisRequest


class BusinessAnalysisService:
    """业务分析服务 - 封装工业数据分析的核心逻辑"""
    
    def __init__(self):
        """初始化业务分析服务"""
        self.data_analyzer = DataAnalyzer()
        self.quality_analyzer = DataQualityAnalyzer()
        self._llm = None
    
    @property
    def llm(self):
        """获取LLM实例（延迟初始化）"""
        if self._llm is None:
            self._llm = get_reasoning_llm()
        return self._llm
    
    async def run_business_analysis(
        self,
        file_path: Path,
        dataset_name: str,
        user_requirements: str = ""
    ) -> Dict[str, Any]:
        """执行业务分析（设备识别、业务含义、控制关系）
        
        Args:
            file_path: 数据文件路径
            dataset_name: 数据集名称
            user_requirements: 用户需求描述
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            logger.info(f"开始业务分析: {dataset_name}")
            
            # 1. 加载数据
            self.data_analyzer.data = self.data_analyzer.load_data(file_path)
            basic_info = self.data_analyzer.get_basic_info()
            
            # 2. 识别设备列和时间列
            device_time_identification = await self._identify_device_time_columns(
                dataset_name, basic_info
            )
            
            # 3. 分析业务含义
            business_meaning_analysis = await self._analyze_business_meaning(
                dataset_name, basic_info, user_requirements
            )
            
            # 4. 分析控制关系
            control_relationships_analysis = await self._analyze_control_relationships(
                dataset_name, basic_info, business_meaning_analysis, user_requirements
            )
            
            result = {
                "data_info": basic_info,
                "device_time_identification": device_time_identification,
                "business_meaning_analysis": business_meaning_analysis,
                "control_relationships_analysis": control_relationships_analysis,
                "statistical_summary": self.data_analyzer.get_statistical_summary(),
                "errors": []
            }
            
            logger.info(f"业务分析完成: {dataset_name}")
            return result
            
        except Exception as e:
            logger.error(f"业务分析失败: {e}", exc_info=True)
            return {
                "errors": [str(e)],
                "data_info": {},
                "device_time_identification": "",
                "business_meaning_analysis": "",
                "control_relationships_analysis": ""
            }
    
    async def _identify_device_time_columns(
        self,
        dataset_name: str,
        basic_info: Dict[str, Any]
    ) -> str:
        """识别设备列和时间列"""
        try:
            columns_info = {}
            for col in basic_info.get("columns", []):
                try:
                    col_analysis = self.data_analyzer.get_column_analysis(col)
                    columns_info[col] = {
                        "dtype": col_analysis.get("dtype", "unknown"),
                        "unique_count": col_analysis.get("unique_count", 0),
                        "null_count": col_analysis.get("null_count", 0),
                        "sample_values": col_analysis.get("sample_values", [])[:5]
                    }
                except Exception as e:
                    logger.warning(f"获取列 {col} 信息失败: {e}")
                    columns_info[col] = {
                        "dtype": "unknown",
                        "unique_count": 0,
                        "null_count": 0,
                        "sample_values": []
                    }
            
            # 构建列信息字符串
            columns_info_str = ""
            for col_name, col_info in columns_info.items():
                columns_info_str += f"""
列名：{col_name}
- 数据类型：{col_info['dtype']}
- 唯一值数量：{col_info['unique_count']}
- 空值数量：{col_info['null_count']}
- 示例值：{col_info['sample_values']}
"""
            
            # 使用简化的提示词
            prompt = f"""请分析以下数据集，识别设备相关列和时间列。

数据集名称：{dataset_name}
总列数：{len(columns_info)}

列信息：
{columns_info_str}

请识别：
1. 设备ID列（如设备编号、设备名称等）
2. 时间列（如时间戳、日期等）

请以JSON格式返回结果：
{{
    "device_columns": ["列名1", "列名2"],
    "time_columns": ["列名1", "列名2"],
    "reasoning": "识别理由"
}}"""
            
            messages = [
                SystemMessage(content="你是一个专业的工业数据分析专家，擅长识别时间序列数据中的设备相关列和时间列。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析并格式化结果
            import json
            try:
                result = json.loads(response.content)
                return f"设备列: {', '.join(result.get('device_columns', []))}\n时间列: {', '.join(result.get('time_columns', []))}\n理由: {result.get('reasoning', '')}"
            except:
                return response.content
                
        except Exception as e:
            logger.error(f"识别设备列和时间列失败: {e}")
            return f"识别失败: {str(e)}"
    
    async def _analyze_business_meaning(
        self,
        dataset_name: str,
        basic_info: Dict[str, Any],
        user_requirements: str
    ) -> str:
        """分析业务含义"""
        try:
            columns_business_info = {}
            for col in basic_info.get("columns", []):
                try:
                    col_analysis = self.data_analyzer.get_column_analysis(col)
                    columns_business_info[col] = {
                        "dtype": col_analysis.get("dtype", "unknown"),
                        "unique_count": col_analysis.get("unique_count", 0),
                        "null_count": col_analysis.get("null_count", 0),
                        "sample_values": col_analysis.get("sample_values", [])[:10]
                    }
                except Exception as e:
                    logger.warning(f"获取列 {col} 分析信息失败: {e}")
                    columns_business_info[col] = {
                        "dtype": "unknown",
                        "unique_count": 0,
                        "null_count": 0,
                        "sample_values": []
                    }
            
            columns_business_info_str = ""
            for col_name, col_info in columns_business_info.items():
                columns_business_info_str += f"""
列名：{col_name}
- 数据类型：{col_info['dtype']}
- 唯一值数量：{col_info['unique_count']}
- 空值数量：{col_info['null_count']}
- 示例值：{col_info['sample_values']}
"""
            
            prompt = f"""请分析以下工业数据集的业务含义。

数据集名称：{dataset_name}
用户需求：{user_requirements or '无特殊要求'}

列信息：
{columns_business_info_str}

请分析每列的业务含义，包括：
1. 列的业务用途
2. 在工业过程中的作用
3. 与其他列的关系

请提供详细的分析报告。"""
            
            messages = [
                SystemMessage(content="你是一个资深的工业数据分析专家，具有丰富的制造业、能源、化工等行业经验，擅长理解工业数据的业务含义。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"业务含义分析失败: {e}")
            return f"分析失败: {str(e)}"
    
    async def _analyze_control_relationships(
        self,
        dataset_name: str,
        basic_info: Dict[str, Any],
        business_meaning_analysis: str,
        user_requirements: str
    ) -> str:
        """分析控制关系"""
        try:
            # 获取相关性分析
            correlation_analysis = self.data_analyzer.get_correlation_analysis()
            
            columns_info = {}
            for col in basic_info.get("columns", []):
                try:
                    col_analysis = self.data_analyzer.get_column_analysis(col)
                    columns_info[col] = col_analysis
                except Exception as e:
                    logger.warning(f"获取列 {col} 信息失败: {e}")
                    columns_info[col] = {
                        "dtype": "unknown",
                        "unique_count": 0,
                        "null_count": 0,
                        "sample_values": []
                    }
            
            columns_info_str = ""
            for col_name, col_info in columns_info.items():
                columns_info_str += f"""
- {col_name}: {col_info.get('dtype', 'unknown')} (唯一值: {col_info.get('unique_count', 0)})
"""
            
            prompt = f"""请分析以下工业数据集中列之间的控制原理和关系。

数据集名称：{dataset_name}
用户需求：{user_requirements or '无特殊要求'}

业务含义分析：
{business_meaning_analysis}

相关性分析：
{str(correlation_analysis)[:1000]}

列信息：
{columns_info_str}

请分析：
1. 控制变量和被控变量的关系
2. 控制逻辑和策略
3. 变量之间的因果关系

请提供详细的控制原理分析报告。"""
            
            messages = [
                SystemMessage(content="你是一个资深的工业自动化和过程控制专家，具有丰富的控制系统设计和优化经验，擅长分析工业过程中的控制原理和变量关系。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"控制关系分析失败: {e}")
            return f"分析失败: {str(e)}"
    
    async def run_quality_analysis(
        self,
        dataset_id: str,
        file_path: Path,
        user_requirements: str = ""
    ) -> Dict[str, Any]:
        """执行质量分析
        
        Args:
            dataset_id: 数据集ID
            file_path: 数据文件路径
            user_requirements: 用户需求描述
            
        Returns:
            Dict[str, Any]: 质量分析结果
        """
        try:
            logger.info(f"开始质量分析: {dataset_id}")
            
            # 加载数据
            self.quality_analyzer.load_data(file_path)
            
            # 自动检测列类型
            column_types = self.quality_analyzer.auto_detect_column_types()
            self.quality_analyzer.set_column_types(column_types)
            
            # 执行质量分析
            report = self.quality_analyzer.analyze_quality()
            
            # 生成质量报告
            quality_report = {
                "overall_score": report.get("overall_score", 0),
                "quality_level": report.get("quality_level", "unknown"),
                "completeness": report.get("completeness", {}).get("overall_score", 0),
                "accuracy": report.get("accuracy", {}).get("overall_score", 0),
                "consistency": report.get("consistency", {}).get("overall_score", 0),
                "timeliness": report.get("timeliness", {}).get("overall_score", 0),
                "key_issues": report.get("key_issues", []),
                "recommendations": report.get("recommendations", [])
            }
            
            logger.info(f"质量分析完成: {dataset_id}")
            return {
                "status": "completed",
                "report": quality_report,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"质量分析失败: {e}", exc_info=True)
            return {
                "status": "failed",
                "errors": [str(e)],
                "report": {}
            }
    
    async def run_enhanced_analysis(
        self,
        file_path: Path,
        dataset_name: str,
        user_requirements: str = ""
    ) -> Dict[str, Any]:
        """执行增强分析（领域识别+重要列识别）
        
        Args:
            file_path: 数据文件路径
            dataset_name: 数据集名称
            user_requirements: 用户需求描述
            
        Returns:
            Dict[str, Any]: 增强分析结果
        """
        try:
            logger.info(f"开始增强分析: {dataset_name}")
            
            # 1. 加载数据
            self.data_analyzer.data = self.data_analyzer.load_data(file_path)
            basic_info = self.data_analyzer.get_basic_info()
            
            # 2. 识别工业领域和业务类型
            domain_result = await self._identify_domain_and_type(
                dataset_name, basic_info
            )
            
            # 3. 识别重要列
            important_columns = await self._identify_important_columns(
                dataset_name, domain_result, basic_info
            )
            
            result = {
                "industrial_domain": domain_result.get("industrial_domain", {}),
                "business_data_types": domain_result.get("business_data_types", []),
                "domain_specific_insights": domain_result.get("domain_specific_insights", {}),
                "important_columns_analysis": important_columns,
                "errors": []
            }
            
            logger.info(f"增强分析完成: {dataset_name}")
            return result
            
        except Exception as e:
            logger.error(f"增强分析失败: {e}", exc_info=True)
            return {
                "errors": [str(e)],
                "industrial_domain": {},
                "business_data_types": [],
                "domain_specific_insights": {},
                "important_columns_analysis": {}
            }
    
    async def _identify_domain_and_type(
        self,
        dataset_name: str,
        basic_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """识别工业领域和业务类型"""
        try:
            columns_info = basic_info.get("columns", [])
            column_names = ", ".join(columns_info)
            column_types = str(basic_info.get("dtypes", {}))
            sample_data = str(basic_info.get("sample_data", {}))[:1000]
            
            prompt = f"""请识别以下数据集的工业领域和业务数据类型。

数据集名称：{dataset_name}
列名：{column_names}
列类型：{column_types}
样本数据：{sample_data}

请识别：
1. 工业领域（如：半导体、化工、能源、汽车、食品、医药等）
2. 业务数据类型（如：设备运行数据、生产数据、质量数据、日志数据等）

请以JSON格式返回：
{{
    "industrial_domain": {{
        "primary": "主要领域",
        "confidence": 0.9
    }},
    "business_data_types": [
        {{"type": "类型1", "confidence": 0.8}}
    ],
    "domain_specific_insights": {{}}
}}"""
            
            messages = [
                SystemMessage(content="你是一位资深的工业数据分析专家。请严格按照JSON格式输出结果，不要添加任何额外文字。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析JSON
            import json
            import re
            try:
                # 尝试直接解析
                result = json.loads(response.content)
            except:
                # 尝试提取JSON块
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    raise ValueError("无法解析JSON响应")
            
            return result
            
        except Exception as e:
            logger.error(f"领域识别失败: {e}")
            return {
                "industrial_domain": {"primary": "未知"},
                "business_data_types": [],
                "domain_specific_insights": {}
            }
    
    async def _identify_important_columns(
        self,
        dataset_name: str,
        domain_result: Dict[str, Any],
        basic_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """识别重要列"""
        try:
            industrial_domain = domain_result.get("industrial_domain", {}).get("primary", "未知")
            business_data_types = [t.get("type", "") for t in domain_result.get("business_data_types", [])]
            
            columns_info = []
            for col in basic_info.get("columns", []):
                try:
                    col_analysis = self.data_analyzer.get_column_analysis(col)
                    columns_info.append({
                        "name": col,
                        "dtype": col_analysis.get("dtype", "unknown"),
                        "unique_count": col_analysis.get("unique_count", 0),
                        "null_count": col_analysis.get("null_count", 0)
                    })
                except:
                    columns_info.append({
                        "name": col,
                        "dtype": "unknown",
                        "unique_count": 0,
                        "null_count": 0
                    })
            
            columns_info_str = "\n".join([
                f"- {col['name']}: type={col['dtype']}, nulls={col['null_count']}, unique={col['unique_count']}"
                for col in columns_info
            ])
            
            prompt = f"""请识别以下数据集中的重要列（关键观测量和控制变量）。

数据集名称：{dataset_name}
工业领域：{industrial_domain}
业务数据类型：{', '.join(business_data_types)}

列信息：
{columns_info_str}

请识别：
1. 关键观测量（需要监控的重要指标）
2. 控制变量（用于控制过程的变量）

请以JSON格式返回：
{{
    "key_measurement_variables": [
        {{"column_name": "列名", "reasoning": "理由"}}
    ],
    "control_variables": [
        {{"column_name": "列名", "reasoning": "理由"}}
    ]
}}"""
            
            messages = [
                SystemMessage(content="你是一位经验丰富的工业数据科学家。请严格按照JSON格式输出结果。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析JSON
            import json
            import re
            try:
                result = json.loads(response.content)
            except:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    raise ValueError("无法解析JSON响应")
            
            return result
            
        except Exception as e:
            logger.error(f"重要列识别失败: {e}")
            return {
                "key_measurement_variables": [],
                "control_variables": []
            }
