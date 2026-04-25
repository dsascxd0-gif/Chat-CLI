# 添加命令文档

[EN](./README.md) | [中文](/docs/ADDING_COMMANDS_cn.md)

## 命令系统架构

本应用的命令系统基于以下组件：

- **`Command` (ABC)**: 所有命令的抽象基类，定义 `name`、`description` 和 `execute()` 方法
- **`CommandRegistry`**: 命令注册表，管理所有可用命令
- **`ChatApp._register_commands()`**: 注册命令到应用的入口

## 如何添加新命令

### 步骤 1: 创建命令类

在 `chat_cli/commands.py` 中，继承 `Command` 并实现 `execute()` 方法：

```python
class MyCommand(Command):
    name = "mycommand"          # 命令名（小写，不带 /）
    description = "描述这个命令的作用"

    async def execute(self, app, args: str) -> None:
        # app: ChatApp 实例，可以访问 state、api、notify 等
        # args: 用户输入的参数部分（不含命令名）
        
        if args.strip():
            # 处理带参数的情况
            app.notify(f"参数: {args}")
        else:
            # 不带参数的情况
            app.notify("执行了我的命令")
```
### 步骤 2: 添加导入

在 `chat_cli/app.py` 的第16行处导入你的命令：

```python
from .commands import CommandRegistry, HelpCommand, ClearCommand, MyCommand, ThemeCommand, QuitCommand
```
### 步骤 3: 注册命令

在 `chat_cli/app.py` 的 `ChatApp._register_commands()` 方法中注册：

```python
def _register_commands(self):
    self.model_cmd = ModelCommand()
    self.command_registry.register(self.model_cmd)
    for cmd_cls in [HelpCommand, ClearCommand, MyCommand, ThemeCommand, QuitCommand]:
        self.command_registry.register(cmd_cls())
```

### 步骤 4: 测试

运行应用并测试：
```powershell
python main.py
```
输入 `/mycommand` 或 `/mycommand 参数` 测试效果。

## 示例：添加 /time 命令

以下是一个完整示例，添加显示当前时间的命令：

**在 `chat_cli/commands.py` 中添加：**

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

**在 `chat_cli/app.py` 的第16行导入**

```python
from .commands import CommandRegistry, HelpCommand, ClearCommand, TimeCommand, ThemeCommand, QuitCommand
```

**在 `chat_cli/app.py` 的 `_register_commands()` 中注册：**

```python
for cmd_cls in [HelpCommand, ClearCommand, TimeCommand, ModelCommand, ThemeCommand, QuitCommand]:
    self.command_registry.register(cmd_cls())
```

## 命令参数处理

命令参数通过 `args` 字符串传递，可自行解析：

```python
async def execute(self, app, args: str):
    parts = args.strip().split()
    if len(parts) > 0:
        # 处理参数
        pass
```

## 可用的 App 属性和方法

在 `execute()` 中，`app` 参数提供以下常用接口：

- `app.state`: `SessionState` 对象（消息历史、当前模型等）
- `app.api`: `LMStudioClient` 对象（发送 API 请求）
- `app.notify(message)`: 发送通知
- `app.refresh_chat()`: 刷新聊天显示
- `app.state_manager.save(app.state)`: 保存状态
- `app.query_one("#msg-input", Input)`: 访问输入框
- `app.query_one("#chat-view", ListView)`: 访问聊天视图

## 注意事项

- 命令名必须是小写，不能包含空格
- `execute()` 是异步的，可用 `await` 调用异步操作
- 命令输出建议通过 `app.state.add_message()` 添加到聊天记录，而非仅 `notify()`
- 修改后无需改其他文件，`_register_commands()` 是唯一的注册入口
