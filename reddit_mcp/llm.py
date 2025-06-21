from enum import Enum
from typing import Optional
import logging
import aiohttp


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class DemandImpactType(Enum):
    """Types of demand impact events"""
    POSITIVE = "positive"  # Increases demand
    NEGATIVE = "negative"  # Decreases demand
    NEUTRAL = "neutral"  # No significant impact
    MIXED = "mixed"  # Mixed impact


class LLMClient:
    """Modular LLM client supporting multiple providers"""

    def __init__(self, provider: LLMProvider, api_key: Optional[str] = None,
                 endpoint: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model or self._get_default_model()

    def _get_default_model(self) -> str:
        """Get default model for each provider"""
        defaults = {
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.OLLAMA: "llama3.2",
            LLMProvider.ANTHROPIC: "claude-3-sonnet-20240229",
            LLMProvider.AZURE_OPENAI: "gpt-4o-mini"
        }
        return defaults.get(self.provider, "gpt-4o-mini")

    def _get_default_endpoint(self) -> str:
        """Get default endpoint for each provider"""
        endpoints = {
            LLMProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
            LLMProvider.OLLAMA: "http://localhost:11434/api/generate",
            LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1/messages",
            LLMProvider.AZURE_OPENAI: None  # Requires custom endpoint
        }
        return self.endpoint or endpoints.get(self.provider)

    async def generate_analysis(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate analysis using the configured LLM provider"""
        try:
            if self.provider == LLMProvider.OPENAI:
                return await self._call_openai(prompt, system_prompt)
            elif self.provider == LLMProvider.OLLAMA:
                return await self._call_ollama(prompt)
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._call_anthropic(prompt, system_prompt)
            elif self.provider == LLMProvider.AZURE_OPENAI:
                return await self._call_azure_openai(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            #logger.error(f"Error calling {self.provider.value}: {str(e)}")
            return f"Error during analysis: {str(e)}"

    async def _call_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self._get_default_endpoint(), headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    return f"OpenAI API error {response.status}: {error_text}"