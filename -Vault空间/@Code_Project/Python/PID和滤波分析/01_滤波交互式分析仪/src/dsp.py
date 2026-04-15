# dsp.py — 信号处理核心函数
# perlin_noise_1d / pt1_coeffs / lkf_coeffs / resonance / notch_coeffs / resonance_dist

import numpy as np
from scipy.signal import freqz, lfilter, welch, butter, iirnotch, bilinear
from constants import FS

def perlin_noise_1d(n, octaves=5, persistence=0.5, lacunarity=2.0, seed=7,
                    base_freq=40.0, coord_offset=0.0):
    """Perlin-style 1D noise sampled at n points.
    base_freq    : base octave frequency in Hz — controls knot density (default 40 Hz).
    coord_offset : integer domain offset — slide to get a different noise patch.
    coord_offset=0 reproduces old behavior exactly (same random sequence).
    """
    rng = np.random.default_rng(int(seed))
    result = np.zeros(n)
    amp = 1.0
    freq_mult = 1.0
    total_amp = 0.0
    co = max(0, int(coord_offset))
    for _ in range(octaves):
        n_knots = max(2, int(n * base_freq * freq_mult / FS))
        n_total = co + n_knots + 2              # enough knots to cover offset window
        knots   = rng.standard_normal(n_total)
        t       = np.linspace(co, co + n_knots, n)   # shifted domain window
        idx     = np.clip(t.astype(int), 0, n_total - 2)
        frac    = t - idx
        s       = frac * frac * (3.0 - 2.0 * frac)   # smoothstep
        val     = knots[idx] * (1.0 - s) + knots[idx + 1] * s
        result += val * amp
        total_amp += amp
        amp *= persistence
        freq_mult *= lacunarity
    return result / total_amp


# ─────────────────────────────────────────────────────────────────
#  PT1 系数
# ─────────────────────────────────────────────────────────────────
def pt1_coeffs(fc, fs=FS):
    a = 2 * np.pi * fc / fs
    a /= (1 + a)
    return [a], [1.0, -(1.0 - a)]


def pt1_coeffs_bilinear(fc, fs=FS):
    """PT1 bilinear (Tustin): s → (2/T)(z-1)/(z+1). Two b-coeffs."""
    wc = 2 * np.pi * fc
    k = 2 * fs          # 2/T
    b0 = wc / (k + wc)
    b1 = b0             # symmetric
    a1 = (wc - k) / (wc + k)
    return [b0, b1], [1.0, a1]


# ─────────────────────────────────────────────────────────────────
#  2-state LKF — Riccati 迭代至稳态
# ─────────────────────────────────────────────────────────────────
def lkf_coeffs(q_omega, q_bias, r_meas, fs=FS, obs_mode=0):
    """obs_mode: 0=原始 H=[1,1], 1=DC归一化, 2=H=[1,0](无bias观测)"""
    ts = 1.0 / fs
    F = np.array([[1.0, -ts], [0.0, 1.0]])
    H = np.array([[1.0, 0.0]]) if obs_mode == 2 else np.array([[1.0, 1.0]])
    Q = np.diag([q_omega * ts, q_bias * ts])
    R = float(r_meas)

    P = np.eye(2)
    for _ in range(150):    # 2-state Riccati 约50-100步收敛，150足够
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
    # DC归一化: 使 H(1)=1
    if obs_mode == 1:
        dc_gain = sum(b_num) / sum(a_den)
        if abs(dc_gain) > 1e-12:
            b_num = [x / dc_gain for x in b_num]
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


def custom_tf_to_digital(num_s, den_s, fs=FS):
    """H(s) = num(s)/den(s) → H(z) via bilinear transform.
    num_s, den_s: list of float, highest power first (e.g. [s^2, s^1, s^0]).
    Returns (b_z, a_z) for lfilter / freqz."""
    b_z, a_z = bilinear(num_s, den_s, fs=fs)
    return b_z, a_z


def teo(x):
    """Teager Energy Operator: T[x(n)] = x(n)^2 - x(n-1)*x(n+1).
    Returns array of same length (edges extrapolated)."""
    y = np.empty_like(x)
    y[1:-1] = x[1:-1]**2 - x[:-2] * x[2:]
    y[0] = y[1]
    y[-1] = y[-2]
    return y


# ─────────────────────────────────────────────────────────────────
#  PID 闭环传递函数（被控对象 G(s)=1/s，角加速度→角速率）
# ─────────────────────────────────────────────────────────────────
def pid_cl_coeffs(kp, ki, kd, f_dlp, fs=FS):
    """Closed-loop PID rate controller: setpoint → actual angular rate.

    Plant: G(s) = 1/s
    Controller: C(s) = Kp + Ki/s + Kd·s/(1+τd·s)
    T_cl(s) = C·G / (1 + C·G)
           = (Kd·s² + Kp·s + Ki) / (τd·s³ + (1+Kd)·s² + Kp·s + Ki)

    Returns (b_z, a_z) via bilinear transform for lfilter / freqz.
    """
    tau_d = 1.0 / (2.0 * np.pi * max(f_dlp, 1.0))
    num_s = [kd, kp, ki]
    den_s = [tau_d, 1.0 + kd, kp, ki]
    b_z, a_z = bilinear(num_s, den_s, fs=fs)
    return b_z, a_z


# ─────────────────────────────────────────────────────────────────
#  工具函数：-3dB / 差分格式化 / 多项式字符串
# ─────────────────────────────────────────────────────────────────
def find_3db_freq(b, a, fs=FS):
    """Find -3dB cutoff frequency of a digital lowpass filter.
    Returns freq in Hz or None if not found."""
    w = np.linspace(0, np.pi, 20000)
    _, H = freqz(b, a, worN=w)
    mag = np.abs(H)
    dc = mag[0]
    if dc < 1e-15:
        return None
    target = dc / np.sqrt(2)
    idx = np.where(np.diff(np.sign(mag - target)))[0]
    if len(idx) == 0:
        return None
    i = idx[0]
    f0 = w[i] * fs / (2 * np.pi)
    f1 = w[i + 1] * fs / (2 * np.pi)
    m0 = mag[i] - target
    m1 = mag[i + 1] - target
    return f0 + (f1 - f0) * m0 / (m0 - m1)


def diff_eq_str(b, a):
    """Format z-domain coefficients as a difference equation string.
    y[n] = b0·x[n] + b1·x[n-1] + ... - a1·y[n-1] - ...
    Assumes a[0] is normalized to 1."""
    parts = []
    for i, bi in enumerate(b):
        if abs(bi) < 1e-15:
            continue
        tag = f"x[n{-i}]" if i > 0 else "x[n]"
        parts.append(f"{bi:+.4g}·{tag}")
    for i in range(1, len(a)):
        ai = a[i]
        if abs(ai) < 1e-15:
            continue
        tag = f"y[n{-i}]"
        parts.append(f"{-ai:+.4g}·{tag}")
    if not parts:
        return "y[n] = 0"
    s = " ".join(parts)
    if s.startswith('+'):
        s = s[1:]
    return f"y[n] = {s}"


def poly_str(coeffs, var='s'):
    """Format polynomial coefficients (highest power first) as readable string."""
    parts = []
    n = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        pw = n - i
        if abs(c) < 1e-15:
            continue
        cs = f"{c:g}"
        if pw == 0:
            parts.append(cs)
        elif pw == 1:
            parts.append(f"{cs}·{var}" if c != 1 else var)
        else:
            sup = '²' if pw == 2 else '³' if pw == 3 else f'^{pw}'
            parts.append(f"{cs}·{var}{sup}" if c != 1 else f"{var}{sup}")
    return " + ".join(parts) if parts else "0"


def poly_z_str(coeffs):
    """Format z-domain coefficients (z^-n order) as readable string.
    coeffs[0] → z⁰ term, coeffs[1] → z⁻¹, coeffs[2] → z⁻², etc."""
    _sup = {2: '⁻²', 3: '⁻³', 4: '⁻⁴', 5: '⁻⁵'}
    parts = []
    for i, c in enumerate(coeffs):
        if abs(c) < 1e-15:
            continue
        cs = f"{c:.4g}" if not parts else f"{c:+.4g}"
        if i == 0:
            parts.append(cs)
        elif i == 1:
            parts.append(f"{cs}·z⁻¹")
        else:
            parts.append(f"{cs}·z{_sup.get(i, f'^(-{i})')}")
    return "".join(parts) if parts else "0"


# ─────────────────────────────────────────────────────────────────
#  PID 逐帧迭代闭环仿真
# ─────────────────────────────────────────────────────────────────
def pid_iterate(setpoint, noise, kp, ki, kd, f_dlp,
                b_filt, a_filt, b_notch_list, a_notch_list,
                fs=FS, plant_gain=1.0):
    """Frame-by-frame PID closed-loop simulation.

    Signal flow per frame (measurement-noise model):
        error = setpoint[n] - gyro_filtered[n-1]
        pid_sum = PID差分(error)    (P + I + D with D-term lowpass)
        delta_omega = pid_sum * plant_gain * Ts
        gyro_actual[n] = gyro_actual[n-1] + delta_omega      (pure physics)
        gyro_unfiltered[n] = gyro_actual[n] + noise[n]        (sensor reading)
        gyro_filtered[n] = apply_filters(gyro_unfiltered[0..n])

    Noise is treated as sensor noise (not process disturbance), so it does NOT
    get accumulated by the plant integrator.

    PID implementation (forward Euler, Betaflight-style):
        P = Kp * error
        I += Ki * error * Ts  (with anti-windup clamping)
        D = Kd * (error - prev_error) / Ts, lowpassed by PT1(f_dlp)

    Args:
        setpoint: (N,) array — desired angular rate
        noise: (N,) array — sensor noise (white + perlin + resonance)
        kp, ki, kd: PID gains
        f_dlp: D-term lowpass cutoff (Hz)
        b_filt, a_filt: feedback filter coefficients (PT1/LKF/DEQ) or ([1],[1]) for unfiltered
        b_notch_list, a_notch_list: list of (b,a) tuples for notch filters
        fs: sample rate
        plant_gain: angular_accel → angular_rate scaling (default 1.0)

    Returns:
        gyro_unfiltered: (N,) sensor reading = actual angular rate + noise
        gyro_filtered: (N,) filtered feedback signal
    """
    N = len(setpoint)
    Ts = 1.0 / fs
    gyro_actual = np.zeros(N)   # true physical angular rate (no noise)
    gyro_unfilt = np.zeros(N)   # sensor reading = actual + noise
    gyro_filt = np.zeros(N)

    # Filter state buffers (b_filt / a_filt as difference equation)
    b_f = np.asarray(b_filt, dtype=np.float64)
    a_f = np.asarray(a_filt, dtype=np.float64)
    # Normalize a_f
    if abs(a_f[0]) > 1e-15 and a_f[0] != 1.0:
        b_f = b_f / a_f[0]
        a_f = a_f / a_f[0]
    nb = len(b_f)
    na = len(a_f)

    # Notch filters state
    notch_states = []
    for bn, an in zip(b_notch_list, a_notch_list):
        bn_ = np.asarray(bn, dtype=np.float64)
        an_ = np.asarray(an, dtype=np.float64)
        if abs(an_[0]) > 1e-15 and an_[0] != 1.0:
            bn_ = bn_ / an_[0]; an_ = an_ / an_[0]
        notch_states.append((bn_, an_, np.zeros(len(bn_)), np.zeros(len(an_))))

    # PID state
    integral = 0.0
    prev_error = 0.0
    d_filtered = 0.0
    # D-term PT1 coefficient (forward Euler)
    alpha_d = 2.0 * np.pi * max(f_dlp, 1.0) * Ts
    alpha_d = alpha_d / (1.0 + alpha_d)

    # Filter history buffers (ring buffer style)
    x_hist = np.zeros(nb)  # input to main filter
    y_hist = np.zeros(na)  # output of main filter

    # Anti-windup limit
    i_limit = 500.0 * Ts * ki * 100 if ki > 0 else 1e9

    for n in range(N):
        # --- PID computation ---
        error = setpoint[n] - gyro_filt[n - 1] if n > 0 else setpoint[n]

        # P
        p_term = kp * error
        # I (forward Euler with anti-windup)
        integral += ki * error * Ts
        integral = np.clip(integral, -i_limit, i_limit)
        i_term = integral
        # D (derivative of error, PT1 lowpassed)
        d_raw = kd * (error - prev_error) / Ts
        d_filtered += alpha_d * (d_raw - d_filtered)
        d_term = d_filtered
        prev_error = error

        pid_sum = p_term + i_term + d_term

        # --- Plant: angular acceleration → angular rate increment ---
        delta_omega = pid_sum * plant_gain * Ts
        gyro_actual[n] = (gyro_actual[n - 1] if n > 0 else 0.0) + delta_omega

        # --- Sensor measurement: actual + noise ---
        gyro_unfilt[n] = gyro_actual[n] + noise[n]

        # --- Feedback filter (difference equation) ---
        # Shift input history and insert new sample
        x_hist[1:] = x_hist[:-1]
        x_hist[0] = gyro_unfilt[n]
        # Compute filtered output: y[n] = sum(b*x) - sum(a[1:]*y)
        val = np.dot(b_f, x_hist[:nb])
        for j in range(1, na):
            val -= a_f[j] * y_hist[j - 1] if j - 1 < len(y_hist) else 0.0
        # Shift output history
        y_hist[1:] = y_hist[:-1]
        y_hist[0] = val

        # Apply notch filters sequentially
        for k, (bn_, an_, xh, yh) in enumerate(notch_states):
            xh[1:] = xh[:-1]; xh[0] = val
            v = np.dot(bn_, xh[:len(bn_)])
            for j in range(1, len(an_)):
                v -= an_[j] * yh[j - 1] if j - 1 < len(yh) else 0.0
            yh[1:] = yh[:-1]; yh[0] = v
            val = v

        gyro_filt[n] = val

    return gyro_unfilt, gyro_filt
