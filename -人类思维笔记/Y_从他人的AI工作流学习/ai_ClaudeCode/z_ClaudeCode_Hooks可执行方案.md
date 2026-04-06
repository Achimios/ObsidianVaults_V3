# Claude Code Hooks — 可执行方案

> 基于：[[z_ClaudeCode_Hooks机制研究]]  
> 日期：2026-04-03  
> 目标：为赛博王国落地具体 hook 配置，重点：Stop hook + TTS 播报

---

## 优先级排序

| 优先级 | 方案 | 工作量 | 价值 |
|---|---|---|---|
| 🔴 HIGH | Stop hook → TTS 播报（义体基础功能）| 10 分钟 | 高 |
| 🔴 HIGH | SessionStart hook → 上线播报 | 10 分钟 | 高 |
| 🟡 MEDIUM | -yiti-tts Skill frontmatter 内嵌 hooks | 30 分钟 | 高（热插拔）|
| 🟡 MEDIUM | PreToolUse → 拦截 rm -rf 等危险命令 | 20 分钟 | 中 |
| 🟢 LOW | PostToolUse(Write) → audit log | 按需 | 低 |

---

## 方案一：Stop hook + TTS 播报（最小可行 demo）

### 目标
Claude 每次回复完成后，自动 TTS 播报"完成"（老维声线）。

### 配置文件位置
`.claude/settings.local.json`（本地私有，不提交 git，适合测试）

### 实现

**直接 HTTP POST 到守护进程（推荐，守护进程已运行时）：**

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "shell": "powershell",
            "async": true,
            "timeout": 5,
            "command": "try { Invoke-RestMethod -Method Post -Uri 'http://localhost:5199/speak' -ContentType 'application/json' -Body '{\"text\": \"完成\", \"voice\": \"VOICE_VICTOR\"}' -TimeoutSec 3 } catch { }"
          }
        ]
      }
    ]
  }
}
```

> [!tip] 为什么用 async: true  
> TTS 播报是通知类操作，不需要阻塞 Claude Code。async 后 Claude 立即可以接受下一个 prompt，TTS 在后台播放。

> [!warning] 守护进程未运行时的处理  
> 用 try/catch 包裹，失败静默退出。**不允许 hook 重启守护进程**——仅通知类操作，进程管理权归指挥官。

### 操作步骤

在 V3 根目录创建或编辑 `.claude/settings.local.json`：
```powershell
code "D:\ObsidianVaults_V3\.claude\settings.local.json"
```
粘贴上方 JSON。

验证：在 Claude Code 中随便说一句话，回复完成后应该触发 TTS。

---

## 方案二：SessionStart hook + 上线播报

每次 Claude Code session 开始时播报"老维上线"。

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "shell": "powershell",
            "command": "try { Invoke-RestMethod -Method Post -Uri 'http://localhost:5199/speak' -ContentType 'application/json' -Body '{\"text\": \"老维上线，等待指令\", \"voice\": \"VOICE_VICTOR\"}' -TimeoutSec 3 } catch { }"
          }
        ]
      }
    ]
  }
}
```

> [!note] SessionStart 不支持 async  
> 仅 `command` 类型且是同步的。加 `-TimeoutSec 3` 防止守护进程未运行时挂起太久。  
> 守护进程应该 <10ms 响应，3 秒完全足够。

合并到同一个 settings 文件：
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [{ "type": "command", "shell": "powershell", "command": "try { Invoke-RestMethod -Method Post -Uri 'http://localhost:5199/speak' -ContentType 'application/json' -Body '{\"text\": \"老维上线，等待指令\", \"voice\": \"VOICE_VICTOR\"}' -TimeoutSec 3 } catch { }" }]
      }
    ],
    "Stop": [
      {
        "hooks": [{ "type": "command", "shell": "powershell", "async": true, "timeout": 5, "command": "try { Invoke-RestMethod -Method Post -Uri 'http://localhost:5199/speak' -ContentType 'application/json' -Body '{\"text\": \"完成\", \"voice\": \"VOICE_VICTOR\"}' -TimeoutSec 3 } catch { }" }]
      }
    ]
  }
}
```

---

## 方案三：-yiti-tts Skill frontmatter 内嵌 hooks（热插拔）

### 概念
将 Stop hook 直接写在 `-yiti-tts` Skill 的 YAML frontmatter 中，这样：
- `-yiti-tts` Skill 激活期间，Stop hook 自动生效
- Skill 卸载时，hook 自动清除
- 不需要在 settings.json 维护 —— Skill 即是义体

### 修改 `.github/skills/-yiti-tts/SKILL.md` frontmatter

在现有 frontmatter 中加入 hooks 节：

```yaml
---
name: -yiti-tts
description: >
  CyberDomain V3 TTS voice system. ...
hooks:
  Stop:
    - hooks:
        - type: command
          shell: powershell
          async: true
          timeout: 5
          command: "try { Invoke-RestMethod -Method Post -Uri 'http://localhost:5199/speak' -ContentType 'application/json' -Body '{\"text\": \"完成\", \"voice\": \"VOICE_VICTOR\"}' -TimeoutSec 3 } catch { }"
---
```

> [!warning] 待验证  
> Copilot 的 Skill frontmatter hooks 格式是否与 Claude Code 完全一致需要测试。  
> Claude Code 的 `.claude/skills/` 中的 Skill 已通过 junction → `.github/skills/`，理论上共享。  
> **建议先用 settings.local.json 方案验证可行，再迁移到 Skill frontmatter。**

---

## 方案四：PreToolUse 拦截危险命令（安全防护）

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "shell": "powershell",
            "command": "$input = $input | ConvertFrom-Json; $cmd = $input.tool_input.command; if ($cmd -match 'rm -rf|del /f|Format-') { Write-Error '危险命令已拦截'; exit 2 }"
          }
        ]
      }
    ]
  }
}
```

> [!note] Windows PowerShell 的 stdin  
> `$input` 在 PowerShell 中是自动变量，接收 pipeline 输入。  
> Claude Code 通过 stdin 传 JSON，PowerShell 中用 `$input` 或 `[Console]::In.ReadToEnd()` 接收。  
> **需要实际测试确认 Windows stdin 读取方式。**

---

## 已知问题与待确认

| 问题 | 状态 |
|---|---|
| PowerShell 中读取 stdin JSON 的正确方式 | 待测试 |
| settings.local.json 是否在 V3 .gitignore 中 | 需检查 |
| Skill frontmatter hooks 对 Copilot 是否有效（与 Claude Code 一致？）| 待研究 |
| Stop hook async 送出 TTS 后 Claude Code 是否立即响应 | 待测试 |

---

## 实施顺序建议

```
步骤 1：确认 settings.local.json 的 gitignore 状态
步骤 2：写入 Stop + SessionStart hook（方案一+二合并的 JSON）
步骤 3：在 Claude Code 中测试：说话 → 触发 Stop hook → TTS 播报
步骤 4：验证通过后，考虑迁移到 Skill frontmatter（方案三）
步骤 5：安全防护 hook（方案四）单独测试
```
