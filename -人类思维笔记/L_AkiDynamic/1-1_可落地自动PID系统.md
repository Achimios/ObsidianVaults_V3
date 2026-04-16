# 可落地自动PID系统 1.1 — 整合更新版

> 基于1.0版，整合AkiDynamic系列研究成果。新增：振荡能量代价、先验注入、动态增益统一、Dshot-RPM失配检测。  
> 不修改原文件。与AkiDynamics_Copilot系列重复的实现细节用引用表示。

#AkiLabs #自动PID #控制论 #黑匣子整定 #嵌入式实时

---

## 核心变化（相对1.0版）

| 变化点 | 1.0版 | 1.1版 |
|--------|-------|-------|
| PID代价函数 | TrackingError + 索伯列夫负范数近似 + D热量 | **新增：振荡能量$E_{osc}$项（物理意义更清晰）**|
| 发散检测 | 李亚普诺夫简易判稳 | **新增：峰度>7 + $E_{osc}$上升趋势联合判断（更早预警）**|
| 参数起点 | 无 | **新增：先验注入（桨叶/电机规格→PID起点，缩小搜索空间）**|
| 增益补偿 | TPA独立 | **统一：TPA + 推力线性化 = $V_{eff}$补偿（见第五节）**|
| 内环监测工具 | TEO（已有）| **补充：Dshot-RPM失配检测作为外环执行器健康指标**|

---

## 一、核心损失函数（更新）

```
J(Kp, Ki, Kd) = w1·TrackingError + w2·E_osc + w3·D_Term_Heat
```

**三项的物理意义：**

| 项 | 物理含义 | 计算方式 | 量纲归一化 |
|---|---|---|---|
| `TrackingError` | setpoint与gyro的积分误差 | $\int|e(t)|^2 dt$（ISE）| 除以$E_{ref}$（参考标称值）|
| `E_osc` | **振荡内耗**：系统在额外震动上浪费的能量 | $\frac{1}{N}\sum(y-\bar{y})^2$ | 除以$E_{osc,hover}$（悬停校准）|
| `D_Term_Heat` | D项引入高频振荡→电机铜损发热 | D项输出方差 × 热系数 | 除以$H_{ref}$（允许最大热量）|

**振荡能量的优势**（相比原版索伯列夫负范数近似）：
- 物理意义直观（就是额外振动的RMS能量）
- 可直接通过一次静置校准对齐到功率读数（相关系数>0.85）
- 在STM32 2kHz下实时可计算，不需要离线

```python
# 合并评分函数（用于Optuna黑盒寻优）
def pid_score(tracking_error, e_osc, d_heat,
              E_ref=1.0, E_osc_hover=0.01, H_ref=1.0,
              w1=1.0, w2=0.5, w3=0.2):
    return (w1 * tracking_error / E_ref +
            w2 * e_osc / E_osc_hover +
            w3 * d_heat / H_ref)
```

---

## 二、先验注入：搜索空间初始化

在黑盒寻优之前，用硬件规格给出有意义的初始增益范围—— **缩小高维搜索空间，避免在物理不可行区浪费试验次数**。

```python
def get_prior_search_space(kv, vbat, prop_inch, prop_pitch, body_mass_g):
    """
    根据硬件规格估算PID合理搜索区间
    输出：Optuna suggest_float 的范围参数
    """
    import math
    max_rpm = kv * vbat * 0.85
    hover_thrust_g = body_mass_g * 1.5 / 4  # 单电机
    # Thrust formula: T ≈ 4.392399e-8 * rpm^2 * D_inch^3.5 / sqrt(pitch)
    hover_rpm = math.sqrt(hover_thrust_g * 1e-3 * 9.81 /
                          (4.392399e-8 * prop_inch**3.5 / math.sqrt(prop_pitch)))
    hover_ratio = hover_rpm / max_rpm  # 悬停油门比
    
    # 惯量估计决定PID上限
    # 轻桨(<5inch)悬停ratio<0.4: 系统响应快，PID上限高
    # 重桨(>8inch)悬停ratio>0.6: 惯量大，PID偏低
    p_max = 80 * (1.0 - hover_ratio * 0.5)  # 粗估P上限
    
    return {
        "Kp": (p_max * 0.3, p_max),
        "Kd": (p_max * 0.1, p_max * 0.6),
        "TPA": (0.3, 0.85),
        "hover_ratio": hover_ratio  # 供后续增益补偿使用
    }
```

---

## 三、四层硬件架构（更新）

### 第4层：2kHz 内环（STM32）

```
✅ LKF 卡尔曼              陀螺去噪
✅ TEO (Teager能量算子)    零延迟脉冲检测（O(1)/帧，3点缓存）
✅ 峰度（Kurtosis）         振荡发散预警（>7=危险区间）
✅ 振荡能量 E_osc           内耗量化，代价函数实时项
✅ ESO/DOB 扰动观测器       实时估计洗桨/扰动
✅ PID 局部线性化            核心控制
✅ 四档参数自动切换          基于峰度+E_osc触发
✅ 李亚普诺夫简易判稳        防参数发散
❌ 任何频域变换 / NN
```

**发散预警（更新为双指标）：**

```c
// 原版：仅李亚普诺夫
// 新版：峰度 + E_osc上升趋势 联合判断
int aki_check_divergence(float kurtosis, float e_osc, float e_osc_prev, float dt)
{
    float de_dt = (e_osc - e_osc_prev) / dt;
    float e_pred = e_osc + de_dt * 0.1f;  // 预测100ms后的E_osc
    
    if (kurtosis > 7.0f || e_pred > E_OSC_DANGER) return 2;  // 紧急降档
    if (kurtosis > 4.0f && de_dt > 0)              return 1;  // 预警
    return 0;  // 正常
}
```

### 第3层：200Hz~2kHz 动态PID（STM32）

```
✅ Dshot-RPM失配检测       执行器健康监测（四分类根因）
✅ VBAT实时监测(200Hz+)   电压补偿前馈
✅ 统一增益补偿            V_eff = VBAT × duty（统一TPA+推力线性化）
✅ EKF                    估计油门/电压/载荷状态
✅ 参数四档切换+平滑过渡    0.15α每帧向目标靠近
```

**Dshot-RPM失配四分类（新增）：**

| 类型 | 表征 | 根因 | 对PID的影响 |
|------|------|------|------------|
| 扭矩不足 | 油门↑快/RPM↑慢 | 桨过大/KV不匹配/VBAT低 | 需先验补偿，不能靠加P |
| 高惯量 | 油门↓快/RPM↓慢 | 转动惯量大，低阻尼 | 振荡风险高，需保守D |
| 共振激发 | Dshot小抖/RPM大纹波 | 机体共振+PID正反馈 | 需要陷波Notch |
| 过度滤波 | Dshot抖/RPM几乎不动 | 电调内部滤波太强 | 控制延迟大，PID难追 |

### 第2层：50Hz 机载（树莓派）

```
✅ VMD + Hilbert           时频特征，无EMD模态混叠
✅ 浅层NN / RBF网络         工况分类（重载/小桨/洗桨/强风）
✅ 振荡能量序列分析          中长期趋势特征
✅ Dshot-RPM特征包接收      (从STM32每20ms一包)
```

**特征包格式（STM32→树莓派）：**

```c
typedef struct __attribute__((packed)) {
    uint32_t timestamp_ms;
    float    E_osc;           // 振荡能量（AkiEnergy）
    float    teager_sum;      // 100ms Teager累积
    float    kurtosis;        // 峰度
    float    dshot_slope;     // Dshot油门上升沿斜率
    float    rpm_slope;       // RPM上升沿斜率
    float    lag_ms;          // 油门-RPM滞后时间
    float    vbat_droop;      // 电池压降速率
    float    pid_d_variance;  // D项方差
    uint8_t  risk_level;      // 0~3
    uint8_t  disturbance_type; // 0-4
} AkiFeaturePacket;           // 每20ms(50Hz)发送一次
```

### 第1层：离线PC（黑匣子全自动整定，更新）

```
✅ 卡尔曼 RTS 平滑         还原真实信号
✅ VMD → Hilbert + 冯·卡门湍流谱  时频分析
✅ 先验注入                缩小搜索空间（新增）
✅ 振荡能量代价函数         替代原版E_osc项（更清晰）
✅ Optuna + MLflow         黑盒寻优+实验跟踪
✅ NSGA-II 多目标优化      延迟 + 超调 + 内耗同时最优
✅ 蒙特卡洛 + 波特图       鲁棒性验证
```

---

## 四、离线整定完整工作流（更新）

### Step 0  先验注入（新增）

```python
# 在寻优前调用
space = get_prior_search_space(kv=2306, vbat=14.8, prop_inch=5, prop_pitch=4.3, body_mass_g=200)

def objective(trial):
    Kp  = trial.suggest_float("Kp",  *space["Kp"])
    Kd  = trial.suggest_float("Kd",  *space["Kd"])
    TPA = trial.suggest_float("TPA", *space["TPA"])
    # ...
```

### Step 1  黑匣子数据清洗

```python
# blackbox_decode .bbl → CSV
# 卡尔曼 RTS 平滑去噪
# 识别"阶跃响应"段 vs "高频振荡"段
# 计算E_osc校准系数（静置3秒标定）
```

### Step 2  Optuna + MLflow 寻优

```python
import mlflow, optuna

def objective(trial):
    Kp, Kd, TPA = ...
    with mlflow.start_run():
        mlflow.log_params({"Kp": Kp, "Kd": Kd, "TPA": TPA})
        tracking_err, e_osc, d_heat = run_simulation_or_replay(Kp, Kd, TPA)
        score = pid_score(tracking_err, e_osc, d_heat)
        mlflow.log_metrics({"score": score, "e_osc": e_osc, "d_heat": d_heat})
    return score

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=300)
```

### Step 3  验证 & 参数写入飞控

```python
# 最优参数组写入四档参数表
# 生成增益调度脚本（JSON格式供STM32读取）
# 记录实验结论到 pid_traps.md
```

---

## 五、统一增益补偿（TPA + 推力线性化）

**原理**（替代原1.0版TPA节）：

$$V_{eff} = V_{BAT} \times \text{duty\_cycle}$$

TPA（高油门降增益）和推力线性化（低VBAT补偿）本质都是对$V_{eff}$的响应，可以统一：

```c
// 统一增益比（只作用于PID，不作用于油门占空比）
float v_eff_hover = vbat_nominal * hover_ratio;   // 先验注入的悬停参考点
float v_eff_now   = vbat_now * throttle_duty;
float gain_scale  = v_eff_hover / (v_eff_now + 0.01f);

p_eff = Kp_base * gain_scale * dynamic_scale;    // dynamic_scale = 四档参数
d_eff = Kd_base * gain_scale * dynamic_scale;
```

**注意**：不对油门→推力映射本身补偿，保留飞手对低电量的感知。

---

## 六、绝对红线（继承1.0版）

```
❌ ℓ₀ 范数：NP-hard，永远不用
❌ 2kHz 内环跑 NN / 频域变换
❌ 各范数/量纲不统一直接相加（原1.0版索伯列夫近似存在此问题，已在1.1修正）
❌ TensorFlow：太重，替代：PyTorch + Optuna
❌ HHT（EMD有模态混叠缺陷）→ 改用 VMD→Hilbert
```

---

## 七、与AkiDynamic系列的分工

| 本文聚焦 | AkiDynamic系列详述 |
|---------|-------------------|
| 整定工作流（黑匣子→Optuna→写入飞控）| TEO/峰度/振荡能量算法实现 |
| 先验注入参数估算 | 先验注入C代码（Phase 6）|
| Dshot-RPM四分类（诊断用）| Dshot-RPM失配检测C代码 |
| 统一增益补偿原理 | 动态增益统一C实现（Phase 7）|
| 离线PC工具链（Optuna/MLflow）| 在线实时层（STM32四档切换）|

---

## 八、待补充（继承1.0版待办）

- [ ] 位置/速度/姿态角度外环的串级PID代价函数
- [ ] 多电机混用时的Mixer层静态补偿系数
- [ ] 洗桨（prop wash）自动识别与参数覆盖（P↑D↓，详见[[0.1？_自动PID与滤波分析_更新版]]）
- [ ] Yaw bounce自动补偿逻辑
- [ ] AHRS动态权重与碰撞处理（详见0.1_更新版草稿）
