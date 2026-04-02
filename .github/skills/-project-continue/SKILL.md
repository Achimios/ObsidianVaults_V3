---
name: -project-continue
description: >
  CyberDomain V3 session continuity workflow. Use when: starting a new session,
  继续上次工作, resuming work, asking about -where_continue or -CONTEXT,
  session ending 对话收尾, updating -CONTEXT.md or -where_continue.md,
  writing to -LEARNINGS.md, entering a subdirectory for the first time,
  需要记录什么, 下一步是什么, 上次做到哪, 记录上下文,
  save context, save progress, record work, end of session.
  Defines: layered read rules, -CONTEXT format, -LEARNINGS format,
  -where_continue sync rules.
---

# Project Continue — V3 Session Continuity

## 分层读取法则（Session 开始时）

1. **每次对话开始**：人类手动把 `-where_continue.md` 里的最近工作层 `-CONTEXT.md` 路径粘贴到对话框。没粘贴就别管 😏
2. 粘贴的 `-CONTEXT.md` 提到进入某子目录时 → 跳转读该目录的 `./-CONTEXT.md`
3. **进入代码项目目录时** → 扫描该目录的 `AGENTS.md`（有则读取，规则同 -CONTEXT）
4. **触发 -LEARNINGS**：同一错误连续失败 2+ 次 → grep 搜索当前工作层或所有层的 `-LEARNINGS.md`
5. **禁止无脑全读**：不要一次性读取所有目录的 CONTEXT

---

## -CONTEXT.md 写法规范

每层目录放一个 `-CONTEXT.md`，目录越深描述越细。

```markdown
## 这是什么（1-2 句）
## 跨 session 提醒（坑点/约定）
## 当前状态（✅已完成 / 🔄进行中 / ⏳待做）
## 上次做了什么（日期 + 行动）
## 下一步（按优先级，第一条加 👆 继续）
```

维护原则：
- 有效条目随进度提炼精简，删掉冗余/无效条目
- 当前状态写具体，不写"进行中"之类模糊词
- 古早已完成且无参考价值的条目要主动删除

---

## -LEARNINGS.md 写法规范

每层目录放一个 `-LEARNINGS.md`，记录本层的坑点和高效方法。

```markdown
## 多次出错的地方找到解决方法后写入
## 找到一个高效方法后写入
## 同一 pattern 3次 → 提升至 HOT，精炼后置顶
```

---

## -where_continue.md 同步规则（Session 结束前）

**顺序：先更新 -CONTEXT，再更新 -where_continue。**

1. **`-CONTEXT.md`**（本次工作的目录层）：记录做了什么 + 下一步
2. **`-where_continue.md`**（V3 根目录）：第一条 = 最近工作层 + 下一步说明，保留最新 3 条

格式示例：
```markdown
1. **根目录 + .github/** — `./-CONTEXT.md`
   → 已完成：X → 下一步：Y
```

更新完毕后 → 弹结尾弹窗。
