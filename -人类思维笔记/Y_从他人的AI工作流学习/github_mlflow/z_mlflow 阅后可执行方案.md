# MLflow 研究 → 可执行方案

> 源自：[[z_mlflow 研究报告]]  
> 三个借鉴点，按优先级排序

---

> **【修正说明】**（Akimos 2026-04-02 纠正）  
> - 子目录已有 `AGENTS.md`（Python 里用户手动加了 magic），这一层没有缺口
> - 方案 A 的目标是建 **`CLAUDE.md`**（Claude Code 专属工程命令文件），与 `AGENTS.md` 不重复——前者是行为宪法，后者是启动/测试手册
> - Hooks 不是 UI 弹窗（不影响计费），是 shell 脚本级拦截，适合"强制调用TTS""自动注入CONTEXT""token超限提醒compact"等**正向自动化**，不是单纯阻止操作
> - 我们已经有 Python 调用了（TTS/视觉/HID 在 V2 运行中），方案 C 等迁移完成后自然合并

## 方案 A — 子项目 CLAUDE.md（⭐️ 最小代价，最快收益）

**问题**：每次进代码子项目，AI 不知道"怎么跑这个项目"（`AGENTS.md` 写行为规范，不写操作命令）。  
**解法**：每个代码子目录建一个 `CLAUDE.md`，记录启动/测试命令，专给 Claude Code 读。

### 步骤

1. 找到所有代码项目目录（`-Vault空间/@Code_Project/Python/` 等）
2. 在每个项目根目录创建 `CLAUDE.md`，模板如下：

```markdown
# CLAUDE.md — [项目名]

## 启动
```bash
# 启动命令
python xxx.py
```

## 测试
```bash
pytest tests/
```

## 依赖
```bash
pip install -r requirements.txt
```

## 特殊约定
- 参数在 `.json` 里改，不改 `.py`
- TTS 调用路径见 V2 义体手册
```

3. 还需为 V3 根目录建一个 `CLAUDE.md`（目前只有 `AGENTS.md`）

### 立即可做
```
D:\ObsidianVaults_V3\CLAUDE.md   ← 创建（V3 整体工程命令）
D:\ObsidianVaults_V3\-Vault空间\@Code_Project\[各项目]\CLAUDE.md
```

---

## 方案 B — Claude Code Hooks 正向自动化（中等优先级）

**澄清**：Hooks 不是 UI 弹窗（不消耗 token、不影响计费），是 Claude Code 在执行工具前/后触发的 shell 脚本。有两种方向：
- **拦截式**：阻止危险操作（但 PARDON 已经够用，不是优先）
- **自动化式**：强制附加行为，比自律更可靠

### 赛博王国的 Hook 使用场景（Akimos 提案）

| 场景 | 类型 | Hook |
|---|---|---|
| 编辑某些文件时强制先读 `-CONTEXT.md` | PostToolUse | 读文件后检测路径，自动 attach 对应 CONTEXT |
| 记忆超过 70k tokens 时提醒 compact | PostToolUse | 检测 token 计数，写入提醒消息 |
| 强制调用 TTS 播报关键动作 | PostToolUse | 调用 `localhost:5199/speak` |

### 步骤

1. 在 V3 `.claude/` 目录下建 `hooks/` 子目录
2. 建 `settings.json` 注册 hooks
3. 每个 hook 写一个 bash 脚本

> ⚠️ hooks 只对 Claude Code 生效，不影响 Copilot（Copilot 的等价物是 Instructions 中的约束）。

---

## 方案 C — Python 可执行 Skills（等义体迁移完成后自然合并）

**澄清**：赛博王国已有大量 Python 调用（TTS/STT/视觉/HID 在 V2 运行中），不是从零开始。  
等义体模块迁移到 V3 后，这些模块本身就是"可执行 Skills"。骨架已有，差的是包装成 `.claude/skills/` 可调用的形式。

### 待做（迁移完后执行）
- 把 TTS 调用包成 `uv run skills speak "内容"`
- 把截图+Vision分析包成 `uv run skills screenshot`
- 这样 Claude Code 可以直接调用，不用写完整路径

> 当前跳过。义体迁移完成是前提条件。

---

## 优先级总结

| 方案 | 代价 | 收益 | 建议 |
|---|---|---|---|
| A — 子项目 CLAUDE.md | 低（写 Markdown）| 高（每次进项目 AI 直接知道命令）| ✅ **立即执行** |
| B — Hooks 硬拦截 | 中（写 shell 脚本）| 中（补强 PARDON 覆盖空白）| 🟡 **下一 session** |
| C — Python Skills | 高（搭整个包结构）| 中（机械任务自动化）| ⏳ **等需求来了再做** |

---

## 关于 MLflow 本体是否引入？

**结论：不引入**。

MLflow 的 Tracking / Model Registry 解决的是团队 ML 实验管理问题。赛博王国是单人工作流，当前规模不需要这套基础设施。如果未来：
- 跑多个 AI 模型对比实验 → 再评估
- 需要追踪 prompt 版本历史 → 先用 git 解决，不够再上 MLflow Prompt Registry
