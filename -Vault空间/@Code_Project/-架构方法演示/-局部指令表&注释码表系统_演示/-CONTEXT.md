# -CONTEXT — 架构方法演示项目

## 这是什么
纯演示项目，展示「分层 -CONTEXT + 局部指令表 + >v< 注释码表」三合一系统的用法。
**不是真实代码**，是给 AI 学习如何快速读懂巨型代码库的方法论样本。

## 跨 session 提醒
- `.rs` 文件是伪代码，只有注释有意义
- 真正的核心是 `-📇索引码表.md` 和 `AGENTS.md` 两个文件

## 当前状态
- ✅ 演示目录树建立（2026-03-29）
- ✅ 五个伪代码文件含真实 `>v<` 注释示例
- ✅ 码表与指令表建立
- ⏳ 待测试：新开 session，丢给 Opus，看是否能快速读懂结构

## 目录结构

```
-局部指令表&注释码表系统_演示/
├── AGENTS.md                 ← 局部规则（VS Code NestedAgentsMd 自动注入）
├── -📇索引码表.md            ← >v< 标注主索引
└── src/
    ├── core/ahrs/ahrs.rs     ← >v<🧠AHRS算法 + >v<📐四元数
    ├── io/ring_buffer.rs     ← >v<➰环形缓冲区
    ├── sensors/calibration.rs← >v<🌡传感器校正
    └── hal/dma_handler.rs    ← >v<⚡中断处理
```

## 下一步
- ⏳ 👆 新开 session 测试：让 AI 只读此 CONTEXT，看能否快速定位核心算法
