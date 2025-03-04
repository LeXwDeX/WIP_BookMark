from fastapi import FastAPI, UploadFile, HTTPException, Request
from bs4 import BeautifulSoup
from fastapi.responses import HTMLResponse
from reference_modules.openai_curl_client import chat_completion
from fastapi.staticfiles import StaticFiles
from reference_modules.web_scraper import WebScraper
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import os

# 全局变量存储书签数据
bookmarks = []

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Upload bookmarks file
@app.post("/upload/")
async def upload_bookmarks(file: UploadFile):
    global bookmarks
    if not file.filename.endswith(".html"):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an HTML file.")
    content = await file.read()
    # Save the file temporarily
    with open(f"temp/{file.filename}", "wb") as f:
        f.write(content)
    # Parse the bookmark file
    bookmarks = parse_bookmarks(content)
    # Skip AI processing during upload; only parse bookmarks
    return {"filename": file.filename, "bookmarks": bookmarks}

@app.get("/update-bookmark/")
async def update_bookmark(url: str):
    """Update a single bookmark's summary and tags."""
    ai_result = generate_ai_summary_and_tags(url)
    return ai_result

@app.post("/refresh-all/")
async def refresh_all():
    """Refresh summaries and tags for all bookmarks."""
    # Assuming bookmarks are stored in memory for simplicity
    global bookmarks
    if not bookmarks:
        return {"error": "No bookmarks available to refresh."}
    updated_bookmarks = []
    for bookmark in bookmarks:
        ai_result = generate_ai_summary_and_tags(bookmark["url"])
        bookmark.update(ai_result)
        updated_bookmarks.append(bookmark)
    return {"bookmarks": updated_bookmarks}

def generate_ai_summary_and_tags(url: str):
    """Generate AI summary and tags for a given URL."""
    api_base = "https://one-api.ycgame.com/v1"
    api_key = "sk-JkjLOSoqsqE8A6XL5cDb428908Cd4aD48bF329Dd1a146395"
    model = "gpt-4o-mini"
    # Fetch website content using WebScraper
    scraper = WebScraper()
    content = scraper.get_url(url)

    if "Failed to fetch URL" in content or "No meaningful content extracted" in content:
        return {"summary": "无法生成摘要", "tags": []}

    # Truncate content to avoid exceeding API limits
    max_length = 100000
    truncated_content = content[:max_length]
    if len(content) > max_length:
        truncated_content += "\n\n(Note: Content was truncated due to size limitations.)"
    # Step 1: Generate summary
    summary_message = [{"role": "user", "content": f"请为以下内容生成摘要：\n{truncated_content}"}]
    try:
        summary_response = chat_completion(api_base, api_key, model, summary_message)
        summary = summary_response.strip() if summary_response else "无法生成摘要"
    except Exception:
        summary = "无法生成摘要"

    # Step 2: Generate tags
    tags_message = [{"role": "user", "content": f"请为以下内容生成1到5个最重要的文字标签（用逗号隔开）：\n{truncated_content}"}]
    try:
        tags_response = chat_completion(api_base, api_key, model, tags_message)
        tags = tags_response.strip().split(",") if tags_response else []
    except Exception:
        tags = []

    return {"summary": summary, "tags": tags}

def parse_bookmarks(content: bytes):
    """Parse the uploaded bookmark file and extract title and URL."""
    soup = BeautifulSoup(content, "html.parser")
    bookmarks = []
    for link in soup.find_all("a"):
        title = link.get_text()
        url = link.get("href")
        if title and url:
            bookmarks.append({"title": title, "url": url})
    return bookmarks
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
