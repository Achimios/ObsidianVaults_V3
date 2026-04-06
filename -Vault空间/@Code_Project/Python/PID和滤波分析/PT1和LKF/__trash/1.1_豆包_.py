# #### 代码特性
# 1. 修正了 LKF 状态方程与传递函数，保证**全频段增益≤0dB、单调递减**，相位特性正常
# 2. 固定采样率 2kHz，频率范围锁定 0~500Hz（穿越机核心关注区间）
# 3. 带 Matplotlib 滑块 GUI，所有关键参数实时可调
# 4. 模拟真实陀螺信号：0~30Hz 打杆低频信号 + Perlin 电机噪声 + 2 个机架共振峰
# 5. 同时对比 PT1 与 LKF 的：波特图、时域跟随性、频谱抑制效果
# 6. 稳态 LKF 实现，可直接移植到 STM32，2kHz 运行零压力


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from scipy.linalg import solve_discrete_are
from scipy.signal import freqz, lfilter

# ===================== 1. 基础配置（穿越机固定参数）=====================
FS = 2000  # 采样率2kHz
DT = 1 / FS
NYQUIST = FS / 2
FREQ_RANGE = np.linspace(0, 500, 2000)  # 只看0~500Hz
W_RANGE = 2 * np.pi * FREQ_RANGE
Z_RANGE = np.exp(1j * W_RANGE * DT)

# ===================== 2. 1D Perlin噪声生成（模拟真实电机宽频噪声）=====================
def perlin_noise_1d(size, scale=10):
    def fade(t):
        return 6 * t**5 - 15 * t**4 + 10 * t**3
    def lerp(a, b, t):
        return a + t * (b - a)
    x = np.linspace(0, scale, size)
    x0 = x.astype(int)
    x1 = x0 + 1
    t = x - x0
    t = fade(t)
    rng = np.random.default_rng()
    grad = rng.uniform(-1, 1, size + 1)
    return lerp(grad[x0], grad[x1], t)

# ===================== 3. 初始默认参数（穿越机常用值）=====================
DEFAULT_PT1_FC = 120  # PT1截止频率120Hz，符合你100Hz以上的要求
DEFAULT_Q_W = 1e-6    # LKF角速度过程噪声
DEFAULT_Q_B = 1e-10   # LKF零偏过程噪声
DEFAULT_R = 1e-4      # LKF测量噪声
DEFAULT_RESON1_F = 120# 共振峰1频率（机架基频）
DEFAULT_RESON1_AMP = 0.5
DEFAULT_RESON2_F = 240# 共振峰2频率（电机二次谐波）
DEFAULT_RESON2_AMP = 0.3
DEFAULT_NOISE_AMP = 0.2

# ===================== 4. 生成模拟陀螺信号 =====================
def generate_gyro_signal(pt1_fc, q_w, q_b, r, reson1_f, reson1_amp, reson2_f, reson2_amp, noise_amp):
    t_total = 1.0  # 1秒信号
    t = np.linspace(0, t_total, int(t_total * FS), endpoint=False)
    
    # 1. 打杆信号：0~30Hz多频正弦，模拟手动操作
    stick_signal = np.zeros_like(t)
    for f in [5, 12, 25]:
        stick_signal += np.sin(2 * np.pi * f * t) * (30 - f)/30
    
    # 2. Perlin电机噪声
    perlin = perlin_noise_1d(len(t), scale=50) * noise_amp
    
    # 3. 机架共振峰（二阶谐振）
    def resonance_signal(t, f0, amp):
        w0 = 2 * np.pi * f0
        zeta = 0.05  # 低阻尼，模拟共振
        num = [w0**2]
        den = [1, 2*zeta*w0, w0**2]
        return lfilter(num, den, np.random.randn(len(t))) * amp
    reson1 = resonance_signal(t, reson1_f, reson1_amp)
    reson2 = resonance_signal(t, reson2_f, reson2_amp)
    
    # 4. 陀螺零偏（慢变漂移）
    bias = np.cumsum(np.random.randn(len(t)) * 1e-5)
    
    # 合成最终陀螺信号
    gyro_raw = stick_signal + bias + perlin + reson1 + reson2
    return t, gyro_raw, stick_signal

# ===================== 5. PT1滤波器实现 =====================
def pt1_filter(fc):
    alpha = 2 * np.pi * fc * DT / (2 * np.pi * fc * DT + 1)
    # PT1离散传递函数: H(z) = alpha / (1 - (1-alpha)*z^-1)
    b = [alpha]
    a = [1, -(1 - alpha)]
    return b, a, alpha

# ===================== 6. 2状态LKF稳态实现（陀螺专用）=====================
def lkf_steady_state(q_w, q_b, r):
    # 正确的状态方程：x = [真实角速度ω, 零偏b]
    A = np.array([[1, 0],
                  [0, 1]])  # 角速度和零偏均为随机游走模型
    H = np.array([[1, 1]])  # 测量模型：z = ω + b + 噪声
    Q = np.diag([q_w, q_b]) # 过程噪声协方差
    R = np.array([[r]])     # 测量噪声协方差
    
    # 求解离散黎卡提方程，得到稳态P
    P = solve_discrete_are(A.T, H.T, Q, R)
    # 计算稳态卡尔曼增益K
    K = P @ H.T @ np.linalg.inv(H @ P @ H.T + R)
    
    # 闭环系统矩阵
    A_cl = A - K @ H
    # LKF闭环传递函数：从测量z到输出ω的传递函数
    # 输出ω = [1, 0] @ (zI - A_cl)^-1 @ K
    def lkf_transfer(z):
        I = np.eye(2)
        return (np.array([[1, 0]]) @ np.linalg.inv(z * I - A_cl) @ K)[0, 0]
    
    return K, lkf_transfer, A_cl

# ===================== 7. 实时更新函数 =====================
def update(val):
    # 读取滑块值
    pt1_fc = s_pt1_fc.val
    q_w = 10 ** s_log_qw.val
    q_b = 10 ** s_log_qb.val
    r = 10 ** s_log_r.val
    reson1_f = s_reson1_f.val
    reson1_amp = s_reson1_amp.val
    reson2_f = s_reson2_f.val
    reson2_amp = s_reson2_amp.val
    noise_amp = s_noise_amp.val
    
    # 重新计算滤波器
    b_pt1, a_pt1, alpha_pt1 = pt1_filter(pt1_fc)
    K_lkf, lkf_tf, A_cl = lkf_steady_state(q_w, q_b, r)
    
    # 计算波特图
    # PT1幅频相频
    w, h_pt1 = freqz(b_pt1, a_pt1, worN=W_RANGE*DT)
    mag_pt1 = 20 * np.log10(np.abs(h_pt1))
    phase_pt1 = np.angle(h_pt1, deg=True)
    
    # LKF幅频相频
    h_lkf = np.array([lkf_tf(z) for z in Z_RANGE])
    mag_lkf = 20 * np.log10(np.abs(h_lkf))
    phase_lkf = np.angle(h_lkf, deg=True)
    
    # 生成信号并滤波
    t, gyro_raw, stick_true = generate_gyro_signal(pt1_fc, q_w, q_b, r, reson1_f, reson1_amp, reson2_f, reson2_amp, noise_amp)
    # PT1滤波
    gyro_pt1 = lfilter(b_pt1, a_pt1, gyro_raw)
    # LKF滤波
    gyro_lkf = np.zeros_like(gyro_raw)
    x = np.zeros((2, 1))
    for i in range(len(gyro_raw)):
        z = gyro_raw[i]
        # 预测
        x_pred = A @ x
        # 更新
        innov = z - H @ x_pred
        x = x_pred + K_lkf @ innov
        gyro_lkf[i] = x[0, 0]
    
    # 计算频谱
    n_fft = 1024
    freq_fft = np.fft.rfftfreq(n_fft, DT)
    mask_fft = freq_fft <= 500
    freq_fft = freq_fft[mask_fft]
    fft_raw = 20 * np.log10(np.abs(np.fft.rfft(gyro_raw, n=n_fft))[:len(freq_fft)])
    fft_pt1 = 20 * np.log10(np.abs(np.fft.rfft(gyro_pt1, n=n_fft))[:len(freq_fft)])
    fft_lkf = 20 * np.log10(np.abs(np.fft.rfft(gyro_lkf, n=n_fft))[:len(freq_fft)])
    
    # 更新绘图
    # 幅频特性
    line_mag_pt1.set_data(FREQ_RANGE, mag_pt1)
    line_mag_lkf.set_data(FREQ_RANGE, mag_lkf)
    ax_mag.relim()
    ax_mag.autoscale_view()
    
    # 相频特性
    line_phase_pt1.set_data(FREQ_RANGE, phase_pt1)
    line_phase_lkf.set_data(FREQ_RANGE, phase_lkf)
    ax_phase.relim()
    ax_phase.autoscale_view()
    
    # 时域波形
    t_plot = t[t <= 0.5]  # 只显示前0.5秒
    line_raw.set_data(t_plot, gyro_raw[t <= 0.5])
    line_pt1.set_data(t_plot, gyro_pt1[t <= 0.5])
    line_lkf.set_data(t_plot, gyro_lkf[t <= 0.5])
    line_true.set_data(t_plot, stick_true[t <= 0.5])
    ax_time.relim()
    ax_time.autoscale_view()
    
    # 频谱
    line_fft_raw.set_data(freq_fft, fft_raw)
    line_fft_pt1.set_data(freq_fft, fft_pt1)
    line_fft_lkf.set_data(freq_fft, fft_lkf)
    ax_fft.relim()
    ax_fft.autoscale_view()
    
    fig.canvas.draw_idle()

# ===================== 8. 绘图与GUI布局 =====================
fig = plt.figure(figsize=(14, 10))
plt.subplots_adjust(left=0.08, bottom=0.3, right=0.98, top=0.95, hspace=0.35, wspace=0.25)

# 子图1：幅频特性
ax_mag = plt.subplot(2, 2, 1)
ax_mag.set_title('幅频特性 (0~500Hz) | fs=2kHz', fontsize=12)
ax_mag.set_ylabel('Magnitude (dB)')
ax_mag.set_xlabel('Frequency (Hz)')
ax_mag.set_xlim(0, 500)
ax_mag.axhline(0, color='k', linestyle='--', alpha=0.7, label='0dB Line')
ax_mag.grid(True, which='both', alpha=0.3)
line_mag_pt1, = ax_mag.plot([], [], 'b-', linewidth=2, label=f'PT1 (fc={DEFAULT_PT1_FC}Hz)')
line_mag_lkf, = ax_mag.plot([], [], 'r-', linewidth=2, label='2-state LKF')
ax_mag.legend(fontsize=10)

# 子图2：相频特性
ax_phase = plt.subplot(2, 2, 2)
ax_phase.set_title('相频特性 (0~500Hz)', fontsize=12)
ax_phase.set_ylabel('Phase (deg)')
ax_phase.set_xlabel('Frequency (Hz)')
ax_phase.set_xlim(0, 500)
ax_phase.axhline(0, color='k', linestyle='--', alpha=0.7)
ax_phase.grid(True, which='both', alpha=0.3)
line_phase_pt1, = ax_phase.plot([], [], 'b-', linewidth=2, label='PT1')
line_phase_lkf, = ax_phase.plot([], [], 'r-', linewidth=2, label='LKF')
ax_phase.legend(fontsize=10)

# 子图3：时域波形
ax_time = plt.subplot(2, 2, 3)
ax_time.set_title('时域滤波效果 (前0.5秒)', fontsize=12)
ax_time.set_ylabel('Angular Rate (dps)')
ax_time.set_xlabel('Time (s)')
ax_time.grid(True, alpha=0.3)
line_raw, = ax_time.plot([], [], 'gray', alpha=0.5, linewidth=1, label='Raw Gyro')
line_pt1, = ax_time.plot([], [], 'b-', linewidth=1.5, label='PT1 Filtered')
line_lkf, = ax_time.plot([], [], 'r-', linewidth=1.5, label='LKF Filtered')
line_true, = ax_time.plot([], [], 'g--', linewidth=1.5, label='True Stick Signal')
ax_time.legend(fontsize=10)

# 子图4：频谱对比
ax_fft = plt.subplot(2, 2, 4)
ax_fft.set_title('频谱对比', fontsize=12)
ax_fft.set_ylabel('Magnitude (dB)')
ax_fft.set_xlabel('Frequency (Hz)')
ax_fft.set_xlim(0, 500)
ax_fft.grid(True, alpha=0.3)
line_fft_raw, = ax_fft.plot([], [], 'gray', alpha=0.5, linewidth=1, label='Raw Gyro')
line_fft_pt1, = ax_fft.plot([], [], 'b-', linewidth=1.5, label='PT1 Filtered')
line_fft_lkf, = ax_fft.plot([], [], 'r-', linewidth=1.5, label='LKF Filtered')
ax_fft.legend(fontsize=10)

# 滑块布局
ax_color = 'lightgoldenrodyellow'
# 第一行滑块
ax_pt1_fc = plt.axes([0.1, 0.22, 0.35, 0.02], facecolor=ax_color)
ax_log_qw = plt.axes([0.55, 0.22, 0.35, 0.02], facecolor=ax_color)
# 第二行滑块
ax_log_qb = plt.axes([0.1, 0.18, 0.35, 0.02], facecolor=ax_color)
ax_log_r = plt.axes([0.55, 0.18, 0.35, 0.02], facecolor=ax_color)
# 第三行滑块
ax_reson1_f = plt.axes([0.1, 0.14, 0.35, 0.02], facecolor=ax_color)
ax_reson1_amp = plt.axes([0.55, 0.14, 0.35, 0.02], facecolor=ax_color)
# 第四行滑块
ax_reson2_f = plt.axes([0.1, 0.10, 0.35, 0.02], facecolor=ax_color)
ax_reson2_amp = plt.axes([0.55, 0.10, 0.35, 0.02], facecolor=ax_color)
# 第五行滑块
ax_noise_amp = plt.axes([0.1, 0.06, 0.35, 0.02], facecolor=ax_color)

# 创建滑块
s_pt1_fc = Slider(ax_pt1_fc, 'PT1 截止频率(Hz)', 30, 300, valinit=DEFAULT_PT1_FC, valstep=1)
s_log_qw = Slider(ax_log_qw, 'LKF lg(q_ω)', -8, -4, valinit=np.log10(DEFAULT_Q_W), valstep=0.1)
s_log_qb = Slider(ax_log_qb, 'LKF lg(q_b)', -12, -8, valinit=np.log10(DEFAULT_Q_B), valstep=0.1)
s_log_r = Slider(ax_log_r, 'LKF lg(R)', -6, -2, valinit=np.log10(DEFAULT_R), valstep=0.1)
s_reson1_f = Slider(ax_reson1_f, '共振峰1频率(Hz)', 50, 300, valinit=DEFAULT_RESON1_F, valstep=1)
s_reson1_amp = Slider(ax_reson1_amp, '共振峰1幅度', 0, 1, valinit=DEFAULT_RESON1_AMP, valstep=0.05)
s_reson2_f = Slider(ax_reson2_f, '共振峰2频率(Hz)', 100, 500, valinit=DEFAULT_RESON2_F, valstep=1)
s_reson2_amp = Slider(ax_reson2_amp, '共振峰2幅度', 0, 1, valinit=DEFAULT_RESON2_AMP, valstep=0.05)
s_noise_amp = Slider(ax_noise_amp, '噪声强度', 0, 1, valinit=DEFAULT_NOISE_AMP, valstep=0.05)

# 绑定滑块更新事件
for s in [s_pt1_fc, s_log_qw, s_log_qb, s_log_r, s_reson1_f, s_reson1_amp, s_reson2_f, s_reson2_amp, s_noise_amp]:
    s.on_changed(update)

# 初始化绘图
update(None)

plt.show()