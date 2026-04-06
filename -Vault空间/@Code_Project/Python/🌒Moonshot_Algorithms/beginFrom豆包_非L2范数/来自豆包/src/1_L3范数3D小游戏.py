import sys
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import QApplication

# ----------------------
# 生成 L3 单位球顶点
# |x|³ + |y|³ + |z|³ = 1
# ----------------------
def make_L3_sphere(radius=1, n=40):
    theta = np.linspace(0, 2*np.pi, n)
    phi   = np.linspace(-np.pi/2, np.pi/2, n//2)
    Theta, Phi = np.meshgrid(theta, phi)
    
    # 方向向量
    x0 = np.cos(Theta) * np.cos(Phi)
    y0 = np.sin(Phi)
    z0 = np.sin(Theta) * np.cos(Phi)
    
    # L3 归一化
    r3 = np.abs(x0)**3 + np.abs(y0)**3 + np.abs(z0)**3
    r  = r3 ** (1/3)
    
    x = x0 / r * radius
    y = y0 / r * radius
    z = z0 / r * radius
    
    # 转成顶点和面
    verts = np.stack([x, y, z], axis=-1).reshape(-1, 3)
    faces = []
    for i in range(n//2 - 1):
        for j in range(n - 1):
            idx = i * n + j
            faces.append([idx, idx+1, idx+n])
            faces.append([idx+1, idx+n+1, idx+n])
    faces = np.array(faces)
    return verts, faces

# ----------------------
# 初始化窗口
# ----------------------
app = QApplication(sys.argv)
w = gl.GLViewWidget()
w.opts['distance'] = 5
w.setWindowTitle('L3 Norm 3D World')
w.setGeometry(100, 100, 1000, 800)

# ----------------------
# 加地面（普通平面，你可以飞着看）
# ----------------------
g = gl.GLGridItem()
g.setSize(10, 10)
g.setSpacing(1, 1)
w.addItem(g)

# ----------------------
# 加几个 L3 球
# ----------------------
# 中心大球
v, f = make_L3_sphere(radius=1, n=40)
m1 = gl.GLMeshItem(vertexes=v, faces=f, color=(0.3, 0.6, 1, 0.8), smooth=True, drawEdges=False)
m1.translate(0, 0, 0)
w.addItem(m1)

# 周围小球
pos = [(2, 0, 0), (-2, 0, 0), (0, 2, 0), (0, -2, 0), (0, 0, 2)]
colors = [(1,0.3,0.3,0.8), (0.3,1,0.3,0.8), (1,1,0.3,0.8), (0.3,1,1,0.8), (1,0.3,1,0.8)]
for p, c in zip(pos, colors):
    v, f = make_L3_sphere(radius=0.5, n=30)
    m = gl.GLMeshItem(vertexes=v, faces=f, color=c, smooth=True, drawEdges=False)
    m.translate(*p)
    w.addItem(m)

# ----------------------
# 运行
# ----------------------
w.show()
sys.exit(app.exec_())