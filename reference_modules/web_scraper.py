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
        scraper = cloudscraper.create_scraper()
        headers = {
            "User-Agent": user_agent or scraper.headers["User-Agent"]
        }

        try:
            # Attempt to fetch the URL
            response = scraper.get(url, headers=headers, timeout=(5, 10))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f"Failed to fetch URL: {e}"

        # Detect encoding using chardet
        detected_encoding = chardet.detect(response.content)
        encoding = detected_encoding["encoding"]
        if encoding:
            try:
                content = response.content.decode(encoding)
            except (UnicodeDecodeError, TypeError):
                content = response.text
        else:
            content = response.text

        extracted_content = WebScraper.extract_content(content)

        if not extracted_content["plain_text"] or not extracted_content["plain_text"].strip():
            return "No meaningful content extracted."

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

        soup = BeautifulSoup(html, "html.parser")

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
