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
✅ 地层独立 checkbox（solo_combo 已废除）
✅ 全轴 zoom/pan 保留（_saved_views 机制）
✅ Home 按鈕重置所有视图（QAction signal 重连）
✅ 亮色主题 toolbar 图标反色（invertPixels）
✅ 图层 solo 按鈕（_toggle_solo）
✅ 打杆按鈕 ↔ toolbar 互斥锁（_deactivate_toolbar + QTimer double-deactivate）
✅ 启动时无预选 ✚（_stick_mode=None, canvas click 有守卫）

## 上次做了什么
2026-04-07（本次 session）：
- 修复开机 ✚ 预选问题（移除 setChecked(True)，_stick_mode=None）
- 修复 toolbar 互斥：新建 `_deactivate_toolbar()` 直连 `_actions['zoom']`，_do_update() 前后各调一次
- debug 方法：Start-Process + RedirectStandardOutput 捕获 print 输出


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
原py分成多个modules(done)
如果需要研究其他滤波器，方便新增模块

## 宏大远景
当前的py只是一个子工具，未来构建 AkiLabs 用于通用动力学、控制论分析工具。


**数据结构**：`self._sine_injections = [{freq, amp, t0, t1, trans_ratio, w_rms, p_rms, p_oct}]`
**Signal 合成**：`s_sine = sum(amp*sin(2π*f*t_full) * half_hann_window(t0,t1,trans_ratio) + local_noise*window)`
**"调整范围"模式**：激活时在 ax5 显示红色标记竖线，可拖拽到 [0, N_SECONDS]；独立于 stick 交互
**默认范围**：当前视图时间轴中段 1/2（如视图 0-30s → 注入范围 7.5-22.5s）
