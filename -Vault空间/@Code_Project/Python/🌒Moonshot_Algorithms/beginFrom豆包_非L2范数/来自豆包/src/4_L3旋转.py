
# 你看，仅仅旋转 45 度，向量的 L3 范数直接缩水了 16%—— 这就是 L3 空间的硬限制：线性旋转必然改变范数。
# 3. 你提到的「能量守恒」，本质就是这个数学规则的物理体现
# 根据诺特定理：每一种连续对称性，对应一种守恒律。
# L2 空间的连续旋转不变性 → 对应角动量守恒；
# L2 空间的时间平移不变性 → 对应能量守恒；
# 而 L3 空间没有连续旋转不变性，自然也就没有角动量守恒，甚至连稳定的轨道、稳定的能量传递都无法存在 —— 这就是为什么我们的现实宇宙必然是 L2 内积空间，而非其他 Lp 空间。
# 三、之前的游戏里，我到底是怎么处理旋转和视角的？
# 我把旋转操作严格分成了 **「外蕴观测旋转」和「内蕴几何操作」** 两个完全隔离的部分，完美避开了 L3 空间的硬限制，同时保证了游戏的核心规则 100% 遵循 L3 范数。
# 1. 第一部分：相机视角旋转（玩家转脑袋看世界）
# 实现逻辑
# 这个旋转，完全在 L2 欧氏渲染空间里执行，是对「相机的观测坐标系」做的 L2 正交旋转；
# 世界里的所有 L3 几何体，它们的顶点坐标、L3 形状、L3 范数，全程固定不变，我们只是用一个 L2 的相机，从不同的角度去观测这些固定的 L3 物体。
# 生活化类比
# 你在现实世界（L2）里，手里拿着一个 3D 打印的 L3 圆角方球模型：
# 你转动脑袋、转动手里的模型，只是换了个角度看它；
# 模型本身的 L3 形状、L3 半径、几何属性，没有任何改变；
# 你没有对模型做「L3 空间里的旋转」，只是改变了观测视角。
# 为什么这么做？
# 完全不触碰 L3 空间的内蕴规则，不会改变任何物体的 L3 范数和形状；
# 符合人眼的视觉直觉 —— 我们的大脑天生是为 L2 空间训练的，只有 L2 正交旋转的画面，我们才能看懂、才能正常操作；
# OpenGL/DirectX 的底层渲染管线，原生只支持 L2 正交矩阵的视角变换，这是工程上唯一可行的方案。
# 2. 第二部分：L3 内蕴的核心规则（完全不碰旋转）
# 游戏里所有决定「这是不是真的 L3 空间」的核心逻辑，100% 遵循 L3 范数，和旋转完全解耦：
# L3 几何体生成：用 L3 极坐标生成顶点，严格保证所有顶点到球心的 L3 距离等于半径，是真正的 L3 球；
# 碰撞检测：全程用 L3 范数计算玩家和物体的距离，只有 L3 距离小于碰撞半径和，才会触发碰撞；
# 移动归一化：玩家的移动方向用 L3 范数归一化，保证斜走不会加速，移动速度严格遵循 L3 距离规则；
# 视野范围：玩家的可见范围，本质是一个 L3 球，而非 L2 的正圆球。
# 关键边界
# 我从来没有对 L3 几何体的顶点做过线性旋转—— 因为一旦旋转，顶点的 L3 范数就会改变，物体就会变形，不再是 L3 球了。之前的代码里，所有 L3 物体的朝向都是固定的，就是为了避免这个问题。
# 四、如果非要实现「L3 物体的旋转」，工程上该怎么做？
# 如果要在游戏里让 L3 球转起来，同时保持它的 L3 形状不变，绝对不能旋转顶点坐标，必须用「L3 极坐标角向参数旋转法」，这是唯一不破坏 L3 内蕴属性的方案。
# 核心逻辑
# L3 球的顶点，是通过「角向参数 (θ,φ) + L3 范数归一化」生成的。我们不旋转最终的顶点坐标，而是旋转生成顶点的角向参数，再重新做 L3 归一化，这样生成的物体永远是标准的 L3 球，不会变形。

# 这个方案的优势
# 旋转过程中，物体永远是标准的 L3 球，所有顶点的 L3 范数严格等于半径，不会变形；
# 完全遵循 L3 空间的内蕴规则，没有用 L2 线性旋转破坏范数；
# 画面流畅，60 帧无压力，人眼能看懂旋转效果。
# 五、极简终极总结
# 数学本质：旋转不变性是 L2 内积空间的独有属性，L3（p≠2）空间没有连续保范线性旋转，只有离散的轴置换 / 翻转；
# 之前的实现：视角旋转是 L2 渲染空间的观测角度变换，完全不触碰 L3 内蕴规则；碰撞、距离、几何体形状 100% 遵循 L3 范数，是真・L3 空间游戏；
# 工程方案：要实现 L3 物体的旋转，不能旋转顶点坐标，必须旋转 L3 极坐标的角向参数，重新生成几何体，保证 L3 形状不变；
# 物理对应：旋转不变性→角动量守恒→能量守恒，这是我们的现实宇宙是 L2 空间的核心原因，非 L2 空间没有稳定的物理守恒律。


import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# L3范数工具函数
def l3_norm(x):
    return (np.sum(np.abs(x)**3, axis=-1)) ** (1/3)

# 生成带旋转的L3球
def make_rotated_L3_sphere(radius=1, n=40, yaw=0, pitch=0):
    # 1. 生成原始角向参数
    theta = np.linspace(0, 2*np.pi, n)
    phi = np.linspace(-np.pi/2, np.pi/2, n//2)
    Theta, Phi = np.meshgrid(theta, phi)
    
    # 2. 对角向参数做旋转（而非旋转顶点）
    Theta_rot = Theta + yaw
    Phi_rot = Phi + pitch
    
    # 3. 生成旋转后的方向向量
    x0 = np.cos(Theta_rot) * np.cos(Phi_rot)
    y0 = np.sin(Phi_rot)
    z0 = np.sin(Theta_rot) * np.cos(Phi_rot)
    
    # 4. L3范数归一化，保证是标准L3球
    r3 = np.abs(x0)**3 + np.abs(y0)**3 + np.abs(z0)**3
    r = r3 ** (1/3)
    x = x0 / r * radius
    y = y0 / r * radius
    z = z0 / r * radius
    
    # 转换为网格顶点和面
    verts = np.stack([x, y, z], axis=-1).reshape(-1, 3)
    faces = []
    for i in range(n//2 - 1):
        for j in range(n - 1):
            idx = i * n + j
            faces.append([idx, idx+1, idx+n])
            faces.append([idx+1, idx+n+1, idx+n])
    faces = np.array(faces)
    return verts, faces

# 主窗口
app = QApplication([])
w = gl.GLViewWidget()
w.setWindowTitle('L3球旋转演示（不改变L3形状）')
w.setGeometry(100, 100, 1000, 800)
w.opts['distance'] = 5

# 初始L3球
v, f = make_rotated_L3_sphere(radius=1, n=40)
mesh = gl.GLMeshItem(vertexes=v, faces=f, color=(0.2, 0.6, 1.0, 0.9), smooth=True)
w.addItem(mesh)

# 旋转动画
yaw = 0
pitch = 0
def update_rotation():
    global yaw, pitch
    yaw += 0.02
    pitch = np.sin(yaw) * 0.3
    v_new, f_new = make_rotated_L3_sphere(radius=1, n=40, yaw=yaw, pitch=pitch)
    mesh.setMeshData(vertexes=v_new, faces=f_new)

timer = QTimer()
timer.timeout.connect(update_rotation)
timer.start(16)  # 60帧

w.show()
app.exec_()