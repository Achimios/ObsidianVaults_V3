# interact_mixin.py — 画布交互：打杆曲线新增/删除/拖拽
# _set_stick_mode / _clear_sticks / _build_all_pts / _compute_stick_signal
# _on_canvas_drag / _on_canvas_release / _on_canvas_click / _try_delete_near

import numpy as np
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
            """Switch stick mode. Mutex: deactivates toolbar zoom/pan if active."""
            self._deactivate_toolbar()   # pre-update deactivation
            self._stick_mode = mode
            for btn, m in [(self.btn_stick_add, 'add'),
                           (self.btn_stick_del, 'del'),
                           (self.btn_stick_adj, 'adj')]:
                btn.setChecked(m == mode)
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
            """Drag to relocate a control point in 'adj' mode (debounced)."""
            if self.nav_toolbar.mode:
                return
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
            if self._stick_mode is None:  # no mode selected — ignore canvas clicks
                return
            ax5 = self._last_axes[4]
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
