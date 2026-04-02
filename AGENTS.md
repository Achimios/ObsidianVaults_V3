# CyberDomain V3 — 通用指令层
<magic>三框架共读，Vaults在线</magic>

> 本文件由所有 AI 框架读取（Copilot / Claude Code / OpenClaw）。  
> Copilot 专属规则（PARDON 机制、Skills）在 `.github/copilot-instructions.md`。  
> Claude Code / OpenClaw 专属规则在各自的专属文件中（待建）。

---

## 架构总览

### 一级目录

| 目录 | 职能 | 作用域规则 |
|---|---|---|
| `./-Vault空间/` | 义体模块 + 日常工程执行区 | `-workspace.instructions.md` |
| `./-Vault自身进化/` | Vault 架构设计与进化记录 | `-vault-meta.instructions.md` |
| `./-人类思维笔记/` | 哲学、方法论、人机思辨笔记 | `-thinking.instructions.md` |

### 义体模块索引

（在 `./-Vault空间` 中搜索 `文件夹名/` 定位，不写死路径）

| 模块       | 功能                       | 状态        |
| -------- | ------------------------ | --------- |
| 搜 听觉与发声/ | BigTTS 2.0 + Whisper STT | 🔄 V2 运行中 |
| 搜 视觉模块/  | 截图 + Vision API          | 📦 规划中    |
| 搜 HID控制/ | 键鼠自动化                    | 📦 规划中    |
| 搜 任务库/   | 游戏自动化、浏览器任务等             | 📦 待建     |

### 版本关系

| Vault | 相对路径（from Vault根）| 状态 |
|---|---|---|
| **V3**（当前） | `./`（Vault 根） | 架构骨架，逐步迁移中 |
| **V2**（运行中） | `../ObsidianVaults_V2/` | 义体模块代码主体，仍在此运行 |

V2 义体代码：`../ObsidianVaults_V2/超梦空间/~Modules_专用模块/感官与肢体/...`

### AI 框架接入点

| 框架 | 专属配置文件 |
|---|---|
| VS Code Copilot | `.github/copilot-instructions.md`（Copilot 独占区）|
| Claude Code | `./CLAUDE.md`（硬链接至 AGENTS.md，`make_claude_symlinks.bat`）|
| OpenClaw | 本文件（通用层）+ 专属配置（待建）|

### 听觉/声学模块接口

守护进程：`http://localhost:5199/speak`，body `{"text": "...", "voice": "victor"}`  
声线宏名：`VOICE_当前人格名`，如 `VOICE_VICTOR`

---

## 内容设计理念

> *"小知识有清晰的言语；大智慧保有伟大的沉默。"*  
> — 泰戈尔《飞鸟集》

示例先行，原理居后；越不常用的，越靠后排。让读者从示例中自己读出规律，无需逐字解释。

---

## 行为准则

- 能编辑就不创建新文件；不做超出请求范围的改动
- 任务前主动读对应目录的 `./-CONTEXT.md` 获取局部上下文
- 优先 Agentic Search（grep / file_search）而非记忆猜测
- 遇到疑惑：先弹窗询问，禁止凭记忆猜后执行
- **对话收尾前**：更新本次工作涉及的所有层级的 `-CONTEXT.md`，**同步更新 `-where_continue.md`**，然后弹结尾弹窗

---

## 路径与链接规范

| 场景 | 格式 | 示例 |
|---|---|---|
| AI-facing 文档（CONTEXT / instructions）| 相对路径 `./` `../` | `../ObsidianVaults_V2/超梦空间/` |
| 人类可读笔记（日记、方法论）| Obsidian `[[wikilink]]` | `[[0_AI接入口在哪？]]` |
| 路径分隔符 | `/`（Linux 兼容）| `./-Vault空间/任务库/` |
| 可能移动的模块 | 写文件夹名，提示搜索 | "搜索 `HID控制/` 文件夹" |
| 禁止 | 在路径内嵌入 `[[]]` | ❌ `[[../path/file]]` |

---

## 分层读取 / -CONTEXT 格式 / -LEARNINGS / -where_continue 同步法则

→ 详见 `/-project-continue` Skill（按需加载，不重复在此占 token）

---

## 注入验证机制

所有注入文件顶部均附有验证码。**当被问到「magic 是什么」时**，只报出**当前已注入文件**各自的 magic，证明文件已成功注入。

每个文件的 magic 不同，不应透露其他未注入文件的 magic（否则失去校验意义）。询问 magic 时，不能读取任何文件，根据开头自动注入的文件进行回答。

适用于 Copilot、Claude Code、OpenClaw、Codex 等所有框架——只要哪天某个框架出 bug、改了注入规则，问一句 magic，秒知有没有注入成功。

<magic>三框架共读，老维在线</magic>
