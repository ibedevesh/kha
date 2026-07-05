"""Bring your own model.

Kha never depends on a specific provider. An `LLM` is any callable that takes a system prompt and
a message list and returns the assistant's text. A minimal adapter for any OpenAI-compatible chat
endpoint is provided; point it at whatever you run via environment variables:

    KHA_BASE_URL   e.g. https://api.your-provider.example/v1   (default: http://localhost:11434/v1)
    KHA_API_KEY    bearer token (optional for local servers)
    KHA_MODEL      model name

The model only ever supplies inputs. It never computes the answer, the environment does.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Protocol


class LLM(Protocol):
    def __call__(self, system: str, messages: list[dict]) -> str: ...


class OpenAICompatLLM:
    """Talks to any OpenAI-compatible /chat/completions endpoint over plain HTTP (no SDK)."""

    def __init__(self, model: str | None = None, base_url: str | None = None,
                 api_key: str | None = None, max_tokens: int = 600):
        self.model = model or os.environ.get("KHA_MODEL", "")
        self.base_url = (base_url or os.environ.get("KHA_BASE_URL", "http://localhost:11434/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("KHA_API_KEY", "")
        self.max_tokens = max_tokens

    def __call__(self, system: str, messages: list[dict]) -> str:
        payload = {"model": self.model, "max_tokens": self.max_tokens,
                   "messages": [{"role": "system", "content": system}, *messages]}
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"content-type": "application/json"
                     **({"authorization": f"Bearer {self.api_key}"} if self.api_key else {})}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        return data["choices"][0]["message"]["content"] or ""


def default_llm() -> LLM:
    return OpenAICompatLLM()
