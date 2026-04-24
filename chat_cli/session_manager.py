import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from .state import SessionState, StateManager


class SessionManager:
    def __init__(self, sessions_dir: Optional[Path] = None):
        self.sessions_dir = sessions_dir or Path.home() / ".chat_cli" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_files(self) -> List[Path]:
        return sorted(
            self.sessions_dir.glob("session-*.json"),
            key=lambda p: int(p.stem.split("-")[1]) if p.stem.split("-")[1].isdigit() else 0
        )
    
    def list_sessions(self) -> List[Dict[str, str]]:
        files = self._get_session_files()
        sessions = []
        for f in files:
            title = self.get_title(f.name)
            sessions.append({"filename": f.name, "title": title})
        return sessions
    
    def get_title(self, filename: str) -> str:
        path = self.sessions_dir / filename
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data.get("title", filename.replace(".json", ""))
            except Exception:
                pass
        return filename.replace(".json", "")
    
    def set_title(self, filename: str, new_title: str):
        path = self.sessions_dir / filename
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                data["title"] = new_title
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
    
    def load_session(self, filename: str) -> SessionState:
        path = self.sessions_dir / filename
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return SessionState.from_dict(data)
            except Exception:
                pass
        return SessionState()
    
    def save_current(self, state: SessionState, filename: str, title: str = None):
        data = state.to_dict()
        if title:
            data["title"] = title
        elif "title" not in data:
            data["title"] = filename.replace(".json", "")
        
        old_path = Path.home() / ".chat_cli" / "state.json"
        if old_path.exists() and not list(self.sessions_dir.glob("session-*.json")):
            try:
                old_data = json.loads(old_path.read_text(encoding="utf-8"))
                new_path = self.sessions_dir / "session-1.json"
                new_data = old_data.copy()
                new_data["title"] = "session-1"
                new_path.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
        
        path = self.sessions_dir / filename
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def create_session(self, title: str = None) -> str:
        files = self._get_session_files()
        max_num = 0
        for f in files:
            parts = f.stem.split("-")
            if len(parts) == 2 and parts[1].isdigit():
                max_num = max(max_num, int(parts[1]))
        
        new_num = max_num + 1
        filename = f"session-{new_num}.json"
        session_title = title or filename.replace(".json", "")
        
        state = SessionState()
        self.save_current(state, filename, session_title)
        return filename
    
    def get_latest_session(self) -> Optional[str]:
        files = self._get_session_files()
        if not files:
            return None
        latest = max(files, key=lambda p: p.stat().st_mtime)
        return latest.name
    
    def get_first_session(self) -> str:
        files = self._get_session_files()
        if not files:
            return self.create_session()
        return files[0].name
    
    def migrate_from_old(self) -> bool:
        old_path = Path.home() / ".chat_cli" / "state.json"
        if old_path.exists() and not list(self.sessions_dir.glob("session-*.json")):
            try:
                old_data = json.loads(old_path.read_text(encoding="utf-8"))
                new_path = self.sessions_dir / "session-1.json"
                new_data = old_data.copy()
                new_data["title"] = "session-1"
                new_path.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8")
                return True
            except Exception:
                pass
        return False