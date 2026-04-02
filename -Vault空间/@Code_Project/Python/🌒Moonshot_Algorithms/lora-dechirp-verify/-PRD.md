# PRD — LoRa CSS 解调机制验证实验

> 来源：`D:\ObsidianVaults_V2\zzzz_神经网络的其他应用\0_Sonnet的思考.md` 严重错误 #1
> 日期：2026-03-31

---

## 背景与目的

豆包在讨论 LoRa 解调时，将核心操作描述为"**滑动内积**"，这是错误的。
正确的 LoRa CSS 解调是：**共轭相乘（Dechirping）+ FFT**。

本实验用 Python 数值仿真，直观验证这个机制，生成可视化输出作为教学材料。

---

## 功能需求

| # | 需求 | 验收标准 |
|---|------|---------|
| F1 | 生成 LoRa up-chirp（可变 SF、BW、symbol） | 数值与理论公式吻合 |
| F2 | 实现 dechirping + FFT 解调 | 无噪声时 100% 正确率 |
| F3 | 三图合一可视化（时域→dechirp→FFT） | 保存 `lora_demod_viz.png` |
| F4 | SNR 扫描测试（-20dB 到 +20dB） | 保存 `lora_snr_curve.png`，绘制 BER 曲线 |

---

## 技术约束

- 语言：**Python 3.x**
- 依赖：`numpy`, `matplotlib`（scipy 可选）
- **不含**：硬件接入、完整 LoRa 协议栈、包头/CRC 解析
- 只验证物理层解调原理，不含循环移位的 wrap-around（简化版）

---

## 不包含范围

- 多路径信道建模
- 实际 LoRa 设备通信
- 对 Doubao 说的"2~3 个数量级性能提升"的 NN 解调对比（这是后续项目）
