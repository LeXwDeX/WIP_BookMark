from typing import Dict, List, Optional, Tuple
from reference_modules.web_scraper import WebScraper
from reference_modules.openai_curl_client import chat_completion
from models.bookmark import BookmarkSummary, BookmarkTag

class AIService:
    """AI服务类，负责网页内容处理和AI摘要生成"""

    def __init__(self, api_base: str, api_key: str, model: str = "gpt-4o-mini"):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.web_scraper = WebScraper()

    def process_url(self, url: str) -> Tuple[Optional[BookmarkSummary], List[BookmarkTag]]:
        """处理URL，获取网页内容并生成AI摘要和标签"""
        # 获取网页内容
        content = self.web_scraper.get_url(url)

        if "Failed to fetch URL" in content or "No meaningful content extracted" in content:
            return BookmarkSummary(content="无法生成摘要", error_message=content), []

        # 截断内容以避免超出API限制
        max_length = 100000
        truncated_content = content[:max_length]
        if len(content) > max_length:
            truncated_content += "\n\n(Note: Content was truncated due to size limitations.)"

        # 生成摘要
        summary = self._generate_summary(truncated_content)
        # 生成标签
        tags = self._generate_tags(truncated_content)

        return summary, tags

    def _generate_summary(self, content: str) -> BookmarkSummary:
        """生成内容摘要"""
        try:
            summary_message = [{
                "role": "user", 
                "content": "请直接描述以下内容的主要内容和要点，不要添加'摘要'等标记词：\n" + content
            }]
            summary_response = chat_completion(self.api_base, self.api_key, self.model, summary_message)
            if summary_response and not summary_response.startswith("Error"):
                # 清理可能出现的标记文本
                cleaned_summary = summary_response.strip()
                cleaned_summary = cleaned_summary.replace("摘要：", "").replace("摘要:", "")
                return BookmarkSummary(content=cleaned_summary)
            return BookmarkSummary(content="无法生成摘要", error_message=summary_response)
        except Exception as e:
            return BookmarkSummary(content="无法生成摘要", error_message=str(e))

    def _generate_tags(self, content: str) -> List[BookmarkTag]:
        """生成内容标签"""
        try:
            tags_message = [{"role": "user", "content": f"请为以下内容生成1到5个最重要的文字标签（用逗号隔开）：\n{content}"}]
            tags_response = chat_completion(self.api_base, self.api_key, self.model, tags_message)
            if tags_response and not tags_response.startswith("Error"):
                return [BookmarkTag(name=tag.strip()) for tag in tags_response.strip().split(",") if tag.strip()]
            return []
        except Exception:
            return []

    @staticmethod
    def batch_process_urls(urls: List[str], api_base: str, api_key: str, model: str = "gpt-4o-mini") -> Dict[str, Tuple[Optional[BookmarkSummary], List[BookmarkTag]]]:
        """批量处理多个URL"""
        service = AIService(api_base, api_key, model)
        results = {}
        for url in urls:
            summary, tags = service.process_url(url)
            results[url] = (summary, tags)
        return results