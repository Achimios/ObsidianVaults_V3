# theme_mixin.py — Mirror's Edge 双主题 + toolbar 图标
# _update_toolbar_icons / _toggle_theme / update_plots

from PyQt5.QtWidgets import QApplication
from constants import FS, N_SECONDS


class ThemeMixin:

        def _update_toolbar_icons(self):
            """Invert toolbar icon RGB for light mode so they are visible on light bg."""
            from PyQt5.QtGui import QImage, QIcon, QPixmap
            for _id, (_act, _orig_ico) in self._toolbar_icons_orig.items():
                if self._dark_mode:
                    _act.setIcon(_orig_ico)
                else:
                    _px = _orig_ico.pixmap(32, 32)
                    _img = _px.toImage()
                    _img.invertPixels(QImage.InvertRgb)
                    _act.setIcon(QIcon(QPixmap.fromImage(_img)))
            self.nav_toolbar.update()


        def _toggle_theme(self, checked):
            """Switch between dark (Mirror's Edge) and light themes."""
            self._dark_mode = not checked
            T = self._DARK if self._dark_mode else self._LIGHT
            self.nav_toolbar.setStyleSheet(T['tbar'])
            self._update_toolbar_icons()
            # 每图轴控按钮随主题更新样式
            _BT_DARK  = ("QPushButton{background:rgba(30,35,55,190);color:#99bbcc;"
                         "border:1px solid #3a4a5a;border-radius:2px;font-size:7pt;padding:0px;}"
                         "QPushButton:checked{background:rgba(60,140,80,210);color:#eeffee;}"
                         "QPushButton:hover{background:rgba(50,70,100,220);}")
            _BT_LIGHT = ("QPushButton{background:rgba(200,210,230,210);color:#334466;"
                         "border:1px solid #8899aa;border-radius:2px;font-size:7pt;padding:0px;}"
                         "QPushButton:checked{background:rgba(80,160,100,220);color:#ffffff;}"
                         "QPushButton:hover{background:rgba(160,180,210,230);}")
            _bss = _BT_DARK if self._dark_mode else _BT_LIGHT
            for _e in getattr(self, '_ax_ctrl_groups', []):
                for _bk in ('ya', 'yr', 'xr'):
                    if _bk in _e: _e[_bk].setStyleSheet(_bss)
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
            # Setpoints注入 box 背景色+按钮对比度（必须在 setPalette 之后，否则 palette 会覆盖样式）
            self._apply_inject_box_style(self._dark_mode)
            self._do_update()


        def update_plots(self):
            self._schedule()
