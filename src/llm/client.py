"""
统一 LLM 客户端
支持 DeepSeek（兼容 OpenAI API 格式），带重试和流式支持
"""

import time
import json
from typing import List, Dict, Any, Optional, Generator

import requests

from ..config import Config


class LLMResponse:
    """LLM 响应封装"""

    def __init__(self, content: str, raw: Dict = None, usage: Dict = None):
        self.content = content
        self.raw = raw or {}
        self.usage = usage or {}

    def __str__(self):
        return self.content

    def __repr__(self):
        return f"LLMResponse(content={self.content[:100]}...)"


class LLMClient:
    """统一 LLM 客户端"""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        llm = self.config.llm
        self.provider = llm['provider']
        self.model = llm['model']
        self.base_url = llm['base_url'].rstrip('/')
        self.api_key = llm['api_key']
        self.temperature = llm['temperature']
        self.max_tokens = llm['max_tokens']
        self.top_p = llm['top_p']
        self.timeout = llm['timeout']
        self.max_retries = llm['max_retries']

        if not self.api_key:
            raise ValueError("API Key 未设置，请设置 DEEPSEEK_API_KEY 环境变量")

        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat(self, messages: List[Dict[str, str]],
             temperature: float = None,
             max_tokens: int = None,
             **kwargs) -> LLMResponse:
        """非流式聊天补全"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "top_p": kwargs.get('top_p', self.top_p),
            "stream": False,
        }
        payload.update({k: v for k, v in kwargs.items()
                        if k not in ['top_p', 'stream']})

        for attempt in range(self.max_retries):
            try:
                resp = self.session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return LLMResponse(content=content, raw=data, usage=usage)
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt + 0.5
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"LLM API 调用失败（重试 {self.max_retries} 次）: {e}")

    def stream(self, messages: List[Dict[str, str]],
               temperature: float = None,
               **kwargs) -> Generator[str, None, None]:
        """流式聊天补全"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "stream": True,
        }

        resp = self.session.post(
            f"{self.base_url}/chat/completions",
            headers=self._get_headers(),
            json=payload,
            timeout=self.timeout,
            stream=True
        )

        for line in resp.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue

    def complete(self, prompt: str, system_prompt: str = None,
                 **kwargs) -> LLMResponse:
        """简单补全接口"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, **kwargs)

    def set_model(self, model: str):
        """切换模型"""
        self.model = model

    def set_temperature(self, temperature: float):
        """设置温度"""
        self.temperature = temperature
