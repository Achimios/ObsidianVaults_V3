"""
LoRa CSS 解调机制验证
=====================
验证点：dechirping + FFT 是正确的 LoRa 解调方式，而非"滑动内积"

数学原理：
  符号 s 的 up-chirp 相位：phi(t) = 2π/N * (s*t + t²/2)
  基准 chirp（symbol=0）相位：phi_base(t) = 2π/N * t²/2
  dechirping = rx * conj(base) → exp(j * 2π/N * s*t)
  → 纯正弦波，频率正比于符号值 s
  → FFT 在 bin=s 处出现峰值，直接读出符号

依赖：numpy, matplotlib（标准库，无需额外安装）
运行：python src/lora_dechirp.py
输出：lora_demod_viz.png, lora_snr_curve.png
"""

import numpy as np
import matplotlib.pyplot as plt

# LoRa 参数（可修改）
SF = 7           # 扩频因子，符号数 = 2^SF = 128
BW = 125e3       # 带宽 125 kHz
N = 2**SF        # 每符号采样点数

# 确保 matplotlib 使用中文字体（如无中文字体，注释中文标签部分）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def gen_upchirp(symbol: int, N: int = N) -> np.ndarray:
    """
    生成 LoRa up-chirp（简化版，不含频率 wrap-around，足够验证解调原理）

    相位公式：phi(t) = 2π/N * (symbol * t + t²/2)
    dechirp 后得到：exp(j * 2π/N * symbol * t) — 纯正弦波
    """
    t = np.arange(N)
    phase = 2 * np.pi / N * (symbol * t + t ** 2 / 2)
    return np.exp(1j * phase)


def demodulate(rx: np.ndarray, N: int = N) -> int:
    """
    >v<🔑核心解调步骤 - dechirping + FFT

    步骤：
      1. 乘以基准 chirp 共轭（不是"滑动内积"！）
      2. FFT
      3. 取幅度最大的 bin 编号 = 检测到的符号值
    """
    base = gen_upchirp(0, N)                       # 基准 chirp（symbol=0）
    dechirped = rx * np.conj(base)                 # >v<🔑核心解调步骤 - 关键混频操作
    spectrum = np.abs(np.fft.fft(dechirped))       # FFT 频域分析
    return int(np.argmax(spectrum))                # 峰值 bin = 符号值


def add_awgn(signal: np.ndarray, snr_db: float) -> np.ndarray:
    """添加加性高斯白噪声（AWGN）"""
    signal_power = np.mean(np.abs(signal) ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = np.sqrt(noise_power / 2) * (
        np.random.randn(len(signal)) + 1j * np.random.randn(len(signal))
    )
    return signal + noise


def plot_demodulation_steps(symbol: int = 42, save_path: str = "lora_demod_viz.png"):
    """
    可视化三步解调流程：时域信号 → Dechirping 后信号 → FFT 频谱
    """
    tx = gen_upchirp(symbol)
    base = gen_upchirp(0)
    dechirped = tx * np.conj(base)
    spectrum = np.abs(np.fft.fft(dechirped))
    detected = int(np.argmax(spectrum))

    fig, axes = plt.subplots(3, 1, figsize=(11, 9))
    fig.suptitle(
        f"LoRa CSS 解调流程验证  |  发送符号: {symbol}  |  SF={SF}  |  BW={BW/1e3:.0f} kHz",
        fontsize=13, fontweight='bold'
    )

    t_axis = np.arange(N)

    # 图1：接收信号（时域）
    axes[0].plot(t_axis, np.real(tx), linewidth=0.7, color='steelblue')
    axes[0].set_title("① 接收信号（Up-chirp 时域实部）— 频率随时间线性增加")
    axes[0].set_xlabel("样本序号"); axes[0].set_ylabel("实部幅度")
    axes[0].grid(True, alpha=0.3)

    # 图2：Dechirping 后（应变成等频正弦波）
    axes[1].plot(t_axis, np.real(dechirped), linewidth=0.7, color='darkorange')
    axes[1].set_title(
        f"② Dechirping 后（乘以共轭基准 chirp）→ 变成单频正弦波，频率 = {symbol}/N"
    )
    axes[1].set_xlabel("样本序号"); axes[1].set_ylabel("实部幅度")
    axes[1].grid(True, alpha=0.3)

    # 图3：FFT 频谱
    axes[2].plot(np.arange(N), spectrum, color='gray', linewidth=0.5)
    axes[2].axvline(x=detected, color='red', linestyle='--', linewidth=1.5,
                    label=f'峰值 bin = {detected}（应为 {symbol}）✓' if detected == symbol else f'峰值 bin = {detected}（应为 {symbol}）✗')
    axes[2].set_title("③ FFT 频谱 — 峰值 bin 编号 = 解调出的符号值")
    axes[2].set_xlabel("频率 Bin"); axes[2].set_ylabel("幅度")
    axes[2].set_xlim([0, N - 1]); axes[2].legend(); axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=130, bbox_inches='tight')
    print(f"[图表] 已保存: {save_path}")
    plt.show()
    print(f"[验证] 发送: {symbol}, 检测到: {detected},", "✓ 正确" if detected == symbol else "✗ 错误")


def snr_sweep_test(
    num_symbols: int = 200,
    snr_range_db=None,
    save_path: str = "lora_snr_curve.png"
):
    """
    SNR 扫描测试：不同信噪比下的符号检测正确率
    """
    if snr_range_db is None:
        snr_range_db = np.arange(-20, 22, 2)

    accuracy = []
    print("\n[SNR 扫描测试]")
    print(f"  SF={SF}, N={N}, 每点 {num_symbols} 个符号")
    print("  " + "-" * 40)

    rng = np.random.default_rng(42)

    for snr_db in snr_range_db:
        correct = 0
        for _ in range(num_symbols):
            sym = int(rng.integers(0, N))
            rx = add_awgn(gen_upchirp(sym), snr_db)
            if demodulate(rx) == sym:
                correct += 1
        acc = correct / num_symbols
        accuracy.append(acc)
        bar = "█" * int(acc * 20)
        print(f"  SNR = {snr_db:+4.0f} dB  {bar:<20s}  {acc*100:5.1f}%")

    # 绘制曲线
    plt.figure(figsize=(9, 5))
    plt.plot(snr_range_db, accuracy, 'bo-', linewidth=1.5, markersize=5)
    plt.axhline(y=0.99, color='green', linestyle='--', alpha=0.7, label='99% 正确率基准线')
    plt.xlabel("SNR (dB)"); plt.ylabel("符号检测正确率")
    plt.title(f"LoRa Dechirping+FFT 解调性能曲线  |  SF={SF}, N={N}, {num_symbols} 符号/点")
    plt.grid(True, alpha=0.4); plt.ylim([-0.05, 1.05]); plt.legend()
    plt.savefig(save_path, dpi=130, bbox_inches='tight')
    print(f"\n[图表] 已保存: {save_path}")
    plt.show()

    # 找到 99% 正确率的门限 SNR
    for snr, acc in zip(snr_range_db, accuracy):
        if acc >= 0.99:
            print(f"[结论] 99% 门限 SNR ≈ {snr:+.0f} dB")
            break


def run_quick_verification():
    """无噪声快速验证：所有边界符号值应 100% 正确"""
    print("\n[无噪声验证]")
    test_symbols = [0, 1, N // 4, N // 2, N - 2, N - 1]
    all_ok = True
    for sym in test_symbols:
        detected = demodulate(gen_upchirp(sym))
        ok = detected == sym
        all_ok = all_ok and ok
        print(f"  发送: {sym:3d}, 检测: {detected:3d}  {'✓' if ok else '✗'}")
    print(f"  → {'全部正确 ✓' if all_ok else '有错误 ✗'}\n")
    return all_ok


if __name__ == "__main__":
    print("=" * 50)
    print(" LoRa CSS 解调机制验证")
    print(f" SF={SF}, N={N}, BW={BW/1e3:.0f} kHz")
    print("=" * 50)

    # 1. 无噪声验证
    run_quick_verification()

    # 2. 解调流程可视化（symbol=42）
    print("[生成解调流程三联图...]")
    plot_demodulation_steps(symbol=42)

    # 3. SNR 扫描（快速版：100 符号/点）
    snr_sweep_test(num_symbols=100)
