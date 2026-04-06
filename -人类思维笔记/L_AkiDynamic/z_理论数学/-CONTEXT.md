## 这是什么
`z_理论数学/` — 穿越机陀螺滤波器数学分析区。存放 Bode 分析代码和理论笔记（Lp 范数、PT1 vs LKF）。

## 跨 session 提醒
- 环境：系统级 Python（无 venv），用 `py "filename.py"` 运行
- scipy / numpy / matplotlib / PyQt5 均已用户级安装（`pip install --user`）
- 文件名前缀规范：`数字_来源_描述.py`（如 `1_豆包_...`、`2_Copilot_...`）

## 当前状态
🔄 进行中：`2_Copilot_交互式分析仪_PT1vsLKF.py` v2 开发

## 上次做了什么
2026-04-06：分析仪 v2 完成
- 修正 LKF 传递函数推导（Riccati 稳态 + 正确 z^{-n} 系数顺序）
- 加入：Notch A/B（含启用开关）、时域波形（30s）、群延迟图、线性/对数轴切换按钮、dB/线性幅度切换、共振增益改为 × 线性倍数、白噪声+Perlin 参数可调、噪声缓存+防抖计时器

## 下一步
👆 运行 v2，测试 Notch 对抗共振效果；考虑增加群延迟数值注释（100Hz/500Hz 延迟 ms 标注）
