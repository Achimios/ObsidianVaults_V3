"""main.py — Lp Norm 3D World V2 入口

运行方式::

    "C:\\Users\\Popst\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" main.py

或者在 VS Code 里把解释器切成 Python 3.10（非 venv），然后 F5。
"""
from __future__ import annotations

import os
import sys

# 确保同目录模块可导入（无论从哪个 cwd 启动）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget

from camera_controller import FPSGLView
from ui_panel import build_panel
from world_objects import build_scene, update_lp_balls


def main() -> None:
    app = QApplication(sys.argv)

    # ── Main window ───────────────────────────────────────────────────
    container = QWidget()
    container.setWindowTitle("Lp Norm 3D World  [Tab = 切换视角  |  WASD = 移动  |  右键 = FPS转头]")
    container.setGeometry(50, 50, 1300, 840)
    container.setStyleSheet("background: #0d0d1a;")

    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # ── GL view ───────────────────────────────────────────────────────
    gl_view = FPSGLView()
    gl_view.opts["distance"] = 12.0
    gl_view.opts["elevation"] = 25.0
    gl_view.opts["azimuth"] = 45.0

    # ── Right panel ───────────────────────────────────────────────────
    panel = build_panel(gl_view)
    panel.setFixedWidth(220)

    layout.addWidget(gl_view, stretch=1)
    layout.addWidget(panel)

    # ── Scene ─────────────────────────────────────────────────────────
    build_scene(gl_view)

    # Wire p-slider → mesh update
    gl_view.world_update_p_callback = lambda p: update_lp_balls(gl_view, p)

    # ── Launch ────────────────────────────────────────────────────────
    container.show()
    gl_view.setFocus()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
