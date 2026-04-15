## 这是什么
PT1 vs 2-state LKF 陀螺滤波器交互式分析仪（多模块版）。
含 Notch、H(s)、DEQ、PID、TEO、Perlin 噪声、机架共振模拟、打杆注入、Mirror's Edge 双主题。

## 当前状态
✅ 模块化完成，7个模块，src/ 架构完整
✅ 图层独立 checkbox + solo 按钮（2列紧凑布局）
✅ 左侧面板：固定顶区（轴切换/PSD切换/图层显示/主题）+ 可滚参数区（PT1/LKF/Notch/共振/噪声/注入）
✅ 全轴 zoom/pan 保留（_saved_views 机制），Home 按钮重置
✅ 打杆注入 + 正弦注入（周期波_N：多峰/梳状/谐波 + Chirp + FM + ⇄范围拖拽）
✅ FocusSpin + PSD↔ASD切换 + 时域自适应抽帧 + 每图3悬浮按钮(|A/|R/-R)
✅ 自定义传递函数 H(s) 后端完整（bilinear s→z，5图全接入，状态标签）
✅ TEO 能量算子（可选信号源，PSD+时域）
✅ 差分表达式 DEQ 窗口（预设下拉+自由输入，状态标签3行：阶数/H(z)/y[n]，橙色 #e07830）
✅ Notch-last 信号链（源无Notch→滤波器→Notch最后一次）
✅ 级联 Bode（实线=总响应，虚线=TF自身，动态标签前缀）
✅ PID 独立通道（独立系数/信号源/颜色/5图曲线，TOP独立key）

## 跨 session 提醒
- 环境：系统级 Python，**运行方式：`cd src && py main.py`**
- 依赖：scipy / numpy / matplotlib / PyQt5
- 代码有 box-drawing 字符（U+2500 `─`）：用 replace_string_in_file 修改相关行会失败，需写 Python temp 脚本
- 时域混叠只是"显示混叠"：计算层 FS=2000 Hz 全精度，显示层抽帧；缩放后展示高频细节
- _spin(lo,hi,val,decs,suffix,step) 中 step=滚轮步长，singleStep=step/5（精调步）；_FocusDSpin._WHEEL_MULT=5
- 信号链：Raw → [PT1/LKF] → [H(s)/DEQ] → Notch(一次) → PID（PID 输入含源 Notch，输出不再叠加）

## 上次做了什么（session 3~4 精简）
- session 3: ASD 默认 + 悬浮按钮 + 多峰注入梳状/谐波 + TOP 按钮
- session 4: H(s) 后端完整(bilinear→5图) + TEO 能量算子 + 图例 note

## 上次做了什么（2026-04-16 session 5）
- DEQ 窗口完整实现（预设下拉+自由输入，状态标签3行）
- Notch-last 信号链修正
- 级联 Bode（实线=总级联，虚线=TF自身）
- PID 完全独立通道

## 上次做了什么（2026-04-20 session 6~7）
- PT1 Euler/Bilinear 切换（btn_pt1_bil）
- LKF 3模式→2模式：原始 H=[1,1]（有谐振峰）/ H=[1,0]（纯低通，默认）
  - DC归一化移除（KF DC恒=1，无偏估计数学性质）
  - 代码保留 obs_mode=1，UI 只留 0/2
- Riccati 150步 + 二分搜索 40步（同步到 PT1 -3dB）
- **info 标签全面升级**：PT1/LKF 显示 DEQ差分方程 + b,a系数 + peak gain
  - TF(H(s))区域新增 H(z) 显示
  - DC增益→peak gain（KF DC恒=1是数学性质，真正有意义的是谐振峰值）
- 打杆注入 box：objectName 隔离 + 主题色背景 + 橙色 checked 按钮
- 启动自动同步 LKF → PT1 截止频率
- Qt 字体警告抑制（`QT_LOGGING_RULES`）
- 幅频/相频 legend 右上角
- r_meas 5位小数、step 0.0005
- Stick mode toggle-off（同按钮取消）
- Subplot 高比 [2.0, 2.0, 1.4, 2.8, 2.8]

## 下一步（优先级）
1. 👆 ODE 连续时间仿真（新功能）
2. 👆 固定群延迟滤波器（FIR-based）
3. 极点零点图（新 subplot）
4. 阶跃响应图（新 subplot）
5. PID 默认参数调整 + 物理映射（5寸机架）
6. 修复旧 bug：|R toggle / |A auto-fit / 中键 pan 抖动 / Ctrl+Shift 修饰键

## 未来可能的大步骤
- 黑匣子 CSV 导入（Betaflight Blackbox .csv → 直接替代合成信号，做真实数据分析）
- 更多滤波器类型 Selector（Butterworth / BiQuad / 带通 作为并列模块挂入）
- 导出快照报告（一键截图全五轴 + 导出当前参数 JSON）
- 采样时间可配置化

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