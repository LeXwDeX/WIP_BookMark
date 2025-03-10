from typing import Optional, List, Dict
from datetime import datetime

class BookmarkSummary:
    """书签摘要模型"""
    def __init__(self, content: str, error_message: Optional[str] = None):
        self.content = content
        self.error_message = error_message

class BookmarkTag:
    """书签标签模型"""
    def __init__(self, name: str):
        self.name = name

class Bookmark:
    """书签模型，包含书签的完整信息"""
    def __init__(self, 
                 title: str, 
                 url: str, 
                 id: Optional[int] = None,
                 icon: Optional[str] = None, 
                 add_date: Optional[str] = None,
                 summary: Optional[str] = None, 
                 tags: Optional[List[str]] = None,
                 last_updated: Optional[str] = None):
        """初始化书签对象
        
        Args:
            title: 书签标题
            url: 书签URL
            id: 书签ID，数据库中的唯一标识
            icon: 书签图标URL
            add_date: 添加日期
            summary: 书签内容摘要
            tags: 标签列表
            last_updated: 最后更新时间
        """
        self.id = id
        self.title = title
        self.url = url
        self.icon = icon
        self.add_date = add_date or datetime.now().isoformat()
        self.summary = summary or ""
        self.tags = tags or []
        self.last_updated = last_updated or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """将书签对象转换为字典
        
        Returns:
            包含书签信息的字典
        """
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'icon': self.icon,
            'add_date': self.add_date,
            'summary': self.summary,
            'tags': self.tags,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Bookmark':
        """从字典创建书签对象
        
        Args:
            data: 包含书签信息的字典
            
        Returns:
            Bookmark对象
        """
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            url=data.get('url', ''),
            icon=data.get('icon'),
            add_date=data.get('add_date'),
            summary=data.get('summary'),
            tags=data.get('tags', []),
            last_updated=data.get('last_updated')
        )
    
    def update_summary(self, summary: str) -> None:
        """更新书签摘要
        
        Args:
            summary: 新的摘要内容
        """
        self.summary = summary
        self.last_updated = datetime.now().isoformat()
    
    def update_tags(self, tags: List[str]) -> None:
        """更新书签标签
        
        Args:
            tags: 新的标签列表
        """
        self.tags = tags
        self.last_updated = datetime.now().isoformat()