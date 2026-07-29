# Project Manager · 项目管家

> Claude Code 用户的私项目管家 — 自动追踪、可视化检索、一键继续开发
> A personal project tracker for Claude Code users — auto-track, visually search, one-click resume.

---

## ✨ 功能 / Features

- 🤖 **自动记录** — Claude Code Skill 检测到新项目时自动写入索引，无需手动操作
- 🔍 **智能搜索** — 支持项目名称、描述、技术栈、标签的关键词模糊检索
- 📅 **时间线浏览** — 按年份分组查看所有项目，一目了然
- 🌐 **Web 面板** — 暗色主题可视化界面，卡片 / 时间线双视图切换
- 📂 **一键继续** — 点击按钮自动打开项目目录 + 启动 Claude Code 继续开发
- 📦 **便携 EXE** — PyInstaller 打包为单个 `ProjectManager.exe`，双击即用，无需 Python

---

## 🚀 快速开始 / Quick Start

### 方式一：EXE（推荐）

1. 从 [Releases](https://github.com/qingyaxuan/project-manager/releases) 下载 `ProjectManager.exe`
2. 双击运行 → 浏览器自动打开 `http://localhost:8765/web-ui/`
3. 数据自动保存在 EXE 同目录下的 `projects-data.json`

### 方式二：源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python server.py

# 浏览器访问
# http://localhost:8765/web-ui/index.html
```

### 在 Claude Code 中使用

将 `.claude/skills/project-manager/` 复制到你项目的 `.claude/skills/` 目录下，然后用自然语言触发：

| 你说的 | 效果 |
|--------|------|
| 「搜索项目 XX」 | 全文模糊搜索 |
| 「项目时间线」 | 按年份浏览 |
| 「打开项目面板」 | 启动 Web 界面 |
| 「继续开发 XX」 | 打开目录 + 启动 Claude |

---

## 🛠 构建 EXE / Build EXE

```bash
pip install pyinstaller
pyinstaller --onefile --name ProjectManager --add-data "web-ui;web-ui" server.py
```

或双击 `build-exe.bat`，构建产物在 `dist/ProjectManager.exe`。

---

## 📁 文件结构 / Structure

```
project-manager/
├── server.py                  # HTTP 服务器 + API（Python 标准库，零外部依赖）
├── web-ui/
│   └── index.html             # Web 面板（纯 HTML/CSS/JS，无框架）
├── projects-data.sample.json  # 数据模板（首次运行自动创建 projects-data.json）
├── build-exe.bat              # 一键构建 EXE 脚本
├── requirements.txt           # 构建依赖（仅 PyInstaller）
└── .claude/
    └── skills/
        └── project-manager/
            └── SKILL.md       # Claude Code 自动记录 Skill
```

---

## 📄 License

MIT
