# AGENTS.md

## Setup
```powershell
cd D:\code\chat_cli
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Commands
- Run app: `.\venv\Scripts\python main.py`
- Syntax check: `.\venv\Scripts\python -m py_compile chat_cli\app.py`

## Architecture
- `chat_cli/api.py` - API client (`APIClient` ABC, `LMStudioClient` impl)
- `chat_cli/state.py` - Session state (`SessionState`)
- `chat_cli\session_manager.py` - Multi-session persistence (`SessionManager`, saves to `~/.chat_cli/sessions/`)
- `chat_cli/commands.py` - Command registry (`Command` ABC, `CommandRegistry`)
- `chat_cli/app.py` - Textual TUI app (`ChatApp`, `MessageWidget`)

## Conventions
- All major components use ABC interfaces, not hardcoded
- `APIClient.chat_stream()` yields streaming tokens
- Commands registered in `ChatApp._register_commands()`
- Default API: LM Studio at `http://127.0.0.1:1234/v1`
- Streaming uses `@work` decorator for non-blocking async
- `MessageWidget.update_content()` for live markdown updates
- Multi-session: stored in `~/.chat_cli/sessions/session-*.json`
- Logs: `logs/` directory
- Tab completion for `/model` command shows available models
