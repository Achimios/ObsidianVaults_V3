# MLflow × 赛博王国 V3 — 研究报告

> 对象：[mlflow/mlflow](https://github.com/mlflow/mlflow)  
> 目的：找出 mlflow 在 AI 协作组织层面与我们 V3 的异同，取长补短  
> 日期：2026-04-02

---

## 一、MLflow 是什么

MLflow 是开源的 **AI 工程平台**，核心定位是全生命周期管理：

| 层面 | 能力 |
|---|---|
| 实验追踪 | 记录参数、指标、模型跨实验对比 |
| LLM 可观测性 | Trace 捕获 LLM + Agent 调用链 |
| Prompt 注册中心 | 版本化 Prompt，有 lineage |
| 模型注册中心 | 生产前审批链，协作部署 |
| AI Gateway | 统一代理所有 LLM 提供商 |
| 评估框架 | 50+ 内置指标，LLM-as-judge |

**规模**：6000 万月下载、1012 贡献者、25k ⭐、Python 61% + TypeScript 28%

---

## 二、MLflow 的 AI 协作组织架构

这是本次调研最核心的部分——他们如何管理多 AI 框架协作：

### 2.1 多 AI 框架共存结构

```
mlflow/
├── CLAUDE.md          ← Claude Code 专属（AGENTS.md 等价物）
├── .claude/           ← Claude Code 独占目录
│   ├── settings.json  ← 工具权限控制（bash 哪些指令被允许）
│   ├── rules/         ← 模块级规则（python.md, github-actions.md）
│   ├── commands/      ← 斜杠命令（/pr-review, /resolve）
│   ├── skills/        ← Skills 库（add-review-comment, analyze-ci, copilot...）
│   ├── hooks/         ← PreToolUse 钩子（如 enforce-uv.sh 阻止 pip 命令）
│   └── scripts/       ← 辅助脚本
└── .github/
    └── copilot-instructions.md  ← Copilot 专属（我们的等价物）
```

### 2.2 Skills 系统（双轨制）

mlflow 的 `.claude/skills/` 是一个完整 Python 包（有 `pyproject.toml`），可以用 `uv run skills <command>` 直接从CLI调用。技能包含：

- `add-review-comment` — 给 PR 添加审阅意见
- `analyze-ci` — 分析 CI 失败结果
- `copilot` — Copilot 专属 Skill（有趣：Claude Code 里有 Copilot skill）
- `fetch-diff` / `fetch-unresolved-comments` — 代码审查辅助

**对比 V3**：我们的 `.github/skills/` 是纯 Markdown + YAML frontmatter，触发方式为自然语言调用。mlflow 的 Skills 是可执行 Python 包，适合重复性代码任务（CI分析、PR审阅）。

### 2.3 Hooks 机制（我们没有的）

mlflow 用 Claude Code hooks 实现**操作拦截**：
- `hooks/enforce-uv.sh` — 阻止 `pip/pip3` 命令（强制用 `uv`）
- `hooks/` 中的 PreToolUse 钩子可以在工具执行前拦截并修改行为

**对比 V3 的 PARDON 机制**：我们用人工弹窗 + AI自律；mlflow 用代码层面的自动化钩子拦截。本质上都是"越权操作拦截"，但实现层不同。

### 2.4 Rules 分层

`rules/` 目录将规则按技术域拆分：
- `python.md` — Python 代码风格规则（Ruff, uv, 导入规范）
- `github-actions.md` — CI/CD 规范

**对比 V3 的 instructions**：功能相同，都是 applyTo / 目录作用域限制。我们按人格和 Vault 域分层；他们按代码技术域分层。

### 2.5 CLAUDE.md 内容质量

mlflow 的 `CLAUDE.md` 高度工程化，包含：
- 开发服务器启动一键命令（`dev/run-dev-server.sh`）
- 完整测试、linting、文档构建命令
- Git 工作流（DCO sign-off 强制要求，`git commit -s`）
- 常见任务快速参考

**对比我们的 AGENTS.md**：mlflow 的是"工程操作手册"；我们的是"AI 行为宪法 + 组织架构图"。两者定位不同，都合理。

---

## 三、相似点

| 维度 | mlflow | 赛博王国 V3 |
|---|---|---|
| 多框架共存 | Claude Code + Copilot 各有专属 | Copilot + Claude Code + OpenClaw |
| 操作拦截机制 | hooks（代码层）| PARDON（UI弹窗层）|
| Skills 系统 | `.claude/skills/`（可执行）| `.github/skills/`（YAML触发）|
| 分层规则 | `rules/` 按技术域 | `instructions/` 按人格域 |
| AI 行为约束文件 | `CLAUDE.md` | `AGENTS.md` |
| 路径规范 | 相对路径 | 相对路径（同款）|

---

## 四、不同点 & 谁的方法更好

### 4.1 Skills 实现方式

| 维度 | mlflow（Python包）| V3（Markdown触发）|
|---|---|---|
| 适用场景 | 固定的、重复性代码任务（CI分析、PR审阅）| 知识类、概念类、领域指引 |
| 触发方式 | `uv run skills <cmd>` 或 CLI | 自然语言调用、对话中自动匹配 |
| 可复用性 | 高（跨项目 pip install）| 高（Markdown 可 fork）|
| **胜者** | 代码任务用 mlflow 方案更好 | 知识/规则 Skills 用 V3 方案合适 |

**结论**：两者不互斥，V3 可以同时建 `.claude/skills/`（Python 可执行任务）+ `.github/skills/`（知识类）。

### 4.2 操作拦截

| 维度 | mlflow Hooks | V3 PARDON |
|---|---|---|
| 强制性 | 硬拦截（代码层面，AI 绕不过）| 软拦截（AI 自律 + 规则约束）|
| 适用场景 | 高频、规则明确的拦截（禁 pip）| 需人工判断的越权操作 |
| 仪式感 | 无 | 高（弹窗有王国仪式感）|
| **胜者** | 高确定性规则用 hooks 更可靠 | 人机协作判断用 PARDON 更合适 |

**结论**：V3 可以引入 hooks 处理高确定性场景（如"禁止读取-档案室/"），PARDON 保留用于需要指挥官判断的场景。

### 4.3 CLAUDE.md vs AGENTS.md

| 维度 | mlflow CLAUDE.md | V3 AGENTS.md |
|---|---|---|
| 内容 | 工程命令手册（启动/测试/lint）| AI行为宪法 + 架构图 |
| 读者 | AI 工具（开发任务）| 所有 AI 框架（行为规范）|
| 更新频率 | 随工程环境变化 | 随组织架构演进 |
| **胜者** | 各有侧重，都是最佳实践 | — |

**结论**：V3 的设计更"宏大"，mlflow 的更"实用"。V3 可以在每个 `-Vault空间/` 子项目中再建一个 `CLAUDE.md` 专门写工程命令——现在缺这一层。

### 4.4 实验追踪 vs 知识管理

这是最本质的差异：

| 维度 | mlflow | 赛博王国 V3 |
|---|---|---|
| 记录对象 | ML 实验参数、指标、模型 Artifacts | 人类思维笔记、AI行为经验、义体模块 |
| 版本化 | 模型版本 + Prompt Registry | git 历史 + `-LEARNINGS.md` |
| 搜索方式 | SQL-like 查询实验 | Agentic Search + Obsidian CLI |
| UI | Web Dashboard（mlflow server）| Obsidian 可视化图谱 |
| **胜者** | ML 实验追踪无对手 | 人机知识共建无对手 |

---

## 五、总结

mlflow 是一个**工业级工程工具**，解决 ML 团队规模化协作问题。V3 是一个**个人知识-义体操作系统**，解决单人×多AI框架协同进化问题。

两者目标不同，但都走向了同一个方向：**让 AI 有结构地工作，人类保持控制权**。

mlflow 给赛博王国最有价值的三个借鉴：
1. **Python 可执行 Skills**（`.claude/skills/` 作为代码包）
2. **Hooks 硬拦截**（高确定性场景替代 PARDON 软拦截）
3. **子项目工程命令文件**（各模块建独立 `CLAUDE.md` 记录启动/测试命令）
