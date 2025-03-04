from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class BookmarkTag(BaseModel):
    """书签标签模型"""
    name: str
    created_at: datetime = datetime.now()

class BookmarkSummary(BaseModel):
    """书签AI摘要模型"""
    content: str
    generated_at: datetime = datetime.now()
    error_message: Optional[str] = None

class Bookmark(BaseModel):
    """书签数据模型"""
    id: str  # 唯一标识符
    title: str  # 书签标题
    url: str  # 书签URL
    created_at: datetime = datetime.now()  # 创建时间
    folder_path: str = "/"  # 文件夹路径，默认为根目录
    tags: List[BookmarkTag] = []  # 标签列表
    summary: Optional[BookmarkSummary] = None  # AI生成的摘要
    last_visited: Optional[datetime] = None  # 最后访问时间
    last_updated: Optional[datetime] = None  # 最后更新时间

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BookmarkFolder(BaseModel):
    """书签文件夹模型"""
    path: str  # 文件夹路径
    name: str  # 文件夹名称
    parent_path: Optional[str] = None  # 父文件夹路径
    created_at: datetime = datetime.now()  # 创建时间
    bookmarks: List[Bookmark] = []  # 文件夹中的书签
    subfolders: List['BookmarkFolder'] = []  # 子文件夹

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BookmarkCollection(BaseModel):
    """书签集合模型，代表整个书签文件"""
    source_file: str  # 源文件名
    imported_at: datetime = datetime.now()  # 导入时间
    last_updated: datetime = datetime.now()  # 最后更新时间
    root_folder: BookmarkFolder = BookmarkFolder(path="/", name="根目录")  # 根文件夹

    def add_bookmark(self, bookmark: Bookmark, folder_path: str = "/") -> None:
        """添加书签到指定文件夹"""
        current_folder = self.root_folder
        if folder_path != "/":
            # TODO: 实现文件夹路径查找和创建逻辑
            pass
        current_folder.bookmarks.append(bookmark)

    def find_bookmark_by_id(self, bookmark_id: str) -> Optional[Bookmark]:
        """通过ID查找书签"""
        def search_folder(folder: BookmarkFolder) -> Optional[Bookmark]:
            # 在当前文件夹中查找
            for bookmark in folder.bookmarks:
                if bookmark.id == bookmark_id:
                    return bookmark
            # 递归查找子文件夹
            for subfolder in folder.subfolders:
                result = search_folder(subfolder)
                if result:
                    return result
            return None

        return search_folder(self.root_folder)

    def search_bookmarks(self, query: str) -> List[Bookmark]:
        """搜索书签（标题和URL）"""
        results: List[Bookmark] = []
        query = query.lower()

        def search_folder(folder: BookmarkFolder) -> None:
            for bookmark in folder.bookmarks:
                if query in bookmark.title.lower() or query in bookmark.url.lower():
                    results.append(bookmark)
            for subfolder in folder.subfolders:
                search_folder(subfolder)

        search_folder(self.root_folder)
        return results