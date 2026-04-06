# dsp.py — 信号处理核心函数
# perlin_noise_1d / pt1_coeffs / lkf_coeffs / resonance / notch_coeffs / resonance_dist

import numpy as np
from scipy.signal import freqz, lfilter, welch, butter, iirnotch
from constants import FS

def perlin_noise_1d(n, octaves=5, persistence=0.5, lacunarity=2.0, seed=7):
    rng = np.random.default_rng(seed)
    result = np.zeros(n)
    amp = 1.0
    freq = 1.0
    total_amp = 0.0
    for _ in range(octaves):
        n_knots = max(2, int(n * freq / 50))   # 每 octave 的控制点数
        knots = rng.standard_normal(n_knots + 2)
        t = np.linspace(0, n_knots, n)
        idx = np.clip(t.astype(int), 0, n_knots - 1)
        frac = t - idx
        s = frac * frac * (3.0 - 2.0 * frac)  # smoothstep
        val = knots[idx] * (1.0 - s) + knots[idx + 1] * s
        result += val * amp
        total_amp += amp
        amp *= persistence
        freq *= lacunarity
    return result / total_amp


# ─────────────────────────────────────────────────────────────────
#  PT1 系数
# ─────────────────────────────────────────────────────────────────
def pt1_coeffs(fc, fs=FS):
    a = 2 * np.pi * fc / fs
    a /= (1 + a)
    return [a], [1.0, -(1.0 - a)]


# ─────────────────────────────────────────────────────────────────
#  2-state LKF — Riccati 迭代至稳态
# ─────────────────────────────────────────────────────────────────
def lkf_coeffs(q_omega, q_bias, r_meas, fs=FS):
    ts = 1.0 / fs
    F = np.array([[1.0, -ts], [0.0, 1.0]])
    H = np.array([[1.0, 1.0]])
    Q = np.diag([q_omega * ts, q_bias * ts])
    R = float(r_meas)

    P = np.eye(2)
    for _ in range(3000):   # 迭代 Riccati 到稳态
        P_pred = F @ P @ F.T + Q
        S = float((H @ P_pred @ H.T).item()) + R
        K = (P_pred @ H.T) / S      # shape (2, 1)
        P = (np.eye(2) - K @ H) @ P_pred

    # 闭环系统矩阵
    A = F - K @ H @ F
    K0 = float(K[0, 0])
    K1 = float(K[1, 0])
    A00, A01 = A[0, 0], A[0, 1]
    A10, A11 = A[1, 0], A[1, 1]

    # 传递函数 H(z) = C(zI-A)^{-1}B，C=[1,0]
    # 分子: K0*z + (-A11*K0 + A01*K1) — 转成 z^{-n} 形式除以分母
    # 分母特征多项式: z^2 - tr(A)*z + det(A)
    tr_A  = A00 + A11
    det_A = A00 * A11 - A01 * A10

    b_num = [0.0, K0, -A11 * K0 + A01 * K1]   # [z^0, z^{-1}, z^{-2}]
    a_den = [1.0, -tr_A, det_A]                 # [z^0, z^{-1}, z^{-2}]
    return b_num, a_den


# ─────────────────────────────────────────────────────────────────
#  机架共振：带通滤波白噪声增益叠加（增益用线性倍数，不用dB）
# ─────────────────────────────────────────────────────────────────
def resonance(white, freq_r, gain_lin, q_factor, fs=FS):
    """gain_lin: 线性增益倍数（1 = 0 dB, 10 = 20 dB）"""
    if gain_lin <= 0 or freq_r <= 0:
        return np.zeros_like(white)
    bw  = freq_r / max(q_factor, 0.5)
    nyq = fs / 2.0
    lo  = max((freq_r - bw / 2.0) / nyq, 1e-4)
    hi  = min((freq_r + bw / 2.0) / nyq, 1.0 - 1e-4)
    if lo >= hi:
        return np.zeros_like(white)
    b, a = butter(2, [lo, hi], btype='band')
    out  = lfilter(b, a, white)
    rms  = np.std(out)
    if rms < 1e-12:
        return np.zeros_like(white)
    return out / rms * gain_lin


# ─────────────────────────────────────────────────────────────────
#  Notch 系数
# ─────────────────────────────────────────────────────────────────
def notch_coeffs(freq, q, fs=FS):
    w0 = np.clip(freq / (fs / 2.0), 1e-5, 1.0 - 1e-5)
    return iirnotch(w0, Q=max(float(q), 0.5))

# ───────────────────────────────────────────────────────────────
#  共振分布模式：多峰微高斯散布
# ───────────────────────────────────────────────────────────────
def resonance_dist(white, freq_r, gain_lin, q_factor, n_peaks, f_spread, seed_val, fs=FS):
    """Multiple resonance peaks distributed ±f_spread around freq_r (4-motor variance)."""
    rng = np.random.RandomState(int(seed_val) % (2**31))
    offsets = rng.normal(0, max(float(f_spread), 1.0) / 3.0, int(n_peaks))
    g_each  = gain_lin / max(np.sqrt(n_peaks), 1.0)   # RMS 均匀
    total   = np.zeros(len(white))
    for off in offsets:
        total += resonance(white, freq_r + off, g_each, q_factor, fs)
    return total
