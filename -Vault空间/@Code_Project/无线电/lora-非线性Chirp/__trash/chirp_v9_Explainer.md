# Perlin-CSS 非线性Chirp仿真器 — 原理理解摘要

## 核心概念

**非线性Chirp (Perlin-CSS)** 是一种 LPI (Low Probability of Intercept) 扩频通讯方案。

### 与标准LoRa的关键区别

| | 标准LoRa (线性CSS) | 本方案 (非线性/Perlin-CSS) |
|---|---|---|
| 频率轨迹 | `f(t)=FL+(FH-FL)·t/M`，解析可预测 | Perlin噪声生成，seed决定，不可解析 |
| 解调 | dechirp(共轭相乘) + FFT | 全模板匹配 (NA×M点积) |
| LPI | 中 — 任何SDR可识别 | 高 — 无seed无法复现波形 |
| 计算量 | 极低 | 中 (~1.7× 于NA=8时) |

### 定位
定位接近 **APART** (Adaptive Phonon-Activated Radio Transceivers) 风格：高LPI优先，种子即密钥。标准LoRa线性chirp任何SDR可识别，本方案不行。

## 仿真器结构

### 左侧控制面板 (sticky sidebar)
- **基础信号**: chirp类型(线性/Perlin/Zadoff-Chu)、识别模式(相移/波形切换)、SF/M值、SNR、各seed
- **扩频**: DSSS开关、Chip倍数、PN seed、循环前缀(CP)
- **干扰**: CW窄带干扰(频率/JSR)、脉冲干扰(谐波EMI/随机)

### 右侧图表区 (7个图)

1. **① 时域波形** — TX(黑) vs RX(橙)，脉冲干扰红竖线标注
2. **② 时频谱** — Hann窗STFT，CW显示水平亮线，脉冲显示竖向亮条
3. **③ 全局功率谱** — 监听者视角，CW呈尖锐谱线
4. **④ 匹配滤波相关** — 8模板互相关柱状图，绿✓正确、红✗误判
5. **⑤ 判决网格 & BER** — 20个symbol的解码结果网格
6. **⑥ 模板互相关矩阵** — 非对角暗=正交性好
7. **⑦ CW频率扫描BER** — 扫所有干扰频率看BER分布

### 声音播放
基带实数信号 → AudioContext，可调频率缩放、symbol数、时长

## 需要翻译的文字内容

### HTML UI (sidebar controls)
- 调频、识别、波形种、消息种、噪声种 等中文标签
- 按钮文字: 多波形、CP循环前缀、DSSS、CW窄带、脉冲干扰等
- 选择菜单选项: 线性Chirp、相移、波形切换、谐波EMI、随机脉冲等
- 播放控制: TX、停、×1原始、快、正常、慢 等

### 信息说明面板 (large info-box 区域)
- 📊 非线性Chirp CSS 原理 · LPI价值与工程权衡 (6个子面板)
  - 为什么非线性Chirp有LPI优势
  - 硬件实现路径 (4阶段)
  - M增大→灵敏度提升
  - M与NA翻倍对比
  - BW反直觉: 增大→灵敏度下降
  - NA权衡 (最佳甜点NA≤16)
  - 近距高干扰 vs 远距低干扰
  - IQ下变频与模板匹配

- 📐 匹配滤波分步动画说明

### 系统设计讨论备忘录 (底部8个子面板)
- ① 命名层次
- ② 前导码同步
- ③ 双工设计 vs 随机发射
- ④ DSSS与Perlin关系
- ⑤ FEC vs 长M
- ⑥ FHSS方案
- ⑦ OCDM
- ⑧ 其他LPI建议
- ⑨ 完整接收流水线

### JS代码中的字符串
- `drawCorr()`: 标签文字 "模板"/"正确"/"误判"
- `drawWave()`: 坐标标签
- `drawCWScan()`: 轴标签
- `buildBadge()`: 调制类型名 ("线性Chirp", "Perlin多波形")
- `drawExplainer()`: 动画分步标签 ("模板 T_correct", "接收 rx", "乘积", "累积和")
- `togBtn()` 标签: "多波形", "CP循环前缀", "DSSS", "CW窄带", "脉冲干扰"

## 建议: 直接做 `_EN.html`

**理由**:
- 双语切换(Switch)方案需要: 提取所有字符串到字典、添加切换UI、所有动态JS也要读字典 → 改动量大、引入bug风险高
- 这个工具本质是个人技术验证/演示，用户要么看中文要么看英文，不需要实时切换
- 保留原 `chirp_v9_withExplain.html`(中文)，新文件 `chirp_v9_withExplain_EN.html`(英文)，两个独立文件干净利落
- 因为已经在读的是 `chirp_v9_withExplain_EN.html`，我可以直接改这个文件为英文
