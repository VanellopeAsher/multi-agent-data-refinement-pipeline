import os
import requests
from openai import AzureOpenAI, OpenAI
from typing import List, Dict, Union, Optional, Any
from dotenv import load_dotenv
from src.exceptions import TavilyQuotaExceededError

load_dotenv()

API_KEY_MAP = {
    'openai': os.getenv('OPENAI_API_KEY'),
    'siliconflow': os.getenv('SILICONFLOW_API_KEY'),
    'tavily': os.getenv('TAVILY_API_KEY') 
}

BASE_URL_MAP = {
    'openai': os.getenv('OPENAI_BASE_URL'),
    'siliconflow': os.getenv('SILICONFLOW_BASE_URL')
}


class LLM:
    def __init__(self, model_name: str, platform: str = 'openai', api_key: Optional[str] = None):
        self.model_name = model_name
        self.platform = platform
        self.api_key = api_key
        self.last_usage = None
        
        self.client = self._init_client(platform)

    def _init_client(self, platform: str):
        assert platform in API_KEY_MAP, f"Platform {platform} is not supported."
        if self.api_key:
            api_key = self.api_key
        else:
            api_key = API_KEY_MAP.get(platform)

        assert api_key, f"API key for platform {platform} is not found in config or environment variables."
        base_url = BASE_URL_MAP.get(platform)
        
        if platform == 'openai':
            client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=base_url,
                api_version="2024-02-01"
            )
        else:
            client = OpenAI(
                api_key=api_key, 
                base_url=base_url
            )
        return client

    def _search_web(self, query: str) -> List[str]:
        """Raises TavilyQuotaExceededError if quota exceeded."""
        api_key = API_KEY_MAP.get('tavily')
        if not api_key:
            raise ValueError("Tavily API key is missing.")
        
        url = "https://api.tavily.com/search"
        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            'api_key': api_key,
            'query': query,
            'search_depth': 'basic',
            'max_results': 5  # 返回前 5 条搜索结果
        }
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            # Tavily返回格式: [{'url': '...', 'title': '...', 'content': '...', ...}, ...]
            return [item.get('url', '') for item in results if item.get('url')]
        else:
            # 检查是否是余额不足错误
            error_text = response.text.lower()
            error_json = {}
            try:
                error_json = response.json()
            except:
                pass
            
            quota_keywords = [
                'quota', 'limit', 'exceeded', 'insufficient', 
                'balance', 'credits', 'subscription', 'plan limit',
                '余额不足', '配额', '超出', '限额'
            ]
            
            error_message = error_json.get('error', '') or error_text
            if any(keyword in error_message for keyword in quota_keywords):
                raise TavilyQuotaExceededError(
                    f"Tavily API quota exceeded. Error: {response.text}"
                )
            
            raise Exception(f"Error fetching search results: {response.status_code} - {response.text}")

    def generate(
        self, 
        prompt: Union[List[Dict[str, Any]], str], 
        model: Optional[str] = None, 
        temperature: float = 1.0,
        web_search: bool = False
    ) -> str:
        if model is None:
            model = self.model_name

        if isinstance(prompt, str):
            messages = [{'role': 'user', 'content': prompt}]
        else:
            messages = prompt
        
        api_params = {
            'model': model,
            'messages': messages,
            'temperature': temperature
        }

        if web_search:
            query = prompt if isinstance(prompt, str) else prompt[0]['content']
            search_results = self._search_web(query)
            api_params['tools'] = [
                {
                    'type': 'function',
                    'function': {
                        'name': 'web_search',
                        'description': '执行网页搜索',
                        'parameters': {
                            'results': search_results
                        }
                    }
                }
            ]
        
        # 使用解包方式传入所有参数
        completion = self.client.chat.completions.create(**api_params)
        
        # 保存 token 使用量信息
        if hasattr(completion, 'usage') and completion.usage:
            self.last_usage = completion.usage

        return completion.choices[0].message.content or ""
