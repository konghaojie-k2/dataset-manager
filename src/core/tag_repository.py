#!/usr/bin/env python3
"""
标签仓储层

负责标签数据的持久化存储
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger

from ..schemas.tag import Tag, TagCategory


class TagRepository:
    """标签数据库仓储"""
    
    def __init__(self, db_path: Path):
        """初始化标签仓储
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库表
        self._init_database()
        
        logger.info(f"标签仓储初始化完成: {self.db_path}")
    
    def _init_database(self) -> None:
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建标签表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        color TEXT DEFAULT '#007bff',
                        category TEXT,
                        usage_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建数据集标签关联表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dataset_tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dataset_id TEXT NOT NULL,
                        tag_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tag_name) REFERENCES tags (name) ON DELETE CASCADE,
                        UNIQUE(dataset_id, tag_name)
                    )
                """)
                
                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags (name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_category ON tags (category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_dataset_tags_dataset_id ON dataset_tags (dataset_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_dataset_tags_tag_name ON dataset_tags (tag_name)")
                
                conn.commit()
                logger.debug("标签数据库表初始化完成")
                
        except Exception as e:
            logger.error(f"初始化标签数据库失败: {e}")
            raise
    
    def create_tag(self, tag: Tag) -> Tag:
        """创建标签
        
        Args:
            tag: 标签对象
            
        Returns:
            Tag: 创建后的标签对象
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO tags (name, description, color, category)
                    VALUES (?, ?, ?, ?)
                """, (
                    tag.name,
                    tag.description,
                    tag.color,
                    tag.category
                ))
                
                tag_id = cursor.lastrowid
                conn.commit()
                
                # 返回创建的标签
                return self.get_tag_by_id(tag_id)
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"标签名称 '{tag.name}' 已存在")
            raise
        except Exception as e:
            logger.error(f"创建标签失败: {e}")
            raise
    
    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """根据ID获取标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Optional[Tag]: 标签对象
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return Tag(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    color=row['color'],
                    category=row['category'],
                    usage_count=row['usage_count'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                
        except Exception as e:
            logger.error(f"获取标签失败: {e}")
            return None
    
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """根据名称获取标签
        
        Args:
            name: 标签名称
            
        Returns:
            Optional[Tag]: 标签对象
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM tags WHERE name = ?", (name,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return Tag(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    color=row['color'],
                    category=row['category'],
                    usage_count=row['usage_count'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                
        except Exception as e:
            logger.error(f"获取标签失败: {e}")
            return None
    
    def list_tags(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[Tag]:
        """获取标签列表
        
        Args:
            category: 标签分类过滤
            limit: 限制数量
            
        Returns:
            List[Tag]: 标签列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM tags"
                params = []
                
                if category:
                    query += " WHERE category = ?"
                    params.append(category)
                
                query += " ORDER BY usage_count DESC, name ASC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                tags = []
                for row in rows:
                    tags.append(Tag(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        color=row['color'],
                        category=row['category'],
                        usage_count=row['usage_count'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    ))
                
                return tags
                
        except Exception as e:
            logger.error(f"获取标签列表失败: {e}")
            return []
    
    def update_tag(self, tag_id: int, updates: Dict[str, Any]) -> Optional[Tag]:
        """更新标签
        
        Args:
            tag_id: 标签ID
            updates: 更新字段
            
        Returns:
            Optional[Tag]: 更新后的标签对象
        """
        try:
            if not updates:
                return self.get_tag_by_id(tag_id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                set_clauses = []
                params = []
                
                for field, value in updates.items():
                    if field in ['name', 'description', 'color', 'category']:
                        set_clauses.append(f"{field} = ?")
                        params.append(value)
                
                if not set_clauses:
                    return self.get_tag_by_id(tag_id)
                
                set_clauses.append("updated_at = ?")
                params.append(datetime.now())
                params.append(tag_id)
                
                query = f"UPDATE tags SET {', '.join(set_clauses)} WHERE id = ?"
                cursor.execute(query, params)
                
                if cursor.rowcount == 0:
                    return None
                
                conn.commit()
                return self.get_tag_by_id(tag_id)
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"标签名称 '{updates.get('name')}' 已存在")
            raise
        except Exception as e:
            logger.error(f"更新标签失败: {e}")
            raise
    
    def delete_tag(self, tag_id: int) -> bool:
        """删除标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 先获取标签名称
                cursor.execute("SELECT name FROM tags WHERE id = ?", (tag_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                tag_name = row[0]
                
                # 删除数据集标签关联
                cursor.execute("DELETE FROM dataset_tags WHERE tag_name = ?", (tag_name,))
                
                # 删除标签
                cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"标签已删除: {tag_name}")
                
                return success
                
        except Exception as e:
            logger.error(f"删除标签失败: {e}")
            return False
    
    def get_categories(self) -> List[TagCategory]:
        """获取标签分类列表
        
        Returns:
            List[TagCategory]: 分类列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT category, COUNT(*) as tag_count
                    FROM tags
                    WHERE category IS NOT NULL AND category != ''
                    GROUP BY category
                    ORDER BY tag_count DESC, category ASC
                """)
                rows = cursor.fetchall()
                
                categories = []
                for row in rows:
                    categories.append(TagCategory(
                        name=row['category'],
                        tag_count=row['tag_count']
                    ))
                
                return categories
                
        except Exception as e:
            logger.error(f"获取标签分类失败: {e}")
            return []
    
    def add_dataset_tags(self, dataset_id: str, tag_names: List[str]) -> None:
        """为数据集添加标签
        
        Args:
            dataset_id: 数据集ID
            tag_names: 标签名称列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for tag_name in tag_names:
                    # 确保标签存在，如果不存在则创建
                    cursor.execute("SELECT name FROM tags WHERE name = ?", (tag_name,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO tags (name, description)
                            VALUES (?, ?)
                        """, (tag_name, f"自动创建的标签: {tag_name}"))
                    
                    # 添加数据集标签关联
                    cursor.execute("""
                        INSERT OR IGNORE INTO dataset_tags (dataset_id, tag_name)
                        VALUES (?, ?)
                    """, (dataset_id, tag_name))
                    
                    # 更新标签使用次数
                    cursor.execute("""
                        UPDATE tags SET usage_count = usage_count + 1, updated_at = ?
                        WHERE name = ?
                    """, (datetime.now(), tag_name))
                
                conn.commit()
                logger.debug(f"数据集标签已添加: {dataset_id} -> {tag_names}")
                
        except Exception as e:
            logger.error(f"添加数据集标签失败: {e}")
            raise
    
    def remove_dataset_tags(self, dataset_id: str, tag_names: List[str]) -> None:
        """移除数据集标签
        
        Args:
            dataset_id: 数据集ID
            tag_names: 标签名称列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for tag_name in tag_names:
                    # 移除数据集标签关联
                    cursor.execute("""
                        DELETE FROM dataset_tags
                        WHERE dataset_id = ? AND tag_name = ?
                    """, (dataset_id, tag_name))
                    
                    # 更新标签使用次数
                    cursor.execute("""
                        UPDATE tags SET usage_count = MAX(0, usage_count - 1), updated_at = ?
                        WHERE name = ?
                    """, (datetime.now(), tag_name))
                
                conn.commit()
                logger.debug(f"数据集标签已移除: {dataset_id} -> {tag_names}")
                
        except Exception as e:
            logger.error(f"移除数据集标签失败: {e}")
            raise
    
    def get_dataset_tags(self, dataset_id: str) -> List[str]:
        """获取数据集的标签
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            List[str]: 标签名称列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT tag_name FROM dataset_tags
                    WHERE dataset_id = ?
                    ORDER BY created_at ASC
                """, (dataset_id,))
                
                rows = cursor.fetchall()
                return [row[0] for row in rows]
                
        except Exception as e:
            logger.error(f"获取数据集标签失败: {e}")
            return []
    
    def update_dataset_tags(self, dataset_id: str, tag_names: List[str]) -> None:
        """更新数据集标签（替换所有标签）
        
        Args:
            dataset_id: 数据集ID
            tag_names: 新的标签名称列表
        """
        try:
            # 获取当前标签
            current_tags = set(self.get_dataset_tags(dataset_id))
            new_tags = set(tag_names)
            
            # 需要添加的标签
            tags_to_add = new_tags - current_tags
            # 需要移除的标签
            tags_to_remove = current_tags - new_tags
            
            if tags_to_remove:
                self.remove_dataset_tags(dataset_id, list(tags_to_remove))
            
            if tags_to_add:
                self.add_dataset_tags(dataset_id, list(tags_to_add))
            
            # 同步更新数据集数据库中的tags字段
            self._sync_dataset_tags_to_dataset_db(dataset_id, tag_names)
                
            logger.debug(f"数据集标签已更新: {dataset_id} -> {tag_names}")
            
        except Exception as e:
            logger.error(f"更新数据集标签失败: {e}")
            raise
    
    def _sync_dataset_tags_to_dataset_db(self, dataset_id: str, tag_names: List[str]) -> None:
        """同步标签到数据集数据库
        
        Args:
            dataset_id: 数据集ID
            tag_names: 标签名称列表
        """
        try:
            import json
            from pathlib import Path
            
            # 数据集数据库路径
            dataset_db_path = self.db_path.parent / "datasets.db"
            
            if dataset_db_path.exists():
                with sqlite3.connect(dataset_db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 更新数据集表中的tags字段
                    tags_json = json.dumps(tag_names, ensure_ascii=False)
                    cursor.execute("""
                        UPDATE datasets 
                        SET tags = ?, updated_at = ?
                        WHERE id = ?
                    """, (tags_json, datetime.now(), dataset_id))
                    
                    conn.commit()
                    logger.debug(f"数据集数据库中的标签已同步: {dataset_id} -> {tag_names}")
            else:
                logger.warning(f"数据集数据库不存在: {dataset_db_path}")
                
        except Exception as e:
            logger.error(f"同步标签到数据集数据库失败: {e}")
            # 不抛出异常，避免影响主流程 