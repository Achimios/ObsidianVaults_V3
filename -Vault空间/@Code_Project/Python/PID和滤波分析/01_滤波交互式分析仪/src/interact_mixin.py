# interact_mixin.py — 画布交互：打杆曲线新增/删除/拖拽 + 中键拖动/滚轮缩放
# _set_stick_mode / _clear_sticks / _build_all_pts / _compute_stick_signal
# _on_canvas_drag / _on_canvas_release / _on_canvas_click / _try_delete_near
# _on_scroll (滚轮缩放) / 中键拖动(pan)
#
# 画布控制快捷键:
#   中键拖动 = 平移画布
#   Ctrl+中键 = 仅平移Y轴    Shift+中键 = 仅平移X轴
#   滚轮 = 缩放(锚点=光标)
#   Ctrl+滚轮 = 仅缩放Y轴    Shift+滚轮 = 仅缩放X轴

import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from constants import FS, N_SECONDS, N_SIG


class InteractMixin:

        def _deactivate_toolbar(self):
            """Force-deactivate toolbar zoom/pan mode (safe, version-aware)."""
            nmt = self.nav_toolbar
            try:
                _za = nmt._actions.get('zoom')
                _pa = nmt._actions.get('pan')
                if _za and _za.isChecked(): nmt.zoom()
                elif _pa and _pa.isChecked(): nmt.pan()
            except Exception:
                pass

        def _set_stick_mode(self, mode):
            """Switch stick mode (toggle off if same mode clicked again)."""
            self._deactivate_toolbar()   # pre-update deactivation
            self._stick_mode = None if self._stick_mode == mode else mode
            mode = self._stick_mode
            for btn, m in [(self.btn_stick_add, 'add'),
                           (self.btn_stick_del, 'del'),
                           (self.btn_stick_adj, 'adj')]:
                btn.setChecked(m == mode)
            # Deactivate sine range buttons when stick mode is active
            if mode is not None and hasattr(self, '_sine_items'):
                for it in self._sine_items:
                    it['btn_rng'].setChecked(False)
            self._do_update()
            # post-update insurance: if redraw re-armed zoom, kill it again
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self._deactivate_toolbar)


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
            """Drag: middle-button pan OR sine range adjust OR stick-adj ctrl point (debounced)."""
            # ── 中键拖动(pan) ─────────────────────────────────────────
            if getattr(self, '_pan_ax', None) is not None:
                ax = self._pan_ax
                # 用像素偏移量 × 初始比例 → 数据偏移量（不依赖当前axis坐标，无抖动）
                dx_px = event.x - self._pan_start_px[0]
                dy_px = event.y - self._pan_start_px[1]
                dx = dx_px * self._pan_x_scale
                dy = dy_px * self._pan_y_scale
                xl = self._pan_start_xlim
                yl = self._pan_start_ylim
                if not self._pan_ctrl:   # 非Ctrl → 移动X轴
                    ax.set_xlim(xl[0] - dx, xl[1] - dx)
                if not self._pan_shift:  # 非Shift → 移动Y轴
                    ax.set_ylim(yl[0] - dy, yl[1] - dy)
                # 保存视图状态
                _ai = next((i for i, a in enumerate(self._last_axes) if a is ax), None)
                if _ai is not None:
                    self._saved_views[_ai] = (list(ax.get_xlim()), list(ax.get_ylim()))
                self.canvas.draw_idle()
                return
            if self.nav_toolbar.mode:
                return
            # ── Sine range drag ─────────────────────────────────────────
            if getattr(self, '_sine_range_item', None) is not None:
                if event.xdata is None: return
                item = self._sine_range_item; x = float(event.xdata)
                t0v = item['t0'].value(); t1v = item['t1'].value(); dur = t1v - t0v
                h   = self._sine_range_handle
                if h == 't0':
                    item['t0'].setValue(max(0.0, min(x, t1v - 0.5)))
                elif h == 't1':
                    item['t1'].setValue(min(float(N_SECONDS), max(x, t0v + 0.5)))
                elif h == 'tctr':
                    half = max(dur / 2, 0.25)
                    nc   = max(half, min(float(N_SECONDS) - half, x))
                    item['t0'].setValue(nc - half); item['t1'].setValue(nc + half)
                self._timer.stop()   # suppress debounce timer during lightweight drag
                self._drag_timer.start()
                return
            # ── Stick adj drag ──────────────────────────────────────────
            if self._stick_mode != 'adj' or self._drag_idx is None:
                return
            ax5 = self._last_axes[4]
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
            self._drag_timer.start()


        def _on_canvas_release(self, event):
            """Finalize drag: clear pan/drag state, full redraw."""
            # ── 中键拖动结束 ────────────────────────────────────────
            if getattr(self, '_pan_ax', None) is not None:
                self._pan_ax = None
                return
            self._drag_timer.stop()
            if getattr(self, '_sine_range_item', None) is not None:
                self._sine_range_item = None; self._sine_range_handle = None
                self._do_update()
                return
            if self._drag_idx is not None and not self._drag_is_anchor:
                self._stick_pts.sort(key=lambda p: p[0])
            self._drag_idx = None
            self._drag_is_anchor = False
            self._drag_anchor_idx = None
            self._do_update()


        def _on_canvas_click(self, event):
            """Stick/sine-range interaction: left click per mode; right click removes in range.
            Middle click starts canvas pan."""
            # ── 中键拖动(pan)开始 ──────────────────────────────────────
            if event.button == 2 and event.inaxes is not None:
                ax = event.inaxes
                self._pan_ax = ax
                self._pan_start_px = (event.x, event.y)    # 像素坐标(稳定)
                self._pan_start_xlim = list(ax.get_xlim())
                self._pan_start_ylim = list(ax.get_ylim())
                # 预算像素→数据比例(基于按下时的axis bbox)，避免拖拽反馈抖动
                bbox = ax.get_window_extent()
                self._pan_x_scale = (self._pan_start_xlim[1] - self._pan_start_xlim[0]) / max(bbox.width, 1)
                self._pan_y_scale = (self._pan_start_ylim[1] - self._pan_start_ylim[0]) / max(bbox.height, 1)
                mods = QApplication.keyboardModifiers()
                self._pan_ctrl  = bool(mods & Qt.ControlModifier)
                self._pan_shift = bool(mods & Qt.ShiftModifier)
                return
            if self.nav_toolbar.mode:   # zoom/pan active — skip
                return
            ax5 = self._last_axes[4]
            if ax5 is None or not ax5.in_axes(event): return
            x, y = event.xdata, event.ydata
            if x is None or y is None: return
            # ── Sine range mode intercepts click regardless of stick mode ──
            active = next((it for it in getattr(self, '_sine_items', []) if it['btn_rng'].isChecked()), None)
            if active is not None and event.button == 1:
                t0v = active['t0'].value(); t1v = active['t1'].value()
                dur = max(t1v - t0v, 0.01)
                # 3-zone model: left→t0, middle→whole-move, right→t1
                if x > t1v - dur / 3:      handle = 't1'
                elif x >= t0v + dur / 3:   handle = 'tctr'
                else:                      handle = 't0'
                self._sine_range_item   = active
                self._sine_range_handle = handle
                return
            if self._stick_mode is None:  # no mode selected — ignore canvas clicks
                return
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
                    # Pure nearest-neighbor: anchors + user pts, no fixed zone
                    ylim  = ax5.get_ylim(); scale = max(ylim[1] - ylim[0], 1.0)
                    anchors = [(0.0, self._anchor_y[0]), (float(N_SECONDS), self._anchor_y[1])]
                    candidates = anchors + self._stick_pts
                    best = min(range(len(candidates)),
                               key=lambda i: (candidates[i][0]-x)**2
                                             + ((candidates[i][1]-y)/scale)**2)
                    if best < 2:
                        self._drag_idx = 0; self._drag_is_anchor = True
                        self._drag_anchor_idx = best
                    else:
                        self._drag_idx = best - 2; self._drag_is_anchor = False

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


        def _on_scroll(self, event):
            """滚轮缩放（锚点=光标位置）。Ctrl+滚轮=仅Y轴，Shift+滚轮=仅X轴。"""
            if event.inaxes is None or event.xdata is None:
                return
            ax = event.inaxes
            # 缩放因子: 上滚放大(0.85), 下滚缩小(1/0.85)
            factor = 0.85 if event.button == 'up' else 1.0 / 0.85
            mods = QApplication.keyboardModifiers()
            ctrl  = bool(mods & Qt.ControlModifier)
            shift = bool(mods & Qt.ShiftModifier)
            xl = ax.get_xlim(); yl = ax.get_ylim()
            xc, yc = event.xdata, event.ydata
            if not ctrl:   # 非Ctrl → 缩放X轴
                new_xl = [xc - (xc - xl[0]) * factor, xc + (xl[1] - xc) * factor]
                ax.set_xlim(new_xl)
            if not shift:  # 非Shift → 缩放Y轴
                new_yl = [yc - (yc - yl[0]) * factor, yc + (yl[1] - yc) * factor]
                ax.set_ylim(new_yl)
            # 保存视图状态
            _ai = next((i for i, a in enumerate(self._last_axes) if a is ax), None)
            if _ai is not None:
                self._saved_views[_ai] = (list(ax.get_xlim()), list(ax.get_ylim()))
            self.canvas.draw_idle()
