"""报告版本管理器

提供数据分析报告的版本管理功能，包括：
- JSON分析结果版本管理  
- Markdown报告版本管理
- 数据库记录版本管理
- 报告历史记录管理
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from loguru import logger

from ..schemas.dataset import DatasetMetadata


class ReportVersionManager:
    """报告版本管理器"""
    
    def __init__(self, 
                 json_dir: Path,
                 reports_dir: Path):
        """初始化报告版本管理器
        
        Args:
            json_dir: JSON分析结果目录
            reports_dir: 报告文件目录
        """
        self.json_dir = Path(json_dir)
        self.reports_dir = Path(reports_dir)
        
        # 创建版本化目录结构
        self._setup_version_directories()
        
        logger.info("报告版本管理器初始化完成")
    
    def _setup_version_directories(self):
        """设置版本化目录结构"""
        try:
            # JSON版本目录
            self.json_versions_dir = self.json_dir / "versions"
            self.json_versions_dir.mkdir(parents=True, exist_ok=True)
            
            # 报告版本目录
            self.report_versions_dir = self.reports_dir / "versions"
            self.report_versions_dir.mkdir(parents=True, exist_ok=True)
            
            # 当前版本软链接目录
            self.json_current_dir = self.json_dir / "current"
            self.report_current_dir = self.reports_dir / "current"
            self.json_current_dir.mkdir(exist_ok=True)
            self.report_current_dir.mkdir(exist_ok=True)
            
            logger.debug("版本化目录结构设置完成")
            
        except Exception as e:
            logger.error(f"设置版本化目录失败: {e}")
            raise
    
    def save_analysis_result_version(self, 
                                   dataset_id: str,
                                   analysis_type: str,
                                   result_data: Dict[str, Any],
                                   version: Optional[str] = None) -> str:
        """保存分析结果版本
        
        Args:
            dataset_id: 数据集ID
            analysis_type: 分析类型 (business, quality)
            result_data: 分析结果数据
            version: 版本号，如果不提供则自动生成
            
        Returns:
            str: 版本号
        """
        try:
            # 生成版本号
            if version is None:
                version = self._generate_version(dataset_id, analysis_type)
            
            # 创建版本化的结果数据
            versioned_data = {
                "dataset_id": dataset_id,
                "analysis_type": analysis_type,
                "version": version,
                "created_at": datetime.now().isoformat(),
                "data": result_data
            }
            
            # 保存到版本目录
            version_file = self._get_version_file_path(dataset_id, analysis_type, version)
            version_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(versioned_data, f, ensure_ascii=False, indent=2)
            
            # 更新当前版本引用
            self._update_current_version(dataset_id, analysis_type, version)
            
            logger.info(f"分析结果版本保存完成: {dataset_id}/{analysis_type} v{version}")
            return version
            
        except Exception as e:
            logger.error(f"保存分析结果版本失败: {e}")
            raise
    
    def save_report_version(self,
                          dataset_id: str,
                          report_type: str,
                          report_files: Dict[str, str],
                          version: Optional[str] = None) -> str:
        """保存报告文件版本
        
        Args:
            dataset_id: 数据集ID
            report_type: 报告类型 (industrial, quality)
            report_files: 报告文件内容 {filename: content}
            version: 版本号
            
        Returns:
            str: 版本号
        """
        try:
            # 生成版本号
            if version is None:
                version = self._generate_version(dataset_id, report_type, "report")
            
            # 创建版本目录
            version_dir = self._get_report_version_dir(dataset_id, report_type, version)
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存报告文件
            for filename, content in report_files.items():
                report_file = version_dir / filename
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # 保存版本元数据
            metadata = {
                "dataset_id": dataset_id,
                "report_type": report_type,
                "version": version,
                "created_at": datetime.now().isoformat(),
                "files": list(report_files.keys()),
                "total_files": len(report_files)
            }
            
            metadata_file = version_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 更新当前版本引用
            self._update_current_report_version(dataset_id, report_type, version)
            
            logger.info(f"报告版本保存完成: {dataset_id}/{report_type} v{version} ({len(report_files)} 个文件)")
            return version
            
        except Exception as e:
            logger.error(f"保存报告版本失败: {e}")
            raise
    
    def get_analysis_result_versions(self, 
                                   dataset_id: str,
                                   analysis_type: str) -> List[Dict[str, Any]]:
        """获取分析结果版本列表
        
        Args:
            dataset_id: 数据集ID
            analysis_type: 分析类型
            
        Returns:
            List[Dict[str, Any]]: 版本列表
        """
        try:
            versions = []
            dataset_version_dir = self.json_versions_dir / dataset_id / analysis_type
            
            if not dataset_version_dir.exists():
                return versions
            
            for version_file in dataset_version_dir.glob("*.json"):
                try:
                    with open(version_file, 'r', encoding='utf-8') as f:
                        version_data = json.load(f)
                    
                    versions.append({
                        "version": version_data.get("version"),
                        "created_at": version_data.get("created_at"),
                        "file_size": version_file.stat().st_size,
                        "file_path": str(version_file)
                    })
                except Exception as e:
                    logger.warning(f"读取版本文件失败: {version_file}, {e}")
            
            # 按版本号排序
            versions.sort(key=lambda x: x["created_at"], reverse=True)
            
            logger.info(f"获取分析结果版本列表: {dataset_id}/{analysis_type} -> {len(versions)} 个版本")
            return versions
            
        except Exception as e:
            logger.error(f"获取分析结果版本列表失败: {e}")
            return []
    
    def get_report_versions(self,
                          dataset_id: str,
                          report_type: str) -> List[Dict[str, Any]]:
        """获取报告版本列表
        
        Args:
            dataset_id: 数据集ID
            report_type: 报告类型
            
        Returns:
            List[Dict[str, Any]]: 版本列表
        """
        try:
            versions = []
            dataset_report_dir = self.report_versions_dir / dataset_id / report_type
            
            if not dataset_report_dir.exists():
                return versions
            
            for version_dir in dataset_report_dir.iterdir():
                if not version_dir.is_dir():
                    continue
                
                metadata_file = version_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        versions.append({
                            "version": metadata.get("version"),
                            "created_at": metadata.get("created_at"),
                            "total_files": metadata.get("total_files", 0),
                            "files": metadata.get("files", []),
                            "directory": str(version_dir)
                        })
                    except Exception as e:
                        logger.warning(f"读取报告版本元数据失败: {metadata_file}, {e}")
            
            # 按创建时间排序
            versions.sort(key=lambda x: x["created_at"], reverse=True)
            
            logger.info(f"获取报告版本列表: {dataset_id}/{report_type} -> {len(versions)} 个版本")
            return versions
            
        except Exception as e:
            logger.error(f"获取报告版本列表失败: {e}")
            return []
    
    def load_analysis_result_version(self,
                                   dataset_id: str,
                                   analysis_type: str,
                                   version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """加载指定版本的分析结果
        
        Args:
            dataset_id: 数据集ID
            analysis_type: 分析类型
            version: 版本号，如果不提供则加载最新版本
            
        Returns:
            Optional[Dict[str, Any]]: 分析结果数据
        """
        try:
            if version is None:
                # 加载最新版本
                version = self._get_latest_version(dataset_id, analysis_type)
                if not version:
                    return None
            
            version_file = self._get_version_file_path(dataset_id, analysis_type, version)
            if not version_file.exists():
                logger.warning(f"版本文件不存在: {version_file}")
                return None
            
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            logger.info(f"加载分析结果版本: {dataset_id}/{analysis_type} v{version}")
            return version_data.get("data")
            
        except Exception as e:
            logger.error(f"加载分析结果版本失败: {e}")
            return None
    
    def cleanup_old_versions(self,
                           dataset_id: str,
                           keep_versions: int = 5) -> int:
        """清理旧版本
        
        Args:
            dataset_id: 数据集ID
            keep_versions: 保留版本数量
            
        Returns:
            int: 清理的版本数量
        """
        try:
            total_cleaned = 0
            
            # 清理JSON版本
            dataset_json_dir = self.json_versions_dir / dataset_id
            if dataset_json_dir.exists():
                for analysis_type_dir in dataset_json_dir.iterdir():
                    if analysis_type_dir.is_dir():
                        cleaned = self._cleanup_directory_versions(analysis_type_dir, keep_versions)
                        total_cleaned += cleaned
            
            # 清理报告版本
            dataset_report_dir = self.report_versions_dir / dataset_id
            if dataset_report_dir.exists():
                for report_type_dir in dataset_report_dir.iterdir():
                    if report_type_dir.is_dir():
                        cleaned = self._cleanup_directory_versions(report_type_dir, keep_versions)
                        total_cleaned += cleaned
            
            logger.info(f"版本清理完成: {dataset_id} -> 清理 {total_cleaned} 个版本")
            return total_cleaned
            
        except Exception as e:
            logger.error(f"清理版本失败: {e}")
            return 0
    
    def _generate_version(self, dataset_id: str, analysis_type: str, prefix: str = "") -> str:
        """生成版本号"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if prefix:
            return f"{prefix}_{timestamp}"
        return timestamp
    
    def _get_version_file_path(self, dataset_id: str, analysis_type: str, version: str) -> Path:
        """获取版本文件路径"""
        return self.json_versions_dir / dataset_id / analysis_type / f"{version}.json"
    
    def _get_report_version_dir(self, dataset_id: str, report_type: str, version: str) -> Path:
        """获取报告版本目录路径"""
        return self.report_versions_dir / dataset_id / report_type / version
    
    def _update_current_version(self, dataset_id: str, analysis_type: str, version: str):
        """更新当前版本引用"""
        try:
            current_file = self.json_current_dir / f"{dataset_id}_{analysis_type}.json"
            current_info = {
                "dataset_id": dataset_id,
                "analysis_type": analysis_type,
                "current_version": version,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(current_info, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"更新当前版本引用失败: {e}")
    
    def _update_current_report_version(self, dataset_id: str, report_type: str, version: str):
        """更新当前报告版本引用"""
        try:
            current_file = self.report_current_dir / f"{dataset_id}_{report_type}.json"
            current_info = {
                "dataset_id": dataset_id,
                "report_type": report_type,
                "current_version": version,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(current_info, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"更新当前报告版本引用失败: {e}")
    
    def _get_latest_version(self, dataset_id: str, analysis_type: str) -> Optional[str]:
        """获取最新版本号"""
        try:
            current_file = self.json_current_dir / f"{dataset_id}_{analysis_type}.json"
            if current_file.exists():
                with open(current_file, 'r', encoding='utf-8') as f:
                    current_info = json.load(f)
                return current_info.get("current_version")
            return None
            
        except Exception as e:
            logger.error(f"获取最新版本号失败: {e}")
            return None
    
    def _cleanup_directory_versions(self, directory: Path, keep_versions: int) -> int:
        """清理目录中的旧版本"""
        try:
            if not directory.exists():
                return 0
            
            # 获取所有版本文件/目录
            items = list(directory.iterdir())
            if len(items) <= keep_versions:
                return 0
            
            # 按修改时间排序，保留最新的
            items.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            items_to_remove = items[keep_versions:]
            
            cleaned_count = 0
            for item in items_to_remove:
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    cleaned_count += 1
                except Exception as e:
                    logger.error(f"删除版本失败: {item}, {e}")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理目录版本失败: {e}")
            return 0


# 全局报告版本管理器实例
report_version_manager = None

def get_report_version_manager(metadata_dir: Path, reports_dir: Path) -> ReportVersionManager:
    """获取报告版本管理器实例"""
    global report_version_manager
    if report_version_manager is None:
        json_dir = metadata_dir / "analysis_results"
        report_version_manager = ReportVersionManager(json_dir, reports_dir)
    return report_version_manager 