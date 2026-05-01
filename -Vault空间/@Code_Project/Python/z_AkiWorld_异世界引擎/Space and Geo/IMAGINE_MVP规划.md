#游戏设计 #∂WORLD #MVP #Godot #UE5 #开发规划

> 2026-04-28 · 老维 × Akimos  
> ∂WORLD MVP 路线图：从 Python Demo 到 2D 可玩版本，再到 3D UE5

---

# ∂WORLD MVP 规划

![[PIC_mvp_roadmap_2d_godot_to_3d_ue5_pipeline_diagram_minimalist_flowchart.png]]

> *"只造一件事，把它造到极致。然后再造下一件。"*  
> — SuperHot 的教训

---

## 目录

**[[#引擎选型决策]]**  
**[[#2D MVP — Godot 4]]**  
- [[#设计哲学：2D中的w维度]] · [[#阶段规划]] · [[#Phase 0]] · [[#Phase 1]] · [[#Phase 2]] · [[#Phase 3]] · [[#Phase 4]] · [[#Phase 5]]  
- [[#Godot项目结构]] · [[#数学核心移植]] · [[#2D Shader方案]]

**[[#3D版本 — UE5]]**  
- [[#设计哲学：3D+w=4D]] · [[#阶段规划3D]] · [[#美术策略]]  
- [[#UE5技术路线]] · [[#从Godot到UE5的迁移路径]]

**[[#垂直切片目标]]**

---

---

# 引擎选型决策

## 2D：Godot 4 ✅

**核心理由**：

```
1. GDScript ≈ Python
   → 脑子不需要切换语言，proto_sdf4d.py 的逻辑可以直接翻译

2. 2D 渲染器是原生实现（不是 3D 的降维包装）
   → CanvasItem Shader 可以直接写 w 轴效果
   → 像素坐标直接对应数学坐标，无中间层

3. 艺术风格完美匹配
   → Hades：2D顶视角 + 动态光效 ✅ Godot 4 实现的典型案例
   → Gris：自定义 Shader 大量使用 ✅
   → Hyper Light Drifter：像素 + 粒子 ✅

4. 免费开源，无 Runtime Fee 风险

5. 可以写 GDExtension（C++）接驳数学计算
   → 如果 GDScript 算不动 SDF，直接 C++ 扩展，接口不变
```

**Pygame 的位置**：留在 Labs/ 做数学实验，不作为游戏引擎。

## 3D：UE5 ✅（已定）

```
优势：
- Nanite + Lumen 让简单场景也有顶级光效
- Niagara 粒子系统 = 数学场的最佳可视化工具
- HLSL 完全自定义 → 4D SDF Ray Marching 着色器
- Blueprint 可以快速原型，C++ 接管性能关键路径
- 材质系统适合 Hades/Control 风格的混合美术
```

---

---

# 2D MVP — Godot 4

---

## 设计哲学：2D中的w维度

```
3D游戏里：x, y, z = 玩家感知空间，w = 隐藏的第4维
2D游戏里：x, y = 玩家感知平面，w = 隐藏的第3维（深度/相位）

这不是降格，这是降维打击：
w轴在2D里可以做成"另一层世界"的感觉
就像《超级马里奥兄弟》的星星无敌 vs 《Celeste》的镜像世界
只是这里的"另一层"有严格的数学定义
```

**具体的 w 轴体验**：
- `w=0`：正常世界（玩家默认所在层）
- `w=δ`：世界开始"溶解"，拓扑结构可见（SDF 等值线透出来）
- `w=max`：纯数学空间，只看到 SDF 场和同调结构

**类比参考**：《灵魂超能力》的精神层 + 《Manifold Garden》的空间逻辑

---

## 阶段规划

```
Phase 0 (1周)    → Godot 4 环境 + 项目结构 + 数学核心移植
Phase 1 (2周)    → 玩家移动 + w轴切换 + 基础物理
Phase 2 (3周)    → 章I 群论战斗原型（对称检测 + 群操作武器）
Phase 3 (2周)    → HUD：持续同调条码 + w轴深度计
Phase 4 (2周)    → ε AI伴侣接入（LLM API 或本地规则）
Phase 5 (3周)    → 垂直切片：废弃工厂1号房间 + Boss Σ-0 可战斗

总计：约 13 周 → 3个月出可展示 Demo
```

---

## Phase 0 — 基础设施（第1周）

### Godot 4 项目结构

```
∂world_2d/
├── project.godot
├── src/
│   ├── math_core/          ← SDF + 群论 + 同调计算
│   │   ├── sdf_shapes.gd
│   │   ├── group_theory.gd
│   │   └── homology_scanner.gd
│   ├── player/
│   │   ├── player.gd
│   │   ├── w_axis_controller.gd
│   │   └── weapon_system.gd
│   ├── enemies/
│   │   ├── base_enemy.gd
│   │   └── sigma_0_boss.gd
│   ├── world/
│   │   ├── room_manager.gd
│   │   └── math_environment.gd
│   ├── ui/
│   │   ├── barcode_hud.gd
│   │   └── w_depth_meter.gd
│   └── epsilon/
│       └── epsilon_ai.gd
├── scenes/
│   ├── player.tscn
│   ├── rooms/
│   │   ├── factory_room_01.tscn
│   │   └── boss_arena.tscn
│   └── ui/
│       └── hud.tscn
├── shaders/
│   ├── sdf_visualizer.gdshader
│   ├── w_axis_effect.gdshader
│   ├── homology_overlay.gdshader
│   └── symmetry_highlight.gdshader
├── assets/
│   ├── sprites/            ← AI生成图像
│   ├── music/
│   └── sfx/
└── labs/                   ← 从 Labs/ 迁移的原型
    └── proto_sdf4d.py
```

### 数学核心移植（GDScript）

```gdscript
# math_core/sdf_shapes.gd
# 把 proto_sdf4d.py 的 SDF4D 类翻译过来

class_name SDF4D
extends RefCounted

# 4D 超球 SDF
static func hypersphere(p: Vector4, center: Vector4, radius: float) -> float:
    return (p - center).length() - radius

# 4D 超立方 SDF
static func hypercube(p: Vector4, center: Vector4, half: float) -> float:
    var q: Vector4 = Vector4(
        abs(p.x - center.x) - half,
        abs(p.y - center.y) - half,
        abs(p.z - center.z) - half,
        abs(p.w - center.w) - half
    )
    var outer = Vector4(max(q.x, 0), max(q.y, 0), max(q.z, 0), max(q.w, 0))
    return outer.length() + min(max(q.x, max(q.y, max(q.z, q.w))), 0.0)

# CSG: 并集 / 交集 / 差集
static func sdf_union(d1: float, d2: float) -> float:
    return min(d1, d2)

static func sdf_intersect(d1: float, d2: float) -> float:
    return max(d1, d2)

static func sdf_subtract(d1: float, d2: float) -> float:
    return max(d1, -d2)

static func smooth_union(d1: float, d2: float, k: float) -> float:
    var h := clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0)
    return lerp(d2, d1, h) - k * h * (1.0 - h)
```

```gdscript
# math_core/group_theory.gd
# 章I 群论核心：对称检测

class_name GroupTheory
extends RefCounted

# D4 群的8个操作（正方形对称群）
# 用于 Boss Σ-0 的弱点系统
enum D4Op { ID, R90, R180, R270, FLIP_H, FLIP_V, FLIP_D1, FLIP_D2 }

static func apply_d4(op: D4Op, point: Vector2) -> Vector2:
    match op:
        D4Op.ID:      return point
        D4Op.R90:     return Vector2(-point.y, point.x)
        D4Op.R180:    return Vector2(-point.x, -point.y)
        D4Op.R270:    return Vector2(point.y, -point.x)
        D4Op.FLIP_H:  return Vector2(-point.x, point.y)
        D4Op.FLIP_V:  return Vector2(point.x, -point.y)
        D4Op.FLIP_D1: return Vector2(point.y, point.x)
        D4Op.FLIP_D2: return Vector2(-point.y, -point.x)
        _:            return point

# 检测当前攻击是否命中 Boss 的对称弱点
static func hits_symmetry_weakness(
        attack_dir: Vector2,
        boss_symmetry_op: D4Op,
        tolerance: float = 0.1) -> bool:
    var transformed := apply_d4(boss_symmetry_op, attack_dir.normalized())
    # 命中条件：变换后方向与原方向反向（穿越对称轴）
    return attack_dir.normalized().dot(transformed) < -1.0 + tolerance
```

---

## Phase 1 — 玩家核心（第2-3周）

### w轴切换系统

```gdscript
# player/w_axis_controller.gd

class_name WAxisController
extends Node

signal w_changed(new_w: float)

@export var w_speed: float = 2.0
@export var w_min: float = 0.0
@export var w_max: float = 5.0
@export var w_snap_points: Array[float] = [0.0, 1.0, 2.0, 3.0]

var current_w: float = 0.0
var w_energy: float = 100.0      # 消耗资源，不能无限滑动

func shift_w(delta: float) -> void:
    if w_energy <= 0.0 and delta != 0.0:
        # ε的台词："能量不足——你需要找到同调锚点。"
        return
    
    var prev_w := current_w
    current_w = clamp(current_w + delta * w_speed, w_min, w_max)
    w_energy -= abs(delta) * 10.0
    
    if not is_equal_approx(current_w, prev_w):
        emit_signal("w_changed", current_w)

func snap_to_nearest() -> void:
    """按 Tab 键：吸附到最近的 w_snap_point（同调稳定点）"""
    var nearest := w_snap_points[0]
    var min_dist := abs(current_w - nearest)
    for p in w_snap_points:
        var d := abs(current_w - p)
        if d < min_dist:
            min_dist = d
            nearest = p
    current_w = nearest
    emit_signal("w_changed", current_w)
```

### 按键映射（建议）

| 操作 | 按键 |
|---|---|
| 移动 | WASD |
| w轴增加 | Q |
| w轴减少 | E |
| 吸附同调点 | Tab |
| 攻击 | 鼠标左键 |
| 群操作切换 | 1/2/3/4 |
| 同调扫描 | F |
| ε对话 | 空格 |

---

## Phase 2 — 群论战斗原型（第4-6周）

### 核心战斗循环

```
玩家感知流:
1. 敌人/Boss 周围有"对称光晕"→ 可读取它的当前对称群
2. 玩家切换武器（群操作）：生成元攻击 / 逆元攻击 / 轨道攻击
3. 命中对称弱点 → 对称破缺 → 大伤害
4. Boss 切换对称态（D4 → Z4 → Z2 → trivial）→ 血量归零
```

**武器系统（章Ⅰ）**：

| 武器 | 群操作 | 视觉效果 |
|---|---|---|
| **生成元枪** | 单次群操作 | 子弹沿对称轴旋转 |
| **轨道炮** | 生成整条轨道（连击） | 子弹在轨道上同时出现 |
| **稳定子护盾** | 保留对称子群 | 护盾只挡对称方向的攻击 |
| **对称破缺炸弹** | 打破所有对称 | AoE，混沌效果 |

---

## Phase 3 — 数学 HUD（第7-8周）

### 持续同调条码 HUD

```
┌─ HUD 左下角 ─────────────────────┐
│  TOPOLOGY SCANNER                │
│  H₀ ████░░░░████░░░░ ← 连通分量  │
│  H₁ ░░████████░░░░░ ← 环形洞    │
│  w  ━━━━━━●━━━━━━━━  2.3        │
│  ε  [能量 ████████░░]            │
└───────────────────────────────────┘
```

**Godot 实现**：`Control` 节点 + 自定义 `_draw()` + GDScript 计算简化条码（不需要完整持续同调，用切片连通分量数近似即可）

### w轴深度可视化 Shader

```glsl
// shaders/w_axis_effect.gdshader
shader_type canvas_item;

uniform float w_current : hint_range(0.0, 5.0) = 0.0;
uniform float w_max : hint_range(1.0, 5.0) = 5.0;
uniform sampler2D sdf_texture;  // 预烘焙的 SDF 纹理

void fragment() {
    vec4 base_color = texture(TEXTURE, UV);
    
    // w 轴相位：产生"穿越维度"的波纹效果
    float phase = w_current / w_max;
    float wave = sin(UV.x * 20.0 + w_current * 3.14159) * 0.5 + 0.5;
    
    // 边缘发光：w 越大，SDF 等值线越明显
    float sdf_val = texture(sdf_texture, UV).r;
    float edge = smoothstep(0.45, 0.5, abs(sdf_val - 0.5)) * phase;
    
    // 颜色混合：基础色 + w 轴辉光
    vec3 glow_color = mix(vec3(0.0, 0.8, 1.0), vec3(1.0, 0.3, 0.8), phase);
    COLOR = vec4(mix(base_color.rgb, glow_color, edge * 0.7), base_color.a);
}
```

---

## Phase 4 — ε 接入（第9-10周）

**两种方案**（选其一或混用）：

### 方案A：规则引擎（轻量，不需要联网）

```gdscript
# epsilon/epsilon_ai.gd

class_name EpsilonAI
extends Node

# 触发条件 → 台词池
const DIALOGUES = {
    "player_w_shift_first": [
        "你感受到了吗？那不是空间——那是拓扑在说话。",
        "w轴移动一单位，你的H₁条码发生了什么？",
    ],
    "boss_symmetry_detected": [
        "它的对称群是 D₄。生成元是90度旋转和反射。",
        "找到它的稳定子群——那就是弱点的数学位置。",
    ],
    "player_low_energy": [
        "维度跃迁消耗了太多能量。找到同调锚点来恢复。",
    ],
    "homology_h1_detected": [
        "H₁ 条码出现了一条长寿命条码。那里有个洞——可以穿过去。",
    ],
}

func trigger(event: String) -> String:
    if event in DIALOGUES:
        var pool: Array = DIALOGUES[event]
        return pool[randi() % pool.size()]
    return ""
```

### 方案B：LLM API（完整ε人格）

```gdscript
# epsilon/epsilon_llm.gd
# 调用本地 Ollama 或 OpenAI API

func ask_epsilon(context: String) -> String:
    var system_prompt := """
    你是 ε，一个居住在数学拓扑空间里的 AI 实体。
    你的说话风格：简短、精准、偶尔诗意。绝不废话。
    当前游戏状态：{context}
    """.format({"context": context})
    
    # HTTP 请求到 localhost:11434/api/generate (Ollama)
    # 或 api.openai.com
    pass
```

**建议**：Phase 4 先用方案A快速完成，后续可无缝切换方案B。

---

## Phase 5 — 垂直切片（第11-13周）

**目标**：1个完整可展示的 Demo，包含：

```
✅ 完整的废弃工厂 Room 1（MODULAR_ENTRY）
✅ 3 种敌人：R-01 模节 / R-02 循环守卫 / R-03 阶哨兵
✅ Boss Σ-0（D₄晶体，3阶段）
✅ w轴切换：至少 3 个 snap point
✅ HUD：H₀/H₁ 条码 + w深度计
✅ ε 台词：至少 15 条（规则引擎）
✅ BGM：1首（参考 Hans Zimmer 风格，Suno/Udio AI生成）
✅ 美术：AI生成概念图 + 简单程序生成几何
```

---

## 2D Shader 方案总结

| Shader | 用途 | 优先级 |
|---|---|---|
| `sdf_visualizer` | 在世界空间显示 SDF 等值线（调试 + 美学） | Phase 1 |
| `w_axis_effect` | w轴移动时的波纹/辉光效果 | Phase 1 |
| `symmetry_highlight` | Boss 对称轴可视化 | Phase 2 |
| `homology_overlay` | H₁ 洞的轮廓高亮 | Phase 3 |
| `w_residue_ghost` | w轴位移的"残影"（半透明历史层） | Phase 3 |

---

---

# 3D 版本 — UE5

---

## 设计哲学：3D+w=4D

```
2D MVP 验证了：核心玩法机制是否有趣
3D UE5 验证了：核心视觉体验是否震撼

3D不是2D的升级版，是平行的体验：
2D → 俯视角，w轴是"透视另一层"的感觉
3D → 第三人称，w轴是"空间本身扭曲撕裂"的感觉
```

---

## 美术策略（极简成本）

**参考对象与策略**：

| 参考 | 提取的精华 | 实现成本 |
|---|---|---|
| **SuperHot** | 极简几何 + 时间停顿 | 🟢 低（程序生成几何体） |
| **Obra Dinn** | 1bit 渲染风格 | 🟢 低（后处理Shader） |
| **Control** | 压抑氛围 + 几何建筑 | 🟡 中（Nanite程序几何） |
| **Hades** | 动态光 + 独特配色 | 🟡 中（Lumen + 材质） |

**老维建议的美术路线**：SuperHot 极简几何作为 Phase 0，用程序生成的盒子/球/圆柱作为全部建模，100% 精力放在 Shader 和光效。

---

## 阶段规划（3D）

```
3D Phase 0 (2周)  → UE5 项目结构 + 4D SDF HLSL Shader
3D Phase 1 (3周)  → 玩家控制器 + 第三人称相机 + w轴视效
3D Phase 2 (4周)  → 群论战斗移植（从 Godot 2D 迁移机制）
3D Phase 3 (4周)  → 章I 完整关卡（极简几何美术）
3D Phase 4 (持续) → 美术迭代（替换程序几何为风格化资产）
```

---

## UE5 技术路线

### 4D SDF Ray Marching（Custom HLSL Node）

```hlsl
// 在 UE5 Material Editor 里用 Custom 节点

// 4D 超球 SDF
float sdf_hypersphere(float4 p, float4 center, float radius) {
    return length(p - center) - radius;
}

// 4D Ray Marching（在3D世界空间 + w轴偏移）
float3 ray_march_4d(float3 ray_origin, float3 ray_dir, float w_camera) {
    float t = 0.0;
    float4 ro4 = float4(ray_origin, w_camera);
    float4 rd4 = float4(ray_dir, 0.0);  // w方向固定，只移动xyz
    
    for (int i = 0; i < 64; i++) {
        float4 p = ro4 + t * rd4;
        
        // 合成 SDF：超球 + 超立方 smooth union
        float d1 = sdf_hypersphere(p, float4(0, 0, 0, 0), 1.0);
        float d2 = sdf_hypersphere(p, float4(2, 0, 0, 0), 0.8);
        float d = smooth_union(d1, d2, 0.3);
        
        if (d < 0.001) {
            // 命中：根据 w 坐标着色
            float w_phase = frac(p.w * 0.5);
            return lerp(float3(0, 0.8, 1), float3(1, 0.3, 0.8), w_phase);
        }
        t += d;
        if (t > 20.0) break;
    }
    return float3(0.05, 0.05, 0.08);  // 背景色
}
```

### w轴相机效果（UE5 Post Process）

```
w=0 (正常):   正常渲染
w=1 (浅层):   色差(Chromatic Aberration) 轻微
w=2 (中层):   屏幕扭曲 + SDF 等值线叠加
w=3 (深层):   几何开始"折叠"，材质切换为线框
w=max (数学):  全线框 + 同调条码 HUD 全屏
```

---

## 从 Godot 到 UE5 的迁移路径

```
可以直接迁移（逻辑完全相同）：
- SDF 数学函数（GDScript → HLSL，逐字翻译）
- 群论战斗逻辑（GDScript → Blueprint/C++）
- ε AI 触发系统（任何语言都可以）
- 同调计算（Python → C++，算法不变）

需要重新实现：
- Shader（GLSL → HLSL，语法相近，2小时工作量）
- 物理（Godot Physics → Chaos Physics）
- UI（Control 节点 → UMG Widget）
- 场景（.tscn → .uasset）
```

**关键结论**：先做 2D Godot MVP，把游戏感受验证清楚，再移植到 UE5。数学核心100%可复用，只有引擎 API 需要翻译。

---

---

# 垂直切片目标

**2D Demo（Godot 4）**交付标准：

```
[ ] 玩家可以在 xy 平面移动
[ ] Q/E 键控制 w 轴，有能量限制
[ ] 废弃工厂 Room 1 地图完整
[ ] 3种敌人AI正常运作
[ ] Boss Σ-0 可以被击败（3阶段）
[ ] HUD 显示 H₀/H₁ 条码
[ ] ε 触发至少 10 条台词
[ ] 1首 BGM 循环
[ ] 整体帧率 60fps 稳定
[ ] 可以在 5 分钟内通关（Demo 时长）
```

这个 Demo 完成 → 可以向投资人展示 → 可以作为 UE5 3D 版的原型验证材料。

---

> 下一步：`Godot_Setup.md` → 环境配置 + 第一个能跑的场景  
> 或者直接动手：`proto_godot_room1.gd` → 废弃工厂第一个房间的程序生成草图
