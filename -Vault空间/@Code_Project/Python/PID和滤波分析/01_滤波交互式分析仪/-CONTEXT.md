## 这是什么
PT1 vs 2-state LKF 陀螺滤波器交互式分析仪（多模块版）。
含 Notch 滤波、Perlin 噪声、机架共振模拟、打杆曲线注入、群延迟可视化、Mirror's Edge 双主题。
## 跨 session 提醒
- 环境：系统级 Python，**运行方式：`cd src && py main.py`**
- 依赖：scipy / numpy / matplotlib / PyQt5
- 代码有 box-drawing 字符（U+2500 `─`）：用 `replace_string_in_file` 修改相关行会失败，需写 Python temp 脚本
- temp 脚本位置：放在项目目录内，**不要**丢到 V3 根目录！

## 当前状态
✅ 模块化完成，7个模块，src/ 架构完整
✅ 图层独立 checkbox + solo 按钮 + 左侧 QScrollArea（可滚动）
✅ 全轴 zoom/pan 保留（_saved_views 机制），Home 按钮重置
✅ 亮色主题默认启动，toolbar 图标反色，toolbar 在画布下方
✅ 拖拽期间轻量更新（_do_update_drag）：stick 拖拽只更新打杆曲线；正弦范围拖拽只显示注入波
✅ adj 模式纯最近邻拾取（无锚点 zone 问题）
✅ 打杆注入 + 正弦注入（周期波_N：t起/t中/t止、f起/f止/幅度/过渡区/FM频偏/白噪音/Perlin、复制/删除/启用复选框）
✅ _compute_sine_total：half-Hann 窗 + 局部噪声 + param-key 缓存 + Chirp(f起≠f止) + FM(Perlin LFO)
✅ ⇄ 范围 canvas 交互：3区(左=拖t起/中=拖整体/右=拖t止)，ax5 蓝色3段可视化
✅ PT1 / LKF 启用 checkbox（可独立关闭）
✅ FocusSpin：滚轮仅在 focused 时修改参数（防误触）
✅ 手动 Cubic 曲线启用 checkbox（chk_stick_en，关闭则 s_stick=0）
✅ 自定义传递函数 H(s) UI 骨架（GroupBox + num/den QLineEdit，后端 pending）

## 上次做了什么（2026-04-08 session）
- toolbar 移至画布下方
- 全局白噪音/Perlin min=0，倍频程上限 9999（彻底无限制）
- sine alpha 降至 0.30
- Chirp：每注入波增加 f止 spinbox，f起≠f止时使用 chirp 相位合成
- FM：每注入波增加 FM频偏 spinbox，>0 时用 Perlin LFO 积分调制相位
- chk_stick_en：手动 Cubic 曲线启用复选框，关闭则 s_stick 清零（_do_update + _do_update_drag 均已gated）
- H(s) UI 骨架：GroupBox、chk_hs_en、hs_num/hs_den QLineEdit（disabled，后端 pending）
- git: a5b0b18（range canvas/toolbar）, cb04b59（noise/alpha tweak）, b810141（chirp/FM/chk_stick/H(s)）

## 下一步（优先级）
1. 👆 H(s) 后端：`scipy.signal.bilinear(b_s, a_s, fs)` 解析 num/den，接入 _do_update 频响 + 时域

## 未来可能的大步骤
- 黑匣子 CSV 导入（Betaflight Blackbox .csv → 直接替代合成信号，做真实数据分析）
- H(s) 后端完工（用户自定义任意传递函数，接入所有图层）
- 更多滤波器类型 Selector（Butterworth / BiQuad / 带通 作为并列模块挂入）
- 导出快照报告（一键截图全五轴 + 导出当前参数 JSON）

## 宏大远景
这个 py 只是第一把手术刀。最终目标是 **AkiLabs 动力学与控制论分析平台**：

| 阶段 | 目标 |
|---|---|
| 当前（Phase 1）| 陀螺滤波分析仪，手工合成信号，本地 GUI |
| Phase 2 | 真实黑匣子数据接入，实测 PSD 驱动 Notch 设计 |
| Phase 3 | 模块插件化 — 任意滤波器模块像"义体器官"一样热插拔 |
| Phase 4 | 控制律仿真 — PID / Cascade / Feedforward 闭环仿真与频域分析 |
| Phase 5 | AkiLabs Web UI — 云端协作，跨平台，供无人机调参社区使用 |

核心设计铁律：**每个滤波算法 = 一个器官；信号流 = 义体神经网；GUI = 驾驶舱仪表盘**。
