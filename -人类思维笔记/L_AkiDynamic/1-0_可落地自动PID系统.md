`<层级大纲>`

```
第四层，2kHz角速度闭环系统肯定不能跑NN，纯STM32飞控任务，还是用PID局部线性化。

第三层PID本身可以根据目前油门值和扰动200~2kHz变化（供电电压，TPA，Dynamic D-term, I-relax等），
但依然不是跑NN，而是根据PID动态规则参数(脚本)变化，或超轻量浅层NN，还是跑在STM32上。

第二層50hz才让机载电脑/树莓派跑NN去设定第三层规则，主要用于判断目前动力值，扰动状态，去选择对应脚本预设等。

第一层黑匆子分析 gyro vs setpoint，motorRPM vs dshotRPM，以及考虑电机温度、功率、飞行器尺寸和重量、
洗桨瞬间对应的gyro wave特征捕捉等，才在电脑上跑离线大模型，设定PID值，和PID动态规则参数(脚本)。
```

`</层级大纲>`

---

# AkiDynamic — 自动PID系统设计（控制论与动力学）
==泛用型🌒Moonshot探索，确定机型时还是人手调PID最快==
> 适用：四旋翄飞行器、AkiDynamic 机械狗、轮式/双足机器人控制层  
> 解耦说明：本文只关注**控制论与动力学**（PID结构、调参、优化）。智能化层（意图、感知、决策）记录在 [[2.0_可落地意图控制层]]  
> 来源整合：Lp范数理论 + Gemini神经PID方案 + MLflow整合方案

---

## 一、核心损失函数

PID 调参的唯一目标：**最低响应延迟 + 受扰不发散**

```
J(Kp, Ki, Kd) = w1TrackingError + w2||e(t)||_{H^{-s}} + w3D_Term_Heat
```

| 项 | 含义 | 替代传统 |
|---|---|---|
| `TrackingError` | setpoint vs gyro 积分误差 | ISE |
| `‖e(t)‖_{H^{-s}}` | **索伯列夫负范数** — 振荡/超调/高频噪声量 | 无（传统无此项） |
| `D_Term_Heat` | D项引起的电机发热（高频振荡代价） | 无 |

**时域近似（STM32 可跑）**：

~~`sobolev_neg = variance(gyro) + peak_to_peak(gyro) + max(abs(overshoot))`~~  
⚠️ 上行三项量纲不同（rad²/s² vs rad/s vs rad/s），直接相加无物理意义

```python
# 修正版：各项归一化后再加权
VAR_REF = 1.0   # rad²/s²，正常飞行方差参考值，需标定
PP_REF  = 5.0   # rad/s，正常飞行峰峰值参考值
OS_REF  = 2.0   # rad/s，允许最大超调参考值
sobolev_neg = variance(gyro)/VAR_REF + peak_to_peak(gyro)/PP_REF + max(abs(overshoot))/OS_REF
```

---

## 二、四层硬件架构  工具选型

### 第4层：2kHz 内环（STM32，零延迟）

```
✅ LKF 卡尔曼              陀螺去噪
✅ ESO/DOB 扰动观测器      实时估计洗桨/扰动
✅ PID 局部线性化           核心控制
✅ Teager 能量算子 (TEO)   亚微秒瞬态检测
✅ 李亚普诺夫简易判稳       防参数发散
✅ L1 硬约束               钳制 P/I/D 上下限
❌ 任何频域变换 / NN / 复杂优化
```

### 第3层：200Hz2kHz 动态PID（STM32）

```
✅ EKF                     估计油门/电压/载荷状态
✅ 索伯列夫负范数近似       振荡强度量化
✅ Gain Scheduling         TPA / Dynamic D / I-relax
✅ 二次规划 QP             平滑参数变化，防跳变
✅ 组 L1 约束              参数稀疏+平滑过渡
```

### 第2层：50Hz 机载（树莓派）

```
✅ VMD / EMD               分离洗桨/振动/噪声
✅ 小波包 WPT / HHT        时频特征
✅ 浅层NN 或 RBF网络       工况分类（重载/小桨/洗桨/强风）
✅ L1 稀疏降维             降低NN计算量
```

**机载NN输入/输出设计**：
```
输入:  [gyro_accel, throttle, volt_drop, motor_temp]
输出:  [Kp, Ki, Kd, TPA_offset]
架构:  MLP 2-3层 或 RBF网络（H7 飞控可跑）
```

### 第1层：离线PC（黑匣子全自动整定）

```
✅ 卡尔曼 RTS 平滑         还原真实 gyro/motor 信号
~~✅ HHT + 冯·卡门湍流谱~~  EMD 有模态混叠（Mode Mixing）缺陷
✅ VMD → Hilbert + 冯·卡门湍流谱  VMD 用能量约束分解，无混叠，数学更严格
✅ 索伯列夫正/负范数       响应速度 + 振荡发散评价
✅ L1 / ℓₚ 稀疏优化       筛选最简有效 PID 参数
✅ NSGA-II 多目标优化     延迟 + 超调 + 扰动敏感度同时最优
✅ 蒙特卡洛 + 波特图       极端工况鲁棒验证
✅ Sobol 灵敏度分析        找最敏感的 PID 参数
```

---

## 三、离线整定完整工作流

### Step 1  黑匣子数据清洗

```python
# process_bbl.py
# blackbox_decode 将 .bbl  CSV
# 卡尔曼 RTS 平滑去噪
# 识别"阶跃响应"段 vs "高频振荡"段
```

### Step 2  PyTorch / Optuna 黑盒寻优

```python
import mlflow, optuna

def objective(trial):
    Kp = trial.suggest_float("Kp", 20, 80)
    Kd = trial.suggest_float("Kd", 10, 60)
    TPA = trial.suggest_float("TPA", 0.3, 0.9)

    with mlflow.start_run():
        mlflow.log_params({"Kp": Kp, "Kd": Kd, "TPA": TPA})
        loss, d_heat = run_simulation(Kp, Kd, TPA)   # 仿真或黑匣子回放
        mlflow.log_metrics({"loss": loss, "d_heat": d_heat})
        mlflow.log_artifact("flight_log.csv")
    
    return loss + d_heat * 0.1

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=200)
```

**MLflow 部署（纯本地，无需服务器）**：
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

### Step 3  稳定性验证

```
波特图 / 奈奎斯特  闭环稳定性
李亚普诺夫  参数空间发散边界
蒙特卡洛  极端工况（低升力小桨/强风/洗桨）鲁棒性
```

### Step 4  V3 回流钩子

```python
# finalize_tuning.py
best = mlflow.search_runs(order_by=["metrics.loss ASC"]).iloc[0]

# 自动写入 V3 context
with open("pid_optimized_state.md", "w") as f:
    f.write(f"Kp={best['params.Kp']}, Kd={best['params.Kd']}")

# 追加硬规则到 learnings
with open("pid_traps.md", "a") as f:
    if float(best['params.Kd']) > 40:
        f.write("[RULE]: Kd > 40 causes D_Term_Heat > 90C. NEVER exceed.\n")
```

---

## 四、绝对红线

```
❌ ℓ₀ 范数：NP-hard，永远不用
❌ 曲波变换：仅适合二维图像
❌ 2kHz 内环跑 NN / 频域变换
❌ L 切换后做任何线性变换/旋转
❌ 各范数空间互相混用操作
❌ ℓₚ (0<p<1) 在线运行
❌ TensorFlow：太重不适合此工程，替代：PyTorch + Optuna
```

---

## 五、📌 待补充：速度与位置外环（未完成）

> 当前 1.0 只覆盖角速率内环（2kHz）和增益调度（200Hz-2kHz）。级联闭环全部层级待补入：

```
待补入：
位置外环（~50Hz，机载） → 输出速度设定值
速度外环（~100Hz嵌入）→ 输出姿态设定值
姿态角度环（~200Hz）→ 输出角速率设定值
角速率内环（✅ 2kHz）→ 已包含，详见二〆四层架构

适用场景过滤：
• 非重载非高速四轴、四足、轮式→ 速度位置闭环通常鲁棒性就够，无需优化
• 高速极速/重载/极限工况→ 必须细化外环
```
