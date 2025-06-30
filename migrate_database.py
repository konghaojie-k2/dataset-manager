#!/usr/bin/env python3
"""数据库迁移脚本 - 添加版本控制字段"""

import sqlite3
from pathlib import Path
from loguru import logger

def migrate_database():
    """迁移数据库，添加版本控制字段"""
    
    # 数据库路径
    db_path = Path("metadata/datasets.db")
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print(f"🔄 开始迁移数据库: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 检查是否已经有版本控制字段
            cursor.execute("PRAGMA table_info(datasets)")
            columns = [row[1] for row in cursor.fetchall()]
            
            print(f"📋 当前表字段: {columns}")
            
            # 需要添加的版本控制字段
            version_fields = [
                ('file_hash', 'TEXT'),
                ('content_hash', 'TEXT'),
                ('version', 'TEXT DEFAULT "1.0"'),
                ('parent_version_id', 'TEXT'),
                ('version_type', 'TEXT DEFAULT "original"'),
                ('version_notes', 'TEXT')
            ]
            
            # 添加缺失的字段
            for field_name, field_type in version_fields:
                if field_name not in columns:
                    print(f"➕ 添加字段: {field_name} {field_type}")
                    cursor.execute(f"ALTER TABLE datasets ADD COLUMN {field_name} {field_type}")
                else:
                    print(f"✅ 字段已存在: {field_name}")
            
            # 提交更改
            conn.commit()
            
            # 验证更改
            cursor.execute("PRAGMA table_info(datasets)")
            new_columns = [row[1] for row in cursor.fetchall()]
            
            print(f"📋 更新后表字段: {new_columns}")
            
            # 更新现有数据的默认值
            print("🔄 更新现有数据的默认值...")
            cursor.execute("""
                UPDATE datasets 
                SET version = '1.0', version_type = 'original' 
                WHERE version IS NULL OR version_type IS NULL
            """)
            
            updated_rows = cursor.rowcount
            print(f"✅ 更新了 {updated_rows} 行数据")
            
            conn.commit()
            
        print("✅ 数据库迁移完成！")
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        logger.error(f"数据库迁移失败: {e}")

if __name__ == "__main__":
    migrate_database() 