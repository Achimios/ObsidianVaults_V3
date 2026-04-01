# -LEARNINGS — Vault 自身进化经验

> Vault 架构设计、AI 工具使用、文档规范类教训。
> 触发读取：Vault 结构改动失败、CLI 报错、wikilink 断裂时搜索此文件。

---

## [LRN-V3-001] Obsidian CLI 中只有文件能 rename，文件夹改名用 VS UI

**类别**：best_practice | **领域**：Obsidian CLI

- `obsidian rename path="file.md" name="new.md"` → ✅ 可用，自动更新 wikilink
- `obsidian move path="file.md" to="folder/"` → ✅ 可用（文件）
- **文件夹重命名** → ❌ CLI 无此命令，必须在 Obsidian UI 内手动操作（自动更新内链）
- 或 PowerShell `Rename-Item` + 手动更新所有引用（高风险，不推荐）

---

## [LRN-V3-002] AI 幻觉 Obsidian CLI 命令（勿照抄未验证文档）

**类别**：knowledge_gap | **领域**：工具验证

以下命令**全部不存在**，是 AI 幻觉：
`obsidian link:mentions`, `obsidian graph:path`, `obsidian suggest:links`, `obsidian graph:clusters`  
**正确验证方法**：`obsidian --help` 或 `obsidian help <cmd>` — 只信官方 help 输出。

---

## [LRN-V3-003] ~ 前缀在 WSL2/bash 有展开风险

**类别**：correction | **领域**：跨平台路径

`~foo` 在 bash 行首被解释为用户名展开（若不存在则保留原样，但易出错）。  
**V3 统一规则**：文件夹和文件前缀统一用 `-`（安全、排序前置、跨平台无歧义）。

---

## [FEAT-V3-001] RAG 长期记忆（Phase 2 触发式）

**类别**：pending feature | **领域**：Vault 基础设施

**触发条件**：Vault > 500 文件 **或** 概念搜索成为明显瓶颈。  
候选方案：`chromadb` + `sentence-transformers` 本地向量嵌入，或 `llama-index` 直接索引 .md。  
当前策略：Agentic Search（grep/file_search）为主，RAG 按需补充。  
→ 详见 V2 FEATURE_REQUESTS.md `FEAT-20260320-001`

---
