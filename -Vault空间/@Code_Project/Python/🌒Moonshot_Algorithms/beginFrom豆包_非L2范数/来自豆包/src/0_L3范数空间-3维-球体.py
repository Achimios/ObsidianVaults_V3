import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ----------------------
# L3 单位球面
# |x|³ + |y|³ + |z|³ = 1
# ----------------------
theta = np.linspace(0, 2*np.pi, 80)
phi   = np.linspace(-np.pi/2, np.pi/2, 40)
Theta, Phi = np.meshgrid(theta, phi)

# 球坐标方向
x0 = np.cos(Theta) * np.cos(Phi)
y0 = np.sin(Phi)
z0 = np.sin(Theta) * np.cos(Phi)

# L3 归一化
r3 = np.abs(x0)**3 + np.abs(y0)**3 + np.abs(z0)**3
r  = r3 ** (1/3)

x = x0 / r
y = y0 / r
z = z0 / r

# 绘图
fig = plt.figure(figsize=(8,8))
ax  = fig.add_subplot(111, projection='3d')
ax.plot_surface(x, y, z, color='#66aadd', rstride=1, cstride=1, linewidth=0)
ax.set_title("L3 Norm Unit Sphere\n|x|³ + |y|³ + |z|³ = 1", fontsize=14)
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")
ax.set_box_aspect([1,1,1])
plt.show()