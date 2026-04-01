# CyberDomain V3 — 通用指令层
<!-- magic: 三框架共读，Vaults在线 -->

> 本文件由所有 AI 框架读取（Copilot / Claude Code / OpenClaw）。  
> Copilot 专属规则（PARDON 机制、Skills）在 `.github/copilot-instructions.md`。  
> Claude Code / OpenClaw 专属规则在各自的专属文件中（待建）。

---

## 架构总览

### 一级目录

| 目录 | 职能 | 作用域规则 |
|---|---|---|
| `./-Vault空间/` | 义体模块 + 日常工程执行区 | `workspace.instructions.md` |
| `./-Vault自身进化/` | Vault 架构设计与进化记录 | `vault-meta.instructions.md` |
| `./-人类思维笔记/` | 哲学、方法论、人机思辨笔记 | `thinking.instructions.md` |

### 义体模块索引

（在 `./-Vault空间` 中搜索 `文件夹名/` 定位，不写死路径）

| 模块 | 功能 | 状态 |
|---|---|---|
| 搜 听觉与发声/ | BigTTS 2.0 + Whisper STT | 🔄 V2 运行中 |
| 搜 视觉模块/ | 截图 + Vision API | 📦 规划中 |
| 搜 HID控制/ | 键鼠自动化 | 📦 规划中 |
| 搜 任务库/ | 游戏自动化、浏览器任务等 | 📦 待建 |

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
| Claude Code | `./CLAUDE.md`（待建）|
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

## 分层读取法则

1. **每次对话开始**：人类手动根据 `-where_continue.md` 中记录的最近工作层，复制需要继续的 `-CONTEXT.md` 路径粘贴到 AI 对话框。没粘贴你就别管😏
2. 人类粘贴的 `-CONTEXT.md` 中提到进入某子目录任务时，跳转读该目录的 `./-CONTEXT.md`
3. **进入代码项目目录时**：扫描该项目根目录的 `AGENTS.md`（如存在则读取，规则同 -CONTEXT）
4. **触发 -LEARNINGS**：同一错误连续失败 2+ 次 → grep 搜索当前工作层的，或所有层的 `-LEARNINGS.md`
5. **禁止无脑全读**：不要一次性读取所有目录的 CONTEXT

---

## -CONTEXT 写法规范

分层上下文 `-CONTEXT.md` 文件，每层写入工作在本层的上下文，目录越深，描述越细

```
## 这是什么（1-2 句）
## 跨 session 提醒（坑点/约定）
## 当前状态（✅已完成 / 🔄进行中 / ⏳待做）
## 上次做了什么（日期 + 行动）
## 下一步（按优先级，第一条加 👆 继续）

## 有效条目随进度完成度越高，可以提炼后精简
## 检查冗余的、无效条目删掉
## 当前条目的状态要写具体
```

## -LEARNINGS 写法规范
分层经验记忆 `-LEARNINGS`文件，每层写入工作在本层的经验和教训，高效方法。

```
## 多次出错的地方找到解决方法后写入
## 找到一个高效方法后写入
## 多次提及某个话题或方法时，提升至HOT，提炼后写入

---

## -where_continue.md 同步规则

**每次对话结束时必须同步更新以下两个文件**（顺序：先 CONTEXT，再 where_continue）：

1. **`-CONTEXT.md`**（工作层级）：记录做了什么、下一步是什么
2. **`-where_continue.md`**（V3 根目录）：记录"从哪里继续"（第一条 = 最近工作层 + 下一步说明）

`-where_continue.md` 格式示例：
```
1. **根目录** — `./-CONTEXT.md`
   → 正在做：义体模块迁移 TTS 部分
```

---

## 注入验证机制

所有注入文件顶部均附有验证码。**当被问到「magic 是什么」时**，只报出**当前已注入文件**各自的 magic，证明文件已成功注入。

每个文件的 magic 不同，不应透露其他未注入文件的 magic（否则失去校验意义）。询问某个 agent 的 magic，此时不能读取任何文件，而是根据回答开始前自动注入的文件进行回答。

适用于 Copilot、Claude Code、OpenClaw、Codex 等所有框架——只要哪天某个框架出 bug、改了注入规则，问一句 magic，秒知有没有注入成功。

<!-- magic: 三框架共读，老维在线 -->
