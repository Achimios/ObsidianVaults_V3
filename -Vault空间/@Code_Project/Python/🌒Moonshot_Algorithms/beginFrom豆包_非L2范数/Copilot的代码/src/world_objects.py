"""world_objects.py — 场景对象生成（Lp 球、地板、坐标轴等）"""
from __future__ import annotations

import numpy as np
import pyqtgraph.opengl as gl


# ─────────────────────────────────────────
# Geometry generators
# ─────────────────────────────────────────

def make_lp_sphere(p: float, radius: float = 1.0, n: int = 40) -> tuple[np.ndarray, np.ndarray]:
    """Generate vertex/face arrays for an Lp unit sphere: (Σ|xᵢ|^p)^(1/p) = radius."""
    theta = np.linspace(0, 2 * np.pi, n)
    phi = np.linspace(-np.pi / 2, np.pi / 2, n // 2)
    Theta, Phi = np.meshgrid(theta, phi)

    x0 = np.cos(Theta) * np.cos(Phi)
    y0 = np.sin(Phi)
    z0 = np.sin(Theta) * np.cos(Phi)

    rp = np.abs(x0) ** p + np.abs(y0) ** p + np.abs(z0) ** p
    rp = np.maximum(rp, 1e-9)
    r = rp ** (1.0 / p)
    r = np.maximum(r, 1e-9)

    verts = np.stack(
        [x0 / r * radius, y0 / r * radius, z0 / r * radius], axis=-1
    ).reshape(-1, 3).astype(np.float32)

    rows = n // 2 - 1
    faces: list[list[int]] = []
    for i in range(rows):
        for j in range(n - 1):
            idx = i * n + j
            faces.append([idx, idx + 1, idx + n])
            faces.append([idx + 1, idx + n + 1, idx + n])
    return verts, np.array(faces, dtype=np.uint32)


def _make_floor_mesh(size: float = 30.0, z: float = -1.02, subs: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """Create a subdivided flat mesh for the floor (better normals for shading)."""
    xs = np.linspace(-size / 2, size / 2, subs + 1)
    ys = np.linspace(-size / 2, size / 2, subs + 1)
    X, Y = np.meshgrid(xs, ys)
    Z = np.full_like(X, z)
    verts = np.stack([X, Y, Z], axis=-1).reshape(-1, 3).astype(np.float32)
    n = subs + 1
    faces: list[list[int]] = []
    for i in range(subs):
        for j in range(subs):
            idx = i * n + j
            faces.append([idx, idx + 1, idx + n])
            faces.append([idx + 1, idx + n + 1, idx + n])
    return verts, np.array(faces, dtype=np.uint32)


# ─────────────────────────────────────────
# Item factory
# ─────────────────────────────────────────

def _mesh(
    verts: np.ndarray,
    faces: np.ndarray,
    color: tuple[float, ...],
    transparent: bool = False,
) -> gl.GLMeshItem:
    """Create a GLMeshItem with 'shaded' shader (Lambert lighting).
    Falls back to plain color if shader is unsupported."""
    glopts = "translucent" if transparent else "opaque"
    try:
        item = gl.GLMeshItem(
            vertexes=verts,
            faces=faces,
            shader="shaded",
            smooth=True,
            color=color,
            glOptions=glopts,
        )
    except Exception:
        item = gl.GLMeshItem(
            vertexes=verts,
            faces=faces,
            color=color,
            smooth=True,
            glOptions=glopts,
        )
    return item


# ─────────────────────────────────────────
# Scene builder
# ─────────────────────────────────────────

#: Positions of the five surrounding adjustable balls
_LP_BALL_POSITIONS: list[tuple[float, float, float]] = [
    (0.0,  5.0, 0.0),
    (0.0, -5.0, 0.0),
    (3.0,  3.0, 1.0),
    (-3.0, 3.0, 1.0),
    (3.0, -3.0, 1.0),
]

_LP_BALL_COLORS: list[tuple[float, float, float, float]] = [
    (1.0, 0.30, 0.30, 1.0),
    (0.3, 1.00, 0.30, 1.0),
    (1.0, 1.00, 0.20, 1.0),
    (0.2, 1.00, 1.00, 1.0),
    (1.0, 0.30, 1.00, 1.0),
]


def build_scene(view: gl.GLViewWidget) -> None:
    """Populate the GL view with all scene objects.

    Attaches ``lp_ball_items`` list to *view* so ``update_lp_balls`` can
    update them without needing to search the scene graph.
    """
    # ── Grid (visual reference lines) ────────────────────────────────
    grid = gl.GLGridItem()
    grid.setSize(30, 30)
    grid.setSpacing(1, 1)
    grid.translate(0, 0, -1.0)
    view.addItem(grid)

    # ── Solid floor mesh ─────────────────────────────────────────────
    fv, ff = _make_floor_mesh(size=40.0, z=-1.02, subs=10)
    floor = _mesh(fv, ff, color=(0.15, 0.15, 0.18, 1.0))
    view.addItem(floor)

    # ── Coordinate axes ───────────────────────────────────────────────
    ax = gl.GLAxisItem()
    ax.setSize(x=4, y=4, z=4)
    view.addItem(ax)

    # ── Central L3 sphere ─────────────────────────────────────────────
    v, f = make_lp_sphere(3.0, radius=1.0, n=50)
    center_ball = _mesh(v, f, color=(0.30, 0.60, 1.00, 1.0))
    view.addItem(center_ball)

    # ── L2 reference (wire-ghost, semi-transparent) ───────────────────
    v2, f2 = make_lp_sphere(2.0, radius=1.10, n=50)
    l2_ref = _mesh(v2, f2, color=(1.0, 1.0, 1.0, 0.10), transparent=True)
    view.addItem(l2_ref)

    # ── L1 octahedron (+X, orange) ────────────────────────────────────
    v1, f1 = make_lp_sphere(1.0, radius=0.85, n=30)
    l1_ball = _mesh(v1, f1, color=(1.0, 0.65, 0.10, 1.0))
    l1_ball.translate(6.0, 0.0, 0.0)
    view.addItem(l1_ball)

    # ── L∞ cube (p=20 ≈ max-norm, -X, purple) ────────────────────────
    vinf, finf = make_lp_sphere(20.0, radius=0.85, n=40)
    linf_ball = _mesh(vinf, finf, color=(0.75, 0.20, 1.00, 1.0))
    linf_ball.translate(-6.0, 0.0, 0.0)
    view.addItem(linf_ball)

    # ── Adjustable Lp balls (default p=3) ────────────────────────────
    lp_balls: list[gl.GLMeshItem] = []
    for pos, col in zip(_LP_BALL_POSITIONS, _LP_BALL_COLORS):
        v, f = make_lp_sphere(3.0, radius=0.65, n=30)
        ball = _mesh(v, f, color=col)
        ball.translate(*pos)
        view.addItem(ball)
        lp_balls.append(ball)

    view.lp_ball_items = lp_balls  # type: ignore[attr-defined]


def update_lp_balls(view: gl.GLViewWidget, p: float) -> None:
    """Regenerate surrounding Lp balls with new *p* value (called from slider)."""
    if not hasattr(view, "lp_ball_items"):
        return
    p = max(0.5, p)
    for ball in view.lp_ball_items:  # type: ignore[attr-defined]
        v, f = make_lp_sphere(p, radius=0.65, n=30)
        ball.setMeshData(vertexes=v, faces=f)
