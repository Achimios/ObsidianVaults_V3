# CONTEXT — 赛博王国 V3 根目录

## 这是什么
V3 Vault 根目录。含人类导航（[[1_人类接入手册]]）、AI 通用接入层（[[0_AI接入口在哪？]]）、AI 固件（`.github/`）。
**一级目录**：`-Vault空间/`（TARS 执行区）、`-Vault自身进化/`（Victor 元层）、`-人类思维笔记/`（泰戈尔思维区）

## 跨 session 提醒
- V2 的 `copilot-instructions.md` 仍包含完整身份信息，multi-root workspace 中 V2 铁律也会被注入
- V3 铁律层极简，只写 Copilot 专属机制 + 读 [[0_AI接入口在哪？]] 的指令
- 全AI框架通用的 自动注入规则 在根目录 AGENTS.md中
- 人格、声线、工作规则在 `.github/instructions/*.instructions.md` 中，按 `applyTo` 自动激活

## 当前状态（2026-03-29）
- ✅ V3 骨架完成：铁律层 + 通用接入层 + 三个一级目录 + applyTo 作用域规则
- ✅ 三人格已建立：Victor（元层）、TARS（执行层）、泰戈尔（思维层）
- ✅ -Vault空间 重组为中间层结构：感官与肢体/ + 任务库/
- ✅ index.md 改名为 [[1_人类接入手册]]（人类导航用）
- ✅ WikiLink 统一化（显现层不再用反引号路径）
- ✅ 文件夹前缀全统一为 `-`（原 `~Vault空间` `_Vault自身进化` 已改）
- ✅ CONTEXT.md → `-CONTEXT.md` 全层改名完成（CLI rename，wikilink 自动更新）
- ✅ applyTo 路径同步更新（vault-meta / workspace instructions）
- ✅ `0_AI通用接入口` 加入分层读取法则 + -CONTEXT 写法规范 + -LEARNINGS 触发规则
- ✅ V2 LEARNINGS 迁移拆分完成（3 层 -LEARNINGS.md）
- ✅ 5 个 Skills 迁移到 `.github/skills/`，注册进 V3 copilot-instructions
- ✅ **[2026-03-29]** copilot-instructions 结构翻转（独占区在前+公共区，成为单一真相源）
- ✅ **[2026-03-29]** 0_AI通用接入口 瘦身为薄指针文件
- ✅ **[2026-03-29]** 路径规范写入公共区（相对路径/wikilink/HID搜索策略）
- ✅ **[2026-03-29]** -where_continue.md 创建（续跑书签）
- ✅ **[2026-03-29]** 明日香陪你打游戏.md 占位（V3根 + 听觉模块_入口.md）
- ✅ **[2026-03-29]** @Code_Project 码表注释系统演示目录树建立
- ✅ **[2026-03-29]** applyTo 机制调研（文件匹配触发，非话题触发；attach/打开/agent编辑均可激活）
- ✅ **[2026-03-29]** PARDON 机制强化写入 copilot-instructions（每次回复结束必弹窗 + 对话收尾更新-CONTEXT）
- ✅ **[2026-03-29]** settings.json 更新：`chat.useClaudeMdFile: false`，`chat.useNestedAgentsMdFiles: true`
- ✅ **[2026-03-29]** -Local-Instructions.md → AGENTS.md 改名（演示项目），3处引用同步
- ✅ **[2026-03-29]** Custom Agents / Subagents 机制调研写入 temp_1（11章完整）
- ✅ **[2026-03-29]** root AGENTS.md 建立（公共区从 copilot-instructions 迁移，三框架共享）
- ✅ **[2026-03-29]** copilot-instructions 瘦身为纯 Copilot 独占区（PARDON+Skills）
- ✅ **[2026-03-29]** -where_continue 同步规则写入 AGENTS.md 行为准则
- 🔄 义体模块代码仍在 V2 运行，V3 占位符待迁移

## 上次做了什么（2026-03-29 session 2）
- compact 测试 + applyTo 官方文档调研
- PARDON 铁律强化（独占区 + 行为准则）
- settings.json：关闭 CLAUDE.md 发现，开启 NestedAgentsMd
- -Local-Instructions.md → AGENTS.md 改名（演示项目），3处引用同步
- Custom Agents / Subagents / SKILLS 机制全调研，写入 temp_1（11章）
- 1_人类接入手册 更新：新增"新用户必须配置的两个设置"章节

## 上次做了什么（2026-03-29 session 3）
- **root AGENTS.md 建立**：公共区从 copilot-instructions 迁移，三框架共享
- **copilot-instructions 瘦身**：保留 PARDON+Skills 独占区，加指针 → AGENTS.md
- **-where_continue 同步规则** 写入 AGENTS.md 行为准则
- 1_人类接入手册 表格更新：AGENTS.md 根目录行改为三框架共享描述

## 上次做了什么（2026-03-31）
- **1_人类接入手册_修订版.md** 精简（删 applyTo 代码块、压缩 Agent Note），加 applyTo/分隔符链接
- **temp_2** → `VSCode-Copilot指令机制参考.md` 移入 `-Vault自身进化/-软件操作手册/`，补实测内容 + Agent 机制章节
- **README.md** 建立于 V3 根目录（来访者快速入口）
- **AI提示词分隔符指南.md** 建立于 `-Vault自身进化/-人类与AI交互手册/`，示例先行排序
- **1_人类接入手册** 末尾加"七、✂️ Prompt 分隔符速查"极简节
- **AGENTS.md** 加入内容设计理念（泰戈尔 + 示例先行原则）

## 下一步
- ⏳ 👆 **义体模块代码迁移**（TTS → STT → HID → 视觉，V2 → V3）
- ⏳ `CLAUDE.md` 建立（Claude Code 接入）
- ⏳ 第4层 AGENTS.md（明日香等子代理）→ 等 OpenClaw 架构研究完成后建
- ⏳ 新开 session 测试码表演示目录（Opus 冷启动读懂能力测试）
- 🚫 搁置：RAG 长期记忆（触发条件：Vault > 500 文件）

---
*[[1_人类接入手册]]：人类导航 | [[0_AI接入口在哪？]]：AI 技术索引*
