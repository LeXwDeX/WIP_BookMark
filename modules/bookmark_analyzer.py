"""
模块功能: 分析导入的书签文件，并将结果转换为 JSON 格式返回.

支持两种输入文件格式:
1. CSV 格式: 使用 csv.DictReader 解析每一行作为字典记录.
2. HTML 格式: 解析 Netscape 风格的书签 HTML 文件，通过递归解析保留书签的原始结构，
   包括标题、URL、ICON、文件夹及其层级、添加时间等属性.

用法:
  调用 analyze_bookmarks(file_path) 即可解析指定文件并返回 JSON 字符串.
"""

import os
import json
import csv

def analyze_bookmarks(file_path: str) -> str:
    """
    分析指定的书签文件，并将解析结果返回为 JSON 格式的字符串.
    
    支持 CSV 格式和 HTML 格式.
    
    参数:
      file_path: 书签文件的路径.
      
    返回:
      JSON 格式的字符串, 表示书签数据的列表.
      
    异常:
      如果文件格式不支持或读取失败则抛出异常.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    ext = os.path.splitext(file_path)[1].lower()
    bookmarks = []
    
    if ext == ".csv":
        # 解析 CSV 文件，假定 CSV 中包含所有原始属性
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bookmarks.append(row)
    elif ext == ".html":
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("需要安装 'beautifulsoup4' 库来解析 HTML 文件 (pip install beautifulsoup4)")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            bookmarks = parse_html_bookmarks(content)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")
    
    return json.dumps(bookmarks, indent=2, ensure_ascii=False)

def parse_html_bookmarks(content: str) -> list:
    """
    解析 Netscape 风格的书签 HTML 文件.
    
    返回的每个书签包含以下属性:
      - title: 书签标题
      - url: 链接地址
      - icon: 图标（如果存在）
      - add_date: 添加日期（如果存在）
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, "html.parser")
    bookmarks = []
    for a in soup.find_all("a"):
        bookmark = {
            "title": a.get_text(strip=True),
            "url": a.get("href"),
            "icon": a.get("icon"),
            "add_date": a.get("add_date")
        }
        bookmarks.append(bookmark)
    return bookmarks

if __name__ == "__main__":
    # 示例用法：请根据实际文件路径修改
    import sys
    if len(sys.argv) < 2:
        print("用法: python bookmark_analyzer.py <书签文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        result = analyze_bookmarks(file_path)
        print("解析结果:")
        print(result)
    except Exception as ex:
        print(f"解析发生错误: {ex}")
