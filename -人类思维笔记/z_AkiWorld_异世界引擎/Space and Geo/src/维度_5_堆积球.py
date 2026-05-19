"""
∂WORLD — Demo C: 5D 超球堆积

左图 (2D 截面)：5D 超立方体 + 32 角超球(r=1) + 中央超球(r=√5-1)
  · 固定 z, w, v → xy 平面切片 (SDF 可视化)
右图 (3D 投影)：固定 w, v → 3D 截面（球面直接渲染）

数学亮点：
  · r_central = √5 − 1 ≈ 1.236 > 1（中央超球**突破**立方体边界！）
  · (w,v)=(0,0) 时：所有角超球消失，只剩中央超球
  · (w,v)=(1,1) 时：8 个 xyz 角超球满尺出现，中央球缩小

运行: python "demo_5d_spheres.py"
"""
import os
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts.warning=false")

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import warnings
warnings.filterwarnings("ignore")

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

BG     = "#f7f9fb"
PANEL  = "#ffffff"
CYAN   = "#357fad"
RED    = "#cc1020"
ORANGE = "#b06010"
WIRE   = "#7aaec4"

R_CENTRAL_5D = np.sqrt(5) - 1   # ≈ 1.236


# ─────────────────────────────────────────────────────────────────────────────
# 几何工具（与 demo_packed_spheres 共用设计）
# ─────────────────────────────────────────────────────────────────────────────

def draw_cube_wire(ax, half: float = 1.0, color: str = WIRE, lw: float = 1.4):
    h = half
    for a, b in [(-h, h), (-h, -h), (h, h), (h, -h)]:
        ax.plot([a, a], [b, b], [-h, h], color=color, lw=lw)
        ax.plot([a, a], [-h, h], [b, b], color=color, lw=lw)
        ax.plot([-h, h], [a, a], [b, b], color=color, lw=lw)


def draw_sphere_surface(ax, r, cx=0., cy=0., cz=0., color=CYAN, alpha=0.30, res=18):
    if r <= 1e-4:
        return
    u = np.linspace(0, 2*np.pi, res)
    v = np.linspace(0, np.pi, res//2)
    ax.plot_surface(
        cx + r * np.outer(np.cos(u), np.sin(v)),
        cy + r * np.outer(np.sin(u), np.sin(v)),
        cz + r * np.outer(np.ones(res), np.cos(v)),
        color=color, alpha=alpha, linewidth=0, antialiased=False, shade=True
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2D SDF 计算（固定 z, w, v → xy 截面）
# ─────────────────────────────────────────────────────────────────────────────

def sdf_5d_at_planes(z0: float, w0: float, v0: float, res: int = 260, ext: float = 2.5):
    """
    5D 球堆积在 (z=z0, w=w0, v=v0) 处的 2D SDF。
    返回 (ta, sdf_cube, sdf_corners, sdf_central)。
    sdf_corners / sdf_central 在截面不存在时返回 None。
    """
    ta = np.linspace(-ext, ext, res)
    X, Y = np.meshgrid(ta, ta)

    # 5D 超立方体 SDF
    q = np.stack([
        np.abs(X) - 1, np.abs(Y) - 1,
        np.full_like(X, abs(z0) - 1),
        np.full_like(X, abs(w0) - 1),
        np.full_like(X, abs(v0) - 1),
    ], axis=-1)
    sdf_cube = (np.linalg.norm(np.maximum(q, 0), axis=-1)
                + np.minimum(np.max(q, axis=-1), 0))

    # 32 个角超球，中心在 (±1,±1,±1,±1,±1)，r=1
    sdf_corners = None
    for cv in (-1., 1.):
        d2_v = (v0 - cv) ** 2
        if d2_v >= 1.0:
            continue
        for cw in (-1., 1.):
            d2_wv = d2_v + (w0 - cw) ** 2
            if d2_wv >= 1.0:
                continue
            for cz in (-1., 1.):
                d2_wvz = d2_wv + (z0 - cz) ** 2
                if d2_wvz >= 1.0:
                    continue
                r_xy = np.sqrt(1.0 - d2_wvz)
                for cx in (-1., 1.):
                    for cy in (-1., 1.):
                        s = np.sqrt((X - cx)**2 + (Y - cy)**2) - r_xy
                        sdf_corners = s if sdf_corners is None else np.minimum(sdf_corners, s)

    # 中央超球 r = √5-1
    r2c = R_CENTRAL_5D**2 - z0**2 - w0**2 - v0**2
    if r2c > 0:
        r_xy_c = np.sqrt(r2c)
        sdf_central = np.sqrt(X*X + Y*Y) - r_xy_c
    else:
        sdf_central = None

    return ta, sdf_cube, sdf_corners, sdf_central


# ─────────────────────────────────────────────────────────────────────────────
# 2D 截面绘制
# ─────────────────────────────────────────────────────────────────────────────

def _draw_2d(ax, ta, sdf_cube, sdf_corners, sdf_central, label: str, ext: float = 2.5):
    ax.set_facecolor(PANEL)
    ax.set_xlim(-ext, ext)
    ax.set_ylim(-ext, ext)
    ax.set_aspect('equal')

    layers = [s for s in [sdf_cube, sdf_corners, sdf_central] if s is not None]
    sdf_union = layers[0].copy()
    for s in layers[1:]:
        sdf_union = np.minimum(sdf_union, s)
    ax.imshow(sdf_union, extent=[-ext, ext, -ext, ext], origin="lower",
              cmap="RdBu_r", vmin=-1.8, vmax=1.8, interpolation="bilinear", alpha=0.75)

    ax.contour(ta, ta, sdf_cube, levels=[0.0], colors=[WIRE], linewidths=[2.2])
    if sdf_corners is not None:
        ax.contour(ta, ta, sdf_corners, levels=[0.0], colors=[ORANGE], linewidths=[2.2])
    if sdf_central is not None:
        ax.contour(ta, ta, sdf_central, levels=[0.0], colors=["white"], linewidths=[2.2])

    ax.set_title(label, color="#aaa", fontsize=9)
    ax.set_xlabel("x", color="#8898a8")
    ax.set_ylabel("y", color="#8898a8")
    ax.tick_params(colors="gray")


# ─────────────────────────────────────────────────────────────────────────────
# 3D 截面渲染（固定 w, v → xyz 空间）
# ─────────────────────────────────────────────────────────────────────────────

def render_5d_scene(ax, w0: float, v0: float):
    ax.cla()
    ax.set_facecolor(PANEL)
    lim = 2.5
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-lim, lim)
    ax.set_box_aspect([1, 1, 1])
    ax.set_xlabel("x", color="#8898a8", fontsize=7)
    ax.set_ylabel("y", color="#8898a8", fontsize=7)
    ax.set_zlabel("z", color="#8898a8", fontsize=7)
    ax.tick_params(colors="gray", labelsize=6)
    ax.set_title(f"5D 超球堆积   w={w0:.2f}  v={v0:.2f}", color="#aaa", fontsize=9)
    ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False

    # 线框（w 和 v 在 [-1,1] 时才画）
    if abs(w0) <= 1.0 and abs(v0) <= 1.0:
        draw_cube_wire(ax, half=1.0)

    # 32 角超球
    for cv in (-1., 1.):
        for cw in (-1., 1.):
            r2 = 1.0 - (w0 - cw)**2 - (v0 - cv)**2
            if r2 <= 0:
                continue
            r = np.sqrt(r2)
            col = CYAN if cw > 0 else ORANGE
            for cx in (-1., 1.):
                for cy in (-1., 1.):
                    for cz in (-1., 1.):
                        draw_sphere_surface(ax, r, cx, cy, cz,
                                            color=col, alpha=0.18, res=12)

    # 中央超球
    r2c = R_CENTRAL_5D**2 - w0**2 - v0**2
    if r2c > 0:
        draw_sphere_surface(ax, np.sqrt(r2c), color=RED, alpha=0.65, res=28)


# ─────────────────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────────────────

def main():
    EXT = 2.5
    RES = 260

    fig = plt.figure(figsize=(14, 10.5))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "∂WORLD  Demo C — 5D 超球堆积  |  2D 截面  ↔  3D 投影",
        fontsize=11, color="#0e1423"
    )

    gs = gridspec.GridSpec(4, 2, height_ratios=[6, 0.55, 0.55, 0.55],
                           hspace=0.52, wspace=0.3)
    ax2d = fig.add_subplot(gs[0, 0])
    ax3d = fig.add_subplot(gs[0, 1], projection="3d")
    axsz = fig.add_subplot(gs[1, 0])
    axsw = fig.add_subplot(gs[1, 1])
    axsv = fig.add_subplot(gs[2, :])   # v 滑条横跨两列
    ax2d.set_facecolor(PANEL)

    # ── 初始渲染 ──────────────────────────────────────────────────────────────
    ta0, sc0, sco0, sce0 = sdf_5d_at_planes(0., 0., 0., RES, EXT)
    _draw_2d(ax2d, ta0, sc0, sco0, sce0, "5D 截面  z=0 w=0 v=0")
    render_5d_scene(ax3d, 0., 0.)

    # ── Sliders ───────────────────────────────────────────────────────────────
    for ax_s in [axsz, axsw, axsv]:
        ax_s.set_facecolor("#eef4f8")

    sz = Slider(axsz, "z  (3D→2D)", -1.5, 1.5, valinit=0.,
                color="#bfd0dc", track_color="#dce8f0")
    sw = Slider(axsw, "w  (5D→4D)", -1.5, 1.5, valinit=0.,
                color="#bfd0dc", track_color="#dce8f0")
    sv = Slider(axsv, "v  (5D→4D)", -1.5, 1.5, valinit=0.,
                color="#c8e4f4", track_color="#e8f4fc")

    for sl in [sz, sw, sv]:
        sl.label.set_color("#1a2030")
        sl.valtext.set_color(CYAN)

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def redraw(_=None):
        z, w, v = sz.val, sw.val, sv.val
        ta, sc, sco, sce = sdf_5d_at_planes(z, w, v, RES, EXT)
        ax2d.cla()
        _draw_2d(ax2d, ta, sc, sco, sce, f"5D 截面  z={z:.2f} w={w:.2f} v={v:.2f}")
        render_5d_scene(ax3d, w, v)
        fig.canvas.draw_idle()

    sz.on_changed(redraw)
    sw.on_changed(redraw)
    sv.on_changed(redraw)

    plt.show()


if __name__ == "__main__":
    main()
