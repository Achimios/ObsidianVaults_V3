import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import freqz

# --------------------------
# 参数（穿越机常用：2kHz）
# --------------------------
fs = 2000
ts = 1.0 / fs

# PT1 截止频率 (Hz)
fc_pt1 = 20

# 2 状态 LKF (ω + b)，调至和 PT1 抑制水平接近
# 过程噪声 Q，观测噪声 R
q_omega = 0.25
q_bias = 1e-6
r_meas = 5

# --------------------------
# PT1 离散系数
# --------------------------
alpha = 2 * np.pi * fc_pt1 * ts / (1 + 2 * np.pi * fc_pt1 * ts)
b_pt1 = [alpha]
a_pt1 = [1, -(1 - alpha)]

# --------------------------
# 2 状态离散 LKF 传递函数（gyro → omega_est）
# 推导为等价离散 IIR，直接用于 freqz
# --------------------------
def lkf_gyro_tf(q_omega, q_bias, r_meas, ts):
    F = np.array([[1, -ts],
                  [0,  1]])
    H = np.array([[1, 1]])
    Q = np.diag([q_omega, q_bias]) * ts
    R = r_meas

    P = np.array([[0.1, 0],
                  [0, 0.1]])
    S = H @ P @ H.T + R
    K = P @ H.T @ np.linalg.inv(S)

    A = F - K @ H @ F
    B = K
    C = np.array([[1, 0]])
    D = np.array([[0]])

    a0 = 1.0
    a1 = -(A[0,0] + A[1,1])
    a2 = A[0,0]*A[1,1] - A[0,1]*A[1,0]
    b0 = C[0,0]*B[0,0] + C[0,1]*B[1,0]
    b1 = (-A[1,1]*C[0,0] - A[0,0]*C[0,1])*B[0,0] + (A[0,1]*C[0,0] - A[0,0]*C[0,1])*B[1,0]

    b_lkf = [b1, b0]
    a_lkf = [a2, a1, a0]
    return b_lkf, a_lkf

b_lkf, a_lkf = lkf_gyro_tf(q_omega, q_bias, r_meas, ts)

# --------------------------
# 计算频响
# --------------------------
f = np.logspace(0, np.log10(fs/2), 500)
w = 2 * np.pi * f / fs

# PT1
w_pt1, h_pt1 = freqz(b_pt1, a_pt1, worN=w)
mag_pt1 = 20 * np.log10(np.abs(h_pt1))
phase_pt1 = np.angle(h_pt1, deg=True)

# LKF
w_lkf, h_lkf = freqz(b_lkf, a_lkf, worN=w)
mag_lkf = 20 * np.log10(np.abs(h_lkf))
phase_lkf = np.angle(h_lkf, deg=True)

# --------------------------
# 绘图
# --------------------------
plt.figure(figsize=(12,7))

# 幅频
plt.subplot(2,1,1)
plt.semilogx(f, mag_pt1, label=f'PT1 (fc={fc_pt1}Hz)', linewidth=1.6)
plt.semilogx(f, mag_lkf, label='2-state LKF (ω+b)', linewidth=1.6)
plt.grid(True, which='both', alpha=0.3)
plt.ylim(-60, 5)
plt.ylabel('Magnitude (dB)')
plt.title('PT1 vs 2-state LKF (gyro rate filter) | fs=2kHz')
plt.legend()
plt.axhline(0, color='k', linestyle='--', alpha=0.3)

# 相频
plt.subplot(2,1,2)
plt.semilogx(f, phase_pt1, linewidth=1.6)
plt.semilogx(f, phase_lkf, linewidth=1.6)
plt.grid(True, which='both', alpha=0.3)
plt.xlabel('Frequency (Hz)')
plt.ylabel('Phase (deg)')
plt.ylim(-180, 10)

plt.tight_layout()
plt.show()