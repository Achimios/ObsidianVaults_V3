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
- 差分表达式 DEQ 窗口完整实现：预设下拉（PT1/LKF/Notch/自定义TF/TEO）+ 自由输入 y[n]=…/H(z) 系数
  - DEQ 状态标签 3 行：阶数/-3dB(+预设设计fc)、H(z) 表达式(poly_z_str)、差分方程(diff_eq_str)
  - DEQ 颜色橙色 #e07830(dark)/#b06020(light)
  - dsp.py: `poly_z_str()` 格式化 z⁻ⁿ 多项式为可读字符串
- Notch-last 信号链修正：
  - 信号链：Raw → [PT1/LKF] → [H(s)/DEQ] → Notch(最后应用一次) → PID
  - 源 combo 移除 "+N" 后缀（H(s)/DEQ/TEO 全部）
  - 新增 `out_pt1_td`/`out_lkf_td`（无 Notch 的完整信号）供级联使用
- 级联频率响应（Cascade Bode）：
  - 源≠未过滤时，Bode 实线=总级联响应(源×滤波器×Hn)，虚线=TF 自身
  - 动态标签前缀如 "PT1→H(s)+N"
- PID 控制器完全独立：
  - 不再覆盖 H(s) 的 num/den，独立系数计算 `custom_tf_to_digital([kd,kp,ki],[τd,1,0],fs)`
  - 独立信号源 combo（未滤波/PT1/LKF），默认 PT1
  - PID 输入含 Notch(PT1_n/LKF_n)，输出不再叠加 Notch
  - 5 图全接入：幅频/相频/群延迟/PSD/时域，独立颜色 C_PID=#e0a040
  - TOP 按钮独立 'pid' key，移除 hs↔pid 同步

## 下一步（优先级）
1. 👆 PID 默认参数调整（P=45 I=60 D=36，主乘数=1.0，D-LP=125Hz，500g 起飞重量）
2. PID 物理映射：质量→旋转惯量→力→传递函数（5寸机架，20% 悬停油门）
3. 阶跃响应图（新 subplot）
4. 极点零点图（新 subplot）
5. 窗口默认 1920×1080 + 新图默认隐藏

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