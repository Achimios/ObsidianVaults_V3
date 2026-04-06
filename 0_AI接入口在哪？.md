# CyberDomain V3 — AI 通用接入口

> 此文件也是给人类看的，告诉你如何添加自己的AI框架（Claude Code，OpenClaw，Codex，OpenCode等）


- Copilot内嵌在VS CODE，GUI的管理优势是超凡的。跑Sonnet/Opus执行重型代码任务、架构重组、高风险操作，**老派德国工程师**
- OpenClaw跑DeepSeek/Kimi(有视觉)作为 **实时操作员，藤原拓海**
- ClaudeCode跑 ? 执行自动化代码任务，很有个性不怎么理你，**法拉利设计师**
- Codex我还没用过，你自己看😜

- 目前Copilot是按次计费，每月10美元300次，且每月1日重置额度，因此搭配PARDON弹窗机制，额度根本用不完
- Copilot也有CLI版本
- 即使同样模型如 Kimi，ClaudeCode思考时间可能达1~4 min，而OpenClaw则是秒回复

## AI框架独占接入点

| 框架              | 入口文件                                | 状态     |
| --------------- | ----------------------------------- | ------ |
| VS Code Copilot | `./.github/copilot-instructions.md` | ✅ 自动注入 |
| Claude Code     | `./.claude/CLAUDE.md`               | ❌ 待建   |
| OpenClaw        | `./.openclaw/workspace/AGENTS.md等`  | ❌ 待建   |

## AI框架公共接入点在哪？

 `./AGENTS.md`，在根目录，内部包含：
- 架构总览、一级目录、义体模块索引
- 版本关系（V2 / V3）
- 行为准则、路径规范、分层读取法则
- -CONTEXT 写法规范


---
* [[1_人类接入手册_修订版]]：人类导航 
