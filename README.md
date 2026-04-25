# Chat CLI

A TUI application for chatting with AI, primarily using the Textual library.

[EN](./README.md) | [中文](./README_cn.md)

## Features

- Chat with LM Studio / OpenAI-compatible APIs
- Markdown rendering
- Thinking animation display
- Command auto-completion
- Auto-save session state
- Logging

## Installation

```powershell
pip install -r requirements.txt
```

## Usage

```powershell
python main.py
```

## Commands

- `/help` - Show help
- `/baseurl` - Change Base URL (the new Base URL must include the `http` or `https` prefix, e.g. `https://api.example.com/v1` or `http://api.example.com/v1`). Syntax: `/baseurl <BaseURL>`
- `/apikey` - Change API key. Syntax: `/apikey <apikey>`
- `/new` - Create new session. Syntax: `/new [title]`
- `/title` - Set session title. Syntax: `/title <title>`
- `/del` - Delete session. Syntax: `/del [session_name]` type again to confirm
- `/prompt` - Set system prompt. Syntax: `/prompt <prompt>`
- `/model` - View / switch model. Syntax: `/model <model>`
- `/reloadurl` - Reload the base URL to prevent network issues from causing connection failures.
- `/clear` - Clear conversation type again to confirm
- `/quit` - Quit
- `/theme` - Switch theme (currently only `monokai` is available). Syntax: `/theme <theme>`

## Default key bindings

- `Ctrl+Z` - Undo
- `Ctrl+C` - Quit

## Logs

Logs are saved in the `logs/` directory.

## Special notice

This project is a practice work I created during my spare time to learn Textual. The core features are functional, but the details are not yet polished.  
Due to my busy academic schedule, I cannot guarantee timely replies to issues/PRs. You are welcome to fork the project or submit PRs; I will try my best to review them on weekends.
