# Chat CLI

与 AI 对话的 TUI 应用程序，主要使用Textual库

[EN](./README.md) | [中文](./README_cn.md)

## 功能

- 与 LM Studio / OpenAI 兼容 API 对话
- Markdown 渲染
- 思考动画显示
- 命令自动补全
- 自动保存会话状态
- 日志记录

## 安装

```powershell
pip install -r requirements.txt
```

## 运行

```powershell
python main.py
```

## 命令

- `/help` - 显示帮助
- `/baseurl` - 更改Base URL（更改的Base URL需要添加http或者https头部，例如`https://api.example.com/v1`或者`http://api.example.com/v1`）语法: `/baseurl <BaseURL>`
- `/apikey` - 更改apikey，语法`/apikey apikey`
- `/new` - 新建对话，语法`/new <title>`
- `/title` - 更改对话标题，语法`/title <title>`
<<<<<<< HEAD
- `/del` - 删除会话，语法`/del <session name>` 输入两次来确认删除
- `/prompt` - 更改系统提示词，语法`/prompt <prompt>`
- `/model` - 查看/切换模型，语法`/model <model>`
- `/clear` - 清除对话 输入两次来确认删除
=======
- `/model` - 查看/切换模型，语法`/model <model>`
- `/clear` - 清除对话（此操作不可逆）
>>>>>>> 4ade61ac2544131ba1f88af8e4e837b82d77a583
- `/quit` - 退出
- `/theme` - 切换主题（目前只有monokai主题）语法: /theme theme

## 默认快捷键

- `Ctrl+Z` - 撤销
- `Ctrl+C` - 退出

## 日志

日志保存在 `logs/` 目录

## 特别声明

本项目是我在课余时间学习 Textual 的练习作品，核心功能可用但细节不完善。
由于学业繁忙，无法保证及时回复 issue/PR，欢迎 fork 自用或提 PR，我会尽力在周末查看。
