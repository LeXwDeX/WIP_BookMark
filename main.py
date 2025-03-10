from fastapi import FastAPI, UploadFile, HTTPException, Request
from bs4 import BeautifulSoup
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.ai_service import AIService
from services.bookmark_service import BookmarkService
import os

app = FastAPI()

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置模板目录
templates = Jinja2Templates(directory="templates")

# 初始化服务
bookmark_service = BookmarkService()
ai_service = AIService()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/bookmarks")
async def list_bookmarks(query: str = None):
    return bookmark_service.search_bookmarks(query)

@app.get("/api/bookmarks/{bookmark_id}")
async def get_bookmark(bookmark_id: int):
    bookmark = bookmark_service.get_bookmark_by_id(bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="书签不存在")
    return bookmark

@app.post("/api/bookmarks/upload")
async def upload_bookmarks(file: UploadFile):
    # 保存上传的文件
    file_path = f"uploads/{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 同步书签
    try:
        stats = bookmark_service.sync_bookmarks(file_path)
        return {"message": "上传成功", "stats": stats}
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

@app.put("/api/bookmarks/{bookmark_id}/summary")
async def update_bookmark_summary(bookmark_id: int, summary: dict):
    success = bookmark_service.update_bookmark_summary(bookmark_id, summary.get("summary", ""))
    if not success:
        raise HTTPException(status_code=404, detail="书签不存在")
    return {"message": "更新成功"}

@app.get("/api/bookmarks/{bookmark_id}/ai-update")
async def update_bookmark_ai(bookmark_id: int):
    print(f"开始AI更新书签 - ID: {bookmark_id}")
    bookmark = bookmark_service.get_bookmark_by_id(bookmark_id)
    if not bookmark:
        print(f"书签不存在 - ID: {bookmark_id}")
        raise HTTPException(status_code=404, detail="书签不存在")
    
    # 调用AI服务生成摘要和标签
    try:
        print(f"开始调用AI服务分析URL - ID: {bookmark_id}, URL: {bookmark['url']}")
        summary, tags = await ai_service.analyze_url(bookmark["url"])
        print(f"AI服务分析完成 - ID: {bookmark_id}, 摘要长度: {len(summary)}, 标签数量: {len(tags)}")
        
        bookmark["summary"] = summary
        bookmark["tags"] = tags
        
        print(f"开始更新书签摘要和标签 - ID: {bookmark_id}")
        summary_success = bookmark_service.update_bookmark_summary(bookmark_id, summary)
        tags_success = bookmark_service.update_bookmark_tags(bookmark_id, tags)
        
        if not summary_success or not tags_success:
            print(f"更新失败 - ID: {bookmark_id}, 摘要更新: {summary_success}, 标签更新: {tags_success}")
            raise HTTPException(status_code=500, detail="更新书签失败")
            
        print(f"AI更新成功 - ID: {bookmark_id}")
        return {"message": "AI更新成功", "summary": summary, "tags": tags}
    except Exception as e:
        print(f"AI更新异常 - ID: {bookmark_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
