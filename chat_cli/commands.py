from abc import ABC, abstractmethod
from typing import Dict, Type, Optional, List
from textual.widgets import ListView, ListItem

from .api import Message, LMStudioClient
from .logging_config import log_operation
from .state import SessionState


class Command(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, app, args: str) -> None: ...


class CommandRegistry:
    def __init__(self):
        self._commands: Dict[str, Command] = {}

    def register(self, cmd: Command):
        self._commands[cmd.name] = cmd

    def get(self, name: str) -> Optional[Command]:
        return self._commands.get(name)

    def all(self) -> Dict[str, Command]:
        return self._commands


class HelpCommand(Command):
    name = "help"
    description = "Show available commands"

    async def execute(self, app, args: str):
        lines = ["Available commands:"]
        for name, cmd in app.command_registry.all().items():
            lines.append(f"  /{name} - {cmd.description}")
        app.notify("\n".join(lines))


class ClearCommand(Command):
    name = "clear"
    description = "Clear conversation (type /clear again to confirm)"

    async def execute(self, app, args: str):
        if app._pending_clear:
            app.state.messages.clear()
            app.refresh_chat()
            app.notify("Conversation cleared")
            app._pending_clear = False
            log_operation("Conversation cleared")
        else:
            app.state.add_message("assistant", "Clear conversation?\nThis cannot be undone.\n\nType /clear again to confirm")
            app.refresh_chat()
            app._pending_clear = True


class ModelCommand(Command):
    name = "model"
    description = "Set or show model"

    def set_models(self, models: list):
        self._available_models = models

    async def execute(self, app, args: str):
        if args.strip():
            app.state.model = args.strip()
            app.notify(f"Model set to: {app.state.model}")
        else:
            models = getattr(self, '_available_models', [])
            current = app.state.model
            if models:
                msg = f"**Current Model**: {current}\n\n**Available Models**:\n" + "\n".join([f"- {m}" for m in models]) + "\n\nUse `/model model_name` to switch models."
            else:
                msg = f"**Current Model**: {current}\n\nNo models available from API"
            app.state.add_message("assistant", msg)
            app.refresh_chat()


class ThemeCommand(Command):
    name = "theme"
    description = "Set or show theme"

    async def execute(self, app, args: str):
        if args.strip():
            app.state.theme = args.strip()
            app.notify(f"Theme set to: {app.state.theme}")
        else:
            app.notify(f"Current theme: {app.state.theme}")


class QuitCommand(Command):
    name = "quit"
    description = "Exit the application"

    async def execute(self, app, args: str):
        app.exit()


class BaseURLCommand(Command):
    name = "baseurl"
    description = "Set or show API base URL. Saved to state.json."

    async def execute(self, app, args: str):
        if args.strip():
            new_url = args.strip()
            app.state.base_url = new_url
            app.api = LMStudioClient(base_url=new_url, api_key=app.state.api_key)
            app.notify(f"Base URL set to: {new_url}")
            # Reload models from new URL
            try:
                models = await app.api.list_models()
                app.model_cmd.set_models(models)
                app.notify(f"Loaded {len(models)} models from new URL")
            except Exception as e:
                app.notify(f"Failed to load models: {e}")
            app._save_current_session()
            log_operation("Base URL changed", new_url)
        else:
            app.notify(f"Current Base URL: {app.state.base_url}")


class APIKeyCommand(Command):
    name = "apikey"
    description = "Set or show API key. Saved to state.json."

    async def execute(self, app, args: str):
        if args.strip():
            new_key = args.strip()
            app.state.api_key = new_key
            app.api = LMStudioClient(base_url=app.state.base_url, api_key=new_key)
            app.notify("API key set.")
            app._save_current_session()
            log_operation("API key changed")
        else:
            app.notify(f"Current API key: {app.state.api_key}")


class NewSessionCommand(Command):
    name = "new"
    description = "Create a new session. Usage: /new [title]"

    async def execute(self, app, args: str):
        title = args.strip() if args.strip() else None
        filename = app.session_mgr.create_session(title)
        # 保存当前会话
        app._save_current_session()
        # 切换到新会话
        app.current_session_file = filename
        app.state = SessionState()
        app.state.base_url = getattr(app.session_mgr, 'base_url', "http://127.0.0.1:1234/v1")
        app.state.api_key = "sk-not-needed"
        app.refresh_session_list()
        app.refresh_chat()
        app.notify(f"Created new session: {title or filename}")
        log_operation("New session created", filename)


class TitleCommand(Command):
    name = "title"
    description = "Set current session title. Usage: /title <new_title>"

    async def execute(self, app, args: str):
        if not args.strip():
            app.notify("Usage: /title <new_title>")
            return
        
        new_title = args.strip()
        app.session_mgr.set_title(app.current_session_file, new_title)
        app.refresh_session_list()
        app.notify(f"Session title set to: {new_title}")
        log_operation("Title changed", new_title)


class SystemPromptCommand(Command):
    name = "prompt"
    description = "Set or show system prompt. Saved to session."

    async def execute(self, app, args: str):
        if args.strip():
            app.state.system_prompt = args.strip()
            app.notify("System prompt updated")
            app._save_current_session()
            log_operation("System prompt changed", args.strip()[:50])
        else:
            if app.state.system_prompt:
                app.notify(f"Current system prompt:\n{app.state.system_prompt}")
            else:
                app.notify("No system prompt set")


class DeleteCommand(Command):
    name = "del"
    description = "Delete session. Usage: /del [session_name] or /del (type again to confirm)"

    async def execute(self, app, args: str):
        if app._pending_delete:
            sessions = app.session_mgr.list_sessions()
            if len(sessions) == 1:
                app.notify("Cannot delete the only session")
                app._pending_delete = False
                return
            current_title = app.session_mgr.get_title(app.current_session_file)
            old_file = app.current_session_file
            sessions = [s for s in sessions if s["filename"] != old_file]
            app.session_mgr.delete_session(old_file)
            app.current_session_file = sessions[0]["filename"]
            app.state = app.session_mgr.load_session(app.current_session_file)
            app.refresh_session_list()
            app.refresh_chat()
            app._pending_delete = False
            app.notify(f"Deleted: {current_title}\nSwitched to: {sessions[0]['title']}")
            log_operation("Session deleted", old_file)
            return
        
        if args.strip():
            target_filename = None
            sessions = app.session_mgr.list_sessions()
            for s in sessions:
                if s["title"] == args.strip() or s["filename"] == args.strip():
                    target_filename = s["filename"]
                    break
            
            if not target_filename:
                app.notify(f"Session not found: {args.strip()}")
                return
            
            if target_filename == app.current_session_file:
                if len(sessions) == 1:
                    app.notify("Cannot delete the only session")
                    return
                sessions = [s for s in sessions if s["filename"] != target_filename]
                app.session_mgr.delete_session(target_filename)
                app.current_session_file = sessions[0]["filename"]
                app.state = app.session_mgr.load_session(app.current_session_file)
                app.refresh_session_list()
                app.refresh_chat()
                app.notify(f"Deleted session: {args.strip()}\nSwitched to: {sessions[0]['title']}")
                log_operation("Session deleted", target_filename)
            else:
                app.session_mgr.delete_session(target_filename)
                app.refresh_session_list()
                app.notify(f"Deleted session: {args.strip()}")
                log_operation("Session deleted", target_filename)
        else:
            sessions = app.session_mgr.list_sessions()
            current_title = app.session_mgr.get_title(app.current_session_file)
            confirm_msg = f"Delete current session '{current_title}'?\nThis cannot be undone.\n\nType /del again to confirm"
            app.state.add_message("assistant", confirm_msg)
            app.refresh_chat()
            app._pending_delete = True
