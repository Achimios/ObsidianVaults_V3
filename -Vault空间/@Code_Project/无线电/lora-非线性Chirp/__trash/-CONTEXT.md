## 这是什么
非线性 Chirp 扩频通信交互仿真器（HTML/Canvas/JS 单文件）。模拟 LoRa 类 CSS 通讯，聚焦 LPI 和抗干扰研究。现实参数：2.4GHz 载波，500kHz 带宽，ms 级帧长。仿真放慢 1000 倍（500Hz BW、ms→s）。

## 当前最新文件
`chirp_v9_CW_Pulse.html` — 最后一个完整版本

## v9 已实现功能
- 调频类型：线性 Chirp / Perlin(LPI) / Zadoff-Chu
- 识别方式：相移 / 波形切换（两者×多波形 ON/OFF = 4 种模式）
- SF6/7/8，BW=500Hz，Fs=1000Hz
- DSSS（chip×2/4/8，PN种子）
- CP 循环前缀（标注"无实际效果，原理演示"）
- CW 窄带干扰（频率、JSR dB）
- 脉冲干扰（谐波EMI 周期 / 随机脉冲）
- BER×200 统计
- 音频播放（TX/RX，频率×，sym数控制长度）
- 多径/多普勒免疫说明（静态文字，已去掉控件）
- ZC makeZCwave 函数，互相关矩阵热力图⑥
- ⑦ CW 频率扫描 BER + 匹配滤波对比图（底部）

## v9 未完成 / 遗留 Bug（Claude 崩了10次，任务截断）
- ✅ 镜之边缘配色：已注入 `:root` CSS 变量块（`id=theme` 注释区，手动改一处全局生效）
- ✅ 左侧 sticky 参数栏：`.sidebar` 230px sticky + `.main-plots` 独立滚动
- ✅ 音频独立时长控制：新增 `时长×` select（×0.5/1/2/4），Phase Vocoder 简化版（插值拉伸，频率不变）
- ❓ 多波形注释（"每个symbol不同波形" / "每个symbol独立波形组"）—— 是否已加未确认
- ❓ DSSS chip× 联动 bug —— 是否已修未确认（v8 有 bug，v9 修了？）

## 核心物理结论（已验证，写入仿真说明框）
- **多普勒免疫**：2.4GHz 100m/s → fd=800Hz，下变频后基带频偏 0.16% BW，仿真等效 < 1 bin，可忽略
- **多径免疫**：100m 反射 τ=0.17 样本（@500kHz），CSS 长 symbol 天然吸收，无 ISI
- **CW 抗干扰**：处理增益 +21dB（SF7），需 JSR > +21dB 才影响 BER

## 数学讨论积累（对话记录 `1_对话记录.md`）
- ZC 互相关 vs Perlin：低 SNR 下差不多，ZC 优势在多用户确定性保证
- DSSS chip×2 比 ×8 频谱更分散；PN 种子筛选可优化 BER
- OCDM Moonshot 方向（Orthogonal Chirp Division Multiplexing）已提出，未实现

## 下一步（按优先级）
👆 1. 验证 v9 的遗留 bug（多波形注释、DSSS联动、音频 Chrome 问题）
2. 镜之边缘配色（ME主题 CSS 变量块）
3. 左侧 sticky 参数栏布局重构
4. 音频 Phase Vocoder 独立时长/频率
5. OCDM Moonshot —— 多 chirp 子载波同时发送（新方向）
