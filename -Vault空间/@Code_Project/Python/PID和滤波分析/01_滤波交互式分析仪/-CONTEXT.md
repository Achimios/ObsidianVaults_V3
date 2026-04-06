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
✅ 亮色主题默认启动，toolbar 图标反色
✅ 拖拽期间轻量更新（_do_update_drag）：仅 stick+sine 曲线，松开后全量刷新
✅ adj 模式纯最近邻拾取（无锚点 zone 问题）
✅ 打杆注入 + 正弦注入（周期波_N，动态新增/复制/删除，t0/t1 spinbox）
✅ _compute_sine_total：half-Hann 窗 + 局部噪声（白噪音/Perlin）
✅ PT1 / LKF 启用 checkbox（可独立关闭）
✅ FocusSpin：滚轮仅在 focused 时修改参数（防误触）

## 上次做了什么
2026-04-07 session 2：
- 拖拽轻量刷新（_drag_timer 30ms → _do_update_drag）
- 左侧 QScrollArea 包裹面板，最小窗口 500×500
- adj 模式改纯最近邻（anchor zone 被用户点附近吸住的 bug 修复）
- 正弦注入完整 UI + 后端信号合成（`_compute_sine_total`）
- PT1/LKF 启用 checkbox，所有频域/时域/PSD 绘图对 use_pt1/use_lkf 响应
- 默认亮色主题，PSD 默认显示范围 [0,100]，时域 hspace 缩小至 0.28

## 下一步（优先级）
1. **⇄ 范围按钮 canvas 交互** — 激活后在 ax5 拖拽红色标记线设置 t0/t1（当前仅互斥锁无交互）
2. **正弦注入缓存优化** — 加 sine_key 缓存，仅当参数变更时重新计算（类似 noise_key）
3. **抗混叠 AAF 选项**（低优先级）— 可选 500Hz LP 前置滤波器，用于降采样模拟




## 未来可能的大步骤
如果需要研究其他滤波器，方便新增模块（用 chk_xx_en 开关控制）

## 宏大远景
当前的py只是一个子工具，未来构建 AkiLabs 用于通用动力学、控制论分析工具。
