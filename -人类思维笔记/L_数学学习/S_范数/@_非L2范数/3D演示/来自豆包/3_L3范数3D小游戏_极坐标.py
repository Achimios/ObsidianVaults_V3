import numpy as np
import matplotlib.pyplot as plt

# L3极坐标转笛卡尔坐标
def l3_polar_to_cart(r, theta):
    x_dir = np.cos(theta)
    y_dir = np.sin(theta)
    r_p = (np.abs(x_dir)**3 + np.abs(y_dir)**3) ** (1/3)
    x = r * x_dir / r_p
    y = r * y_dir / r_p
    return x, y

# 生成L3极坐标网格
theta = np.linspace(0, 2*np.pi, 100)
r_list = np.linspace(0, 2, 5)

plt.figure(figsize=(8,8))
# 画径向线（固定theta，变化r）
for t in theta[::10]:
    x, y = l3_polar_to_cart(r_list, t)
    plt.plot(x, y, color='#cccccc', linewidth=0.8)
# 画角向线（固定r，变化theta）
for r in r_list[1:]:
    x, y = l3_polar_to_cart(r, theta)
    plt.plot(x, y, color='#3366cc', linewidth=1.2)

# 对比L2单位圆
x_circle = np.cos(theta)
y_circle = np.sin(theta)
plt.plot(x_circle, y_circle, color='#cc3333', linestyle='--', label='L2单位圆')

plt.title('L3范数极坐标网格', fontsize=14)
plt.axis('equal')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()