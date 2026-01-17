from __future__ import annotations
from typing import Dict, Any
from .providers import OpenAICompatibleLLM


class Interlink:
    """Single place Heimdall uses to talk to LLMs (cloud or local)."""
    def __init__(self) -> None:
        self.llm = OpenAICompatibleLLM()

    async def ask(self, system: str, user: str) -> str:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        return await self.llm.chat(msgs)

    async def summarize(self, text: str, goal: str = "key points") -> str:
        sys = "You are an elite summarizer. Return tight bullets, no fluff."
        usr = f"Goal: {goal}\n---\n{text}"
        return await self.ask(sys, usr)

    async def plan(self, objective: str) -> str:
        sys = "You plan tasks into small, verifiable steps with clear success criteria."
        return await self.ask(sys, objective)
