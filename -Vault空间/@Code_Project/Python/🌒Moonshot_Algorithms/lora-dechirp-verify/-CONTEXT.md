# -CONTEXT — LoRa CSS 解调机制验证实验

## 这是什么
Python 数值仿真，验证 LoRa Chirp Spread Spectrum (CSS) 的正确解调机制：
**共轭相乘（Dechirping）+ FFT**，并可视化三步流程。

起因：豆包将 LoRa 解调描述为"滑动内积"，本项目用代码证伪。

## 跨 session 提醒
- 入口：`src/lora_dechirp.py`，直接 `python src/lora_dechirp.py` 运行
- 输出两张图：`lora_demod_viz.png`（解调流程）和 `lora_snr_curve.png`（BER 曲线）
- 依赖：numpy + matplotlib，无需安装其他库
- **chirp 生成简化版**：不含频率 wrap-around，足够演示原理

## 当前状态
- ✅ PRD 完成（2026-03-31）
- ✅ 代码完成（2026-03-31）
- ✅ 运行验证完成（2026-03-31）
- ✅ 人类解释文档完成（2026-03-31）

## 实测结果（2026-03-31）
- 无噪声验证：6 个边界符号全部正确 ✓
- SNR 扫描（SF=7, N=128, 100符号/点）：**99% 门限 SNR ≈ -10 dB**
- 与 LoRa 官方规格书灵敏度数据高度一致
- 输出图：`lora_demod_viz.png`（三联流程图）、`lora_snr_curve.png`（BER曲线）

## 目录结构

```
lora-dechirp-verify/
├── -PRD.md              ← 需求文档
├── -CONTEXT.md          ← 本文件
├── 给人类解释.md         ← 数学原理 + 实验结果 + 代码架构（人话版）
├── lora_demod_viz.png   ← 三联流程图（时域/dechirp后/FFT）
├── lora_snr_curve.png   ← SNR-正确率曲线
└── src/
    └── lora_dechirp.py  ← 主程序（含可视化 + SNR 测试）
```

## 下一步
- ⏳ 可扩展：加入 NN 解调对比（见 `pid-nn-norm-compare` 项目的 L1/L2 框架）
- ⏳ 可扩展：加入频率 wrap-around（折回），让仿真更贴近真实 LoRa 物理层
