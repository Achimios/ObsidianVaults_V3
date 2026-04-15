# draw_mixin.py — 绘图核心 + 轴切换 + LKF 同步
# _toggle_x / _toggle_y / _sync_lkf_to_pt1 / _do_update

import numpy as np
from scipy.signal import freqz, lfilter, welch
from matplotlib.gridspec import GridSpec
from constants import FS, N_SECONDS, N_SIG
from dsp import (
    pt1_coeffs, pt1_coeffs_bilinear, lkf_coeffs, notch_coeffs,
    resonance, resonance_dist, perlin_noise_1d,
    custom_tf_to_digital, teo,
    find_3db_freq, diff_eq_str, poly_str, poly_z_str,
    pid_iterate,
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
                 it['fm_smooth'].value()   if 'fm_smooth'   in it else 3,
                 it['p_base_freq'].value() if 'p_base_freq' in it else 20.0,
                 it['p_persist'].value()   if 'p_persist'   in it else 0.6,
                 it['p_lacunar'].value()   if 'p_lacunar'   in it else 2.0,
                 it['p_seed'].value()      if 'p_seed'      in it else 0,
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
                w_rms         = item['w_rms'].value(); p_rms = item['p_rms'].value()
                p_oct         = int(item['p_oct'].value())
                p_base_freq_v = item['p_base_freq'].value() if 'p_base_freq' in item else 20.0
                p_persist_v   = item['p_persist'].value()   if 'p_persist'   in item else 0.6
                p_lacunar_v   = item['p_lacunar'].value()   if 'p_lacunar'   in item else 2.0
                p_seed_v      = int(item['p_seed'].value()) if 'p_seed'      in item else 0
                fm_smooth_v   = int(item['fm_smooth'].value()) if 'fm_smooth' in item else 3
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
                        lfo = perlin_noise_1d(N_SIG, octaves=fm_smooth_v, seed=seed_fm)
                        phase += 2 * np.pi * f_mod_v * np.cumsum(lfo) / FS
                    total += (amp / n_pk) * np.sin(phase) * window
                if w_rms > 0 or p_rms > 0:
                    seed = int(f_start * 100 + amp + t0 * 10) % (2**31)
                    rng  = np.random.default_rng(seed)
                    loc  = np.zeros(N_SIG)
                    if w_rms > 0: loc += rng.standard_normal(N_SIG) * w_rms
                    if p_rms > 0: loc += perlin_noise_1d(
                        N_SIG, octaves=p_oct,
                        base_freq=p_base_freq_v, persistence=p_persist_v,
                        lacunarity=p_lacunar_v,
                        seed=(seed + 1 + p_seed_v) % (2**31)) * p_rms
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
            # 切换时重置幅频图Y轴到新模式默认值（|R）
            ylim_def = [-65.0, 8.0] if checked else [-0.05, 1.15]
            sv = self._saved_views[0]
            xl = list(sv[0]) if sv else [0.0, 1000.0]
            self._saved_views[0] = (xl, ylim_def)
            self._views_reset = True   # 阻止 _do_update 开头覆写
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
            """Binary search r_meas until LKF -3dB freq ≈ PT1 actual -3dB.
            同步始终用H=[1,0]模式(obs_mode=2)搜索。"""
            _pt1_bil = getattr(self, 'btn_pt1_bil', None) and self.btn_pt1_bil.isChecked()
            _pt1_fn = pt1_coeffs_bilinear if _pt1_bil else pt1_coeffs
            b_p, a_p = _pt1_fn(self.fc_pt1.value(), FS)
            f3_actual = find_3db_freq(b_p, a_p, FS)
            fc_target = f3_actual if f3_actual else self.fc_pt1.value()
            w_t = 2 * np.pi * fc_target / FS; tgt = 1.0 / np.sqrt(2)
            lo, hi = 1e-5, 1e5
            for _ in range(40):  # log2(1e10)≈33, 40步精度远超spinbox分辨率
                mid = np.sqrt(lo * hi)
                b_l, a_l = lkf_coeffs(self.q_omega.value(), self.q_bias.value(), mid, FS,
                                       obs_mode=2)  # 始终用H=[1,0]模式搜索
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
            _pt1_bil = getattr(self, 'btn_pt1_bil', None) and self.btn_pt1_bil.isChecked()
            _pt1_fn = pt1_coeffs_bilinear if _pt1_bil else pt1_coeffs
            b_pt1, a_pt1 = _pt1_fn(self.fc_pt1.value(), fs)
            _lkf_combo = self.cmb_lkf_obs.currentIndex() if hasattr(self, 'cmb_lkf_obs') else 1
            _lkf_obs = [0, 2][_lkf_combo]  # combo idx→obs_mode: 0=原始(0), 1=H=[1,0](2)
            b_lkf, a_lkf = lkf_coeffs(
                self.q_omega.value(), self.q_bias.value(), self.r_meas.value(), fs,
                obs_mode=_lkf_obs)

            # PT1 实际 -3dB 标注 + DEQ
            if hasattr(self, 'pt1_info'):
                f3 = find_3db_freq(b_pt1, a_pt1, fs)
                fc_set = self.fc_pt1.value()
                _method = '双线性 (Tustin)' if _pt1_bil else '前向欧拉法 (Betaflight)'
                _deq = diff_eq_str(b_pt1, a_pt1)
                _b_str = ', '.join(f'{v:.5g}' for v in b_pt1)
                _a_str = ', '.join(f'{v:.5g}' for v in a_pt1)
                _dc_pt1 = float(np.abs(freqz(b_pt1, a_pt1, worN=[0])[1][0]))
                _info_pt1 = f"<small style='color:#778'>{_method}"
                if f3 is not None:
                    _info_pt1 += f"<br>实际-3dB: {f3:.1f}Hz (设定{fc_set:.0f}Hz)  DC: {_dc_pt1:.4f}"
                _info_pt1 += f"<br>{_deq}"
                _info_pt1 += f"<br>b=[{_b_str}]  a=[{_a_str}]</small>"
                self.pt1_info.setText(_info_pt1)
            # LKF info: -3dB频率 + DEQ + b,a系数
            if hasattr(self, 'lkf_info'):
                f3_lkf = find_3db_freq(b_lkf, a_lkf, fs)
                _obs_names = ['原始 H=[1,1]', 'H=[1,0]']
                _obs_lab = _obs_names[_lkf_combo] if _lkf_combo < 2 else '?'
                _b_str = ', '.join(f'{v:.5g}' for v in b_lkf)
                _a_str = ', '.join(f'{v:.5g}' for v in a_lkf)
                # peak gain: KF DC恒=1(无偏估计), 但H=[1,1]有谐振峰
                _w_full, _H_full = freqz(b_lkf, a_lkf, worN=2048)
                _peak = float(np.max(np.abs(_H_full)))
                _deq_lkf = diff_eq_str(b_lkf, a_lkf)
                _info = f"<small style='color:#778'>{_obs_lab}"
                if f3_lkf is not None:
                    _info += f"<br>-3dB: {f3_lkf:.1f}Hz  peak: {_peak:.4f}"
                _info += f"<br>{_deq_lkf}"
                _info += f"<br>b=[{_b_str}]<br>a=[{_a_str}]</small>"
                self.lkf_info.setText(_info)
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
                        hz = f"({poly_z_str(b_hs_z)}) / ({poly_z_str(a_hs_z)})"
                        self.hs_status_label.setText(
                            f"<small style='color:#7a7'>✓ z域直接(Euler) {len(b_hs_z)-1}/{len(a_hs_z)-1}阶"
                            f"{'  ' + f3_txt if f3_txt else ''}"
                            f"<br>H(z) = {hz}"
                            f"<br>{deq}</small>")
                    else:
                        expr = f"({poly_str(num_s)}) / ({poly_str(den_s)})"
                        hz = f"({poly_z_str(b_hs_z)}) / ({poly_z_str(a_hs_z)})"
                        self.hs_status_label.setText(
                            f"<small style='color:#7a7'>✓ bilinear→H(z) {len(b_hs_z)-1}/{len(a_hs_z)-1}阶"
                            f"{'  ' + f3_txt if f3_txt else ''}"
                            f"<br>H(s) = {expr}"
                            f"<br>H(z) = {hz}"
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
                  self.perlin_base_freq.value(), self.perlin_persist.value(),
                  self.perlin_lacunar.value(), self.perlin_coord.value(), self.perlin_seed.value(),
                  self.fr1.value(), self.gain_r1.value(), self.qr1.value(),
                  self.chk_r1.isChecked(),
                  self.fr2.value(), self.gain_r2.value(), self.qr2.value(),
                  self.chk_r2.isChecked(),
                  self.chk_res_dist.isChecked(),
                  self.n_res_peaks.value(), self.f_res_spread.value(), self.seed_res.value())
            if self._noise_key != nk:
                rng = np.random.default_rng(42)
                w   = rng.standard_normal(N_SIG) * self.white_rms.value()
                p   = perlin_noise_1d(N_SIG,
                                      octaves=self.perlin_oct.value(),
                                      persistence=self.perlin_persist.value(),
                                      lacunarity=self.perlin_lacunar.value(),
                                      base_freq=self.perlin_base_freq.value(),
                                      coord_offset=float(self.perlin_coord.value()),
                                      seed=self.perlin_seed.value()) \
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

            # ── PID 逐帧迭代闭环（sensor noise模型: noise不被积分器累积）──
            # setpoint→error→PID→Δω→actual[n]=prev+Δω→unfilt=actual+noise→F→filt→vs setpoint
            use_pid = hasattr(self, 'chk_pid_en') and self.chk_pid_en.isChecked()
            pid_solo = use_pid and hasattr(self, 'chk_pid_solo') and self.chk_pid_solo.isChecked()
            pid_src_idx = 0
            out_pid_unfilt = out_pid_filt = None
            # 解析闭环TF保留（Bode参考虚线）
            b_cl_sp = a_cl = b_cl_n = b_cl0_sp = a_cl0 = None
            if use_pid:
                try:
                    kp = self.pid_kp.value()
                    ki = self.pid_ki.value()
                    kd = self.pid_kd.value()
                    df = self.pid_df.value()
                    pid_src_idx = self.cmb_pid_src.currentIndex() if hasattr(self, 'cmb_pid_src') else 0
                    # Feedback filter coefficients (independent copy, not reusing open-loop waveforms)
                    if pid_src_idx == 1:      # PT1
                        b_pf, a_pf = _pt1_fn(self.fc_pt1.value(), fs)
                    elif pid_src_idx == 2:    # LKF
                        b_pf, a_pf = lkf_coeffs(self.q_omega.value(), self.q_bias.value(),
                                                 self.r_meas.value(), fs, obs_mode=_lkf_obs)
                    elif pid_src_idx == 3:    # DEQ (may cascade through PT1/LKF if DEQ source is set)
                        b_pf_deq = np.array([float(x.strip()) for x in self.deq_b.text().split(',') if x.strip()])
                        a_pf_deq = np.array([float(x.strip()) for x in self.deq_a.text().split(',') if x.strip()])
                        _deq_src_for_pid = self.cmb_deq_src.currentIndex() if hasattr(self, 'cmb_deq_src') else 0
                        if _deq_src_for_pid == 1:    # DEQ源=PT1 → 串级PT1→DEQ
                            b_pf = np.convolve(b_pt1, b_pf_deq)
                            a_pf = np.convolve(a_pt1, a_pf_deq)
                        elif _deq_src_for_pid == 2:  # DEQ源=LKF → 串级LKF→DEQ
                            b_pf = np.convolve(b_lkf, b_pf_deq)
                            a_pf = np.convolve(a_lkf, a_pf_deq)
                        else:
                            b_pf, a_pf = b_pf_deq, a_pf_deq
                    else:                      # 未滤波
                        b_pf, a_pf = np.array([1.0]), np.array([1.0])
                    # Notch filters for PID feedback path
                    b_notch_l, a_notch_l = [], []
                    if use_n1:
                        b_notch_l.append(b_n1); a_notch_l.append(a_n1)
                    if use_n2:
                        b_notch_l.append(b_n2); a_notch_l.append(a_n2)
                    # Setpoint = stick + sine (clean, no noise)
                    setpoint_clean = s_stick + s_sine_total
                    # Run iterative PID
                    out_pid_unfilt, out_pid_filt = pid_iterate(
                        setpoint_clean, signal, kp, ki, kd, df,
                        b_pf, a_pf, b_notch_l, a_notch_l, fs)
                    # ── 解析闭环TF（Bode参考用）──
                    tau_d = 1.0 / (2.0 * np.pi * max(df, 1.0))
                    b_c, a_c = custom_tf_to_digital([kd, kp, ki], [tau_d, 1, 0], fs)
                    Ts = 1.0 / fs
                    b_g = np.array([Ts / 2, Ts / 2])
                    a_g = np.array([1.0, -1.0])
                    def _cascade_notch(b, a):
                        if use_n1: b = np.convolve(b, b_n1); a = np.convolve(a, a_n1)
                        if use_n2: b = np.convolve(b, b_n2); a = np.convolve(a, a_n2)
                        return b, a
                    b_f_an, a_f_an = _cascade_notch(np.array(b_pf, dtype=float), np.array(a_pf, dtype=float))
                    NcNg = np.convolve(b_c, b_g)
                    b_cl_sp = np.convolve(NcNg, a_f_an)
                    d1 = np.convolve(np.convolve(a_c, a_g), a_f_an)
                    d2 = np.convolve(NcNg, b_f_an)
                    ml = max(len(d1), len(d2))
                    a_cl = np.zeros(ml); a_cl[:len(d1)] += d1; a_cl[:len(d2)] += d2
                    b_cl_n = -d2
                    b_cl0_sp = NcNg.copy()
                    d0 = np.convolve(a_c, a_g)
                    ml0 = max(len(d0), len(NcNg))
                    a_cl0 = np.zeros(ml0); a_cl0[:len(d0)] += d0; a_cl0[:len(NcNg)] += NcNg
                except Exception:
                    use_pid = False
                    pid_solo = False
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

            # PID 闭环频响: 虚线=解析T_sp, 点线=解析T_n, 实线=FFT估算
            _pid_src_pfx = ''
            if use_pid:
                _, H_pid   = freqz(b_cl0_sp, a_cl0, worN=w_ax)  # T_cl (F=1, dashed)
                _, H_pid_n = freqz(b_cl_sp,  a_cl,  worN=w_ax)  # T_sp (with F, analytical)
                _, H_pid_tn = freqz(b_cl_n,  a_cl,  worN=w_ax)  # T_n (noise rejection)
                if pid_src_idx == 1:   _pid_src_pfx = 'PT1→'
                elif pid_src_idx == 2: _pid_src_pfx = 'LKF→'
                elif pid_src_idx == 3: _pid_src_pfx = 'DEQ→'
                gd_pid = gd_ms(H_pid); gd_pidn = gd_ms(H_pid_n); gd_pid_tn = gd_ms(H_pid_tn)
                # FFT-based transfer function estimate: H_fft = FFT(gyro_filt) / FFT(setpoint)
                _sp_clean = s_stick + s_sine_total
                _nfft = min(8192, N_SIG)
                _sp_fft = np.fft.rfft(_sp_clean, n=_nfft)
                _gf_fft = np.fft.rfft(out_pid_filt[:_nfft], n=_nfft)
                _gu_fft = np.fft.rfft(out_pid_unfilt[:_nfft], n=_nfft)
                _fft_freqs = np.fft.rfftfreq(_nfft, d=1.0/fs)
                # Avoid division by zero
                _sp_mag = np.abs(_sp_fft)
                _sp_mask = _sp_mag > np.max(_sp_mag) * 1e-6
                H_pid_fft = np.ones(len(_sp_fft), dtype=complex)
                H_pid_fft[_sp_mask] = _gf_fft[_sp_mask] / _sp_fft[_sp_mask]

            # ── PSD ──
            nperseg = min(4096, N_SIG // 8)
            f_w, P_in   = welch(signal_ws,   fs, nperseg=nperseg)  # 输入（含打杆）
            _,   P_sp   = welch(s_stick + s_sine_total, fs, nperseg=nperseg)  # pure setpoints
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
            # PID PSD (iterative results)
            if use_pid:
                _, P_pid_unfilt = welch(out_pid_unfilt, fs, nperseg=nperseg)
                _, P_pid_filt   = welch(out_pid_filt,   fs, nperseg=nperseg)
            # TEO
            use_teo = getattr(self, 'chk_teo_en', None) and self.chk_teo_en.isChecked()
            if use_teo:
                src_idx = self.cmb_teo_src.currentIndex() if hasattr(self, 'cmb_teo_src') else 0
                if src_idx == 1:    teo_input = out_pt1_n_td
                elif src_idx == 2:  teo_input = out_lkf_n_td
                elif src_idx == 3 and use_hs: teo_input = out_hs_n_td  # 已含Notch
                elif src_idx == 4 and use_deq: teo_input = out_deq_n_td
                elif src_idx == 5 and use_pid: teo_input = out_pid_filt
                elif src_idx == 6 and use_pid: teo_input = out_pid_unfilt
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
            pid_uf = out_pid_unfilt[::dec] if use_pid else None  # PID gyro_unfiltered
            pid_fl = out_pid_filt[::dec]   if use_pid else None  # PID gyro_filtered
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
            # >v<📐子图顺序 - _all_hr[i]对应逻辑索引: 0=幅频 1=相频 2=群延迟 3=PSD 4=时域
            _all_hr  = [2.0, 2.0, 1.4, 2.8, 2.8]
            # _DISP: 从上到下的物理显示顺序（值=逻辑索引）
            # 改这一行就能重排子图，不用动其他任何代码
            # 当前: 幅频→相频→群延迟→时域→PSD
            _DISP = [0, 1, 2, 4, 3]
            # 按显示顺序取 checkbox 启用状态和对应高度
            _disp_en = [en[i] for i in _DISP]
            _en_hr  = [_all_hr[_DISP[j]] for j, e in enumerate(_disp_en) if e]
            if n_en > 1:
                gs = GridSpec(n_en, 1, figure=self.fig,
                              height_ratios=_en_hr,
                              hspace=0.28,
                              left=0.065, right=0.975, top=0.965, bottom=0.045)
            else:
                gs = None
                self.fig.subplots_adjust(left=0.07, right=0.975, top=0.955, bottom=0.085)
            # 按显示顺序创建 axes，然后映射回逻辑索引 ax1-ax5
            _axes_disp = []; _gi = 0
            for de in _disp_en:
                if de:
                    if gs is not None:
                        _axes_disp.append(self.fig.add_subplot(gs[_gi]))
                    else:
                        _axes_disp.append(self.fig.add_subplot(1, 1, 1))
                    _gi += 1
                else:
                    _axes_disp.append(None)
            _ax_map = [None] * 5
            for di, li in enumerate(_DISP):
                _ax_map[li] = _axes_disp[di]
            ax1, ax2, ax3, ax4, ax5 = _ax_map

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
            # pid_solo: 只显示PID源滤波器Bode + PID闭环曲线
            _show_pt1 = use_pt1 and (not pid_solo or pid_src_idx == 1)
            _show_lkf = use_lkf and (not pid_solo or pid_src_idx == 2)
            _show_hs  = use_hs  and not pid_solo
            _show_deq = use_deq and (not pid_solo or pid_src_idx == 3)
            if ax1 is not None:
                if self._log_yaxis:
                    mg = lambda h: 20 * np.log10(np.abs(h) + 1e-15)
                    ax1.set_ylim(-65, 8); ax1.axhline(-3, color=T['href'], lw=0.7, ls=":")
                    ylabel_mag = "Gain (dB)"
                else:
                    mg = np.abs
                    ax1.set_ylim(-0.05, 1.15); ax1.axhline(1.0, color=T['href'], lw=0.7, ls=":")
                    ylabel_mag = "Gain (×)"
                if _show_pt1: ax1.plot(f_ax, mg(H_pt1),   color=C_PT1, lw=0.6, ls="--", alpha=0.55,
                                     label=f"PT1 {self.fc_pt1.value():.0f}Hz")
                if _show_lkf: ax1.plot(f_ax, mg(H_lkf),   color=C_LKF, lw=0.6, ls="--", alpha=0.55, label="LKF")
                if _show_pt1: ax1.plot(f_ax, mg(H_pt1_n), color=C_PT1, lw=1.3, label="PT1+N")
                if _show_lkf: ax1.plot(f_ax, mg(H_lkf_n), color=C_LKF, lw=1.3, label="LKF+N")
                if _show_hs:
                    ax1.plot(f_ax, mg(H_hs),   color=C_HS, lw=0.6, ls="--", alpha=0.55, label='H(s)')
                    ax1.plot(f_ax, mg(H_hs_n), color=C_HS, lw=1.3, label=f"{_hs_src_pfx}H(s)+N")
                if _show_deq:
                    ax1.plot(f_ax, mg(H_deq),   color=C_DEQ, lw=0.6, ls="--", alpha=0.55, label="DEQ")
                    ax1.plot(f_ax, mg(H_deq_n), color=C_DEQ, lw=1.3, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid:
                    ax1.plot(f_ax, mg(H_pid_n), color=C_PID, lw=0.6, ls="--", alpha=0.45, label=f"{_pid_src_pfx}T_sp(解析)")
                    ax1.plot(f_ax, mg(H_pid_tn), color=C_PID, lw=0.5, ls=":", alpha=0.40, label=f"{_pid_src_pfx}T_n(解析)")
                bands(ax1); ax1.set_xscale(xsc); ax1.set_xlim(*xlim)
                ax1.set_ylabel(ylabel_mag, color=T['label'], fontsize=8)
                ax1.set_title("陀螺滤波器分析仪  PT1 vs 2-state LKF (+Notch)  |  fs=2kHz",
                              color=T['title'], fontsize=9)
                ax1.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                           framealpha=0.85, loc="upper right", ncol=2)

            # ── 2. 相频 ──────────────────────────────────
            if ax2 is not None:
                if _show_pt1: ax2.plot(f_ax, np.angle(H_pt1,  deg=True), color=C_PT1, lw=0.6, ls="--", alpha=0.55)
                if _show_lkf: ax2.plot(f_ax, np.angle(H_lkf,  deg=True), color=C_LKF, lw=0.6, ls="--", alpha=0.55)
                if _show_pt1: ax2.plot(f_ax, np.angle(H_pt1_n, deg=True), color=C_PT1, lw=1.2, label="PT1+N")
                if _show_lkf: ax2.plot(f_ax, np.angle(H_lkf_n, deg=True), color=C_LKF, lw=1.2, label="LKF+N")
                if _show_hs:
                    ax2.plot(f_ax, np.angle(H_hs,   deg=True), color=C_HS, lw=0.6, ls="--", alpha=0.55)
                    ax2.plot(f_ax, np.angle(H_hs_n, deg=True), color=C_HS, lw=1.2, label=f"{_hs_src_pfx}H(s)+N")
                if _show_deq:
                    ax2.plot(f_ax, np.angle(H_deq,   deg=True), color=C_DEQ, lw=0.6, ls="--", alpha=0.55)
                    ax2.plot(f_ax, np.angle(H_deq_n, deg=True), color=C_DEQ, lw=1.2, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid:
                    ax2.plot(f_ax, np.angle(H_pid_n, deg=True), color=C_PID, lw=0.6, ls="--", alpha=0.45, label=f"{_pid_src_pfx}T_sp(解析)")
                    ax2.plot(f_ax, np.angle(H_pid_tn, deg=True), color=C_PID, lw=0.5, ls=":", alpha=0.40, label=f"{_pid_src_pfx}T_n(解析)")
                bands(ax2); ax2.axhline(0, color=T['href'], lw=0.7)
                for deg in (-90, -180): ax2.axhline(deg, color=T['href2'], lw=0.5, ls=":")
                ax2.set_xscale(xsc); ax2.set_xlim(*xlim)
                ax2.set_ylim(-188, 95); ax2.set_yticks([-180, -90, 0, 90])
                ax2.set_ylabel("Phase (°)", color=T['label'], fontsize=8)
                ax2.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                           framealpha=0.85, loc="upper right", ncol=2)

            # ── 3. 群延迟 ────────────────────────────────
            if ax3 is not None:
                clip = 15.0
                if _show_pt1: ax3.plot(f_ax, np.clip(gd_pt1,  -clip, clip), color=C_PT1, lw=0.75, ls="--", alpha=0.55)
                if _show_lkf: ax3.plot(f_ax, np.clip(gd_lkf,  -clip, clip), color=C_LKF, lw=0.75, ls="--", alpha=0.55)
                if _show_pt1: ax3.plot(f_ax, np.clip(gd_pt1n, -clip, clip), color=C_PT1, lw=0.6, label="PT1+N")
                if _show_lkf: ax3.plot(f_ax, np.clip(gd_lkfn, -clip, clip), color=C_LKF, lw=0.6, label="LKF+N")
                if _show_hs:
                    ax3.plot(f_ax, np.clip(gd_hs,  -clip, clip), color=C_HS, lw=0.75, ls="--", alpha=0.55)
                    ax3.plot(f_ax, np.clip(gd_hsn, -clip, clip), color=C_HS, lw=0.6, label=f"{_hs_src_pfx}H(s)+N")
                if _show_deq:
                    ax3.plot(f_ax, np.clip(gd_deq,  -clip, clip), color=C_DEQ, lw=0.75, ls="--", alpha=0.55)
                    ax3.plot(f_ax, np.clip(gd_deqn, -clip, clip), color=C_DEQ, lw=0.6, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid:
                    ax3.plot(f_ax, np.clip(gd_pidn, -clip, clip), color=C_PID, lw=0.6, ls="--", alpha=0.45, label=f"{_pid_src_pfx}T_sp(解析)")
                    ax3.plot(f_ax, np.clip(gd_pid_tn, -clip, clip), color=C_PID, lw=0.4, ls=":", alpha=0.40, label=f"{_pid_src_pfx}T_n(解析)")
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
                if not pid_solo:
                    psd_plot(f_w[mask], _cvt(P_in[mask]),          color=T['noise_psd'], lw=0.6,  label="Setpoints+噪音")
                if pid_solo:
                    psd_plot(f_w[mask], _cvt(P_sp[mask]),          color=T['stick'], lw=0.7, alpha=0.7, label="Setpoints")
                if _show_pt1: psd_plot(f_w[mask], _cvt(P_pt1_ref[mask]), color=C_PT1, lw=0.5, ls="--", alpha=0.35)
                if _show_pt1: psd_plot(f_w[mask], _cvt(P_pt1n[mask]),   color=C_PT1, lw=1.2,  label="PT1+N")
                if _show_lkf: psd_plot(f_w[mask], _cvt(P_lkf_ref[mask]), color=C_LKF, lw=0.5, ls="--", alpha=0.35)
                if _show_lkf: psd_plot(f_w[mask], _cvt(P_lkfn[mask]),   color=C_LKF, lw=1.2,  label="LKF+N")
                if _show_hs:
                    psd_plot(f_w[mask], _cvt(P_hs_ref[mask]), color=C_HS, lw=0.5, ls="--", alpha=0.35)
                    psd_plot(f_w[mask], _cvt(P_hsn[mask]),    color=C_HS, lw=1.2, label=f"{_hs_src_pfx}H(s)+N")
                if _show_deq:
                    psd_plot(f_w[mask], _cvt(P_deq_ref[mask]), color=C_DEQ, lw=0.5, ls="--", alpha=0.35)
                    psd_plot(f_w[mask], _cvt(P_deqn[mask]),    color=C_DEQ, lw=1.2, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid:
                    psd_plot(f_w[mask], _cvt(P_pid_filt[mask]),   color=C_PID, lw=1.2, label=f"{_pid_src_pfx}PID_gyro filt")
                    psd_plot(f_w[mask], _cvt(P_pid_unfilt[mask]), color=C_PID, lw=0.7, ls="--", alpha=0.55, label=f"{_pid_src_pfx}PID_gyro unfilt")
                if use_teo and not pid_solo:
                    psd_plot(f_w[mask], _cvt(P_teo[mask]),    color=C_TEO, lw=1.0, label="TEO")
                for fr, col in [(self.fr1.value(), T['lkf']), (self.fr2.value(), T['pt1'])]:  # fr1=lkf color, fr2=pt1 color
                    ax4.axvline(fr, color=col, lw=0.65, ls=":", alpha=0.8)
                ax4.axvspan(0, 30, alpha=0.09, color=T['band'], zorder=0)
                ax4.axvline(500, color=T['xmark'], lw=0.6, ls="--", alpha=0.50)
                if self._log_xaxis:
                    ax4.set_xscale('log')
                    ax4.set_xlim(1, 1000)
                else:
                    ax4.set_xlim(0, 1000)
                _ylabel = ("ASD (dps/√Hz)" if _amp else "PSD (dps²/Hz)") + (" — log" if self._log_yaxis else "")
                ax4.set_ylabel(_ylabel, color=T['label'], fontsize=8)
                ax4.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                           framealpha=0.85, ncol=3, loc="upper right")

            # ── 5. 时域波形 ──────────────────────────────
            if ax5 is not None:
                # 输入（噪声+打杆）灰色背景线
                if not pid_solo:
                    ax5.plot(t, sp, color=T['noise'], lw=0.28, alpha=0.55, label="Setpoints+噪音")
                else:
                    # 独奏: 显示 setpoint (stick+sine) 而非噪声输入
                    _sp_dec = (s_stick + s_sine_total)[::dec]
                    ax5.plot(t, _sp_dec, color=T['stick'], lw=0.7, alpha=0.7, label="Setpoints")
                # Cubic曲线
                has_stick = np.any(np.abs(sk) > 1e-9)
                if has_stick:
                    ax5.plot(t, sk, color=T['stick'], lw=0.85, alpha=0.85, label="Cubic")
                # 锚点散点（正方形，区别于普通控制点）
                if not pid_solo:
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
                if _show_pt1: ax5.plot(t, pp, color=C_PT1, lw=0.65, label="PT1+N")
                if _show_lkf: ax5.plot(t, lp, color=C_LKF, lw=0.65, label="LKF+N")
                if _show_hs and hp is not None:
                    ax5.plot(t, hp, color=C_HS, lw=0.65, label=f"{_hs_src_pfx}H(s)+N")
                if _show_deq and dp is not None:
                    ax5.plot(t, dp, color=C_DEQ, lw=0.65, label=f"{_deq_src_pfx}DEQ+N")
                if use_pid and pid_uf is not None:
                    ax5.plot(t, pid_fl, color=C_PID, lw=0.65, label=f"{_pid_src_pfx}PID_gyro filt")
                    ax5.plot(t, pid_uf, color=C_PID, lw=0.7, ls="--", alpha=0.3, label=f"{_pid_src_pfx}PID_gyro unfilt")
                if use_teo and tp_ is not None and not pid_solo:
                    ax5.plot(t, tp_, color=C_TEO, lw=0.55, alpha=0.75, label="TEO")
                # 模式提示
                _hint = {"add": "✚ 新增", "del": "✖ 删除(1/200)", "adj": "⇄ 调整"}
                _active_rng = hasattr(self, '_sine_items') and any(it['btn_rng'].isChecked() for it in self._sine_items)
                _hint_str = "⇄ 正弦范围" if _active_rng else _hint.get(self._stick_mode, '')
                ax5.set_title(f"时域  [{_hint_str}]  显示{_disp_hz:.0f}Hz",
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
                        # |A: 仅根据当前可见X范围内的数据自动适应Y轴
                        try:
                            _xl = self._saved_views[_i][0]
                            _ymin, _ymax = float('inf'), float('-inf')
                            for _ln in _ax.get_lines():
                                if (_ln.get_label() or '').startswith('_'):
                                    continue  # 跳过装饰线(axhline/axvline)
                                xd = np.asarray(_ln.get_xdata(), dtype=float)
                                yd = np.asarray(_ln.get_ydata(), dtype=float)
                                if len(xd) == 0:
                                    continue
                                _m = (xd >= _xl[0]) & (xd <= _xl[1])
                                if not np.any(_m):
                                    continue
                                _vis = yd[_m]
                                _vis = _vis[np.isfinite(_vis)]
                                if len(_vis) == 0:
                                    continue
                                _ymin = min(_ymin, float(np.min(_vis)))
                                _ymax = max(_ymax, float(np.max(_vis)))
                            if _ymin < _ymax:
                                _pad = max((_ymax - _ymin) * 0.05, 0.1)
                                _ax.set_ylim(_ymin - _pad, _ymax + _pad)
                        except Exception:
                            pass
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
