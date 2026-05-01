"""
∂WORLD — Demo B: 球堆积（Sphere Packing）

左图 (3D场景)：2×2×2 立方体 + 8个角球(r=1) + 中央球(r=√3-1)，z 滑块 → 2D 截面
右图 (4D场景)：2×2×2×2 超立方 + 16个角超球(r=1) + 中央超球(r=1)，w 滑块 → 3D 截面

数学亮点：
  · 3D: 中央球半径 r = √3−1 ≈ 0.732（与8个角球正好相切）
  · 4D: 中央超球半径 r = √4−1 = 1（与16个角超球半径相等！）
  · 拖 w 滑块：w=0 只见中央球（r=1）；w=±1 时 8个角球浮现，中央球消失
      ↑ 这揭示了 4D 堆积"包含" 3D 堆积作为截面的事实

运行: python "demo_packed_spheres.py"
依赖: pip install --user numpy matplotlib
"""

import os
import sys
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts.warning=false")

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, RadioButtons
from mpl_toolkits.mplot3d import Axes3D   # noqa: F401
import warnings
warnings.filterwarnings("ignore")

# ── 字体：优先微软雅黑，回退至 DejaVu Sans（避免方框乱码）
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# ── 主题色 ────────────────────────────────────────────────────────────────────
BG      = "#f7f9fb"
PANEL   = "#ffffff"
CYAN    = "#357fad"
RED     = "#cc1020"
ORANGE  = "#b06010"
GRAY    = "#8898a8"
WIRE    = "#7aaec4"   # 立方体线框

# ── 3D 切面方向模式 ──────────────────────────────────────────────────────────────────────
CUT_MODES = {
    "轴向 z":        {"n": np.array([0,0,1.]),                  "t_max": 1.0},
    "对边 (y+z)": {"n": np.array([0,1.,1.])/np.sqrt(2),   "t_max": np.sqrt(2)},
    "对角 (x+y+z)": {"n": np.array([1.,1.,1.])/np.sqrt(3), "t_max": np.sqrt(3)},
}

# ── 4D 切面方向模式（超立方体的 4 个对称方向）──────────────────────────────────
CUT_MODES_4D = {
    "轴向 w":          {"n": np.array([0.,0.,0.,1.]),              "t_max": 1.0},
    "面对角 (z+w)":   {"n": np.array([0.,0.,1.,1.])/np.sqrt(2),  "t_max": np.sqrt(2)},
    "体对角 (y+z+w)": {"n": np.array([0.,1.,1.,1.])/np.sqrt(3),  "t_max": np.sqrt(3)},
    "超对角 (all)":   {"n": np.array([1.,1.,1.,1.])/2,           "t_max": 2.0},
}

# ── 数学常数 ───────────────────────────────────────────────────────────────────
R_CENTRAL_3D = np.sqrt(3) - 1   # ≈ 0.732：3D 中央球半径
R_CENTRAL_4D = 1.0               # = √4−1 = 1：4D 中央超球半径（等于角球！）


# ─────────────────────────────────────────────────────────────────────────────
# 几何工具
# ─────────────────────────────────────────────────────────────────────────────

def draw_cube_wire(ax, half: float = 1.0, color: str = WIRE, lw: float = 1.4):
    """在 3D 轴上画立方体线框（12 条棱）。"""
    h = half
    for a, b in [(-h, h), (-h, -h), (h, h), (h, -h)]:
        ax.plot([a, a], [b, b], [-h, h], color=color, lw=lw)
        ax.plot([a, a], [-h, h], [b, b], color=color, lw=lw)
        ax.plot([-h, h], [a, a], [b, b], color=color, lw=lw)


def draw_sphere_surface(
    ax, r: float,
    cx: float = 0.0, cy: float = 0.0, cz: float = 0.0,
    color: str = CYAN, alpha: float = 0.30, res: int = 18
):
    """在 3D 轴上画参数化球面。"""
    if r <= 1e-4:
        return
    u = np.linspace(0, 2 * np.pi, res)
    v = np.linspace(0, np.pi, res // 2)
    sx = cx + r * np.outer(np.cos(u), np.sin(v))
    sy = cy + r * np.outer(np.sin(u), np.sin(v))
    sz = cz + r * np.outer(np.ones(res), np.cos(v))
    ax.plot_surface(sx, sy, sz, color=color, alpha=alpha,
                    linewidth=0, antialiased=False, shade=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3D 场景 — 2D 截面 SDF
# ─────────────────────────────────────────────────────────────────────────────

def _get_basis_2d(n):
    """给定单位法向量 n (3D)，返回与之正交的两个单位向量 (e1, e2)。"""
    n = n / np.linalg.norm(n)
    ref = np.array([1., 0., 0.]) if abs(n[0]) < 0.9 else np.array([0., 1., 0.])
    e1 = ref - (ref @ n) * n;  e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    return e1, e2


def _get_basis_3d(n4):
    """在 4D 中找到与 n4 正交的 3 个单位向量 (e1, e2, e3)。"""
    n4 = n4 / np.linalg.norm(n4)
    basis = [n4];  vecs = []
    for i in range(4):
        ref = np.eye(4)[i];  v = ref.copy()
        for b in basis:
            v -= (v @ b) * b
        nrm = np.linalg.norm(v)
        if nrm > 1e-6:
            v /= nrm;  basis.append(v);  vecs.append(v)
        if len(vecs) == 3:
            break
    return vecs[0], vecs[1], vecs[2]


def sdf_packed_at_plane(t: float, mode_key: str, res: int = 260, ext: float = 2.5):
    """
    3D 球堆积在切面 n̂·x = t 上的 2D SDF，分开返回各形状。
    返回 (ta, sdf_cube, sdf_corners, sdf_central)。
    """
    n = CUT_MODES[mode_key]["n"]
    e1, e2 = _get_basis_2d(n)
    ta = np.linspace(-ext, ext, res)
    A, B = np.meshgrid(ta, ta)
    X = t*n[0] + A*e1[0] + B*e2[0]
    Y = t*n[1] + A*e1[1] + B*e2[1]
    Z = t*n[2] + A*e1[2] + B*e2[2]

    q = np.stack([np.abs(X)-1, np.abs(Y)-1, np.abs(Z)-1], axis=-1)
    sdf_cube = np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(np.max(q, axis=-1), 0)

    sdf_corners = None
    for cx in (-1., 1.):
        for cy in (-1., 1.):
            for cz in (-1., 1.):
                s = np.sqrt((X-cx)**2 + (Y-cy)**2 + (Z-cz)**2) - 1.0
                sdf_corners = s if sdf_corners is None else np.minimum(sdf_corners, s)

    sdf_central = np.sqrt(X*X + Y*Y + Z*Z) - R_CENTRAL_3D
    return ta, sdf_cube, sdf_corners, sdf_central


# ─────────────────────────────────────────────────────────────────────────────# 2D 截面绘制辅助
# ───────────────────────────────────────────────────────────────────────────

def _draw_2d(ax, ta, sdf_cube, sdf_corners, sdf_central, t0: float, ext: float = 2.5):
    """渐变背景 + 各形状独立边界线。"""
    ax.set_facecolor(PANEL)
    ax.set_xlim(-ext, ext)
    ax.set_ylim(-ext, ext)
    ax.set_aspect('equal')

    # ── Union SDF 渐变背景 ──────────────────────────────────────────────────
    layers = [s for s in [sdf_cube, sdf_corners, sdf_central] if s is not None]
    sdf_union = layers[0].copy()
    for s in layers[1:]:
        sdf_union = np.minimum(sdf_union, s)
    ax.imshow(sdf_union, extent=[-ext, ext, -ext, ext], origin="lower",
              cmap="RdBu_r", vmin=-1.8, vmax=1.8, interpolation="bilinear", alpha=0.75)

    # ── 各形状边界线（画在渐变层上面）────────────────────────────────────────
    ax.contour(ta, ta, sdf_cube, levels=[0.0], colors=[WIRE], linewidths=[2.2])
    if sdf_corners is not None:
        ax.contour(ta, ta, sdf_corners, levels=[0.0], colors=[ORANGE], linewidths=[2.2])
    if sdf_central is not None:
        ax.contour(ta, ta, sdf_central, levels=[0.0], colors=["white"], linewidths=[2.2])

    ax.set_title(f"3D 截面   t = {t0:.2f}", color="#aaa", fontsize=9)
    ax.set_xlabel("u", color="#8898a8")
    ax.set_ylabel("v", color="#8898a8")
    ax.tick_params(colors="gray")



# ─────────────────────────────────────────────────────────────────────────────
# 4D 场景 — 3D 截面（mpl 3D 直接画几何体）
# ─────────────────────────────────────────────────────────────────────────────

INNER_MODES_4D = {
    "轴向 e3=t'":          (0., 0., 1.),
    "对边 (e2+e3)=t'":     (0., 1., 1.),
    "对角 (e1+e2+e3)=t'":  (1., 1., 1.),
}
INNER_MODES = list(INNER_MODES_4D.keys())


def _inner_cut_basis(e1, e2, e3, inner_mode_key):
    """Returns (fa_4d, fb_4d, inner_n_4d) for the 2D inner cut.
    inner_n_4d is the unit normal to the 2D plane (in the hyperplane's 3D subspace).
    fa_4d, fb_4d form an orthonormal basis of the 2D cut plane (perp to inner_n_4d & n4).
    """
    coeff = INNER_MODES_4D[inner_mode_key]
    inner_n_4d = coeff[0]*e1 + coeff[1]*e2 + coeff[2]*e3
    inner_n_4d = inner_n_4d / np.linalg.norm(inner_n_4d)
    perp = []
    for b in [e1, e2, e3]:
        v = b.copy()
        v = v - np.dot(v, inner_n_4d) * inner_n_4d
        for p in perp:
            v = v - np.dot(v, p) * p
        nv = np.linalg.norm(v)
        if nv > 1e-10:
            perp.append(v / nv)
        if len(perp) == 2:
            break
    return perp[0], perp[1], inner_n_4d


def _cutting_plane_corners(e1, e2, e3, inner_mode_key, inner_t, ext):
    """Returns list of 4 corners (3D local coords) of the cutting plane rectangle."""
    fa_4d, fb_4d, inner_n_4d = _inner_cut_basis(e1, e2, e3, inner_mode_key)
    fa_loc = np.array([np.dot(fa_4d, e1), np.dot(fa_4d, e2), np.dot(fa_4d, e3)])
    fb_loc = np.array([np.dot(fb_4d, e1), np.dot(fb_4d, e2), np.dot(fb_4d, e3)])
    n_loc  = np.array([np.dot(inner_n_4d, e1), np.dot(inner_n_4d, e2), np.dot(inner_n_4d, e3)])
    it = float(np.clip(inner_t, -ext, ext))
    ctr = n_loc * it
    h = ext
    return [
        (ctr + h*fa_loc + h*fb_loc).tolist(),
        (ctr + h*fa_loc - h*fb_loc).tolist(),
        (ctr - h*fa_loc - h*fb_loc).tolist(),
        (ctr - h*fa_loc + h*fb_loc).tolist(),
    ]

def sdf4d_packed_at_inner_plane(t_4d: float, mode4d_key: str, inner_mode_key: str,
                                 inner_t: float, res: int = 260, ext: float = 2.5):
    """4D 堆积球在超平面 n4·x=t_4d 内的 2D SDF（inner_mode_key 截面）。"""
    n4 = CUT_MODES_4D[mode4d_key]["n"]
    e1, e2, e3 = _get_basis_3d(n4)
    fa, fb, _ = _inner_cut_basis(e1, e2, e3, inner_mode_key)
    coeff = INNER_MODES_4D[inner_mode_key]
    inner_n_4d = coeff[0]*e1 + coeff[1]*e2 + coeff[2]*e3
    inner_n_4d = inner_n_4d / np.linalg.norm(inner_n_4d)
    ta = np.linspace(-ext, ext, res)
    A, B = np.meshgrid(ta, ta)
    X4 = t_4d*n4[0] + A*fa[0] + B*fb[0] + inner_t*inner_n_4d[0]
    Y4 = t_4d*n4[1] + A*fa[1] + B*fb[1] + inner_t*inner_n_4d[1]
    Z4 = t_4d*n4[2] + A*fa[2] + B*fb[2] + inner_t*inner_n_4d[2]
    W4 = t_4d*n4[3] + A*fa[3] + B*fb[3] + inner_t*inner_n_4d[3]
    q = np.stack([np.abs(X4)-1, np.abs(Y4)-1, np.abs(Z4)-1, np.abs(W4)-1], axis=-1)
    sc = np.linalg.norm(np.maximum(q,0), axis=-1) + np.minimum(np.max(q,axis=-1), 0)
    sco = None
    for cx in (-1.,1.):
        for cy in (-1.,1.):
            for cz in (-1.,1.):
                for cw in (-1.,1.):
                    s = np.sqrt((X4-cx)**2+(Y4-cy)**2+(Z4-cz)**2+(W4-cw)**2) - 1.
                    sco = s if sco is None else np.minimum(sco, s)
    scn = np.sqrt(X4**2+Y4**2+Z4**2+W4**2) - R_CENTRAL_4D
    return ta, sc, sco, scn


def render_packed_4d(ax, t: float, mode4d_key: str, ext: float = 2.5,
                     inner_mode_key: str = "轴向 e3=t'", inner_t: float = 0.0,
                     show_plane: bool = True):
    """
    4D 球堆积在切面 n4·x=t 内的 3D 可视化。
    超立方：线框；角超球 + 中央超球：解析球面。
    show_plane=True 时绘出左图 2D 切面所在平面（半透明黄色）。
    """
    n4 = CUT_MODES_4D[mode4d_key]["n"]
    e1, e2, e3 = _get_basis_3d(n4)

    ax.cla()
    ax.set_facecolor(PANEL)
    ax.set_xlim(-ext, ext); ax.set_ylim(-ext, ext); ax.set_zlim(-ext, ext)
    ax.set_box_aspect([1, 1, 1])
    ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False
    ax.set_xlabel("e1", color="#8898a8", fontsize=7)
    ax.set_ylabel("e2", color="#8898a8", fontsize=7)
    ax.set_zlabel("e3", color="#8898a8", fontsize=7)
    ax.tick_params(colors="gray", labelsize=6)
    ax.set_title(f"4D 球堆积  {mode4d_key}  t={t:.2f}", color="#aaa", fontsize=9)

    # ── 超立方体：线框 ──────────────────────────────────────────────────────────
    t_max = CUT_MODES_4D[mode4d_key]["t_max"]
    if abs(t) < t_max:
        draw_cube_wire(ax, half=1.0)

    # ── 16 角超球：解析截面球面 ─────────────────────────────────────────────────
    for cx4 in (-1., 1.):
        for cy4 in (-1., 1.):
            for cz4 in (-1., 1.):
                for cw4 in (-1., 1.):
                    c4 = np.array([cx4, cy4, cz4, cw4])
                    d = float(np.dot(n4, c4)) - t
                    r2 = 1.0 - d * d
                    if r2 <= 0:
                        continue
                    c_proj = c4 - d * n4
                    cx3 = float(np.dot(e1, c_proj))
                    cy3 = float(np.dot(e2, c_proj))
                    cz3 = float(np.dot(e3, c_proj))
                    col = CYAN if np.dot(n4, c4) >= 0 else ORANGE
                    draw_sphere_surface(ax, np.sqrt(r2), cx3, cy3, cz3,
                                        color=col, alpha=0.20, res=14)

    # ── 中央超球：解析截面 ──────────────────────────────────────────────────────
    d_c = -t
    r2c = R_CENTRAL_4D ** 2 - d_c * d_c
    if r2c > 0:
        draw_sphere_surface(ax, np.sqrt(r2c), 0., 0., 0., color=RED, alpha=0.55, res=28)

    # ── 左图切面平面（半透明黄色矩形）────────────────────────────────────────────
    if show_plane:
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        corners = _cutting_plane_corners(e1, e2, e3, inner_mode_key, inner_t, ext)
        poly = Poly3DCollection([corners], alpha=0.12,
                                facecolor="#cc1020", edgecolor="#a00818", linewidths=[0.8])
        ax.add_collection3d(poly)


# ─────────────────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────────────────

def main():
    EXT = 2.5
    RES = 260
    cut4d_mode = [list(CUT_MODES_4D.keys())[0]]
    inner_key  = [INNER_MODES[0]]
    inner_t    = [0.0]
    show_plane = [True]

    fig = plt.figure(figsize=(14, 11.0))
    fig.patch.set_facecolor(BG)
    fig.suptitle("∂WORLD  Demo B — 4D 球堆积  | 左=4D内部截面  右=4D立体",
                 fontsize=11, color="#0e1423")

    gs = gridspec.GridSpec(4, 2, height_ratios=[6, 0.52, 0.52, 2.5], hspace=0.58, wspace=0.3)
    ax2d   = fig.add_subplot(gs[0, 0])
    ax3d   = fig.add_subplot(gs[0, 1], projection="3d")
    axsw   = fig.add_subplot(gs[1, :])
    axsi   = fig.add_subplot(gs[2, 0])
    axchk  = fig.add_subplot(gs[2, 1])
    ax_rbl = fig.add_subplot(gs[3, 0])
    ax_rbr = fig.add_subplot(gs[3, 1])
    ax2d.set_facecolor(PANEL)

    # ── 初始渲染 ──────────────────────────────────────────────────────────────
    ta0, sc0, sc_c0, sc_n0 = sdf4d_packed_at_inner_plane(0.0, cut4d_mode[0], INNER_MODES[0], 0.0, RES, EXT)
    _draw_2d(ax2d, ta0, sc0, sc_c0, sc_n0, 0.0)
    render_packed_4d(ax3d, 0.0, cut4d_mode[0], EXT, INNER_MODES[0], 0.0, True)

    # ── Sliders ───────────────────────────────────────────────────────────────
    axsw.set_facecolor("#eef4f8")
    sw = Slider(axsw, "t  (4D 超平面位置)", -1.0, 1.0, valinit=0.0,
                color="#bfd0dc", track_color="#dce8f0")
    sw.label.set_color("#1a2030");  sw.valtext.set_color(CYAN)

    axsi.set_facecolor("#eef4f8")
    si = Slider(axsi, "t'  (左图内部深度)", -EXT, EXT, valinit=0.0,
                color="#c8e4f4", track_color="#e8f4fc")
    si.label.set_color("#1a2030");  si.valtext.set_color(CYAN)

    # ── 左图 2D 切面平面 RadioButtons ─────────────────────────────────────────
    ax_rbl.set_facecolor("#eef4f8")
    ax_rbl.set_title("左图 2D 切面平面", color="#8898a8", fontsize=7.5, pad=1)
    radio_inner = RadioButtons(ax_rbl, INNER_MODES, active=0, activecolor=CYAN)
    for lbl in radio_inner.labels:
        lbl.set_color("#1a2030"); lbl.set_fontsize(8)

    # ── 右图 4D 切面方向 RadioButtons ─────────────────────────────────────────
    ax_rbr.set_facecolor("#eef4f8")
    ax_rbr.set_title("右图 4D 切面方向", color="#8898a8", fontsize=7.5, pad=1)
    radio_4d = RadioButtons(ax_rbr, list(CUT_MODES_4D.keys()), active=0, activecolor=CYAN)
    for lbl in radio_4d.labels:
        lbl.set_color("#1a2030"); lbl.set_fontsize(8)

    # ── 显示切面平面 CheckButtons ─────────────────────────────────────────────
    from matplotlib.widgets import CheckButtons
    axchk.set_facecolor("#eef4f8")
    axchk.set_title("右图内显示左图平面", color="#8898a8", fontsize=7.5, pad=1)
    chk = CheckButtons(axchk, ["显示切面"], [True])
    for lbl in chk.labels:
        lbl.set_color("#1a2030"); lbl.set_fontsize(8)

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _redraw_2d():
        ta, sc, sc_c, sc_n = sdf4d_packed_at_inner_plane(
            sw.val, cut4d_mode[0], inner_key[0], si.val, RES, EXT)
        ax2d.cla()
        _draw_2d(ax2d, ta, sc, sc_c, sc_n, si.val)
        fig.canvas.draw_idle()

    def _redraw_4d():
        render_packed_4d(ax3d, sw.val, cut4d_mode[0], EXT,
                         inner_key[0], si.val, show_plane[0])
        fig.canvas.draw_idle()

    def upd_sw(val):   _redraw_2d(); _redraw_4d()
    def upd_si(val):   inner_t[0] = si.val; _redraw_2d(); _redraw_4d()

    def upd_inner(label):
        inner_key[0] = label
        _redraw_2d(); _redraw_4d()

    def upd_4d(label):
        cut4d_mode[0] = label
        t_max = CUT_MODES_4D[label]["t_max"]
        sw.valmin = -t_max;  sw.valmax = t_max
        sw.set_val(0.0);  sw.ax.set_xlim(-t_max, t_max)
        sw.label.set_text(f"t  [{label.split()[0]}=t]")
        _redraw_2d(); _redraw_4d()

    def upd_chk(label):
        show_plane[0] = chk.get_status()[0]
        _redraw_4d()

    sw.on_changed(upd_sw);  si.on_changed(upd_si)
    radio_inner.on_clicked(upd_inner)
    radio_4d.on_clicked(upd_4d)
    chk.on_clicked(upd_chk)

    plt.show()


if __name__ == "__main__":
    main()
