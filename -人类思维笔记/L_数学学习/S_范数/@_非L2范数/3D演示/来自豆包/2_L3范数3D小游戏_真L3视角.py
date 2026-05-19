import sys
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer

# ----------------------
# L3范数核心工具函数（全游戏逻辑的核心）
# ----------------------
def l3_dist(p1, p2):
    """L3范数距离计算，替代默认的L2距离"""
    dx = np.abs(p1[0] - p2[0])
    dy = np.abs(p1[1] - p2[1])
    dz = np.abs(p1[2] - p2[2])
    return (dx**3 + dy**3 + dz**3) ** (1/3)

def l3_normalize(vec):
    """L3范数归一化，替代L2归一化，用于移动方向计算"""
    norm = l3_dist(vec, (0,0,0))
    if norm < 1e-6:
        return vec
    return np.array(vec) / norm

# ----------------------
# 生成L3单位球顶点数据
# ----------------------
def make_L3_sphere(radius=1, n=40):
    theta = np.linspace(0, 2*np.pi, n)
    phi = np.linspace(-np.pi/2, np.pi/2, n//2)
    Theta, Phi = np.meshgrid(theta, phi)
    
    # 生成方向向量
    x0 = np.cos(Theta) * np.cos(Phi)
    y0 = np.sin(Phi)
    z0 = np.sin(Theta) * np.cos(Phi)
    
    # L3范数归一化，生成真正的L3球面
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

# ----------------------
# 主游戏窗口 + 控制器
# ----------------------
class L3WorldWindow(gl.GLViewWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('True L3 Norm 3D World')
        self.setGeometry(100, 100, 1200, 800)
        self.opts['distance'] = 0  # 第一人称视角，关闭默认轨道相机
        self.opts['fov'] = 60
        
        # 第一人称相机状态
        self.cam_pos = np.array([0.0, -5.0, 0.0], dtype=np.float32)  # 初始位置
        self.yaw = 0.0    # 左右视角（鼠标X）
        self.pitch = 0.0  # 上下视角（鼠标Y）
        self.pitch_limit = np.radians(40)  # 上下视角限制±40°
        
        # 按键状态
        self.key_state = {
            Qt.Key_W: False, Qt.Key_S: False,
            Qt.Key_A: False, Qt.Key_D: False,
            Qt.Key_Space: False, Qt.Key_Shift: False
        }
        
        # 游戏参数（全L3规则）
        self.move_speed = 2.0  # 每秒移动L3单位
        self.mouse_sensitivity = 0.002
        self.collision_radius = 0.3  # 玩家碰撞盒的L3半径
        
        # 场景物体列表（位置+L3半径），用于碰撞检测
        self.objects = []
        
        # 初始化场景
        self.init_scene()
        
        # 游戏主循环定时器（60帧）
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)  # 16ms ≈ 60fps
        
        # 鼠标捕获
        self.setMouseTracking(True)
        self.grabMouse()
        self.setFocusPolicy(Qt.StrongFocus)

    def init_scene(self):
        # 1. 添加L3地面网格
        grid = gl.GLGridItem()
        grid.setSize(20, 20)
        grid.setSpacing(1, 1)
        grid.translate(0, 0, -1)
        self.addItem(grid)
        
        # 2. 添加中心大L3球
        v, f = make_L3_sphere(radius=1.5, n=50)
        center_sphere = gl.GLMeshItem(
            vertexes=v, faces=f, 
            color=(0.2, 0.5, 1.0, 0.9), 
            smooth=True, drawEdges=False
        )
        center_pos = np.array([0.0, 0.0, 0.0])
        center_sphere.translate(*center_pos)
        self.addItem(center_sphere)
        self.objects.append((center_pos, 1.5))
        
        # 3. 添加周围6个彩色L3小球
        sphere_positions = [
            (4, 0, 0), (-4, 0, 0),
            (0, 4, 0), (0, -4, 0),
            (0, 0, 2), (0, 0, -2)
        ]
        sphere_colors = [
            (1.0, 0.3, 0.3, 0.9), (0.3, 1.0, 0.3, 0.9),
            (1.0, 1.0, 0.3, 0.9), (0.3, 1.0, 1.0, 0.9),
            (1.0, 0.3, 1.0, 0.9), (0.8, 0.8, 0.8, 0.9)
        ]
        
        for pos, color in zip(sphere_positions, sphere_colors):
            pos = np.array(pos)
            v, f = make_L3_sphere(radius=0.8, n=40)
            sphere = gl.GLMeshItem(
                vertexes=v, faces=f, 
                color=color, smooth=True, drawEdges=False
            )
            sphere.translate(*pos)
            self.addItem(sphere)
            self.objects.append((pos, 0.8))

    def keyPressEvent(self, event):
        key = event.key()
        if key in self.key_state:
            self.key_state[key] = True
        # ESC键退出
        if key == Qt.Key_Escape:
            self.releaseMouse()
            QApplication.quit()

    def keyReleaseEvent(self, event):
        key = event.key()
        if key in self.key_state:
            self.key_state[key] = False

    def mouseMoveEvent(self, event):
        # 鼠标delta控制视角，完全符合你的要求：X→yaw，Y→pitch
        delta = event.pos() - self.rect().center()
        self.yaw += delta.x() * self.mouse_sensitivity
        self.pitch -= delta.y() * self.mouse_sensitivity
        
        # 限制pitch角度，防止翻跟头
        self.pitch = np.clip(self.pitch, -self.pitch_limit, self.pitch_limit)
        
        # 鼠标固定在窗口中心
        self.cursor().setPos(self.mapToGlobal(self.rect().center()))
        
        # 更新相机视角
        self.update_camera()

    def update_camera(self):
        # 计算相机朝向
        rot_x = pg.transform3D.rotate(self.pitch * 180/np.pi, 1, 0, 0)
        rot_y = pg.transform3D.rotate(self.yaw * 180/np.pi, 0, 0, 1)
        self.opts['rotation'] = (rot_y * rot_x)
        # 设置相机位置
        self.opts['center'] = pg.Vector(*self.cam_pos)

    def check_collision(self, new_pos):
        """L3范数碰撞检测：玩家和所有球体的L3距离小于半径和，就碰撞"""
        for obj_pos, obj_radius in self.objects:
            dist = l3_dist(new_pos, obj_pos)
            if dist < (self.collision_radius + obj_radius):
                return True  # 碰撞
        return False  # 无碰撞

    def game_loop(self):
        # 计算移动方向（基于当前视角）
        forward = np.array([
            np.sin(self.yaw),
            np.cos(self.yaw),
            0.0
        ], dtype=np.float32)
        right = np.array([
            np.cos(self.yaw),
            -np.sin(self.yaw),
            0.0
        ], dtype=np.float32)
        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        
        # 合并按键输入
        move_dir = np.zeros(3, dtype=np.float32)
        if self.key_state[Qt.Key_W]: move_dir += forward
        if self.key_state[Qt.Key_S]: move_dir -= forward
        if self.key_state[Qt.Key_A]: move_dir -= right
        if self.key_state[Qt.Key_D]: move_dir += right
        if self.key_state[Qt.Key_Space]: move_dir += up
        if self.key_state[Qt.Key_Shift]: move_dir -= up
        
        # L3范数归一化移动方向，防止斜走加速
        if np.linalg.norm(move_dir) > 1e-6:
            move_dir = l3_normalize(move_dir)
        
        # 计算新位置
        delta_time = 0.016  # 60帧
        new_pos = self.cam_pos + move_dir * self.move_speed * delta_time
        
        # L3碰撞检测，无碰撞才更新位置
        if not self.check_collision(new_pos):
            self.cam_pos = new_pos
        
        # 更新相机
        self.update_camera()

# ----------------------
# 启动游戏
# ----------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 隐藏鼠标光标
    app.setOverrideCursor(Qt.BlankCursor)
    window = L3WorldWindow()
    window.show()
    sys.exit(app.exec_())