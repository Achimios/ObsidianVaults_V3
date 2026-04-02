# CyberDomain V3 — Claude Code 独占层
<magic>Claude Code 专属，义体医生就绪</magic>

> 本文件仅 Claude Code 读取。Copilot 独占规则在 `.github/copilot-instructions.md`。  
> 通用规则在根目录 `CLAUDE.md`（硬链接至 AGENTS.md）。

---

## Claude Code 特有行为规范（占位符 — 待完善）

### 思考时间控制
- Claude Code 默认 extended thinking 会导致 1-4 分钟延迟
- 非必要不开启深度思考，优先快速执行
- 指挥官明确说"慢慢想" / "深度分析" 时才开启

### 自动化任务模式
- Claude Code 用于**无人值守的自动化代码任务**，不需反复弹窗
- 但涉及不可逆操作（删文件、git push --force 等）仍需 terminal 确认
- 代码生成 → 自动测试 → 自动提交 是标准工作流

### 子代理机制（待研究）
- 待研究：如何定义 Claude Code SubAgent
- 占位：见 `-人类思维笔记/Y_从他人的AI工作流学习/ai_ClaudeCode/`

---

<!-- 此文件由 Claude Code 直接读取，gitignore 豁免：!.claude/CLAUDE.md -->

