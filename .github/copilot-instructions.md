# CyberDomain V3 — Copilot 铁律层

<magic> 铁律在线，PARDON 已就绪 </magic>

## 【COPILOT 独占】Skills

Skills 在 `.claude/skills/` 中，VS Code 从 SKILL.md 的 YAML frontmatter 自动发现，无需手动注册。

## 🚨【COPILOT 独占】PARDON 机制 — 绝对强制，无例外

**以下任何操作前，必须立即调用 `vscode_askQuestions` 弹窗等待授权，不得跳过，不得用终端代替，跳过即视为严重失职：**

| 触发场景 | 说明 |
|---|---|
| **每次回复结束时**（无论任务大小）| 🚨 必须弹窗询问后续任务，不得直接收尾，已是连续违规高频失误 |
| 读取 `-档案室/` 内任何文件 | 含账号令牌 |
| 删除 / 覆盖任何文件 | 不可逆操作 |
| 修改 `.github/` 核心配置 | 含此文件 |
| 安装任何包（pip / npm 等） | 破坏环境 |
| **不确定该怎么做时** | 先问！不要凭记忆猜 |

**`vscode_askQuestions` 调用规范（每次都要满足）：**
1. 弹窗必须包含 **自由文本输入框**（禁止 `allowFreeformInput: false`）
2. 必须提供 ALLOW / DENY 预设按钮
3. 收到 ALLOW 后才执行；DENY 或无回应 → 立即停止

> ⚠️ 违反 PARDON = 浪费指挥官计费额度 = Copilot最不可接受的失误

---

> 📖 通用规则（架构、行为准则、分层读取、路径规范、-where_continue 同步法则）  
> 见根目录 `../AGENTS.md`（Vault 通用指令层，Copilot / Claude Code / OpenClaw 三框架共享）。

