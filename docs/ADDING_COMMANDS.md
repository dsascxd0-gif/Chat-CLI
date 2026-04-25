# Adding Commands

[EN](/docs/ADDING_COMMANDS.md) | [中文](/docs/ADDING_COMMANDS_cn.md)

## Command system architecture

The command system of this application is built on the following components:

- **`Command` (ABC)**: Abstract base class for all commands, defining `name`, `description`, and the `execute()` method.
- **`CommandRegistry`**: Command registry that manages all available commands.
- **`ChatApp._register_commands()`**: Entry point for registering commands with the app.

## How to add a new command

### Step 1: Create a command class

In `chat_cli/commands.py`, inherit from `Command` and implement the `execute()` method:

```python
class MyCommand(Command):
    name = "mycommand"          # command name (lowercase, without /)
    description = "Describe what this command does"

    async def execute(self, app, args: str) -> None:
        # app: ChatApp instance, providing access to state, api, notify, etc.
        # args: the argument part of the user input (without the command name)
        
        if args.strip():
            # Handle case with arguments
            app.notify(f"Arguments: {args}")
        else:
            # Handle case without arguments
            app.notify("My command executed")
```

### Step 2: Import command

Import command in `chat_cli/app.py` line 16

```python
from .commands import CommandRegistry, HelpCommand, ClearCommand, MyCommand, ThemeCommand, QuitCommand
```

### Step 3: Register the command

Register the command in the `ChatApp._register_commands()` method inside `chat_cli/app.py`:

```python
def _register_commands(self):
    self.model_cmd = ModelCommand()
    self.command_registry.register(self.model_cmd)
    for cmd_cls in [HelpCommand, ClearCommand, MyCommand, ThemeCommand, QuitCommand]:
        self.command_registry.register(cmd_cls())
```

### Step 4: Test

Run the application and test:
```powershell
python main.py
```
Try `/mycommand` or `/mycommand some arguments` to see the effect.

## Example: Adding a `/time` command

Here is a complete example that adds a command to display the current time:

**Add to `chat_cli/commands.py`:**

```python
import time

class TimeCommand(Command):
    name = "time"
    description = "Show current time"

    async def execute(self, app, args: str):
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app.state.add_message("assistant", f"Current time: {now}")
        app.refresh_chat()
        app.state_manager.save(app.state)
```

**Import command at `chat_cli\app.py` line 16**

```python
from .commands import CommandRegistry, HelpCommand, ClearCommand, TimeCommand, ThemeCommand, QuitCommand
```
**Register in `_register_commands()` inside `chat_cli/app.py`:**

```python
for cmd_cls in [HelpCommand, ClearCommand, TimeCommand, ModelCommand, ThemeCommand, QuitCommand]:
    self.command_registry.register(cmd_cls())
```

## Handling command arguments

Command arguments are passed via the `args` string. You can parse them as needed:

```python
async def execute(self, app, args: str):
    parts = args.strip().split()
    if len(parts) > 0:
        # handle arguments
        pass
```

## Available app properties and methods

Within `execute()`, the `app` parameter provides the following commonly used interfaces:

- `app.state`: `SessionState` object (message history, current model, etc.)
- `app.api`: `LMStudioClient` object (to send API requests)
- `app.notify(message)`: Send a notification
- `app.refresh_chat()`: Refresh the chat display
- `app.state_manager.save(app.state)`: Save state
- `app.query_one("#msg-input", Input)`: Access the input widget
- `app.query_one("#chat-view", ListView)`: Access the chat view

## Notes

- Command names must be lowercase and cannot contain spaces.
- `execute()` is asynchronous; you can use `await` for async operations.
- It is recommended to add command output to the chat history via `app.state.add_message()` rather than using only `notify()`.
- No other files need to be changed; `_register_commands()` is the only registration entry point.