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
| `constants.py` | 采样参数 + 双主题颜色字典 |
| `dsp.py` | 纯数学：PT1/LKF/Notch/Perlin/共振 |
| `ui_mixin.py` | 左侧参数面板 UI 构建 |
| `interact_mixin.py` | 打杆曲线画布交互 |
| `draw_mixin.py` | matplotlib 绘图 + 轴切换 + LKF 同步 |
| `theme_mixin.py` | Mirror's Edge 主题切换 + toolbar 图标 |
| `main.py` | 入口：FilterAnalyzer 类 + main() |

## >v< 注释码表（关键参数搜索标记）

搜索方式：`grep -r ">v<" src/`

| 标记 | 含义 | 文件:位置 |
|---|---|---|
| `>v<⚡步进规则` | 滚轮 = 5× 精调步，方向键 = 精调步，改此处须同步注释 | ui_mixin.py `_WHEEL_MULT` |
| `>v<🎯LKF默认r` | r_meas=0.012 → -3dB≈100Hz≈PT1默认fc；与 spinbox 下限联动 | ui_mixin.py `r_meas` |
| `>v<🎯LKF同步下限` | sync 按钮 clip 下限必须与 r_meas spinbox 下限一致 | draw_mixin.py `_sync_lkf_to_pt1` |
| `>v<📊PSD_ASD切换` | ASD↔PSD 切换逻辑 + Y 轴 ×0.1/×10 自动规则 | draw_mixin.py `_toggle_psd_amp` |
| `>v<📊PSD默认Y范围` | PSD 初始 Y=[0,2000]，ASD 切换后=[0,200]；Home 重置也用此值 | main.py `_saved_views[3]` |
| `>v<🕐抽帧公式` | dec=ceil(t_span×FS/6000)，缩放后 dec→1 消除显示混叠 | draw_mixin.py `_do_update` 时域段 |

## 新增功能落点
- **新滤波算法** → `dsp.py` + `draw_mixin.py`（_do_update 调用）
- **新 UI 控件** → `ui_mixin.py`（_build_ui）+ `main.py`（__init__ 若需新状态变量）
- **新画布交互** → `interact_mixin.py`
- **主题颜色调整** → `constants.py` 仅改此处
