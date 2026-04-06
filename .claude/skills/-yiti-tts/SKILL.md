---
name: -yiti-tts
description: >
  CyberDomain V3 TTS voice system. Use when: calling TTS/speech/发声/语音/speak,
  playing audio output, Victor needs to speak, 老维发声, typing TTS commands,
  game reporting, step announcements, or any audio output task.
  Covers: daemon HTTP interface, CLI invocation, voice IDs, Victor vs OpenClaw
  voice separation rules.
---

# 义体-TTS — 发声模块接口手册

## 架构概览

**主力引擎**：Volcengine BigTTS 2.0（~1-2s 冷启动，守护进程 <10ms 响应）  
**守护进程**：`http://localhost:5199/speak`（POST，threading.Lock 串行排队，多方请求不串声）  
**代码位置**：`../ObsidianVaults_V2/超梦空间/~Modules_专用模块/感官与肢体/听觉与发声/`

---

## 🚨 声线隔离铁律（绝对不可混淆）

| 人格 | 声线 ID | 调用方式 |
|---|---|---|
| **老维（Victor）** | `VOICE_VICTOR` | CLI 或守护进程 POST |
| **OpenClaw / 飞鸟** | `VOICE_OPENCLAW` | **守护进程 POST → `localhost:5199/speak`** |

**禁止老维调用 `speak_claw.ps1`**。  
老维只用下方两种方式发声。

---

## 老维发声 — 两种方式

### 方式一（推荐）：守护进程 HTTP（<10ms，守护进程已启动时）

```python
import urllib.request, json

def victor_speak(text: str):
    body = json.dumps({"text": text, "voice": "VOICE_VICTOR"}).encode()
    req = urllib.request.Request(
        "http://localhost:5199/speak",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
```

### 方式二：CLI 冷启动（守护进程未运行时降级）

```powershell
python "D:\ObsidianVaults_V2\超梦空间\~Modules_专用模块\感官与肢体\听觉与发声\tts_engine.py" "发声内容"
```

带声线切换（宏名由 `volcengine_tts.py` 自动映射为实际 voice ID）：
```powershell
python "D:\...\tts_engine.py" --voice "VOICE_VICTOR" "内容"
```

---

## 守护进程状态检查

```python
import urllib.request
try:
    urllib.request.urlopen("http://localhost:5199/speak", timeout=1)
    # 守护进程在线
except Exception:
    # 守护进程离线，降级 CLI 或通知指挥官
    pass
```

⚠️ 若守护进程未响应 → **立即停止**，弹弹窗告知指挥官，不得循环重试/自动重启。

---

## 常见场景模板

```python
# 任务开始前语音通知
victor_speak("开始执行：截图并识别游戏状态")

# 步骤完成通知  
victor_speak("截图已完成，正在分析坐标")

# 弹窗前提醒切回 VS Code
victor_speak("请切回 VS Code")
# 然后再调用 vscode_askQuestions
```
