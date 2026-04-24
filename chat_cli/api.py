from abc import ABC, abstractmethod
from typing import AsyncIterator, List
from dataclasses import dataclass

@dataclass
class StreamChunk:
    type: str  # "reasoning" or "content"
    content: str

class Message:
    def __init__(self, role: str, content: str, message_id: str = None, reasoning: str = ""):
        self.role = role
        self.content = content
        self.message_id = message_id
        self.reasoning = reasoning


class APIClient(ABC):
    @abstractmethod
    async def chat(self, messages: List[Message], model: str) -> str: ...

    @abstractmethod
    async def chat_stream(self, messages: List[Message], model: str) -> AsyncIterator[StreamChunk]: ...

    @abstractmethod
    async def list_models(self) -> List[str]: ...


from openai import AsyncOpenAI
import requests

class LMStudioClient(APIClient):
    def __init__(self, base_url: str = "http://127.0.0.1:1234/v1", api_key: str = "sk-not-needed"):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.base_url = base_url.replace("/v1", "")

    async def chat(self, messages: List[Message], model: str) -> str:
        resp = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages]
        )
        return resp.choices[0].message.content

    async def chat_stream(self, messages: List[Message], model: str) -> AsyncIterator[StreamChunk]:
        stream = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            stream=True
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                yield StreamChunk(type="reasoning", content=delta.reasoning_content)
            if delta.content:
                yield StreamChunk(type="content", content=delta.content)

    async def list_models(self) -> List[str]:
        try:
            resp = requests.get(f"{self.base_url}/v1/models")
            data = resp.json()
            models = []
            for i in data.get("data", []):
                models.append(i["id"])
            return models
        except Exception:
            return []
