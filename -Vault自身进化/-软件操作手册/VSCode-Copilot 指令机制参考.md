# VS Code Copilot 自定义指令机制 — 完整参考

> 基于官方文档（https://code.visualstudio.com/docs/copilot/customization/custom-instructions）整理，结合实测补充（2026-03-30）

---

## 一、核心概念

自定义指令（Custom Instructions）让你用 Markdown 文件预先定义规则，Copilot 在生成代码或处理任务时会自动参考这些规则，而不需要你每次在对话框里手动输入背景信息。

> **重要限制**：自定义指令**不会**影响编辑器里的行内补全建议（Inline Suggestions），只对 Chat 对话生效。

---

## 二、注入方式分类

### 🟢 全局自动注入（Always-on）

> 无需任何条件，每次 Chat 请求都会自动带入。

| 文件 / 来源                                   | 路径                                                                              | 说明                               |
| ----------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------- |
| `.github/copilot-instructions.md`         | workspace 根目录下的 `.github/` 文件夹                                                  | 最常用的全局指令文件，适合整个项目的编码规范           |
| `AGENTS.md`                               | workspace 根目录                                                                   | 适合多 AI Agent 协同场景，也可通过实验设置支持子文件夹 |
| `CLAUDE.md`                               | workspace 根目录 / `.claude/CLAUDE.md` / `~/.claude/CLAUDE.md` / `CLAUDE.local.md` | 兼容 Claude Code 等工具，VS Code 同样识别（建议关闭 `chat.useClaudeMdFile` 避免 Copilot 重复注入）  |
| 组织级别指令                                    | 在 GitHub 组织层级配置                                                                 | 跨多个仓库共享，自动应用到所有 Chat 请求          |
| 用户级 `.instructions.md`（含 `applyTo: "**"`） | `~/.copilot/instructions/` 或当前 VS Code Profile 的 `instructions/` 文件夹            | 写了 `applyTo: "**"` 就等同全局         |

**适用场景举例**：

- 统一命名规范（PascalCase / camelCase）
- 声明技术栈和首选库
- 全局错误处理约定
- 文档规范

---

### 🟡 条件化自动注入（File-based / Conditional）

> 根据当前正在操作的**文件类型或路径**自动匹配，满足条件才注入。

核心文件类型：**`*.instructions.md`**

#### 生效机制

在文件的 YAML Front Matter 里配置 `applyTo` 字段（glob 模式），Agent 编辑哪类文件就自动带入对应的指令：

```yaml
---
name: 'Python Standards'
description: '针对 Python 文件的编码规范'
applyTo: '**/*.py'
---
# Python 编码规范
- 遵循 PEP 8
- 所有函数签名使用类型注解
```

#### 默认文件位置

|作用域|默认路径|
|---|---|
|Workspace 级|`.github/instructions/`（递归搜索子目录）|
|Workspace 级（Claude 格式）|`.claude/rules/`|
|用户级|`~/.copilot/instructions/`、`~/.claude/rules/`、当前 VS Code Profile 的 `instructions/`|

可通过 `chat.instructionsFilesLocations` 设置自定义额外搜索路径。

#### Front Matter 字段说明

|字段|必填|说明|
|---|---|---|
|`name`|否|UI 中显示的名称，默认为文件名|
|`description`|否|鼠标悬停时显示的简短描述|
|`applyTo`|否|glob 模式，匹配则自动注入；**若不填，则不会自动注入**|

> `.claude/rules/` 下的文件使用 `paths` 属性（数组格式）代替 `applyTo`，这是 Claude Rules 格式的差异。

**`applyTo` 常用写法**：

```yaml
applyTo: "-Vault空间/**"          # 指定目录及所有子目录
applyTo: "**/*.py"                # 所有 Python 文件
applyTo: "**/*.{ts,tsx}"          # 多后缀
applyTo: "src/**/*.test.ts"       # 特定目录下的测试文件
applyTo: "docs/**/*.md"           # 特定目录下的特定后缀
applyTo: "**"                     # 全部文件（等同全局）
```

**适用场景举例**：

- 前端 `.tsx` 文件用 React Hooks 规范
- 后端 `.py` 文件用 PEP 8
- `docs/**/*.md` 文档用写作风格规范
- 测试文件用测试框架约定

---

### 🔵 手动注入（Manual Attach）

> 不自动注入，需要用户在 Chat 时主动添加到请求中。

以下情况属于手动注入：

1. **`applyTo` 未填写的 `.instructions.md` 文件**：文件存在但没有 `applyTo`，不会自动触发，需手动附加到对话。
2. **在 Chat 输入框手动 @ 附加**：用户在对话中手动选择要引用的指令文件。
3. **在 Prompt Files 中引用**：在 `.prompt.md` 文件里用 Markdown 链接方式引用指令文件，作为提示词的一部分。

---

## 三、优先级规则

当多个来源的指令发生冲突时，按以下顺序，**优先级从高到低**：

```
用户级（个人）指令
    ↓
仓库级指令（.github/copilot-instructions.md 或 AGENTS.md）
    ↓
组织级指令（最低）
```

VS Code 会将所有匹配的指令文件**合并**后传给 AI，不保证特定顺序，但冲突时高优先级覆盖低优先级。

---

## 四、设置项驱动的指令（已部分废弃）

> ⚠️ 从 VS Code 1.102 起，代码生成和测试生成的设置项指令已**废弃**，建议改用文件方式。

以下场景仍可使用 Settings 配置（接受 `text` 或 `file` 属性的对象数组）：

|场景|设置项|
|---|---|
|Code Review|`github.copilot.chat.reviewSelection.instructions`|
|Commit 消息生成|`github.copilot.chat.commitMessageGeneration.instructions`|
|PR 描述生成|`github.copilot.chat.pullRequestDescriptionGeneration.instructions`|

---

## 五、特殊功能与机制

### 5.1 AGENTS.md 嵌套（实验性）

开启 `chat.useNestedAgentsMdFiles` 后，VS Code 递归搜索所有子文件夹中的 `AGENTS.md`，Agent 根据当前操作的文件路径自动决定使用哪个。适合 monorepo 场景（前端、后端各有独立规范）。

### 5.2 CLAUDE.md 兼容性

同时使用 VS Code Copilot 和 Claude Code 时，两者都能读取 `CLAUDE.md`，实现一份指令多工具共用。`CLAUDE.local.md` 用于本地专属指令（不提交版本控制）。

### 5.3 组织级指令

在 GitHub 组织层级定义，成员无需手动配置，VS Code 自动拉取并在 Chat 中应用。需开启设置 `github.copilot.chat.organizationInstructions.enabled: true`。

### 5.4 AI 生成指令

- **`/init`**：分析 workspace 结构和编码习惯，自动生成全局 `copilot-instructions.md`
- **`/create-instruction`**：根据描述生成针对性的 `.instructions.md` 文件（可从当前对话中提取规则）

### 5.5 跨设备同步

用户级 `.instructions.md` 文件可通过 VS Code Settings Sync 同步。在 **Settings Sync: Configure** 中勾选 **Prompts and Instructions** 即可。

### 5.6 指令内引用其他文件

支持在指令文件正文里用 Markdown 链接引用其他指令文件，实现组合复用：

```markdown
Apply the [general coding guidelines](./general-coding.instructions.md) to all code.
```

也支持引用 Agent 工具：`#tool:web/fetch`

---

## 六、全景对比表

|维度|`.github/copilot-instructions.md`|`*.instructions.md`|`AGENTS.md`|`CLAUDE.md`|Settings|
|---|---|---|---|---|---|
|**注入方式**|全局自动|条件自动 / 手动|全局自动|全局自动|场景自动|
|**作用域**|Workspace|Workspace / 用户|Workspace / 子文件夹|Workspace / 用户|特定操作|
|**条件控制**|无|`applyTo` glob|无（或实验性子目录）|无|固定场景|
|**跨工具兼容**|Copilot|Copilot|多 Agent|Claude Code + Copilot|Copilot 专属|
|**版本控制**|✅ 推荐共享|✅ 推荐共享|✅ 推荐共享|✅ / local 版不提交|❌ 通常不共享|
|**废弃状态**|正常|正常|正常|正常|部分废弃|

---

## 七、最佳实践建议

1. **起步**：先用一个 `.github/copilot-instructions.md` 管理全局规范
2. **细分**：对前端/后端/测试等不同文件类型，再用 `.instructions.md` + `applyTo` 精细控制
3. **原因优先**：指令里说明 _为什么_，比只说 _是什么_ 效果更好（AI 在边界情况下判断更准）
4. **具体示例**：提供正面和反面代码示例，比抽象规则更有效
5. **避免冗余**：不需要重复 linter/formatter 已经强制的规范
6. **monorepo**：用 `AGENTS.md` 的实验性嵌套功能，或用多个带精确 `applyTo` 的 `.instructions.md`
7. **诊断**：在 Chat 视图右键选 **Diagnostics** 可查看所有已加载的指令文件及错误

---

## 八、相关设置项速查

|设置项|说明|
|---|---|
|`chat.instructionsFilesLocations`|自定义指令文件搜索路径|
|`chat.includeApplyingInstructions`|是否启用基于 `applyTo` 模式的自动指令注入|
|`chat.includeReferencedInstructions`|是否处理指令文件内的 Markdown 链接引用|
|`chat.useAgentsMdFile`|是否启用 `AGENTS.md` 支持|
|`chat.useNestedAgentsMdFiles`|是否启用嵌套子文件夹 `AGENTS.md`（实验性）|
|`chat.useClaudeMdFile`|是否启用 `CLAUDE.md` 支持|
|`chat.useCustomizationsInParentRepositories`|monorepo 场景下是否从父仓库根目录查找指令|
---

## 九、Agent 文件（`.agent.md`）

### 9.1 文件位置与格式

| 作用域 | 路径 |
|---|---|
| Workspace 级 | `.github/agents/` |
| 用户级 | `%USERPROFILE%\AppData\Roaming\Code\User\prompts\agents\`（疑似 bug，`prompts\` 根目录也可能识别）|

格式：`*.agent.md`（实测 `*.md` 也被识别，疑为 ==bug==）

### 9.2 召唤方式

| 方式 | 效果 |
|---|---|
| Chat 窗口左下角 Agent 图标弹出列表选择 | 叠加注入（和 instructions/prompt 无区别）|
| 对话让主代理自然触发 | 叠加注入 |
| `runSubagent` 工具调用 | ==独立上下文== 子代理 |

**Claude Code 中召唤**：`/subagent` 或对话触发。

### 9.3 frontmatter 字段示例（实测可用）

```yaml
---
name: 明日香打游戏
description: "赛博王国游戏协同子代理。"
tools: ['read', 'search', 'execute']
model: ['claude-opus-4-6', 'gpt-4o']  # 填真实模型 ID，按顺序尝试
user-invocable: true                   # true = 在 Agent 图标列表中可见
disable-model-invocation: false        # false = 允许被其他代理/子代理自动调用
---
```

### 9.4 子代理隔离的真实情况（实测 2026-03-30）

- ✅ 子代理可以成功召唤（`runSubagent` 工具或对话自然触发）
- ✅ 上下文干净，无主对话历史
- ⚠️ 但 `copilot-instructions.md` / `AGENTS.md` **仍会被注入**
- ⚠️ 需要聪明模型（Sonnet 级别），Haiku 很可能压根不召唤甚至假装召唤了 😜
- ❌ 非真正沙箱隔离，真正隔离需绕开 VS Code workspace 注入机制（独立 API 调用）

> [!tip] Chat 窗口右上角齿轮图标，可查看当前已加载的 Agent、Skills 等配置。|`github.copilot.chat.organizationInstructions.enabled`|是否拉取 GitHub 组织级指令|

---

## 九、如何查看当前请求注入了哪些文件

**方法一：Diagnostics（全貌）**

> VS Code Chat 面板空白处 **右键** → `Diagnostics`

可以看到所有已加载的：指令文件、技能、智能体、以及任何加载错误。

**方法二：References（本次请求）**

每次 AI 回复后，底部会出现 **References** 展开区（夹子图标），显示本次请求**实际使用**了哪些指令/技能文件。

> 两者区别：Diagnostics = 全量已注册，References = 本次请求实际采用。

---

## 十、Custom Agents（.agent.md）

### 与 AGENTS.md 的本质区别

| | AGENTS.md | Custom Agent (`.agent.md`) |
|---|---|---|
| **工作方式** | 被动注入，始终在 context | 主动切换，从 dropdown 选后才激活 |
| **叠加性** | Always-on | 叠加在全局指令之上（不能替换/屏蔽） |
| **工具控制** | ❌ 无法限制 | ✅ 可用 `tools:` 限制可用工具 |
| **人格切换** | 不支持 | ✅ 独立指令体 |
| **存放位置** | 工作区根目录 | `.github/agents/*.agent.md` 或用户级 |

### 关键认知：Custom Agents 是"叠加"而非"隔离"

Custom Agent 激活后，`copilot-instructions.md`、`AGENTS.md` 等**仍然在 context 中**。  
Agent 指令只是**追加**在全局指令之后，优先级上覆盖冲突项，但无法真正"屏蔽"全局配置。

### 当前王国的 Agent 文件

| Agent | 位置 | 说明 |
|---|---|---|
| `DOGE 效率部` | `~\AppData\Roaming\Code\User\prompts\doge.agent.md` | 用户级，全工作区可用 |
| `🎮明日香` | `.github/agents/🎮明日香.agent.md` | 工作区级，`user-invocable: false`，游戏专用 |
| `吹牛老爹` | `.github/agents/吹牛老爹.agent.md` | 工作区级，测试用 |
| `Explore` | VS Code 内置 | 快速代码探索只读 agent |

### 子目录 AGENTS.md 适用场景

```
-Vault空间/Games/AGENTS.md   ← 进入 Games 目录工作时自动叠加注入
                               不能作为"隔离沙箱"，仍与全局指令合并
```

适合：为特定模块追加背景知识（游戏坐标系统、API 约定）  
不适合：希望完全隔离全局规则的场景

---

## 十一、Subagents — 实测结论（已验证，2026-03-30）

### 理论 vs 实测

| | 理论描述 | 实测结果（Sonnet 4.6）|
|---|---|---|
| **对话历史** | 全新，不含主对话 | ✅ 确认隔离 |
| **Workspace 指令** | "全新干净上下文" | ❌ **仍然注入** |
| **用户身份** | 不知道 | ❌ 从 workspace 指令读到"指挥官" |
| **Vault 路径** | 不知道 | ❌ 知道 V2/V3 路径 |
| **主 agent 身份** | 不知道 | ❌ 知道是 Claude Sonnet 4.6 |

### 实测过程

创建 `吹牛老爹.agent.md`（`user-invocable: false`），通过 `runSubagent` 召唤并询问它"你是谁、我是谁、召唤者是谁"。  
结果：吹牛老爹正确说出"指挥官"、"ObsidianVaults_V3"、"Claude Sonnet 4.6"。

### 结论

**VS Code Copilot 的 `runSubagent` ≠ 真正的沙箱隔离。**

它的"干净上下文"指的是：**没有当前对话的聊天记录**。  
但 workspace-level 的指令文件（`copilot-instructions.md`、`AGENTS.md` 等）**依然会被注入**进 subagent。

真正的隔离需要：另起独立 API 调用，完全绕开 VS Code 的 workspace 注入机制（如直接调用 Anthropic API，不经过 Copilot 的 Chat 层）。

### Custom Agent vs Subagent 对比（修正版）

| | Custom Agent（dropdown 选择）| Subagent（runSubagent 召唤）|
|---|---|---|
| **对话历史** | 叠加主对话历史 | ✅ 全新，无历史 |
| **Workspace 指令** | 全局指令注入 | ❌ **仍然注入**（实测确认）|
| **用户身份可见** | 可见 | 可见（从指令文件获取）|
| **激活方式** | 用户手动切换 | 主 agent 用 `runSubagent` 工具调用 |
| **结果归还** | 继续在主对话中 | 执行完返回摘要给主 agent |

### `chat.useClaudeMdFile` 与 Claude Code 插件

`chat.useClaudeMdFile: false` **只影响 VS Code Copilot Chat**，不影响 Claude Code 插件（独立读取）。  
→ 关闭是正确的，避免 Copilot 重复注入 Claude 专用配置。

### Subagent 嵌套设置

```json
"chat.subagents.allowInvocationsFromSubagents": true
// 允许子代理再召唤子代理（最深5层），默认 false
```

### Haiku vs Sonnet：子代理召唤失败的根因

用 Claude Haiku 时子代理工具调用链经常失败，因为：
- `runSubagent` 需要嵌套工具调用判断（识别语义 → 生成 tool_use → 解析返回）
- Haiku 模型参数量不足，复杂工具调用容易出错或根本不解析指令
- 换 Sonnet 4.6 后召唤成功率大幅提升（本次测试即用 Sonnet 4.6 首次成功召唤）
