# Claude Code 记忆机制研究

> 来源：https://code.claude.com/docs/en/memory  
> 日期：2026-04-02  
> 目的：搞清楚 Claude Code 的注入机制，与 Copilot 对比，决定 V3 怎么用

---

## 一、两套记忆系统

| 维度 | CLAUDE.md（你写）| Auto Memory（它写）|
|---|---|---|
| 作者 | 人类 | Claude 自动 |
| 内容 | 指令、规范、架构约定 | 调试经验、发现的偏好、工作流习惯 |
| 作用域 | 项目 / 用户 / 组织 | 每个 git 仓库独立 |
| 加载时机 | 每次 session 开始 | 每次 session 开始（只加载 MEMORY.md 前 200 行）|
| 能否编辑 | 是 | 是（plain markdown）|

**关键认知**：Claude Code 把 CLAUDE.md 当 context 注入，不是强制执行配置——越具体简洁，遵从越稳定。

---

## 二、CLAUDE.md 的四个作用域（优先级从高到低）

| 层级 | 路径（Windows）| 用途 |
|---|---|---|
| 组织 | `C:\Program Files\ClaudeCode\CLAUDE.md` | IT 全局强制，不可被排除 |
| 项目 | `./CLAUDE.md` 或 `./.claude/CLAUDE.md` | 团队共享，git 提交 |
| 子目录 | 各子目录下的 `CLAUDE.md` | 懒加载：Claude 访问该目录文件时才注入 |
| 用户 | `~/.claude/CLAUDE.md` | 个人偏好，所有项目生效 |

**子目录 CLAUDE.md 是懒加载**——只有 Claude 读取该目录下的文件时才加载，不会污染全局 context。  
→ 这是给每个代码子项目建 `CLAUDE.md` 的理论依据。

---

## 三、`.claude/rules/` — 分模块规则（重点对比）

### 基本用法

```
.claude/
└── rules/
    ├── python.md       # 无 frontmatter → 全局加载
    ├── testing.md      # 无 frontmatter → 全局加载
    └── api-design.md   # 有 paths: → 路径匹配时才加载
```

### 路径作用域（YAML frontmatter）

```yaml
---
paths:
  - "src/api/**/*.ts"
  - "lib/**/*.{ts,tsx}"
---

# API Development Rules
- All endpoints must include input validation
```

**无 paths 字段 → session 开始全量加载（等同于主 CLAUDE.md）**  
**有 paths 字段 → 匹配文件被访问时才加载（懒加载）**

### 对比 Copilot 的 `.github/instructions/*.instructions.md`

| 维度 | Claude Code `.claude/rules/` | Copilot `.github/instructions/` |
|---|---|---|
| 路径匹配字段 | `paths:` | `applyTo:` |
| 语法 | glob 模式 | glob 模式 |
| 无字段时行为 | 全局加载 | 需要 `applyTo: **` 或用户 attach |
| 触发时机 | Claude 访问匹配文件时 | 文件打开 / agent 编辑 / attach 时 |
| 共享目录 | 支持 symlink 到共享目录 | 不支持（必须在仓库内）|
| 用户级规则 | `~/.claude/rules/` | 用户级 `.github/` 目录 |

**结论：机制几乎相同，两者都是"按文件路径懒加载规则"，写法高度对称。**

---

## 四、AGENTS.md + CLAUDE.md 并存方案（官方建议）

官方文档明确写了：

> Claude Code 读 `CLAUDE.md`，不读 `AGENTS.md`。  
> 如果仓库已有 `AGENTS.md` 给其他 AI 用，建一个 `CLAUDE.md` import 它：

```markdown
@AGENTS.md

## Claude Code 专属补充
- 在 src/billing/ 下的改动使用 plan mode
```

**V3 的做法**：  
- `AGENTS.md` = 三框架通用宪法（已建，已使用）  
- 还需建 `CLAUDE.md` = 导入 AGENTS.md + Claude Code 专属工程命令

---

## 五、Import 语法（`@path`）

在任何 CLAUDE.md 中可以用：

```markdown
@AGENTS.md                          # import 同目录文件
@../shared-rules/python.md          # import 相对路径
@~/.claude/personal-prefs.md        # import 用户目录文件（个人偏好，不提交 git）
```

- 最多 5 层递归 import
- 被 import 的文件在 session 开始时一起加载到 context

---

## 六、Auto Memory

- 存储位置：`~/.claude/projects/<git-repo-path>/memory/`
- `MEMORY.md` = 索引文件（前 200 行或 25KB 每次 session 加载）
- 其余 topic 文件（`debugging.md`, `patterns.md`）按需读取
- Auto memory 是机器本地的，跨机器不同步
- 用 `/memory` 命令浏览/编辑/开关

---

## 七、其他实用细节

| 特性 | 说明 |
|---|---|
| `/init` 命令 | 自动分析代码库生成初始 CLAUDE.md |
| `<!-- comment -->` | CLAUDE.md 中的 HTML 注释会被剥离，不消耗 token（除非在代码块内）|
| `/compact` 后 | CLAUDE.md 从磁盘重新注入，对话指令丢失但文件指令保留 |
| `claudeMdExcludes` | monorepo 中排除其他团队的 CLAUDE.md |
| `--append-system-prompt` | 将指令注入 system prompt（CLI 参数，不是文件）|
| `InstructionsLoaded` hook | 调试哪些指令文件被加载了 |

---

## 八、关键认知：指令是 context，不是强制配置

官方原文：
> "Claude treats them as context, not enforced configuration."

→ 写越具体的指令（"Use 2-space indentation" not "format code properly"），遵从越稳定。  
→ 这和 Copilot Instructions 的处理方式完全相同——都不是 100% 强制。  
→ **硬拦截只能靠 Hooks（Claude Code）或 settings.json 的 permissions.deny**。
