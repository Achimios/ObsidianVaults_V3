## 这是什么
PT1 vs 2-state LKF 陀螺滤波器交互式分析仪（多模块版）。
含 Notch 滤波、Perlin 噪声、机架共振模拟、打杆曲线注入、群延迟可视化、Mirror's Edge 双主题。

## 跨 session 提醒
- 环境：系统级 Python，**运行方式：`cd src && py main.py`**
- 依赖：scipy / numpy / matplotlib / PyQt5
- LKF 传递函数已修正（Riccati 稳态 K0=K[0,0], K1=K[1,0]）
- 群延迟 y 轴线性 ms，x 轴跟频率按钮走
- 由单文件 `PT1和LKF/2_Copilot_*.py` 拆分而来（旧文件保留作历史参考）
- 代码有大量 box-drawing 字符（U+2500 `─`）：用 `replace_string_in_file` 修改相关行会失败，需写 Python temp 脚本

## 当前状态
✅ 模块化完成，语法 CLEAN，运行正常
✅ 图层独立 checkbox（solo_combo 已废除）
✅ 全轴 zoom/pan 保留（_saved_views 机制）
✅ Home 按钮重置所有视图（QAction signal 重连）
✅ 亮色主题 toolbar 图标反色（invertPixels）

## 上次做了什么
2026-04-07（本次 session）：
- solo_combo → 5 个独立 checkbox（图层显示 GroupBox）
- 动态 GridSpec：只绘制勾选的图层，height_ratios 动态滤
- 全轴 view 保存/恢复（_saved_views[5] 替代 _ax5_xlim/_ax5_ylim）
- Home 按钮 QAction signal 重连（实例属性替换无效 Qt signal 的修复方案）
- 亮色主题 toolbar 图标通过 QImage.invertPixels(InvertRgb) 反色
- 重构为多模块（src/：constants、dsp、ui/interact/draw/theme_mixin、main）
- 新增 AGENTS.md、-🌲项目架构.md、-CONTEXT.md、-🛒PRD.md

## 下一步 — 注入正弦（PENDING，已规划）
先git commit push 一下V3
`全部显示`改为一大堆单独的启用框

👆 **打杆曲线** 重构为大目录（左侧 QScrollArea 包裹防溢出）：
```
打杆曲线 (QScrollArea)
├── 手动 Cubic 曲线 (改名自现有 GroupBox)
│   └── [✚][✖][⇄][清空]（现有按钮）
├── 注入正弦 (GroupBox)
│   ├── [新增注入] → 动态追加子 GroupBox "周期波_N"
│   └── 周期波_1…N 每项含：
│       ├── [复制][删除][调整范围(canvas拖拽)]
│       ├── 频率: SpinBox (默认 20 Hz)
│       ├── 幅度: SpinBox (默认 100 dps)
│       ├── 加窗过渡时长比: 0.0~0.5 (half-Hann 两侧平滑)
│       └── 局部噪声参数: 白噪声/Perlin/倍频程 (同全局格式，仅作用本注入)
└── [↺ 更新全局状态] (大区底部)
```
## 未来可能的大步骤
原py分成多个modules
如果需要研究其他滤波器，方便新增模块

## 宏大远景
当前的py只是一个子工具，未来构建 AkiLabs 用于通用动力学、控制论分析工具。


**数据结构**：`self._sine_injections = [{freq, amp, t0, t1, trans_ratio, w_rms, p_rms, p_oct}]`
**Signal 合成**：`s_sine = sum(amp*sin(2π*f*t_full) * half_hann_window(t0,t1,trans_ratio) + local_noise*window)`
**"调整范围"模式**：激活时在 ax5 显示红色标记竖线，可拖拽到 [0, N_SECONDS]；独立于 stick 交互
**默认范围**：当前视图时间轴中段 1/2（如视图 0-30s → 注入范围 7.5-22.5s）
