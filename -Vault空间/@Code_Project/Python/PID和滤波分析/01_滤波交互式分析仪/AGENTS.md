<magic> AkiLabs滤波分析仪上线... </magic>

# 局部指令层 — 滤波交互式分析仪

## 专属规则（继承自 PT1和LKF）
1. 物理量单位：陀螺角速度 **dps**，滤波器增益 **× 线性倍数**（不用 dB）
2. LKF 修改时先确认 Riccati 收敛（3000 次迭代），不允许使用初始 P
3. 运行：`cd src && py main.py`

## 架构规则
- **Mixin 模式**：每个 `.py` 对应一个功能层，方法通过 `FilterAnalyzer` 多重继承合并
- **禁止跨层直接调用**：ui_mixin 禁止直接调用 dsp.py 里的函数；通过 _do_update 触发
- **参数分离**：主题颜色/采样常数全在 `constants.py`，代码文件不硬编码

## 文件职责
| 文件 | 职责 |
|---|---|
| `constants.py` | 采样参数 + 双主题颜色字典（PT1/LKF/H(s)/DEQ/PID/TEO 7色）|
| `dsp.py` | 纯数学：PT1/LKF/Notch/Perlin/共振/bilinear(custom_tf_to_digital)/TEO/find_3db/diff_eq_str/poly_str/poly_z_str |
| `ui_mixin.py` | 左侧参数面板 UI 构建（含 H(s)/DEQ/PID/TEO GroupBox + 信号源选择）|
| `interact_mixin.py` | 打杆曲线画布交互 |
| `draw_mixin.py` | matplotlib 5图绘制 + 6通道滤波(PT1/LKF/H(s)/DEQ/PID/TEO) + Notch-last级联 + cascade Bode |
| `theme_mixin.py` | Mirror's Edge 主题切换 + toolbar 图标反色 |
| `main.py` | 入口：FilterAnalyzer 类 + main() |


## 新增功能落点
- **新滤波算法** → `dsp.py` + `draw_mixin.py`（_do_update 调用）
- **新 UI 控件** → `ui_mixin.py`（_build_ui）+ `main.py`（__init__ 若需新状态变量）
- **新画布交互** → `interact_mixin.py`
- **主题颜色调整** → `constants.py` 仅改此处

# -🛒PRD.md
主要用于 构建自己的项目
写明需求，设计理念，功能模块，用户场景，交互流程，界面设计，技术选型，数据结构设计，接口设计，测试方案等内容。

# -📇索引码表.md
特殊的、重要的注释以指定格式写在代码里，并记录于此文件。看码表，grep对应名称，就能找到对应段落。

# -🌲项目架构.md
解读巨型代码项目时，把架构写入此文件，便于人和AI获得概览