# Claude Code Hooks — 机制研究报告

> 来源：https://code.claude.com/docs/en/hooks  
> 研究日期：2026-04-03  
> 目的：理解 hooks 运行机制，为王国 TTS/HID 义体模块接入提供理论基础

---

## 一、什么是 Hooks

Hooks 是用户定义的 **shell 命令、HTTP 端点或 LLM 提示**，在 Claude Code 生命周期的特定节点自动执行。

本质：Claude Code 在特定事件（Event）发生时，将 JSON 上下文通过 stdin 传入你的 hook 脚本，hook 脚本可以通过 exit code / stdout 影响 Claude 的行为。

---

## 二、四种 Hook 类型

| 类型 | 说明 | 适用场景 |
|---|---|---|
| `command` | 执行 shell 命令，stdin 收 JSON | 最通用，支持 async |
| `http` | 向 URL 发 POST 请求，body 为 JSON | 接入外部服务、守护进程 |
| `prompt` | 把 hook 输入发给小模型，让 LLM 判断 allow/deny | 自动审批、软约束 |
| `agent` | 生成有工具访问权的子代理来验证条件 | 复杂验证（如：跑测试后才允许 Stop）|

> [!note] Windows 注意  
> `command` 类型支持 `"shell": "powershell"`，直接跑 PowerShell 5.1/7+，无需额外配置。

---

## 三、生命周期事件（完整表）

```
SessionStart → UserPromptSubmit → [PreToolUse → PermissionRequest → PostToolUse] (循环) → Stop
                                         ↓ 拒绝时
                                   PermissionDenied
```

### 主线事件

| 事件 | 触发时机 | 可以做什么 | 支持 prompt/agent hook |
|---|---|---|---|
| `SessionStart` | session 开始/恢复时 | 注入上下文、设环境变量 | ❌ 仅 command |
| `UserPromptSubmit` | 用户提交 prompt 前 | 注入上下文、拦截 prompt | ✅ |
| `PreToolUse` | 工具执行前 | allow/deny/ask/defer 工具调用 | ✅ |
| `PermissionRequest` | permission 对话框出现前 | 自动 allow/deny 权限 | ✅ |
| `PostToolUse` | 工具成功执行后 | 触发后续操作、给 Claude 反馈 | ✅ |
| `PostToolUseFailure` | 工具执行失败后 | 给 Claude 补充失败上下文 | ✅ |
| `PermissionDenied` | auto mode 拒绝工具时 | 让 Claude 知道可以 retry | ❌ |
| `Stop` | Claude 回复完成时 | 阻止停止、触发后续任务 | ✅ |
| `StopFailure` | API 错误导致中止时 | 日志、报警 | ❌ 仅 command |

### 异步/环境事件

| 事件 | 触发时机 | 说明 |
|---|---|---|
| `Notification` | Claude Code 发通知时 | 监听 permission_prompt / idle 等 |
| `FileChanged` | 监听的文件变化时 | 配合 `matcher` 指定文件名 |
| `CwdChanged` | 工作目录切换时 | 自动 activate venv 等 |
| `InstructionsLoaded` | CLAUDE.md 加载时 | 审计哪些指令文件被注入 |
| `ConfigChange` | 配置文件变化时 | 防止未授权配置修改 |
| `PreCompact` / `PostCompact` | compact 前后 | 保存 compact 前状态 |
| `SessionEnd` | session 结束时 | 清理、记录日志 |

### Subagent / Team 事件

`SubagentStart`、`SubagentStop`、`TaskCreated`、`TaskCompleted`、`TeammateIdle`

---

## 四、配置位置与 Scope

| 文件 | 作用域 | 是否提交 git |
|---|---|---|
| `~/.claude/settings.json` | 所有项目（全用户） | ❌ 仅本机 |
| `.claude/settings.json` | 当前项目 | ✅ 可提交 |
| `.claude/settings.local.json` | 当前项目（本地私有） | ❌ gitignored |
| Skill / Agent frontmatter | Skill/Agent 激活期间 | ✅ 随文件提交 |

### 配置结构

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "optional-regex",
        "hooks": [
          {
            "type": "command",
            "command": "your-script.sh"
          }
        ]
      }
    ]
  }
}
```

三层嵌套：**hook 事件** → **matcher 组**（可选过滤） → **hook handler 数组**

---

## 五、Hook Input / Output 机制

### Input（stdin JSON）

所有事件都包含公共字段：
```json
{
  "session_id": "...",
  "transcript_path": "/.../.claude/projects/.../transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "Stop"
}
```
各事件有额外字段（如 `Stop` 有 `last_assistant_message`、`PreToolUse` 有 `tool_name` + `tool_input`）。

### Output（exit code + stdout）

| 表达方式 | 含义 |
|---|---|
| `exit 0` | 成功，Claude Code 解析 stdout 的 JSON |
| `exit 2` | **阻断错误**，stderr 作为错误信息反馈给 Claude |
| 其他 exit code | 非阻断错误，stderr 仅在 verbose 模式显示 |

JSON stdout 结构：
```json
{
  "decision": "block",
  "reason": "原因",
  "continue": false,           // universal：强制停止 Claude
  "stopReason": "...",         // 配合 continue: false 显示给用户
  "hookSpecificOutput": { ... } // 事件特定输出（PreToolUse 用这个）
}
```

---

## 六、Skills / Agents Frontmatter 内嵌 Hooks

**这是最重要的发现之一。** Skills 和 Subagents 可以在 YAML frontmatter 中直接定义 hooks，这些 hooks 只在该 Skill/Agent 激活期间有效：

```yaml
---
name: my-skill
description: ...
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
---
```

这意味着：
- `-yiti-tts` Skill 激活时，可以自动挂上 Stop hook 做 TTS 播报
- 义体模块可以通过 Skill frontmatter 实现"热插拔"——Skill 加载即激活，Skill 卸载即清除
- **`once: true`** 字段（Skills 专属）：hook 触发一次后自动移除

---

## 七、Async Hooks（异步非阻塞）

在 `command` hook 上加 `"async": true`，hook 在后台执行，不阻塞 Claude：

```json
{
  "type": "command",
  "command": "...",
  "async": true,
  "timeout": 120
}
```

注意：async hook 的 `decision`、`permissionDecision` 等控制字段无效（action 已经执行了）。  
适用于 TTS 播报、日志记录等"通知类"操作。

---

## 八、对王国的潜在应用

| 场景 | Hook 事件 | 实现方式 |
|---|---|---|
| 老维完成回复后 TTS 播报 | `Stop` + async | POST 到 `localhost:5199/speak` |
| session 开始时 TTS "老维上线" | `SessionStart` | command + PowerShell |
| 每次写文件后记录 audit log | `PostToolUse(Write/Edit)` | async command |
| 阻止 rm -rf 等危险命令 | `PreToolUse(Bash)` | exit 2 |
| CLAUDE.md 加载时记录 | `InstructionsLoaded` | async command log |
| -yiti-tts Skill 激活时挂 hooks | Skill frontmatter | 热插拔义体模块 |

---

## 九、已知限制

- `SessionStart` 只支持 `command` 类型
- Async hooks 无法返回 decision（只能做通知类操作）
- async 没有去重，每次触发都是独立进程
- `UserPromptSubmit`、`Stop` 等事件不支持 matcher（每次必触发）
- output 注入 Claude 上下文上限 10,000 字符

---

## 参考

- 官方 Hooks 参考文档：https://code.claude.com/docs/en/hooks  
- Hooks 实践指南（示例更多）：https://code.claude.com/docs/en/hooks-guide  
- Settings 文件结构：https://code.claude.com/docs/en/settings
