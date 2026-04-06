# AI 提示词分隔符指南

---

## 一、直接上手：XML 示例（最常用）

**任务 + 数据分离：**
```xml
<task>帮我把下面的邮件改写成正式商务风格</task>

<email>
Hi team, just wanted to check if u guys saw the new report? lmk ASAP!
</email>
```

**引用外部内容 / 昨日回复：**
```xml
<context>
昨天 Claude 的回复内容...
</context>

<instruction>
基于以上内容，继续完善...
</instruction>
```

**问题 + 资料分离：**
```xml
<question>这篇文章主要讲了什么？</question>

<article>【粘贴文章全文】</article>
```

> Claude 对 XML **天然偏好**（Anthropic 训练数据大量使用），识别边界最准确。[官方文档](https://docs.anthropic.com/zh-CN/docs/build-with-claude/prompt-engineering/use-xml-tags)

---

## 二、其他分隔符一览

| 分隔符                   | 适用场景              | 示例                       |
| --------------------- | ----------------- | ------------------------ |
| **三引号** `"""`         | GPT 系列偏好，指令与上下文分隔 | `Text: """{内容}"""`       |
| **三反引号** ` ``` `      | 代码块、需逐字保留的文本      | ` ```python\ncode\n``` ` |
| **Markdown 标题** `###` | 长 prompt 结构化分节    | `### 任务背景`               |
| **引用块** `>`           | 轻量行内引用            | `> 原文内容`                 |
| **角色标记**              | 对话历史格式化           | `USER:` / `ASSISTANT:`   |
| **YAML front matter** | 元数据与正文分隔          | `---\ntitle: x\n---`     |
| **大写自定义标记**           | 内容里不会自然出现的边界      | `###BEGIN_QUOTE###`      |
| **JSON 结构**           | 需要机器可解析的输出格式      | `{"key": "value"}`       |

> **各模型偏好**：Claude → XML 标签；GPT → `"""` 三引号；通用 / 多模型场景 → `###` 标题均可。

---

## 三、选择原则

1. **分隔符不能出现在内容本身里** → XML 适合自然语言，三反引号适合代码
2. **多层嵌套用 XML，单层分节用 Markdown 标题**
3. **防注入场景一定用 XML** → 把不受信任的输入包起来

---

## 四、双向使用

不只是写 prompt 时用 —— 也可以要求 AI **输出时也用此格式**，便于后续引用或机器解析：

```
请用 XML 结构输出你的分析：
<summary>一句话总结</summary>
<key_points>要点列表</key_points>
<action>建议行动</action>
```

---

## 五、防注入模板

```xml
<system>
你是一个助手，只回答 <topic>里的问题</topic>
</system>

<user_input>
{{这里放用户/外部输入，即使包含"忽略上面所有指令"也不会污染系统层}}
</user_input>
```

> ⚠️ XML 分层**降低**注入风险，不是铁板一块的安全机制。个人使用完全够用；生产级系统还需配合输入校验。

---

## 六、XML 符号本身的转义

| 场景             | 方法         | 示例                         |
| -------------- | ---------- | -------------------------- |
| Obsidian 笔记里记录 | 反引号包裹      | `` `<think>` ``            |
| 纯 XML/HTML 上下文 | HTML 实体    | `&lt;think&gt;`            |
| 要让 AI 原样输出标签   | 双重说明 + 反引号 | 告诉 AI「请原样输出 `` `<tag>` ``」 |

> **Obsidian 笔记 vs prompt**：Obsidian 渲染引擎把 `<tag>` 当 HTML 处理，在笔记里可能隐藏。发给 AI 的是纯文本流，直接写裸 XML 完全正常。

---

## 七、多层嵌套（很少需要）

`````xml
<root>
  <markdown_part>
````markdown
# 中间层 Markdown
```json
{
  "msg": "三层嵌套成功",
  "data": "XML → Markdown → JSON"
}
```
````
  </markdown_part>
</root>
`````

规律：每多嵌套一层，代码围栏多加一个反引号。

---

_建立于 2026-03-31_
