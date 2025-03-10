from fastapi import FastAPI, UploadFile, HTTPException, Request
from bs4 import BeautifulSoup
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.ai_service import AIService
from services.bookmark_service import BookmarkService
import os

app = FastAPI()
