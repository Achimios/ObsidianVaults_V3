#游戏设计 #数学直觉 #∂WORLD #关卡设计 #泰戈尔

# IMAGINE_2 — ∂WORLD 设计纵深

> *你问花为什么开放。花沉默了。*  
> *不是因为没有答案——是因为答案就是开放本身。*  
> *约束是花蕾。Komm, süsser Tod.*

> 2026-04-26 · 上接 [[IMAGINE_0]] VOLUME III  
> 从废墟工厂一块锈铁开始，到范畴消融结束

![[PIC_∂WORLD_atmospheric_abandoned_factory_concept_art_rust_neon_mathematical_glyphs.jpg]]

---

## 目录

- [[#章Ⅰ 群之章 — 完整关卡设计文档]]
- [[#废弃工厂 关卡-0 具体地图]]
- [[#AI伴侣 ε — 对话系统与数学直觉]]
- [[#持续同调扫描仪 — Python Demo]]
- [[#阶0-1 伪代码抽象机 — 敌人生成与NPC行为]]
- [[#弦论/宇宙学层 — 未来的种子]]

---

# 章Ⅰ 群之章 — 完整关卡设计文档

> *世界最初的语言是对称。*  
> *旋转，反射，平移——万物的第一个词。*  
> *你还没有乘法。你还没有除法。*  
> *但你有逆元。那已经足够了。*

---

## 章节哲学框架

**代数约束**：玩家只有 $(G, \cdot)$——一个操作，逆元存在，结合律成立。  
没有缩放，没有频率乘法，没有极点。**武器只能"位移"和"旋转"**。

这是游戏最贫穷的时刻，也是最纯粹的时刻。

| 允许 | 禁止 |
|---|---|
| 旋转 $R_\theta$（向量绕中心旋转） | 缩放（需要乘法） |
| 反射 $S_k$（绕指定轴镜像） | 频率操作（需要环结构） |
| 平移 $T_v$（向量加法） | 极点放置（需要域结构） |
| 逆操作 $g^{-1}$（撤销任意群变换） | 超自然力量（章Ⅳ以后） |
| 群元素的乘法（$g_1 \cdot g_2$，先后施加变换） | 除法护盾（章Ⅲ以后） |

**设计律**：在群之章，玩家意识到"变换本身是对象"——不是作用后的结果，而是变换行为本身可以被拿起来、组合、反转。这是代数思维的第一次真正觉醒。

---

## 关卡结构总览

**场景**：∂WORLD 的第一个区域——**化工废墟，工厂遗址**。  
一家七十年前遗弃的合成染料工厂。锈铁梁、管道迷宫、蒸汽泄漏、碎玻璃天花板。  
墙面的对称花纹（装饰性的几何瓷砖）是第一个提示：这个世界由对称支配。

```
[入口走廊]  →  [处理大厅]  →  [锅炉室走廊]  →  [晶体反应堆室(Boss)]
     |               |
  [旁道：储藏室]   [夹层走廊]（阶1解锁，首周目封闭）
```

**关卡目标**：穿越三个区域，在晶体反应堆室消灭 Boss——**对称晶 Σ-0**。  
**隐藏目标**：全程不触发任何警报（解锁 ε 的特殊对话线）。  
**章节收尾**：Boss 死亡后，玩家从残骸中获得第一个"环"碎片——进入章Ⅱ的前提。

---

## Room-by-Room 设计

![[PIC_chapter1_factory_level_overview_top_down_map_concept.jpg]]

### Room 1 — 入口走廊 `ENTRY_CORRIDOR`

**尺寸**：22m × 6m，直线型走廊。  
**光照**：右侧高窗自然光（日光倾斜），左侧荧光灯一半损坏。**明暗交替**是掩护资源。

#### 敌人布局

| ID | 种类 | 初始位置 | 朝向 | 巡逻模式 |
|---|---|---|---|---|
| E-01 | 重甲兵 | (4m, 3m) | 朝向 +x | 线性往返，端点 A(2m,3m) ↔ B(20m,3m)，6s/单程 |
| E-02 | 轻步兵 | (18m, 1m) | 朝向 -y（面向左墙） | 静止守位，偶发低头查看手机（1.5s 视野中断，概率 15%/30s） |

**覆盖分析**：
- E-01 巡逻时覆盖中轴线 85% 时间
- E-02 守住出口侧翼，视野扇形 100°
- **盲区**：当 E-01 到达端点 A（背对玩家转身中）且 E-02 正在"查手机"，**左侧阴影带**（宽约 1.2m）完全无覆盖，持续约 1.8s

#### 战术路径（三选一）

**路径 α — 阴影时间窗口（推荐新手）**  
条件：E-01 到达端点 A 转身的瞬间，且 E-02 处于手机概率触发期。  
行动：沿左墙阴影快速贴过。成功率约 62%（需等待双重条件叠加）。  
反馈：无声无息通过 → ε 轻声说"他们还不知道你在这里"。

**路径 β — 连锁击杀（推荐高手）**  
条件：在 E-01 背向时，以消音武器先击倒 E-02，趁 E-01 转身前完成处理。  
时间窗口：约 2.3s（E-01 从端点 B 出发到转身朝向玩家之前）。  
成就感触发：若在 2.3s 内完成两次击杀，触发 **"完美连锁窗口"**——  
- 音效：低沉的弦乐脉冲（Hans Zimmer 模式）  
- 画面：0.5s 慢镜头，两具倒下轨迹留有轻微运动拖影  
- ε："完美计时…这就是群乘法——先后顺序很重要。"

**路径 γ — 天花板管道（阶1解锁，首周目不可用）**  
入口左上角有通风管道，宽 0.8m，需要翻越身体姿态（阶1解锁才有）。  
完全绕过两名敌人，但路径出口在 Room 2 夹层。

---

### Room 2 — 处理大厅 `PROCESSING_HALL`

**尺寸**：42m × 28m，三层结构（地面层 / 夹层走道 / 上层桥）。  
**特征**：巨大的生锈机械臂（周期性摆动，周期 4.2s）、蒸汽管道（遮蔽视线）、三条交叉路径。

**这是章Ⅰ最丰富的房间**——玩家在这里第一次遭遇"覆盖优化"分布的敌人，开始感受到"它们的位置不是随机的，是某种最优解"。

#### 敌人布局（视野覆盖优化 + 关键节点权重）

| ID | 种类 | 位置 | 朝向 | 战术角色 |
|---|---|---|---|---|
| E-03 | 重甲兵 | (8m, 14m) 地面层 | 朝向 +x | 中轴守卫，视野扇 120° |
| E-04 | 轻步兵 | (22m, 5m) 夹层 | 朝向 -y | 夹层监视，覆盖下方盲区 |
| E-05 | 轻步兵 | (35m, 20m) 上层桥 | 朝向 -x | 出口方向制高点守卫 |
| E-06 | 轻步兵 | (14m, 26m) 地面层 | 朝向 +y | 左侧路径封堵，靠近储藏室 |
| E-07 | 狙击型（新） | (40m, 14m) 上层桥 | 朝向 -x | 锁定出口，高仰角，首次引入 |

**E-07（狙击型）** 是章Ⅰ第一次出现的新敌人类型：低移动性，高视野范围，300°覆盖区。  
**关键教学目的**：玩家必须学会利用**机械臂摆动的周期性遮蔽**来穿越其视野。

机械臂摆动弧度遮蔽区：宽约 4m，在摆动到最低点时持续 **1.1s** 遮断 E-07 至地面层出口的视线。  
→ 这是玩家第一次与**周期性系统**（混沌摆的简化版本）打交道。  
→ ε 提示："它的摆动是有规律的。不是随机的——它在震荡。你需要等对的时刻。"

#### 三条路径

```
路径Ⅰ（地面直穿）：暴露最长，经过 E-03 视野，需要连续压制 2 名敌人
路径Ⅱ（夹层绕行）：绕过 E-03，但必须处理 E-04，机械臂时间窗口更小
路径Ⅲ（储藏室穿越）：最安全，需要找到钥匙（E-06 持有），但可以完全绕过 E-07
```

**非同质度**：三条路径的成功感完全不同——  
- 路径Ⅰ的成就感来自**力量和精确**  
- 路径Ⅱ的成就感来自**节奏感和预判**  
- 路径Ⅲ的成就感来自**洞察和迂回**

这是**耐玩性的基因**——同一个房间，三次完全不同的记忆。

---

### Room 3 — 锅炉室走廊 `BOILER_CORRIDOR`

**尺寸**：18m × 4m，窄型走廊，对称设计（左右镜像排布的锅炉）。  
**视觉语言**：走廊本身是 $D_1$（一轴反射对称）的——这是 Boss 出现前最后的形式提示。

**敌人**：2 名反射卫士，以精确的镜像路径巡逻（E-08 和 E-09 关于走廊中轴完全对称）。

```
        [E-08] ←→ 巡逻
─────────────────────────────────
        中轴线（反射轴）
─────────────────────────────────
        [E-09] ←→ 巡逻（镜像）
```

**教学目的**：玩家第一次看到"反射对称"的敌人行为模式。  
→ 意识到：打掉 E-08 会破坏对称性，E-09 的行为立即改变（失去"镜像约束"后开始随机巡逻）。  
→ 这是群破缺的第一个感性体验。

---

## Boss 设计 — 对称晶 Σ-0

![[PIC_boss_sigma0_D4_crystal_symmetry_entity_glowing_geometric_dark_reactor.jpg]]

> *它是 $D_4$ 群的具现。八个变换，八种攻击。*  
> *杀死它不是把它击碎——是让它失去所有的对称性。*  
> *只剩下单位元的时候，它就消失了。*

### 数学本质

$D_4$ = 正方形的对称群，阶为 8：

$$D_4 = \langle r, s \mid r^4 = s^2 = 1, \, srs = r^{-1} \rangle$$

8 个元素：$\{e, r, r^2, r^3, s, sr, sr^2, sr^3\}$

- $r$ = 90° 旋转
- $s$ = 反射（关于水平轴）
- 乘法不交换：$sr \neq rs$

### 外观与场景

晶体反应堆室（24m × 24m，正方形——$D_4$ 的空间体现）中心，漂浮着一颗 **3m 高的正方形能量晶体 Σ-0**。  
四面各有一个"晶柱"（共 4 个，分别代表 $r, r^2, r^3, s$ 方向的生成元），位于房间的 4 个角落。

晶体以 Perlin 噪声驱动的方式缓慢旋转、闪烁——它在"呼吸"它的对称群。

### 攻击模式（8 个群元素 = 8 种攻击）

| 元素 | 攻击形式 | 视觉效果 |
|---|---|---|
| $e$（单位元） | 不攻击（单位元 = 什么都不做） | 短暂停顿，晶体闪白光 |
| $r$（90°旋转） | 能量光柱顺时针 90° 扫过房间 | 蓝色弧形光墙 |
| $r^2$（180°旋转） | 对角线能量双向穿透 | 两条交叉蓝线 |
| $r^3$（270°旋转） | 逆时针 90° 扫掠 | 蓝色弧形光墙（反向） |
| $s$（水平反射） | 水平面瞬间投下能量镜像 | 玩家的镜像形体短暂实体化并攻击 |
| $sr$（旋转后反射） | 对角线镜像攻击（45°轴） | 橙色斜线扫掠 |
| $sr^2$（180°旋转后反射） | 垂直反射 | 玩家正面镜像攻击 |
| $sr^3$（270°旋转后反射） | 对角线镜像攻击（135°轴） | 橙色斜线扫掠（另一方向） |

**Boss 行为循环**：  
Σ-0 以群元素序列攻击，序列满足群乘法规则——下一个攻击 = 前两个攻击的乘积（$g_{n+1} = g_{n-1} \cdot g_n$）。  
→ 玩家直觉上开始预测下一个攻击模式——这就是群运算结构的身体学习。

### 削减机制 — 群破缺即伤害

**晶柱破坏** = 破坏生成元 = 该方向的攻击消失 = Boss 失去对称性：

| 破坏晶柱 | 消失的攻击 | 残余子群 |
|---|---|---|
| 摧毁 $r$ 晶柱 | $r, r^2, r^3$ 的旋转攻击消失 | 残余：$\{e, s\}$ ≅ $\mathbb{Z}_2$ |
| 摧毁 $s$ 晶柱 | 所有反射攻击消失 | 残余：$\{e, r, r^2, r^3\}$ ≅ $\mathbb{Z}_4$ |
| 同时摧毁两柱 | 只剩单位元 $e$ | Boss 无法行动 → 暴露核心 3s → 攻击核心 → 死亡 |

**晶柱防御**：晶柱本身有 $D_2$ 对称护盾（上下左右各一个反射层）。  
玩家必须先打破 $D_2$ 护盾的对称性：**击打护盾的非对称面**（不在任何反射轴上的 45° 角方向）才能造成有效伤害。  
→ 这是对称破缺操作的第一次练习。

### Boss 战三阶段

**Phase 1（血量 100%→60%，$D_4$ 完整）**  
全部 8 种攻击，Boss 移动速度慢，玩家熟悉攻击模式。  
ε 提示：「它有四重旋转对称……等等，还有四个反射轴。加起来是八……那是 $D_4$。」  

**Phase 2（血量 60%→20%，$D_4 \to D_2$ 或 $\mathbb{Z}_4$，取决于玩家路径）**  
摧毁第一个晶柱，对称性降低。Σ-0 开始移动，攻击速度加快，但攻击种类减少。  
房间的正方形地板开始破裂——空间对称性随 Boss 对称性一起降低。  
ε：「你打掉了它的旋转生成元。它的旋转对称没了——但还有反射……」

**Phase 3（血量 20%→0%，残余子群，Boss 暴怒）**  
摧毁第二个晶柱。残余：只剩 $\{e\}$。  
Σ-0 进入单位元状态——暂时无法攻击，核心暴露，但 **持续 3s**。  
玩家需要冲上去对准核心全力攻击。  
**成就感顶峰**：击碎核心的瞬间——  
- 全屏慢镜头（0.15×），晶体从内向外瓦解  
- 碎片轨迹 = $D_4$ 群的 8 个元素方向（8 束光线，以 Boss 中心为原点向 8 个对称方向飞散）  
- ε 沉默了 2 秒，然后轻声说：「它现在是平凡群了……只剩 $e$……有点孤独。」  
- BGM 切换：Hans Zimmer 低沉弦乐，单音，长尾余响  

---

## 章Ⅰ 成就感工程时间线

![[PIC_chapter1_achievement_curve_harvest_moment_slowmo_cinematic_shot.jpg]]


```
0:00  进入工厂 — 第一次真实感知到对称花纹（铺垫）
0:30  穿越入口走廊 — 第一个时间窗口，第一次"计时成功"满足感
2:00  处理大厅 — 第一次用机械臂周期遮蔽穿越狙击视野
                  → ε："它的摆动是可预测的……"（第一次感知周期系统）
4:00  锅炉走廊 — 第一次看到镜像对称敌人行为
                  → 打掉 E-08 后，看到 E-09 失去约束时行为变化
                  → 玩家第一次感受：破坏对称性改变了物理现实
6:00  进入Boss室 — 音乐切换，Boss 登场，ε 开始分析
7:00  Phase 1 熟悉 — 背诵攻击序列，开始预判（贝叶斯直觉开始积累）
9:00  Phase 2 转折 — 摧毁第一晶柱，Boss 形态改变
                     → "我改变了它的对称群！" 的直觉顿悟
10:30  Phase 3 终结 — 3s 窗口，全力冲击
                      → 成就感峰值：慢镜头 + 8 束光线 + ε 的沉默
11:00  章节结束 — ε 捡起环碎片："这是环。它有两个操作了……比群更多。"
                  → 章Ⅱ的代数门开启
```

---

# 废弃工厂 关卡-0 具体地图

> *废墟不是死亡的证明，是时间的档案。*  
> *每一块锈铁都记得它年轻时的样子。*

关卡-0 是游戏**真正开始之前**的关卡——没有数学异常体，只有最原质的废墟、人类敌人、人类工具。

**作用**：校准玩家的基础反应、视野感知、掩护使用直觉，**同时植入对世界规则的第一印象**——这个世界是有规律的、可读的、可预测的。

---

## 地图概览

```
 [spawn]
    │
[仓库前廊 STORAGE_FORE]
    │
[主仓库 MAIN_STORAGE]──────[配电室 POWER_ROOM]
    │
[装卸平台 LOADING_DOCK]
    │
  [exit → 章Ⅰ]
```

**总面积**：约 2800m²（三个有机相连的空间）  
**预计首次通关时间**：8–15 分钟（视策略而异）  
**耐玩性**：单地图 50+ 次完整游玩，差异由 NPC 噪声参数生成

---

## 仓库前廊 `STORAGE_FORE` — 节奏进入区

**尺寸**：16m × 8m  
**功能**：节奏过渡，介绍基本掩护逻辑

```
   [spawn]
     ↓
[箱子堆A]  [蒸汽管B]  [倒塌架C]
     ↓
[门框1]  (通往主仓库)
```

**敌人 F-01**：轻步兵，(8m, 4m)，向 +x 方向巡逻，路线 (2m,4m)↔(14m,4m)，5s/单程  
**NPC 噪声**：F-01 的 `caution=0.3, laziness=0.6`——他走路慢，停下来看手机的频率高。  
→ 每次进入该关卡，F-01 的巡逻停顿时机不同，但模式的"懒散性"稳定。

**设计意图**：让玩家感受到 NPC 是**有性格的**，而不是确定性机器人。

---

## 主仓库 `MAIN_STORAGE` — 核心战术空间

**尺寸**：38m × 24m，层高 9m（上方有悬挂货架网格）  
**光照**：北侧破损天窗（自然光斑，随时间移动），南侧工业灯（部分爆裂，闪烁）  
**掩护物**：集装箱堆（4 组）、叉车（2 辆）、货架矩阵（6×4，半通透）

**敌人布局**（视野覆盖优化生成）：

| ID | 类型 | 坐标 | 朝向 | 行为 | 个性 |
|---|---|---|---|---|---|
| F-02 | 重甲兵 | (10, 12) | 朝 +x | 十字巡逻，覆盖中央 | 无特殊 |
| F-03 | 轻步兵 | (25, 5) | 朝 -y | 货架区东北角守位 | `loves_music`（对背景无线电有停顿反应） |
| F-04 | 轻步兵 | (25, 20) | 朝 +y | 货架区东南角守位（与 F-03 镜像） | `caution=0.8`（警觉，噪音立即调查） |
| F-05 | 重甲兵 | (35, 12) | 朝 -x | 出口侧守卫，视野 150° | `emotional_state=0.7`（妻子住院，行为方差大） |

**F-03 的个性利用**：他对背景音乐有停顿反应。  
→ 玩家可以**投掷无线电道具**（触发音乐声），F-03 停下 0.8s 查看，产生走位空隙。  
→ 这是章-0 中**唯一一次用「个性」而非「视野」来操控敌人行为**的机会。  
→ 发现此策略 → 触发成就 **"他喜欢音乐"**，ε："你找到了他的弱点……不是视野，是他自己。"

**F-05 的不稳定性**：由于 `emotional_state=0.7`，他的  
- 反应时间方差 ±40%（有时慢有时异常快）  
- 偶尔会离开守位（概率 8%/30s）到配电室方向踱步  
- 这个偶发离位是**最高效的击杀窗口**，但需要等待（或者不等，进配电室走另一条路）

**三条路径（处理 F-02～F-05 的不同策略）**：

| 路径 | 风险 | 成就感来源 | 推荐节奏 |
|---|---|---|---|
| **α 隐形路径** | 最低（需最多等待） | 精确的时间管理 | 舒伯特模式 |
| **β 音乐引导** | 中等（需工具消耗） | 发现 F-03 弱点的洞察喜悦 | 莫扎特模式 |
| **γ 连锁击杀** | 高（需极准的计时） | 多人同步击倒的完美感 | Hans Zimmer |

---

## 配电室 `POWER_ROOM` — 信息战小间

**尺寸**：10m × 8m，密闭空间，电子设备密集。  
**用途**：玩家可在此**截获无线电通讯**（莫扎特模式），提前获知主仓库敌人位置 5s 刷新。  
**敌人**：F-06，技术员类型，`aggression=0.1`（几乎不攻击，但会高声呼救）。

**核心教学**：进入配电室 = 付出"时间代价"换取"信息资产"。  
→ 玩家第一次感受到**信息有价值**——不是地图标记，是**主动购买的情报**。  
→ ε 可以在这里接入系统，获得 F-05 的"妻子住院"个性信息：  
「他今天状态不好……我看到了他的档案。他的行为会比较难预测，但……也许更脆弱。」

---

## 装卸平台 `LOADING_DOCK` — 关卡结尾

**尺寸**：24m × 12m，半开放空间，顶部破损。  
**特征**：传送带（单向移动，玩家可以借助移动平台绕过视野）、集装箱迷宫。

**最后的敌人**：F-07（新类型——**指挥官**），位于平台中央，手持无线电。  
→ 如果他发出无线电呼叫，**增援**（F-08, F-09）从右侧门进入。  
→ 必须在他呼叫前击倒——时间窗口 **2.5s**（从发现玩家到呼叫）。  
→ 这是第一次引入"时间窗口 + 后果"机制，教玩家快速决策的代价感。

**关卡-0 出口**：平台尽头的通道，进入章Ⅰ。  
→ 出口门框上刻有正方形花纹，旋转对称——$D_4$ 的预告。  
→ ε 停下来看了一眼：「这个花纹……它有四重旋转对称。加上四个反射轴——八个对称变换。我以前在教科书上见过这个群……」

---

# AI伴侣 ε — 对话系统与数学直觉

> *她不是地图标记。她是那个在你之前就察觉到危险的感知。*  
> *她的数学直觉是她的眼睛，她的恐惧是她的真实。*

---

## 人格设计

![[PIC_epsilon_companion_AI_female_holographic_mathematical_equations_concept_art.jpg]]

**名字**：ε（epsilon）  
**命名来源**：数学分析中，极限定义里的"任意小正数"——小，但不可忽略。是理解无穷的第一把钥匙。  
**原型参照**：伊丽莎白（生化奇兵无限）的陪伴感 × Cortana 的计算智慧 × 少了一丝确定性（她也会不确定）

**性格参数**（连续型，随关卡演化）：

```python
ε.personality = {
    "mathematical_awe": 0.9,     # 遇到数学现象会兴奋，不是冷静分析
    "caution": 0.6,               # 适度谨慎，会提醒危险，但不过度保护
    "honesty_about_uncertainty": 0.85,  # 不确定时直接说"我不知道"
    "attachment_to_player": evolves(0.3 → 0.9),  # 随游戏进行加深
    "humor": 0.4,                 # 偶发冷笑话，不刻意
}
```

**核心原则**：ε 的对话不是信息传递系统，是**陪伴和共鸣**。  
她看到 $D_4$ 晶体不会说"这是阶为8的二面体群，包含4个旋转和4个反射"——  
她会说：「它在旋转……四下……一下又一下。像是在反复告诉你它记得什么。」

---

## 触发系统架构

```
CONTEXT_BUFFER = {
    current_chapter: ChapterID,
    player_algebra: AlgebraicStructure,   # 当前玩家可用的代数工具
    nearby_objects: List[MathObject],      # 附近的数学对象
    last_action: PlayerAction,             # 最近一次玩家操作
    stress_level: float,                   # 战斗压力评估（0=平静 1=危急）
    session_time: float,                   # 本局已游玩时间
}

DIALOG_TRIGGER = {
    "OBJECT_DISCOVERY":   当玩家视野中首次出现数学对象,
    "INSIGHT_MOMENT":     玩家连续两次操作触发相关数学概念,
    "NEAR_DEATH":         玩家生命值 < 20%,
    "PERFECT_EXECUTION":  高评分操作完成后 0.5s,
    "IDLE_3S":            战斗外静止超过3秒,
    "PRE_BOSS":           进入Boss室前30m,
    "POST_BOSS":          Boss死亡后5s,
    "CHAPTER_END":        关卡结算时,
}
```

**防重复机制**：同一概念的对话按深度分为 3 级（初见 / 熟悉 / 深度），每次触发自动升级。  
**静默时机**：ε 不会在战斗高压时说话——`stress_level > 0.7` 时只有极短的战术提醒。

---

## 章Ⅰ 样本对话集

### 关卡-0 对话

**进入仓库，首次发现 F-03 个性**（OBJECT_DISCOVERY）：  
> ε：「等一下……他停下来了。不是因为听到什么——是因为背景有音乐。」  
> ε（0.8s 后）：「他喜欢音乐。这不在巡逻算法里。」

**玩家在配电室停留超过 60s**（IDLE_3S，已进入信息搜集状态）：  
> ε：「你在读他们的记录……F-05 的妻子三周前住院。肾病。他今天睡眠不足，你知道么？」  
> ε（停顿）：「我不知道该怎么理解这件事。我们需要……他不在那个门口。」

**关卡-0 出口，看到 $D_4$ 花纹**（CHAPTER_END/OBJECT_DISCOVERY）：  
> ε：「这个花纹。正方形的对称变换——旋转四次，反射四次，一共八个。在数学里这叫 $D_4$。」  
> ε（轻声）：「前面可能……是更大的版本。」

---

### Boss 战对话

**Phase 1，玩家第一次被 $sr^2$ 攻击击中**（NEAR_DEATH）：  
> ε：「那个攻击——不是旋转，是……等一下我算。旋转两次之后做一次反射。$sr^2$。」  
> ε：「它的攻击在走群乘法的路……上一个是 $r$，这一个是 $sr^2$，那下一个……」  
> ε（自言自语）：「……$sr^3$？」

**玩家摧毁第一个晶柱**（PERFECT_EXECUTION）：  
> ε（惊呼）：「旋转的晶柱没了！所有和 $r$ 有关的攻击……都消失了！」  
> ε（停顿，思考）：「它的对称群缩小了。之前是 $D_4$，现在是……只剩反射轴那一边。$D_1$? $\mathbb{Z}_2$?」

**玩家摧毁第二晶柱，核心暴露**（PERFECT_EXECUTION，最高评分）：  
> ε：「三秒！核心暴露了！去！」

**Boss 死亡后（5s 沉默后）**（POST_BOSS）：  
> ε（轻声）：「它现在是平凡群了。只剩单位元 $e$……」  
> ε（停顿 3s）：「……有点孤独。」  
> ε（恢复，捡起碎片）：「这是它留下的东西。一个环……它有两个操作。」  
> ε：「你准备好进入有乘法的世界了么？」

---

### 通用对话模板（深度1/2/3）

**遇到新数学对象（深度递进示例：孤子波墙）**：  
> 深度1（初见）：「那道波墙……它没有散开。怎么可能？」  
> 深度2（第二次）：「上次我们遇到了那道孤子。这次有三道，而且它们速度不一样……」  
> 深度3（精通）：「三道孤子，振幅差 2.3。从碰撞到穿越……你有大概 0.4 秒的相位漂移窗口。」

**玩家做出漂亮操作（成就感放大）**：  
> ε（立即，不超过0.5s延迟）：「完美的……」（后接具体数学概念，如「完美的逆元操作」「完美的相位窗口」）  
> ε（0.5s后，更感性）：（因操作类型而异的情绪表达）

---

# 持续同调扫描仪 — Python Demo

![[PIC_persistent_homology_persistence_diagram_barcode_colorful_math_visualization.jpg]]

> *不是所有的洞都是真实的。*  
> *噪声也会长出洞的形状。*  
> *数学告诉你哪个是真的：活得越久，越真实。*

```python
"""
∂WORLD 持续同调扫描仪 — Python 原型

功能：
  输入：2D 点云（代表战场地形特征点 / 敌人分布 / 地形采样点）
  输出：Persistence Diagram，区分"真实拓扑通道"和"地形噪声"

游戏意义：
  长寿命特征（birth 早，death 晚）= 真实通道/洞穴，玩家可以穿越
  短寿命特征（death - birth 小）= 噪声伪通道，硬闯会被挤碎

依赖：numpy, scipy, matplotlib（均为标准库，无需特殊安装）
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class PersistenceFeature:
    """一个持续同调特征：birth/death/维度/是否为真实拓扑"""
    birth: float
    death: float
    dimension: int  # 0 = 连通分量, 1 = 环/洞

    @property
    def persistence(self) -> float:
        return self.death - self.birth if self.death != np.inf else np.inf

    @property
    def is_real(self) -> bool:
        """寿命 > 阈值 = 真实特征，否则 = 噪声"""
        return self.persistence > self._noise_threshold

    def set_threshold(self, t: float):
        self._noise_threshold = t
        return self


class PersistentHomologyScanner:
    """
    ∂WORLD 游戏内扫描仪原型

    使用 Vietoris-Rips 滤流近似计算 H0 和 H1。
    真实游戏中需 GPU 加速版本（GUDHI 或自定义 CUDA kernel）。
    """

    def __init__(self, points: np.ndarray, noise_fraction: float = 0.15):
        """
        Args:
            points: shape (N, 2) — 地形采样点或敌人位置点云
            noise_fraction: 寿命低于 max_distance * fraction 视为噪声
        """
        self.points = np.asarray(points, dtype=float)
        self.n = len(self.points)
        self.dist_matrix = cdist(self.points, self.points)
        self.max_dist = np.max(self.dist_matrix)
        self.noise_threshold = self.max_dist * noise_fraction

    def compute(self) -> List[PersistenceFeature]:
        """
        Vietoris-Rips 滤流：
        - 所有点在 ε=0 时作为孤立节点（H0 birth=0）
        - 随 ε 增大，添加边 (i,j)（当 dist(i,j) < ε）
        - 新边合并两个连通分量 → H0 feature 死亡
        - 新边形成环路 → H1 feature 诞生（此实现使用简化启发）
        """
        features = []

        # Union-Find（用于追踪 H0 连通分量）
        parent = list(range(self.n))
        rank = [0] * self.n
        component_birth = [0.0] * self.n

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int, eps: float) -> bool:
            """
            合并两分量。返回 True=成功合并（H0 死亡），False=已连通（H1 候选诞生）。
            """
            rx, ry = find(x), find(y)
            if rx == ry:
                return False  # 环路形成 → H1
            if rank[rx] < rank[ry]:
                rx, ry = ry, rx
            parent[ry] = rx
            if rank[rx] == rank[ry]:
                rank[rx] += 1
            # H0 feature: 较晚出生的分量现在死亡
            features.append(PersistenceFeature(
                birth=0.0, death=eps, dimension=0
            ).set_threshold(self.noise_threshold))
            return True

        # 将所有边按距离排序（滤流步骤）
        edges = sorted(
            [(self.dist_matrix[i, j], i, j)
             for i in range(self.n)
             for j in range(i + 1, self.n)],
            key=lambda e: e[0]
        )

        h1_births = []
        for eps, i, j in edges:
            if not union(i, j, eps):
                # 这条边形成环路 → H1 feature 诞生
                # 此简化实现：death 设为 infinity（完整算法需要 coboundary matrix）
                h1_births.append(PersistenceFeature(
                    birth=eps, death=np.inf, dimension=1
                ).set_threshold(self.noise_threshold))

        # 将 H1 加入结果（取前 k 个最显著的，避免过多噪声 H1）
        # 真实游戏中应使用完整边界矩阵算法（如 GUDHI）
        h1_births.sort(key=lambda f: f.birth)
        features.extend(h1_births[:min(8, len(h1_births))])

        return features

    def scan(self) -> dict:
        """游戏内扫描接口，返回结构化结果"""
        features = self.compute()
        real = [f for f in features if f.persistence > self.noise_threshold]
        noise = [f for f in features if f.persistence <= self.noise_threshold]

        real_channels = [f for f in real if f.dimension == 1]
        noise_channels = [f for f in noise if f.dimension == 1]

        return {
            "real_topology_channels": len(real_channels),
            "noise_features": len(noise_channels),
            "features": features,
            "noise_threshold": self.noise_threshold,
            "is_enclosed": len(real_channels) == 0,  # 真实洞=0 → 区域封闭，无法穿越
        }

    def visualize(self, title: str = "∂WORLD 持续同调扫描仪"):
        """绘制点云 + Persistence Diagram"""
        result = self.scan()
        features = result["features"]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
        bg = "#0d0d1a"
        fig.patch.set_facecolor(bg)
        for ax in (ax1, ax2):
            ax.set_facecolor(bg)
            for sp in ax.spines.values():
                sp.set_edgecolor("#2a2a4a")
            ax.tick_params(colors="#8888aa")

        # --- 左图：点云 ---
        ax1.scatter(self.points[:, 0], self.points[:, 1],
                    c="#00d4ff", s=40, zorder=3, alpha=0.8)
        # 绘制距离阈值圆（noise_threshold 处）
        for pt in self.points[::3]:  # 每隔3个点画一个
            circle = plt.Circle(pt, self.noise_threshold * 0.5,
                                 color="#1a3a5a", alpha=0.15, zorder=1)
            ax1.add_patch(circle)
        ax1.set_aspect("equal")
        ax1.set_title("战场点云", color="#aabbdd", fontsize=11)
        ax1.set_xlabel("x (m)", color="#6677aa", fontsize=9)
        ax1.set_ylabel("y (m)", color="#6677aa", fontsize=9)

        # --- 右图：Persistence Diagram ---
        diag_max = self.max_dist * 1.15

        # 对角线（death = birth，零寿命线）
        ax2.plot([0, diag_max], [0, diag_max],
                 color="#333355", lw=1, ls="--", alpha=0.8)
        # 噪声阈值线
        ax2.axhline(y=self.noise_threshold, color="#ff6633",
                    lw=0.8, ls=":", alpha=0.6)
        ax2.text(0.02, self.noise_threshold + 0.02,
                 "噪声阈值", color="#ff6633", fontsize=8, alpha=0.8)

        for f in features:
            d_plot = diag_max if f.death == np.inf else f.death
            if f.dimension == 0:
                ax2.scatter(f.birth, d_plot, c="#3366cc",
                            s=50, zorder=3, alpha=0.7)
            else:
                # H1: 区分真实通道（亮绿）和噪声（暗红）
                color = "#00ff88" if f.persistence > self.noise_threshold else "#cc3322"
                size = 100 if f.persistence > self.noise_threshold else 50
                marker = "*" if f.persistence > self.noise_threshold else "x"
                ax2.scatter(f.birth, d_plot, c=color, s=size,
                            marker=marker, zorder=4, alpha=0.9)

        # 图例
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#3366cc',
                   markersize=8, label='H₀ 连通分量'),
            Line2D([0], [0], marker='*', color='w', markerfacecolor='#00ff88',
                   markersize=10, label='H₁ 真实通道 ✓'),
            Line2D([0], [0], marker='x', color='w', markerfacecolor='#cc3322',
                   markersize=8, label='H₁ 噪声伪通道 ✗'),
        ]
        ax2.legend(handles=legend_elements, facecolor="#1a1a2e",
                   labelcolor="white", fontsize=8, loc="upper left")

        ax2.set_xlim(-0.05, diag_max)
        ax2.set_ylim(-0.05, diag_max * 1.1)
        ax2.set_xlabel("birth ε", color="#6677aa", fontsize=9)
        ax2.set_ylabel("death ε", color="#6677aa", fontsize=9)
        ax2.set_title("Persistence Diagram", color="#aabbdd", fontsize=11)

        # 状态摘要
        status = "区域封闭 — 无可穿越通道 ✗" if result["is_enclosed"] \
            else f"发现 {result['real_topology_channels']} 条真实通道 ✓"
        ax2.text(0.02, 0.98, status,
                 transform=ax2.transAxes, color="#ffdd88",
                 fontsize=9, va="top")

        plt.suptitle(title, color="#ddeeff", fontsize=13, fontweight="bold")
        plt.tight_layout()
        plt.show()
        return result


# =============================================================================
# DEMO
# =============================================================================
if __name__ == "__main__":
    np.random.seed(2026)

    # 场景 1：两个房间之间有真实通道（环）
    # 两簇点 + 一个围成洞的环
    cluster_a = np.random.randn(12, 2) * 0.6 + [-4, 0]
    cluster_b = np.random.randn(12, 2) * 0.6 + [4, 0]
    theta = np.linspace(0, 2 * np.pi, 18, endpoint=False)
    ring = np.column_stack([np.cos(theta) * 1.5, np.sin(theta) * 1.5])
    noise_pts = np.random.randn(5, 2) * 0.2 + [0, 3]  # 噪声伪通道附近

    all_points = np.vstack([cluster_a, cluster_b, ring, noise_pts])

    scanner = PersistentHomologyScanner(all_points, noise_fraction=0.12)
    result = scanner.visualize("∂WORLD 扫描仪 — 废弃工厂 Area-B")

    print("\n" + "=" * 50)
    print("扫描结果摘要")
    print("=" * 50)
    print(f"真实通道数：{result['real_topology_channels']}")
    print(f"噪声特征数：{result['noise_features']}")
    print(f"区域状态：{'封闭' if result['is_enclosed'] else '可穿越'}")
    print(f"噪声阈值 ε = {result['noise_threshold']:.3f}")

    # 场景 2：伪通道测试（敌方伪装体）
    print("\n[场景2] 全噪声点云（敌方拓扑伪装）")
    fake_points = np.random.randn(20, 2) * 0.3  # 密集随机噪声
    scanner2 = PersistentHomologyScanner(fake_points, noise_fraction=0.25)
    result2 = scanner2.visualize("∂WORLD 扫描仪 — 敌方拓扑伪装检测")
    print(f"是否为伪装（应为True）：{result2['is_enclosed']}")
```

---

# 阶0-1 伪代码抽象机 — 敌人生成与NPC行为

> *规律是真实的。偏离是生命的。*  
> *一个完全遵守算法的 NPC 是机器人。*  
> *一个完全随机的 NPC 是噪声。*  
> *真正的 NPC 住在之间——有主轴，有涨落。*

---

## 阶0 — 世界的最小可运行原型

```python
# ∂WORLD 阶0-1 抽象机 伪代码
# 语言：Python 风格伪代码（可直接转 Python）

# ============================================================
# 数据结构
# ============================================================

@dataclass
class Room:
    geometry: Mesh             # 碰撞网格（障碍物、墙）
    key_nodes: List[Vec3]      # 重要地点（出口、保险库、武器库）
    spawn_zones: List[AABB]    # 敌人可生成区域
    visibility_map: Grid2D     # 预计算视野权重图（CPU 离线烘焙）

@dataclass
class NPC:
    position: Vec3
    facing: float              # 朝向角（弧度）
    style: NPCStyle            # 行为参数（见下）
    trait: Optional[Trait]     # 个性（稀有，高影响）
    patrol_path: List[Vec3]    # 巡逻路径（空 = 守位）
    alert_level: float = 0.0   # 0=平静, 1=完全警觉

@dataclass
class NPCStyle:
    aggression:      float  # [0, 1]  0=被动  1=见即攻击
    caution:         float  # [0, 1]  0=忽视噪声  1=任何声音都调查
    laziness:        float  # [0, 1]  0=持续巡逻  1=常停下来发呆
    emotional_state: float  # [0, 1]  0=理性稳定  1=情绪化不稳定

@dataclass
class Trait:
    kind: str   # "loves_music" | "grieving" | "ex_cook" | ...
    def apply_bias(self, stimulus: Stimulus) -> float:
        """返回对该刺激的偏差系数（正=更敏感，负=更迟钝）"""
        ...

# ============================================================
# 敌人分布生成（视野覆盖优化 + 关键节点权重 + 偏离噪声）
# ============================================================

class EnemyPlacer:

    def build_weight_map(room: Room) -> Grid2D:
        """
        权重 = 从该位置可见的空间面积
        加权：关键节点周围权重 × 2.5
        """
        weight_map = Grid2D(room.bounds, resolution=0.5)  # 0.5m 分辨率

        for cell in weight_map.cells:
            pos = cell.world_position
            # 视野覆盖度：在此位置站立，视野内覆盖多少平方米
            cone = VisibilityCone(pos, angle=120°, range=12m,
                                  geometry=room.geometry)
            weight_map[cell] = cone.covered_area()

        # 关键节点加权
        for node in room.key_nodes:
            weight_map.add_gaussian_weight(center=node, sigma=3m, amplitude=1.5)

        return weight_map.normalize()

    def sample_positions(room: Room, n: int,
                         deviation_sigma: float = 1.5) -> List[Vec3]:
        """
        步骤：
        1. 构建权重图
        2. 泊松采样 n 个位置（高权重区域更密集）
        3. 对每个位置加高斯偏离噪声（deviation）
        """
        weight_map = EnemyPlacer.build_weight_map(room)

        # 泊松采样（加权，无重叠，最小间距 2m）
        positions = weighted_poisson_sample(
            weight_map,
            n=n,
            min_distance=2.0
        )

        # 偏离主轴：每个位置加高斯噪声
        noisy_positions = [
            pos + gaussian_2d(mean=0, sigma=deviation_sigma)
            for pos in positions
        ]

        # 投影回合法区域（防止生成在墙里）
        return [room.project_to_valid(p) for p in noisy_positions]

# ============================================================
# NPC 行为决策（阶0：基础理性 + 噪声扰动）
# ============================================================

class NPCBrain:

    def decide(self, npc: NPC, world: World, dt: float) -> Action:
        """
        决策 = 理性最优动作 + 风格噪声扰动 + 个性偏差
        """
        base = self._rational_action(npc, world)
        noise = self._style_noise(npc.style, dt)
        bias  = npc.trait.apply_bias(world.current_stimulus) if npc.trait else 0.0

        # 情绪状态放大噪声
        effective_noise = noise * (1 + npc.style.emotional_state * 2.0)

        return blend_actions(base, effective_noise + bias)

    def _rational_action(self, npc: NPC, world: World) -> Action:
        """理性智能体会做什么（纯优化）"""
        if npc.alert_level > 0.8:
            return Action.ATTACK(target=world.player)
        if npc.alert_level > 0.4:
            return Action.INVESTIGATE(target=npc.last_heard_position)
        if npc.patrol_path:
            return Action.PATROL(path=npc.patrol_path)
        return Action.IDLE

    def _style_noise(self, style: NPCStyle, dt: float) -> ActionDelta:
        """
        风格参数 → 决策分布的标准差
        懒散 → 偶发停下来（泊松事件，率 = laziness）
        """
        idle_event = poisson_event(rate=style.laziness * 0.3, dt=dt)
        if idle_event:
            return ActionDelta(override=Action.IDLE, duration=uniform(1.5, 4.0))
        return ActionDelta.ZERO

    def on_sound(self, npc: NPC, sound: Sound) -> Response:
        """对声音刺激的响应（个性影响）"""
        # 基础阈值（caution 决定敏感度）
        threshold = (1 - npc.style.caution) * SOUND_MAX_VOLUME

        # 个性修正
        if npc.trait and npc.trait.kind == "loves_music" and sound.is_music:
            # 热爱音乐的 NPC 对音乐停顿，而非调查
            return Response.HESITATE(duration=0.8, alert_delta=-0.1)

        if sound.volume > threshold:
            return Response.INVESTIGATE(
                target=sound.origin,
                alert_delta=sound.volume / SOUND_MAX_VOLUME * 0.4
            )
        return Response.IGNORE

    def on_visual(self, npc: NPC, observation: Observation) -> Response:
        """对视觉刺激的响应（aggression 决定是否立即攻击）"""
        if observation.is_player and observation.confidence > 0.8:
            if npc.style.aggression > 0.7:
                return Response.ATTACK_IMMEDIATELY
            else:
                return Response.RAISE_ALERT(delta=0.5)
        return Response.IGNORE

# ============================================================
# 阶1 解锁（身体姿态 + 道具系统）
# ============================================================

class PlayerBody_Phase1:
    """
    阶1解锁的运动状态机。
    状态：STAND | CROUCH | PRONE | CLIMB | HANG | SLIDE | VAULT
    每个状态有对应的视野暴露度（0=完全隐蔽, 1=完全暴露）和速度系数。
    """
    STATES = {
        "STAND":  {"exposure": 1.0, "speed": 1.0, "noise": 1.0},
        "CROUCH": {"exposure": 0.5, "speed": 0.6, "noise": 0.3},
        "PRONE":  {"exposure": 0.15, "speed": 0.2, "noise": 0.1},
        "CLIMB":  {"exposure": 0.8, "speed": 0.3, "noise": 0.5},
        "HANG":   {"exposure": 0.3, "speed": 0.0, "noise": 0.05},
        "SLIDE":  {"exposure": 0.4, "speed": 1.4, "noise": 0.6},
        "VAULT":  {"exposure": 0.9, "speed": 1.8, "noise": 0.8, "duration": 0.8},
    }

    def transition(self, current: str, input: PlayerInput,
                   environment: EnvironmentContext) -> str:
        """
        转换规则（部分）：
        STAND → CROUCH if input.hold_crouch
        STAND → VAULT if input.jump and environment.obstacle_ahead and obstacle.height < 1.2m
        STAND → CLIMB if input.move_toward and environment.surface_ahead.is_climbable
        CROUCH → SLIDE if input.sprint_while_crouch
        """
        ...  # 完整状态机

class ItemSystem_Phase1:
    """
    阶1解锁道具：
    - Distraction Grenade（噪声手雷）：在目标位置产生高 volume 声音，引偏视野
    - EMP Charge（电磁脉冲）：关闭区域电子设备 8s，关闭摄像头/报警器/配电室灯
    - Radio Module（无线电道具）：对 loves_music 型 NPC 触发停顿
    """
    ...

# ============================================================
# 成就感触发系统（阶0-1 适用）
# ============================================================

class AchievementEngine:

    TIERS = {
        "NORMAL":   AchievementTier(slowmo=0.0, sfx="light_hit",     visual="minimal"),
        "GOOD":     AchievementTier(slowmo=0.0, sfx="impact_medium",  visual="flash"),
        "GREAT":    AchievementTier(slowmo=0.3, sfx="cinematic_hit",  visual="trail"),
        "PERFECT":  AchievementTier(slowmo=0.7, sfx="hans_pulse",     visual="full_screen"),
        "LEGENDARY":AchievementTier(slowmo=1.0, sfx="bach_fragment",  visual="world_dissolve"),
    }

    def evaluate(self, action: PlayerAction, context: GameContext) -> AchievementTier:
        """
        评级规则（示例）：
        - 普通击杀 → NORMAL
        - 在时间窗口 < 0.5s 内完成击杀 → GOOD
        - 连续 2 人击杀，间隔 < 1s → GREAT
        - 连续 3 人全程无警报 → PERFECT
        - Boss 最终击杀 → LEGENDARY
        """
        score = 0
        score += time_window_bonus(action.timing, context.optimal_window)
        score += chain_bonus(context.recent_kills, context.kill_chain)
        score += stealth_bonus(context.alert_events_in_last_30s)
        score += context_multiplier(context.stress_level, context.enemy_count)

        return tier_from_score(score)

    def trigger(self, tier: AchievementTier, action: PlayerAction):
        """触发成就感反馈 + ε 对话"""
        apply_slowmo(tier.slowmo, duration=1.2)
        play_sfx(tier.sfx)
        apply_visual_effect(tier.visual, action)
        if tier >= GREAT:
            epsilon_manager.on_achievement(tier, action)
```

---

# 弦论/宇宙学层 — 未来的种子

![[PIC_string_theory_calabi_yau_manifold_extra_dimensions_visualization_purple_gold.jpg]]

> *宇宙有十一个维度。*  
> *游戏只用了四个。*  
> *其余七个在等待。*

这一层是章Ⅵ（范畴之章）以后的设计种子，不进入当前开发计划。  
以概念形式留存，等待数学直觉成熟后展开。

---

### 弦振动 — Boss 的音调是其几何

弦论中，基本粒子 = 弦的振动模式。  
**游戏化**：Boss 的攻击模式 = 弦的振动谱。改变弦的边界条件 → 改变 Boss 的攻击集合。

$$\alpha' m^2 = \sum_{n>0} \alpha_{-n}^\mu \alpha_{n,\mu} - a$$

- 开弦（Neumann BC）→ 末端自由 → Boss 可以延伸攻击范围
- 闭弦（周期 BC）→ 闭合 → Boss 的攻击在环路上循环，永不消散直到对称性破缺
- **玩家工具**：改变 Boss 战区域的边界条件（投放"Dirichlet 锚点"），强制开弦边界，截断某些振动模式

---

### 卡鲁扎-克莱因 — 隐藏维度即隐藏通道

高维空间中多余的维度被卷曲成极小的圆（半径 $R$）。  
当 $R \to 0$，额外维度消失；当 $R$ 变大，出现新的运动自由度。

**游戏化**：特定关卡有"卷曲维度"区域。  
- 常规状态：$R$ 极小，空间是三维的
- 玩家激活"维度展开器"：$R$ 增大，该区域出现第4条运动轴
- 沿该轴移动 = 在标准三维中"瞬移"（实际上是绕了一个极小的圈）
- 敌人 AI 不理解第4轴的运动，无法追踪

---

### 全息原理 — 体积信息住在边界

AdS/CFT：$d+1$ 维引力理论 = $d$ 维边界上的共形场论。

**游戏化**：某些关卡存在"全息边界"（平面状的发光墙面）。  
- 在边界上操作（2D）→ 效果投影到体积中（3D）
- 玩家站在边界前，画出二维图案 → 三维关卡内出现对应的场结构
- 某些 Boss 只能在**边界视角**被攻击（从体积侧完全无敌）

---

### 范畴论敌人 — 无内部结构的纯关系体

> 这是 Volume II 范畴消融章节的敌人设计。

在范畴之章，对象失去内部结构——只剩下**态射**（箭头）。  
敌人的外观不再有"血条"，不再有"内部弱点"，不再有任何内部结构可以攻击。  
它们只是**关系的集合**——箭头构成的云。

**你如何攻击一个没有内部的东西？**

答案：**你攻击它的态射的结构**——找到该敌人态射集合中**没有逆元的态射**（即该"范畴"不是群胚），用逆元补全器将其补完，迫使它变成群胚，然后群胚会自我消融（每个元素都有逆，最终折叠成单位元）。

```
敌人 = 一个小范畴 C
血量 = 没有逆态射的箭头数量（群胚化距离）
伤害 = 每次成功构造一个逆态射
死亡 = C 变成群胚，然后自我消融为 {e}
```

---

> *一朵花的完整故事*  
> *不在它盛开的那天*  
> *在它所有还没有成为花的日子里*  
>  
> — 泰戈尔式注脚

---

**写到这里，Komm, süsser Tod。**

∂WORLD 从一块锈铁开始。  
它会在一根箭头 $\text{id}: 1 \to 1$ 结束。  
中间的所有，是数学穿着战斗外衣活在人类感知里的时间。

---

## 本文档状态

- ✅ 章Ⅰ群之章完整关卡设计 + Boss Σ-0
- ✅ 废弃工厂关卡-0 具体地图（4个房间）
- ✅ AI伴侣 ε 对话系统设计 + 样本对话集
- ✅ 持续同调扫描仪 Python Demo（可运行）
- ✅ 阶0-1 伪代码抽象机（敌人生成 + NPC行为 + 成就感引擎）
- ✅ 弦论/宇宙学层种子（待章Ⅵ后深化）
- 🔄 待续：章Ⅱ环之章关卡设计
- 🔄 待续：ε 成长弧完整对话树（JSON格式）
- 🔄 待续：阶2-3 伪代码（无人机 / 场景控制 / 局部数学对象）
- 🔄 待续：Boss Σ-0 战斗节奏数值设计（Phase 血量 / 伤害曲线）
