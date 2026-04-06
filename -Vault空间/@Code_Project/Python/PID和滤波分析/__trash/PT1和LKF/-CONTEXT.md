## 这是什么
PT1 vs 2-state LKF 陀螺滤波器交互式分析仪。含 Notch 滤波、Perlin 噪声、机架共振模拟、群延迟可视化。

## 跨 session 提醒
- ⚠️ 已迁移到多模块 → `../01_滤波交互式分析仪/src/`
- 此文件夹保留作历史参考，旧单文件不再主动维护
- 新项目运行：`cd 01_滤波交互式分析仪/src && py main.py`
- 依赖：scipy / numpy / matplotlib / PyQt5（用户级安装 `pip install --user`）
- LKF 传递函数已修正（Riccati 稳态 K0=K[0,0], K1=K[1,0]）
- 群延迟 y 轴本身就是线性 ms，x 轴跟频率切换按钮走

## 当前状态
✅ v3 特性集大幅扩充，语法 CLEAN，测试通过，PSD 已含打杆效果

## 上次做了什么
2026-04-08：
- 打杆曲线控制：CubicSpline + 起止锚点 + ✚/✖/⇄ 模式 + 清空 + 80ms 拖拽防抖
- 删除区域 1/200 视图宽，锚点免疫
- GroupBox: 打杆曲线控制 + 更新全局状态按钮
- 机架共振 A/B 各加启用 checkbox（chk_r1/chk_r2）
- 共振分布参数 内置 chk_res_dist；全局噪声参数 加"启用噪声"（仅屏蔽白噪声+Perlin）
- Mirror's Edge 双主题（深/亮 一键切换，Qt palette 同步）—— _DARK/_LIGHT 类变量
- PSD 现在 welch(signal_ws)，反映打杆实际频谱；↺ 按钮 lambda 修复

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
