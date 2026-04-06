# CONTEXT — 赛博王国 V3 根目录

## 这是什么
V3 Vault 根目录。含人类导航（[[1_人类接入手册]]）、AI 通用接入层（[[0_AI接入口在哪？]]）、AI 固件（.github/）。
**一级目录**：-Vault空间/（TARS 执行区）、-Vault自身进化/（Victor 元层）、-人类思维笔记/（泰戈尔思维区）

## 跨 session 提醒
- V2 的 copilot-instructions.md 仍包含完整身份信息，multi-root workspace 中 V2 铁律也会被注入
- 全AI框架通用 → 根目录 `AGENTS.md`；Copilot 独占 → `.github/copilot-instructions.md`；Claude Code 独占 → `.claude/CLAUDE.md`
- 人格/声线/工作规则 → `.github/instructions/*.instructions.md`（`applyTo` 作用域自动激活）
- `.claude/skills` junction → `.github/skills`（Claude Code 与 Copilot 共用 Skills）
- `**/CLAUDE.md` 被 gitignore，但 `.claude/CLAUDE.md` 被豁免单独追踪

## 当前状态（2026-04-04）
- V3 架构完稳：铁律层 + AGENTS.md + 三人格 + applyTo 作用域规则（03-29 完毕）
- AI 多框架接入全套：AGENTS.md + CLAUDE.md 硬链接 x4 + .claude/CLAUDE.md 独占 + Settings 配置
- magic 系统：全 AGENTS.md 中 magic HTML注释 改为 XML tags（Claude Code 不 strip tags）
- Skills x6（`.claude/skills/` 统一存放，Copilot+Claude 均可读）：5个 Obsidian + `-yiti-tts` + `-how-write-instructions`；`.github/skills/` 已删除
- AGENTS.md：听觉接口精简为宏名四连 + pointer to `-yiti-tts` Skill；Session 流程规则内联（不再依赖外部 Skill）
- `-workspace.instructions.md`：移除 daemon ping 提示（已在 -yiti-tts Skill 覆盖）
- 义体模块代码：TTS/STT/HID/Vision 仍在 V2 运行，V3 只有占位符

## 上次做了什么（2026-04-04）
- `-project-continue` Skill 内容内联进 AGENTS.md，Skill 目录删除
- AGENTS.md 听觉接口精简为宏名四连 + pointer to `-yiti-tts` Skill
- `-workspace.instructions.md` 移除 `localhost:5199/ping` 行（TTS Skill 已覆盖）

## 下一步
- 👆 OpenClaw 机制研究（研究报告 + 可执行方案）
- 继续 SKILL 机制研究（上次停在 Copilot Skills，下次研究 OpenClaw）
- 声线宏清查：根目录工作时应用 VOICE_COPILOT（非 VOICE_VICTOR），找出错误引用逐个修正
- 义体模块代码迁移（TTS → STT → HID → 视觉，V2 → V3）
- 搁置：RAG 长期记忆（触发条件：Vault > 500 文件）

---
*[[1_人类接入手册]]：人类导航 | [[0_AI接入口在哪？]]：AI 技术索引*
