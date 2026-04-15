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
    """Ignores wheel events unless focused.
    # 步进规则：方向键/箭头图标 = singleStep（精调）；滚轮 = _WHEEL_MULT × singleStep（快调）
    # → _spin() 中以 step/_WHEEL_MULT 设置 singleStep，保证滚轮实际步长 = 调用方指定 step
    """
    _WHEEL_MULT = 5  # >v<⚡步进规则 - 滚轮每格=5×singleStep; _spin(step)=滚轮目标步，singleStep=step/5(精调)

    def wheelEvent(self, e):
        if self.hasFocus():
            delta = 1 if e.angleDelta().y() > 0 else -1
            self.stepBy(delta * self._WHEEL_MULT)
            e.accept()  # 阻止事件冒泡到⍫外层 QScrollArea 滚动
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
            # 精调步 = step / _WHEEL_MULT；轮步 = _WHEEL_MULT × 精调步 = step（见 _FocusDSpin）
            if step:   sb.setSingleStep(step / _FocusDSpin._WHEEL_MULT)
            sb.valueChanged.connect(lambda _: self._schedule())
            return sb


        def _ispin(self, lo, hi, val):
            sb = _FocusISpin()
            sb.setRange(lo, hi); sb.setValue(val)
            sb.valueChanged.connect(lambda _: self._schedule())
            return sb

        def _apply_pid(self):
            """PID参数变化→触发重绘（PID独立通道，不覆盖自定义TF）。"""
            if not hasattr(self, 'chk_pid_en'):
                return
            self._schedule()


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


        def _apply_inject_box_style(self, dark: bool) -> None:
            """Set Setpoints注入 box style for current theme (only outer box background)."""
            ib = getattr(self, '_inject_box', None)
            if ib is None:
                return
            if dark:
                ib.setStyleSheet(
                    "QGroupBox#injectBox{background:#141e30; border:1px solid #253048;"
                    "border-radius:4px; margin-top:8px; padding-top:14px;}"
                    "QGroupBox#injectBox::title{subcontrol-origin:margin; subcontrol-position:top left;"
                    "padding:0 6px; color:#8ab0cc;}"
                    "QPushButton:checked{background:#8a5000; color:#ffe0a0; border:1px solid #c07800;}"
                )
            else:
                ib.setStyleSheet(
                    "QGroupBox#injectBox{background:#d4dee8; border:1px solid #a8b8cc;"
                    "border-radius:4px; margin-top:8px; padding-top:14px;}"
                    "QGroupBox#injectBox::title{subcontrol-origin:margin; subcontrol-position:top left;"
                    "padding:0 6px; color:#2a3a50;}"
                    "QPushButton:checked{background:#b06800; color:#ffffff; border:1px solid #d08a00;}"
                )

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
            tc_spin = self._spin(0, N_SECONDS, round((t0 + t1) / 2, 1), 1, "s", 0.5)
            t_row.addWidget(lw_t0); t_row.addWidget(t0_spin)
            t_row.addWidget(lw_t1); t_row.addWidget(t1_spin)
            lay.addLayout(t_row)
            tc_row = QHBoxLayout()
            lw_tc = QLabel("t中:"); lw_tc.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_tc.setFixedWidth(28)
            tc_row.addWidget(lw_tc); tc_row.addWidget(tc_spin)
            lay.addLayout(tc_row)
            freq  = self._spin(0.01, 9999, 20, 2, "Hz", 5)
            freq_end = self._spin(0.01, 9999, 20, 2, "Hz", 5)
            freq_end.setToolTip("起止频率相同时=单频，不同时=Chirp扫频")
            amp   = self._spin(1, 1000, 100, 0, "dps", 10)
            f_mod = self._spin(0, 500, 0, 0, "Hz", 1)
            f_mod.setToolTip("频率调制（FM）的最大频偏幅度，0=关闭")
            trans = self._spin(0, 0.5, 0.1, 2, "", 0.05)
            # f起/f止 side-by-side row
            fq_row = QHBoxLayout()
            lw_f0 = QLabel("f起:"); lw_f0.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_f0.setFixedWidth(28)
            lw_f1 = QLabel("f止:"); lw_f1.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_f1.setFixedWidth(28)
            fq_row.addWidget(lw_f0); fq_row.addWidget(freq)
            fq_row.addWidget(lw_f1); fq_row.addWidget(freq_end)
            lay.addLayout(fq_row)
            # f中 spinbox（f起=f止时单频，f起≠f止时chirp；修改f中保持带宽平移）
            fc_spin = self._spin(0.01, 9999, 20, 2, "Hz", 5)
            fc_spin.setToolTip("f中 = (f起+f止)/2；修改时等比平移f起/f止，保持频带宽度")
            fc_row = QHBoxLayout()
            lw_fc = QLabel("f中:"); lw_fc.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_fc.setFixedWidth(28)
            fc_row.addWidget(lw_fc); fc_row.addWidget(fc_spin)
            lay.addLayout(fc_row)
            fm_smooth = self._ispin(1, 8, 3)
            fm_smooth.setToolTip("FM调制LFO的倍频程：1=平滑大弧，8=粗糙随机（f_mod=0时无效）")
            amp_row = QHBoxLayout()
            lw_amp = QLabel("幅度:"); lw_amp.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_amp.setFixedWidth(50)
            amp_row.addWidget(lw_amp); amp_row.addWidget(amp); lay.addLayout(amp_row)
            fm_row = QHBoxLayout()
            lw_fmd = QLabel("FM频偏:"); lw_fmd.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_fmd.setFixedWidth(50)
            lw_fms = QLabel("光滑:"); lw_fms.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_fms.setFixedWidth(36)
            fm_row.addWidget(lw_fmd); fm_row.addWidget(f_mod)
            fm_row.addWidget(lw_fms); fm_row.addWidget(fm_smooth)
            lay.addLayout(fm_row)
            trans_row = QHBoxLayout()
            lw_tr = QLabel("过渡区:"); lw_tr.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_tr.setFixedWidth(50)
            trans_row.addWidget(lw_tr); trans_row.addWidget(trans); lay.addLayout(trans_row)
            # 多峰：N峰 spinbox + 梳/谐 切换 + Δf（谐波模式时隐藏）
            n_peaks = self._ispin(1, 8, 1)
            btn_harmonic = QPushButton("梳"); btn_harmonic.setCheckable(True); btn_harmonic.setFixedHeight(20)
            btn_harmonic.setToolTip("切换模式：梳状均匀间距 ↔ 谐波倍频列（谐波=1×2×3×...N×f起）")
            delta_f = self._spin(0, 2000, 10, 0, "Hz", 1)
            delta_f.setToolTip("梳状各峰间距 Δf（谐波模式时隐藏）")
            mp_row = QHBoxLayout()
            lw_np = QLabel("N峰:"); lw_np.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_np.setFixedWidth(28)
            mp_row.addWidget(lw_np); mp_row.addWidget(n_peaks); mp_row.addWidget(btn_harmonic)
            lay.addLayout(mp_row)
            df_container = QWidget()
            df_lay2 = QHBoxLayout(df_container); df_lay2.setContentsMargins(0, 0, 0, 0)
            lw_df = QLabel("Δf:"); lw_df.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_df.setFixedWidth(28)
            df_lay2.addWidget(lw_df); df_lay2.addWidget(delta_f)
            lay.addWidget(df_container)
            def _upd_mp_vis(_=None, _b=btn_harmonic, _c=df_container):
                _hm = _b.isChecked()
                _b.setText("谐" if _hm else "梳")
                _c.setVisible(not _hm)
                self._schedule()
            btn_harmonic.clicked.connect(_upd_mp_vis)
            n_peaks.valueChanged.connect(lambda _: self._schedule())
            delta_f.valueChanged.connect(lambda _: self._schedule())
            w_rms       = self._spin(0,   500,   0,   0, "dps", 5)
            p_rms       = self._spin(0,   200,   0,   0, "dps", 2)
            p_oct       = self._ispin(1, 8, 4)
            p_base_freq = self._spin(0.1, 400,  20.0, 1, "Hz",  1.0)
            p_persist   = self._spin(0.1, 1.0,   0.6, 2, "",    0.05)
            p_lacunar   = self._spin(1.2, 4.0,   2.0, 1, "×",   0.1)
            p_seed      = self._ispin(0, 99, 0)
            wnoise_row = QHBoxLayout()
            lw_wn = QLabel("白噪音:"); lw_wn.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_wn.setFixedWidth(50)
            wnoise_row.addWidget(lw_wn); wnoise_row.addWidget(w_rms); lay.addLayout(wnoise_row)
            pr_row = QHBoxLayout()
            lw_pr = QLabel("Perlin:"); lw_pr.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_pr.setFixedWidth(44)
            lw_po = QLabel("程:"); lw_po.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_po.setFixedWidth(26)
            pr_row.addWidget(lw_pr); pr_row.addWidget(p_rms)
            pr_row.addWidget(lw_po); pr_row.addWidget(p_oct)
            lay.addLayout(pr_row)
            bf_row = QHBoxLayout()
            lw_bf = QLabel("基Hz:"); lw_bf.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_bf.setFixedWidth(44)
            lw_sd = QLabel("种:"); lw_sd.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_sd.setFixedWidth(26)
            bf_row.addWidget(lw_bf); bf_row.addWidget(p_base_freq)
            bf_row.addWidget(lw_sd); bf_row.addWidget(p_seed)
            lay.addLayout(bf_row)
            ps_row = QHBoxLayout()
            lw_ps = QLabel("持续:"); lw_ps.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_ps.setFixedWidth(44)
            lw_lc = QLabel("间隔:"); lw_lc.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lw_lc.setFixedWidth(26)
            ps_row.addWidget(lw_ps); ps_row.addWidget(p_persist)
            ps_row.addWidget(lw_lc); ps_row.addWidget(p_lacunar)
            lay.addLayout(ps_row)
            chk_en = QCheckBox("启用"); chk_en.setChecked(True)
            chk_en.stateChanged.connect(lambda _: self._schedule())
            lay.addWidget(chk_en)
            item = {'box': box, 'freq': freq, 'freq_end': freq_end, 'fctr': fc_spin, 'f_mod': f_mod,
                    'amp': amp, 'trans': trans,
                    't0': t0_spin, 't1': t1_spin, 'tctr': tc_spin, 'chk_en': chk_en,
                    'w_rms': w_rms, 'p_rms': p_rms, 'p_oct': p_oct, 'btn_rng': btn_rng,
                    'n_peaks': n_peaks, 'harmonic': btn_harmonic, 'delta_f': delta_f,
                    'fm_smooth': fm_smooth,
                    'p_base_freq': p_base_freq, 'p_persist': p_persist,
                    'p_lacunar': p_lacunar, 'p_seed': p_seed}
            btn_del.clicked.connect(lambda: self._remove_sine_item(item))
            btn_dup.clicked.connect(lambda: self._duplicate_sine_item(item))
            btn_rng.clicked.connect(lambda: self._toggle_sine_range(item))
            # t中 ↔ t起/t止 mutual update (signal-blocked to avoid feedback loops)
            def _upd_tc():
                c = (item['t0'].value() + item['t1'].value()) / 2
                item['tctr'].blockSignals(True); item['tctr'].setValue(c); item['tctr'].blockSignals(False)
            def _upd_t0t1(v):
                d = (item['t1'].value() - item['t0'].value()) / 2
                for w in (item['t0'], item['t1']): w.blockSignals(True)
                item['t0'].setValue(max(0.0, v - d)); item['t1'].setValue(min(float(N_SECONDS), v + d))
                for w in (item['t0'], item['t1']): w.blockSignals(False)
            item['t0'].valueChanged.connect(lambda _: _upd_tc())
            item['t1'].valueChanged.connect(lambda _: _upd_tc())
            item['tctr'].valueChanged.connect(_upd_t0t1)
            # f中 ↔ f起/f止 mutual update（同 t中 规则）
            def _upd_fc():
                c = (item['freq'].value() + item['freq_end'].value()) / 2
                item['fctr'].blockSignals(True); item['fctr'].setValue(c); item['fctr'].blockSignals(False)
            def _upd_f_ends(v):
                d = (item['freq_end'].value() - item['freq'].value()) / 2
                lo = max(1.0, v - d); hi = min(9999.0, v + d)
                for w in (item['freq'], item['freq_end']): w.blockSignals(True)
                item['freq'].setValue(lo); item['freq_end'].setValue(hi)
                for w in (item['freq'], item['freq_end']): w.blockSignals(False)
            item['freq'].valueChanged.connect(lambda _: _upd_fc())
            item['freq_end'].valueChanged.connect(lambda _: _upd_fc())
            item['fctr'].valueChanged.connect(_upd_f_ends)
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
            item['freq_end'].setValue(src['freq_end'].value())
            item['f_mod'].setValue(src['f_mod'].value())
            item['amp'].setValue(src['amp'].value())
            item['trans'].setValue(src['trans'].value())
            item['t0'].setValue(src['t0'].value())
            item['t1'].setValue(src['t1'].value())
            item['w_rms'].setValue(src['w_rms'].value())
            item['p_rms'].setValue(src['p_rms'].value())
            item['p_oct'].setValue(src['p_oct'].value())
            item['fm_smooth'].setValue(src['fm_smooth'].value())
            item['p_base_freq'].setValue(src['p_base_freq'].value())
            item['p_persist'].setValue(src['p_persist'].value())
            item['p_lacunar'].setValue(src['p_lacunar'].value())
            item['p_seed'].setValue(src['p_seed'].value())
            item['chk_en'].setChecked(src['chk_en'].isChecked())
            item['n_peaks'].setValue(src['n_peaks'].value())
            item['harmonic'].setChecked(src['harmonic'].isChecked())
            item['delta_f'].setValue(src['delta_f'].value())
            item['harmonic'].clicked.emit(item['harmonic'].isChecked())  # 触发显隐更新
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
                self._deactivate_toolbar()
            # Deactivate all other sine range buttons
            for it in self._sine_items:
                if it is not item:
                    it['btn_rng'].setChecked(False)
            self._schedule()   # force canvas refresh to show/hide range visualization


        def _build_ui(self):
            central = QWidget(); self.setCentralWidget(central)
            ml = QHBoxLayout(central)
            ml.setContentsMargins(5, 5, 5, 5); ml.setSpacing(6)

            # ── 左侧：固定顶区（轴切换+图层+提示）+ 可滚参数区 ───────────────
            # 顶区（不随滚轮滚动）
            top_pane = QWidget(); top_pane.setFixedWidth(316)
            tp = QVBoxLayout(top_pane); tp.setContentsMargins(5, 5, 5, 2); tp.setSpacing(4)
            # 可滚参数区
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
            self.btn_psd_amp = QPushButton("ASD: 幅度谱"); self.btn_psd_amp.setCheckable(True); self.btn_psd_amp.setChecked(True)
            self.btn_psd_amp.setToolTip("切换 ASD 幅度谱(dps/√Hz) ↔ PSD 功率谱(dps²/Hz)")
            self.btn_psd_amp.clicked.connect(self._toggle_psd_amp)
            btn_row.addWidget(self.btn_x); btn_row.addWidget(self.btn_y)
            btn_row.addWidget(self.btn_psd_amp)
            tp.addLayout(btn_row)
            # <提示> 滚轮=快调（×5步），方向键/GUI箭头=精调（×1步）</提示>
            hint_lbl = QLabel("💡 滚轮=快调×5，方向键/箭头图标=精调×1")
            hint_lbl.setStyleSheet("color:#7aaa55; padding:1px 3px;")  # font size unchanged (no <small>)
            tp.addWidget(hint_lbl)

            # 图层显示（紧凖布局：2列排列）
            show_grp = QGroupBox('图层显示'); show_lay = QGridLayout(show_grp)
            show_lay.setSpacing(2)
            _show_names = ["\u2460 幅频", "\u2461 相频", "\u2462 群延迟", "\u2463 PSD", "\u2464 时域"]
            self.chk_show = []; self.btn_solo = []
            for _i, _nm in enumerate(_show_names):
                _chk = QCheckBox(_nm)
                _chk.setChecked(True)
                _chk.stateChanged.connect(lambda _: self._schedule())
                self.chk_show.append(_chk)
                _r, _c = _i // 2, (_i % 2) * 2  # 2项一行，4列共(chk,独,chk,独)
                show_lay.addWidget(_chk, _r, _c)
                _sbtn = QPushButton("独"); _sbtn.setFixedWidth(24); _sbtn.setCheckable(True)
                _sbtn.clicked.connect(lambda _, i=_i: self._toggle_solo(i))
                self.btn_solo.append(_sbtn)
                show_lay.addWidget(_sbtn, _r, _c + 1)
            tp.addWidget(show_grp)

            # 主题切换
            self.btn_theme = QPushButton("☀ 亮色主题")
            self.btn_theme.setCheckable(True)
            self.btn_theme.setToolTip("切换明暗色主题")
            self.btn_theme.clicked.connect(self._toggle_theme)
            tp.addWidget(self.btn_theme)

            # PT1
            self.chk_pt1_en = QCheckBox("启用 PT1"); self.chk_pt1_en.setChecked(True)
            self.chk_pt1_en.stateChanged.connect(lambda _: self._schedule())
            self.btn_top_pt1 = QPushButton("TOP"); self.btn_top_pt1.setCheckable(True)
            self.btn_top_pt1.setToolTip("PT1 操线置顶（互斜）—使 PT1 的所有线段绘制在最上层")
            self.btn_top_pt1.clicked.connect(lambda: self._toggle_filter_top('pt1'))
            self.btn_pt1_bil = QPushButton("E"); self.btn_pt1_bil.setCheckable(True)
            self.btn_pt1_bil.setFixedWidth(26)
            self.btn_pt1_bil.setToolTip("E=前向欧拉(受采样率影响大)  B=双线性(Tustin)—精度更高但多一次乘\n切换后查看实际-3dB偏差")
            self.btn_pt1_bil.clicked.connect(lambda ch: (
                self.btn_pt1_bil.setText("B" if ch else "E"), self._schedule()))
            self.fc_pt1 = self._spin(10, 900, 100, 0, "Hz", 10)
            self.pt1_info = QLabel("<small style='color:#778'>前向欧拉法 (Betaflight)</small>")
            self.pt1_info.setWordWrap(True)
            self.pt1_info.setMinimumHeight(50)  # >v<📏标签高度 - PT1 info（DEQ + b,a显示需要足够高度）
            pl.addWidget(self._group("PT1 Filter", [("截止 fc:", self.fc_pt1)],
                                     extras=[self.chk_pt1_en, self.btn_top_pt1, self.btn_pt1_bil, self.pt1_info]))

            # LKF
            self.chk_lkf_en = QCheckBox("启用 LKF"); self.chk_lkf_en.setChecked(True)
            self.chk_lkf_en.stateChanged.connect(lambda _: self._schedule())
            self.btn_top_lkf = QPushButton("TOP"); self.btn_top_lkf.setCheckable(True)
            self.btn_top_lkf.setToolTip("LKF 操线置顶（互斜）—使 LKF 的所有线段绘制在最上层")
            self.btn_top_lkf.clicked.connect(lambda: self._toggle_filter_top('lkf'))
            self.q_omega = self._spin(1e-4, 200,  1.0,  4, "",   0.1)
            self.q_bias  = self._spin(1e-9, 1e-3, 1e-4, 5, "",   1e-5)
            self.r_meas  = self._spin(0.0001, 500, 0.012, 5, "",  0.0005)  # >v<🎯LKF默认r - q_omega=1.0,q_bias=1e-4时 r=0.012对应-3dB≫100Hz=PT1默认FC
            btn_sync = QPushButton("同步 PT1 fc")
            btn_sync.setToolTip("自动调整 r, 使 LKF -3dB 频率 = PT1 实际截止频率")
            btn_sync.clicked.connect(self._sync_lkf_to_pt1)
            from PyQt5.QtWidgets import QComboBox
            self.cmb_lkf_obs = QComboBox()
            # DC归一化(obs_mode=1)已从UI移除：KF的DC恒=1(无偏估计), 归一化无意义
            # 代码保留 lkf_coeffs(obs_mode=1) 供未来其他滤波器复用
            self.cmb_lkf_obs.addItems(["原始 H=[1,1]", "H=[1,0]"])
            self.cmb_lkf_obs.setCurrentIndex(1)  # 默认 H=[1,0]
            self.cmb_lkf_obs.setToolTip("原始: 有谐振峰(bias分离副作用)\nH=[1,0]: 去掉bias观测，纯低通")
            self.cmb_lkf_obs.currentIndexChanged.connect(lambda _: self._schedule())
            self.lkf_info = QLabel("<small style='color:#778'>未计算</small>")
            self.lkf_info.setWordWrap(True)
            self.lkf_info.setMinimumHeight(70)  # >v<📏标签高度 - LKF info（DEQ + b,a + peak 显示需要更多高度）
            pl.addWidget(self._group("2-state LKF (ω + bias)",
                [("qω:", self.q_omega), ("q_b:", self.q_bias), ("r:", self.r_meas)],
                extras=[btn_sync, self.cmb_lkf_obs, self.chk_lkf_en, self.btn_top_lkf, self.lkf_info]))

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
            self.white_rms  = self._spin(0, 2000,  5, 0, "dps", 5)
            self.perlin_rms       = self._spin(0,   500,    5,   0, "dps", 2)
            self.perlin_oct       = self._ispin(1, 8, 4)
            self.perlin_base_freq = self._spin(0.1, 400,  5.0,  1, "Hz",  1.0)
            self.perlin_persist   = self._spin(0.1, 1.0,  0.5,  2, "",    0.05)
            self.perlin_lacunar   = self._spin(1.2, 4.0,  2.0,  1, "×",   0.1)
            self.perlin_coord     = self._ispin(0, 999, 0)
            self.perlin_seed      = self._ispin(0,  99, 7)
            pl.addWidget(self._group("全局噪声参数", [
                ("白噪声:", self.white_rms),
                ("Perlin:", self.perlin_rms),
                ("倍频程:", self.perlin_oct),
                ("基频率:", self.perlin_base_freq),
                ("持续度:", self.perlin_persist),
                ("倍频间隔:", self.perlin_lacunar),
                ("坐标:",   self.perlin_coord),
                ("种子:",   self.perlin_seed),
            ], extras=[self.chk_noise_en]))

            # ── Setpoints注入（手动 Cubic 曲线 + 正弦注入）──
            inject_box = QGroupBox("Setpoints注入")
            inject_box.setObjectName("injectBox")
            self._inject_box = inject_box  # 主题切换时更新背景色
            self._apply_inject_box_style(True)  # 初始暗色主题
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
            self.chk_stick_en = QCheckBox("启用"); self.chk_stick_en.setChecked(True)
            self.chk_stick_en.stateChanged.connect(lambda _: self._schedule())
            sb_layout.addWidget(self.chk_stick_en)
            inj_lay.addWidget(stick_box)
            # 正弦注入
            self._sine_items = []
            sine_box = QGroupBox("正弦注入")
            self._sine_layout = QVBoxLayout(sine_box)
            self._sine_layout.setContentsMargins(4, 8, 4, 5); self._sine_layout.setSpacing(3)
            btn_add_sine = QPushButton("＋ 新增周期波(to当前时间轴1/3范围)"); btn_add_sine.setFixedHeight(22)
            btn_add_sine.clicked.connect(self._add_sine_injection)
            self._sine_layout.addWidget(btn_add_sine)
            inj_lay.addWidget(sine_box)
            pl.addWidget(inject_box)

            # ── 自定义传递函数 ──
            from PyQt5.QtWidgets import QLineEdit, QComboBox
            hs_box = QGroupBox("自定义传递函数")
            hs_lay = QVBoxLayout(hs_box); hs_lay.setContentsMargins(5, 8, 5, 5); hs_lay.setSpacing(3)
            self.chk_hs_en = QCheckBox("启用"); self.chk_hs_en.setChecked(False)
            self.chk_hs_en.setToolTip("H(s)=num(s)/den(s)，bilinear→H(z)，支持PID等任意线性系统")
            self.chk_hs_en.stateChanged.connect(lambda _: self._schedule())
            hs_lay.addWidget(self.chk_hs_en)
            # 预设下拉
            preset_row = QHBoxLayout()
            lw_pr = QLabel("预设:"); lw_pr.setFixedWidth(46)
            lw_pr.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cmb_hs_preset = QComboBox()
            self.cmb_hs_preset.addItems([
                "(自定义)",
                "PT1 @100Hz",
                "PT1 @50Hz",
                "2阶低通 @100Hz Q=0.7",
                "PID示例 (5\"角速度)",
            ])
            def _apply_hs_preset(idx):
                presets = {
                    1: ("1",            "1.592e-3, 1"),
                    2: ("1",            "3.183e-3, 1"),
                    3: ("1",            "2.533e-6, 2.251e-3, 1"),
                    4: ("0.036, 4.5, 6.0", "1.33e-3, 1, 0"),
                }
                self._hs_z_direct = None
                if idx in presets:
                    self.hs_num.setText(presets[idx][0])
                    self.hs_den.setText(presets[idx][1])
                    self._schedule()
            self.cmb_hs_preset.currentIndexChanged.connect(_apply_hs_preset)
            preset_row.addWidget(lw_pr); preset_row.addWidget(self.cmb_hs_preset)
            hs_lay.addLayout(preset_row)
            # 信号源选择（频响始终显示TF本身；源仅影响时域+PSD）
            src_hs_row = QHBoxLayout()
            lw_hs_src = QLabel("源:"); lw_hs_src.setFixedWidth(46)
            lw_hs_src.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cmb_hs_src = QComboBox()
            self.cmb_hs_src.addItems(["未滤波", "PT1", "LKF"])
            self.cmb_hs_src.setToolTip("输入信号选择\n实线=级联总响应，虚线=TF自身")
            self.cmb_hs_src.currentIndexChanged.connect(lambda _: self._schedule())
            src_hs_row.addWidget(lw_hs_src); src_hs_row.addWidget(self.cmb_hs_src)
            hs_lay.addLayout(src_hs_row)
            self.btn_top_hs = QPushButton("TOP"); self.btn_top_hs.setCheckable(True)
            self.btn_top_hs.setToolTip("自定义TF 操线置顶（互斥）")
            self.btn_top_hs.clicked.connect(lambda: self._toggle_filter_top('hs'))
            hs_lay.addWidget(self.btn_top_hs)
            for lbl_txt, attr, ph in [
                ("num s:", "hs_num", "高→低次系数: 1,0.4,4 (=s²+0.4s+4)"),
                ("den s:", "hs_den", "高→低次系数: 0.0016,1 (=0.0016s+1)")]:
                row = QHBoxLayout()
                lw  = QLabel(lbl_txt); lw.setFixedWidth(46)
                lw.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                le  = QLineEdit(); le.setPlaceholderText(ph)
                le.editingFinished.connect(lambda: (setattr(self, '_hs_z_direct', None), self._schedule()))
                setattr(self, attr, le)
                row.addWidget(lw); row.addWidget(le); hs_lay.addLayout(row)
            hs_status = QLabel("<small style='color:#778'>未启用</small>"); hs_status.setWordWrap(True); hs_status.setMinimumHeight(48)
            hs_lay.addWidget(hs_status)
            self.hs_status_label = hs_status
            pl.addWidget(hs_box)

            # ── 差分表达式 y[n]=... ──
            deq_box = QGroupBox("差分表达式 y[n]=...")
            deq_lay = QVBoxLayout(deq_box); deq_lay.setContentsMargins(5, 8, 5, 5); deq_lay.setSpacing(3)
            self.chk_deq_en = QCheckBox("启用"); self.chk_deq_en.setChecked(False)
            self.chk_deq_en.setToolTip("z域差分方程: 直接指定 b(z)/a(z) 系数")
            self.chk_deq_en.stateChanged.connect(lambda _: self._schedule())
            deq_lay.addWidget(self.chk_deq_en)
            # 预设
            deq_pr_row = QHBoxLayout()
            lw_dpr = QLabel("预设:"); lw_dpr.setFixedWidth(46)
            lw_dpr.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cmb_deq_preset = QComboBox()
            self.cmb_deq_preset.addItems([
                "(自定义)",
                "PT1 @100Hz (Euler)",
                "PT1 @50Hz (Euler)",
                "PT1 @100Hz (Bilinear)",
                "2阶Butter @100Hz",
            ])
            def _apply_deq_preset(idx):
                import numpy as _np
                from dsp import pt1_coeffs as _pt1c
                from scipy.signal import butter as _butter, bilinear as _bil
                _fc_map = {1: 100, 2: 50, 3: 100, 4: 100}
                if idx == 1:
                    b, a = _pt1c(100, FS)
                elif idx == 2:
                    b, a = _pt1c(50, FS)
                elif idx == 3:
                    b, a = _bil([1], [1.0/(2*_np.pi*100), 1], fs=FS)
                elif idx == 4:
                    b, a = _butter(2, 100, btype='low', fs=FS)
                else:
                    self._deq_designed_fc = None
                    return
                self._deq_designed_fc = _fc_map.get(idx)
                self.deq_b.setText(", ".join(f"{c:.6g}" for c in b))
                self.deq_a.setText(", ".join(f"{c:.6g}" for c in a))
                self._schedule()
            self.cmb_deq_preset.currentIndexChanged.connect(_apply_deq_preset)
            deq_pr_row.addWidget(lw_dpr); deq_pr_row.addWidget(self.cmb_deq_preset)
            deq_lay.addLayout(deq_pr_row)
            # 源
            deq_src_row = QHBoxLayout()
            lw_dsrc = QLabel("源:"); lw_dsrc.setFixedWidth(46)
            lw_dsrc.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cmb_deq_src = QComboBox()
            self.cmb_deq_src.addItems(["未滤波", "PT1", "LKF"])
            self.cmb_deq_src.setToolTip("输入信号选择\n实线=级联总响应，虚线=TF自身")
            self.cmb_deq_src.currentIndexChanged.connect(lambda _: self._schedule())
            deq_src_row.addWidget(lw_dsrc); deq_src_row.addWidget(self.cmb_deq_src)
            deq_lay.addLayout(deq_src_row)
            self.btn_top_deq = QPushButton("TOP"); self.btn_top_deq.setCheckable(True)
            self.btn_top_deq.setToolTip("差分表达式曲线置顶")
            self.btn_top_deq.clicked.connect(lambda: self._toggle_filter_top('deq'))
            deq_lay.addWidget(self.btn_top_deq)
            for lbl_txt, attr, ph in [
                ("b(z):", "deq_b", "z^-n系数: b0,b1,... (如 0.2392)"),
                ("a(z):", "deq_a", "z^-n系数: 1,a1,... (如 1,-0.7608)")]:
                row = QHBoxLayout()
                lw = QLabel(lbl_txt); lw.setFixedWidth(46)
                lw.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                le = QLineEdit(); le.setPlaceholderText(ph)
                le.editingFinished.connect(lambda: (setattr(self, '_deq_designed_fc', None), self._schedule()))
                setattr(self, attr, le)
                row.addWidget(lw); row.addWidget(le); deq_lay.addLayout(row)
            deq_status = QLabel("<small style='color:#778'>未启用</small>"); deq_status.setWordWrap(True); deq_status.setMinimumHeight(48)
            deq_lay.addWidget(deq_status)
            self.deq_status_label = deq_status
            pl.addWidget(deq_box)

            # ── PID 控制器 ──
            pid_box = QGroupBox("PID 控制器")
            pid_lay = QVBoxLayout(pid_box); pid_lay.setContentsMargins(5, 8, 5, 5); pid_lay.setSpacing(3)
            self.chk_pid_en = QCheckBox("启用"); self.chk_pid_en.setChecked(False)
            self.chk_pid_en.setToolTip("闭环PID: T(s)=C(s)/s / (1+C(s)/s)\nG(s)=1/s (角加速度→角速率)")
            self.chk_pid_en.stateChanged.connect(lambda _: self._apply_pid())
            pid_lay.addWidget(self.chk_pid_en)
            # PID 滤波
            pid_src_row = QHBoxLayout()
            lw_psrc = QLabel("滤波:"); lw_psrc.setFixedWidth(46)
            lw_psrc.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cmb_pid_src = QComboBox()
            self.cmb_pid_src.addItems(["未滤波", "PT1", "LKF", "差分表达式"])
            self.cmb_pid_src.setCurrentIndex(1)
            self.cmb_pid_src.setToolTip("PID反馈路径滤波器\n独立差分迭代计算(不复用开环波形)")
            self.cmb_pid_src.currentIndexChanged.connect(lambda _: self._schedule())
            pid_src_row.addWidget(lw_psrc); pid_src_row.addWidget(self.cmb_pid_src)
            pid_lay.addLayout(pid_src_row)
            self.pid_kp = self._spin(0, 5000, 150,  1, "Kp", 5)
            self.pid_ki = self._spin(0, 5000, 200,  1, "Ki", 20)
            self.pid_kd = self._spin(0, 50,   0.5,  2, "Kd", 0.05)
            self.pid_df = self._spin(10, 500, 120,   0, "Hz", 10)
            self.pid_df.setToolTip("D项低通滤波截止频率")
            for lbl, w in [("Kp:", self.pid_kp), ("Ki:", self.pid_ki),
                           ("Kd:", self.pid_kd), ("D滤波:", self.pid_df)]:
                row = QHBoxLayout()
                lw = QLabel(lbl); lw.setFixedWidth(46)
                lw.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                row.addWidget(lw); row.addWidget(w); pid_lay.addLayout(row)
            # 连接PID参数变化→自动更新H(s)
            for w in (self.pid_kp, self.pid_ki, self.pid_kd, self.pid_df):
                w.valueChanged.connect(lambda _: self._apply_pid())
            self.btn_top_pid = QPushButton("TOP"); self.btn_top_pid.setCheckable(True)
            self.btn_top_pid.setToolTip("PID曲线置顶")
            self.btn_top_pid.clicked.connect(lambda: self._toggle_filter_top('pid'))
            pid_lay.addWidget(self.btn_top_pid)
            self.chk_pid_solo = QCheckBox("独奏 (隐藏非PID相关曲线)")
            self.chk_pid_solo.setChecked(False)
            self.chk_pid_solo.setToolTip("只显示PID闭环迭代曲线+PID所用滤波器开环曲线\n隐藏`其他滤波器`和`直接叠加噪音的输入`波形")
            self.chk_pid_solo.stateChanged.connect(lambda _: self._schedule())
            pid_lay.addWidget(self.chk_pid_solo)
            pl.addWidget(pid_box)

            # ── Teager能量算子(TEO) ──
            teo_box = QGroupBox("Teager能量算子(TEO)")
            teo_lay = QVBoxLayout(teo_box); teo_lay.setContentsMargins(5, 8, 5, 5); teo_lay.setSpacing(3)
            self.chk_teo_en = QCheckBox("启用 TEO"); self.chk_teo_en.setChecked(False)
            self.chk_teo_en.setToolTip("Teager Energy Operator: x²[n]−x[n−1]·x[n+1] — 仅 PSD+时域")
            self.chk_teo_en.stateChanged.connect(lambda _: self._schedule())
            teo_lay.addWidget(self.chk_teo_en)
            src_row = QHBoxLayout()
            lw_src = QLabel("信号源:"); lw_src.setFixedWidth(46)
            lw_src.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cmb_teo_src = QComboBox()
            self.cmb_teo_src.addItems(["未滤波", "PT1", "LKF", "自定义TF", "差分表达式", "PID_gyro filt", "PID_gyro unfilt"])
            self.cmb_teo_src.setCurrentIndex(1)  # 默认PT1（未滤波噪声太大TEO无意义）
            self.cmb_teo_src.currentIndexChanged.connect(lambda _: self._schedule())
            src_row.addWidget(lw_src); src_row.addWidget(self.cmb_teo_src)
            teo_lay.addLayout(src_row)
            scale_row = QHBoxLayout()
            lw_sc = QLabel("缩放:"); lw_sc.setFixedWidth(46)
            lw_sc.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.teo_scale = self._spin(0.001, 100, 0.1, 3, "", 0.01)
            self.teo_scale.setToolTip("TEO输出乘以此系数（正弦输入时TEO幅度极大，建议0.01~0.1）")
            scale_row.addWidget(lw_sc); scale_row.addWidget(self.teo_scale)
            teo_lay.addLayout(scale_row)
            teo_note = QLabel("<small style='color:#778'>x²[n]−x[n−1]·x[n+1] — 非线性，仅PSD+时域</small>")
            teo_note.setWordWrap(True)
            teo_lay.addWidget(teo_note)
            pl.addWidget(teo_box)

            note = QLabel(
                "<small>"
                "<span style='color:#7ac4e0'>■</span> PT1 虚线=单独  实线=+Notch<br>"
                "<span style='color:#e8394a'>■</span> LKF 同上<br>"
                "<span style='color:#a070e0'>■</span> 自定义TF 同上<br>"
                "<span style='color:#e07830'>■</span> 差分表达式 同上<br>"
                "<span style='color:#50c878'>■</span> Teager能量算子TEO (PSD+时域)<br>"
                "<span style='color:#e0a040'>■</span> PID 控制器<br>"
                "<span style='color:#f5f5ff'>■</span> 信号（注入滤波）<br>"
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
            # 左栏容器：顶区固定 + 参数区可滚动
            left_wrap = QWidget(); left_wrap.setFixedWidth(316)
            lw_lay = QVBoxLayout(left_wrap); lw_lay.setContentsMargins(0, 0, 0, 0); lw_lay.setSpacing(0)
            lw_lay.addWidget(top_pane)
            lw_lay.addWidget(scroll, 1)

            # ── 右侧画布 ──────────────────────────────────
            self.fig    = Figure(facecolor="#080c14")
            self.canvas = FigureCanvas(self.fig)
            # ── 每图左侧快捷轴控按钮（悬浮于画布左边距，draw_event 后自动定位）──
            _BTN_SS = ("QPushButton{background:rgba(30,35,55,190);color:#99bbcc;"
                       "border:1px solid #3a4a5a;border-radius:2px;"
                       "font-size:7pt;padding:0px;}"
                       "QPushButton:checked{background:rgba(60,140,80,210);color:#eeffee;}"
                       "QPushButton:hover{background:rgba(50,70,100,220);}")
            self._ax_ctrl_groups = []
            for _ai in range(5):
                _grp = QWidget(self.canvas)
                _grp.setStyleSheet("background:transparent;")
                _grp.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                _vl = QVBoxLayout(_grp)
                _vl.setSpacing(1); _vl.setContentsMargins(1, 1, 1, 1)
                _bya = QPushButton("|A"); _bya.setCheckable(True)
                _bya.setFixedSize(22, 16); _bya.setStyleSheet(_BTN_SS)
                _bya.setToolTip("Y轴适应（开关，自动覆盖峰谷）")
                _bya.clicked.connect(lambda checked, i=_ai: self._on_yfit(i, checked))
                _byr = QPushButton("|R"); _byr.setFixedSize(22, 16); _byr.setStyleSheet(_BTN_SS)
                _byr.setToolTip("Y轴重置")
                _byr.clicked.connect(lambda _, i=_ai: self._on_yreset(i))
                _bxr = QPushButton("-R"); _bxr.setFixedSize(22, 16); _bxr.setStyleSheet(_BTN_SS)
                _bxr.setToolTip("X轴重置")
                _bxr.clicked.connect(lambda _, i=_ai: self._on_xreset(i))
                _vl.addWidget(_bya); _vl.addWidget(_byr); _vl.addWidget(_bxr)
                _grp.adjustSize(); _grp.hide()
                self._ax_ctrl_groups.append({'widget': _grp, 'ya': _bya, 'yr': _byr, 'xr': _bxr})
            self.canvas.mpl_connect('draw_event', self._reposition_ax_ctrl_overlay)
            toolbar = NavToolbar(self.canvas, self)
            self.nav_toolbar = toolbar
            toolbar.setStyleSheet("background:#1a1a2e; color:#ccccdd; font-size:8pt;")
            # ⓘ 说明按鈕与 toolbar 同行（toolbar 有大片空白，放这里很合适）
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
                "注意：修改将在下次刷新时被换掉。"
            )
            _btn_sp = QPushButton("ⓘ 子图")
            _btn_sp.setFixedHeight(26); _btn_sp.setToolTip("查看 Configure Subplots 使用说明")
            _btn_sp.clicked.connect(lambda: QMessageBox.information(self, "Configure Subplots", _MSG_SUBPLOTS))
            _btn_ea = QPushButton("ⓘ 坐标轴")
            _btn_ea.setFixedHeight(26); _btn_ea.setToolTip("查看 Edit Axis 使用说明")
            _btn_ea.clicked.connect(lambda: QMessageBox.information(self, "Edit Axis", _MSG_EDITAXIS))
            toolbar_row = QHBoxLayout(); toolbar_row.setSpacing(3); toolbar_row.setContentsMargins(0, 0, 0, 0)
            toolbar.setMaximumHeight(34)
            toolbar_row.addWidget(toolbar)
            # 画布控制提示（toolbar图标右侧、ⓘ按钮左侧，字体与左上角"滚轮=快调..."一致）
            _canvas_hint = QLabel("中键=拖动  滚轮=缩放  +Ctrl=仅Y轴  +Shift=仅X轴")
            _canvas_hint.setStyleSheet("color:#7aaa55; padding:1px 3px;")
            toolbar_row.addWidget(_canvas_hint)
            toolbar_row.addStretch()
            toolbar_row.addWidget(_btn_sp); toolbar_row.addWidget(_btn_ea)
            canvas_col = QVBoxLayout()
            canvas_col.setContentsMargins(0, 0, 0, 0); canvas_col.setSpacing(2)
            canvas_col.addWidget(self.canvas, stretch=1); canvas_col.addLayout(toolbar_row)
            ml.addWidget(left_wrap); ml.addLayout(canvas_col, stretch=1)
