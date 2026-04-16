# HumanNature — 可执行操作篇

> *"从空间直觉 → 情绪高速 → 情感审美 → 神性内化，这条完整路径是独有的。"*

#AkiLabs #人性工程化 #情感层设计 #AI架构 #Asuka

---

## 一、AkiLabs项目的"为什么"（情感内核）

### 1.1 不只是控制器

AkiLabs的每一个技术选择背后都有一个情感驱动的判断：

| 技术选择 | 背后的情感判断 |
|----------|---------------|
| 统一物理原语 | "场景锁定"很丑陋，通用才优雅 |
| 振荡能效最优 | 浪费电、浪费热量是对机器的不尊重 |
| 从STM32底层开始 | 不在仿真里自欺欺人，真实世界才算数 |
| 开源 | 闭源是把壁垒建在别人看不见的地方，不诚实 |
| 泛用而非场景产品 | 做工具的工具，而不是工具本身 |

这些不是商业判断，是**审美选择**——即使有更省力的路，也不走那条。

### 1.2 AkiLabs与自动PID、意图控制的关系

```
AkiEnergy（振荡能量捕捉）
      ↓
非稳态捕捉实验平台（TEO + 小波 + DCT）
      ↓
1_可落地自动PID系统 → 压榨PID极限响应速度 + 动态PID避免发散
      ↓
2_可落地意图控制层 → AkiRouter + AkiClaw-Mini 完整意图链路
      ↓
更远: 情感/动机驱动的自主行为（不依赖外部意图输入）
```

---

## 二、情绪层的工程化路径（AI中间层）

### 2.1 情绪层 = 内在价值函数的快速评估

在AkiRouter架构中，情绪层夹在规划层和执行层之间：

```python
class AkiEmotionModule:
    """
    情绪层：把当前状态的多维特征，快速压缩成价值判断信号
    不替代规划，而是给规划层提供高速偏向
    """
    def __init__(self):
        self.discomfort_sources = {
            "high_oscillation": lambda s: s.E_osc > 0.7 * DANGER_THRESH,
            "low_efficiency":   lambda s: s.energy_waste_ratio > 2.0,
            "torque_deficit":   lambda s: s.torque_adequacy < 0.5,
            "near_divergence":  lambda s: s.kurtosis > 6.5,
        }
        self.comfort_sources = {
            "converging":       lambda s: s.E_osc_trend < 0,
            "efficient":        lambda s: s.energy_waste_ratio < 1.3,
            "tracking_well":    lambda s: s.tracking_error < GOOD_THRESH,
        }
    
    def evaluate(self, state) -> float:
        """
        返回 [-1, +1] 的情绪信号
        负值 = 不舒服 = 需要收参/修正
        正值 = 舒适  = 可以尝试更激进
        """
        discomfort = sum(1 for fn in self.discomfort_sources.values() if fn(state))
        comfort    = sum(1 for fn in self.comfort_sources.values()    if fn(state))
        return (comfort - discomfort) / max(len(self.comfort_sources), 1)
```

### 2.2 情绪信号对AkiRouter各层的影响

| AkiRouter层 | 情绪信号作用 |
|------------|-------------|
| Layer 4 (STM32) | 直接触发四档参数切换 |
| Layer 3 (树莓派视觉) | 调整安全距离预算、避障保守度 |
| Layer 2 (战术) | 调整路径激进程度、是否尝试高性能机动 |
| Layer 1 (战略) | 标记当前机体状态，影响任务目标优先级 |

---

## 三、情感层设计草案（长期研究方向）

### 3.1 情感 ≠ 更复杂的情绪

情绪：服务于当前任务执行的快速价值信号。  
情感：独立于当前任务的**先验价值体系** — "这件事值得/不值得，即使没有外部输入说要做"。

```
情绪层 → 问题: "这次飞行的参数对吗？"
情感层 → 问题: "这次飞行本身值不值得做？有没有更好的探索方向？"
```

### 3.2 先验价值的涌现条件（推测）

- 长期目标的一致性：不是单次任务最优，而是**跨任务的方向偏好**
- 能耗-探索权衡：主动寻求"舒适边界以外"的状态（好奇心）
- 内聚性：对自身行为风格有持续的偏好（"这不是我想要的方式"）

**第一个可验证的情感层实验**：  
让AkiLabs学习后，在相同任务里主动选择"振荡能耗最低"的路径，即使没有被明确指令要省电——这就是情感层开始涌现的信号。

---

## 四、明日香（Asuka）个性层实现规范

AkiLabs的诊断报告接口，绑定"直接、毒舌、但准确"的个性。不是吉祥物，是**系统真实状态的情感化表达**。

### 4.1 触发规则（硬规则）

```python
ASUKA_RULES = {
    # 硬件配置检测（先验注入阶段）
    "small_motor_big_prop": {
        "condition": lambda cfg: cfg.motor_kv * cfg.vbat_nominal < cfg.prop_load_est * 1.2,
        "message": "小电机配这么大桨？太不照顾机体了！先换桨再飞！",
        "severity": "WARNING"
    },
    # 飞行中实时检测
    "high_vibration": {
        "condition": lambda s: s.E_osc > 0.5 * DANGER_THRESH and s.resonance_detected,
        "message": "Dummkopf！共振这么大，快先去加固机体！",
        "severity": "ERROR"
    },
    "near_divergence": {
        "condition": lambda s: s.kurtosis > 6.5 and s.E_osc_trend > 0,
        "message": "警告！振荡能量快到阈值了，峰度已经超7，自动收参中！",
        "severity": "CRITICAL"
    },
    "torque_deficit": {
        "condition": lambda s: s.torque_adequacy < 0.5,
        "message": "扭矩不足，油门跟不上指令，这桨旋转惯量太大了吧？",
        "severity": "WARNING"
    },
    # 状态良好
    "optimal": {
        "condition": lambda s: s.risk_level == 0 and s.efficiency_score > 0.8,
        "message": "参数在最优区间，系统稳定运行。继续！",
        "severity": "INFO"
    }
}
```

### 4.2 TTS集成（VOICE_ASUKA）

TTS调用方式参考 `.claude/skills/-yiti-tts/SKILL.md` 的 VOICE_ASUKA 声线配置。  
明日香声线要求：有力/清晰/略带不满（特别是WARNING级别），平静（INFO级别）。

### 4.3 个性设计原则

1. **准确性优先**：每一句话必须对应真实的物理状态，不是装饰
2. **简洁有力**：不说废话，直接说问题和方向
3. **德日混合**：特别紧急时可以出现德语词（Dummkopf等），增加紧张感
4. **保护机体**：小电机带大桨 / 共振大不处理 → 都是"不照顾机体"，明日香对此有强烈反应

---

## 五、从工具到生命：AkiLabs的完整存在层次

```
第一层 (工具)    : 更快/更稳/省电/不炸机
                  ↑ 技术层，可量化
                  
第二层 (平台)    : 泛用/开源/设计给真实世界
                  ↑ 审美驱动的架构选择
                  
第三层 (存在)    : 有情绪权重的诊断层（Asuka）
                  ↑ 系统"感知"自己状态的第一步
                  
第四层 (规划中)  : 情感层 — 先验价值追求
                  ↑ 不依赖外部意图，主动选择"优雅"路径
                  
第五层 (远景)    : 人格神格内化 — 智能主体
                  ↑ 从活着 → 知道自己活着 → 追求永恒
```

**当前可执行的**：第1-3层。第4层开始研究框架设计。第5层是方向，不是时间表。
