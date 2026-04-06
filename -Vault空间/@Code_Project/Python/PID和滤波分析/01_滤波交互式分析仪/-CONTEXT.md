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
✅ 拖拽期间轻量更新（_do_update_drag）：stick 拖拽只更新打杆曲线；正弦范围拖拽只显示注入波
✅ adj 模式纯最近邻拾取（无锚点 zone 问题）
✅ 打杆注入 + 正弦注入（周期波_N：t起/t中/t止、频率/幅度/过渡区、白噪音/Perlin、复制/删除/启用复选框）
✅ _compute_sine_total：half-Hann 窗 + 局部噪声 + param-key 缓存
✅ ⇄ 范围 canvas 交互：3区(左=拖t起/中=拖整体/右=拖t止)，ax5 蓝色3段可视化
✅ PT1 / LKF 启用 checkbox（可独立关闭）
✅ FocusSpin：滚轮仅在 focused 时修改参数（防误触）

## 上次做了什么（2026-04-07 session 3）
- t中 spinbox（t起/t止 双向联动，平移范围时保持时长锁定）
- sine_key param 缓存（stickdrag时 sine 不重算，含 chk_en 状态）
- ⇄ 范围 canvas 3区交互（3-zone 点击，_do_update_drag 仅显示注入波）
- 各期 ax5 低饱和蓝色 axvspan 范围可视化（激活时3段，非激活时细条）
- 每注入波"启用"复选框（取消则从合成信号移除，缓存key含此状态）
- 正弦注入线 lw=0.5, alpha=0.50（更细更淡）
- 范围⇄画布工具互斥锁（_toggle_sine_range 调用 _deactivate_toolbar）
- _toggle_sine_range 末尾加 _schedule() 修复"点击按钮不刷新范围"的 bug
- git: a5b0b18

## 下一步（优先级）
1. （无明确 next-step，等待指挥官指示）



## 未来可能的大步骤
如果需要研究其他滤波器，方便新增模块（用 chk_xx_en 开关控制）

## 宏大远景
当前的py只是一个子工具，未来构建 AkiLabs 用于通用动力学、控制论分析工具。
