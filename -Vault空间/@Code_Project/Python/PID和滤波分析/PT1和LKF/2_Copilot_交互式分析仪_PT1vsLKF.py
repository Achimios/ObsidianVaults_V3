"""
穿越机陀螺仪滤波器交互式分析仪  v2
PT1 vs 2-state LKF + Notch A/B — Perlin 噪声 + 机架共振 + 时域波形 + 群延迟

运行: py "2_Copilot_交互式分析仪_PT1vsLKF.py"
依赖: numpy matplotlib scipy PyQt5
"""
import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QDoubleSpinBox, QGroupBox, QSizePolicy,
    QPushButton, QCheckBox, QSpinBox, QComboBox,
)
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavToolbar,
)
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from scipy.signal import freqz, lfilter, welch, butter, iirnotch

FS        = 2000     # 采样率固定 2 kHz
N_SECONDS = 30       # 时域信号长度
N_SIG     = FS * N_SECONDS

# ─────────────────────────────────────────────────────────────────
#  Perlin-style 1D 噪声（纯 numpy，无外部库）
# ─────────────────────────────────────────────────────────────────
def perlin_noise_1d(n, octaves=5, persistence=0.5, lacunarity=2.0, seed=7):
    rng = np.random.default_rng(seed)
    result = np.zeros(n)
    amp = 1.0
    freq = 1.0
    total_amp = 0.0
    for _ in range(octaves):
        n_knots = max(2, int(n * freq / 50))   # 每 octave 的控制点数
        knots = rng.standard_normal(n_knots + 2)
        t = np.linspace(0, n_knots, n)
        idx = np.clip(t.astype(int), 0, n_knots - 1)
        frac = t - idx
        s = frac * frac * (3.0 - 2.0 * frac)  # smoothstep
        val = knots[idx] * (1.0 - s) + knots[idx + 1] * s
        result += val * amp
        total_amp += amp
        amp *= persistence
        freq *= lacunarity
    return result / total_amp


# ─────────────────────────────────────────────────────────────────
#  PT1 系数
# ─────────────────────────────────────────────────────────────────
def pt1_coeffs(fc, fs=FS):
    a = 2 * np.pi * fc / fs
    a /= (1 + a)
    return [a], [1.0, -(1.0 - a)]


# ─────────────────────────────────────────────────────────────────
#  2-state LKF — Riccati 迭代至稳态
# ─────────────────────────────────────────────────────────────────
def lkf_coeffs(q_omega, q_bias, r_meas, fs=FS):
    ts = 1.0 / fs
    F = np.array([[1.0, -ts], [0.0, 1.0]])
    H = np.array([[1.0, 1.0]])
    Q = np.diag([q_omega * ts, q_bias * ts])
    R = float(r_meas)

    P = np.eye(2)
    for _ in range(3000):   # 迭代 Riccati 到稳态
        P_pred = F @ P @ F.T + Q
        S = float((H @ P_pred @ H.T).item()) + R
        K = (P_pred @ H.T) / S      # shape (2, 1)
        P = (np.eye(2) - K @ H) @ P_pred

    # 闭环系统矩阵
    A = F - K @ H @ F
    K0 = float(K[0, 0])
    K1 = float(K[1, 0])
    A00, A01 = A[0, 0], A[0, 1]
    A10, A11 = A[1, 0], A[1, 1]

    # 传递函数 H(z) = C(zI-A)^{-1}B，C=[1,0]
    # 分子: K0*z + (-A11*K0 + A01*K1) — 转成 z^{-n} 形式除以分母
    # 分母特征多项式: z^2 - tr(A)*z + det(A)
    tr_A  = A00 + A11
    det_A = A00 * A11 - A01 * A10

    b_num = [0.0, K0, -A11 * K0 + A01 * K1]   # [z^0, z^{-1}, z^{-2}]
    a_den = [1.0, -tr_A, det_A]                 # [z^0, z^{-1}, z^{-2}]
    return b_num, a_den


# ─────────────────────────────────────────────────────────────────
#  机架共振：带通滤波白噪声增益叠加（增益用线性倍数，不用dB）
# ─────────────────────────────────────────────────────────────────
def resonance(white, freq_r, gain_lin, q_factor, fs=FS):
    """gain_lin: 线性增益倍数（1 = 0 dB, 10 = 20 dB）"""
    if gain_lin <= 0 or freq_r <= 0:
        return np.zeros_like(white)
    bw  = freq_r / max(q_factor, 0.5)
    nyq = fs / 2.0
    lo  = max((freq_r - bw / 2.0) / nyq, 1e-4)
    hi  = min((freq_r + bw / 2.0) / nyq, 1.0 - 1e-4)
    if lo >= hi:
        return np.zeros_like(white)
    b, a = butter(2, [lo, hi], btype='band')
    out  = lfilter(b, a, white)
    rms  = np.std(out)
    if rms < 1e-12:
        return np.zeros_like(white)
    return out / rms * gain_lin


# ─────────────────────────────────────────────────────────────────
#  Notch 系数
# ─────────────────────────────────────────────────────────────────
def notch_coeffs(freq, q, fs=FS):
    w0 = np.clip(freq / (fs / 2.0), 1e-5, 1.0 - 1e-5)
    return iirnotch(w0, Q=max(float(q), 0.5))

# ───────────────────────────────────────────────────────────────
#  共振分布模式：多峰微高斯散布
# ───────────────────────────────────────────────────────────────
def resonance_dist(white, freq_r, gain_lin, q_factor, n_peaks, f_spread, seed_val, fs=FS):
    """Multiple resonance peaks distributed ±f_spread around freq_r (4-motor variance)."""
    rng = np.random.RandomState(int(seed_val) % (2**31))
    offsets = rng.normal(0, max(float(f_spread), 1.0) / 3.0, int(n_peaks))
    g_each  = gain_lin / max(np.sqrt(n_peaks), 1.0)   # RMS 均匀
    total   = np.zeros(len(white))
    for off in offsets:
        total += resonance(white, freq_r + off, g_each, q_factor, fs)
    return total

# ─────────────────────────────────────────────────────────────────
#  主窗口
# ─────────────────────────────────────────────────────────────────
class FilterAnalyzer(QMainWindow):
    # ── 主题调色板 ────────────────────────────────────────────────
    _DARK = dict(
        fig='#080c14', ax='#0c1018',
        grid='#1a2232', spine='#192440',
        tick='#c8d8e6', label='#c8d8e6', title='#ffffff',
        href='#1e3050', href2='#1a2840',
        band='#6ec6e8', xmark='#6ec6e8',
        pt1='#7ac4e0', lkf='#e8394a',
        noise='#253048', noise_psd='#555575',
        stick='#f5f5ff', dot='#e8394a',
        legend_bg='#060c1a', legend_txt='white',
        tbar='background:#080f1e; color:#c8d8e6; font-size:8pt;',
        pal_win='#080c16', pal_btn='#0d1e38', pal_txt='#e0e0f0',
        pal_hl='#a01020', pal_base='#060a12',
    )
    _LIGHT = dict(
        fig='#f7f9fb', ax='#ffffff',
        grid='#dce8f0', spine='#bfd0dc',
        tick='#1a2030', label='#1a2030', title='#080c18',
        href='#b8c8d4', href2='#d0dce4',
        band='#c8e4f4', xmark='#7aaec4',
        pt1='#3a92ba', lkf='#cc1020',
        noise='#a4b8c8', noise_psd='#8898a8',
        stick='#1a202e', dot='#cc1020',
        legend_bg='#f0f6fa', legend_txt='#1a2030',
        tbar='background:#e8f0f6; color:#1a2030; font-size:8pt;',
        pal_win='#eef4f8', pal_btn='#d8e8f2', pal_txt='#1a2030',
        pal_hl='#a01020', pal_base='#ffffff',
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "穿越机陀螺滤波器分析仪 v2  |  PT1 vs LKF + Notch  |  fs=2kHz"
        )
        self.resize(1680, 980)
        self._log_xaxis  = False
        self._log_yaxis  = False
        self._noise_cache = None
        self._noise_wp    = None
        self._noise_res   = None
        self._noise_key   = None
        self._last_ax5    = None
        self._stick_pts   = []      # [(t, y)] user control points (not anchors)
        self._anchor_y    = [0.0, 0.0]   # y at t=0 and t=N_SECONDS
        self._stick_mode  = 'add'   # 'add' | 'del' | 'adj'
        self._drag_idx    = None    # index into _build_all_pts() during adj drag
        self._drag_is_anchor = False
        self._drag_anchor_idx = None
        self._ax5_xlim    = [0.0, float(N_SECONDS)]
        self._ax5_ylim    = [-400.0, 400.0]
        self._td_cache    = None    # (signal, b_pt1, a_pt1, b_lkf, a_lkf,
                                    #  use_n1, b_n1, a_n1, use_n2, b_n2, a_n2)
        self._dark_mode   = True    # Mirror's Edge dark by default
        # Timers
        self._timer = QTimer(); self._timer.setSingleShot(True)
        self._timer.setInterval(280); self._timer.timeout.connect(self._do_update)
        self._stick_timer = QTimer(); self._stick_timer.setSingleShot(True)
        self._stick_timer.setInterval(80); self._stick_timer.timeout.connect(self._do_update)
        self._build_ui()
        self.canvas.mpl_connect('button_press_event',   self._on_canvas_click)
        self.canvas.mpl_connect('motion_notify_event',  self._on_canvas_drag)
        self.canvas.mpl_connect('button_release_event', self._on_canvas_release)
        self._do_update()

    # ── 工具函数 ──────────────────────────────────────────────────
    def _spin(self, lo, hi, val, decs=1, suffix="", step=None):
        sb = QDoubleSpinBox()
        sb.setRange(lo, hi); sb.setValue(val); sb.setDecimals(decs)
        if suffix: sb.setSuffix(f" {suffix}")
        if step:   sb.setSingleStep(step)
        sb.valueChanged.connect(lambda _: self._schedule())
        return sb

    def _ispin(self, lo, hi, val):
        sb = QSpinBox()
        sb.setRange(lo, hi); sb.setValue(val)
        sb.valueChanged.connect(lambda _: self._schedule())
        return sb

    def _group(self, title, rows, extras=None):
        g  = QGroupBox(title)
        gl = QGridLayout(g)
        gl.setContentsMargins(5, 8, 5, 5); gl.setSpacing(3)
        for i, (lbl, w) in enumerate(rows):
            gl.addWidget(QLabel(lbl), i, 0, Qt.AlignRight)
            gl.addWidget(w,           i, 1)
        if extras:
            r = gl.rowCount()
            for ew in extras:
                gl.addWidget(ew, r, 0, 1, 2); r += 1
        return g

    def _schedule(self):
        self._timer.stop(); self._timer.start()

    # ── 建 UI ─────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        ml = QHBoxLayout(central)
        ml.setContentsMargins(5, 5, 5, 5); ml.setSpacing(6)

        # ── 左侧参数面板 ──────────────────────
        pane = QWidget(); pane.setFixedWidth(305)
        pl = QVBoxLayout(pane); pl.setSpacing(4)

        # 轴切换
        btn_row = QHBoxLayout()
        self.btn_x = QPushButton("频率轴: 线性"); self.btn_x.setCheckable(True)
        self.btn_x.clicked.connect(self._toggle_x)
        self.btn_y = QPushButton("幅度: 线性");   self.btn_y.setCheckable(True)
        self.btn_y.clicked.connect(self._toggle_y)
        btn_row.addWidget(self.btn_x); btn_row.addWidget(self.btn_y)
        pl.addLayout(btn_row)

        # 放大独显
        self.solo_combo = QComboBox()
        self.solo_combo.addItems(["全部显示", "① 幅频", "② 相频", "③ 群延迟", "④ PSD", "⑤ 时域"])
        self.solo_combo.currentIndexChanged.connect(lambda _: self._schedule())
        pl.addWidget(self.solo_combo)

        # 主题切换
        self.btn_theme = QPushButton("☀ 亮色主题")
        self.btn_theme.setCheckable(True)
        self.btn_theme.setToolTip("切换明暗色主题")
        self.btn_theme.clicked.connect(self._toggle_theme)
        pl.addWidget(self.btn_theme)

        # PT1
        self.fc_pt1 = self._spin(10, 900, 100, 0, "Hz", 10)
        pl.addWidget(self._group("PT1 Filter", [("截止 fc:", self.fc_pt1)]))

        # LKF
        self.q_omega = self._spin(1e-4, 200,  1.0,  4, "",   0.1)
        self.q_bias  = self._spin(1e-9, 1e-3, 1e-4, 5, "",   1e-5)
        self.r_meas  = self._spin(0.05, 500,  0.5,  3, "",   0.05)
        btn_sync = QPushButton("同步 PT1 fc")
        btn_sync.setToolTip("自动调整 r, 使 LKF -3dB 频率 = PT1 截止频率")
        btn_sync.clicked.connect(self._sync_lkf_to_pt1)
        pl.addWidget(self._group("2-state LKF (ω + bias)",
            [("ω:", self.q_omega), ("q_b:", self.q_bias), ("r:", self.r_meas)],
            extras=[btn_sync]))

        # Notch A/B
        self.n1_en = QCheckBox("启用 Notch A"); self.n1_en.setChecked(True)
        self.n1_en.stateChanged.connect(lambda _: self._schedule())
        self.f_n1 = self._spin(10, 950, 150, 0, "Hz", 10)
        self.q_n1 = self._spin(1, 200, 10, 1, "Q", 1)
        pl.addWidget(self._group("Notch 滤波器 A",
            [("频率:", self.f_n1), ("Q:", self.q_n1)], extras=[self.n1_en]))

        self.n2_en = QCheckBox("启用 Notch B"); self.n2_en.setChecked(True)
        self.n2_en.stateChanged.connect(lambda _: self._schedule())
        self.f_n2 = self._spin(10, 950, 320, 0, "Hz", 10)
        self.q_n2 = self._spin(1, 200,  8., 1, "Q", 1)
        pl.addWidget(self._group("Notch 滤波器 B",
            [("频率:", self.f_n2), ("Q:", self.q_n2)], extras=[self.n2_en]))

        # 机架共振 A/B (with enable checkbox)
        self.chk_r1 = QCheckBox("启用共振 A"); self.chk_r1.setChecked(True)
        self.chk_r1.stateChanged.connect(lambda _: self._schedule())
        self.fr1    = self._spin(10, 950, 150, 0, "Hz", 10)
        self.gain_r1 = self._spin(0, 200, 10, 1, "×", 1)
        self.qr1    = self._spin(1, 200, 10, 1, "Q", 1)
        pl.addWidget(self._group("机架共振 A",
            [("频率:", self.fr1), ("增益:", self.gain_r1), ("Q:", self.qr1)],
            extras=[self.chk_r1]))

        self.chk_r2 = QCheckBox("启用共振 B"); self.chk_r2.setChecked(True)
        self.chk_r2.stateChanged.connect(lambda _: self._schedule())
        self.fr2    = self._spin(10, 950, 320, 0, "Hz", 10)
        self.gain_r2 = self._spin(0, 200,  8, 1, "×", 1)
        self.qr2    = self._spin(1, 200,  8, 1, "Q", 1)
        pl.addWidget(self._group("机架共振 B",
            [("频率:", self.fr2), ("增益:", self.gain_r2), ("Q:", self.qr2)],
            extras=[self.chk_r2]))

        # ── 共振分布参数（checkbox 放在框内）──
        res_dist_box = QGroupBox("共振分布参数")
        rd_layout = QGridLayout(res_dist_box)
        rd_layout.setContentsMargins(5, 8, 5, 5); rd_layout.setSpacing(3)
        self.chk_res_dist = QCheckBox("启用分布模式（多峰）")
        self.chk_res_dist.setChecked(False)
        self.chk_res_dist.stateChanged.connect(lambda _: self._schedule())
        rd_layout.addWidget(self.chk_res_dist, 0, 0, 1, 2)
        self.n_res_peaks  = self._ispin(2, 10, 3)
        self.f_res_spread = self._spin(1, 200, 20, 0, "Hz", 5)
        self.seed_res     = self._ispin(0, 999, 0)
        for i, (lbl, w) in enumerate(
                [("峰数:", self.n_res_peaks),
                 ("展宽:", self.f_res_spread),
                 ("种子:", self.seed_res)], 1):
            lbl_w = QLabel(lbl); lbl_w.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            rd_layout.addWidget(lbl_w, i, 0)
            rd_layout.addWidget(w,    i, 1)
            w.setEnabled(False)
        self.chk_res_dist.stateChanged.connect(
            lambda s: [w.setEnabled(bool(s))
                       for w in (self.n_res_peaks, self.f_res_spread, self.seed_res)])
        pl.addWidget(res_dist_box)

        # 全局噪声参数
        self.chk_noise_en = QCheckBox("启用噪声")
        self.chk_noise_en.setChecked(True)
        self.chk_noise_en.stateChanged.connect(lambda _: self._schedule())
        self.white_rms  = self._spin(1, 2000,  20, 0, "dps", 5)
        self.perlin_rms = self._spin(0,  500,   8, 0, "dps", 2)
        self.perlin_oct = self._ispin(1, 8, 4)
        pl.addWidget(self._group("全局噪声参数", [
            ("白噪声:", self.white_rms),
            ("Perlin:", self.perlin_rms),
            ("倍频程:", self.perlin_oct),
        ], extras=[self.chk_noise_en]))

        # ── 打杆曲线控制（GroupBox）──
        stick_box = QGroupBox("打杆曲线控制")
        sb_layout = QVBoxLayout(stick_box)
        sb_layout.setContentsMargins(5, 8, 5, 5); sb_layout.setSpacing(3)
        mode_row = QHBoxLayout()
        self.btn_stick_add = QPushButton("✚ 新增")
        self.btn_stick_del = QPushButton("✖ 删除")
        self.btn_stick_adj = QPushButton("⇄ 调整")
        self.btn_stick_clr = QPushButton("清空")
        for btn in (self.btn_stick_add, self.btn_stick_del,
                    self.btn_stick_adj, self.btn_stick_clr):
            btn.setFixedHeight(22); mode_row.addWidget(btn)
        for btn, m in [(self.btn_stick_add, 'add'),
                       (self.btn_stick_del, 'del'),
                       (self.btn_stick_adj, 'adj')]:
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, mode=m: self._set_stick_mode(mode))
        self.btn_stick_add.setChecked(True)
        self.btn_stick_clr.clicked.connect(self._clear_sticks)
        sb_layout.addLayout(mode_row)
        btn_upd = QPushButton("↺ 更新全局状态"); btn_upd.setFixedHeight(22)
        btn_upd.clicked.connect(lambda: self._do_update())
        sb_layout.addWidget(btn_upd)
        pl.addWidget(stick_box)

        note = QLabel(
            "<small>"
            "<span style='color:#7ac4e0'>■</span> PT1 虚线=单独  实线=+Notch<br>"
            "<span style='color:#e8394a'>■</span> LKF 同上<br>"
            "<span style='color:#f5f5ff'>■</span> 打杆（注入滤波）<br>"
            "<span style='color:#aaa'>绿带=0–30 Hz | 时域 ±400 dps</span>"
            "</small>"
        )
        note.setWordWrap(True); note.setStyleSheet("color:#a0b8c8; padding:3px;")
        pl.addWidget(note)
        pl.addStretch()

        # ── 右侧画布 ──────────────────────────────────
        self.fig    = Figure(facecolor="#080c14")
        self.canvas = FigureCanvas(self.fig)
        toolbar = NavToolbar(self.canvas, self)
        self.nav_toolbar = toolbar
        toolbar.setStyleSheet("background:#1a1a2e; color:#ccccdd; font-size:8pt;")
        canvas_col = QVBoxLayout()
        canvas_col.setContentsMargins(0, 0, 0, 0); canvas_col.setSpacing(2)
        canvas_col.addWidget(toolbar); canvas_col.addWidget(self.canvas)
        ml.addWidget(pane); ml.addLayout(canvas_col, stretch=1)

    # ── 轴切换 ────────────────────────────────────────
    def _toggle_x(self, checked):
        self._log_xaxis = checked
        self.btn_x.setText("频率轴: 对数" if checked else "频率轴: 线性")
        self._do_update()

    def _toggle_y(self, checked):
        self._log_yaxis = checked
        self.btn_y.setText("幅度: dB" if checked else "幅度: 线性")
        self._do_update()

    # ── 同步 LKF 截止频率 ────────────────────────────
    def _sync_lkf_to_pt1(self):
        """Binary search r_meas until LKF -3dB freq ≈ PT1 fc."""
        fc = self.fc_pt1.value(); w_t = 2 * np.pi * fc / FS; tgt = 1.0 / np.sqrt(2)
        lo, hi = 1e-5, 1e5
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            b_l, a_l = lkf_coeffs(self.q_omega.value(), self.q_bias.value(), mid, FS)
            _, H = freqz(b_l, a_l, worN=[w_t])
            if abs(H[0]) > tgt: lo = mid
            else:               hi = mid
        self.r_meas.blockSignals(True)
        self.r_meas.setValue(float(np.clip(np.sqrt(lo * hi), 0.05, 500)))
        self.r_meas.blockSignals(False)
        self._do_update()

    # ── 打杆交互 ──────────────────────────────────────
    def _set_stick_mode(self, mode):
        """Switch stick mode. Does NOT toggle NavToolbar (user does that manually)."""
        self._stick_mode = mode
        for btn, m in [(self.btn_stick_add, 'add'),
                       (self.btn_stick_del, 'del'),
                       (self.btn_stick_adj, 'adj')]:
            btn.setChecked(m == mode)
        self._do_update()

    def _clear_sticks(self):
        self._stick_pts   = []
        self._anchor_y    = [0.0, 0.0]
        self._drag_idx    = None
        self._drag_is_anchor = False
        self._do_update()

    def _build_all_pts(self):
        """Merge anchor end-points with user control points (sorted by t)."""
        anchors = [(0.0, self._anchor_y[0]), (float(N_SECONDS), self._anchor_y[1])]
        # Remove user pts too close to anchor t (avoid duplicate knots)
        eps = 0.05
        inner = [(t, y) for t, y in self._stick_pts
                 if eps < t < N_SECONDS - eps]
        return sorted(anchors + inner, key=lambda p: p[0])

    def _compute_stick_signal(self):
        """CubicSpline through all control points across [0, N_SECONDS]."""
        from scipy.interpolate import CubicSpline
        pts = self._build_all_pts()
        t_k = [p[0] for p in pts]; y_k = [p[1] for p in pts]
        try:
            cs     = CubicSpline(t_k, y_k)
            t_full = np.arange(N_SIG) / FS
            return cs(t_full)
        except Exception:
            return np.zeros(N_SIG)

    def _on_canvas_drag(self, event):
        """Drag to relocate a control point in 'adj' mode (debounced)."""
        if self.nav_toolbar.mode:
            return
        if self._stick_mode != 'adj' or self._drag_idx is None:
            return
        ax5 = self._last_ax5
        if ax5 is None: return
        x, y = event.xdata, event.ydata
        if x is None or y is None: return
        if self._drag_is_anchor:
            # Anchor points: only y can move
            self._anchor_y[self._drag_anchor_idx] = float(y)
        else:
            idx = self._drag_idx
            if 0 <= idx < len(self._stick_pts):
                self._stick_pts[idx] = (float(x), float(y))
        self._stick_timer.start()

    def _on_canvas_release(self, event):
        """Finalize drag: sort user pts, clear drag state."""
        if self._drag_idx is not None and not self._drag_is_anchor:
            self._stick_pts.sort(key=lambda p: p[0])
        self._drag_idx = None
        self._drag_is_anchor = False
        self._drag_anchor_idx = None
        self._do_update()

    def _on_canvas_click(self, event):
        """Stick interaction: left click per mode; right click removes in range."""
        if self.nav_toolbar.mode:   # zoom/pan active — skip
            return
        ax5 = self._last_ax5
        if ax5 is None or not ax5.in_axes(event): return
        x, y = event.xdata, event.ydata
        if x is None or y is None: return
        mode = self._stick_mode

        if event.button == 1:
            if mode == 'add':
                eps = 0.05
                if x < eps:    self._anchor_y[0] = float(y)
                elif x > N_SECONDS - eps: self._anchor_y[1] = float(y)
                else:
                    self._stick_pts.append((float(x), float(y)))
                    self._stick_pts.sort(key=lambda p: p[0])
                self._do_update()
            elif mode == 'del':
                self._try_delete_near(ax5, x)
            elif mode == 'adj':
                # Check if near an anchor
                xlim = ax5.get_xlim()
                view = (xlim[1] - xlim[0]) or N_SECONDS
                a_zone = view / 20   # anchor pick zone is 1/20 (larger tolerance)
                if abs(x - 0.0) <= a_zone:
                    self._drag_idx = 0; self._drag_is_anchor = True; self._drag_anchor_idx = 0
                elif abs(x - float(N_SECONDS)) <= a_zone:
                    self._drag_idx = 0; self._drag_is_anchor = True; self._drag_anchor_idx = 1
                elif self._stick_pts:
                    ylim  = ax5.get_ylim(); scale = max(ylim[1] - ylim[0], 1.0)
                    self._drag_idx = min(
                        range(len(self._stick_pts)),
                        key=lambda i: (self._stick_pts[i][0]-x)**2
                                     + ((self._stick_pts[i][1]-y)/scale)**2)
                    self._drag_is_anchor = False

        elif event.button == 3:
            self._try_delete_near(ax5, x)

    def _try_delete_near(self, ax5, x):
        """Remove nearest user control point within 1/200 of current view. Anchors immune."""
        if not self._stick_pts: return
        xlim = ax5.get_xlim()
        zone = (xlim[1] - xlim[0]) / 200.0
        dists = [(abs(p[0] - x), i) for i, p in enumerate(self._stick_pts)]
        dists.sort()
        if dists[0][0] <= zone:
            self._stick_pts.pop(dists[0][1])
            self._do_update()

    # ── 绘图核心 ─────────────────────────────────────────────────
    def _do_update(self):
        # 保存时域轴缩放状态
        if self._last_ax5 is not None:
            try:
                self._ax5_xlim = list(self._last_ax5.get_xlim())
                self._ax5_ylim = list(self._last_ax5.get_ylim())
            except Exception: pass

        fs = FS

        # ── 滤波器系数 ──
        b_pt1, a_pt1 = pt1_coeffs(self.fc_pt1.value(), fs)
        b_lkf, a_lkf = lkf_coeffs(
            self.q_omega.value(), self.q_bias.value(), self.r_meas.value(), fs)
        b_n1, a_n1 = notch_coeffs(self.f_n1.value(), self.q_n1.value(), fs)
        b_n2, a_n2 = notch_coeffs(self.f_n2.value(), self.q_n2.value(), fs)
        use_n1 = self.n1_en.isChecked()
        use_n2 = self.n2_en.isChecked()

        # ── 噪声生成（缓存）──
        nk = (self.chk_noise_en.isChecked(),
              self.white_rms.value(), self.perlin_rms.value(), self.perlin_oct.value(),
              self.fr1.value(), self.gain_r1.value(), self.qr1.value(),
              self.chk_r1.isChecked(),
              self.fr2.value(), self.gain_r2.value(), self.qr2.value(),
              self.chk_r2.isChecked(),
              self.chk_res_dist.isChecked(),
              self.n_res_peaks.value(), self.f_res_spread.value(), self.seed_res.value())
        if self._noise_key != nk:
            rng = np.random.default_rng(42)
            w   = rng.standard_normal(N_SIG) * self.white_rms.value()
            p   = perlin_noise_1d(N_SIG, octaves=self.perlin_oct.value()) \
                  * self.perlin_rms.value()
            if self.chk_res_dist.isChecked():
                n_pk = self.n_res_peaks.value()
                f_sp = self.f_res_spread.value()
                s_rd = self.seed_res.value()
                ra = resonance_dist(w, self.fr1.value(), self.gain_r1.value(),
                                    self.qr1.value(), n_pk, f_sp, s_rd, fs) \
                     if self.chk_r1.isChecked() else np.zeros(N_SIG)
                rb = resonance_dist(w, self.fr2.value(), self.gain_r2.value(),
                                    self.qr2.value(), n_pk, f_sp, s_rd, fs) \
                     if self.chk_r2.isChecked() else np.zeros(N_SIG)
            else:
                ra = resonance(w, self.fr1.value(), self.gain_r1.value(),
                               self.qr1.value(), fs) if self.chk_r1.isChecked() else np.zeros(N_SIG)
                rb = resonance(w, self.fr2.value(), self.gain_r2.value(),
                               self.qr2.value(), fs) if self.chk_r2.isChecked() else np.zeros(N_SIG)
            self._noise_wp    = w + p           # white + perlin only
            self._noise_res   = ra + rb          # resonance only
            self._noise_cache = self._noise_wp + self._noise_res
            self._noise_key   = nk
        # Noise enable: only suppresses white+perlin; resonance always active
        _wp = self._noise_wp if self.chk_noise_en.isChecked() else np.zeros(N_SIG)
        signal = _wp + self._noise_res

        # ── 打杆信号（贯穿全程）──
        s_stick   = self._compute_stick_signal()
        signal_ws = signal + s_stick   # combined input to filters

        # ── 缓存 filter coeffs（供快速局部更新用）──
        self._td_cache = (signal, b_pt1, a_pt1, b_lkf, a_lkf,
                          use_n1, b_n1, a_n1, use_n2, b_n2, a_n2)

        # ── 滤波 ──
        def apply_notch(sig):
            if use_n1: sig = lfilter(b_n1, a_n1, sig)
            if use_n2: sig = lfilter(b_n2, a_n2, sig)
            return sig

        out_pt1   = lfilter(b_pt1, a_pt1, signal)
        out_pt1_n = apply_notch(out_pt1.copy())
        out_lkf   = lfilter(b_lkf, a_lkf, signal)
        out_lkf_n = apply_notch(out_lkf.copy())
        out_pt1_n_td = apply_notch(lfilter(b_pt1, a_pt1, signal_ws))
        out_lkf_n_td = apply_notch(lfilter(b_lkf, a_lkf, signal_ws))

        # ── 频响 ──
        f_ax = (np.logspace(0, np.log10(fs / 2), 1200) if self._log_xaxis
                else np.linspace(1, fs / 2, 2400))
        w_ax = 2 * np.pi * f_ax / fs

        _, H_pt1 = freqz(b_pt1, a_pt1, worN=w_ax)
        _, H_lkf = freqz(b_lkf, a_lkf, worN=w_ax)
        _, H_n1  = freqz(b_n1,  a_n1,  worN=w_ax)
        _, H_n2  = freqz(b_n2,  a_n2,  worN=w_ax)

        Hn = np.ones(len(w_ax), dtype=complex)
        if use_n1: Hn *= H_n1
        if use_n2: Hn *= H_n2
        H_pt1_n = H_pt1 * Hn
        H_lkf_n = H_lkf * Hn

        def gd_ms(H):
            ph = -np.unwrap(np.angle(H))
            dw = np.gradient(w_ax)
            return np.gradient(ph) / (dw + 1e-20) / fs * 1000.0

        gd_pt1  = gd_ms(H_pt1);  gd_lkf  = gd_ms(H_lkf)
        gd_pt1n = gd_ms(H_pt1_n); gd_lkfn = gd_ms(H_lkf_n)

        # ── PSD ──
        nperseg = min(4096, N_SIG // 8)
        f_w, P_in   = welch(signal_ws,   fs, nperseg=nperseg)  # 输入（含打杆）
        _,   P_pt1n = welch(out_pt1_n_td, fs, nperseg=nperseg)  # PT1+N filtered
        _,   P_lkfn = welch(out_lkf_n_td, fs, nperseg=nperseg)  # LKF+N filtered
        # baseline noise-only (thin dashed reference)
        _,   P_pt1_ref = welch(out_pt1_n, fs, nperseg=nperseg)
        _,   P_lkf_ref = welch(out_lkf_n, fs, nperseg=nperseg)
        mask = (f_w >= 0.5) & (f_w <= 700)

        # ── 时域（抽取显示）──
        dec = 10
        t   = np.arange(N_SIG)[::dec] / fs
        sp  = signal_ws[::dec]          # 输入（噪声+打杆）
        sk  = s_stick[::dec]            # 纯打杆
        pp  = out_pt1_n_td[::dec]       # PT1 响应
        lp  = out_lkf_n_td[::dec]       # LKF 响应

        # ══════════════════════════════════════════════
        #  绘图
        # ══════════════════════════════════════════════
        solo = self.solo_combo.currentIndex()
        self.fig.clear()
        T = self._DARK if self._dark_mode else self._LIGHT
        self.fig.set_facecolor(T['fig'])
        if solo == 0:
            gs = GridSpec(5, 1, figure=self.fig,
                          height_ratios=[3.0, 2.0, 1.4, 2.8, 1.4],
                          hspace=0.42,
                          left=0.065, right=0.975, top=0.965, bottom=0.045)
            ax1 = self.fig.add_subplot(gs[0])
            ax2 = self.fig.add_subplot(gs[1])
            ax3 = self.fig.add_subplot(gs[2])
            ax4 = self.fig.add_subplot(gs[3])
            ax5 = self.fig.add_subplot(gs[4])
        else:
            _ax = self.fig.add_subplot(1, 1, 1)
            self.fig.subplots_adjust(left=0.07, right=0.975, top=0.955, bottom=0.085)
            ax1 = _ax if solo == 1 else None
            ax2 = _ax if solo == 2 else None
            ax3 = _ax if solo == 3 else None
            ax4 = _ax if solo == 4 else None
            ax5 = _ax if solo == 5 else None

        C_PT1 = T['pt1']; C_LKF = T['lkf']; C_GRID = T['grid']

        for ax in filter(None, (ax1, ax2, ax3, ax4, ax5)):
            ax.set_facecolor(T['ax'])
            ax.grid(True, which="both", color=C_GRID, linewidth=0.55)
            ax.tick_params(colors=T['tick'], labelsize=7.5)
            for s in ax.spines.values(): s.set_edgecolor(T['spine'])

        xsc  = "log" if self._log_xaxis else "linear"
        xlim = (1 if self._log_xaxis else 0, fs / 2)

        def bands(ax, bode=True):
            lo = 1 if (self._log_xaxis and bode) else 0
            ax.axvspan(lo, 30,  alpha=0.09, color=T['band'], zorder=0)
            ax.axvline(500, color=T['xmark'], lw=0.6, ls="--", alpha=0.50)

        # ── 1. 幅频 ──────────────────────────────────
        if ax1 is not None:
            if self._log_yaxis:
                mg = lambda h: 20 * np.log10(np.abs(h) + 1e-15)
                ax1.set_ylim(-65, 8); ax1.axhline(-3, color=T['href'], lw=0.7, ls=":")
                ylabel_mag = "Gain (dB)"
            else:
                mg = np.abs
                ax1.set_ylim(-0.05, 1.15); ax1.axhline(1.0, color=T['href'], lw=0.7, ls=":")
                ylabel_mag = "Gain (×)"
            ax1.plot(f_ax, mg(H_pt1),   color=C_PT1, lw=0.6, ls="--", alpha=0.55,
                     label=f"PT1 {self.fc_pt1.value():.0f}Hz")
            ax1.plot(f_ax, mg(H_lkf),   color=C_LKF, lw=0.6, ls="--", alpha=0.55, label="LKF")
            ax1.plot(f_ax, mg(H_pt1_n), color=C_PT1, lw=1.3, label="PT1+Notch")
            ax1.plot(f_ax, mg(H_lkf_n), color=C_LKF, lw=1.3, label="LKF+Notch")
            bands(ax1); ax1.set_xscale(xsc); ax1.set_xlim(*xlim)
            ax1.set_ylabel(ylabel_mag, color=T['label'], fontsize=8)
            ax1.set_title("陀螺滤波器分析仪  PT1 vs 2-state LKF (+Notch)  |  fs=2kHz",
                          color=T['title'], fontsize=9)
            ax1.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                       framealpha=0.85, loc="lower left", ncol=2)

        # ── 2. 相频 ──────────────────────────────────
        if ax2 is not None:
            ax2.plot(f_ax, np.angle(H_pt1,  deg=True), color=C_PT1, lw=0.6, ls="--", alpha=0.55)
            ax2.plot(f_ax, np.angle(H_lkf,  deg=True), color=C_LKF, lw=0.6, ls="--", alpha=0.55)
            ax2.plot(f_ax, np.angle(H_pt1_n, deg=True), color=C_PT1, lw=1.2, label="PT1+N")
            ax2.plot(f_ax, np.angle(H_lkf_n, deg=True), color=C_LKF, lw=1.2, label="LKF+N")
            bands(ax2); ax2.axhline(0, color=T['href'], lw=0.7)
            for deg in (-90, -180): ax2.axhline(deg, color=T['href2'], lw=0.5, ls=":")
            ax2.set_xscale(xsc); ax2.set_xlim(*xlim)
            ax2.set_ylim(-188, 95); ax2.set_yticks([-180, -90, 0, 90])
            ax2.set_ylabel("Phase (°)", color=T['label'], fontsize=8)
            ax2.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                       framealpha=0.85, loc="lower left", ncol=2)

        # ── 3. 群延迟 ────────────────────────────────
        if ax3 is not None:
            clip = 15.0
            ax3.plot(f_ax, np.clip(gd_pt1,  -clip, clip), color=C_PT1, lw=0.75, ls="--", alpha=0.55)
            ax3.plot(f_ax, np.clip(gd_lkf,  -clip, clip), color=C_LKF, lw=0.75, ls="--", alpha=0.55)
            ax3.plot(f_ax, np.clip(gd_pt1n, -clip, clip), color=C_PT1, lw=0.6, label="PT1+N")
            ax3.plot(f_ax, np.clip(gd_lkfn, -clip, clip), color=C_LKF, lw=0.6, label="LKF+N")
            bands(ax3); ax3.axhline(0, color=T['href'], lw=0.7)
            ax3.set_xscale(xsc); ax3.set_xlim(*xlim)
            ax3.set_ylabel("Grp Dly (ms)", color=T['label'], fontsize=8)
            ax3.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                       framealpha=0.85, loc="upper right", ncol=2)

        # ── 4. PSD ──────────────────────────────────
        if ax4 is not None:
            psd_plot = ax4.semilogy if self._log_yaxis else ax4.plot
            psd_plot(f_w[mask], P_in[mask],     color=T['noise_psd'], lw=0.6,  label="输入+打杆")
            psd_plot(f_w[mask], P_pt1_ref[mask], color=C_PT1, lw=0.5, ls="--", alpha=0.35)
            psd_plot(f_w[mask], P_pt1n[mask],   color=C_PT1, lw=1.2,  label="PT1+N")
            psd_plot(f_w[mask], P_lkf_ref[mask], color=C_LKF, lw=0.5, ls="--", alpha=0.35)
            psd_plot(f_w[mask], P_lkfn[mask],   color=C_LKF, lw=1.2,  label="LKF+N")
            for fr, col in [(self.fr1.value(), T['lkf']), (self.fr2.value(), T['pt1'])]:  # fr1=lkf color, fr2=pt1 color
                ax4.axvline(fr, color=col, lw=0.65, ls=":", alpha=0.8)
            ax4.axvspan(0, 30, alpha=0.09, color=T['band'], zorder=0)
            ax4.axvline(500, color=T['xmark'], lw=0.6, ls="--", alpha=0.50)
            ax4.set_xlim(0, 720)
            ax4.set_ylabel("PSD (dps²/Hz)" + (" — log" if self._log_yaxis else ""),
                           color=T['label'], fontsize=8)
            ax4.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                       framealpha=0.85, ncol=3, loc="upper right")

        # ── 5. 时域波形 ──────────────────────────────
        if ax5 is not None:
            # 输入（噪声+打杆）灰色背景线
            ax5.plot(t, sp, color=T['noise'], lw=0.28, alpha=0.55, label="输入")
            # 纯打杆曲线（如有）
            has_stick = np.any(np.abs(sk) > 1e-9)
            if has_stick:
                ax5.plot(t, sk, color=T['stick'], lw=0.85, alpha=0.85, label="打杆")
            # 锚点散点（正方形，区别于普通控制点）
            ax5.scatter([0.0, float(N_SECONDS)],
                        [self._anchor_y[0], self._anchor_y[1]],
                        color=T['dot'], s=38, marker='s', zorder=7)
            # 用户控制点散点（圆形）
            if self._stick_pts:
                inner = [(t_, y_) for t_, y_ in self._stick_pts
                         if 0.05 < t_ < N_SECONDS - 0.05]
                if inner:
                    ax5.scatter([p[0] for p in inner], [p[1] for p in inner],
                                color=T['dot'], s=22, zorder=6)
            # 删除模式：1/200 视图宽度区域（含锚点保护不显示）
            if self._stick_mode == 'del' and self._stick_pts:
                zone = (self._ax5_xlim[1] - self._ax5_xlim[0]) / 200.0
                for pt in self._stick_pts:
                    ax5.axvspan(pt[0] - zone/2, pt[0] + zone/2,
                                alpha=0.15, color=T['dot'], zorder=2)
            # 滤波输出
            ax5.plot(t, pp, color=C_PT1, lw=0.65, label="PT1+N")
            ax5.plot(t, lp, color=C_LKF, lw=0.65, label="LKF+N")
            # 模式提示
            _hint = {"add": "✚ 新增", "del": "✖ 删除(1/200)", "adj": "⇄ 调整"}
            ax5.set_title(f"时域  [{_hint.get(self._stick_mode, '')}]  Y轴手动缩放",
                          color=T['label'], fontsize=7.5, pad=2)
            ax5.set_xlabel("Time (s)", color=T['label'], fontsize=8)
            ax5.set_ylabel("dps",     color=T['label'], fontsize=8)
            ax5.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                       framealpha=0.85, loc="upper right", ncol=4)
            ax5.set_xlim(self._ax5_xlim)
            ax5.set_ylim(self._ax5_ylim)
            self._last_ax5 = ax5

        self.canvas.draw()

    def _toggle_theme(self, checked):
        """Switch between dark (Mirror's Edge) and light themes."""
        self._dark_mode = not checked
        T = self._DARK if self._dark_mode else self._LIGHT
        self.nav_toolbar.setStyleSheet(T['tbar'])
        self.btn_theme.setText("☀ 亮色主题" if self._dark_mode else "🌙 深色主题")
        from PyQt5.QtGui import QPalette, QColor
        pal = QPalette()
        entries = [
            (QPalette.Window,          T['pal_win']),
            (QPalette.WindowText,      T['pal_txt']),
            (QPalette.Base,            T['pal_base']),
            (QPalette.AlternateBase,   T['pal_win']),
            (QPalette.Text,            T['pal_txt']),
            (QPalette.Button,          T['pal_btn']),
            (QPalette.ButtonText,      T['pal_txt']),
            (QPalette.Highlight,       T['pal_hl']),
            (QPalette.HighlightedText, '#ffffff'),
        ]
        for role, color in entries:
            pal.setColor(role, QColor(color))
        QApplication.instance().setPalette(pal)
        self._do_update()

    def update_plots(self):
        self._schedule()


def main():
    import matplotlib
    matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    from PyQt5.QtGui import QPalette, QColor
    pal = QPalette()
    for role, color in [
        (QPalette.Window,          "#080c16"),
        (QPalette.WindowText,      "#e0e0f0"),
        (QPalette.Base,            "#060a12"),
        (QPalette.AlternateBase,   "#080c16"),
        (QPalette.Text,            "#e0e0f0"),
        (QPalette.Button,          "#0d1e38"),
        (QPalette.ButtonText,      "#e0e0f0"),
        (QPalette.Highlight,       "#a01020"),
        (QPalette.HighlightedText, "#ffffff"),
    ]:
        pal.setColor(role, QColor(color))
    app.setPalette(pal)
    win = FilterAnalyzer()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
