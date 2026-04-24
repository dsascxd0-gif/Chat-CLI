# AGENTS.md

## Setup
```bash
cd D:\code\chat_cli
.\venv\Scripts\Activate.ps1
pip install textual openai
```

## Commands
- Run app: `.\venv\Scripts\python main.py`
- Syntax check: `.\venv\Scripts\python -m py_compile chat_cli\<file>.py`

## Architecture
- `chat_cli/api.py` - API client interface (`APIClient` ABC, `LMStudioClient` impl)
- `chat_cli/state.py` - Session state and persistence (`SessionState`, `StateManager`)
- `chat_cli/commands.py` - Command registry and commands (`Command` ABC, `CommandRegistry`)
- `chat_cli/app.py` - Textual TUI app (`ChatApp`, `MessageWidget`)
- State saved to `~/.chat_cli/state.json`

## Conventions
- All major components use ABC interfaces, not hardcoded
- `APIClient.chat_stream()` yields tokens for streaming
- Commands registered in `ChatApp._register_commands()`
- Default API: LM Studio at `http://127.0.0.1:1234/v1`
- Streaming uses `@work` decorator for non-blocking async
- `MessageWidget.update_content()` for live markdown updates
