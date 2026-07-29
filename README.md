# Project Manager · 项目管家

> Claude Code 用户的本地项目管理器 — 手动追踪、可视化检索、一键继续开发
> A personal project tracker for Claude Code users — manually track, visually search, one-click resume.

---

## ✨ 功能

- 📋 **CRUD 管理** — Web 面板新增/编辑/删除项目，支持名称、描述、技术栈、标签、亮点
- 🔍 **智能搜索** — 关键词模糊检索项目名称、描述、技术栈、标签
- 📅 **时间线浏览** — 按年份分组查看所有项目
- 🌐 **暗色 Web 面板** — 卡片 / 时间线双视图切换，无框架纯原生 JS
- 📂 **一键继续** — 点击按钮自动打开项目目录 + 启动 Claude Code 继续开发
- 🔍 **自动扫描** — 检测 `D:\Claude program\` 下未追踪的新目录，一键添加
- 🗑️ **安全删除** — 删除面板记录时同步删除对应项目目录（仅限 `D:\Claude program\` 下）
- 📦 **离线可用** — 内嵌数据快照，双击 HTML 文件即可查看，无需启动服务器

---

## 🚀 快速开始

### 启动服务器

```bash
cd D:\claude-projects-manager
python server.py
```

浏览器打开 `http://localhost:8765/web-ui/index.html`

**不需要安装任何依赖** — 服务器仅使用 Python 标准库（`http.server`、`json` 等）。

### 离线查看

直接双击打开 `web-ui\index.html`，无需启动服务器。数据来自上次服务器运行时写入的内嵌快照。

---

## 📖 使用说明

### Web 面板操作

| 操作 | 说明 |
|------|------|
| **查看项目** | 打开面板自动加载，卡片视图/时间线视图可切换 |
| **搜索** | 顶部搜索框输入关键词，实时过滤 |
| **新增项目** | 点击「＋ 新增」填写表单，路径默认 `D:\Claude program\项目名` |
| **编辑项目** | 点击卡片上的 ✏️ 按钮，修改后提交 |
| **删除项目** | 点击卡片上的 🗑️ 按钮，确认后删除记录 + 目录 |
| **打开目录** | 点击卡片上的 📂 按钮，在资源管理器中打开项目文件夹 |
| **继续开发** | 点击卡片上的 ▶️ 按钮，打开目录并启动 Claude Code |
| **扫描新项目** | 点击「扫描」按钮，检测 `D:\Claude program\` 下未追踪的目录 |
| **刷新数据** | 点击 🔄 按钮刷新面板数据 |

### API 接口

所有数据操作通过 REST API，方便脚本调用：

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/projects` | 获取全部项目 |
| `POST` | `/api/projects` | 创建新项目 |
| `PUT` | `/api/projects/<id>` | 更新项目 |
| `DELETE` | `/api/projects/<id>` | 删除项目 |
| `GET` | `/api/scan` | 扫描未追踪目录 |
| `GET` | `/api/status` | 服务器状态 |
| `GET` | `/api/open?path=...` | 在资源管理器打开目录 |
| `GET` | `/api/continue?name=...&path=...` | 打开目录 + 启动 Claude Code |

### 卸载

双击 `uninstall.bat`，按提示操作。

---

## 📁 文件结构

```
project-manager/
├── server.py              # HTTP 服务器 + REST API（Python 标准库，零外部依赖）
├── web-ui/
│   └── index.html          # Web 面板（纯 HTML/CSS/JS，无框架）
├── projects-data.json      # 项目数据（JSON 格式）
├── uninstall.bat           # 一键卸载程序
├── requirements.txt        # 可选：PyInstaller 构建依赖
├── README.md               # 本文件
└── .claude/
    └── skills/
        └── project-manager/
            └── SKILL.md    # Claude Code Skill（自然语言触发）
```

---

## ⚙️ 配置

编辑 `server.py` 顶部常量：

```python
PORT = 8765                    # 服务端口
DEFAULT_PROJECT_DIR = r"D:\Claude program"   # 项目存放路径
CLAUDE_CMD = r"C:\Users\...\npm\claude.cmd"  # Claude Code CLI 路径
```

---

## 📄 License

MIT
