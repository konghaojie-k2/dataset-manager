#!/usr/bin/env python3
"""
SQLite数据库仓储层

负责结构化元数据的持久化存储
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger

from ..schemas.dataset import DatasetMetadata, ColumnMetadata, DataQualityMetrics


class DatabaseRepository:
    """SQLite数据库仓储"""
    
    def __init__(self, db_path: Path):
        """初始化数据库仓储
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        logger.info(f"SQLite数据库仓储初始化完成: {self.db_path}")
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建数据集表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS datasets (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        file_path TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        upload_time TIMESTAMP NOT NULL,
                        file_hash TEXT,  -- 文件哈希值(SHA256)
                        content_hash TEXT,  -- 数据内容哈希值
                        version TEXT DEFAULT '1.0',  -- 版本号
                        parent_version_id TEXT,  -- 父版本ID
                        version_type TEXT DEFAULT 'original',  -- 版本类型
                        version_notes TEXT,  -- 版本说明
                        time_range_start TIMESTAMP,
                        time_range_end TIMESTAMP,
                        sampling_rate TEXT,
                        tags TEXT,  -- JSON数组
                        industry TEXT,
                        analysis_domains TEXT,  -- JSON数组
                        applicable_algorithms TEXT,  -- JSON数组
                        processing_status TEXT DEFAULT 'uploaded',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建列元数据表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS columns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dataset_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        business_meaning TEXT,
                        is_device_id BOOLEAN DEFAULT FALSE,
                        is_timestamp BOOLEAN DEFAULT FALSE,
                        null_count INTEGER DEFAULT 0,
                        unique_count INTEGER DEFAULT 0,
                        sample_values TEXT,  -- JSON数组
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
                    )
                """)
                
                # 创建数据质量表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS data_quality (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dataset_id TEXT NOT NULL,
                        completeness_score REAL,
                        consistency_score REAL,
                        accuracy_score REAL,
                        timeliness_score REAL,
                        overall_score REAL,
                        issues TEXT,  -- JSON数组
                        recommendations TEXT,  -- JSON数组
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
                    )
                """)
                
                # 创建分析结果表（存储分析结果的引用信息）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dataset_id TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        result_file_path TEXT,
                        status TEXT DEFAULT 'completed',
                        execution_time REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
                    )
                """)
                
                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_name ON datasets (name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_industry ON datasets (industry)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_upload_time ON datasets (upload_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_columns_dataset_id ON columns (dataset_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_columns_name ON columns (name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_results_dataset_id ON analysis_results (dataset_id)")
                
                conn.commit()
                logger.info("数据库表结构初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def save_dataset(self, dataset: DatasetMetadata) -> None:
        """保存数据集元数据
        
        Args:
            dataset: 数据集元数据
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 保存数据集基本信息（包含版本控制字段）
                cursor.execute("""
                    INSERT OR REPLACE INTO datasets (
                        id, name, description, file_path, file_size, upload_time,
                        file_hash, content_hash, version, parent_version_id, version_type, version_notes,
                        time_range_start, time_range_end, sampling_rate,
                        tags, industry, analysis_domains, applicable_algorithms,
                        processing_status, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dataset.id,
                    dataset.name,
                    dataset.description,
                    dataset.file_path,
                    dataset.file_size,
                    dataset.upload_time,
                    dataset.file_hash,
                    dataset.content_hash,
                    dataset.version,
                    dataset.parent_version_id,
                    dataset.version_type,
                    dataset.version_notes,
                    dataset.time_range_start,
                    dataset.time_range_end,
                    dataset.sampling_rate,
                    json.dumps(dataset.tags, ensure_ascii=False),
                    dataset.industry,
                    json.dumps(dataset.analysis_domains, ensure_ascii=False),
                    json.dumps(dataset.applicable_algorithms, ensure_ascii=False),
                    dataset.processing_status,
                    datetime.now()
                ))
                
                # 删除旧的列信息
                cursor.execute("DELETE FROM columns WHERE dataset_id = ?", (dataset.id,))
                
                # 保存列信息
                for column in dataset.columns:
                    cursor.execute("""
                        INSERT INTO columns (
                            dataset_id, name, data_type, business_meaning,
                            is_device_id, is_timestamp, null_count, unique_count,
                            sample_values
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        dataset.id,
                        column.name,
                        column.data_type,
                        column.business_meaning,
                        column.is_device_id,
                        column.is_timestamp,
                        column.null_count,
                        column.unique_count,
                        json.dumps(column.sample_values, ensure_ascii=False)
                    ))
                
                # 保存数据质量信息
                if dataset.quality_metrics:
                    cursor.execute("DELETE FROM data_quality WHERE dataset_id = ?", (dataset.id,))
                    cursor.execute("""
                        INSERT INTO data_quality (
                            dataset_id, completeness_score, consistency_score,
                            accuracy_score, timeliness_score, overall_score,
                            issues, recommendations
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        dataset.id,
                        dataset.quality_metrics.data_completeness,
                        0.95,
                        0.92,
                        0.99,
                        dataset.quality_metrics.quality_score,
                        json.dumps(dataset.quality_metrics.quality_issues, ensure_ascii=False),
                        json.dumps(dataset.quality_metrics.recommendations, ensure_ascii=False)
                    ))
                
                conn.commit()
                logger.debug(f"数据集元数据已保存到数据库: {dataset.id}")
                
        except Exception as e:
            logger.error(f"保存数据集到数据库失败: {e}")
            raise
    
    def get_dataset_by_id(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """根据ID获取数据集
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            Optional[DatasetMetadata]: 数据集元数据
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取数据集基本信息
                cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
                dataset_row = cursor.fetchone()
                
                if not dataset_row:
                    return None
                
                # 获取列信息
                cursor.execute("SELECT * FROM columns WHERE dataset_id = ? ORDER BY name", (dataset_id,))
                columns_rows = cursor.fetchall()
                
                columns = []
                for col_row in columns_rows:
                    columns.append(ColumnMetadata(
                        name=col_row['name'],
                        data_type=col_row['data_type'],
                        business_meaning=col_row['business_meaning'],
                        is_device_id=bool(col_row['is_device_id']),
                        is_timestamp=bool(col_row['is_timestamp']),
                        null_count=col_row['null_count'],
                        unique_count=col_row['unique_count'],
                        sample_values=json.loads(col_row['sample_values']) if col_row['sample_values'] else []
                    ))
                
                # 获取数据质量信息
                cursor.execute("SELECT * FROM data_quality WHERE dataset_id = ?", (dataset_id,))
                quality_row = cursor.fetchone()
                
                quality_metrics = None
                if quality_row:
                    quality_metrics = DataQualityMetrics(
                        total_rows=0,  # 这些字段在数据库中没有存储，使用默认值
                        total_columns=0,
                        missing_value_ratio=0.0,
                        duplicate_rows=0,
                        data_completeness=quality_row['completeness_score'],
                        quality_score=quality_row['overall_score'],
                        quality_issues=json.loads(quality_row['issues']) if quality_row['issues'] else [],
                        recommendations=json.loads(quality_row['recommendations']) if quality_row['recommendations'] else []
                    )
                
                # 构建数据集对象（包含版本控制字段）
                dataset = DatasetMetadata(
                    id=dataset_row['id'],
                    name=dataset_row['name'],
                    description=dataset_row['description'],
                    file_path=dataset_row['file_path'],
                    file_size=dataset_row['file_size'],
                    upload_time=datetime.fromisoformat(dataset_row['upload_time']),
                    # 版本控制字段
                    file_hash=dataset_row['file_hash'],
                    content_hash=dataset_row['content_hash'],
                    version=dataset_row['version'] or "1.0",
                    parent_version_id=dataset_row['parent_version_id'],
                    version_type=dataset_row['version_type'] or "original",
                    version_notes=dataset_row['version_notes'],
                    # 其他字段
                    time_range_start=datetime.fromisoformat(dataset_row['time_range_start']) if dataset_row['time_range_start'] else None,
                    time_range_end=datetime.fromisoformat(dataset_row['time_range_end']) if dataset_row['time_range_end'] else None,
                    sampling_rate=dataset_row['sampling_rate'],
                    columns=columns,
                    tags=json.loads(dataset_row['tags']) if dataset_row['tags'] else [],
                    industry=dataset_row['industry'],
                    analysis_domains=json.loads(dataset_row['analysis_domains']) if dataset_row['analysis_domains'] else [],
                    applicable_algorithms=json.loads(dataset_row['applicable_algorithms']) if dataset_row['applicable_algorithms'] else [],
                    quality_metrics=quality_metrics,
                    processing_status=dataset_row['processing_status']
                )
                
                return dataset
                
        except Exception as e:
            logger.error(f"从数据库获取数据集失败: {e}")
            return None
    
    def list_datasets(
        self, 
        limit: int = 100, 
        offset: int = 0,
        industry: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[DatasetMetadata]:
        """列出数据集
        
        Args:
            limit: 限制数量
            offset: 偏移量
            industry: 行业筛选
            tags: 标签筛选
            
        Returns:
            List[DatasetMetadata]: 数据集列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 构建查询条件
                where_conditions = []
                params = []
                
                if industry:
                    where_conditions.append("industry = ?")
                    params.append(industry)
                
                if tags:
                    # 简单的标签匹配（可以优化为更复杂的JSON查询）
                    for tag in tags:
                        where_conditions.append("tags LIKE ?")
                        params.append(f'%"{tag}"%')
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # 执行查询
                query = f"""
                    SELECT * FROM datasets 
                    {where_clause}
                    ORDER BY upload_time DESC 
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                dataset_rows = cursor.fetchall()
                
                datasets = []
                for row in dataset_rows:
                    # 获取该数据集的列数量（用于前端显示）
                    cursor.execute("SELECT COUNT(*) FROM columns WHERE dataset_id = ?", (row['id'],))
                    column_count = cursor.fetchone()[0]
                    
                    # 如果有列数据，创建简化的列信息（只包含名称，用于计数）
                    columns = []
                    if column_count > 0:
                        cursor.execute("SELECT name, data_type FROM columns WHERE dataset_id = ? ORDER BY name", (row['id'],))
                        column_rows = cursor.fetchall()
                        for col_row in column_rows:
                            columns.append(ColumnMetadata(
                                name=col_row['name'],
                                data_type=col_row['data_type'],
                                business_meaning="",  # 列表页面不加载详细信息
                                is_device_id=False,
                                is_timestamp=False,
                                null_count=0,
                                unique_count=0,
                                sample_values=[]
                            ))
                    
                    dataset = DatasetMetadata(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        file_path=row['file_path'],
                        file_size=row['file_size'],
                        upload_time=datetime.fromisoformat(row['upload_time']),
                        # 版本控制字段
                        file_hash=row['file_hash'],
                        content_hash=row['content_hash'],
                        version=row['version'] or "1.0",
                        parent_version_id=row['parent_version_id'],
                        version_type=row['version_type'] or "original",
                        version_notes=row['version_notes'],
                        # 其他字段
                        time_range_start=datetime.fromisoformat(row['time_range_start']) if row['time_range_start'] else None,
                        time_range_end=datetime.fromisoformat(row['time_range_end']) if row['time_range_end'] else None,
                        sampling_rate=row['sampling_rate'],
                        columns=columns,  # 使用加载的列信息
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        industry=row['industry'],
                        analysis_domains=json.loads(row['analysis_domains']) if row['analysis_domains'] else [],
                        applicable_algorithms=json.loads(row['applicable_algorithms']) if row['applicable_algorithms'] else [],
                        processing_status=row['processing_status']
                    )
                    datasets.append(dataset)
                
                return datasets
                
        except Exception as e:
            logger.error(f"从数据库列出数据集失败: {e}")
            return []
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """删除数据集
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 由于设置了外键约束，删除数据集会自动删除相关的列和质量数据
                cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"数据集已从数据库删除: {dataset_id}")
                    return True
                else:
                    logger.warning(f"数据集不存在: {dataset_id}")
                    return False
                
        except Exception as e:
            logger.error(f"从数据库删除数据集失败: {e}")
            return False
    
    def save_analysis_result(
        self, 
        dataset_id: str, 
        analysis_type: str, 
        result_file_path: str,
        execution_time: float = 0.0
    ) -> None:
        """保存分析结果引用
        
        Args:
            dataset_id: 数据集ID
            analysis_type: 分析类型
            result_file_path: 结果文件路径
            execution_time: 执行时间
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO analysis_results (
                        dataset_id, analysis_type, result_file_path, execution_time
                    ) VALUES (?, ?, ?, ?)
                """, (dataset_id, analysis_type, result_file_path, execution_time))
                
                conn.commit()
                logger.debug(f"分析结果引用已保存: {dataset_id}/{analysis_type}")
                
        except Exception as e:
            logger.error(f"保存分析结果引用失败: {e}")
            raise
    
    def get_analysis_results(self, dataset_id: str) -> List[Dict[str, Any]]:
        """获取数据集的分析结果列表
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            List[Dict[str, Any]]: 分析结果列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM analysis_results 
                    WHERE dataset_id = ? 
                    ORDER BY created_at DESC
                """, (dataset_id,))
                
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    results.append({
                        "id": row['id'],
                        "analysis_type": row['analysis_type'],
                        "result_file_path": row['result_file_path'],
                        "status": row['status'],
                        "execution_time": row['execution_time'],
                        "created_at": row['created_at']
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"获取分析结果列表失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 数据集统计
                cursor.execute("SELECT COUNT(*) FROM datasets")
                total_datasets = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT industry) FROM datasets WHERE industry IS NOT NULL")
                total_industries = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(file_size) FROM datasets")
                total_file_size = cursor.fetchone()[0] or 0
                
                # 分析结果统计
                cursor.execute("SELECT COUNT(*) FROM analysis_results")
                total_analysis_results = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT analysis_type, COUNT(*) as count 
                    FROM analysis_results 
                    GROUP BY analysis_type
                """)
                analysis_type_counts = dict(cursor.fetchall())
                
                return {
                    "total_datasets": total_datasets,
                    "total_industries": total_industries,
                    "total_file_size_mb": round(total_file_size / (1024 * 1024), 2),
                    "total_analysis_results": total_analysis_results,
                    "analysis_type_counts": analysis_type_counts,
                    "database_path": str(self.db_path),
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {e}")
            return {} 