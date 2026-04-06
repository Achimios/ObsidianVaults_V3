"""camera_controller.py — FPS + 上帝视角双模式相机控制器

数学说明
---------
pyqtgraph GLViewWidget 相机模型::

    eye = center + [-d·cos(el)·sin(az),
                    -d·cos(el)·cos(az),
                     d·sin(el)]

其中 el = elevation（度），az = azimuth（度），d = distance。
FPS 模式下将 d 设为极小值（0.001），center = cam_pos，
相机基本就在 cam_pos 处，azimuth/elevation 控制朝向。

水平前进方向（pressing W）:  forward_h = [sin(az), cos(az), 0]
水平右移方向（pressing D）:  right_h   = [cos(az), -sin(az), 0]
"""
from __future__ import annotations

import numpy as np
import pyqtgraph.opengl as gl
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor, QVector3D


class FPSGLView(gl.GLViewWidget):
    """GLViewWidget with Tab-toggled FPS / orbit camera modes."""

    def __init__(self) -> None:
        super().__init__()

        # ── Camera state ──────────────────────────────────────────────
        self.cam_pos: np.ndarray = np.array([0.0, -10.0, 3.0], dtype=float)
        self.move_speed: float = 3.0
        self.fps_mode: bool = False
        self.keys_pressed: set[int] = set()
        self.mouse_locked: bool = False

        # Optional callback wired by main.py
        self.world_update_p_callback = None

        # Keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)

        # ~60 fps movement timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    # ─────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────

    def toggle_mode(self) -> None:
        """Switch between orbit (god) and FPS camera modes."""
        self.fps_mode = not self.fps_mode
        if self.fps_mode:
            self._enter_fps()
        else:
            self._exit_to_orbit()

    # ─────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────

    def _enter_fps(self) -> None:
        """Derive cam_pos from current orbit state and switch to FPS."""
        az = np.deg2rad(float(self.opts["azimuth"]))
        el = np.deg2rad(float(self.opts["elevation"]))
        d = float(self.opts["distance"])
        cx = float(self.opts["center"].x())
        cy = float(self.opts["center"].y())
        cz = float(self.opts["center"].z())
        # Camera eye position in world coords
        self.cam_pos = np.array(
            [
                cx - d * np.cos(el) * np.sin(az),
                cy - d * np.cos(el) * np.cos(az),
                cz + d * np.sin(el),
            ],
            dtype=float,
        )
        self._apply_fps_camera()

    def _exit_to_orbit(self) -> None:
        """Return to orbit mode, releasing mouse lock."""
        if self.mouse_locked:
            self.mouse_locked = False
            self.setCursor(Qt.ArrowCursor)
        self.opts["distance"] = 12.0
        self.setCameraPosition(
            pos=QVector3D(0.0, 0.0, 0.0),
            elevation=25.0,
            azimuth=45.0,
        )

    def _apply_fps_camera(self) -> None:
        """Push cam_pos into pyqtgraph's orbit model (distance≈0)."""
        self.opts["center"] = QVector3D(
            float(self.cam_pos[0]),
            float(self.cam_pos[1]),
            float(self.cam_pos[2]),
        )
        self.opts["distance"] = 0.001
        self.update()

    def _horizontal_dirs(self) -> tuple[np.ndarray, np.ndarray]:
        """Return horizontal forward and right vectors for current azimuth."""
        az = np.deg2rad(float(self.opts["azimuth"]))
        forward = np.array([np.sin(az), np.cos(az), 0.0])
        right = np.array([np.cos(az), -np.sin(az), 0.0])
        return forward, right

    def _tick(self) -> None:
        """Called ~60×/s; translates held keys into camera movement."""
        if not self.fps_mode or not self.keys_pressed:
            return
        forward, right = self._horizontal_dirs()
        up = np.array([0.0, 0.0, 1.0])
        speed = self.move_speed * 0.016  # units/frame

        delta = np.zeros(3)
        if Qt.Key_W in self.keys_pressed:
            delta += forward
        if Qt.Key_S in self.keys_pressed:
            delta -= forward
        if Qt.Key_A in self.keys_pressed:
            delta -= right
        if Qt.Key_D in self.keys_pressed:
            delta += right
        if Qt.Key_Space in self.keys_pressed:
            delta += up
        if Qt.Key_Control in self.keys_pressed:
            delta -= up

        norm = float(np.linalg.norm(delta))
        if norm > 1e-6:
            self.cam_pos += delta / norm * speed
            self._apply_fps_camera()

    # ─────────────────────────────────────────
    # Qt event overrides
    # ─────────────────────────────────────────

    def keyPressEvent(self, ev) -> None:
        key = ev.key()
        if key == Qt.Key_Tab:
            self.toggle_mode()
            ev.accept()
            return
        if self.fps_mode and key in (
            Qt.Key_W, Qt.Key_A, Qt.Key_S, Qt.Key_D,
            Qt.Key_Space, Qt.Key_Control,
        ):
            self.keys_pressed.add(key)
            ev.accept()
            return
        super().keyPressEvent(ev)

    def keyReleaseEvent(self, ev) -> None:
        self.keys_pressed.discard(ev.key())
        super().keyReleaseEvent(ev)

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.RightButton and self.fps_mode:
            self.mouse_locked = True
            QCursor.setPos(self.mapToGlobal(self.rect().center()))
            self.setCursor(Qt.BlankCursor)
            ev.accept()
            return
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev) -> None:
        if ev.button() == Qt.RightButton and self.fps_mode:
            self.mouse_locked = False
            self.setCursor(Qt.ArrowCursor)
            ev.accept()
            return
        super().mouseReleaseEvent(ev)

    def mouseMoveEvent(self, ev) -> None:
        if self.mouse_locked and self.fps_mode:
            center = self.rect().center()
            dx = ev.x() - center.x()
            dy = ev.y() - center.y()
            if abs(dx) > 0 or abs(dy) > 0:
                sens = 0.25
                self.opts["azimuth"] = (float(self.opts["azimuth"]) + dx * sens) % 360.0
                self.opts["elevation"] = float(
                    max(-80.0, min(80.0, float(self.opts["elevation"]) - dy * sens))
                )
                QCursor.setPos(self.mapToGlobal(center))
                self.update()
            ev.accept()
            return
        super().mouseMoveEvent(ev)

    def wheelEvent(self, ev) -> None:
        # Suppress scroll-to-zoom in FPS mode (confusing)
        if not self.fps_mode:
            super().wheelEvent(ev)
        else:
            ev.accept()
