# -LEARNINGS — V3 根目录通用经验

> 全局性规则、工作流教训、跨模块适用的经验。
> 触发读取：同一类型操作连续失败 2+ 次时，搜索此文件。

---

## [LRN-001] TTS 声线不能混用

**类别**：correction | **领域**：TTS / 人格分离

老维（Victor）发声 → 宏名`VOICE_VICTOR`，直调 `tts_engine.py`  
明日香（Asuka）发声 → 宏名`VOICE_ASUKA`，守护进程 `localhost:5199/speak`  
**绝对禁止**老维调用 `speak_claw.ps1`（硬编码女声）。  
→ 详细规则在 userMemory `game_automation_rules.md`

---

## [LRN-002] 任务前必读 -CONTEXT，勿靠记忆

**类别**：knowledge_gap | **领域**：工作流

不读 `-CONTEXT.md` 就开工 → 操作按旧架构执行 → 与现实不符。  
正确流程：**新对话 → 读根目录 `-CONTEXT.md` → 读 `0_AI通用接入口.md` → 按需读子层 `-CONTEXT.md` → 再行动。**

---

## [LRN-003] Obsidian CLI 默认连接当前打开的 Vault

**类别**：best_practice | **领域**：工具使用

在 multi-root workspace 中，`obsidian <cmd>` 默认作用于 Obsidian 应用中**当前活跃的 vault**。  
要切换到 V2 或 V3，需用 `obsidian vault=<name>` 参数，或在 Obsidian 应用中切换 vault 后再调用。  
验证方法：`obsidian files total` — 会显示文件数，对比两个 vault 确认当前连接。

---
