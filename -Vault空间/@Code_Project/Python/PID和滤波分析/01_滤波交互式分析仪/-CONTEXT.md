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
✅ 图层独立 checkbox + solo 按钮（2列紧凑布局）
✅ 左侧面板：固定顶区（轴切换/PSD切换/图层显示/主题）+ 可滚参数区（PT1/LKF/Notch/共振/噪声/注入）
✅ 全轴 zoom/pan 保留（_saved_views 机制），Home 按钮重置
✅ 打杆注入 + 正弦注入（周期波_N：t起/t中/t止、f起/f中/f止/幅度/FM频偏/过渡区/局部Perlin&白噪声）
✅ _compute_sine_total：half-Hann 窗 + param-key 缓存 + Chirp(f起≠f止) + FM(Perlin LFO)
✅ ⇄ 范围 canvas 交互：3区(左=拖t起/中=拖整体/右=拖t止)，ax5 蓝色3段可视化
✅ FocusSpin：滚轮=5×精调步(stepBy(5))，方向键=1×精调步(singleStep=step/5)；wheelEvent e.accept()阻止冒泡
✅ PSD ↔ ASD 切换按钮（√P → dps/√Hz；ylabel 联动）；PSD 显示范围 0-1000 Hz
✅ 时域自适应抽帧：dec=ceil(t_span*FS/6000)，缩放后 dec→1 消除显示混叠，标题显示当前有效显示频率
✅ 手动 Cubic 曲线启用 checkbox（chk_stick_en）
✅ 自定义传递函数 H(s) UI 骨架（后端 pending）

## 跨 session 提醒
- 环境：系统级 Python，**运行方式：`cd src && py main.py`**
- 依赖：scipy / numpy / matplotlib / PyQt5
- 代码有 box-drawing 字符（U+2500 `─`）：用 replace_string_in_file 修改相关行会失败，需写 Python temp 脚本
- 时域混叠只是"显示混叠"：计算层 FS=2000 Hz 全精度，显示层抽帧；缩放后展示高频细节
- _spin(lo,hi,val,decs,suffix,step) 中 step=滚轮步长，singleStep=step/5（精调步）；_FocusDSpin._WHEEL_MULT=5

## 上次做了什么（2026-04-08 session 3）
- 频谱图启动默认 ASD（range 0~200），_psd_amp_mode=True，切换时 PSD=ASD×10 ✓
- 每图左侧 3 个悬浮按钮（|A=Y适应开关 / |R=Y重置 / -R=X重置）
  - QWidget child of canvas，draw_event 后按 ax.get_position() 自动定位
  - 各图独立状态（_y_auto[5]），chk_show=False 时对应组自动隐藏
  - _default_views[5] 记录各图默认坐标范围
  - 亮色/暗色主题切换时按钮颜色同步更新
- 多峰注入（每个注入波项独立）：
  - N峰 spinbox(1~8) + 梳/谐 切换按钮 + Δf 间距（谐波模式时隐藏）
  - 梳状：f0, f0+Δf, ..., f0+(N-1)Δf；谐波：1×2×3×...N×f0
  - 幅度 amp/N 平分，各峰 FM seed 独立（+pk×17 偏移）
  - cache key 包含新字段，复制时完整传递含显隐状态
- git: af6f09b(ASD默认+3按钮), ecd2469(亮色按钮), 4cb61be+77eb13e(多峰), e290e22(TOP按钮)

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


## 多峰方案汇总，按应用场景整理，4个方案：

| 方案        | UI                                       | 适用场景                 | 复杂度            |
| --------- | ---------------------------------------- | -------------------- | -------------- |
| A 梳状N峰    | 加 N (1~8) + Δf spinbox，峰频 f₀, f₀+Δf, ... | 无人机桨叶振动（等间距谐波），机架模态  | ☆☆ 简单<br>(已完成) |
| B 谐波列     | 加 N (1~8)，自动生成 1×, 2×, ..., N×f₀         | 旋转机械（伺服、电机），信号失真分析   | ☆☆ 简单<br>(已完成) |
| C 迷你子列表   | GroupBox 内 N 行，每行一个 f + amp spinbox      | 轮式载具路面振动（任意多频混合），最灵活 | ☆☆☆☆ 复杂        |
| D 梳状+谐波混合 | 一个 checkbox 选"等距梳状/谐波比"模式                | 无人机+电动载具通用           | ☆☆☆ 中等         |

##### 针对具体用途：
- 无人机 / 穿越机：方案 A（桨频+谐波间距均匀）或方案 B（叶尖失速谐波）
- 机械狗腿部：方案 A（步态周期谐波）
- 轮式载具：方案 C（路面不规则，多任意频率）
- 通用测试台：方案 D（两种模式切换）