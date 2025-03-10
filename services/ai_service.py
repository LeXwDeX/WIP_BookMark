from typing import Dict, List, Optional, Tuple
from modules.web_scraper import WebScraper
from modules.llms_client import chat_completion

"""
自述：
AIService类是一个专门用于处理网页内容并生成AI摘要和标签的服务类。

主要功能：
1. 网页内容获取：通过WebScraper模块抓取目标URL的网页内容。
2. 内容处理：对获取的内容进行预处理，包括内容截断等操作，以确保符合API限制。
3. AI摘要生成：调用OpenAI接口，基于网页内容生成精炼的摘要信息。
4. 标签生成：分析网页内容，生成相关的标签，便于分类和检索。
5. 批量处理：支持多个URL的批量处理功能。

工作流程：
1. 初始化时配置API参数（api_base、api_key、model）和WebScraper实例。
2. 接收URL请求后，首先通过WebScraper获取网页内容。
3. 对获取的内容进行预处理和长度控制。
4. 分别调用OpenAI接口生成摘要和标签。
5. 返回处理结果，包括摘要对象和标签列表。

异常处理：
- 网页抓取失败时返回错误信息
- API调用异常时提供友好的错误提示
- 内容超限时进行自动截断处理

与其他模块的关系：
- 依赖WebScraper进行网页内容获取
- 使用OpenAI接口进行AI处理
- 与BookmarkSummary和BookmarkTag模型交互
"""

class AIService:
    """AI服务类，负责网页内容处理和AI摘要生成"""

    def __init__(self, api_base: str, api_key: str, model: str = "gpt-4o-mini"):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.web_scraper = WebScraper()

    def process_url(self, url: str) -> Tuple[str, List[str], Optional[str]]:
        """处理URL，获取网页内容并生成AI摘要和标签
        
        Returns:
            Tuple[str, List[str], Optional[str]]: 返回(摘要内容, 标签列表, 错误信息)
        """
        # 获取网页内容
        content = self.web_scraper.get_url(url)

        if "Failed to fetch URL" in content or "No meaningful content extracted" in content:
            return "无法生成摘要", [], content

        # 截断内容以避免超出API限制
        max_length = 100000
        truncated_content = content[:max_length]
        if len(content) > max_length:
            truncated_content += "\n\n(Note: Content was truncated due to size limitations.)"

        # 生成摘要
        summary = self._generate_summary(truncated_content)
        # 生成标签
        tags = self._generate_tags(truncated_content)

        return summary, tags, None

    def _generate_summary(self, content: str) -> str:
        """生成内容摘要
        
        Returns:
            str: 摘要内容
        """
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
                return cleaned_summary
            return "无法生成摘要"
        except Exception as e:
            print(f"生成摘要时出错: {str(e)}")
            return "无法生成摘要"

    def _generate_tags(self, content: str) -> List[str]:
        """生成内容标签
        
        Returns:
            List[str]: 标签列表
        """
        try:
            tags_message = [{"role": "user", "content": f"请为以下内容生成1到5个重要的文字标签（用逗号隔开）：\n{content}"}]
            tags_response = chat_completion(self.api_base, self.api_key, self.model, tags_message)
            if tags_response and not tags_response.startswith("Error"):
                return [tag.strip() for tag in tags_response.strip().split(",") if tag.strip()]
            return []
        except Exception as e:
            print(f"生成标签时出错: {str(e)}")
            return []

    @staticmethod
    def batch_process_urls(urls: List[str], api_base: str, api_key: str, model: str = "gpt-4o-mini") -> Dict[str, Tuple[str, List[str], Optional[str]]]:
        """批量处理多个URL
        
        Returns:
            Dict[str, Tuple[str, List[str], Optional[str]]]: 返回URL到(摘要内容, 标签列表, 错误信息)的映射
        """
        service = AIService(api_base, api_key, model)
        results = {}
        for url in urls:
            summary, tags, error = service.process_url(url)
            results[url] = (summary, tags, error)
        return results