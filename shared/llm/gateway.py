"""
Beyond AI — Shared LLM Gateway

Unified interface for LLM calls. Ollama as primary, Claude API as fallback.
Follows FinRegAgents confidence-aware pattern.
"""

import os
import json
import httpx
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized LLM response with confidence metadata."""
    content: str
    model: str
    provider: str  # "ollama" | "claude"
    tokens_used: int
    confidence: float | None = None


class LLMGateway:
    """Route LLM requests to Ollama (primary) or Claude API (fallback)."""

    def __init__(
        self,
        ollama_url: str | None = None,
        ollama_model: str | None = None,
        claude_api_key: str | None = None,
        claude_model: str = "claude-sonnet-4-20250514",
        timeout: float = 60.0,
    ):
        self.ollama_url = ollama_url or os.getenv(
            "OLLAMA_URL", "http://localhost:11434"
        )
        self.ollama_model = ollama_model or os.getenv(
            "OLLAMA_MODEL", "kimi-k2.5"
        )
        self.claude_api_key = claude_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.claude_model = claude_model
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Send completion request — tries Ollama first, falls back to Claude."""
        try:
            return await self._ollama_complete(
                prompt, system, temperature, max_tokens
            )
        except Exception:
            if self.claude_api_key:
                return await self._claude_complete(
                    prompt, system, temperature, max_tokens
                )
            raise

    async def _ollama_complete(
        self, prompt: str, system: str, temperature: float, max_tokens: int
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "system": system,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return LLMResponse(
                content=data.get("response", ""),
                model=self.ollama_model,
                provider="ollama",
                tokens_used=data.get("eval_count", 0),
            )

    async def _claude_complete(
        self, prompt: str, system: str, temperature: float, max_tokens: int
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.claude_model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                    **({"system": system} if system else {}),
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = "".join(
                b["text"] for b in data["content"] if b["type"] == "text"
            )
            tokens = data.get("usage", {})
            return LLMResponse(
                content=content,
                model=self.claude_model,
                provider="claude",
                tokens_used=tokens.get("input_tokens", 0)
                + tokens.get("output_tokens", 0),
            )

    def close(self):
        self._client.close()
