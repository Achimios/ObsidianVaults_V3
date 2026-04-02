# Claude Code 研究后可执行操作

> 源自：[[z_ClaudeCode机制研究]]  
> 简洁版，阅后直接执行

---

## 立即做：建 V3 根目录 CLAUDE.md

**为什么**：Claude Code 只读 `CLAUDE.md`，不读 `AGENTS.md`。需要一个桥接文件。

```markdown
# V3 CLAUDE.md（建在 D:\ObsidianVaults_V3\CLAUDE.md 或 .claude\CLAUDE.md）

@AGENTS.md

## Claude Code 专属
- 运行 Claude Code 时工作目录：D:\ObsidianVaults_V3
- 义体模块代码在 ../ObsidianVaults_V2/超梦空间/~Modules_专用模块/
- 修改代码前先读对应目录的 -CONTEXT.md
```

操作：在 V3 根目录创建 `CLAUDE.md`，两行内容：`@AGENTS.md` + 几条 Claude Code 专属补充。

---

## 可选：`.claude/rules/` 替代部分 Instructions

当前 Copilot 用 `.github/instructions/*.instructions.md` + `applyTo`。  
Claude Code 等价物是 `.claude/rules/` + `paths:` frontmatter。

**机制几乎一样，两者路径写法对称：**
- `.github/instructions/-workspace.instructions.md` → `applyTo: -Vault空间/**`
- `.claude/rules/vault-space.md` → `paths: ["-Vault空间/**"]`

**建议**：现有 Instructions 对 Claude Code 生效的最省力方式是在 `CLAUDE.md` 里 import：
```
@.github/instructions/-workspace.instructions.md
```
不用重复建 rules/——避免双份维护。

---

## 了解即可：Auto Memory

Claude Code 会自动在 `~/.claude/projects/<V3-path>/memory/` 写笔记。  
不需要手动维护，用 `/memory` 命令浏览。  
**与我们的 `-LEARNINGS.md` 是互补的**：auto memory 是它自己记，learnings 是我们明确要它记。

---

## 优先级总结

| 任务 | 状态 |
|---|---|
| 建 V3 根目录 `CLAUDE.md`（import AGENTS.md + 专属补充）| ✅ **立即做** |
| 子项目建 `CLAUDE.md`（工程命令）| 🟡 进代码项目时顺手加 |
| `.claude/rules/` 路径规则 | ⏳ 现有 Instructions 够用，不急 |
| Auto memory | 自动运行，无需操作 |
