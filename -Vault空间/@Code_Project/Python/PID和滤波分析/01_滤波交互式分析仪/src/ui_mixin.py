# ui_mixin.py — 左侧参数面板构建 + 小工具函数
# _spin / _ispin / _group / _schedule / _build_ui

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QDoubleSpinBox, QGroupBox,
    QPushButton, QCheckBox, QSpinBox, QScrollArea, QMessageBox,
)
from PyQt5.QtCore import Qt
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


        def _build_ui(self):
            central = QWidget(); self.setCentralWidget(central)
            ml = QHBoxLayout(central)
            ml.setContentsMargins(5, 5, 5, 5); ml.setSpacing(6)

            # ── 左侧参数面板 ──────────────────────
            pane = QWidget()
            pane.setFixedWidth(295)
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
