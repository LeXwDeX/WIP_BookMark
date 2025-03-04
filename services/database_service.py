from sqlalchemy.orm import Session
from typing import List, Optional
from models.database import DBBookmark, DBBookmarkTag, DBBookmarkSummary, get_db, SessionLocal
from models.bookmark import Bookmark, BookmarkTag, BookmarkSummary, BookmarkCollection
import uuid

class DatabaseService:
    """数据库服务类，处理书签的持久化操作"""

    @staticmethod
    def save_bookmark_collection(collection: BookmarkCollection) -> None:
        """保存整个书签集合到数据库"""
        with SessionLocal() as db:
            try:
                # 清空现有数据
                db.query(DBBookmark).delete()
                db.commit()

                def save_bookmarks_in_folder(folder):
                    for bookmark in folder.bookmarks:
                        # 创建书签记录
                        db_bookmark = DBBookmark(
                            id=bookmark.id,
                            title=bookmark.title,
                            url=bookmark.url,
                            created_at=bookmark.created_at,
                            folder_path=bookmark.folder_path,
                            last_visited=bookmark.last_visited,
                            last_updated=bookmark.last_updated
                        )

                        # 保存标签
                        if bookmark.tags:
                            for tag in bookmark.tags:
                                db_tag = DBBookmarkTag(
                                    id=str(uuid.uuid4()),
                                    name=tag.name,
                                    created_at=tag.created_at,
                                    bookmark_id=bookmark.id
                                )
                                db_bookmark.tags.append(db_tag)

                        # 保存摘要
                        if bookmark.summary:
                            db_summary = DBBookmarkSummary(
                                id=str(uuid.uuid4()),
                                content=bookmark.summary.content,
                                generated_at=bookmark.summary.generated_at,
                                error_message=bookmark.summary.error_message,
                                bookmark_id=bookmark.id
                            )
                            db_bookmark.summary = db_summary

                        db.add(db_bookmark)

                    # 递归处理子文件夹
                    for subfolder in folder.subfolders:
                        save_bookmarks_in_folder(subfolder)

                # 从根文件夹开始保存所有书签
                save_bookmarks_in_folder(collection.root_folder)
                db.commit()
            except Exception as e:
                db.rollback()
                raise e

    @staticmethod
    def load_bookmark_collection() -> Optional[BookmarkCollection]:
        """从数据库加载书签集合"""
        with SessionLocal() as db:
            try:
                collection = BookmarkCollection(source_file="database")

                # 查询所有书签
                bookmarks = db.query(DBBookmark).all()
                for db_bookmark in bookmarks:
                    # 转换标签
                    tags = [BookmarkTag(
                        name=tag.name,
                        created_at=tag.created_at
                    ) for tag in db_bookmark.tags]

                    # 转换摘要
                    summary = None
                    if db_bookmark.summary:
                        summary = BookmarkSummary(
                            content=db_bookmark.summary.content,
                            generated_at=db_bookmark.summary.generated_at,
                            error_message=db_bookmark.summary.error_message
                        )

                    # 创建书签对象
                    bookmark = Bookmark(
                        id=db_bookmark.id,
                        title=db_bookmark.title,
                        url=db_bookmark.url,
                        created_at=db_bookmark.created_at,
                        folder_path=db_bookmark.folder_path,
                        tags=tags,
                        summary=summary,
                        last_visited=db_bookmark.last_visited,
                        last_updated=db_bookmark.last_updated
                    )

                    # 添加到集合中
                    collection.add_bookmark(bookmark, db_bookmark.folder_path)

                return collection
            except Exception as e:
                print(f"Error loading bookmarks: {e}")
                return None