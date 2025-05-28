#!/usr/bin/env python3
"""
分析报告管理器

负责将工业数据分析结果保存为Markdown文件，并提供文件管理功能
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from ..config import get_settings


class ReportManager:
    """分析报告管理器"""
    
    def __init__(self):
        """初始化报告管理器"""
        self.settings = get_settings()
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        self.industrial_dir = self.reports_dir / "industrial"
        self.general_dir = self.reports_dir / "general"
        self.exports_dir = self.reports_dir / "exports"
        
        for dir_path in [self.industrial_dir, self.general_dir, self.exports_dir]:
            dir_path.mkdir(exist_ok=True)
        
        logger.info(f"报告管理器初始化完成，报告目录: {self.reports_dir}")
    
    def save_industrial_analysis_report(
        self, 
        dataset_id: str, 
        dataset_name: str,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Path]:
        """保存工业数据分析报告
        
        Args:
            dataset_id: 数据集ID
            dataset_name: 数据集名称
            analysis_results: 分析结果
            
        Returns:
            Dict[str, Path]: 保存的文件路径字典
        """
        try:
            logger.info(f"开始保存工业分析报告: {dataset_name}")
            
            # 创建数据集专用目录
            dataset_dir = self.industrial_dir / f"{dataset_id}_{self._sanitize_filename(dataset_name)}"
            dataset_dir.mkdir(exist_ok=True)
            
            saved_files = {}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. 保存设备时间列识别结果
            if analysis_results.get("device_time_identification"):
                device_file = dataset_dir / f"01_设备时间列识别_{timestamp}.md"
                self._save_markdown_file(
                    device_file,
                    "设备列和时间列识别结果",
                    analysis_results["device_time_identification"],
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                        "analysis_type": "device_time_identification",
                        "generated_at": datetime.now().isoformat()
                    }
                )
                saved_files["device_time_identification"] = device_file
            
            # 2. 保存业务含义分析结果
            if analysis_results.get("business_meaning_analysis"):
                business_file = dataset_dir / f"02_业务含义分析_{timestamp}.md"
                self._save_markdown_file(
                    business_file,
                    "业务含义分析结果",
                    analysis_results["business_meaning_analysis"],
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                        "analysis_type": "business_meaning_analysis",
                        "generated_at": datetime.now().isoformat()
                    }
                )
                saved_files["business_meaning_analysis"] = business_file
            
            # 3. 保存控制原理分析结果
            if analysis_results.get("control_relationships_analysis"):
                control_file = dataset_dir / f"03_控制原理分析_{timestamp}.md"
                self._save_markdown_file(
                    control_file,
                    "控制原理分析结果",
                    analysis_results["control_relationships_analysis"],
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                        "analysis_type": "control_relationships_analysis",
                        "generated_at": datetime.now().isoformat()
                    }
                )
                saved_files["control_relationships_analysis"] = control_file
            
            # 4. 生成综合报告
            summary_file = dataset_dir / f"00_综合分析报告_{timestamp}.md"
            self._generate_comprehensive_report(
                summary_file,
                dataset_id,
                dataset_name,
                analysis_results,
                saved_files
            )
            saved_files["comprehensive_report"] = summary_file
            
            # 5. 保存元数据
            metadata_file = dataset_dir / f"metadata_{timestamp}.json"
            self._save_metadata(metadata_file, dataset_id, dataset_name, analysis_results, saved_files)
            saved_files["metadata"] = metadata_file
            
            logger.info(f"工业分析报告保存完成，共 {len(saved_files)} 个文件")
            return saved_files
            
        except Exception as e:
            logger.error(f"保存工业分析报告失败: {e}")
            raise
    
    def _save_markdown_file(
        self, 
        file_path: Path, 
        title: str, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> None:
        """保存Markdown文件
        
        Args:
            file_path: 文件路径
            title: 文件标题
            content: 文件内容
            metadata: 元数据
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入YAML Front Matter
                f.write("---\n")
                for key, value in metadata.items():
                    f.write(f"{key}: {json.dumps(value, ensure_ascii=False)}\n")
                f.write("---\n\n")
                
                # 写入标题
                f.write(f"# {title}\n\n")
                
                # 写入生成信息
                f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**数据集**: {metadata.get('dataset_name', 'Unknown')}\n")
                f.write(f"**分析类型**: {metadata.get('analysis_type', 'Unknown')}\n\n")
                f.write("---\n\n")
                
                # 写入主要内容
                f.write(content)
                
                # 写入页脚
                f.write(f"\n\n---\n\n")
                f.write("*本报告由工业数据分析系统自动生成*\n")
            
            logger.info(f"Markdown文件已保存: {file_path}")
            
        except Exception as e:
            logger.error(f"保存Markdown文件失败: {e}")
            raise
    
    def _generate_comprehensive_report(
        self,
        file_path: Path,
        dataset_id: str,
        dataset_name: str,
        analysis_results: Dict[str, Any],
        saved_files: Dict[str, Path]
    ) -> None:
        """生成综合分析报告
        
        Args:
            file_path: 文件路径
            dataset_id: 数据集ID
            dataset_name: 数据集名称
            analysis_results: 分析结果
            saved_files: 已保存的文件
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # YAML Front Matter
                f.write("---\n")
                f.write(f"title: {dataset_name} - 工业数据分析综合报告\n")
                f.write(f"dataset_id: {dataset_id}\n")
                f.write(f"dataset_name: {dataset_name}\n")
                f.write(f"report_type: comprehensive_industrial_analysis\n")
                f.write(f"generated_at: {datetime.now().isoformat()}\n")
                f.write("---\n\n")
                
                # 报告标题
                f.write(f"# {dataset_name} - 工业数据分析综合报告\n\n")
                
                # 报告概览
                f.write("## 📊 报告概览\n\n")
                f.write(f"- **数据集名称**: {dataset_name}\n")
                f.write(f"- **数据集ID**: {dataset_id}\n")
                f.write(f"- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- **分析类型**: 工业数据深度分析\n")
                f.write(f"- **报告文件数**: {len(saved_files)} 个\n\n")
                
                # 数据基本信息
                if analysis_results.get("data_info"):
                    data_info = analysis_results["data_info"]
                    f.write("## 📈 数据基本信息\n\n")
                    f.write(f"- **数据形状**: {data_info.get('shape', 'Unknown')}\n")
                    f.write(f"- **列数**: {len(data_info.get('columns', []))}\n")
                    f.write(f"- **数据类型**: {len(set(data_info.get('dtypes', {}).values()))} 种\n\n")
                
                # 分析结果摘要
                f.write("## 🔍 分析结果摘要\n\n")
                
                # 设备时间列识别摘要
                if analysis_results.get("device_time_identification"):
                    f.write("### 1. 设备列和时间列识别\n")
                    f.write("- ✅ 已完成设备相关列和时间列的自动识别\n")
                    f.write("- 📋 识别结果以表格形式展示，包含重要程度排序\n")
                    f.write(f"- 📄 详细结果请查看: `{saved_files.get('device_time_identification', {}).name}`\n\n")
                
                # 业务含义分析摘要
                if analysis_results.get("business_meaning_analysis"):
                    f.write("### 2. 业务含义分析\n")
                    f.write("- ✅ 已完成各列业务含义的深度分析\n")
                    f.write("- 🏭 专注于工业业务场景的理解和应用\n")
                    f.write(f"- 📄 详细结果请查看: `{saved_files.get('business_meaning_analysis', {}).name}`\n\n")
                
                # 控制原理分析摘要
                if analysis_results.get("control_relationships_analysis"):
                    f.write("### 3. 控制原理分析\n")
                    f.write("- ✅ 已完成控制关系和因果关系分析\n")
                    f.write("- 📊 包含Mermaid图表的可视化展示\n")
                    f.write("- ⚙️ 提供控制系统优化建议\n")
                    f.write(f"- 📄 详细结果请查看: `{saved_files.get('control_relationships_analysis', {}).name}`\n\n")
                
                # 文件清单
                f.write("## 📁 报告文件清单\n\n")
                f.write("| 序号 | 文件名 | 分析类型 | 描述 |\n")
                f.write("|------|--------|----------|------|\n")
                
                file_descriptions = {
                    "device_time_identification": "设备列和时间列识别",
                    "business_meaning_analysis": "业务含义分析", 
                    "control_relationships_analysis": "控制原理分析",
                    "comprehensive_report": "综合分析报告",
                    "metadata": "分析元数据"
                }
                
                for i, (key, file_path) in enumerate(saved_files.items(), 1):
                    desc = file_descriptions.get(key, "其他文件")
                    f.write(f"| {i} | `{file_path.name}` | {desc} | {desc}详细结果 |\n")
                
                f.write("\n")
                
                # 使用建议
                f.write("## 💡 使用建议\n\n")
                f.write("1. **查看顺序**: 建议按照文件编号顺序查看分析结果\n")
                f.write("2. **重点关注**: 控制原理分析中的Mermaid图表提供了直观的系统架构展示\n")
                f.write("3. **业务应用**: 业务含义分析结果可直接用于业务理解和决策支持\n")
                f.write("4. **技术优化**: 控制原理分析提供了具体的系统优化建议\n\n")
                
                # 技术说明
                f.write("## 🔧 技术说明\n\n")
                f.write("- **分析引擎**: 基于LangGraph的工业数据分析工作流\n")
                f.write("- **AI模型**: DeepSeek Chat (专业推理模型)\n")
                f.write("- **输出格式**: Markdown表格 + Mermaid图表\n")
                f.write("- **文件编码**: UTF-8\n")
                f.write("- **版本控制**: 支持时间戳版本管理\n\n")
                
                # 页脚
                f.write("---\n\n")
                f.write("*本综合报告由工业数据分析系统自动生成*\n")
                f.write(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
            
            logger.info(f"综合分析报告已保存: {file_path}")
            
        except Exception as e:
            logger.error(f"生成综合报告失败: {e}")
            raise
    
    def _save_metadata(
        self,
        file_path: Path,
        dataset_id: str,
        dataset_name: str,
        analysis_results: Dict[str, Any],
        saved_files: Dict[str, Path]
    ) -> None:
        """保存分析元数据
        
        Args:
            file_path: 文件路径
            dataset_id: 数据集ID
            dataset_name: 数据集名称
            analysis_results: 分析结果
            saved_files: 已保存的文件
        """
        try:
            metadata = {
                "dataset_info": {
                    "id": dataset_id,
                    "name": dataset_name,
                    "analysis_timestamp": datetime.now().isoformat()
                },
                "analysis_summary": {
                    "completed_steps": analysis_results.get("completed_steps", []),
                    "current_step": analysis_results.get("current_step", "unknown"),
                    "errors": analysis_results.get("errors", []),
                    "execution_time": analysis_results.get("execution_time", 0)
                },
                "files": {
                    key: {
                        "path": str(path),
                        "name": path.name,
                        "size": path.stat().st_size if path.exists() else 0,
                        "created_at": datetime.now().isoformat()
                    }
                    for key, path in saved_files.items()
                },
                "data_info": analysis_results.get("data_info", {}),
                "system_info": {
                    "version": "1.0",
                    "generator": "Industrial Data Analysis System",
                    "workflow_type": "industrial_analysis"
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析元数据已保存: {file_path}")
            
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            raise
    
    def list_reports(self, report_type: str = "industrial") -> List[Dict[str, Any]]:
        """列出已保存的报告
        
        Args:
            report_type: 报告类型 ("industrial", "general")
            
        Returns:
            List[Dict[str, Any]]: 报告列表
        """
        try:
            if report_type == "industrial":
                base_dir = self.industrial_dir
            else:
                base_dir = self.general_dir
            
            reports = []
            
            for dataset_dir in base_dir.iterdir():
                if dataset_dir.is_dir():
                    # 查找元数据文件
                    metadata_files = list(dataset_dir.glob("metadata_*.json"))
                    
                    for metadata_file in metadata_files:
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            reports.append({
                                "dataset_id": metadata["dataset_info"]["id"],
                                "dataset_name": metadata["dataset_info"]["name"],
                                "analysis_timestamp": metadata["dataset_info"]["analysis_timestamp"],
                                "directory": str(dataset_dir),
                                "files_count": len(metadata["files"]),
                                "completed_steps": metadata["analysis_summary"]["completed_steps"],
                                "metadata_file": str(metadata_file)
                            })
                        except Exception as e:
                            logger.warning(f"读取元数据文件失败: {metadata_file}, {e}")
            
            # 按时间排序
            reports.sort(key=lambda x: x["analysis_timestamp"], reverse=True)
            
            logger.info(f"找到 {len(reports)} 个{report_type}报告")
            return reports
            
        except Exception as e:
            logger.error(f"列出报告失败: {e}")
            return []
    
    def export_report_archive(self, dataset_id: str, export_format: str = "zip") -> Optional[Path]:
        """导出报告归档文件
        
        Args:
            dataset_id: 数据集ID
            export_format: 导出格式 ("zip", "tar")
            
        Returns:
            Optional[Path]: 归档文件路径
        """
        try:
            # 查找数据集目录
            dataset_dirs = list(self.industrial_dir.glob(f"{dataset_id}_*"))
            
            if not dataset_dirs:
                logger.warning(f"未找到数据集 {dataset_id} 的报告")
                return None
            
            dataset_dir = dataset_dirs[0]  # 取第一个匹配的目录
            
            # 创建归档文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{dataset_dir.name}_{timestamp}"
            
            if export_format == "zip":
                archive_path = self.exports_dir / f"{archive_name}.zip"
                shutil.make_archive(str(archive_path.with_suffix('')), 'zip', dataset_dir)
            else:
                archive_path = self.exports_dir / f"{archive_name}.tar.gz"
                shutil.make_archive(str(archive_path.with_suffix('').with_suffix('')), 'gztar', dataset_dir)
            
            logger.info(f"报告归档文件已创建: {archive_path}")
            return archive_path
            
        except Exception as e:
            logger.error(f"导出报告归档失败: {e}")
            return None
    
    def cleanup_old_reports(self, days: int = 30) -> int:
        """清理旧报告
        
        Args:
            days: 保留天数
            
        Returns:
            int: 清理的报告数量
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            for report_dir in [self.industrial_dir, self.general_dir]:
                for dataset_dir in report_dir.iterdir():
                    if dataset_dir.is_dir():
                        # 检查目录修改时间
                        dir_mtime = datetime.fromtimestamp(dataset_dir.stat().st_mtime)
                        
                        if dir_mtime < cutoff_date:
                            shutil.rmtree(dataset_dir)
                            cleaned_count += 1
                            logger.info(f"已清理旧报告目录: {dataset_dir}")
            
            logger.info(f"清理完成，共清理 {cleaned_count} 个旧报告")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧报告失败: {e}")
            return 0
    
    def get_report_statistics(self) -> Dict[str, Any]:
        """获取报告统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            industrial_reports = self.list_reports("industrial")
            general_reports = self.list_reports("general")
            
            # 计算总文件大小
            total_size = 0
            for report_dir in [self.industrial_dir, self.general_dir]:
                for file_path in report_dir.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            statistics = {
                "total_reports": len(industrial_reports) + len(general_reports),
                "industrial_reports": len(industrial_reports),
                "general_reports": len(general_reports),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "reports_directory": str(self.reports_dir),
                "last_updated": datetime.now().isoformat()
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"获取报告统计失败: {e}")
            return {}
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        import re
        # 移除或替换非法字符
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        return sanitized


# 创建全局实例
report_manager = ReportManager() 