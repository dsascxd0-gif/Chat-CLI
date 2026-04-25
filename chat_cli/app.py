import asyncio
import os
import time
from textual.app import App, ComposeResult
from textual.widgets import Input, Static, ListView, ListItem
from textual.containers import Vertical, Horizontal
from textual import work
from textual.binding import Binding
from rich.markdown import Markdown
from rich.text import Text
from rich.console import Group

from .api import LMStudioClient, Message, StreamChunk
from .state import SessionState, StateManager
from .session_manager import SessionManager
from .commands import CommandRegistry, HelpCommand, ClearCommand, BaseURLCommand, APIKeyCommand, NewSessionCommand, TitleCommand, ModelCommand, ThemeCommand, QuitCommand, SystemPromptCommand, DeleteCommand, ReloadBaseURLCommand
from .logging_config import log_operation, log_error, log_warning, log_info
from .header import HeaderBar


class CommandInput(Input):
    BINDINGS = [
        Binding("tab", "complete", "Complete command", show=False),
    ]

    def action_complete(self):
        text = self.value

        # Handle model completion for /model command
        if text.startswith("/model "):
            prefix = text[7:]
            if not hasattr(self.app, 'model_cmd') or not hasattr(self.app.model_cmd, '_available_models'):
                return
            models = self.app.model_cmd._available_models
            if not models:
                return

            matches = [m for m in models if m.startswith(prefix)]
            if not matches:
                return

            if len(matches) == 1:
                self.value = f"/model {matches[0]}"
            else:
                lcp = os.path.commonprefix(matches)
                if lcp != prefix:
                    self.value = f"/model {lcp}"

            self.cursor_position = len(self.value)
            return

        if not text.startswith("/") or " " in text:
            return

        prefix = text[1:]
        if not prefix:
            return

        commands: dict = self.app.command_registry.all()
        matches = [name for name in commands if name.startswith(prefix)]

        if not matches:
            return

        if len(matches) == 1:
            self.value = f"/{matches[0]} "
        else:
            lcp = os.path.commonprefix(matches)
            if lcp != prefix:
                self.value = f"/{lcp}"

        self.cursor_position = len(self.value)


class MessageWidget(Static):
    _frames = ["Thinking", "tHinking", "thInking", "thiNking", "thinKing", "thinkIng", "thinkiNg", "thinkinG"]

    def __init__(self, message: Message):
        super().__init__()
        self.message = message
        self.thinking_start = None
        self.thinking_frame = 0

    def compose(self) -> ComposeResult:
        role = "You" if self.message.role == "user" else "AI"
        reasoning = getattr(self.message, 'reasoning', '')
        
        if self.message.role != "user" and reasoning:
            reasoning_text = Text()
            reasoning_text.append("Reasoning:\n", style="bold grey50")
            reasoning_text.append(reasoning, style="grey50")
            content_md = Markdown(f"**{role}**: {self.message.content}")
            group = Group(reasoning_text, content_md)
            yield Static(group, id="content")
        else:
            yield Static(Markdown(f"**{role}**: {self.message.content}"), id="content")

    def start_thinking(self):
        self.thinking_start = time.time()
        self.thinking_frame = 0
        log_info("AI thinking started")

    def compose(self) -> ComposeResult:
        role = "You" if self.message.role == "user" else "AI"
        reasoning = getattr(self.message, 'reasoning', '')
        
        if self.message.role != "user" and reasoning:
            reasoning_text = Text()
            reasoning_text.append("Reasoning:\n", style="bold grey50")
            reasoning_text.append(reasoning, style="grey50")
            content_md = Markdown(f"**{role}**: {self.message.content}")
            group = Group(reasoning_text, content_md)
            yield Static(group, id="content")
        else:
            yield Static(Markdown(f"**{role}**: {self.message.content}"), id="content")

    def update_thinking(self):
        if self.thinking_start is None:
            return
        elapsed = int(time.time() - self.thinking_start)
        mins = elapsed // 60
        secs = elapsed % 60
        time_str = f"{mins}:{secs:02d}"
        frame = self._frames[self.thinking_frame % len(self._frames)]
        self.thinking_frame += 1
        display = f"> {frame} {time_str}"
        self.query_one("#content", Static).update(Markdown(f"**AI**: {display}"))

    def update_content(self, content: str, thinking: bool = False, reasoning: str = ""):
        self.message.content = content
        self.message.reasoning = reasoning
        self._reasoning = reasoning
        role = "You" if self.message.role == "user" else "AI"
        
        if thinking and not content:
            display = f"> {self._frames[0]} 0:00"
            self.query_one("#content", Static).update(Markdown(f"**{role}**: {display}"))
        else:
            if role == "AI" and reasoning:
                reasoning_text = Text()
                reasoning_text.append("Reasoning:\n", style="bold grey50")
                reasoning_text.append(reasoning, style="grey50")
                content_md = Markdown(f"**{role}**: {content}")
                group = Group(reasoning_text, content_md)
                self.query_one("#content", Static).update(group)
            else:
                self.query_one("#content", Static).update(Markdown(f"**{role}**: {content}"))

    def update_reasoning(self, reasoning: str):
        self._reasoning = reasoning


class ChatApp(App):
    CSS = """
    Screen { layout: horizontal; }
    #sidebar { width: 20; height: 100%; background: $panel; padding: 0; }
    Vertical { width: 100%; }
    #session-list { height: 1fr; padding: 0; margin: 0; }
    ListItem { padding: 0 1; margin: 0; }
    #main-panel { width: 1fr; layout: vertical; }
    #header { height: 1; }
    #header-date { width: 33%; content-align: left middle; }
    #header-time { width: 34%; content-align: center middle; }
    #header-tokens { width: 33%; content-align: right middle; }
    #chat-view { height: 1fr; overflow-y: auto; }
    #input-bar { dock: bottom; height: 3; }
    Input { width: 100%; }
    #suggestions { dock: bottom; height: 1; background: $surface; color: $text-muted; display: none; }
    #suggestions.visible { display: block; }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+z", "undo", "Undo"),
    ]

    def __init__(self):
        super().__init__()
        self.state = SessionState()
        self.session_mgr = SessionManager()
        self.command_registry = CommandRegistry()
        self._register_commands()
        self._msg_widgets = {}
        self.current_session_file = ""
        self._thinking_task = None
        self._pending_delete = False
        self._pending_clear = False

    def _register_commands(self):
        self.model_cmd = ModelCommand()
        self.command_registry.register(self.model_cmd)
        for cmd_cls in [HelpCommand, ClearCommand, BaseURLCommand, APIKeyCommand, NewSessionCommand, TitleCommand, ThemeCommand, QuitCommand, SystemPromptCommand, DeleteCommand, ReloadBaseURLCommand]:
            self.command_registry.register(cmd_cls())

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("Sessions", id="sidebar-title")
                yield ListView(id="session-list")
            with Vertical(id="main-panel"):
                yield HeaderBar(id="header")
                yield ListView(id="chat-view")
                with Horizontal(id="input-bar"):
                    yield CommandInput(placeholder="Type a message or /help...", id="msg-input")
                yield Static("", id="suggestions")

    async def on_mount(self):
        # 迁移旧 state.json
        self.session_mgr.migrate_from_old()
        
        # 获取会话列表
        sessions = self.session_mgr.list_sessions()
        if not sessions:
            # 创建第一个会话
            self.current_session_file = self.session_mgr.create_session("session-1")
        else:
            # 加载最近或第一个会话
            latest = self.session_mgr.get_latest_session()
            self.current_session_file = latest or sessions[0]["filename"]
        
        # 加载会话状态
        self.state = self.session_mgr.load_session(self.current_session_file)
        
        # 初始化 API
        base_url = self.state.base_url
        api_key = self.state.api_key
        self.api = LMStudioClient(base_url=base_url, api_key=api_key)
        
        # 刷新UI
        self.refresh_session_list()
        self.refresh_chat()
        self.header = self.query_one("#header", HeaderBar)
        self.query_one("#msg-input").focus()
        
        # 加载模型
        try:
            models = await self.api.list_models()
            self.model_cmd.set_models(models)
            log_operation("Models loaded", f"{len(models)} models")
        except Exception as e:
            log_warning(f"Failed to load models: {e}")

    def _save_current_session(self):
        """保存当前会话"""
        if self.current_session_file:
            title = self.session_mgr.get_title(self.current_session_file)
            self.session_mgr.save_current(self.state, self.current_session_file, title)

    def refresh_session_list(self):
        """刷新侧边栏会话列表"""
        lv = self.query_one("#session-list", ListView)
        lv.clear()
        
        sessions = self.session_mgr.list_sessions()
        for s in sessions:
            # 创建带标题的列表项，显示 title
            item = ListItem(Static(f"{s['title']}", markup=False))
            lv.append(item)
        
        # 选中当前会话
        for i, s in enumerate(sessions):
            if s["filename"] == self.current_session_file:
                lv.index = i
                break

    async def on_list_view_selected(self, event: ListView.Selected):
        if event.list_view.id == "session-list" and event.item is not None:
            sessions = self.session_mgr.list_sessions()
            idx = event.index
            if 0 <= idx < len(sessions):
                new_file = sessions[idx]["filename"]
                if new_file != self.current_session_file:
                    self._save_current_session()
                    self.current_session_file = new_file
                    self.state = self.session_mgr.load_session(new_file)
                    if self._thinking_task:
                        self._thinking_task.cancel()
                    self.refresh_chat()
                    self.refresh_session_list()

    def refresh_chat(self):
        lv = self.query_one("#chat-view", ListView)
        lv.clear()
        self._msg_widgets.clear()
        for i, m in enumerate(self.state.messages):
            w = MessageWidget(m)
            self._msg_widgets[i] = w
            lv.append(ListItem(w))
        lv.scroll_end()

    def _add_message_widget(self, message: Message) -> MessageWidget:
        lv = self.query_one("#chat-view", ListView)
        w = MessageWidget(message)
        self._msg_widgets[len(self.state.messages) - 1] = w
        lv.append(ListItem(w))
        return w

    def _get_input(self) -> Input:
        return self.query_one("#msg-input", Input)

    async def on_input_changed(self, event: Input.Changed):
        text = event.value
        suggestions = self.query_one("#suggestions")
        
        if not text.startswith("/"):
            suggestions.remove_class("visible")
            return
        
        if text.startswith("/model "):
            prefix = text[7:]
            models = getattr(self.model_cmd, '_available_models', [])
            if models:
                matches = [m for m in models if m.startswith(prefix)]
                if matches:
                    suggestions.update(" | ".join(matches[:5]))
                    suggestions.add_class("visible")
                else:
                    suggestions.remove_class("visible")
            return
        
        if len(text) == 1:
            cmds = list(self.command_registry.all().keys())
            suggestions.update(" | ".join([f"/{c}" for c in cmds]))
            suggestions.add_class("visible")
        else:
            prefix = text[1:].lower()
            cmds = [f"/{c}" for c in self.command_registry.all().keys() if c.startswith(prefix)]
            if cmds:
                suggestions.update(" | ".join(cmds))
                suggestions.add_class("visible")
            else:
                suggestions.remove_class("visible")

    async def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        if text:
            if text.startswith("/"):
                await self._handle_command(text[1:])
            else:
                self._send_message(text)
            event.input.value = ""

    async def _handle_command(self, cmdline: str):
        if not cmdline.strip():
            self.notify("Usage: /command [args]")
            return
        parts = cmdline.split(None, 1)
        name = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        cmd = self.command_registry.get(name)
        if cmd:
            await cmd.execute(self, args)
            log_operation(f"Command: /{name}", args or "no args")
        else:
            self.notify(f"Unknown command: /{name}")
            log_warning(f"Unknown command: /{name}")

    @work
    async def _send_message(self, content: str):
        self.state.add_message("user", content)
        self._add_message_widget(Message("user", content))
        self._get_input().value = ""
        log_operation("User message", content[:50])

        # 创建唯一的 AI 消息对象，直接添加到 state
        assistant_msg = Message("assistant", "", reasoning="")
        self.state.messages.append(assistant_msg)
        widget = self._add_message_widget(assistant_msg)

        widget.start_thinking()
        thinking_task = asyncio.create_task(self._update_thinking_loop(widget))

        full_reasoning = ""
        full_content = ""
        first_token = True
        content_start_time = None
        session_tokens = 0

        try:
            async for chunk in self.api.chat_stream(self.state.messages[:-1], self.state.model, self.state.system_prompt):
                now = time.time()
                
                if first_token:
                    # 开始计时，只有超过 1 秒才取消 thinking 动画
                    if content_start_time is None:
                        content_start_time = now
                    elif now - content_start_time >= 1.0:
                        # 延迟 1 秒后取消 thinking确保不会闪烁
                        thinking_task.cancel()
                        first_token = False
                
                if chunk.type == "usage":
                    session_tokens += int(chunk.content)
                    self.header.update_token_count(session_tokens)
                    continue
                
                if isinstance(chunk, str):
                    full_content += chunk
                    assistant_msg.content = full_content
                    widget.update_content(full_content, thinking=False, reasoning=full_reasoning)
                else:
                    if chunk.type == "reasoning":
                        full_reasoning += chunk.content
                        assistant_msg.reasoning = full_reasoning
                        widget.update_reasoning(full_reasoning)
                    elif chunk.type == "content":
                        full_content += chunk.content
                        assistant_msg.content = full_content
                        assistant_msg.reasoning = full_reasoning
                    widget.update_content(full_content, thinking=False, reasoning=full_reasoning)
                
                self.query_one("#chat-view", ListView).scroll_end()
        except Exception as e:
            thinking_task.cancel()
            log_error(f"API error: {e}", exc_info=True)
            self.notify(f"API error: {e}")
            return

        thinking_task.cancel()
        # 确保最终状态正确保存
        assistant_msg.content = full_content
        assistant_msg.reasoning = full_reasoning
        widget.update_content(full_content, thinking=False, reasoning=full_reasoning)
        self._save_current_session()
        log_operation("AI response", f"content={len(full_content)}, reasoning={len(full_reasoning)}")

    async def _update_thinking_loop(self, widget: MessageWidget):
        try:
            while True:
                await asyncio.sleep(1)
                widget.update_thinking()
        except asyncio.CancelledError:
            pass

    async def action_undo(self):
        msg = self.state.pop_last()
        if msg:
            self.refresh_chat()
            self._save_current_session()
            self.notify(f"Removed last message ({msg.role})")
            log_operation("Undo", msg.role)
        else:
            self.notify("Nothing to undo")

    async def action_quit(self):
        self._save_current_session()
        log_operation("App quit", f"{len(self.state.messages)} messages in {self.current_session_file}")
        self.exit()


if __name__ == "__main__":
    ChatApp().run()
