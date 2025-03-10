"""SQLite数据库管理模块，用于存储和管理书签数据。

提供以下功能：
1. 数据库初始化和表结构创建
2. 书签的增删改查操作
3. 文件夹层级关系管理
4. 数据导入导出
"""

import os
import sqlite3
import json
from typing import List, Dict, Optional, Union

class BookmarkDBManager:
    def __init__(self, db_path: str = 'bookmarks.db'):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库，创建必要的表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建书签表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                icon TEXT,
                add_date TEXT,
                summary TEXT,
                tags TEXT,
                last_updated TEXT
            )
            """)
            
            conn.commit()
    
    def add_bookmark(self, bookmark_data: Dict) -> int:
        """添加新书签
        
        Args:
            bookmark_data: 包含书签信息的字典
        
        Returns:
            新添加书签的ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 插入书签基本信息
            cursor.execute("""
            INSERT INTO bookmarks (title, url, icon, add_date, summary, tags)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                bookmark_data['title'],
                bookmark_data['url'],
                bookmark_data.get('icon'),
                bookmark_data.get('add_date'),
                bookmark_data.get('summary'),
                json.dumps(bookmark_data.get('tags', []))
            ))
            
            bookmark_id = cursor.lastrowid
            conn.commit()
            return bookmark_id
    
    def _process_folders(self, cursor, bookmark_id: int, folder_path: List[str]):
        """处理书签的文件夹层级关系
        
        Args:
            cursor: 数据库游标
            bookmark_id: 书签ID
            folder_path: 文件夹路径列表
        """
        parent_id = None
        for folder_name in folder_path:
            # 查找或创建文件夹
            cursor.execute(
                "SELECT id FROM folders WHERE name = ? AND parent_id IS ?",
                (folder_name, parent_id)
            )
            result = cursor.fetchone()
            
            if result:
                folder_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO folders (name, parent_id) VALUES (?, ?)",
                    (folder_name, parent_id)
                )
                folder_id = cursor.lastrowid
            
            parent_id = folder_id
        
        # 关联书签和最后一级文件夹
        if parent_id:
            cursor.execute(
                "INSERT INTO bookmark_folders (bookmark_id, folder_id) VALUES (?, ?)",
                (bookmark_id, parent_id)
            )
    
    def get_bookmark(self, bookmark_id: int) -> Optional[Dict]:
        """获取指定书签的详细信息
        
        Args:
            bookmark_id: 书签ID
        
        Returns:
            包含书签信息的字典，如果不存在则返回None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM bookmarks WHERE id = ?
            """, (bookmark_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'id': row[0],
                'title': row[1],
                'url': row[2],
                'icon': row[3],
                'add_date': row[4],
                'summary': row[5],
                'tags': json.loads(row[6]) if row[6] else [],
                'last_updated': row[7]
            }
    
    def update_bookmark(self, bookmark_id: int, update_data: Dict) -> bool:
        """更新书签信息
        
        Args:
            bookmark_id: 书签ID
            update_data: 需要更新的字段和值
        
        Returns:
            更新是否成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 构建更新语句
            update_fields = []
            params = []
            for key, value in update_data.items():
                if key != 'id':
                    if key == 'tags' and isinstance(value, list):
                        value = json.dumps(value)
                    update_fields.append(f"{key} = ?")
                    params.append(value)
            
            if not update_fields:
                return False
            
            # 更新书签基本信息
            params.append(bookmark_id)
            cursor.execute(
                f"UPDATE bookmarks SET {', '.join(update_fields)} WHERE id = ?",
                params
            )
            
            conn.commit()
            return True
    
    def delete_bookmark(self, bookmark_id: int) -> bool:
        """删除指定书签
        
        Args:
            bookmark_id: 书签ID
        
        Returns:
            删除是否成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM bookmarks WHERE id = ?",
                (bookmark_id,)
            )
            
            conn.commit()
            return cursor.rowcount > 0
    
    def search_bookmarks(self, query: str = None) -> List[Dict]:
        """搜索书签
        
        Args:
            query: 搜索关键词，匹配标题和URL
        
        Returns:
            符合条件的书签列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            sql = "SELECT * FROM bookmarks"
            params = []
            
            if query:
                sql += " WHERE title LIKE ? OR url LIKE ?"
                params.extend([f"%{query}%", f"%{query}%"])
            
            cursor.execute(sql, params)
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'icon': row[3],
                    'add_date': row[4],
                    'summary': row[5],
                    'tags': json.loads(row[6]) if row[6] else [],
                    'last_updated': row[7]
                })
            
            return results
    
    def import_bookmarks(self, bookmarks_json: Union[str, List[Dict]]):
        """导入书签数据
        
        Args:
            bookmarks_json: JSON字符串或书签数据列表
        """
        if isinstance(bookmarks_json, str):
            bookmarks = json.loads(bookmarks_json)
        else:
            bookmarks = bookmarks_json
        
        for bookmark in bookmarks:
            self.add_bookmark(bookmark)
    
    def export_bookmarks(self) -> str:
        """导出所有书签数据
        
        Returns:
            JSON格式的书签数据
        """
        bookmarks = self.search_bookmarks()
        return json.dumps(bookmarks, ensure_ascii=False, indent=2)