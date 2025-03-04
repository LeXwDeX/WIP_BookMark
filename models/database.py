from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# 创建数据库引擎，使用项目根目录下的SQLite数据库文件
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bookmarks.db')
engine = create_engine(f'sqlite:///{db_path}')

# 创建基类
Base = declarative_base()

class DBBookmark(Base):
    """书签数据库模型"""
    __tablename__ = 'bookmarks'

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    original_title = Column(String, nullable=True)  # 存储网站的原始标题
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    folder_path = Column(String, default='/')
    last_visited = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, nullable=True)

    # 关联关系
    tags = relationship('DBBookmarkTag', back_populates='bookmark', cascade='all, delete-orphan')
    summary = relationship('DBBookmarkSummary', back_populates='bookmark', uselist=False, cascade='all, delete-orphan')

class DBBookmarkTag(Base):
    """书签标签数据库模型"""
    __tablename__ = 'bookmark_tags'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    bookmark_id = Column(String, ForeignKey('bookmarks.id'))

    # 关联关系
    bookmark = relationship('DBBookmark', back_populates='tags')

class DBBookmarkSummary(Base):
    """书签摘要数据库模型"""
    __tablename__ = 'bookmark_summaries'

    id = Column(String, primary_key=True)
    content = Column(String, nullable=False)
    generated_at = Column(DateTime, default=datetime.now)
    error_message = Column(String, nullable=True)
    bookmark_id = Column(String, ForeignKey('bookmarks.id'))

    # 关联关系
    bookmark = relationship('DBBookmark', back_populates='summary')

# 创建所有表
Base.metadata.create_all(engine)

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()