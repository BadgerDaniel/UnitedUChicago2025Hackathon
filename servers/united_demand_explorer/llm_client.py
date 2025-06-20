import aiohttp
from enum import Enum
from typing import Optional

class LLMProvider(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"

class LLMClient:
    """Generic LLM client supporting multiple providers"""
    def __init__(
        self,
        provider: LLMProvider,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model or self._get_default_model()

    def _get_default_model(self) -> str:
        defaults = {
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.OLLAMA: "llama3.2",
            LLMProvider.ANTHROPIC: "claude-3-sonnet-20240229",
            LLMProvider.AZURE_OPENAI: "gpt-4o-mini",
        }
        return defaults[self.provider]

    def _default_endpoint(self) -> str:
        endpoints = {
            LLMProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
            LLMProvider.OLLAMA: "http://localhost:11434/api/generate",
            LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1/messages",
            LLMProvider.AZURE_OPENAI: None,
        }
        return self.endpoint or endpoints[self.provider]

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.provider == LLMProvider.OPENAI:
            return await self._call_openai(prompt, system_prompt)
        elif self.provider == LLMProvider.OLLAMA:
            return await self._call_ollama(prompt)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(prompt, system_prompt)
        elif self.provider == LLMProvider.AZURE_OPENAI:
            return await self._call_azure(prompt, system_prompt)
        else:
            raise ValueError(f"Unsupported provider {self.provider}")

    async def _call_openai(self, prompt: str, system_prompt: Optional[str]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "temperature": 0.1, "max_tokens": 4000}

        async with aiohttp.ClientSession() as session:
            async with session.post(self._default_endpoint(), headers=headers, json=payload) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def _call_ollama(self, prompt: str) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        async with aiohttp.ClientSession() as session:
            async with session.post(self._default_endpoint(), json=payload) as resp:
                data = await resp.json()
                return data.get("response", "")

    async def _call_anthropic(self, prompt: str, system_prompt: Optional[str]) -> str:
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4000}
        async with aiohttp.ClientSession() as session:
            async with session.post(self._default_endpoint(), headers=headers, json=payload) as resp:
                data = await resp.json()
                return data.get("content", "")

    async def _call_azure(self, prompt: str, system_prompt: Optional[str]) -> str:
        if not self.endpoint:
            return "Azure endpoint not configured"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"temperature": 0.1, "max_tokens": 4000, "messages": messages}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=headers, json=payload) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]