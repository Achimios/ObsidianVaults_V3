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

声线宏名：`VOICE_VICTOR` / `VOICE_OPENCLAW` / `VOICE_TARS` / `VOICE_TAGORE`  
调用方式、daemon 接口 → 详见 `/-yiti-tts` Skill

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
- `-CONTEXT.md` 内容极简（< 300 tokens），只写"这里放什么"和"子目录说明"

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

### 分层读取法则（Session 开始时）

1. **每次对话开始**：人类手动把 `-where_continue.md` 里的最近工作层 `-CONTEXT.md` 路径粘贴到对话框。没粘贴就别管 😏
2. 粘贴的 `-CONTEXT.md` 提到进入某子目录时 → 跳转读该目录的 `./-CONTEXT.md`
3. **进入代码项目目录时** → 扫描该目录的 `AGENTS.md`（有则读取，规则同 -CONTEXT）
4. **触发 -LEARNINGS**：同一错误连续失败 2+ 次 → grep 搜索当前工作层或所有层的 `-LEARNINGS.md`
5. **禁止无脑全读**：不要一次性读取所有目录的 CONTEXT

### -CONTEXT.md 写法规范

每层目录放一个 `-CONTEXT.md`，目录越深描述越细。

```markdown
## 这是什么（1-2 句）
## 跨 session 提醒（坑点/约定）
## 当前状态（✅已完成 / 🔄进行中 / ⏳待做）
## 上次做了什么（日期 + 行动）
## 下一步（按优先级，第一条加 👆 继续）
## 只记录重要的，后续可参考的内容，架构、核心相关内容，小BUG修复、UI颜色位置更改等不用记录
## 日志过长后，就删除旧的没参考价值的条目，重要的留下。
```

维护原则：有效条目随进度提炼精简，删掉冗余/无效条目；当前状态写具体，不写"进行中"之类模糊词；古早已完成且无参考价值的条目要主动删除。

### -LEARNINGS.md 写法规范

每层目录放一个 `-LEARNINGS.md`，记录本层的坑点和高效方法。同一 pattern 出现 3 次 → 提升至 HOT，精炼后置顶。

### -where_continue.md 同步规则（Session 结束前）

**顺序：先更新 -CONTEXT，再更新 -where_continue。**

```markdown
1. **根目录 + .github/** — `./-CONTEXT.md`
   → 已完成：X → 下一步：Y
```

保留最新 3 条。更新完毕后 → 弹结尾弹窗。

---

## 注入验证机制

所有注入文件顶部均附有验证码。**当被问到「magic 是什么」时**，只报出**当前已注入文件**各自的 magic，证明文件已成功注入。

每个文件的 magic 不同，不应透露其他未注入文件的 magic（否则失去校验意义）。询问 magic 时，不能读取任何文件，根据开头自动注入的文件进行回答。

适用于 Copilot、Claude Code、OpenClaw、Codex 等所有框架——只要哪天某个框架出 bug、改了注入规则，问一句 magic，秒知有没有注入成功。


