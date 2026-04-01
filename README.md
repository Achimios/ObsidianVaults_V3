# CyberDomain V3

> 建造者 → 来访者：你可以直接把这个 Vault 的路径丢给你的 AI，让它来为你详细剖析本项目的理念和架构。

> If you plan to translate or adapt this project into your language/workflow — ask your AI to do it, with the philosophy and methodology of this project as context.

---

## 这是什么

一个把 AI 当做工程搭档（而不是聊天工具）来使用的 Obsidian Vault。

核心思路：通过分层指令注入（`copilot-instructions.md` / `AGENTS.md` / `*.instructions.md`），让不同 AI 工具在不同工作区域自动切换人格和规则，把 AI 行为工程化、可维护化。

---

## 快速起点

- 看 [[-where_continue]] — 当前工作在哪，下一步是什么
- 看 [[1_人类接入手册_修订版]] — VS Code + Copilot 配置一张图
- `.github/` 目录（Obsidian 不显示，用 VS Code 看）— AI 指令、Skills、Agents 全在这

---

## 文件编辑约定

- **Obsidian 可见的 `.md` 文件**（路径中无 `.` 开头文件夹）：优先用 Obsidian CLI 操作，保留 wikilink 引用关系。改完文件名后，grep 检查其他文件中是否有需要同步更新的引用。
- **配置/代码文件**（`.github/`、`.venv/` 等）：用 VS Code 或终端操作。
- **路径统一用相对路径**（`./` `../` `~/` `%USERPROFILE%\`），避免写死绝对路径。

---

## 目录一览

| 目录 | 内容 |
|---|---|
| `-Vault空间/` | 代码项目、义体模块（TTS/HID/视觉）、自动化任务 |
| `-Vault自身进化/` | Vault 架构设计、AI 配置参考文档 |
| `-人类思维笔记/` | 和 AI 共同思考的笔记（哲学、方法论、AI工作流） |
| `.github/` | Copilot 铁律、Instructions、Skills、Agents（IDE 可见）|

---

> 更深层的细节——叫你的 AI 来挖，这里不多写了。
