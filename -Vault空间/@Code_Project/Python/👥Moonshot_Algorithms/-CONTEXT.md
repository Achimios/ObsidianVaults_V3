# -CONTEXT —  算法探索项目目录

## 这是什么
`@Code_Project/Python/👥Moonshot_Algorithms` 下所有 算法 项目的索引层。
项目来源：`0_Sonnet的思考.md`（神经网络相关话题审阅后产生的可执行操作）

---

## 子项目一览

| 项目 | 状态 | 简介 |
|------|------|------|
| `lora-dechirp-verify/` | ✅ 完成并验证 | LoRa CSS 解调机制证伪实验（Dechirping+FFT vs 滑动内积） |
| `pid-nn-norm-compare/` | ⏳ 待实现 | L1 vs L2 损失函数在浅层 PID 整定 NN 上的对比（含异常值注入） |
| `natural-gradient-nn/` | ⏳ 待实现（研究级）| 自然梯度法 / 信息几何 — 非 L2 参数空间 NN 的正确数学框架 |

---

## 跨 session 提醒
- `lora-dechirp-verify` 实测 99% 门限 SNR ≈ -10 dB，与 LoRa 规格书吻合
- `pid-nn-norm-compare` 的关键点：L1 正则化 ≠ MAE 损失 ≠ L1 度量空间（三个概念要分开实验）
- `natural-gradient-nn` 需先读 Amari 1998 原文，jax 或 backpack 库实现 K-FAC 近似

---

## 下一步
- ⏳ 👆 实现 `pid-nn-norm-compare`（见其 `-CONTEXT.md`）
