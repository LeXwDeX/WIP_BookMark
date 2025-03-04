import chardet
import cloudscraper
import requests
from typing import Optional, Any

FULL_TEMPLATE = """
TITLE: {title}
AUTHORS: {authors}
PUBLISH DATE: {publish_date}
TOP_IMAGE_URL: {top_image}
TEXT:

{text}
"""

class WebScraper:
    @staticmethod
    def get_url(url: str, user_agent: Optional[str] = None) -> str:
        """
        Fetch URL and return the contents as a string.
        """
        print(f"[WebScraper] 开始获取URL: {url}")
        scraper = cloudscraper.create_scraper()
        headers = {
            "User-Agent": user_agent or scraper.headers["User-Agent"]
        }
        print(f"[WebScraper] 使用User-Agent: {headers['User-Agent']}")


        try:
            # Attempt to fetch the URL
            print("[WebScraper] 正在发送HTTP请求...")
            response = scraper.get(url, headers=headers, timeout=(5, 10))
            response.raise_for_status()
            print(f"[WebScraper] 成功获取响应，状态码: {response.status_code}")

        except requests.exceptions.RequestException as e:
            return f"Failed to fetch URL: {e}"

        # Detect encoding using chardet
        print("[WebScraper] 正在检测页面编码...")
        detected_encoding = chardet.detect(response.content)
        encoding = detected_encoding["encoding"]
        print(f"[WebScraper] 检测到编码: {encoding}")
        if encoding:
            try:
                print(f"[WebScraper] 尝试使用 {encoding} 解码内容...")
                content = response.content.decode(encoding)
                print("[WebScraper] 内容解码成功")
            except (UnicodeDecodeError, TypeError) as e:
                print(f"[WebScraper] 解码失败: {e}，使用response.text作为备选")
                content = response.text
        else:
            print("[WebScraper] 未检测到编码，使用response.text")
            content = response.text

        print("[WebScraper] 开始提取页面内容...")
        extracted_content = WebScraper.extract_content(content)

        if not extracted_content["plain_text"] or not extracted_content["plain_text"].strip():
            print("[WebScraper] 警告：未能提取到有效内容")
            return "No meaningful content extracted."
        
        print("[WebScraper] 内容提取完成")


        return FULL_TEMPLATE.format(
            title=extracted_content["title"],
            authors=extracted_content["byline"],
            publish_date=extracted_content["date"],
            top_image="",
            text=extracted_content["plain_text"] or "",
        )

    @staticmethod
    def extract_content(html: str) -> dict[str, Any]:
        """
        Extract main content from HTML using BeautifulSoup.
        """
        from bs4 import BeautifulSoup
        print("[WebScraper] 开始解析HTML...")
        soup = BeautifulSoup(html, "html.parser")
        print("[WebScraper] HTML解析完成")


        # Extract title
        title = soup.title.string if soup.title else "No Title"

        # Extract text content
        # Extract main content from body
        body_content = soup.body
        plain_text = ""
        if body_content:
            seen_texts = set()
            plain_text = "\n".join(
                element.get_text(strip=True)
                for element in body_content.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "span", "div"])
                if (text := element.get_text(strip=True)) and text not in seen_texts and not seen_texts.add(text)
            )

        # Extract authors
        authors = soup.find_all("meta", {"name": "author"})
        authors_list = [author.get("content", "Unknown Author") for author in authors]

        # Extract publish date
        publish_date_meta = soup.find("meta", {"name": "publish_date"})
        publish_date = publish_date_meta.get("content", "Unknown Date") if publish_date_meta else "Unknown Date"

        return {
            "title": title,
            "byline": ", ".join(authors_list) if authors_list else "Unknown Author",
            "date": publish_date,
            "plain_text": plain_text,
        }

if __name__ == "__main__":
    # Example usage for manual testing
    test_url = "https://www.fantasynamegenerators.com/"
    scraper = WebScraper()
    result = scraper.get_url(test_url)
    print(result)
