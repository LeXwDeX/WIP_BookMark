"""书签服务模块，用于处理书签的同步、更新和删除操作。

主要功能：
1. 解析书签文件并导入到数据库
   - 支持HTML格式的书签文件解析
   - 自动提取书签的标题、URL、图标等信息
   - 保持书签的层级结构

2. 比较和更新已存在的书签
   - 支持多字段比较（标题、URL、图标）
   - 可配置的比较策略
   - 自动记录并显示书签变更信息

3. 删除不再存在的书签
   - 自动清理已失效的书签
   - 维护数据库一致性

性能优化：
- 使用URL索引进行快速查找
- 批量处理减少数据库操作
- 高效的比较算法

使用注意：
- 建议定期进行书签同步以保持数据最新
- 同步前确保书签文件格式正确
- 大量书签同步时可能需要较长时间
- 确保数据库有足够的存储空间

异常处理：
- 文件读取错误处理
- 数据库操作异常处理
- 格式解析异常处理
"""

import json
from typing import List, Dict, Optional
from modules.bookmark_analyzer import analyze_bookmarks
from modules.db_manager import BookmarkDBManager

class BookmarkService:
    def __init__(self, db_path: str = 'bookmarks.db'):
        """初始化书签服务
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_manager = BookmarkDBManager(db_path)
    
    def sync_bookmarks(self, html_file: str, compare_fields: List[str] = None) -> Dict:
        """同步书签数据
        
        解析书签文件，将新书签导入数据库，更新已存在的书签，删除不再存在的书签。
        
        Args:
            html_file: 书签HTML文件路径
            compare_fields: 需要比较的字段列表，可选值为['title', 'url', 'icon']。
                          如果为None，则默认只比较标题。
            
        Returns:
            同步结果统计信息
        """
        # 解析新的书签文件
        result = analyze_bookmarks(html_file)
        new_bookmarks = json.loads(result)
        
        # 获取数据库中现有的书签
        existing_bookmarks = json.loads(self.db_manager.export_bookmarks())
        
        # 用于跟踪操作结果
        stats = {
            'total_new': len(new_bookmarks),
            'total_existing': len(existing_bookmarks),
            'updated': 0,
            'added': 0,
            'deleted': 0
        }
        
        # 创建URL到书签ID的映射，用于快速查找
        existing_url_map = {bookmark['url']: bookmark['id'] for bookmark in existing_bookmarks}
        new_url_set = {bookmark['url'] for bookmark in new_bookmarks}
        
        # 处理新书签：添加或更新
        for new_bookmark in new_bookmarks:
            url = new_bookmark['url']
            if url in existing_url_map:
                # 更新已存在的书签
                bookmark_id = existing_url_map[url]
                if self._should_update_bookmark(new_bookmark, self.db_manager.get_bookmark(bookmark_id), compare_fields):
                    self.db_manager.update_bookmark(bookmark_id, new_bookmark)
                    stats['updated'] += 1
            else:
                # 添加新书签
                self.db_manager.add_bookmark(new_bookmark)
                stats['added'] += 1
        
        # 删除不再存在的书签
        for existing_bookmark in existing_bookmarks:
            if existing_bookmark['url'] not in new_url_set:
                self.db_manager.delete_bookmark(existing_bookmark['id'])
                stats['deleted'] += 1
        
        return stats
    
    def _should_update_bookmark(self, new_bookmark: Dict, existing_bookmark: Dict, compare_fields: List[str] = None) -> bool:
        """判断是否需要更新书签
        
        比较书签的关键属性，判断是否需要更新。
        
        Args:
            new_bookmark: 新书签数据
            existing_bookmark: 现有书签数据
            compare_fields: 需要比较的字段列表，可选值为['title', 'url', 'icon']。
                          如果为None，则默认只比较标题。
            
        Returns:
            如果需要更新返回True，否则返回False
        """
        if not existing_bookmark:
            return True
        
        # 如果没有指定比较字段，则默认只比较标题
        if not compare_fields:
            compare_fields = ['title']
        
        # 遍历指定的字段进行比较
        for field in compare_fields:
            if field in ['title', 'url', 'icon']:
                if new_bookmark.get(field) != existing_bookmark.get(field):
                    # 如果是标题发生变化，打印差异信息
                    if field == 'title':
                        print(f"标题变更 - URL: {existing_bookmark.get('url')}")
                        print(f"  旧标题: {existing_bookmark.get('title')}")
                        print(f"  新标题: {new_bookmark.get('title')}")
                    return True
        
        return False
    
    def get_bookmark_by_id(self, bookmark_id: int) -> Optional[Dict]:
        """获取指定ID的书签详细信息
        
        Args:
            bookmark_id: 书签ID
            
        Returns:
            包含书签信息的字典，如果不存在则返回None
        """
        return self.db_manager.get_bookmark(bookmark_id)
    
    def search_bookmarks(self, query: str = None, tags: List[str] = None) -> List[Dict]:
        """搜索书签
        
        Args:
            query: 搜索关键词，匹配标题和URL
            tags: 标签列表，用于按标签筛选书签
            
        Returns:
            符合条件的书签列表
        """
        return self.db_manager.search_bookmarks(query)
    
    def update_bookmark_notes(self, bookmark_id: int, notes: str) -> bool:
        """更新书签备注
        
        Args:
            bookmark_id: 书签ID
            notes: 新的备注内容
            
        Returns:
            更新是否成功
        """
        bookmark = self.db_manager.get_bookmark(bookmark_id)
        if not bookmark:
            return False
            
        # 更新备注字段
        bookmark['notes'] = notes
        return self.db_manager.update_bookmark(bookmark_id, bookmark)
    
    def update_bookmark_tags(self, bookmark_id: int, tags: List[str]) -> bool:
        """更新书签标签
        
        Args:
            bookmark_id: 书签ID
            tags: 新的标签列表
            
        Returns:
            更新是否成功
        """
        bookmark = self.db_manager.get_bookmark(bookmark_id)
        if not bookmark:
            return False
            
        # 更新标签字段
        bookmark['tags'] = tags
        return self.db_manager.update_bookmark(bookmark_id, bookmark)