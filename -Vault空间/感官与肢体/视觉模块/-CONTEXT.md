---
applyTo: "~Vault空间/视觉模块/**"
---

# 视觉模块工作规则

## 模块状态
📦 **规划中** — 尚未迁移到 V3

## V2 参考位置
`D:\ObsidianVaults_V2\超梦空间\~Modules_专用模块\感官与肢体\视觉模块\`

## 技术栈（V2 验证过）
- `vision_engine.py` — 截图 + Vision API 调用
- `vision_blackboard/` — 截图临时存储目录

## 接口规范（V2）
- 截图路径：`Workbench/vision_blackboard/`
- Vision API：通过 AnyRouter 代理调用（凭证在 `-档案室/`）

## 待建内容
- `vision_engine.py` 迁移
- `vision_blackboard/` 目录
- 图像处理中枢集成方案
