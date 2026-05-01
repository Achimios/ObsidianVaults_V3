


<alreadyInInstructions_so_I_putItInLearnings>
`matplotlib`是用于发期刊的论文级绘图。但是很卡。
**拯救 Python GUI 高刷新率的偏方**：如果你非要留在 Python，别用 `matplotlib`，去用 **`pyqtgraph`** 或者 **`VisPy`**，它们是直接调用底层 OpenGL 接口让显卡干活的，跑 60 帧 3D 轨迹轻轻松松。
</alreadyInInstructions_so_I_putItInLearnings>

---

## 4D 可视化 Demo — 教训总结（2026-04 AkiWorld 项目）

### 🔴 HOT: matplotlib 不适合交互 4D 可视化

- **问题**：每次滑块移动需要重绘整个 3D 场景，帧率极低（<2fps）。
- **表现**：`contourf(zdir=)` 叠层只能出现"平面煎饼堆"，不是真正的 3D 实体。
- **根因**：matplotlib 3D 是伪 3D（投影绘图），无 GPU 加速，无真实体渲染。
- **✅ 下次用**：`vispy`、`pyqtgraph`（OpenGL 直驱）或 `plotly`（Web 渲染）。

### 🔴 HOT: Unicode 下标字符 ₁₂₃ 在 CJK 字体中显示为方框

- **问题**：matplotlib 轴标签 / RadioButtons 标签写 `"e₁"` → Microsoft YaHei 等 CJK 字体无此字符 → 方框乱码。
- **修复**：一律用 ASCII `"e1"` `"e2"` `"e3"`，不用 Unicode `₁₂₃`。
- **适用所有**：`ax.set_xlabel()`、`RadioButtons` 标签、`ax.set_title()` 中的下标符号。

### 左右双面板共享同一 4D 场景

- 左图（2D）和右图（3D）必须由**同一套** 4D 超平面参数控制，不应是独立的 3D 场景。
- 模式：共享一个 `t`（4D 超平面位置）滑块，左图多一个 `t'`（内部深度）滑块，右图显示对应的 3D 截面，左图显示该 3D 截面内的 2D 内切面。

### 4D 超立方线框是近似

- `draw_cube_wire(ax, half=1.0)` 画的是标准 3D 立方体，仅在轴向切（如 `n4=(0,0,0,1)`）时与真实 4D 超立方体截面精确一致。
- 对角方向切时，真实截面需要边-平面求交 + `scipy.ConvexHull`（目前未实现，可接受近似）。

### 切面平面 UI 模式

- 在 3D 右图内用 `Poly3DCollection` 画半透明黄色矩形代表左图 2D 切面的位置，透明度约 0.12，可通过 CheckButtons 开关。
- 代码模式：`inner_idx` 决定哪个轴为"固定轴"，切面平面法向就是该轴方向。