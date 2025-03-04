from fastapi import FastAPI, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import os

from models.bookmark import Bookmark, BookmarkCollection
from services.bookmark_parser import BookmarkParser
from services.ai_service import AIService

app = FastAPI(title="浏览器书签工具")

# 配置静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# OpenAI API配置
API_BASE = "https://one-api.ycgame.com/v1"
API_KEY = "sk-JkjLOSoqsqE8A6XL5cDb428908Cd4aD48bF329Dd1a146395"
MODEL = "gpt-4o-mini"

# 全局变量
bookmark_collection: Optional[BookmarkCollection] = None
ai_service = AIService(API_BASE, API_KEY, MODEL)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """渲染主页"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_bookmarks(file: UploadFile):
    """上传并解析书签文件"""
    global bookmark_collection
    
    if not file.filename.endswith(".html"):
        raise HTTPException(status_code=400, detail="请上传HTML格式的书签文件")
    
    content = await file.read()
    # 保存文件到临时目录
    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)
    
    # 解析书签文件
    bookmark_collection = BookmarkParser.parse_html_content(content)
    if not bookmark_collection:
        raise HTTPException(status_code=400, detail="书签文件解析失败")
    
    # 返回展平的书签列表用于显示
    bookmarks = BookmarkParser.flatten_bookmarks(bookmark_collection)
    return {"filename": file.filename, "bookmarks": [bookmark.dict() for bookmark in bookmarks]}

@app.get("/bookmarks/")
async def get_bookmarks():
    """获取所有书签"""
    if not bookmark_collection:
        raise HTTPException(status_code=404, detail="未上传书签文件")
    
    bookmarks = BookmarkParser.flatten_bookmarks(bookmark_collection)
    return {"bookmarks": [bookmark.dict() for bookmark in bookmarks]}

@app.get("/bookmarks/{bookmark_id}")
async def get_bookmark(bookmark_id: str):
    """获取单个书签详情"""
    if not bookmark_collection:
        raise HTTPException(status_code=404, detail="未上传书签文件")
    
    bookmark = bookmark_collection.find_bookmark_by_id(bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="书签不存在")
    
    return bookmark.dict()

@app.get("/bookmarks/{bookmark_id}/update")
async def update_bookmark(bookmark_id: str):
    """更新单个书签的AI摘要和标签"""
    if not bookmark_collection:
        raise HTTPException(status_code=404, detail="未上传书签文件")
    
    bookmark = bookmark_collection.find_bookmark_by_id(bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="书签不存在")
    
    # 生成AI摘要和标签
    summary, tags = ai_service.process_url(bookmark.url)
    bookmark.summary = summary
    bookmark.tags = tags
    
    return bookmark.dict()

@app.post("/bookmarks/refresh-all")
async def refresh_all_bookmarks():
    """刷新所有书签的AI摘要和标签"""
    if not bookmark_collection:
        raise HTTPException(status_code=404, detail="未上传书签文件")
    
    bookmarks = BookmarkParser.flatten_bookmarks(bookmark_collection)
    updated_bookmarks = []
    
    for bookmark in bookmarks:
        summary, tags = ai_service.process_url(bookmark.url)
        bookmark.summary = summary
        bookmark.tags = tags
        updated_bookmarks.append(bookmark.dict())
    
    return {"bookmarks": updated_bookmarks}

@app.get("/search/")
async def search_bookmarks(query: str):
    """搜索书签"""
    if not bookmark_collection:
        raise HTTPException(status_code=404, detail="未上传书签文件")
    
    results = bookmark_collection.search_bookmarks(query)
    return {"bookmarks": [bookmark.dict() for bookmark in results]}