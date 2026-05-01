"""
∂WORLD — 4D SDF 原型
Phase 1: 基础 4D 有向距离函数 + 切片动画

运行: python "维度_4_SDF原型.py"
依赖: numpy, matplotlib
     pip install numpy matplotlib
"""
import os
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts.warning=false")

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, RadioButtons
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import warnings
warnings.filterwarnings("ignore")

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────────────────────────────────────
# 1. SDF4D 基类与常用形状
# ─────────────────────────────────────────────────────────────────────────────

class SDF4D:
    """4 维有向距离函数基类。子类只需实现 __call__(p) → float，p.shape=(4,)"""

    def __call__(self, p: np.ndarray) -> float:
        raise NotImplementedError

    # ── CSG 操作 ──────────────────────────────────────────────────────────────

    def __or__(self, other):
        """并集: min(f1, f2)"""
        return _BinaryOp(self, other, np.minimum)

    def __and__(self, other):
        """交集: max(f1, f2)"""
        return _BinaryOp(self, other, np.maximum)

    def __sub__(self, other):
        """差集: max(f1, -f2)"""
        return _SubOp(self, other)

    def smooth_union(self, other, k: float = 0.3):
        """光滑并集 (IQ's smooth-min)"""
        return _SmoothUnion(self, other, k)


class _BinaryOp(SDF4D):
    def __init__(self, a, b, op):
        self.a, self.b, self.op = a, b, op

    def __call__(self, p):
        return self.op(self.a(p), self.b(p))


class _SubOp(SDF4D):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def __call__(self, p):
        return np.maximum(self.a(p), -self.b(p))


class _SmoothUnion(SDF4D):
    def __init__(self, a, b, k):
        self.a, self.b, self.k = a, b, k

    def __call__(self, p):
        d1, d2 = self.a(p), self.b(p)
        k = self.k
        h = np.clip(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0)
        return d2 * (1 - h) + d1 * h - k * h * (1.0 - h)


# ─────────────────────────────────────────────────────────────────────────────
# 2. 具体 4D 形状
# ─────────────────────────────────────────────────────────────────────────────

class Hypersphere(SDF4D):
    """4D 超球: x²+y²+z²+w² = R²"""

    def __init__(self, center=(0, 0, 0, 0), radius=1.0):
        self.c = np.asarray(center, dtype=float)
        self.r = radius

    def __call__(self, p):
        return np.linalg.norm(p - self.c) - self.r


class HyperCube(SDF4D):
    """4D 超立方 (正 8 胞体): 各轴 [-half, half]"""

    def __init__(self, center=(0, 0, 0, 0), half=1.0):
        self.c = np.asarray(center, dtype=float)
        self.h = half

    def __call__(self, p):
        q = np.abs(p - self.c) - self.h
        return np.linalg.norm(np.maximum(q, 0.0)) + min(np.max(q), 0.0)


class HyperTorus(SDF4D):
    """4D 超环面: 两个正交圆的笛卡尔积
       (sqrt(x²+y²) - R)² + (sqrt(z²+w²) - r)² = ε²
    """

    def __init__(self, R=1.5, r=0.4):
        self.R = R  # xy 平面大圆半径
        self.r = r  # zw 平面小圆半径

    def __call__(self, p):
        xy = np.sqrt(p[0] ** 2 + p[1] ** 2) - self.R
        zw = np.sqrt(p[2] ** 2 + p[3] ** 2) - self.r
        return np.sqrt(xy ** 2 + zw ** 2) - 0.1


class HyperCylinder(SDF4D):
    """4D 超圆柱: xyz 球 × w 线段"""

    def __init__(self, sphere_r=1.0, w_half=1.5):
        self.sr = sphere_r
        self.wh = w_half

    def __call__(self, p):
        d_sphere = np.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) - self.sr
        d_w = abs(p[3]) - self.wh
        return max(d_sphere, d_w)


class TwistedHyperPrism(SDF4D):
    """扭曲超棱柱: w 轴上带旋转调制 (FBM 演示)"""

    def __init__(self, base_r=1.0, twist_freq=1.0, twist_amp=0.3):
        self.base = base_r
        self.freq = twist_freq
        self.amp  = twist_amp

    def __call__(self, p):
        # w 轴调制：旋转 xy 平面
        angle = self.amp * np.sin(self.freq * p[3] * np.pi)
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x_rot = p[0] * cos_a - p[1] * sin_a
        y_rot = p[0] * sin_a + p[1] * cos_a
        p_twisted = np.array([x_rot, y_rot, p[2], p[3]])
        return HyperCube(half=self.base)(p_twisted)


# ─────────────────────────────────────────────────────────────────────────────
# 3. 4D 切面方向模式（超立方体的 4 个对称方向）
# ─────────────────────────────────────────────────────────────────────────────

CUT_MODES_4D = {
    "轴向 w":          {"n": np.array([0.,0.,0.,1.]),              "t_max": 1.0},
    "面对角 (z+w)":   {"n": np.array([0.,0.,1.,1.])/np.sqrt(2),  "t_max": np.sqrt(2)},
    "体对角 (y+z+w)": {"n": np.array([0.,1.,1.,1.])/np.sqrt(3),  "t_max": np.sqrt(3)},
    "超对角 (all)":   {"n": np.array([1.,1.,1.,1.])/2,           "t_max": 2.0},
}


def _get_basis_3d(n4):
    """在 4D 中找到与 n4 正交的 3 个单位向量 (e1, e2, e3)。"""
    n4 = n4 / np.linalg.norm(n4)
    basis = [n4]
    vecs = []
    for i in range(4):
        ref = np.eye(4)[i]
        v = ref.copy()
        for b in basis:
            v -= (v @ b) * b
        nrm = np.linalg.norm(v)
        if nrm > 1e-6:
            v /= nrm
            basis.append(v)
            vecs.append(v)
        if len(vecs) == 3:
            break
    return vecs[0], vecs[1], vecs[2]


def _sdf4d_on_plane(sdf, t, n4, e1, e2, e3, z_val, res, ext):
    """在超平面 n4·x=t 的内部 2D 截面上求 SDF。"""
    ta = np.linspace(-ext, ext, res)
    A, B = np.meshgrid(ta, ta)
    X = t*n4[0] + A*e1[0] + B*e2[0] + z_val*e3[0]
    Y = t*n4[1] + A*e1[1] + B*e2[1] + z_val*e3[1]
    Z = t*n4[2] + A*e1[2] + B*e2[2] + z_val*e3[2]
    W = t*n4[3] + A*e1[3] + B*e2[3] + z_val*e3[3]
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel(), W.ravel()], axis=1)
    dist = np.array([sdf(p) for p in pts])
    return ta, dist.reshape(X.shape)


# ─────────────────────────────────────────────────────────────────────────────
# 4. 向量化切片渲染
# ─────────────────────────────────────────────────────────────────────────────

def render_slice_xy(sdf: SDF4D, w_val: float, z_val: float = 0.0,
                    resolution: int = 200, extent: float = 3.0) -> np.ndarray:
    """
    渲染 w=w_val, z=z_val 处的 xy 切片距离图。
    返回 (resolution, resolution) 的 float 数组。
    """
    xs = np.linspace(-extent, extent, resolution)
    ys = np.linspace(-extent, extent, resolution)
    X, Y = np.meshgrid(xs, ys)

    dist = np.zeros_like(X)
    for i in range(resolution):
        for j in range(resolution):
            p = np.array([X[i, j], Y[i, j], z_val, w_val])
            dist[i, j] = sdf(p)
    return dist


def render_slice_xy_fast(sdf: SDF4D, w_val: float, z_val: float = 0.0,
                         resolution: int = 150, extent: float = 3.0) -> np.ndarray:
    """
    快速版本 — 用 numpy 向量化（适用于支持向量化输入的 SDF）。
    对于 lambda-组合的 SDF，回退到逐点计算。
    """
    xs = np.linspace(-extent, extent, resolution)
    ys = np.linspace(-extent, extent, resolution)
    X, Y = np.meshgrid(xs, ys)
    Z = np.full_like(X, z_val)
    W = np.full_like(X, w_val)

    dist = np.zeros_like(X)
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel(), W.ravel()], axis=1)
    for idx, p in enumerate(pts):
        dist.ravel()[idx] = sdf(p)
    return dist


# ─────────────────────────────────────────────────────────────────────────────
# 4. 持续同调近似：统计连通分量（H₀条码）
# ─────────────────────────────────────────────────────────────────────────────

def count_components_at_threshold(dist_map: np.ndarray, threshold: float = 0.0) -> int:
    """
    粗糙的 H₀ 估计：在阈值 <= threshold 的像素中，统计连通分量数。
    使用 scipy 的标记算法。
    """
    try:
        from scipy.ndimage import label
        mask = dist_map <= threshold
        _, n = label(mask)
        return n
    except ImportError:
        return -1  # scipy 未安装时跳过


def compute_barcode_along_w(sdf: SDF4D, w_range=(-2.5, 2.5), steps: int = 40,
                             resolution: int = 80) -> dict:
    """
    沿 w 轴扫描，计算每个 w 切片的近似条码（H₀分量数）。
    返回 {'w_vals': [...], 'H0': [...]}
    """
    w_vals = np.linspace(*w_range, steps)
    H0 = []

    for w in w_vals:
        dm = render_slice_xy_fast(sdf, w, resolution=resolution, extent=3.0)
        n = count_components_at_threshold(dm, threshold=0.0)
        H0.append(n)

    return {'w_vals': w_vals, 'H0': H0}


# ─────────────────────────────────────────────────────────────────────────────
# 5. 主演示：交互式切片查看器
# ─────────────────────────────────────────────────────────────────────────────

def demo_interactive(sdf: SDF4D, name: str = "4D Shape",
                     resolution: int = 60, extent: float = 2.5):
    """
    交互式查看器 v2：
    左图 — 2D SDF 截面（可选 轴向/对边/对角 切面，内部深度可调）
    右图 — 3D 叠层实体面（填充轮廓，显示实体形状，沿 e3 堆叠 9 层）
    底部 — t 滑条（4D 超平面位置）+ t' 滑条（左图内部深度）+ 两组 RadioButtons
    """
    BG    = "#f7f9fb"
    PANEL = "#ffffff"
    CYAN  = "#357fad"

    INNER_MODES_LOC = {
        "轴向 e3=t'":          (0., 0., 1.),
        "对边 (e2+e3)=t'":     (0., 1., 1.),
        "对角 (e1+e2+e3)=t'":  (1., 1., 1.),
    }
    INNER_MODES = list(INNER_MODES_LOC.keys())

    def _inner_cut_basis_loc(e1, e2, e3, key):
        coeff = INNER_MODES_LOC[key]
        inner_n = coeff[0]*e1 + coeff[1]*e2 + coeff[2]*e3
        inner_n = inner_n / np.linalg.norm(inner_n)
        perp = []
        for b in [e1, e2, e3]:
            v = b.copy() - np.dot(b, inner_n)*inner_n
            for p in perp:
                v = v - np.dot(v, p)*p
            nv = np.linalg.norm(v)
            if nv > 1e-10:
                perp.append(v/nv)
            if len(perp) == 2:
                break
        return perp[0], perp[1], inner_n

    cut_mode  = [list(CUT_MODES_4D.keys())[0]]
    inner_key = [INNER_MODES[0]]
    inner_t   = [0.0]
    show_plane = [True]

    fig = plt.figure(figsize=(13, 10.5))
    fig.patch.set_facecolor(BG)
    fig.suptitle(f"∂WORLD — 4D SDF: {name}", fontsize=11, color="#0e1423")

    gs = gridspec.GridSpec(4, 3, height_ratios=[6, 0.55, 0.55, 2.5],
                           hspace=0.56, wspace=0.3)
    ax2d   = fig.add_subplot(gs[0, 0])
    ax3d   = fig.add_subplot(gs[0, 1:], projection="3d")
    axsw   = fig.add_subplot(gs[1, :])   # 4D 超平面 t 滑条
    ax_shape = fig.add_subplot(gs[3, 2])   # 形状切换
    axsi   = fig.add_subplot(gs[2, 0])   # 左图内部深度 t' 滑条
    axchk  = fig.add_subplot(gs[2, 1])   # 显示切面平面开关
    ax_rbl = fig.add_subplot(gs[3, 0])   # 左图 3D 截面方向
    ax_rbr = fig.add_subplot(gs[3, 1])   # 右图 4D 切面方向
    ax2d.set_facecolor(PANEL)

    sdf_ref  = [sdf]
    name_ref = [name]

    def _fa_fb(e1, e2, e3):
        return _inner_cut_basis_loc(e1, e2, e3, inner_key[0])

    def _compute_and_draw(t_val, mode_key):
        n4 = CUT_MODES_4D[mode_key]["n"]
        e1, e2, e3 = _get_basis_3d(n4)
        fa, fb, inner_n_cur = _fa_fb(e1, e2, e3)

        # ── 左图: 2D 截面 ───────────────────────────────────────────────────
        ta, d2d = _sdf4d_on_plane(sdf_ref[0], t_val, n4, fa, fb, inner_n_cur, inner_t[0],
                                   resolution, extent)
        ax2d.cla()
        ax2d.set_facecolor(PANEL)
        ax2d.set_xlim(-extent, extent); ax2d.set_ylim(-extent, extent)
        ax2d.set_aspect('equal')
        ax2d.imshow(d2d, extent=[-extent, extent, -extent, extent], origin='lower',
                    cmap='RdBu_r', vmin=-2, vmax=2, interpolation='bilinear', alpha=0.8)
        ax2d.contour(ta, ta, d2d, levels=[0.0], colors=[CYAN], linewidths=[2.2])
        ax2d.set_title(f"{inner_key[0]}  t'={inner_t[0]:.2f}  t={t_val:.2f}",
                       color='#555', fontsize=9)
        lbl_a = "fa"
        lbl_b = "fb"
        ax2d.set_xlabel(lbl_a, color='#8898a8'); ax2d.set_ylabel(lbl_b, color='#8898a8')
        ax2d.tick_params(colors='gray')

        # ── 右图: 3D 叠层实体面 ─────────────────────────────────────────────
        ax3d.cla()
        ax3d.set_facecolor(PANEL)
        ax3d.set_xlim(-extent, extent); ax3d.set_ylim(-extent, extent)
        ax3d.set_zlim(-extent, extent)
        ax3d.set_box_aspect([1, 1, 1])
        ax3d.xaxis.pane.fill = ax3d.yaxis.pane.fill = ax3d.zaxis.pane.fill = False
        ax3d.set_xlabel("e1", color="#8898a8", fontsize=7)
        ax3d.set_ylabel("e2", color="#8898a8", fontsize=7)
        ax3d.set_zlabel("e3", color="#8898a8", fontsize=7)
        ax3d.set_title(f"3D 叠层实体面   {mode_key}  t={t_val:.2f}",
                       color='#555', fontsize=9)
        ax3d.tick_params(colors='gray', labelsize=6)
        res3 = min(resolution, 40)
        A3, B3 = np.meshgrid(np.linspace(-extent, extent, res3),
                             np.linspace(-extent, extent, res3))
        # ── 自适应 z 范围：找模型实际所在 e3 区间 ──────────────────────────
        z_coarse = np.linspace(-extent, extent, 30)
        z_hits = []
        for z_c in z_coarse:
            _, d_c = _sdf4d_on_plane(sdf_ref[0], t_val, n4, e1, e2, e3, z_c, 6, extent)
            if np.any(d_c <= 0.15):
                z_hits.append(z_c)
        if z_hits:
            margin = max((z_hits[-1] - z_hits[0]) * 0.15, 0.15)
            z_lo = max(-extent, z_hits[0]  - margin)
            z_hi = min( extent, z_hits[-1] + margin)
        else:
            z_lo, z_hi = -extent, extent
        for z_val in np.linspace(z_lo, z_hi, 15):
            _, d3 = _sdf4d_on_plane(sdf_ref[0], t_val, n4, e1, e2, e3,
                                     z_val, res3, extent)
            if np.any(d3 <= 0):
                ax3d.contourf(A3, B3, d3, levels=[-999, 0], zdir='z', offset=z_val,
                              colors=[CYAN], alpha=0.55)
            ax3d.contour(A3, B3, d3, levels=[0.0], zdir='z', offset=z_val,
                         colors=[CYAN], alpha=0.85, linewidths=[1.2])

        # ── 左图切面平面在右图显示 ──────────────────────────────────────────
        if show_plane[0]:
            from mpl_toolkits.mplot3d.art3d import Poly3DCollection
            fa_p, fb_p, inner_n_p = _inner_cut_basis_loc(e1, e2, e3, inner_key[0])
            fa_loc = np.array([np.dot(fa_p,e1), np.dot(fa_p,e2), np.dot(fa_p,e3)])
            fb_loc = np.array([np.dot(fb_p,e1), np.dot(fb_p,e2), np.dot(fb_p,e3)])
            n_loc  = np.array([np.dot(inner_n_p,e1), np.dot(inner_n_p,e2), np.dot(inner_n_p,e3)])
            it = float(np.clip(inner_t[0], -extent, extent))
            ctr = n_loc * it
            c1 = (ctr + extent*fa_loc + extent*fb_loc).tolist()
            c2 = (ctr + extent*fa_loc - extent*fb_loc).tolist()
            c3 = (ctr - extent*fa_loc - extent*fb_loc).tolist()
            c4 = (ctr - extent*fa_loc + extent*fb_loc).tolist()
            poly = Poly3DCollection([[c1,c2,c3,c4]], alpha=0.12,
                                    facecolor="#cc1020", edgecolor="#a00818", linewidths=[0.8])
            ax3d.add_collection3d(poly)

        fig.canvas.draw_idle()

    # ── 初始渲染 ──────────────────────────────────────────────────────────────
    _compute_and_draw(0.0, cut_mode[0])

    # ── 4D 超平面 t 滑条 ──────────────────────────────────────────────────────
    axsw.set_facecolor("#eef4f8")
    t_max0 = CUT_MODES_4D[cut_mode[0]]["t_max"]
    sw = Slider(axsw, "t  (4D 超平面位置)", -t_max0, t_max0, valinit=0.0,
                color="#bfd0dc", track_color="#dce8f0")
    sw.label.set_color("#1a2030"); sw.valtext.set_color(CYAN)

    # ── 左图内部深度 t' 滑条 ──────────────────────────────────────────────────
    axsi.set_facecolor("#eef4f8")
    si = Slider(axsi, "t'  (左图内部深度)", -extent, extent, valinit=0.0,
                color="#c8e4f4", track_color="#e8f4fc")
    si.label.set_color("#1a2030"); si.valtext.set_color(CYAN)

    # ── 显示切面平面 CheckButtons ─────────────────────────────────────────────
    from matplotlib.widgets import CheckButtons
    axchk.set_facecolor("#eef4f8")
    axchk.set_title("右图显示左图平面", color="#8898a8", fontsize=7.5, pad=1)
    chk = CheckButtons(axchk, ["显示切面"], [True])
    for lbl in chk.labels:
        lbl.set_color("#1a2030"); lbl.set_fontsize(8)

    # ── 左图 RadioButtons ─────────────────────────────────────────────────────
    ax_rbl.set_facecolor("#eef4f8")
    ax_rbl.set_title("左图 3D 截面方向", color="#8898a8", fontsize=7.5, pad=1)
    radio_inner = RadioButtons(ax_rbl, INNER_MODES, active=0, activecolor=CYAN)
    for lbl in radio_inner.labels:
        lbl.set_color("#1a2030"); lbl.set_fontsize(8)

    # ── 右图 RadioButtons ─────────────────────────────────────────────────────
    ax_rbr.set_facecolor("#eef4f8")
    ax_rbr.set_title("右图 4D 切面方向", color="#8898a8", fontsize=7.5, pad=1)
    radio = RadioButtons(ax_rbr, list(CUT_MODES_4D.keys()), active=0, activecolor=CYAN)
    for lbl in radio.labels:
        lbl.set_color("#1a2030"); lbl.set_fontsize(8)

    def upd_t(val):
        _compute_and_draw(sw.val, cut_mode[0])

    def upd_inner_t(val):
        inner_t[0] = si.val
        _compute_and_draw(sw.val, cut_mode[0])

    def upd_inner(label):
        inner_key[0] = label
        _compute_and_draw(sw.val, cut_mode[0])

    def upd_cut(label):
        cut_mode[0] = label
        t_max = CUT_MODES_4D[label]["t_max"]
        sw.valmin = -t_max; sw.valmax = t_max
        sw.set_val(0.0)
        sw.ax.set_xlim(-t_max, t_max)
        _compute_and_draw(0.0, label)

    def upd_chk(label):
        show_plane[0] = chk.get_status()[0]
        _compute_and_draw(sw.val, cut_mode[0])

    # ── 形状切换 RadioButtons ───────────────────────────────────────────
    ax_shape.set_facecolor("#eef4f8")
    ax_shape.set_title("切换形状", color="#8898a8", fontsize=7.5, pad=1)
    _shape_labels = [f"[{k}] {n}" for k, (n, _) in DEMOS.items()]
    _shape_default = next(
        i for i, (k, _) in enumerate(DEMOS.items()) if DEMOS[k][1] is sdf_ref[0]
    ) if any(DEMOS[k][1] is sdf_ref[0] for k in DEMOS) else 2
    radio_shape = RadioButtons(ax_shape, _shape_labels,
                               active=_shape_default, activecolor=CYAN)
    for lbl in radio_shape.labels:
        lbl.set_color("#1a2030"); lbl.set_fontsize(7.5)

    def upd_shape(label):
        key = label.split("]")[0].lstrip("[").strip()
        new_name, new_sdf = DEMOS[key]
        sdf_ref[0] = new_sdf
        name_ref[0] = new_name
        fig.suptitle(f"∂WORLD — 4D SDF: {new_name}",
                     fontsize=11, color="#0e1423")
        sw.set_val(0.0)
        si.set_val(0.0)
        _compute_and_draw(0.0, cut_mode[0])

    sw.on_changed(upd_t)
    si.on_changed(upd_inner_t)
    chk.on_clicked(upd_chk)
    radio_inner.on_clicked(upd_inner)
    radio.on_clicked(upd_cut)
    radio_shape.on_clicked(upd_shape)

    plt.show()

# ─────────────────────────────────────────────────────────────────────────────
# 6. 动画演示（无交互，用于截图/录屏）
# ─────────────────────────────────────────────────────────────────────────────

def demo_animation(sdf: SDF4D, name: str = "4D Shape",
                   w_range: tuple = (-2.5, 2.5), frames: int = 60,
                   resolution: int = 100, extent: float = 3.0,
                   save_gif: str = None):
    """沿 w 轴自动扫描动画，可选保存 GIF。"""
    w_vals = np.linspace(*w_range, frames)

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor('#0d0d0d')
    ax.set_facecolor('#1a1a2e')

    dm0 = render_slice_xy_fast(sdf, w_vals[0], resolution=resolution, extent=extent)
    xs = np.linspace(-extent, extent, dm0.shape[1])
    ys = np.linspace(-extent, extent, dm0.shape[0])

    im = ax.imshow(dm0, extent=[-extent, extent, -extent, extent],
                   origin='lower', cmap='RdBu_r', vmin=-2, vmax=2,
                   interpolation='bilinear')
    cnt_col = ax.contour(xs, ys, dm0, levels=[0.0],
                         colors=['white'], linewidths=[2])
    title = ax.set_title(f'∂WORLD — {name}  |  w = {w_vals[0]:.2f}',
                         color='white', fontsize=10)
    ax.tick_params(colors='gray')

    def update(frame):
        w = w_vals[frame]
        dm = render_slice_xy_fast(sdf, w, resolution=resolution, extent=extent)
        ax.cla()
        ax.set_facecolor('#1a1a2e')
        ax.imshow(dm, extent=[-extent, extent, -extent, extent],
                  origin='lower', cmap='RdBu_r', vmin=-2, vmax=2,
                  interpolation='bilinear')
        ax.contour(xs, ys, dm, levels=[0.0], colors=['white'], linewidths=[2])
        ax.set_title(f'∂WORLD — {name}  |  w = {w:.2f}',
                     color='white', fontsize=10)
        ax.tick_params(colors='gray')

    anim = FuncAnimation(fig, update, frames=frames, interval=80, blit=False)

    if save_gif:
        print(f"[∂WORLD] 保存 GIF → {save_gif} ...")
        anim.save(save_gif, writer='pillow', fps=12, dpi=80)
        print("[∂WORLD] 保存完成。")
    else:
        plt.show()

    return anim


# ─────────────────────────────────────────────────────────────────────────────
# 7. 入口：选择想看的演示
# ─────────────────────────────────────────────────────────────────────────────

DEMOS = {
    "1": ("超球 Hypersphere",
          Hypersphere(radius=1.2)),
    "2": ("超立方 Hypercube",
          HyperCube(half=1.0)),
    "3": ("超环面 HyperTorus",
          HyperTorus(R=1.5, r=0.5)),
    "4": ("超球 ∪ 超立方 (CSG 并集)",
          Hypersphere(center=(0.5, 0, 0, 0), radius=0.9) |
          HyperCube(center=(-0.5, 0, 0, 0), half=0.8)),
    "5": ("超球 ∩ 超立方 (CSG 交集)",
          Hypersphere(radius=1.3) & HyperCube(half=1.0)),
    "6": ("超球 - 超立方 (CSG 差集)",
          Hypersphere(radius=1.4) - HyperCube(half=0.8)),
    "7": ("光滑并集 smooth_union",
          Hypersphere(center=(0.8, 0, 0, 0), radius=0.8).smooth_union(
              Hypersphere(center=(-0.8, 0, 0, 0), radius=0.8), k=0.5)),
    "8": ("扭曲超棱柱 TwistedPrism (FBM演示)",
          TwistedHyperPrism(base_r=0.9, twist_freq=1.5, twist_amp=0.6)),
    "9": ("超球链 (3个球的光滑并)",
          Hypersphere(center=(0, 1.2, 0, 0), radius=0.6).smooth_union(
              Hypersphere(center=(0, 0, 0, 0), radius=0.7), k=0.3
          ).smooth_union(
              Hypersphere(center=(0, -1.2, 0, 0), radius=0.6), k=0.3
          )),
}


def main():
    """启动图形化形状选择器，然后打开交互查看器。"""
    from matplotlib.widgets import RadioButtons, Button

    # ── 构建选项标签 ───────────────────────────────────────────────────────────
    labels = [f"[{k}] {name}" for k, (name, _) in DEMOS.items()]

    fig_sel = plt.figure(figsize=(5.5, len(labels) * 0.42 + 1.2))
    fig_sel.patch.set_facecolor("#f7f9fb")
    fig_sel.suptitle("∂WORLD — 4D SDF 形状选择", color="#0e1423", fontsize=11)

    gs_sel = gridspec.GridSpec(2, 1, height_ratios=[1, 0.12], hspace=0.25)
    ax_rb  = fig_sel.add_subplot(gs_sel[0])
    ax_btn = fig_sel.add_subplot(gs_sel[1])
    ax_rb.set_facecolor("#eef4f8")
    ax_btn.set_facecolor("#f7f9fb")

    radio = RadioButtons(ax_rb, labels, active=2, activecolor="#00d4ff")
    for lbl in radio.labels:
        lbl.set_color("#1a2030"); lbl.set_fontsize(9)

    selected = [list(DEMOS.keys())[2]]  # 默认选第 3 项

    def on_select(label):
        key = label.split("]")[0].lstrip("[").strip()
        selected[0] = key
    radio.on_clicked(on_select)

    btn = Button(ax_btn, "启动  →", color="#d8e8f2", hovercolor="#bfd0dc")
    btn.label.set_color("#cc1020"); btn.label.set_fontsize(10)
    launched = [False]

    def on_launch(event):
        launched[0] = True
        plt.close(fig_sel)
    btn.on_clicked(on_launch)

    plt.show()

    if launched[0]:
        key = selected[0]
        name, sdf = DEMOS.get(key, DEMOS["3"])
        print(f"[∂WORLD] 启动: {name}")
        demo_interactive(sdf, name=name)




if __name__ == "__main__":
    main()
