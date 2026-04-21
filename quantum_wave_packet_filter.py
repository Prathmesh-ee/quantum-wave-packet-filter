import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.widgets import Slider
from matplotlib.animation import FuncAnimation

plt.style.use('dark_background')

# ─────────────────────────────────────────────
#  RC LOW-PASS FILTER PARAMETERS
#  R = 1000 Ω, C = 1e-6 F  →  fc ≈ 159 Hz
#  In wave-number units: cutoff at k_c = 1.0
# ─────────────────────────────────────────────
R = 1000          # Ohms
C = 1e-6          # Farads
fc_hz = 1 / (2 * np.pi * R * C)   # ≈ 159.15 Hz
k_cutoff = 1.0    # wave-number cutoff (mapped from fc for visualization)

# Domain
x = np.linspace(-10, 10, 1000)
dx = x[1] - x[0]
L = 20

# Initial parameters
k0_init = 2.0
sigma_init = 1.0

# ─── Figure layout: 3 rows ───
fig = plt.figure(figsize=(12, 10))
plt.subplots_adjust(hspace=0.55, bottom=0.22, top=0.93, left=0.1, right=0.95)

ax1 = fig.add_subplot(3, 1, 1)   # Position space
ax2 = fig.add_subplot(3, 1, 2)   # Momentum space + filter cutoff
ax3 = fig.add_subplot(3, 1, 3)   # Filtered signal (inverse FFT back to position)

fig.suptitle("Quantum Wave Packet  ·  Signal Filtering  ·  RC Low-Pass Filter",
             color='cyan', fontsize=13, fontweight='bold')

# ── Axis labels ──
ax1.set_title("Position Space  —  ψ(x)", color='white', fontsize=10)
ax1.set_xlabel("Position (x)", fontsize=9)
ax1.set_ylabel("Amplitude", fontsize=9)

ax2.set_title(
    f"Momentum / Frequency Space  —  RC Filter  |  R=1kΩ, C=1µF  |  fc ≈ {fc_hz:.1f} Hz  (k_cutoff = {k_cutoff})",
    color='white', fontsize=9)
ax2.set_xlabel("Wave Number (k)", fontsize=9)
ax2.set_ylabel("Spectral Power", fontsize=9)

ax3.set_title("Filtered Signal  —  Only LOW frequencies kept (Inverse FFT)", color='white', fontsize=10)
ax3.set_xlabel("Position (x)", fontsize=9)
ax3.set_ylabel("Amplitude", fontsize=9)

# ── Plot lines ──
line_wave,     = ax1.plot([], [], color='cyan',   lw=1.8, label='ψ(x)  — wave packet')
line_prob,     = ax1.plot([], [], color='yellow', lw=1.2, label='|ψ(x)|²  — probability density', alpha=0.8)

line_fft,      = ax2.plot([], [], color='orange', lw=2,   label='|ψ(k)|²  — frequency spectrum')
line_pass,     = ax2.plot([], [], color='#00ff88', lw=1.5, linestyle='--', label=f'PASS  (k < {k_cutoff})')
line_block,    = ax2.plot([], [], color='red',     lw=1.5, linestyle='--', label=f'BLOCK (k > {k_cutoff})')
vline_cutoff   = ax2.axvline(x=k_cutoff,  color='white', lw=1.2, linestyle=':')
vline_cutoff_n = ax2.axvline(x=-k_cutoff, color='white', lw=1.2, linestyle=':')

line_filtered, = ax3.plot([], [], color='#00ff88', lw=2,   label='Filtered ψ(x)  — clean signal')
line_original, = ax3.plot([], [], color='cyan',    lw=1,   label='Original ψ(x)', alpha=0.35, linestyle='--')

# Cutoff annotation on ax2
cutoff_label = ax2.text(k_cutoff + 0.1, 0, f'  k_c = {k_cutoff}\n  fc ≈ {fc_hz:.0f} Hz',
                         color='white', fontsize=7.5, va='bottom')

# Shaded PASS / BLOCK regions (static background)
pass_patch  = mpatches.Patch(color='#00ff88', alpha=0.07, label='PASS region')
block_patch = mpatches.Patch(color='red',     alpha=0.07, label='BLOCK region')

ax1.legend(fontsize=8, loc='upper left')
ax2.legend(fontsize=8, loc='upper right')
ax3.legend(fontsize=8, loc='upper left')

for ax in [ax1, ax2, ax3]:
    ax.grid(alpha=0.2)
    ax.tick_params(labelsize=8)

# ── Sliders ──
ax_k0    = plt.axes([0.15, 0.11, 0.7, 0.025])
ax_sigma = plt.axes([0.15, 0.06, 0.7, 0.025])
ax_kcut  = plt.axes([0.15, 0.01, 0.7, 0.025])

slider_k0    = Slider(ax_k0,    'k₀  (carrier frequency)', 0.5, 8.0, valinit=k0_init,    color='cyan')
slider_sigma = Slider(ax_sigma, 'σ   (packet width)',       0.5, 3.0, valinit=sigma_init, color='yellow')
slider_kcut  = Slider(ax_kcut,  'k_cutoff  (filter)',       0.3, 6.0, valinit=k_cutoff,   color='#00ff88')

# ── RC filter in k-space: H(k) = 1 / sqrt(1 + (k/k_c)^2) ──
def rc_filter_response(k_arr, k_c):
    return 1.0 / np.sqrt(1.0 + (k_arr / k_c) ** 2)

frame_count = [0]

def update(frame):
    frame_count[0] += 1
    k0    = slider_k0.val
    sigma = slider_sigma.val
    k_c   = slider_kcut.val

    # Moving center
    center = (0.03 * frame) % L - L / 2

    # ── 1. Wave packet in position space ──
    psi = np.exp(-((x - center) ** 2) / (2 * sigma ** 2)) * np.cos(k0 * (x - center))
    prob_x = psi ** 2
    prob_x /= np.trapezoid(prob_x, x)

    # ── 2. FFT → momentum space ──
    psi_k_raw = np.fft.fftshift(np.fft.fft(psi))
    k_arr     = np.fft.fftshift(np.fft.fftfreq(len(x), d=dx)) * (2 * np.pi)
    prob_k    = np.abs(psi_k_raw) ** 2
    norm_k    = np.trapezoid(prob_k, k_arr)
    if norm_k > 0:
        prob_k /= norm_k

    # ── 3. Apply RC low-pass filter in k-space ──
    H = rc_filter_response(k_arr, k_c)
    psi_k_filtered = psi_k_raw * H

    # ── 4. Inverse FFT → filtered position-space signal ──
    psi_filtered = np.real(np.fft.ifft(np.fft.ifftshift(psi_k_filtered)))

    # ── Update ax1: position space ──
    line_wave.set_data(x, psi)
    line_prob.set_data(x, prob_x)
    ax1.set_xlim(-10, 10)
    ax1.set_ylim(-1.6, 1.6)

    # ── Update ax2: momentum space + filter regions ──
    line_fft.set_data(k_arr, prob_k)

    # Split into PASS and BLOCK segments for color
    pass_mask  = np.abs(k_arr) <= k_c
    block_mask = ~pass_mask

    k_pass  = np.where(pass_mask,  k_arr, np.nan)
    k_block = np.where(block_mask, k_arr, np.nan)
    p_pass  = np.where(pass_mask,  prob_k, np.nan)
    p_block = np.where(block_mask, prob_k, np.nan)

    line_pass.set_data(k_pass,  p_pass)
    line_block.set_data(k_block, p_block)

    vline_cutoff.set_xdata([k_c, k_c])
    vline_cutoff_n.set_xdata([-k_c, -k_c])
    cutoff_label.set_position((k_c + 0.1, 0))
    cutoff_label.set_text(f'  k_c = {k_c:.2f}\n  fc ≈ {fc_hz:.0f} Hz')

    pk_max = max(np.nanmax(prob_k) * 1.25, 0.01)
    ax2.set_xlim(-10, 10)
    ax2.set_ylim(0, pk_max)

    # Shaded background regions
    for coll in ax2.collections:
        coll.remove()
    ax2.axvspan(-k_c, k_c,   alpha=0.08, color='#00ff88', zorder=0)
    ax2.axvspan(-10,  -k_c,  alpha=0.08, color='red',     zorder=0)
    ax2.axvspan(k_c,   10,   alpha=0.08, color='red',     zorder=0)

    # ── Update ax3: filtered signal ──
    scale = np.max(np.abs(psi)) / (np.max(np.abs(psi_filtered)) + 1e-10)
    line_filtered.set_data(x, psi_filtered * scale)
    line_original.set_data(x, psi)
    ax3.set_xlim(-10, 10)
    ax3.set_ylim(-1.6, 1.6)

    return line_wave, line_prob, line_fft, line_pass, line_block, line_filtered, line_original

ani = FuncAnimation(fig, update, interval=50, blit=False)

# ── Annotation box explaining the physics ──
fig.text(0.01, 0.97,
         "HOW TO READ:\n"
         "① Top: Raw wave packet ψ(x) — a quantum particle's position probability\n"
         "② Middle: Its frequency content (FFT). Green = frequencies that PASS the RC filter. Red = BLOCKED.\n"
         "③ Bottom: The filtered signal — high-frequency noise removed, core signal preserved.\n"
         f"   RC values: R=1kΩ, C=1µF → cutoff fc≈{fc_hz:.0f} Hz  |  Drag k_cutoff slider to change filter threshold.",
         fontsize=7.5, color='#aaaaaa', va='top',
         bbox=dict(boxstyle='round', facecolor='#1a1a1a', edgecolor='#444444', alpha=0.8))

plt.show()
