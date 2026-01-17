"""Provider adapters for LLMs and embeddings.

Keep adapters small and testable. Each provider should expose a thin
`Client` class that implements the common methods used by the app.
"""
from typing import Any, Dict, Iterable, Optional


class BaseClient:
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError()


class DummyClient(BaseClient):
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        return {"text": "stub: " + prompt}


class OpenAICompatibleLLM:
    """Async helper that calls OpenAI-style chat/completions endpoints.

    Usage:
        client = OpenAICompatibleLLM()
        await client.chat([...])
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        import os

        self.base_url = (
            (base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        )
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    async def chat(self, messages: Iterable[Dict[str, str]], **kwargs) -> str:
        payload: Dict[str, Any] = {"model": self.model, "messages": list(messages)}
        payload.update(kwargs)
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            # compatible with OpenAI response shape
            return data["choices"][0]["message"]["content"]
