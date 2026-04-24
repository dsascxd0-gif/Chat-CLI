import json
from pathlib import Path
from typing import List, Optional
from .api import Message


class SessionState:
    def __init__(self):
        self.messages: List[Message] = []
        self.model: str = ""
        self.theme: str = "monokai"
        self.base_url: str = "http://127.0.0.1:1234/v1"
        self.api_key: str = "sk-not-needed"

    def add_message(self, role: str, content: str, message_id: str = None, reasoning: str = ""):
        self.messages.append(Message(role, content, message_id, reasoning))

    def pop_last(self) -> Optional[Message]:
        return self.messages.pop() if self.messages else None

    def to_dict(self, title: str = None) -> dict:
        data = {
            "messages": [{"role": m.role, "content": m.content, "message_id": m.message_id, "reasoning": m.reasoning} for m in self.messages],
            "model": self.model,
            "theme": self.theme,
            "base_url": self.base_url,
            "api_key": self.api_key,
        }
        if title:
            data["title"] = title
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        s = cls()
        s.model = data.get("model", "")
        s.theme = data.get("theme", "monokai")
        s.base_url = data.get("base_url", "http://127.0.0.1:1234/v1")
        s.api_key = data.get("api_key", "sk-not-needed")
        for m in data.get("messages", []):
            s.messages.append(Message(m["role"], m["content"], m.get("message_id"), m.get("reasoning", "")))
        return s


class StateManager:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path.home() / ".chat_cli" / "state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: SessionState):
        self.path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> SessionState:
        if self.path.exists():
            try:
                return SessionState.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
            except Exception:
                pass
        return SessionState()
