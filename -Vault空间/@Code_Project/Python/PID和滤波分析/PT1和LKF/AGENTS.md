<magic> AkiLabs滤波分析仪上线... </magic>

# 局部指令层 — PT1 和 LKF 滤波器分析项目

## 专属规则
1. 物理量单位：陀螺角速度 **dps**（degrees per second），滤波器增益 **× 线性倍数**（不用 dB）
2. 新增功能前先在本目录查 `-CONTEXT.md`，避免重复造轮子
3. 用户级 Python 运行：`py "2_Copilot_交互式分析仪_PT1vsLKF.py"`
4. 修改 LKF 时先确认 Riccati 收敛（300+ 次迭代），不允许使用初始 P

## 目录文件说明
| 文件 | 来源 | 说明 |
|---|---|---|
| `1_豆包_PT1 vs 2-state LKF 波特图对比.py` | 豆包生成 | 原始静态 Bode 图，不修改 |
| `2_Copilot_交互式分析仪_PT1vsLKF.py` | Copilot | 交互式 GUI 分析仪（主力文件）|
