---
name: -how-write-instructions
description: >
  Use when writing or reviewing *.instructions.md, AGENTS.md, agent or skill
  files. Covers: conciseness philosophy, dedup rules, official VS Code tips.
---

# 如何写 V3 注入文件

## V3 哲学 — 罗素风格

> 保持明确的前提下，简洁到极致。数学语言精确且无废词。

**核实原则**：各条之间有冗余 = 写失败了。同一意思只在最高层写一次，下层只写例外和特有细节。

---

## 官方 VS Code Tips（中文摘要）

- **每条指令单一、简洁**：一个规则一句话
- **说明原因**：解释 *why* 比只说 *what* 更有效（AI 能处理边界情况）
- **具体示例 > 抽象规则**：preferred pattern vs avoided pattern
- **跳过显而易见的约定**：linter/formatter 已经管的别写
- **用 `applyTo` 分文件**：不同语言/区域用 scope 限制，不要一个大文件堆所有规则
- **在 prompt / agent 文件中引用** instructions 文件，不要复制粘贴

---

## Official VS Code Tips (Original)

- Keep your instructions short and self-contained. Each instruction should be a single, simple statement.
- Include the reasoning behind rules. When instructions explain _why_ a convention exists, the AI makes better decisions in edge cases. For example: "Use `date-fns` instead of `moment.js` because moment.js is deprecated and increases bundle size."
- Show preferred and avoided patterns with concrete code examples. The AI responds more effectively to examples than to abstract rules.
- Focus on non-obvious rules. Skip conventions that standard linters or formatters already enforce.
- For task or language-specific instructions, use multiple `*.instructions.md` files per topic and apply them selectively by using the `applyTo` property.
- Store project-specific instructions in your workspace to share them with other team members and include them in your version control.
- Reuse and reference instructions files in your prompt files and custom agents to keep them clean and focused, and to avoid duplicating instructions.
- Whitespace between instructions is ignored, so you can format instructions as a single paragraph, on separate lines, or separated by blank lines for legibility.
