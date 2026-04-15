# draw_mixin.py — 绘图核心 + 轴切换 + LKF 同步
# _toggle_x / _toggle_y / _sync_lkf_to_pt1 / _do_update

import numpy as np
from scipy.signal import freqz, lfilter, welch
from matplotlib.gridspec import GridSpec
from constants import FS, N_SECONDS, N_SIG
from dsp import (
    pt1_coeffs, lkf_coeffs, notch_coeffs,
    resonance, resonance_dist, perlin_noise_1d,
    custom_tf_to_digital, teo,
    find_3db_freq, diff_eq_str, poly_str, poly_z_str,
)


class DrawMixin:

        def _compute_sine_total(self):
            """Sum all sine injection signals (half-Hann window + local noise). Cached by param key.
            Supports single-freq, chirp (f_start≠f_end), and FM (f_mod>0)."""
            items = getattr(self, '_sine_items', [])
            if not items:
                self._sine_cache_key = None
                return np.zeros(N_SIG)
            key = tuple(
                (it['freq'].value(), it.get('freq_end', it['freq']).value(),
                 it.get('f_mod', it['freq']).value() if hasattr(it.get('f_mod', None), 'value') else 0,
                 it['n_peaks'].value() if 'n_peaks' in it else 1,
                 it['harmonic'].isChecked() if 'harmonic' in it else False,
                 it['delta_f'].value() if 'delta_f' in it else 0.0,
                 it['amp'].value(), it['trans'].value(),
                 it['t0'].value(), it['t1'].value(),
                 it['w_rms'].value(), it['p_rms'].value(), it['p_oct'].value(),
                 it.get('chk_en') is None or it['chk_en'].isChecked())
                for it in items
            )
            if getattr(self, '_sine_cache_key', None) == key:
                return self._sine_cache
            t_full = np.arange(N_SIG) / FS
            total  = np.zeros(N_SIG)
            for item in items:
                if item.get('chk_en') is not None and not item['chk_en'].isChecked():
                    continue
                f_start = item['freq'].value()
                f_end   = item['freq_end'].value() if 'freq_end' in item else f_start
                f_mod_v = item['f_mod'].value()    if 'f_mod'   in item else 0.0
                amp   = item['amp'].value()
                trans = item['trans'].value(); t0 = item['t0'].value(); t1 = item['t1'].value()
                w_rms = item['w_rms'].value(); p_rms = item['p_rms'].value()
                p_oct = int(item['p_oct'].value())
                dur   = t1 - t0
                if dur <= 0:
                    continue
                window = np.zeros(N_SIG)
                fade   = max(0.0, trans) * dur
                if fade > 0:
                    mx_in  = (t_full >= t0) & (t_full < t0 + fade)
                    mx_out = (t_full > t1 - fade) & (t_full <= t1)
                    mx_mid = (t_full >= t0 + fade) & (t_full <= t1 - fade)
                    window[mx_in]  = 0.5 * (1 - np.cos(np.pi*(t_full[mx_in]  - t0) / fade))
                    window[mx_out] = 0.5 * (1 - np.cos(np.pi*(t1 - t_full[mx_out]) / fade))
                    window[mx_mid] = 1.0
                else:
                    window[(t_full >= t0) & (t_full <= t1)] = 1.0
                # Phase synthesis: multi-peak support (comb / harmonic / single)
                n_pk   = int(item['n_peaks'].value()) if 'n_peaks' in item else 1
                use_hm = item['harmonic'].isChecked() if 'harmonic' in item else False
                d_f    = item['delta_f'].value()       if 'delta_f'  in item else 0.0
                seed_fm_base = int(f_start * 73 + f_end * 37 + t0 * 11) % (2**31)
                for pk in range(n_pk):
                    if n_pk == 1:
                        pk_f0, pk_f1 = f_start, f_end
                    elif use_hm:                           # 谐波: 1× 2× 3× ...
                        pk_f0 = f_start * (pk + 1)
                        pk_f1 = f_end   * (pk + 1)
                    else:                                  # 法状: 均匀间距
                        pk_f0 = f_start + pk * d_f
                        pk_f1 = f_end   + pk * d_f
                    if abs(pk_f1 - pk_f0) > 0.5:          # chirp
                        k = (pk_f1 - pk_f0) / dur
                        t_loc = np.clip(t_full - t0, 0, dur)
                        phase = 2 * np.pi * (pk_f0 * t_loc + 0.5 * k * t_loc**2)
                    else:
                        phase = 2 * np.pi * pk_f0 * t_full
                    if f_mod_v > 0:
                        seed_fm = (seed_fm_base + pk * 17) % (2**31)
                        lfo = perlin_noise_1d(N_SIG, octaves=3, seed=seed_fm)
                        phase += 2 * np.pi * f_mod_v * np.cumsum(lfo) / FS
                    total += (amp / n_pk) * np.sin(phase) * window
                if w_rms > 0 or p_rms > 0:
                    seed = int(f_start * 100 + amp + t0 * 10) % (2**31)
                    rng  = np.random.default_rng(seed)
                    loc  = np.zeros(N_SIG)
                    if w_rms > 0: loc += rng.standard_normal(N_SIG) * w_rms
                    if p_rms > 0: loc += perlin_noise_1d(N_SIG, octaves=p_oct, seed=seed+1) * p_rms
                    total += loc * window
            self._sine_cache_key = key
            self._sine_cache = total
            return total


        def _do_update_drag(self):
            """拖拽中轻量更新 — 仅重绘打杆曲线+控制点，跳过噪声/滤波/PSD/频响。"""
            ax5 = self._last_axes[4]
            if ax5 is None:
                self._do_update(); return
            T = self._DARK if self._dark_mode else self._LIGHT
            xlim, ylim = ax5.get_xlim(), ax5.get_ylim()
            ax5.cla()
            ax5.set_facecolor(T['ax'])
            ax5.grid(True, which="both", color=T['grid'], linewidth=0.55)
            ax5.tick_params(colors=T['tick'], labelsize=7.5)
            for sp in ax5.spines.values(): sp.set_edgecolor(T['spine'])
            # 正弦范围模式：只显示当前注入波形和范围标记
            if getattr(self, '_sine_range_item', None) is not None:
                s_sine = self._compute_sine_total()
                dec_r = 10; t_r = np.arange(N_SIG)[::dec_r] / FS
                ax5.plot(t_r, s_sine[::dec_r], color=T['sine'], lw=0.5, alpha=0.7)
                item_r = self._sine_range_item
                t0v = item_r['t0'].value(); t1v = item_r['t1'].value()
                dur = max(t1v - t0v, 0.01)
                ax5.axvspan(t0v,         t0v + dur/3,  alpha=0.12, color='#7799bb', zorder=1)
                ax5.axvspan(t0v + dur/3, t1v - dur/3,  alpha=0.20, color='#7799bb', zorder=1)
                ax5.axvspan(t1v - dur/3, t1v,          alpha=0.12, color='#7799bb', zorder=1)
                ax5.axvline(t0v,         color='#7799bb', lw=1.0, ls='--', alpha=0.80, zorder=5)
                ax5.axvline(t1v,         color='#7799bb', lw=1.0, ls='--', alpha=0.80, zorder=5)
                ax5.set_title("时域  [⇄ 正弦范围]  [拖拽中...]",
                              color=T['label'], fontsize=7.5, pad=2)
                ax5.set_xlabel("Time (s)", color=T['label'], fontsize=8)
                ax5.set_ylabel("dps",      color=T['label'], fontsize=8)
                ax5.set_xlim(xlim); ax5.set_ylim(ylim)
                self.canvas.draw_idle()
                return
            _use_stick = getattr(self, 'chk_stick_en', None)
            _draw_stick = (_use_stick is None or _use_stick.isChecked())
            s_stick = self._compute_stick_signal() if _draw_stick else np.zeros(N_SIG)
            dec = 10; t = np.arange(N_SIG)[::dec] / FS
            if _draw_stick:
                ax5.plot(t, s_stick[::dec], color=T['stick'], lw=0.85, alpha=0.85)
            ax5.scatter([0.0, float(N_SECONDS)],
                        [self._anchor_y[0], self._anchor_y[1]],
                        color=T['dot'], s=38, marker='s', zorder=7)
            if self._stick_pts:
                inner = [(t_, y_) for t_, y_ in self._stick_pts
                         if 0.05 < t_ < N_SECONDS - 0.05]
                if inner:
                    ax5.scatter([p[0] for p in inner], [p[1] for p in inner],
                                color=T['dot'], s=22, zorder=6)
            _hint = {"add": "✚ 新增", "del": "✖ 删除(1/200)", "adj": "⇄ 调整"}
            ax5.set_title(f"时域  [{_hint.get(self._stick_mode, '')}]  [拖拽中...]",
                          color=T['label'], fontsize=7.5, pad=2)
            ax5.set_xlabel("Time (s)", color=T['label'], fontsize=8)
            ax5.set_ylabel("dps",      color=T['label'], fontsize=8)
            ax5.set_xlim(xlim); ax5.set_ylim(ylim)
            self.canvas.draw_idle()


        def _toggle_x(self, checked):
            self._log_xaxis = checked
            self.btn_x.setText("频率轴: 对数" if checked else "频率轴: 线性")
            self._do_update()


        def _toggle_y(self, checked):
            self._log_yaxis = checked
            self.btn_y.setText("幅度: dB" if checked else "幅度: 线性")
            self._do_update()


        def _toggle_psd_amp(self, checked):
            # >v<📊PSD_ASD切换 - checked=True=ASD; Y轴自动×0.1(→ASD)或×10(→PSD); 无需HOME
            # PSD默认Y=[0,2000], ASD默认Y=[0,200] (见main.py _saved_views[3])
            self._psd_amp_mode = checked
            self.btn_psd_amp.setText("ASD: 幅度谱" if checked else "PSD: 功率谱")
            # 自动调整 PSD 轴 Y 范围（用户约定：ASD↔PSD ×0.1 or ×10，不需要按 HOME）
            _tv3 = self._saved_views[3]
            if _tv3 is not None:
                xl = list(_tv3[0])
                yl = list(_tv3[1])
                factor = 0.1 if checked else 10.0  # →ASD=÷10, →PSD=×10
                self._saved_views[3] = (xl, [yl[0] * factor, yl[1] * factor])
            else:
                self._saved_views[3] = ([0.0, 1000.0], [0.0, 200.0] if checked else [0.0, 2000.0])
            self._do_update()


        def _reposition_ax_ctrl_overlay(self, event=None):
            """每次 figure draw 后，将各图左侧控件组定位到对应 axes 左边距中央。"""
            grps = getattr(self, '_ax_ctrl_groups', [])
            if not grps:
                return
            cw = self.canvas.width(); ch = self.canvas.height()
            if cw <= 0 or ch <= 0:
                return
            for _i, _entry in enumerate(grps):
                _ax  = self._last_axes[_i] if _i < len(self._last_axes) else None
                _w   = _entry['widget']
                _vis = (self.chk_show[_i].isChecked() if _i < len(self.chk_show) else True)
                if _ax is None or not _vis:
                    _w.hide(); continue
                _bb   = _ax.get_position()          # 图坐标系分数（y 从底部起）
                _ytop = int((1.0 - _bb.y1) * ch)
                _ybot = int((1.0 - _bb.y0) * ch)
                _cy   = (_ytop + _ybot) // 2
                _w.move(2, max(0, _cy - _w.height() // 2))
                _w.show(); _w.raise_()

        def _on_yfit(self, ax_idx, checked):
            """Toggle per-axis Y auto-fit（覆盖峰谷）。"""
            if not hasattr(self, '_y_auto'):
                self._y_auto = [False] * 5
            self._y_auto[ax_idx] = checked
            self._schedule()

        def _on_yreset(self, ax_idx):
            """Reset Y axis of given plot to its default range."""
            ax = self._last_axes[ax_idx] if ax_idx < len(self._last_axes) else None
            if ax is None:
                return
            if ax_idx == 3:
                ylim_def = [0.0, 200.0] if getattr(self, '_psd_amp_mode', True) else [0.0, 2000.0]
            elif ax_idx == 0:
                ylim_def = [-65.0, 8.0] if self._log_yaxis else [-0.05, 1.15]
            else:
                dv = getattr(self, '_default_views', None)
                if dv is None:
                    return
                ylim_def = list(dv[ax_idx][1])
            sv = self._saved_views[ax_idx]
            xl = list(sv[0]) if sv else [0.0, 1000.0]
            self._saved_views[ax_idx] = (xl, ylim_def)
            ax.set_ylim(ylim_def)
            self.canvas.draw_idle()

        def _on_xreset(self, ax_idx):
            """Reset X axis of given plot to its default range."""
            ax = self._last_axes[ax_idx] if ax_idx < len(self._last_axes) else None
            if ax is None:
                return
            if ax_idx in (0, 1, 2):
                xlim_def = [1.0 if self._log_xaxis else 0.0, float(FS / 2)]
            elif ax_idx == 3:
                xlim_def = [0.0, 1000.0]
            else:
                xlim_def = [0.0, float(N_SECONDS)]
            sv = self._saved_views[ax_idx]
            yl = list(sv[1]) if sv else list(getattr(self, '_default_views', [[]] * 5)[ax_idx][1])
            self._saved_views[ax_idx] = (xlim_def, yl)
            ax.set_xlim(xlim_def)
            self.canvas.draw_idle()

        def _toggle_filter_top(self, name):
            """Exclusive TOP: 互斥选择一个滤波器的线置顶显示。"""
            checked = getattr(self, f'btn_top_{name}').isChecked()
            self._top_filter = name if checked else None
            # 解除其他 TOP 按钮
            for _n in ('pt1', 'lkf', 'hs', 'pid', 'deq'):
                if _n != name:
                    btn = getattr(self, f'btn_top_{_n}', None)
                    if btn is not None:
                        btn.setChecked(False)
            self._schedule()

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
            self.r_meas.setValue(float(np.clip(np.sqrt(lo * hi), 0.001, 500)))  # >v<🎯LKF同步下限 - 必须与 r_meas spinbox 下限一致(0.001)
            self.r_meas.blockSignals(False)
            self._do_update()


        def _do_update(self):
            # 保存时域轴缩放状态
            if not self._views_reset:
                for _i, _la in enumerate(self._last_axes):
                    if _la is not None:
                        try:
                            self._saved_views[_i] = (list(_la.get_xlim()), list(_la.get_ylim()))
                        except Exception:
                            pass
            self._views_reset = False

            fs = FS

            # ── 滤波器系数 ──
            b_pt1, a_pt1 = pt1_coeffs(self.fc_pt1.value(), fs)
            b_lkf, a_lkf = lkf_coeffs(
                self.q_omega.value(), self.q_bias.value(), self.r_meas.value(), fs)

            # PT1 实际 -3dB 标注
            if hasattr(self, 'pt1_info'):
                f3 = find_3db_freq(b_pt1, a_pt1, fs)
                fc_set = self.fc_pt1.value()
                if f3 is not None:
                    self.pt1_info.setText(
                        f"<small style='color:#778'>前向欧拉法 (Betaflight)"
                        f"<br>实际-3dB: {f3:.1f}Hz (设定{fc_set:.0f}Hz)</small>")
                else:
                    self.pt1_info.setText("<small style='color:#778'>前向欧拉法</small>")
            b_n1, a_n1 = notch_coeffs(self.f_n1.value(), self.q_n1.value(), fs)
            b_n2, a_n2 = notch_coeffs(self.f_n2.value(), self.q_n2.value(), fs)
            use_n1 = self.n1_en.isChecked()
            use_n2 = self.n2_en.isChecked()
            use_pt1 = self.chk_pt1_en.isChecked()
            use_lkf = self.chk_lkf_en.isChecked()

            # ── 自定义传递函数 H(s) ──
            use_hs = self.chk_hs_en.isChecked()
            b_hs_z, a_hs_z = None, None
            hs_err = None
            if use_hs:
                _z_direct = getattr(self, '_hs_z_direct', None)
                try:
                    if _z_direct is not None:
                        import numpy as _np
                        b_hs_z = _np.array(_z_direct[0], dtype=float)
                        a_hs_z = _np.array(_z_direct[1], dtype=float)
                    else:
                        num_s = [float(x.strip()) for x in self.hs_num.text().split(',') if x.strip()]
                        den_s = [float(x.strip()) for x in self.hs_den.text().split(',') if x.strip()]
                        if not num_s or not den_s:
                            raise ValueError("分子/分母至少一个系数")
                        b_hs_z, a_hs_z = custom_tf_to_digital(num_s, den_s, fs)
                except Exception as e:
                    hs_err = str(e)
                    use_hs = False
            if hasattr(self, 'hs_status_label'):
                if hs_err:
                    self.hs_status_label.setText(f"<small style='color:#e44'>⚠ {hs_err}</small>")
                elif self.chk_hs_en.isChecked() and use_hs:
                    _zd = getattr(self, '_hs_z_direct', None)
                    f3_hs = find_3db_freq(b_hs_z, a_hs_z, fs)
                    f3_txt = f"-3dB: {f3_hs:.1f}Hz" if f3_hs else ""
                    deq = diff_eq_str(b_hs_z, a_hs_z)
                    if _zd is not None:
                        self.hs_status_label.setText(
                            f"<small style='color:#7a7'>✓ z域直接(Euler) {len(b_hs_z)-1}/{len(a_hs_z)-1}阶"
                            f"{'  ' + f3_txt if f3_txt else ''}"
                            f"<br>{deq}</small>")
                    else:
                        expr = f"({poly_str(num_s)}) / ({poly_str(den_s)})"
                        self.hs_status_label.setText(
                            f"<small style='color:#7a7'>✓ bilinear→H(z) {len(b_hs_z)-1}/{len(a_hs_z)-1}阶"
                            f"{'  ' + f3_txt if f3_txt else ''}"
                            f"<br>H(s) = {expr}"
                            f"<br>{deq}</small>")
                else:
                    self.hs_status_label.setText("<small style='color:#778'>未启用</small>")

            # ── 差分表达式 y[n]=... ──
            use_deq = getattr(self, 'chk_deq_en', None) and self.chk_deq_en.isChecked()
            b_deq, a_deq = None, None
            deq_err = None
            if use_deq:
                try:
                    b_deq = np.array([float(x.strip()) for x in self.deq_b.text().split(',') if x.strip()])
                    a_deq = np.array([float(x.strip()) for x in self.deq_a.text().split(',') if x.strip()])
                    if len(b_deq) == 0 or len(a_deq) == 0:
                        raise ValueError("b/a 至少一个系数")
                except Exception as e:
                    deq_err = str(e)
                    use_deq = False
            if hasattr(self, 'deq_status_label'):
                if deq_err:
                    self.deq_status_label.setText(f"<small style='color:#e44'>⚠ {deq_err}</small>")
                elif getattr(self, 'chk_deq_en', None) and self.chk_deq_en.isChecked() and use_deq:
                    f3_deq = find_3db_freq(b_deq, a_deq, fs)
                    _dfc = getattr(self, '_deq_designed_fc', None)
                    f3d_txt = f"-3dB: {f3_deq:.1f}Hz" if f3_deq else ""
                    if _dfc and f3_deq:
                        f3d_txt += f" (设定{_dfc:.0f}Hz)"
                    deq_str = diff_eq_str(b_deq, a_deq)
                    hz_str = f"({poly_z_str(b_deq)}) / ({poly_z_str(a_deq)})"
                    self.deq_status_label.setText(
                        f"<small style='color:#7a7'>✓ z域直接 {len(b_deq)-1}/{len(a_deq)-1}阶"
                        f"{'  ' + f3d_txt if f3d_txt else ''}"
                        f"<br>H(z) = {hz_str}"
                        f"<br>{deq_str}</small>")
                else:
                    self.deq_status_label.setText("<small style='color:#778'>未启用</small>")

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

            # ── 打杆信号 + 正弦注入（贯穿全程）──
            _use_stick   = getattr(self, 'chk_stick_en', None)
            s_stick      = self._compute_stick_signal() if (_use_stick is None or _use_stick.isChecked()) else np.zeros(N_SIG)
            s_sine_total = self._compute_sine_total()
            signal_ws = signal + s_stick + s_sine_total   # combined input to filters

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
            # 未含Notch版本 — 供H(s)/DEQ级联源使用（Notch最后施加一次）
            out_pt1_td = lfilter(b_pt1, a_pt1, signal_ws)
            out_lkf_td = lfilter(b_lkf, a_lkf, signal_ws)

            # ── H(s) 滤波（源：0=未滤波, 1=PT1, 2=LKF → Notch 统一最后施加）──
            if use_hs:
                hs_src_idx = self.cmb_hs_src.currentIndex() if hasattr(self, 'cmb_hs_src') else 0
                if hs_src_idx == 1:    hs_td_input = out_pt1_td
                elif hs_src_idx == 2:  hs_td_input = out_lkf_td
                else:                  hs_td_input = signal_ws
                out_hs   = lfilter(b_hs_z, a_hs_z, signal)
                out_hs_n = apply_notch(out_hs.copy())
                out_hs_n_td = apply_notch(lfilter(b_hs_z, a_hs_z, hs_td_input))
            else:
                out_hs_n_td = np.zeros(N_SIG)

            # ── 差分表达式 滤波（Notch 统一最后施加）──
            if use_deq:
                deq_src_idx = self.cmb_deq_src.currentIndex() if hasattr(self, 'cmb_deq_src') else 0
                if deq_src_idx == 1:    deq_td_input = out_pt1_td
                elif deq_src_idx == 2:  deq_td_input = out_lkf_td
                else:                   deq_td_input = signal_ws
                out_deq   = lfilter(b_deq, a_deq, signal)
                out_deq_n = apply_notch(out_deq.copy())
                out_deq_n_td = apply_notch(lfilter(b_deq, a_deq, deq_td_input))
            else:
                out_deq_n_td = np.zeros(N_SIG)

            # ── PID 控制器（独立通道：非未过滤源含Notch, PID后不再Notch）──
            use_pid = hasattr(self, 'chk_pid_en') and self.chk_pid_en.isChecked()
            b_pid_z, a_pid_z = None, None
            if use_pid:
                import math
                try:
                    kp = self.pid_kp.value()
                    ki = self.pid_ki.value()
                    kd = self.pid_kd.value()
                    df = self.pid_df.value()
                    tau_d = 1.0 / (2.0 * math.pi * max(df, 1.0))
                    b_pid_z, a_pid_z = custom_tf_to_digital([kd, kp, ki], [tau_d, 1, 0], fs)
                except Exception:
                    use_pid = False
            if use_pid:
                pid_src_idx = self.cmb_pid_src.currentIndex() if hasattr(self, 'cmb_pid_src') else 1
                if pid_src_idx == 1:    pid_td_input = out_pt1_n_td
                elif pid_src_idx == 2:  pid_td_input = out_lkf_n_td
                else:                   pid_td_input = signal_ws
                out_pid_ref = lfilter(b_pid_z, a_pid_z, signal)
                out_pid_td  = lfilter(b_pid_z, a_pid_z, pid_td_input)
            else:
                out_pid_td = np.zeros(N_SIG)
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

            # H(s) 频响（级联 + Notch统一最后）
            _hs_src_pfx = ''
            if use_hs:
                _, H_hs = freqz(b_hs_z, a_hs_z, worN=w_ax)
                if hs_src_idx == 1:
                    H_hs_n = H_pt1 * H_hs * Hn; _hs_src_pfx = 'PT1→'
                elif hs_src_idx == 2:
                    H_hs_n = H_lkf * H_hs * Hn; _hs_src_pfx = 'LKF→'
                else:
                    H_hs_n = H_hs * Hn

            def gd_ms(H):
                ph = -np.unwrap(np.angle(H))
                dw = np.gradient(w_ax)
                return np.gradient(ph) / (dw + 1e-20) / fs * 1000.0

            gd_pt1  = gd_ms(H_pt1);  gd_lkf  = gd_ms(H_lkf)
            gd_pt1n = gd_ms(H_pt1_n); gd_lkfn = gd_ms(H_lkf_n)
            if use_hs:
                gd_hs = gd_ms(H_hs); gd_hsn = gd_ms(H_hs_n)

            # DEQ 频响 + 群延迟（级联 + Notch统一最后）
            _deq_src_pfx = ''
            if use_deq:
                _, H_deq = freqz(b_deq, a_deq, worN=w_ax)
                if deq_src_idx == 1:
                    H_deq_n = H_pt1 * H_deq * Hn; _deq_src_pfx = 'PT1→'
                elif deq_src_idx == 2:
                    H_deq_n = H_lkf * H_deq * Hn; _deq_src_pfx = 'LKF→'
                else:
                    H_deq_n = H_deq * Hn
                gd_deq = gd_ms(H_deq); gd_deqn = gd_ms(H_deq_n)

            # PID 频响（独立, 非未过滤时含源+Notch级联, PID后无Notch）
            _pid_src_pfx = ''
            if use_pid:
                _, H_pid = freqz(b_pid_z, a_pid_z, worN=w_ax)
                if pid_src_idx == 1:
                    H_pid_n = H_pt1_n * H_pid; _pid_src_pfx = 'PT1→'
                elif pid_src_idx == 2:
                    H_pid_n = H_lkf_n * H_pid; _pid_src_pfx = 'LKF→'
                else:
                    H_pid_n = H_pid
                gd_pid = gd_ms(H_pid); gd_pidn = gd_ms(H_pid_n)

            # ── PSD ──
            nperseg = min(4096, N_SIG // 8)
            f_w, P_in   = welch(signal_ws,   fs, nperseg=nperseg)  # 输入（含打杆）
            _,   P_pt1n = welch(out_pt1_n_td, fs, nperseg=nperseg)  # PT1+N filtered
            _,   P_lkfn = welch(out_lkf_n_td, fs, nperseg=nperseg)  # LKF+N filtered
            # baseline noise-only (thin dashed reference)
            _,   P_pt1_ref = welch(out_pt1_n, fs, nperseg=nperseg)
            _,   P_lkf_ref = welch(out_lkf_n, fs, nperseg=nperseg)
            # H(s) PSD
            if use_hs:
                _, P_hs_ref = welch(out_hs_n, fs, nperseg=nperseg)
                _, P_hsn    = welch(out_hs_n_td, fs, nperseg=nperseg)
            # DEQ PSD
            if use_deq:
                _, P_deq_ref = welch(out_deq_n, fs, nperseg=nperseg)
                _, P_deqn    = welch(out_deq_n_td, fs, nperseg=nperseg)
            # PID PSD
            if use_pid:
                _, P_pid_ref = welch(out_pid_ref, fs, nperseg=nperseg)
                _, P_pid     = welch(out_pid_td,  fs, nperseg=nperseg)
            # TEO
            use_teo = getattr(self, 'chk_teo_en', None) and self.chk_teo_en.isChecked()
            if use_teo:
                src_idx = self.cmb_teo_src.currentIndex() if hasattr(self, 'cmb_teo_src') else 0
                if src_idx == 1:    teo_input = out_pt1_n_td
                elif src_idx == 2:  teo_input = out_lkf_n_td
                elif src_idx == 3 and use_hs: teo_input = out_hs_n_td  # 已含Notch
                elif src_idx == 4 and use_deq: teo_input = out_deq_n_td
                else:               teo_input = signal_ws
                teo_out = teo(teo_input)
                teo_sc = getattr(self, 'teo_scale', None)
                if teo_sc is not None:
                    teo_out = teo_out * teo_sc.value()
                _, P_teo = welch(teo_out, fs, nperseg=nperseg)
            mask = (f_w >= 0.5) & (f_w <= 1000)

            # >v<🕐抖帧公式 - dec=ceil(t_span*FS/6000); 目标显示6000点; 缩放到小范围dec=1消除显示混叠
            # ── 时域（自适应抖帧：目标约6000个显示点，缩放后分辨率自动提升，高频注入不混叠）──
            _tv4 = self._saved_views[4]
            _t_span = max(0.1, ((_tv4[0][1] - _tv4[0][0]) if _tv4 else float(N_SECONDS)))
            dec = max(1, int(np.ceil(_t_span * fs / 6000)))  # zoom到小范围时 dec=1、全视图时 dec=10
            _disp_hz = fs / dec  # 当前显示分辨率（奈奎斯特限制在 disp_hz/2）
            t   = np.arange(N_SIG)[::dec] / fs
            sp  = signal_ws[::dec]          # 输入（噪声+打杆+注入）
            sk  = s_stick[::dec]            # 纯打杆
            si  = s_sine_total[::dec]       # 正弦注入
            pp  = out_pt1_n_td[::dec]       # PT1 响应
            lp  = out_lkf_n_td[::dec]       # LKF 响应
            hp  = out_hs_n_td[::dec]  if use_hs  else None   # H(s) 响应
            dp  = out_deq_n_td[::dec] if use_deq else None   # 差分表达式响应
            pidp = out_pid_td[::dec]  if use_pid else None   # PID 响应
            tp_ = teo_out[::dec]      if use_teo else None   # TEO 输出

            # ══════════════════════════════════════════════
            #  绘图
            # ══════════════════════════════════════════════
            en = [chk.isChecked() for chk in self.chk_show]
            n_en = sum(en)
            self.fig.clear()
            T = self._DARK if self._dark_mode else self._LIGHT
            self.fig.set_facecolor(T['fig'])
            if n_en == 0:
                self.canvas.draw_idle()
                return
            _all_hr  = [3.0, 2.0, 1.4, 2.8, 2.2]
            _en_hr  = [_all_hr[i] for i, e in enumerate(en) if e]
            if n_en > 1:
                gs = GridSpec(n_en, 1, figure=self.fig,
                              height_ratios=_en_hr,
                              hspace=0.28,
                              left=0.065, right=0.975, top=0.965, bottom=0.045)
            else:
                gs = None
                self.fig.subplots_adjust(left=0.07, right=0.975, top=0.955, bottom=0.085)
            _axes = []; _gi = 0
            for _ei in en:
                if _ei:
                    if gs is not None:
                        _axes.append(self.fig.add_subplot(gs[_gi]))
                    else:
                        _axes.append(self.fig.add_subplot(1, 1, 1))
                    _gi += 1
                else:
                    _axes.append(None)
            ax1, ax2, ax3, ax4, ax5 = _axes

            C_PT1 = T['pt1']; C_LKF = T['lkf']; C_TEO = T['teo']; C_GRID = T['grid']
            C_DEQ = T.get('deq', '#e07830')
            C_HS = T['hs']
            C_PID = T.get('pid', '#e0a040')

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
                if use_pt1: ax1.plot(f_ax, mg(H_pt1),   color=C_PT1, lw=0.6, ls="--", alpha=0.55,
                                     label=f"PT1 {self.fc_pt1.value():.0f}Hz")
                if use_lkf: ax1.plot(f_ax, mg(H_lkf),   color=C_LKF, lw=0.6, ls="--", alpha=0.55, label="LKF")
                if use_pt1: ax1.plot(f_ax, mg(H_pt1_n), color=C_PT1, lw=1.3, label="PT1+Notch")
                if use_lkf: ax1.plot(f_ax, mg(H_lkf_n), color=C_LKF, lw=1.3, label="LKF+Notch")
                if use_hs:
                    ax1.plot(f_ax, mg(H_hs),   color=C_HS, lw=0.6, ls="--", alpha=0.55, label='H(s)')
                    ax1.plot(f_ax, mg(H_hs_n), color=C_HS, lw=1.3, label=f"{_hs_src_pfx}H(s)+N")
                if use_deq:
                    ax1.plot(f_ax, mg(H_deq),   color=C_DEQ, lw=0.6, ls="--", alpha=0.55, label="DEQ")
                    ax1.plot(f_ax, mg(H_deq_n), color=C_DEQ, lw=1.3, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid:
                    ax1.plot(f_ax, mg(H_pid),   color=C_PID, lw=0.6, ls="--", alpha=0.55, label="PID")
                    ax1.plot(f_ax, mg(H_pid_n), color=C_PID, lw=1.3, label=f"{_pid_src_pfx}PID")
                bands(ax1); ax1.set_xscale(xsc); ax1.set_xlim(*xlim)
                ax1.set_ylabel(ylabel_mag, color=T['label'], fontsize=8)
                ax1.set_title("陀螺滤波器分析仪  PT1 vs 2-state LKF (+Notch)  |  fs=2kHz",
                              color=T['title'], fontsize=9)
                ax1.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                           framealpha=0.85, loc="lower left", ncol=2)

            # ── 2. 相频 ──────────────────────────────────
            if ax2 is not None:
                if use_pt1: ax2.plot(f_ax, np.angle(H_pt1,  deg=True), color=C_PT1, lw=0.6, ls="--", alpha=0.55)
                if use_lkf: ax2.plot(f_ax, np.angle(H_lkf,  deg=True), color=C_LKF, lw=0.6, ls="--", alpha=0.55)
                if use_pt1: ax2.plot(f_ax, np.angle(H_pt1_n, deg=True), color=C_PT1, lw=1.2, label="PT1+N")
                if use_lkf: ax2.plot(f_ax, np.angle(H_lkf_n, deg=True), color=C_LKF, lw=1.2, label="LKF+N")
                if use_hs:
                    ax2.plot(f_ax, np.angle(H_hs,   deg=True), color=C_HS, lw=0.6, ls="--", alpha=0.55)
                    ax2.plot(f_ax, np.angle(H_hs_n, deg=True), color=C_HS, lw=1.2, label=f"{_hs_src_pfx}H(s)+N")
                if use_deq:
                    ax2.plot(f_ax, np.angle(H_deq,   deg=True), color=C_DEQ, lw=0.6, ls="--", alpha=0.55)
                    ax2.plot(f_ax, np.angle(H_deq_n, deg=True), color=C_DEQ, lw=1.2, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid:
                    ax2.plot(f_ax, np.angle(H_pid,   deg=True), color=C_PID, lw=0.6, ls="--", alpha=0.55)
                    ax2.plot(f_ax, np.angle(H_pid_n, deg=True), color=C_PID, lw=1.2, label=f"{_pid_src_pfx}PID")
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
                if use_pt1: ax3.plot(f_ax, np.clip(gd_pt1,  -clip, clip), color=C_PT1, lw=0.75, ls="--", alpha=0.55)
                if use_lkf: ax3.plot(f_ax, np.clip(gd_lkf,  -clip, clip), color=C_LKF, lw=0.75, ls="--", alpha=0.55)
                if use_pt1: ax3.plot(f_ax, np.clip(gd_pt1n, -clip, clip), color=C_PT1, lw=0.6, label="PT1+N")
                if use_lkf: ax3.plot(f_ax, np.clip(gd_lkfn, -clip, clip), color=C_LKF, lw=0.6, label="LKF+N")
                if use_hs:
                    ax3.plot(f_ax, np.clip(gd_hs,  -clip, clip), color=C_HS, lw=0.75, ls="--", alpha=0.55)
                    ax3.plot(f_ax, np.clip(gd_hsn, -clip, clip), color=C_HS, lw=0.6, label=f"{_hs_src_pfx}H(s)+N")
                if use_deq:
                    ax3.plot(f_ax, np.clip(gd_deq,  -clip, clip), color=C_DEQ, lw=0.75, ls="--", alpha=0.55)
                    ax3.plot(f_ax, np.clip(gd_deqn, -clip, clip), color=C_DEQ, lw=0.6, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid:
                    ax3.plot(f_ax, np.clip(gd_pid,  -clip, clip), color=C_PID, lw=0.75, ls="--", alpha=0.55)
                    ax3.plot(f_ax, np.clip(gd_pidn, -clip, clip), color=C_PID, lw=0.6, label=f"{_pid_src_pfx}PID")
                bands(ax3); ax3.axhline(0, color=T['href'], lw=0.7)
                ax3.set_xscale(xsc); ax3.set_xlim(*xlim)
                ax3.set_ylabel("Grp Dly (ms)", color=T['label'], fontsize=8)
                ax3.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                           framealpha=0.85, loc="upper right", ncol=2)

            # ── 4. PSD ──────────────────────────────────
            if ax4 is not None:
                # 功率谱(dps²/Hz) 或 幅度谱 ASD(dps/√Hz)；由 btn_psd_amp 切换
                _amp = getattr(self, '_psd_amp_mode', False)
                def _cvt(P): return np.sqrt(np.maximum(P, 0)) if _amp else P
                psd_plot = ax4.semilogy if self._log_yaxis else ax4.plot
                psd_plot(f_w[mask], _cvt(P_in[mask]),          color=T['noise_psd'], lw=0.6,  label="输入+打杆")
                if use_pt1: psd_plot(f_w[mask], _cvt(P_pt1_ref[mask]), color=C_PT1, lw=0.5, ls="--", alpha=0.35)
                if use_pt1: psd_plot(f_w[mask], _cvt(P_pt1n[mask]),   color=C_PT1, lw=1.2,  label="PT1+N")
                if use_lkf: psd_plot(f_w[mask], _cvt(P_lkf_ref[mask]), color=C_LKF, lw=0.5, ls="--", alpha=0.35)
                if use_lkf: psd_plot(f_w[mask], _cvt(P_lkfn[mask]),   color=C_LKF, lw=1.2,  label="LKF+N")
                if use_hs:
                    psd_plot(f_w[mask], _cvt(P_hs_ref[mask]), color=C_HS, lw=0.5, ls="--", alpha=0.35)
                    psd_plot(f_w[mask], _cvt(P_hsn[mask]),    color=C_HS, lw=1.2, label=f"{_hs_src_pfx}H(s)+N")
                if use_deq:
                    psd_plot(f_w[mask], _cvt(P_deq_ref[mask]), color=C_DEQ, lw=0.5, ls="--", alpha=0.35)
                    psd_plot(f_w[mask], _cvt(P_deqn[mask]),    color=C_DEQ, lw=1.2, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid:
                    psd_plot(f_w[mask], _cvt(P_pid_ref[mask]), color=C_PID, lw=0.5, ls="--", alpha=0.35)
                    psd_plot(f_w[mask], _cvt(P_pid[mask]),     color=C_PID, lw=1.2, label=f"{_pid_src_pfx}PID")
                if use_teo:
                    psd_plot(f_w[mask], _cvt(P_teo[mask]),    color=C_TEO, lw=1.0, label="TEO")
                for fr, col in [(self.fr1.value(), T['lkf']), (self.fr2.value(), T['pt1'])]:  # fr1=lkf color, fr2=pt1 color
                    ax4.axvline(fr, color=col, lw=0.65, ls=":", alpha=0.8)
                ax4.axvspan(0, 30, alpha=0.09, color=T['band'], zorder=0)
                ax4.axvline(500, color=T['xmark'], lw=0.6, ls="--", alpha=0.50)
                ax4.set_xlim(0, 1000)
                _ylabel = ("ASD (dps/√Hz)" if _amp else "PSD (dps²/Hz)") + (" — log" if self._log_yaxis else "")
                ax4.set_ylabel(_ylabel, color=T['label'], fontsize=8)
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
                                    color=T['dot'], s=22, zorder=6)                # 正弦注入曲线
                has_sine = np.any(np.abs(si) > 1e-9)
                if has_sine:
                    ax5.plot(t, si, color=T['sine'], lw=0.5, alpha=0.30, label="正弦注入")                # 删除模式：1/200 视图宽度区域（含锚点保护不显示）
                if self._stick_mode == 'del' and self._stick_pts:
                    _sv4 = self._saved_views[4] or ([0.0, float(N_SECONDS)], None)
                    zone = (_sv4[0][1] - _sv4[0][0]) / 200.0
                    for pt in self._stick_pts:
                        ax5.axvspan(pt[0] - zone/2, pt[0] + zone/2,
                                    alpha=0.15, color=T['dot'], zorder=2)
                # 正弦注入范围（低饱和浅蓝，激活时显示3区段）
                for it in getattr(self, '_sine_items', []):
                    t0v = it['t0'].value(); t1v = it['t1'].value()
                    if it['btn_rng'].isChecked():
                        dur = max(t1v - t0v, 0.01)
                        ax5.axvspan(t0v,          t0v + dur/3,  alpha=0.10, color='#7799bb', zorder=1)
                        ax5.axvspan(t0v + dur/3,  t1v - dur/3, alpha=0.17, color='#7799bb', zorder=1)
                        ax5.axvspan(t1v - dur/3,  t1v,         alpha=0.10, color='#7799bb', zorder=1)
                        ax5.axvline(t0v,          color='#7799bb', lw=1.0, ls='--', alpha=0.75, zorder=5)
                        ax5.axvline(t0v + dur/3,  color='#7799bb', lw=0.6, ls=':',  alpha=0.55, zorder=5)
                        ax5.axvline(t1v - dur/3,  color='#7799bb', lw=0.6, ls=':',  alpha=0.55, zorder=5)
                        ax5.axvline(t1v,          color='#7799bb', lw=1.0, ls='--', alpha=0.75, zorder=5)
                    else:
                        ax5.axvspan(t0v, t1v, alpha=0.08, color='#7799bb', zorder=0)
                # 滤波输出
                if use_pt1: ax5.plot(t, pp, color=C_PT1, lw=0.65, label="PT1+N")
                if use_lkf: ax5.plot(t, lp, color=C_LKF, lw=0.65, label="LKF+N")
                if use_hs and hp is not None:
                    ax5.plot(t, hp, color=C_HS, lw=0.65, label=f"{_hs_src_pfx}H(s)+N")
                if use_deq and dp is not None:
                    ax5.plot(t, dp, color=C_DEQ, lw=0.65, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid and pidp is not None:
                    ax5.plot(t, pidp, color=C_PID, lw=0.65, label=f"{_pid_src_pfx}PID")
                if use_teo and tp_ is not None:
                    ax5.plot(t, tp_, color=C_TEO, lw=0.55, alpha=0.75, label="TEO")
                # 模式提示
                _hint = {"add": "✚ 新增", "del": "✖ 删除(1/200)", "adj": "⇄ 调整"}
                _active_rng = hasattr(self, '_sine_items') and any(it['btn_rng'].isChecked() for it in self._sine_items)
                _hint_str = "⇄ 正弦范围" if _active_rng else _hint.get(self._stick_mode, '')
                ax5.set_title(f"时域  [{_hint_str}]  显示{_disp_hz:.0f}Hz（缩放可提升）  Y轴手动缩放",
                              color=T['label'], fontsize=7.5, pad=2)
                ax5.set_xlabel("Time (s)", color=T['label'], fontsize=8)
                ax5.set_ylabel("dps",     color=T['label'], fontsize=8)
                ax5.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                           framealpha=0.85, loc="upper right", ncol=4)
            # Restore saved views for all axes (zoom/pan preserved across ticks)
            _y_auto = getattr(self, '_y_auto', [False] * 5)
            for _i, _ax in enumerate([ax1, ax2, ax3, ax4, ax5]):
                if _ax is not None and self._saved_views[_i] is not None:
                    _ax.set_xlim(self._saved_views[_i][0])
                    if _y_auto[_i]:
                        _ax.relim(); _ax.autoscale_view(scalex=False, scaley=True)
                    else:
                        _ax.set_ylim(self._saved_views[_i][1])
            self._last_axes = [ax1, ax2, ax3, ax4, ax5]

            # 置顶处理：将 _top_filter 对应滤波器的所有 label 匹配线提升 zorder
            _top = getattr(self, '_top_filter', None)
            if _top is not None:
                _top_kw = {'pt1': 'PT1', 'lkf': 'LKF', 'hs': 'H(s)', 'pid': 'PID', 'deq': 'DEQ'}.get(_top, '')
                for _ax in filter(None, [ax1, ax2, ax3, ax4, ax5]):
                    for _ln in _ax.get_lines():
                        if _top_kw in (_ln.get_label() or ''):
                            _ln.set_zorder(4)

            self.canvas.draw()
