"""数据质量分析工作流"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid
from datetime import datetime
from loguru import logger

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from ..tools.data_quality_analyzer import DataQualityAnalyzer
from ..schemas.data_quality import (
    QualityAnalysisRequest, QualityAnalysisResponse, DataQualityReport,
    ColumnType
)
from langchain_openai import ChatOpenAI


class DataQualityState(TypedDict):
    """数据质量分析状态"""
    request: QualityAnalysisRequest
    file_path: Optional[Path]
    analyzer: Optional[DataQualityAnalyzer]
    column_types: Optional[Dict[str, ColumnType]]
    report: Optional[DataQualityReport]
    error_message: Optional[str]
    processing_time: Optional[float]
    messages: Annotated[List[Dict[str, Any]], add_messages]


class DataQualityWorkflow:
    """数据质量分析工作流"""
    
    def __init__(self, llm: ChatOpenAI):
        """初始化工作流"""
        self.llm = llm
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(DataQualityState)
        
        # 添加节点
        workflow.add_node("load_data", self._load_data)
        workflow.add_node("detect_column_types", self._detect_column_types)
        workflow.add_node("analyze_quality", self._analyze_quality)
        workflow.add_node("generate_insights", self._generate_insights)
        workflow.add_node("finalize_report", self._finalize_report)
        
        # 设置入口点
        workflow.set_entry_point("load_data")
        
        # 添加边
        workflow.add_edge("load_data", "detect_column_types")
        workflow.add_edge("detect_column_types", "analyze_quality")
        workflow.add_edge("analyze_quality", "generate_insights")
        workflow.add_edge("generate_insights", "finalize_report")
        workflow.add_edge("finalize_report", END)
        
        return workflow.compile()
    
    def _load_data(self, state: DataQualityState) -> DataQualityState:
        """加载数据"""
        try:
            logger.info(f"开始加载数据集: {state['request'].dataset_id}")
            
            # 创建数据质量分析器
            analyzer = DataQualityAnalyzer()
            
            # 从数据集服务获取文件路径
            from ..core.dataset_repository import DatasetRepository
            from ..config.settings import get_settings
            
            settings = get_settings()
            repository = DatasetRepository(
                metadata_dir=Path(settings.metadata_dir)
            )
            
            dataset = repository.get_by_id(state['request'].dataset_id)
            if not dataset:
                raise ValueError(f"数据集不存在: {state['request'].dataset_id}")
            
            file_path = Path(dataset.file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"数据文件不存在: {file_path}")
            
            # 加载数据
            analyzer.load_data(file_path)
            
            state["analyzer"] = analyzer
            state["file_path"] = file_path
            state["messages"].append({
                "role": "system",
                "content": f"成功加载数据文件: {file_path}, 数据形状: {analyzer.data.shape}"
            })
            
            logger.info(f"数据加载完成: {analyzer.data.shape}")
            
        except Exception as e:
            error_msg = f"数据加载失败: {str(e)}"
            logger.error(error_msg)
            state["error_message"] = error_msg
            state["messages"].append({
                "role": "system",
                "content": error_msg
            })
        
        return state
    
    def _detect_column_types(self, state: DataQualityState) -> DataQualityState:
        """检测列类型"""
        try:
            if state.get("error_message"):
                return state
            
            analyzer = state["analyzer"]
            request = state["request"]
            
            logger.info("开始检测列类型")
            
            # 如果用户指定了列类型，使用用户指定的
            if request.column_types:
                analyzer.set_column_types(request.column_types)
                column_types = request.column_types
                state["messages"].append({
                    "role": "system",
                    "content": f"使用用户指定的列类型: {column_types}"
                })
            else:
                # 自动检测列类型
                column_types = analyzer.auto_detect_column_types()
                state["messages"].append({
                    "role": "system",
                    "content": f"自动检测到的列类型: {column_types}"
                })
            
            state["column_types"] = column_types
            
            # 使用LLM优化列类型检测
            if self.llm:
                optimized_types = self._optimize_column_types_with_llm(
                    analyzer.data, column_types, request.user_requirements
                )
                if optimized_types:
                    analyzer.set_column_types(optimized_types)
                    state["column_types"] = optimized_types
                    state["messages"].append({
                        "role": "assistant",
                        "content": f"LLM优化后的列类型: {optimized_types}"
                    })
            
            logger.info(f"列类型检测完成: {state['column_types']}")
            
        except Exception as e:
            error_msg = f"列类型检测失败: {str(e)}"
            logger.error(error_msg)
            state["error_message"] = error_msg
            state["messages"].append({
                "role": "system",
                "content": error_msg
            })
        
        return state
    
    def _analyze_quality(self, state: DataQualityState) -> DataQualityState:
        """分析数据质量"""
        try:
            if state.get("error_message"):
                return state
            
            analyzer = state["analyzer"]
            request = state["request"]
            
            logger.info("开始数据质量分析")
            
            start_time = datetime.now()
            
            # 生成数据质量报告
            analysis_id = str(uuid.uuid4())
            report = analyzer.generate_quality_report(
                dataset_id=request.dataset_id,
                analysis_id=analysis_id
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            state["report"] = report
            state["processing_time"] = processing_time
            state["messages"].append({
                "role": "system",
                "content": f"数据质量分析完成，整体得分: {report.overall_score:.1f}, 质量等级: {report.quality_level.value}"
            })
            
            logger.info(f"数据质量分析完成，处理时间: {processing_time:.2f}秒")
            
        except Exception as e:
            error_msg = f"数据质量分析失败: {str(e)}"
            logger.error(error_msg)
            state["error_message"] = error_msg
            state["messages"].append({
                "role": "system",
                "content": error_msg
            })
        
        return state
    
    def _generate_insights(self, state: DataQualityState) -> DataQualityState:
        """生成质量洞察"""
        try:
            if state.get("error_message"):
                return state
            
            report = state["report"]
            request = state["request"]
            
            logger.info("开始生成质量洞察")
            
            if self.llm:
                # 使用LLM生成深度洞察
                insights = self._generate_quality_insights_with_llm(report, request.user_requirements)
                if insights:
                    # 更新报告中的洞察和建议
                    enhanced_recommendations = report.recommendations + insights.get("recommendations", [])
                    enhanced_key_issues = report.key_issues + insights.get("key_issues", [])
                    
                    # 创建增强的报告
                    enhanced_report = DataQualityReport(
                        dataset_id=report.dataset_id,
                        analysis_id=report.analysis_id,
                        created_at=report.created_at,
                        time_columns=report.time_columns,
                        parameter_columns=report.parameter_columns,
                        category_columns=report.category_columns,
                        overall_score=report.overall_score,
                        quality_level=report.quality_level,
                        summary=report.summary,
                        key_issues=enhanced_key_issues,
                        recommendations=list(set(enhanced_recommendations)),  # 去重
                        total_columns=report.total_columns,
                        analyzed_columns=report.analyzed_columns,
                        high_quality_columns=report.high_quality_columns,
                        low_quality_columns=report.low_quality_columns
                    )
                    
                    state["report"] = enhanced_report
                    state["messages"].append({
                        "role": "assistant",
                        "content": f"生成了 {len(insights.get('recommendations', []))} 条额外建议和 {len(insights.get('key_issues', []))} 个关键洞察"
                    })
            
            logger.info("质量洞察生成完成")
            
        except Exception as e:
            error_msg = f"质量洞察生成失败: {str(e)}"
            logger.error(error_msg)
            # 洞察生成失败不影响主流程，只记录错误
            state["messages"].append({
                "role": "system",
                "content": error_msg
            })
        
        return state
    
    def _finalize_report(self, state: DataQualityState) -> DataQualityState:
        """完成报告"""
        try:
            if state.get("error_message"):
                return state
            
            report = state["report"]
            
            logger.info("完成数据质量分析报告")
            
            # 添加最终摘要消息
            summary_message = f"""
数据质量分析完成！

📊 整体评分: {report.overall_score:.1f}/100 ({report.quality_level.value})
📈 分析列数: {report.analyzed_columns}/{report.total_columns}
✅ 高质量列: {report.high_quality_columns}
⚠️ 低质量列: {report.low_quality_columns}

🔍 列类型分布:
- 时间列: {len(report.time_columns)}
- 参数列: {len(report.parameter_columns)}  
- 类目列: {len(report.category_columns)}

💡 主要建议: {len(report.recommendations)} 条
⚠️ 关键问题: {len(report.key_issues)} 个
"""
            
            state["messages"].append({
                "role": "assistant",
                "content": summary_message
            })
            
            logger.info(f"数据质量分析工作流完成，整体得分: {report.overall_score:.1f}")
            
        except Exception as e:
            error_msg = f"报告完成失败: {str(e)}"
            logger.error(error_msg)
            state["error_message"] = error_msg
            state["messages"].append({
                "role": "system",
                "content": error_msg
            })
        
        return state
    
    def _optimize_column_types_with_llm(self, data, detected_types: Dict[str, ColumnType], 
                                       user_requirements: Optional[str]) -> Optional[Dict[str, ColumnType]]:
        """使用LLM优化列类型检测"""
        try:
            # 构建提示词
            columns_info = []
            for col in data.columns[:10]:  # 只分析前10列避免token过多
                sample_values = data[col].dropna().head(5).tolist()
                columns_info.append({
                    "name": col,
                    "detected_type": detected_types.get(col, "unknown").value if col in detected_types else "unknown",
                    "sample_values": sample_values,
                    "dtype": str(data[col].dtype)
                })
            
            prompt = f"""
请分析以下数据列的类型，并判断自动检测的结果是否正确。

列信息:
{columns_info}

用户要求: {user_requirements or "无特殊要求"}

可选的列类型:
- time: 时间列（日期、时间戳等）
- parameter: 参数列（数值型测量值、指标等）
- category: 类目列（分类、标签等）

请严格按照以下格式返回JSON，只包含需要修正的列：

```json
{{"column_name": "type"}}
```

如果自动检测结果都正确，返回：

```json
{{}}
```

注意：请只返回JSON格式，不要添加其他说明文字。
"""
            
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content="你是一个专业的数据分析师，请分析数据列类型。"),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_content = response.content
            
            # 解析LLM响应
            from ..utils.json_utils import repair_json_output
            import json
            
            try:
                # 使用json_utils修复和解析JSON
                repaired_json = repair_json_output(response_content)
                optimized_types = json.loads(repaired_json)
                
                if optimized_types and isinstance(optimized_types, dict):
                    # 合并优化结果
                    final_types = detected_types.copy()
                    for col, type_str in optimized_types.items():
                        if col in final_types and type_str in ["time", "parameter", "category"]:
                            final_types[col] = ColumnType(type_str)
                    return final_types
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"LLM返回的JSON格式无效，使用原始检测结果。响应内容: {response_content[:200]}...")
            
        except Exception as e:
            logger.warning(f"LLM列类型优化失败: {e}")
        
        return None
    
    def _generate_quality_insights_with_llm(self, report: DataQualityReport, 
                                          user_requirements: Optional[str]) -> Optional[Dict[str, Any]]:
        """使用LLM生成质量洞察"""
        try:
            # 构建报告摘要
            report_summary = {
                "overall_score": report.overall_score,
                "quality_level": report.quality_level.value,
                "column_breakdown": report.summary["column_breakdown"],
                "quality_distribution": report.summary["quality_distribution"],
                "key_issues": report.key_issues[:5],  # 只包含前5个问题
                "recommendations": report.recommendations[:5]  # 只包含前5个建议
            }
            
            prompt = f"""
基于以下数据质量分析报告，请提供深度洞察和改进建议：

报告摘要:
{report_summary}

用户要求: {user_requirements or "无特殊要求"}

请从以下角度分析：
1. 数据质量的整体评估
2. 主要质量问题的根本原因
3. 优先级改进建议
4. 潜在的业务影响
5. 数据治理建议

请严格按照以下格式返回JSON：

```json
{{
    "key_insights": ["洞察1", "洞察2"],
    "root_causes": ["原因1", "原因2"],
    "priority_actions": ["行动1", "行动2"],
    "business_impact": "业务影响描述",
    "governance_recommendations": ["治理建议1", "治理建议2"]
}}
```

注意：请只返回JSON格式，不要添加其他说明文字。
"""
            
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content="你是一个专业的数据质量分析师，请提供深度洞察。"),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_content = response.content
            
            # 解析LLM响应
            from ..utils.json_utils import repair_json_output
            import json
            
            try:
                # 使用json_utils修复和解析JSON
                repaired_json = repair_json_output(response_content)
                insights = json.loads(repaired_json)
                
                if insights and isinstance(insights, dict):
                    # 转换为报告格式
                    enhanced_insights = {
                        "key_issues": insights.get("key_insights", []) + insights.get("root_causes", []),
                        "recommendations": (insights.get("priority_actions", []) + 
                                          insights.get("governance_recommendations", []))
                    }
                    
                    return enhanced_insights
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"LLM返回的洞察JSON格式无效。响应内容: {response_content[:200]}...")
            
        except Exception as e:
            logger.warning(f"LLM洞察生成失败: {e}")
        
        return None
    
    async def run_analysis(self, request: QualityAnalysisRequest) -> QualityAnalysisResponse:
        """运行数据质量分析"""
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            logger.info(f"开始数据质量分析: {request_id}")
            
            # 初始化状态
            initial_state = DataQualityState(
                request=request,
                file_path=None,
                analyzer=None,
                column_types=None,
                report=None,
                error_message=None,
                processing_time=None,
                messages=[]
            )
            
            # 运行工作流
            final_state = await self.graph.ainvoke(initial_state)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # 构建响应
            if final_state.get("error_message"):
                return QualityAnalysisResponse(
                    request_id=request_id,
                    status="failed",
                    report=None,
                    error_message=final_state["error_message"],
                    processing_time=processing_time
                )
            else:
                return QualityAnalysisResponse(
                    request_id=request_id,
                    status="completed",
                    report=final_state["report"],
                    error_message=None,
                    processing_time=processing_time
                )
                
        except Exception as e:
            error_msg = f"数据质量分析工作流失败: {str(e)}"
            logger.error(error_msg)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return QualityAnalysisResponse(
                request_id=request_id,
                status="failed",
                report=None,
                error_message=error_msg,
                processing_time=processing_time
            ) 