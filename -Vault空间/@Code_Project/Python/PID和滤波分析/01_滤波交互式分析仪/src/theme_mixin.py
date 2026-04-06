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
            self._do_update()


        def update_plots(self):
            self._schedule()
