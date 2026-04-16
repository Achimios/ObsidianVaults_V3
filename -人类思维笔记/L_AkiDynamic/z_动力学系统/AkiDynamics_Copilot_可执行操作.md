# AkiDynamics — 可执行操作篇

> *"不要问路怎么走，先把脚踏上去。第一步之后，世界会告诉你第二步在哪里。"*

#AkiLabs #动力学 #执行计划 #嵌入式 #控制论

---

## Phase 0：环境与基础（现在就能做）

### 0.1 补全信号工具包

在现有信号注入基础上，补入缺失的4类噪声模型：

```python
# 粉红噪声 (1/f) — 最接近真实电机/电源纹波
def pink_noise(n_samples, fs=2000):
    white = np.random.randn(n_samples)
    # Voss-McCartney算法或频域法
    freqs = np.fft.rfftfreq(n_samples, d=1/fs)
    freqs[0] = 1  # 避免除以0
    pink_psd = 1.0 / np.sqrt(freqs)
    pink_psd[0] = 0
    phases = np.random.uniform(0, 2*np.pi, len(pink_psd))
    spectrum = pink_psd * np.exp(1j * phases)
    return np.fft.irfft(spectrum, n=n_samples)

# 布朗噪声 / 随机游走 — 传感器零偏漂移
def brown_noise(n_samples):
    return np.cumsum(np.random.randn(n_samples)) * 0.01

# 脉冲噪声 — EMI/尖峰/撞击
def impulse_noise(n_samples, rate=0.001, amplitude=5.0):
    out = np.zeros(n_samples)
    mask = np.random.rand(n_samples) < rate
    out[mask] = amplitude * np.random.choice([-1, 1], mask.sum())
    return out
```

---

## Phase 1：AkiLabs内核（目标3~6个月）

### 1.1 统一刚度/阻尼在线辨识（从穿越机开始）

**任务**：在线估计机体等效刚度K和阻尼比ζ

**实现方法**（不需要高深数学，工程近似足够）：
1. 给一个阶跃油门指令（小幅度，不危险）
2. 记录姿态响应曲线的：超调量%、振荡周期T、收敛时间ts
3. 用标准二阶系统公式反推：

$$\zeta = -\frac{\ln(\text{超调\%}/100)}{\sqrt{\pi^2 + \ln^2(\text{超调\%}/100)}}$$

$$\omega_n = \frac{2\pi}{T_d\sqrt{1-\zeta^2}}$$

4. 更新系统参数表，用于调度PID上限

### 1.2 STM32振荡能量模块（C代码框架）

```c
#define WINDOW_100MS  200   // 2kHz × 0.1s

static float window[WINDOW_100MS];
static int   win_idx = 0;
static float E_osc   = 0.0f;
static float E_osc_prev = 0.0f;
static float y_prev  = 0.0f;
static float y_pprev = 0.0f;  // y[n-1]

// 每帧2kHz调用
void aki_calc_osc_energy(float y, float dt)
{
    // 1. 更新滑动窗口
    window[win_idx] = y;
    win_idx = (win_idx + 1) % WINDOW_100MS;

    // 2. 计算均值和震荡能量
    float mean = 0.0f;
    for (int i = 0; i < WINDOW_100MS; i++) mean += window[i];
    mean /= WINDOW_100MS;

    float e_sum = 0.0f;
    for (int i = 0; i < WINDOW_100MS; i++) {
        float d = window[i] - mean;
        e_sum += d * d;
    }
    E_osc_prev = E_osc;
    E_osc = e_sum / WINDOW_100MS;

    // 3. Teager能量算子 (需要 y, y_prev, y_next — 用y_pprev模拟滞后)
    float teager = y_prev * y_prev - y_pprev * y;
    y_pprev = y_prev;
    y_prev  = y;

    // 4. 内耗趋势预测 (100ms后)
    float dE_dt = (E_osc - E_osc_prev) / dt;
    float E_pred = E_osc + dE_dt * 0.1f;

    // 5. 决策
    if (E_pred > THRESH_DANGER || dE_dt > SLOPE_THRESH) {
        aki_reduce_pid_gain();
        aki_tighten_filter();
        aki_enable_notch();
    }
}
```

### 1.3 四档参数组实现（STM32）

```c
typedef struct {
    float lpf_fc;    // 主低通截止频率
    float d_lpf_fc;  // D项低通截止
    float p_scale;   // P增益倍率
    float d_scale;   // D增益倍率
    float i_freeze;  // 是否冻结积分
} AkiParamSet;

static const AkiParamSet PARAM_TABLE[4] = {
    {900.0f, 350.0f, 1.0f, 1.0f, 0},  // L0: 正常激进
    {550.0f, 200.0f, 0.7f, 0.6f, 0},  // L1: 预警
    {250.0f, 100.0f, 0.4f, 0.3f, 1},  // L2: 危险
    {120.0f,  50.0f, 0.2f, 0.1f, 1},  // L3: 紧急
};

// 平滑过渡 — 每帧向目标靠近15%
static AkiParamSet current_params;
void aki_smooth_params(int target_level)
{
    const AkiParamSet *target = &PARAM_TABLE[target_level];
    float alpha = 0.15f;
    current_params.lpf_fc   += alpha * (target->lpf_fc   - current_params.lpf_fc);
    current_params.d_lpf_fc += alpha * (target->d_lpf_fc - current_params.d_lpf_fc);
    current_params.p_scale  += alpha * (target->p_scale  - current_params.p_scale);
    current_params.d_scale  += alpha * (target->d_scale  - current_params.d_scale);
}
```

### 1.4 验证机型扩展顺序

1. **穿越机**（已有，验证动力学层基础）
2. **单轮自平衡**（验证柔性/低刚度控制策略）
3. **轮式差速小车**（验证基础运动学集成）
4. → 然后再进入AkiKinematic（多足/机械臂）

---

## Phase 2：AkiRouter通信层

### 2.1 Layer4 ↔ Layer3 特征包格式（最小化带宽）

```c
// STM32 → 树莓派，每20ms（50Hz）一包
typedef struct __attribute__((packed)) {
    uint32_t timestamp_ms;
    float    E_osc;           // 振荡能量
    float    teager_sum;      // 100ms Teager累积
    float    kurtosis;        // 峰度
    float    dshot_slope;     // Dshot油门上升沿斜率
    float    rpm_slope;       // RPM上升沿斜率
    float    lag_ms;          // 油门-RPM滞后时间
    float    vbat_droop;      // 电池压降速率
    float    pid_d_variance;  // D项方差
    uint8_t  risk_level;      // 当前风险等级0~3
    uint8_t  disturbance_type; // 0=平稳/1=振荡/2=冲击/3=共振
    uint8_t  checksum;
} AkiFeaturePacket;
```

### 2.2 树莓派接收端（Python骨架）

```python
import serial, struct, numpy as np
from sklearn.neural_network import MLPClassifier  # 或PyTorch

class AkiEdgeNode:
    def __init__(self, port='/dev/ttyS0', baud=115200):
        self.ser = serial.Serial(port, baud)
        self.history = []  # 特征序列缓冲
        self.model = self._load_model()
    
    def _load_model(self):
        # 轻量LSTM或MLP，预训练后加载
        pass
    
    def loop(self):
        while True:
            packet = self._recv_packet()
            if packet:
                self.history.append(self._to_feature_vec(packet))
                if len(self.history) > 100:  # 2秒历史
                    self.history.pop(0)
                
                # 推理
                result = self.model.predict([self.history[-20:]])
                params = self._result_to_params(result)
                
                # 下发参数给飞控（通过另一串口或MAVLink）
                self._send_params(params)
```

---

## Phase 3：高低PID能耗对比标准流程

用于AkiEnergy验证和最优参数数据库建立：

### 步骤

1. **静置校准**：飞机上桌，不动，记录3秒功率P₀和E_osc₀≈0，拟合系数k,b
2. **固定动作基准**：确定一个动作序列（如：悬停5s → 前进2m → 悬停5s）
3. **低PID跑一次**：记录全程E_osc、Epid、Pavg
4. **高PID跑一次**：同样动作，记录同样3指标
5. **计算综合分**，输入参数数据库
6. 重复3~4个PID组合，得出该机型最优参数区间

### 关键注意

- 大动作时E_osc会被有用运动淹没 → 滑动窗内先去均值再计算
- 用角速度/加速度作为y，不用角度（刚性运动影响小）
- 风/负载变化大时标注，不纳入对比数据库

---

## Phase 4：AkiClaw-Mini（STM32超轻量AI框架）

### 4.1 函数库预加载（行为原语）

```c
// AkiClaw-Mini 可调用行为函数列表
typedef void (*AkiBehavior)(void);

typedef struct {
    const char    *name;
    AkiBehavior    func;
} AkiBehaviorEntry;

// 注册表
static const AkiBehaviorEntry AKI_BEHAVIORS[] = {
    {"hover",          aki_hover},
    {"land",           aki_land},
    {"emergency_stop", aki_emergency_stop},
    {"safe_mode",      aki_safe_mode},
    {"stand",          aki_stand},    // 多足
    {"reset_joints",   aki_reset_joints},
    {NULL, NULL}
};

// 执行链 — 由上层Layer3/Layer2下发JSON或二进制序列
void aki_execute_chain(uint8_t *chain, int len) {
    for (int i = 0; i < len; i++) {
        AKI_BEHAVIORS[chain[i]].func();
    }
}
```

### 4.2 超浅层NN推理（8bit量化，STM32直接跑）

```c
// 8→16→8→3 MLP
// 权重和偏置由Python训练后转为int8数组写入Flash
int8_t W1[16][8], b1[16];
int8_t W2[8][16], b2[8];
int8_t W3[3][8],  b3[3];

void aki_nn_infer(float inputs[8], float outputs[3])
{
    // 量化输入
    int8_t x[8];
    for (int i = 0; i < 8; i++) x[i] = (int8_t)(inputs[i] * 127.0f);
    
    // 层1: 8→16, ReLU
    int8_t h1[16];
    for (int i = 0; i < 16; i++) {
        int32_t s = b1[i];
        for (int j = 0; j < 8; j++) s += W1[i][j] * x[j];
        h1[i] = (s > 0) ? (int8_t)MIN(s>>7, 127) : 0;
    }
    // 层2、3类似...
    // 反量化输出
    for (int i = 0; i < 3; i++) outputs[i] = (float)_h3[i] / 127.0f;
}
```

---

## Phase 6：先验注入系统

在飞机上天之前，用已知的硬件规格缩小高维搜索空间，给控制器一个有意义的初始增益估计：

### 6.1 先验信息来源

**桨叶参数 → 升力/扭矩梯度表**
| 输入 | 推导目标 |
|------|----------|
| 桨叶尺寸（直径/螺距）| RPM → 推力曲线斜率 |
| 叶数 | 扭矩系数（多叶更高扭矩，更平滑但惯量大）|
| 桨宽/形状（椭圆/梯形）| 升力分布均匀性 |

**电机参数 → 初始参考向量起点**
| 输入 | 推导目标 |
|------|----------|
| KV值 | 给定电压下最大RPM → 推力上限 |
| 电机尺寸（定子直径×高）| 扭矩上限（扭矩≈定子体积×磁通密度）|
| 机体重量 | 悬停油门估算（推力 ≈ 重力 × 1.5安全倍率）|

```python
def estimate_prior_gains(kv, vbat, prop_inch, prop_pitch, body_mass_g):
    """从硬件规格估算初始PID增益参考区间"""
    max_rpm = kv * vbat * 0.85   # 约85%效率
    hover_thrust_g = body_mass_g * 1.5 / 4  # 单电机悬停推力
    # 用桨推力公式：T ≈ 4.392399e-8 * rpm^2 * prop_inch^3.5 / sqrt(prop_pitch)
    import math
    hover_rpm = math.sqrt(hover_thrust_g * 1e-3 * 9.81 
                          / (4.392399e-8 * prop_inch**3.5 / math.sqrt(prop_pitch)))
    hover_throttle_ratio = hover_rpm / max_rpm
    return {
        "hover_throttle": hover_throttle_ratio,
        "p_gain_start": 0.04 * (1.0 / hover_throttle_ratio),
        "max_bandwidth_hz": max_rpm / 60 * 0.1  # 粗估机体带宽
    }
```

### 6.2 闭环监测手法

```c
// 电池电压直读（STM32 ADC，目标200Hz+）
float vbat_raw[VBAT_BUF_LEN];
float vbat_filtered;  // 一阶LPF，fc=5Hz

// 功耗监测 = 是否开始振荡
float power_mw = vbat_filtered * current_ma;  // 霍尔电流传感器
float power_integral += power_mw * dt;         // 积分功耗

// 电机温度（若有NTC） = 是否过载
float motor_temp_c;
if (motor_temp_c > TEMP_WARNING) {
    // 可能：小电机带大桨，或持续共振
    aki_reduce_pid_gain_soft(0.8f);
}
```

### 6.3 发散判断逻辑

**功耗曲线对比（档案建立后可用）：**
```python
# 对比低PID vs 高PID的积分功耗曲线
def check_energy_waste(pid_low_integral, pid_high_integral, action_result_ratio):
    """
    如果高PID积分功耗/低PID > 2x，但动作结果比 < 1.3x
    → 这段PID增量在浪费能量，不值得
    """
    energy_waste = pid_high_integral / pid_low_integral
    performance_gain = action_result_ratio
    return energy_waste / performance_gain  # >2.0 建议降PID
```

**MotorRPM vs DshotThrottle 升降沿对比（扭矩充足性检测）：**
```c
// 油门10→100，10采样点（2kHz下5ms），计算斜率
float throttle_slope = (throttle[9] - throttle[0]) / 9.0f;
float rpm_slope      = (rpm[9] - rpm[0]) / 9.0f;

// 转速递减导数 + 功率递增导数联合判断
float torque_adequacy = rpm_slope / (throttle_slope + 0.001f);
float power_rise = (power[9] - power[0]) / 9.0f;

if (torque_adequacy < TORQUE_THRESH && power_rise > POWER_THRESH) {
    // 桨叶过大或电机KV不匹配 → 告警
    aki_report_underpowered();
}
```

---

## Phase 7：动态增益统一化（TPA + 推力线性化合并）

### 7.1 物理本质

油门本质 = VBAT在当前VPWM占空比下的等效电压：

$$V_{eff} = V_{BAT} \times \text{duty\_cycle}$$

两种增益变化来源：
- **推力线性化**：VBAT变化 → 同油门产生不同推力 → 需要补偿
- **TPA（Throttle PID Attenuation）**：占空比高时PID增益过大会振荡 → 需要衰减

**关键洞察**：两者本质相同，都是对等效电压的响应。合并处理更简洁：

```c
// 统一增益补偿系数（只作用于PID，不作用于油门占空比）
float vbat_nominal = 3.7f * cell_count;               // 标称电压
float v_eff        = vbat_now * throttle_duty;         // 当前等效电压
float v_eff_hover  = vbat_nominal * hover_duty;        // 悬停参考点
float gain_scale   = v_eff_hover / (v_eff + 0.01f);   // 归一化补偿

// 应用到PID（不动油门输出）
p_gain_eff = p_gain_base * gain_scale * dynamic_scale;
d_gain_eff = d_gain_base * gain_scale * dynamic_scale;
```

### 7.2 负载变化后的全局增益推断

```python
def estimate_inertia_from_hover(hover_power_new, hover_power_ref, body_mass_ref_g):
    """
    负载变化后，用悬停功率比推断旋转惯量数量级 → 粗略全局增益调整
    注：增量负载位于质心附近 → 平均油门增加可补偿，旋转惯量基本不变，不需要调增益
    """
    mass_ratio = hover_power_new / hover_power_ref  # 质量比近似
    # 旋转惯量 ∝ 质量 × 特征长度^2（质心附近负载增量 ≈ 纯质量增加）
    inertia_scale = mass_ratio  # 粗估，若负载不在质心则需修正
    global_gain_adj = 1.0 / inertia_scale  # 惯量↑ → PID需要↑才能保持相同响应
    return global_gain_adj

# 特例：增量负载位于质心附近
# → 悬停功率增加，但旋转惯量变化极小
# → 仅增加平均油门即可，PID增益无需调整
```

---

## Phase 8：AkiLabs明日香（Asuka）个性层

声线绑定：`VOICE_ASUKA`（德日混合个性，AkiLabs诊断报告专用）

```python
# 在AkiEdgeNode中集成
def aki_asuka_report(diagnosis_result):
    """明日香诊断报告 — 直接、毒舌、但准确"""
    
    if diagnosis_result["issue"] == "small_motor_big_prop":
        speak("小电机配这么大桨？太不照顾机体了！先换桨再飞！")
    
    elif diagnosis_result["issue"] == "high_vibration":
        speak("Dummkopf！共振这么大，快先去加固机体！")
    
    elif diagnosis_result["issue"] == "underpowered"]:
        speak("扭矩不足，油门跟不上指令，这桨旋转惯量太大了吧？")
    
    elif diagnosis_result["issue"] == "near_divergence"]:
        speak("警告！振荡能量快到阈值了，峰度已经超7，自动收参中")
    
    elif diagnosis_result["status"] == "optimal"]:
        speak("参数在最优区间，系统稳定运行。继续！")
```

TTS调用方式参考 `.claude/skills/-yiti-tts/SKILL.md` 的 VOICE_ASUKA 声线定义。

### 阶段发布节点

| 节点 | 内容 | 目标 |
|------|------|------|
| v0.1 | AkiEnergy: 振荡能量+TEO+峰度 C库 | 打出名气，飞控社区验证 |
| v0.2 | 动态PID四档切换+平滑过渡 | 穿越机/轮式实测数据 |
| v0.3 | Dshot-RPM失配检测+动力根因 | 和BetaFlight/ArduPilot比 |
| v0.5 | STM32+树莓派双NN+特征传输 | 真正的边缘智能演示 |
| v0.8 | AkiRouter Layer 3+4 完整实现 | 自主飞行demo |
| v1.0 | AkiKinematic FK/IK + 四足适配 | 对标FAST Lab |

### README核心主张（写进第一行）

> AkiLabs: 泛用机器人动力学与控制论开放平台
> 从穿越机到人形步行，用统一的物理原语驱动所有运动形态。
> 不炸机。不浪费电。从底层开始，设计给真实世界。
