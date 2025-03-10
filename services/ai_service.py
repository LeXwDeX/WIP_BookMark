from typing import Dict, List, Optional, Tuple
from modules.web_scraper import WebScraper
from modules.llms_client import chat_completion
import logging

class AIService:
    def __init__(self, 
                api_base: str = "https://one-api.ycgame.com/v1",
                api_key: str = "sk-JkjLOSoqsqE8A6XL5cDb428908Cd4aD48bF329Dd1a146395",
                model: str = "gpt-4o-mini"
                ):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.web_scraper = WebScraper()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def analyze_url(self, url: str) -> Tuple[str, List[str]]:
        try:
            # 获取网页内容
            self.logger.info(f"开始分析URL: {url}")
            content = self.web_scraper.get_url(url)
            if content.startswith("Failed to fetch URL"):
                raise Exception(f"无法获取网页内容: {content}")

            # 生成摘要
            self.logger.info("正在生成摘要...")
            summary_prompt = f"请为以下网页内容生成一个简短的摘要（100字以内）：\n\n{content[:3000]}"  # 限制内容长度
            summary = chat_completion(self.api_base, self.api_key, self.model, [
                {"role": "user", "content": summary_prompt}
            ])
            if summary.startswith("Error"):
                raise Exception(f"生成摘要失败: {summary}")

            # 生成标签
            self.logger.info("正在生成标签...")
            tags_prompt = f"请为这个网页内容生成3-5个关键标签（每个标签不超过4个字）：\n\n{content[:3000]}"
            tags_response = chat_completion(self.api_base, self.api_key, self.model, [
                {"role": "user", "content": tags_prompt}
            ])
            if tags_response.startswith("Error"):
                raise Exception(f"生成标签失败: {tags_response}")

            tags = [tag.strip() for tag in tags_response.split(',')]
            self.logger.info(f"分析完成 - 摘要长度: {len(summary)}, 标签数量: {len(tags)}")
            return summary, tags

        except Exception as e:
            self.logger.error(f"URL分析失败: {str(e)}")
            raise Exception(f"URL分析失败: {str(e)}")