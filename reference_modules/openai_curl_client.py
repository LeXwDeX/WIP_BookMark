import requests
import json

def chat_completion(api_base, api_key, model, messages):
    """
    调用 OpenAI Chat Completion 接口的封装
    :param api_base: OpenAI API 基础 URL
    :param api_key: OpenAI API 密钥
    :param model: 使用的模型名称，例如 "gpt-4o-mini"
    :param messages: 消息列表，包含角色和内容
    :return: 模型的回复内容或错误信息
    """
    try:
        url = f"{api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages
        }

        # 发送 POST 请求
        response = requests.post(url, headers=headers, json=payload, verify=False)  # Temporary workaround for SSL issues

        # 检查响应状态码
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}"

        # 解析 JSON 响应
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

    except Exception as e:
        return f"Error: {str(e)}"

# 示例用法
if __name__ == "__main__":
    api_base = "https://chat_admin.sunsan05.com/v1"
    api_key = "sk-JkjLOSoqsqE8A6XL5cDb428908Cd4aD48bF329Dd1a146395"
    model = "gpt-4o-mini"
    messages = [{"role": "user", "content": "你好，测试一下。"}]

    result = chat_completion(api_base, api_key, model, messages)
    print("测试结果:", result)
