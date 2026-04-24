from abc import ABC, abstractmethod
from typing import Dict, Type, Optional, List
from textual.widgets import ListView, ListItem

from .api import Message, LMStudioClient
from .logging_config import log_operation


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
    description = "Clear the conversation"

    async def execute(self, app, args: str):
        app.state.messages.clear()
        app.refresh_chat()
        app.notify("Conversation cleared")


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
            app.state_manager.save(app.state)


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
            app.state_manager.save(app.state)
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
            app.state_manager.save(app.state)
            log_operation("API key changed")
        else:
            app.notify(f"Current API key: {app.state.api_key}")
