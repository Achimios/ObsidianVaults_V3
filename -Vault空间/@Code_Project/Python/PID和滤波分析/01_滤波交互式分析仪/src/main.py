# main.py — 程序入口
# FilterAnalyzer 主类（组合所有 Mixin）+ main()
#
# 运行: py main.py
# 依赖: numpy matplotlib scipy PyQt5

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavToolbar,
)
from matplotlib.figure import Figure
from constants import FS, N_SECONDS, N_SIG, DARK_THEME, LIGHT_THEME
from ui_mixin      import UIMixin
from interact_mixin import InteractMixin
from draw_mixin    import DrawMixin
from theme_mixin   import ThemeMixin


class FilterAnalyzer(ThemeMixin, InteractMixin, DrawMixin, UIMixin, QMainWindow):
    _DARK  = DARK_THEME
    _LIGHT = LIGHT_THEME

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "穿越机陀螺滤波器分析仪 v2  |  PT1 vs LKF + Notch  |  fs=2kHz"
        )
        self.resize(1680, 980)
        self.setMinimumSize(500, 500)
        self._log_xaxis  = False
        self._log_yaxis  = False
        self._psd_amp_mode = True    # PSD 功率谱(False=dps²/Hz) | ASD 幅度谱(True=dps/√Hz)
        self._top_filter   = None       # None | 'pt1' | 'lkf' | 'hs' — 置顶滤波器
        self._solo_idx   = None   # None | 0-4: solo display index
        self._solo_cache = None   # list[bool] of chk_show states before solo
        self._noise_cache = None
        self._noise_wp    = None
        self._noise_res   = None
        self._noise_key   = None
        self._last_axes   = [None] * 5
        self._saved_views = [None] * 5
        self._saved_views[3] = ([0.0, 1000.0], [0.0, 200.0])   # >v<📊 ASD默认Y范围 - PSD模式切换即 ×10=[0,2000]
        self._saved_views[4] = ([0.0, float(N_SECONDS)], [-400.0, 400.0])
        self._y_auto = [False] * 5          # 每图 Y轴自动适应开关
        self._default_views = [             # Y重置 / X重置 的默认范围
            ([0.0, 1000.0], [-0.05, 1.15]),         # ax1 幅频 linear
            ([0.0, 1000.0], [-188.0, 95.0]),         # ax2 相频
            ([0.0, 1000.0], [-0.5,  15.0]),          # ax3 群延迟
            ([0.0, 1000.0], [0.0,  200.0]),          # ax4 ASD
            ([0.0, float(N_SECONDS)], [-400.0, 400.0]),  # ax5 时域
        ]
        self._views_reset = False  # skip save on next tick after home
        self._stick_pts   = []      # [(t, y)] user control points (not anchors)
        self._anchor_y    = [0.0, 0.0]   # y at t=0 and t=N_SECONDS
        self._stick_mode  = None    # None | 'add' | 'del' | 'adj'
        self._drag_idx    = None    # index into _build_all_pts() during adj drag
        self._drag_is_anchor = False
        self._drag_anchor_idx = None
        self._pan_ax      = None    # 中键拖动目标axes (None=非拖动状态)
        self._sine_range_item   = None   # sine item being range-adjusted via canvas
        self._sine_range_handle = None   # 't0' | 'tctr' | 't1'
        self._td_cache    = None    # (signal, b_pt1, a_pt1, b_lkf, a_lkf,
                                    #  use_n1, b_n1, a_n1, use_n2, b_n2, a_n2)
        self._dark_mode   = False   # light mode by default
        # Timers
        self._timer = QTimer(); self._timer.setSingleShot(True)
        self._timer.setInterval(280); self._timer.timeout.connect(self._do_update)
        self._stick_timer = QTimer(); self._stick_timer.setSingleShot(True)
        self._stick_timer.setInterval(80); self._stick_timer.timeout.connect(self._do_update)
        self._drag_timer = QTimer(); self._drag_timer.setSingleShot(True)
        self._drag_timer.setInterval(30); self._drag_timer.timeout.connect(self._do_update_drag)
        self._build_ui()
        # Home button: reconnect QAction signal (instance attr won't intercept Qt signal)
        def _new_home(*_a, **_kw):
            self._saved_views = [None] * 5
            self._saved_views[3] = ([0.0, 1000.0], [0.0, 200.0])   # >v<📊 ASD默认Y范围(Home重置回ASD)
            self._saved_views[4] = ([0.0, float(N_SECONDS)], [-400.0, 400.0])
            self._views_reset = True  # skip save on next tick
            self._schedule()
        for _act in self.nav_toolbar.actions():
            if _act.text() == 'Home':
                _act.triggered.disconnect()
                _act.triggered.connect(_new_home)
                break
        # Store original toolbar icons (created for dark bg = light icons)
        self._toolbar_icons_orig = {}
        for _act in self.nav_toolbar.actions():
            if not _act.icon().isNull():
                self._toolbar_icons_orig[id(_act)] = (_act, _act.icon())
        self.canvas.mpl_connect('button_press_event',   self._on_canvas_click)
        self.canvas.mpl_connect('motion_notify_event',  self._on_canvas_drag)
        self.canvas.mpl_connect('button_release_event', self._on_canvas_release)
        self.canvas.mpl_connect('scroll_event',         self._on_scroll)
        # Apply light theme on startup (sets palette + initial draw)
        self._sync_lkf_to_pt1()      # 启动时自动同步 LKF 到 PT1 截止频率
        self.btn_theme.setChecked(True)
        self._toggle_theme(True)


def main():
    import os
    os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts=false'  # 抑制 FONTSPRING DEMO 字体警告
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


if __name__ == '__main__':
    main()
