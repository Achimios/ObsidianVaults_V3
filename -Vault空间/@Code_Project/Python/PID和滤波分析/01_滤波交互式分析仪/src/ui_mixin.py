# ui_mixin.py — 左侧参数面板构建 + 小工具函数
# _spin / _ispin / _group / _schedule / _build_ui

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QDoubleSpinBox, QGroupBox,
    QPushButton, QCheckBox, QSpinBox, QScrollArea, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavToolbar,
)
from matplotlib.figure import Figure
from constants import FS, N_SECONDS, N_SIG


class _FocusDSpin(QDoubleSpinBox):
    """Ignores wheel events unless focused — prevents accidental param change."""
    def wheelEvent(self, e):
        if self.hasFocus(): super().wheelEvent(e)
        else: e.ignore()


class _FocusISpin(QSpinBox):
    """Ignores wheel events unless focused."""
    def wheelEvent(self, e):
        if self.hasFocus(): super().wheelEvent(e)
        else: e.ignore()


class UIMixin:

        def _spin(self, lo, hi, val, decs=1, suffix="", step=None):
            sb = _FocusDSpin()
            sb.setRange(lo, hi); sb.setValue(val); sb.setDecimals(decs)
            if suffix: sb.setSuffix(f" {suffix}")
            if step:   sb.setSingleStep(step)
            sb.valueChanged.connect(lambda _: self._schedule())
            return sb


        def _ispin(self, lo, hi, val):
            sb = _FocusISpin()
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

        def _toggle_solo(self, idx):
            """Enter/exit/switch solo display mode for axis idx."""
            if self._solo_idx == idx:
                # Exit solo — restore cached state
                for i, chk in enumerate(self.chk_show):
                    chk.blockSignals(True)
                    chk.setChecked(self._solo_cache[i])
                    chk.setEnabled(True)
                    chk.blockSignals(False)
                for btn in self.btn_solo:
                    btn.setChecked(False)
                self._solo_idx = None; self._solo_cache = None
            else:
                # Enter or switch solo
                if self._solo_idx is None:
                    self._solo_cache = [chk.isChecked() for chk in self.chk_show]
                self._solo_idx = idx
                for i, (chk, btn) in enumerate(zip(self.chk_show, self.btn_solo)):
                    chk.blockSignals(True)
                    chk.setChecked(i == idx)
                    chk.setEnabled(False)
                    chk.blockSignals(False)
                    btn.setChecked(i == idx)
            self._schedule()


        def _build_sine_item(self, n, t0=10.0, t1=20.0):
            """Create UI for one sine injection entry. Returns item dict."""
            box = QGroupBox(f"周期波_{n}")
            lay = QVBoxLayout(box)
            lay.setContentsMargins(5, 6, 5, 4); lay.setSpacing(2)
            btn_row = QHBoxLayout()
            btn_dup = QPushButton("复制"); btn_dup.setFixedHeight(20)
            btn_rng = QPushButton("⇄ 范围"); btn_rng.setFixedHeight(20); btn_rng.setCheckable(True)
            btn_del = QPushButton("✖ 删除"); btn_del.setFixedHeight(20)
            btn_row.addWidget(btn_dup); btn_row.addWidget(btn_rng); btn_row.addWidget(btn_del)
            lay.addLayout(btn_row)
            # t0/t1 side-by-side row
            t_row = QHBoxLayout()
            lw_t0 = QLabel("t起:"); lw_t0.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_t0.setFixedWidth(28)
            lw_t1 = QLabel("t止:"); lw_t1.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_t1.setFixedWidth(28)
            t0_spin = self._spin(0, N_SECONDS, round(t0, 1), 1, "s", 0.5)
            t1_spin = self._spin(0, N_SECONDS, round(t1, 1), 1, "s", 0.5)
            t_row.addWidget(lw_t0); t_row.addWidget(t0_spin)
            t_row.addWidget(lw_t1); t_row.addWidget(t1_spin)
            lay.addLayout(t_row)
            freq  = self._spin(1, 500, 20, 0, "Hz", 5)
            amp   = self._spin(1, 1000, 100, 0, "dps", 10)
            trans = self._spin(0, 0.5, 0.1, 2, "", 0.05)
            for lbl, w in [("频率:", freq), ("幅度:", amp), ("过渡区:", trans)]:
                row = QHBoxLayout()
                lw = QLabel(lbl); lw.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw.setFixedWidth(50)
                row.addWidget(lw); row.addWidget(w); lay.addLayout(row)
            w_rms = self._spin(0, 500, 0, 0, "dps", 5)
            p_rms = self._spin(0, 200, 0, 0, "dps", 2)
            p_oct = self._ispin(1, 8, 4)
            for lbl, w in [("白噪音:", w_rms), ("Perlin:", p_rms), ("倍频程:", p_oct)]:
                row = QHBoxLayout()
                lw = QLabel(lbl); lw.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw.setFixedWidth(50)
                row.addWidget(lw); row.addWidget(w); lay.addLayout(row)
            item = {'box': box, 'freq': freq, 'amp': amp, 'trans': trans,
                    't0': t0_spin, 't1': t1_spin,
                    'w_rms': w_rms, 'p_rms': p_rms, 'p_oct': p_oct, 'btn_rng': btn_rng}
            btn_del.clicked.connect(lambda: self._remove_sine_item(item))
            btn_dup.clicked.connect(lambda: self._duplicate_sine_item(item))
            btn_rng.clicked.connect(lambda: self._toggle_sine_range(item))
            return item


        def _add_sine_injection(self):
            """Append a new sine injection entry to the panel."""
            ax5 = getattr(self, '_last_axes', [None]*5)[4]
            if ax5 is not None:
                xlim = ax5.get_xlim(); span = xlim[1] - xlim[0]
                t0 = round(xlim[0] + span / 3, 1)
                t1 = round(xlim[0] + 2 * span / 3, 1)
            else:
                t0, t1 = 10.0, 20.0
            item = self._build_sine_item(len(self._sine_items) + 1, t0=t0, t1=t1)
            self._sine_items.append(item)
            self._sine_layout.addWidget(item['box'])
            QTimer.singleShot(0, self._left_pane.adjustSize)
            self._schedule()


        def _remove_sine_item(self, item):
            """Remove a sine injection entry and renumber remaining."""
            if item in self._sine_items:
                self._sine_items.remove(item)
                item['box'].setParent(None)
                item['box'].deleteLater()
                for i, it in enumerate(self._sine_items):
                    it['box'].setTitle(f"周期波_{i + 1}")
                QTimer.singleShot(0, self._left_pane.adjustSize)
                self._schedule()


        def _duplicate_sine_item(self, src):
            """Duplicate a sine injection entry with identical parameters."""
            item = self._build_sine_item(len(self._sine_items) + 1)
            item['freq'].setValue(src['freq'].value())
            item['amp'].setValue(src['amp'].value())
            item['trans'].setValue(src['trans'].value())
            item['t0'].setValue(src['t0'].value())
            item['t1'].setValue(src['t1'].value())
            item['w_rms'].setValue(src['w_rms'].value())
            item['p_rms'].setValue(src['p_rms'].value())
            item['p_oct'].setValue(src['p_oct'].value())
            self._sine_items.append(item)
            src_idx = self._sine_layout.indexOf(src['box'])
            self._sine_layout.insertWidget(src_idx + 1, item['box'])
            QTimer.singleShot(0, self._left_pane.adjustSize)
            self._schedule()


        def _toggle_sine_range(self, item):
            """Exclusive: deactivate stick mode + other sine range buttons."""
            if item['btn_rng'].isChecked():
                # Deactivate stick mode buttons
                self._stick_mode = None
                for btn in (self.btn_stick_add, self.btn_stick_del, self.btn_stick_adj):
                    btn.setChecked(False)
            # Deactivate all other sine range buttons
            for it in self._sine_items:
                if it is not item:
                    it['btn_rng'].setChecked(False)


        def _build_ui(self):
            central = QWidget(); self.setCentralWidget(central)
            ml = QHBoxLayout(central)
            ml.setContentsMargins(5, 5, 5, 5); ml.setSpacing(6)

            # ── 左侧参数面板 ──────────────────────
            pane = QWidget()
            pane.setFixedWidth(295)
            self._left_pane = pane
            pl = QVBoxLayout(pane); pl.setSpacing(4)

            # 轴切换
            btn_row = QHBoxLayout()
            self.btn_x = QPushButton("频率轴: 线性"); self.btn_x.setCheckable(True)
            self.btn_x.clicked.connect(self._toggle_x)
            self.btn_y = QPushButton("幅度: 线性");   self.btn_y.setCheckable(True)
            self.btn_y.clicked.connect(self._toggle_y)
            btn_row.addWidget(self.btn_x); btn_row.addWidget(self.btn_y)
            pl.addLayout(btn_row)

            # 图层显示
            show_grp = QGroupBox('图层显示'); show_lay = QGridLayout(show_grp)
            show_lay.setSpacing(2)
            _show_names = ["① 幅频", "② 相频", "③ 群延迟", "④ PSD", "⑤ 时域"]
            self.chk_show = []; self.btn_solo = []
            for _i, _nm in enumerate(_show_names):
                _chk = QCheckBox(_nm)
                _chk.setChecked(True)
                _chk.stateChanged.connect(lambda _: self._schedule())
                self.chk_show.append(_chk)
                show_lay.addWidget(_chk, _i, 0)
                _sbtn = QPushButton("独"); _sbtn.setFixedWidth(26); _sbtn.setCheckable(True)
                _sbtn.clicked.connect(lambda _, i=_i: self._toggle_solo(i))
                self.btn_solo.append(_sbtn)
                show_lay.addWidget(_sbtn, _i, 1)
            pl.addWidget(show_grp)

            # 主题切换
            self.btn_theme = QPushButton("☀ 亮色主题")
            self.btn_theme.setCheckable(True)
            self.btn_theme.setToolTip("切换明暗色主题")
            self.btn_theme.clicked.connect(self._toggle_theme)
            pl.addWidget(self.btn_theme)

            # Toolbar 小工具说明
            tb_row = QHBoxLayout()
            _MSG_SUBPLOTS = (
                "⚙ 配置子图（Configure Subplots）\n\n"
                "调整画布内各子图的边距：\n"
                "• left/right/top/bottom — 图表区在画布内的占比（百分比）\n"
                "• hspace — 子图之间纵向间距\n"
                "• wspace — 子图之间横向间距\n\n"
                "使用方式：拖动滑块后立即生效（无需Apply）。\n\n"
                "⚠ 注意：每次参数变更触发刷新时，布局会被重建，\n"
                "此处调整将被还原。建议仅在截图前临时调整。"
            )
            _MSG_EDITAXIS = (
                "✒ 编辑轴（Edit Axis / Curves \u2014 Ctrl+E）\n\n"
                "点击后在弹出窗口中：\n"
                "• Axes — 修改坐标轴标题、范围、小数点位\n"
                "• Curves — 调整每条线的颜色、线宽、标签\n\n"
                "注意：修改将在下次 刷新时被换掉。"
            )
            _btn_sp = QPushButton("ⓘ 子图配置")
            _btn_sp.setFixedHeight(22)
            _btn_sp.setToolTip("查看 Configure Subplots 使用说明")
            _btn_sp.clicked.connect(
                lambda: QMessageBox.information(self, "Configure Subplots", _MSG_SUBPLOTS))
            _btn_ea = QPushButton("ⓘ 编辑坐标轴")
            _btn_ea.setFixedHeight(22)
            _btn_ea.setToolTip("查看 Edit Axis 使用说明")
            _btn_ea.clicked.connect(
                lambda: QMessageBox.information(self, "Edit Axis", _MSG_EDITAXIS))
            tb_row.addWidget(_btn_sp); tb_row.addWidget(_btn_ea)
            pl.addLayout(tb_row)

            # PT1
            self.chk_pt1_en = QCheckBox("启用 PT1"); self.chk_pt1_en.setChecked(True)
            self.chk_pt1_en.stateChanged.connect(lambda _: self._schedule())
            self.fc_pt1 = self._spin(10, 900, 100, 0, "Hz", 10)
            pl.addWidget(self._group("PT1 Filter", [("截止 fc:", self.fc_pt1)],
                                     extras=[self.chk_pt1_en]))

            # LKF
            self.chk_lkf_en = QCheckBox("启用 LKF"); self.chk_lkf_en.setChecked(True)
            self.chk_lkf_en.stateChanged.connect(lambda _: self._schedule())
            self.q_omega = self._spin(1e-4, 200,  1.0,  4, "",   0.1)
            self.q_bias  = self._spin(1e-9, 1e-3, 1e-4, 5, "",   1e-5)
            self.r_meas  = self._spin(0.05, 500,  0.5,  3, "",   0.05)
            btn_sync = QPushButton("同步 PT1 fc")
            btn_sync.setToolTip("自动调整 r, 使 LKF -3dB 频率 = PT1 截止频率")
            btn_sync.clicked.connect(self._sync_lkf_to_pt1)
            pl.addWidget(self._group("2-state LKF (ω + bias)",
                [("ω:", self.q_omega), ("q_b:", self.q_bias), ("r:", self.r_meas)],
                extras=[btn_sync, self.chk_lkf_en]))

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

            # ── 打杆注入（手动 Cubic 曲线 + 注入正弦）──
            inject_box = QGroupBox("打杆注入")
            inj_lay = QVBoxLayout(inject_box)
            inj_lay.setContentsMargins(4, 8, 4, 5); inj_lay.setSpacing(4)
            # 手动 Cubic 曲线
            stick_box = QGroupBox("手动 Cubic 曲线")
            sb_layout = QVBoxLayout(stick_box)
            sb_layout.setContentsMargins(5, 6, 5, 4); sb_layout.setSpacing(3)
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
            self.btn_stick_clr.clicked.connect(self._clear_sticks)
            sb_layout.addLayout(mode_row)
            inj_lay.addWidget(stick_box)
            # 注入正弦
            self._sine_items = []
            sine_box = QGroupBox("注入正弦")
            self._sine_layout = QVBoxLayout(sine_box)
            self._sine_layout.setContentsMargins(4, 8, 4, 5); self._sine_layout.setSpacing(3)
            btn_add_sine = QPushButton("＋ 新增周期波"); btn_add_sine.setFixedHeight(22)
            btn_add_sine.clicked.connect(self._add_sine_injection)
            self._sine_layout.addWidget(btn_add_sine)
            inj_lay.addWidget(sine_box)
            pl.addWidget(inject_box)

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

            scroll = QScrollArea()
            scroll.setWidget(pane)
            scroll.setWidgetResizable(False)
            scroll.setFixedWidth(316)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            # ── 右侧画布 ──────────────────────────────────
            self.fig    = Figure(facecolor="#080c14")
            self.canvas = FigureCanvas(self.fig)
            toolbar = NavToolbar(self.canvas, self)
            self.nav_toolbar = toolbar
            toolbar.setStyleSheet("background:#1a1a2e; color:#ccccdd; font-size:8pt;")
            canvas_col = QVBoxLayout()
            canvas_col.setContentsMargins(0, 0, 0, 0); canvas_col.setSpacing(2)
            canvas_col.addWidget(toolbar); canvas_col.addWidget(self.canvas)
            ml.addWidget(scroll); ml.addLayout(canvas_col, stretch=1)
