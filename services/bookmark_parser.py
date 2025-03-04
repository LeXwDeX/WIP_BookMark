from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime
import uuid
from models.bookmark import Bookmark, BookmarkCollection, BookmarkFolder

class BookmarkParser:
    """书签解析器，负责从HTML文件中解析书签数据"""

    @staticmethod
    def parse_html_content(content: bytes) -> BookmarkCollection:
        """解析书签HTML文件内容"""
        soup = BeautifulSoup(content, "html.parser")
        collection = BookmarkCollection(source_file="bookmarks.html")

        def parse_folder(dl_element, parent_path: str = "/") -> BookmarkFolder:
            folder = BookmarkFolder(path=parent_path, name="未命名文件夹")
            current_h3 = dl_element.find_previous_sibling("h3")
            if current_h3:
                folder.name = current_h3.get_text(strip=True)

            for element in dl_element.children:
                if element.name == "dt":
                    # 处理书签链接
                    link = element.find("a")
                    if link:
                        bookmark = Bookmark(
                            id=str(uuid.uuid4()),
                            title=link.get_text(strip=True),
                            url=link.get("href", ""),
                            folder_path=parent_path,
                            created_at=datetime.fromtimestamp(int(link.get("add_date", "0"))) if link.get("add_date") else datetime.now()
                        )
                        folder.bookmarks.append(bookmark)
                    # 处理子文件夹
                    sub_dl = element.find("dl")
                    if sub_dl:
                        sub_folder_path = f"{parent_path}{folder.name}/" if parent_path != "/" else f"/{folder.name}/"
                        subfolder = parse_folder(sub_dl, sub_folder_path)
                        folder.subfolders.append(subfolder)

            return folder

        # 查找根DL元素并开始解析
        root_dl = soup.find("dl")
        if root_dl:
            collection.root_folder = parse_folder(root_dl)

        return collection

    @staticmethod
    def parse_file(file_path: str) -> Optional[BookmarkCollection]:
        """从文件中解析书签"""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return BookmarkParser.parse_html_content(content)
        except Exception as e:
            print(f"Error parsing bookmark file: {e}")
            return None

    @staticmethod
    def flatten_bookmarks(collection: BookmarkCollection) -> list[Bookmark]:
        """将书签集合展平为列表"""
        bookmarks = []

        def traverse_folder(folder: BookmarkFolder):
            bookmarks.extend(folder.bookmarks)
            for subfolder in folder.subfolders:
                traverse_folder(subfolder)

        traverse_folder(collection.root_folder)
        return bookmarks