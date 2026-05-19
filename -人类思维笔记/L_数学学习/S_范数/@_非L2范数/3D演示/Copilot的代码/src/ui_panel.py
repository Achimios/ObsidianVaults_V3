"""ui_panel.py — 右侧控制面板（参数 / 操作提示 / 视角切换）"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

_STYLE_PANEL = "background-color: #12122a; color: #d0d0e0;"
_STYLE_TITLE = "font-size: 14px; font-weight: bold; color: #7ec8e3; padding: 4px 0;"
_STYLE_SECTION = "font-size: 11px; color: #888; padding-top: 6px;"
_STYLE_VALUE = "font-size: 12px; color: #e0e0e0;"
_STYLE_HELP = "font-size: 11px; color: #999; line-height: 1.5;"
_STYLE_BTN = (
    "QPushButton {"
    "  background: #1a1a4a; color: #7ec8e3;"
    "  border: 1px solid #7ec8e3; padding: 6px; border-radius: 4px;"
    "}"
    "QPushButton:hover { background: #22226a; }"
    "QPushButton:pressed { background: #0a0a2a; }"
)

_HELP_TEXT = (
    "Tab       切换视角\n"
    "WASD      FPS 移动\n"
    "Space     上升\n"
    "Ctrl      下降\n"
    "右键拖拽  FPS 转头\n"
    "左键拖拽  上帝轨道\n"
    "滚轮      上帝缩放"
)


def _separator(parent: QWidget | None = None) -> QFrame:
    sep = QFrame(parent)
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("color: #333;")
    return sep


def build_panel(fps_view) -> QWidget:
    """Build and return the right-side control panel widget.

    Parameters
    ----------
    fps_view:
        The :class:`camera_controller.FPSGLView` instance to control.
    """
    panel = QWidget()
    panel.setStyleSheet(_STYLE_PANEL)
    layout = QVBoxLayout(panel)
    layout.setSpacing(6)
    layout.setContentsMargins(10, 12, 10, 12)

    # ── Title ─────────────────────────────────────────────────────────
    title = QLabel("Lₚ Norm World")
    title.setStyleSheet(_STYLE_TITLE)
    layout.addWidget(title)
    layout.addWidget(_separator())

    # ── Help ──────────────────────────────────────────────────────────
    layout.addWidget(_section_label("操作说明"))
    help_lbl = QLabel(_HELP_TEXT)
    help_lbl.setStyleSheet(_STYLE_HELP)
    layout.addWidget(help_lbl)
    layout.addWidget(_separator())

    # ── P value slider ────────────────────────────────────────────────
    layout.addWidget(_section_label("Lₚ 指数  p"))
    p_val_lbl = QLabel("p = 3.0")
    p_val_lbl.setStyleSheet(_STYLE_VALUE)
    layout.addWidget(p_val_lbl)

    p_slider = QSlider(Qt.Horizontal)
    p_slider.setRange(7, 80)   # ÷10 → 0.7 … 8.0
    p_slider.setValue(30)       # p = 3.0
    layout.addWidget(p_slider)

    @p_slider.valueChanged.connect
    def _on_p(val: int) -> None:
        p = val / 10.0
        p_val_lbl.setText(f"p = {p:.1f}")
        if fps_view.world_update_p_callback is not None:
            fps_view.world_update_p_callback(p)

    layout.addWidget(_separator())

    # ── Zoom / distance slider (god mode only) ────────────────────────
    layout.addWidget(_section_label("上帝模式缩放距离"))
    zoom_val_lbl = QLabel("distance = 12")
    zoom_val_lbl.setStyleSheet(_STYLE_VALUE)
    layout.addWidget(zoom_val_lbl)

    zoom_slider = QSlider(Qt.Horizontal)
    zoom_slider.setRange(3, 40)
    zoom_slider.setValue(12)
    layout.addWidget(zoom_slider)

    @zoom_slider.valueChanged.connect
    def _on_zoom(val: int) -> None:
        zoom_val_lbl.setText(f"distance = {val}")
        if not fps_view.fps_mode:
            fps_view.opts["distance"] = float(val)
            fps_view.update()

    layout.addWidget(_separator())

    # ── Move speed slider ─────────────────────────────────────────────
    layout.addWidget(_section_label("FPS 移动速度"))
    speed_val_lbl = QLabel("speed = 3.0")
    speed_val_lbl.setStyleSheet(_STYLE_VALUE)
    layout.addWidget(speed_val_lbl)

    speed_slider = QSlider(Qt.Horizontal)
    speed_slider.setRange(1, 100)  # ÷10 → 0.1 … 10.0
    speed_slider.setValue(30)       # 3.0
    layout.addWidget(speed_slider)

    @speed_slider.valueChanged.connect
    def _on_speed(val: int) -> None:
        s = val / 10.0
        speed_val_lbl.setText(f"speed = {s:.1f}")
        fps_view.move_speed = s

    layout.addWidget(_separator())

    # ── Mode indicator + toggle button ────────────────────────────────
    mode_lbl = QLabel("模式: 上帝视角 🌍")
    mode_lbl.setStyleSheet("font-size: 12px; color: #7ec8e3;")
    layout.addWidget(mode_lbl)

    toggle_btn = QPushButton("切换视角  (Tab)")
    toggle_btn.setStyleSheet(_STYLE_BTN)
    layout.addWidget(toggle_btn)

    @toggle_btn.clicked.connect
    def _on_toggle() -> None:
        fps_view.toggle_mode()
        if fps_view.fps_mode:
            mode_lbl.setText("模式: FPS 视角 🎮")
        else:
            mode_lbl.setText("模式: 上帝视角 🌍")
        fps_view.setFocus()

    layout.addStretch()

    # ── Info footer ───────────────────────────────────────────────────
    footer = QLabel("L1=八面体  L2=球  L3=中心\nL∞=方块    p可调=周围5球")
    footer.setStyleSheet("font-size: 10px; color: #555;")
    layout.addWidget(footer)

    return panel


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_STYLE_SECTION)
    return lbl
