# Agent Skills 机制研究报告
#研究报告 #VSCode #Copilot #Skills

> 研究时间：2026-04-02  
> 来源：[VS Code 官方文档](https://code.visualstudio.com/docs/copilot/customization/agent-skills) + `.vscode/extensions/github.copilot-chat-*/assets/prompts/skills/agent-customization/`

---

## 核心定位：Skills vs 其他 Primitives

| Primitive | 用途 | 加载时机 |
|---|---|---|
| Workspace Instructions | 编码规范、行为准则 | 全程常驻 |
| File Instructions (`.instructions.md`) | 文件类型 / 文件夹专属规则 | 按 glob 触发 |
| **Skills** | 专项工作流 + 可携带脚本/资源 | 按需触发（三级渐进） |
| Prompts (`.prompt.md`) | 单次参数化任务 | 手动 `/` 调用 |
| Custom Agents (`.agent.md`) | 子代理 / 多阶段工作流 | 手动调用 |

**选择原则**："这件事需要工具脚本 or 多步骤操作 + 会反复用" → Skill。只是规范 → Instructions。

---

## 三级渐进加载（关键！）

```
1. DISCOVERY   ~100 tokens   读 name + description —— 每次对话都读
         ↓ 判断相关
2. LOAD BODY   <5000 tokens  加载 SKILL.md 完整正文
         ↓ 执行过程中
3. RESOURCES   按文件大小   SKILL.md 里有 [链接](./refs/file.md)，Agent 主动读时才加载
```

**实践意义**：可以装很多 Skills 不怕上下文爆，因为第一阶段只有 100 token；只要 description 写得够精准，不相关的 Skills 永远停在第一层。

---

## SKILL.md 格式

```yaml
---
name: skill-name          # 必须和文件夹名相同！否则 silent fail
description: |            # 关键：触发词面。越具体越好，Max 1024 chars
  What it does. Use when: X, Y, Z.
argument-hint: "[options]" # 可选：/ 调用时的提示
user-invocable: true      # 是否出现在 / 命令列表（默认 true）
disable-model-invocation: false  # 禁止 AI 自动触发（默认 false）
---
```

### user-invocable × disable-model-invocation 矩阵

| 组合 | 在 / 菜单 | AI 自动触发 | 适用场景 |
|---|---|---|---|
| 默认（两者都不设置）| ✅ | ✅ | 通用技能 |
| `user-invocable: false` | ❌ | ✅ | 后台知识库，不需要用户感知 |
| `disable-model-invocation: true` | ✅ | ❌ | 只在用户主动调用时激活，防止误触 |
| 两者都设 | ❌ | ❌ | 临时禁用 |

---

## 目录结构规范

```
.github/skills/<skill-name>/
├── SKILL.md          # 必须，name 字段必须等于文件夹名
├── scripts/          # 可执行脚本
├── references/       # 参考文档（懒加载）
└── assets/           # 模板 / 样板代码
```

**懒加载关键**：资源文件只有在 SKILL.md 正文里用 Markdown 链接引用，且 Agent 主动读取该链接时，才会被加载进上下文。如果没有引用 → 永远不加载。

---

## 🚨 跨框架兼容性（重磅发现）

Agent Skills 是**开放标准**（[agentskills.io](https://agentskills.io/)）！

| 存放位置 | 被哪些框架读取 |
|---|---|
| `.github/skills/<name>/` | VS Code Copilot ✅，GitHub Copilot CLI ✅，Coding Agent ✅ |
| `.claude/skills/<name>/` | Claude Code 可发现（同标准） |
| `.agents/skills/<name>/` | 通用 AI agents |

**结论**：V3 的 5 个 Skills 在 `.github/skills/` → Copilot 可用。如果未来要让 Claude Code 也用同一套 Skills，可以在 `.claude/skills/` 放同名 Skills（或 symlink）。

---

## 现状：V3 已有 5 个 Skills

| 名称 | 来源 | 状态 |
|---|---|---|
| `obsidian-cli` | Obsidian 官方（Obsidian CEO 出品）| ✅ 运行中 |
| `obsidian-markdown` | 同上 | ✅ 运行中 |
| `obsidian-bases` | 同上 | ✅ 运行中 |
| `json-canvas` | 同上 | ✅ 运行中 |
| `defuddle` | 同上 | ✅ 运行中 |

description 无需优化，这批是官方写的。

---

## 可执行方案 — V3 新 Skills 机会

### 优先级 HIGH

1. **`🎮义体-tts` Skill** — 触发词：TTS、发声、语音播报、speak  
   内容：`tts_engine.py` 调用路径、声线宏、`localhost:5199/speak` 接口、Victor vs OpenClaw 区分  
   资源文件：`references/voice-config.md`（声线配置）

2. **`-project-continue` Skill** — 触发词：继续上次、-CONTEXT、-where_continue、resume  
   内容：分层读取法则、-CONTEXT 格式规范、-where_continue 同步规则  
   → 这样可以把 AGENTS.md 里的分层读取规则移出，改为按需加载（省常驻 token）

### 优先级 MEDIUM

3. **`git-clean-history` Skill** — 捕获本次的孤儿重置操作流程  
   内容：Orphan Reset 步骤 + 3 个 Vault 的 remote 地址 + PARDON 触发提示

4. **`亿体模块-dispatch` Skill** — 触发词：HID、截图、视觉、键鼠  
   内容：各模块入口路径、调用方式

### 不建议做 Skill 的场景

- PARDON 机制（常驻规则 → Instructions 更合适）  
- 架构规范（全局意识 → AGENTS.md 更合适）

---

## /create-skill 命令

直接在 Chat 输入 `/create-skill` + 描述 → AI 自动生成 SKILL.md + 目录结构。  
或从已有对话里提炼："create a skill from how we just did X"。

---

## 社区资源

- `github/awesome-copilot` — 社区 Skills + Agents + Instructions 集合
- `anthropics/skills` — Anthropic 官方参考 Skills（可与 Claude 配套使用）

---

## 下一步

→ 研究 VSCode Custom Agents（`.agent.md`）机制  
→ 研究 SubAgent 架构  
→ 可执行方案：制作 `🎮义体-tts` Skill

*下次报告：[ai_Copilot_AGENT/研究报告](../ai_Copilot_AGENT/)*
