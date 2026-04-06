# draw_mixin.py — 绘图核心 + 轴切换 + LKF 同步
# _toggle_x / _toggle_y / _sync_lkf_to_pt1 / _do_update

import numpy as np
from scipy.signal import freqz, lfilter, welch
from matplotlib.gridspec import GridSpec
from constants import FS, N_SECONDS, N_SIG
from dsp import (
    pt1_coeffs, lkf_coeffs, notch_coeffs,
    resonance, resonance_dist, perlin_noise_1d,
)


class DrawMixin:

        def _compute_sine_total(self):
            """Sum all sine injection signals (half-Hann window + local noise). Cached by param key."""
            items = getattr(self, '_sine_items', [])
            if not items:
                self._sine_cache_key = None
                return np.zeros(N_SIG)
            key = tuple(
                (it['freq'].value(), it['amp'].value(), it['trans'].value(),
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
                freq  = item['freq'].value();  amp   = item['amp'].value()
                trans = item['trans'].value(); t0    = item['t0'].value()
                t1    = item['t1'].value()
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
                total += amp * np.sin(2 * np.pi * freq * t_full) * window
                if w_rms > 0 or p_rms > 0:
                    seed = int(freq * 100 + amp + t0 * 10) % (2**31)
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
            s_stick = self._compute_stick_signal()
            dec = 10; t = np.arange(N_SIG)[::dec] / FS
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
            b_n1, a_n1 = notch_coeffs(self.f_n1.value(), self.q_n1.value(), fs)
            b_n2, a_n2 = notch_coeffs(self.f_n2.value(), self.q_n2.value(), fs)
            use_n1 = self.n1_en.isChecked()
            use_n2 = self.n2_en.isChecked()
            use_pt1 = self.chk_pt1_en.isChecked()
            use_lkf = self.chk_lkf_en.isChecked()

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
            s_stick      = self._compute_stick_signal()
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
            sp  = signal_ws[::dec]          # 输入（噪声+打杆+注入）
            sk  = s_stick[::dec]            # 纯打杆
            si  = s_sine_total[::dec]       # 正弦注入
            pp  = out_pt1_n_td[::dec]       # PT1 响应
            lp  = out_lkf_n_td[::dec]       # LKF 响应

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
                if use_pt1: ax1.plot(f_ax, mg(H_pt1),   color=C_PT1, lw=0.6, ls="--", alpha=0.55,
                                     label=f"PT1 {self.fc_pt1.value():.0f}Hz")
                if use_lkf: ax1.plot(f_ax, mg(H_lkf),   color=C_LKF, lw=0.6, ls="--", alpha=0.55, label="LKF")
                if use_pt1: ax1.plot(f_ax, mg(H_pt1_n), color=C_PT1, lw=1.3, label="PT1+Notch")
                if use_lkf: ax1.plot(f_ax, mg(H_lkf_n), color=C_LKF, lw=1.3, label="LKF+Notch")
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
                bands(ax3); ax3.axhline(0, color=T['href'], lw=0.7)
                ax3.set_xscale(xsc); ax3.set_xlim(*xlim)
                ax3.set_ylabel("Grp Dly (ms)", color=T['label'], fontsize=8)
                ax3.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                           framealpha=0.85, loc="upper right", ncol=2)

            # ── 4. PSD ──────────────────────────────────
            if ax4 is not None:
                psd_plot = ax4.semilogy if self._log_yaxis else ax4.plot
                psd_plot(f_w[mask], P_in[mask],     color=T['noise_psd'], lw=0.6,  label="输入+打杆")
                if use_pt1: psd_plot(f_w[mask], P_pt1_ref[mask], color=C_PT1, lw=0.5, ls="--", alpha=0.35)
                if use_pt1: psd_plot(f_w[mask], P_pt1n[mask],   color=C_PT1, lw=1.2,  label="PT1+N")
                if use_lkf: psd_plot(f_w[mask], P_lkf_ref[mask], color=C_LKF, lw=0.5, ls="--", alpha=0.35)
                if use_lkf: psd_plot(f_w[mask], P_lkfn[mask],   color=C_LKF, lw=1.2,  label="LKF+N")
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
                                    color=T['dot'], s=22, zorder=6)                # 正弦注入曲线
                has_sine = np.any(np.abs(si) > 1e-9)
                if has_sine:
                    ax5.plot(t, si, color=T['sine'], lw=0.5, alpha=0.50, label="正弦注入")                # 删除模式：1/200 视图宽度区域（含锚点保护不显示）
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
                # 模式提示
                _hint = {"add": "✚ 新增", "del": "✖ 删除(1/200)", "adj": "⇄ 调整"}
                _active_rng = hasattr(self, '_sine_items') and any(it['btn_rng'].isChecked() for it in self._sine_items)
                _hint_str = "⇄ 正弦范围" if _active_rng else _hint.get(self._stick_mode, '')
                ax5.set_title(f"时域  [{_hint_str}]  Y轴手动缩放",
                              color=T['label'], fontsize=7.5, pad=2)
                ax5.set_xlabel("Time (s)", color=T['label'], fontsize=8)
                ax5.set_ylabel("dps",     color=T['label'], fontsize=8)
                ax5.legend(fontsize=7.5, facecolor=T['legend_bg'], labelcolor=T['legend_txt'],
                           framealpha=0.85, loc="upper right", ncol=4)
            # Restore saved views for all axes (zoom/pan preserved across ticks)
            for _i, _ax in enumerate([ax1, ax2, ax3, ax4, ax5]):
                if _ax is not None and self._saved_views[_i] is not None:
                    _ax.set_xlim(self._saved_views[_i][0])
                    _ax.set_ylim(self._saved_views[_i][1])
            self._last_axes = [ax1, ax2, ax3, ax4, ax5]

            self.canvas.draw()
