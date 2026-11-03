"""Synthesises the trailer's sound effects (nothing downloaded) into public/sfx/*.wav, 48 kHz stereo.
Run from video/: python audio/make_sfx.py"""
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000
OUT = Path(__file__).resolve().parent.parent / "public" / "sfx"
rng = np.random.default_rng(7)


def t(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, attack, release, curve=3.0):
    """Attack then exponential-ish release, n samples."""
    a = max(1, int(attack * SR))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    r = np.linspace(1, 0, n - a) ** curve
    e[a:] = r
    return e


def band(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def sweep_noise(sec, f0, f1, q=0.6):
    """Noise through a band-pass whose centre moves from f0 to f1 (processed in short blocks)."""
    n = int(sec * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    block = 512
    for i in range(0, n, block):
        k = i / n
        fc = f0 * (f1 / f0) ** k
        lo, hi = max(40, fc * (1 - q)), min(SR / 2 - 100, fc * (1 + q))
        seg = noise[max(0, i - 2048):i + block]
        out[i:i + block] = band(seg, lo, hi)[-min(block, n - i):]
    return out


def stereo(x, pan=0.0):
    """pan -1 (left) .. 1 (right), constant power; pan can be an array."""
    p = (np.asarray(pan) + 1) * np.pi / 4
    return np.stack([x * np.cos(p), x * np.sin(p)], axis=1)


def save(name, x, peak_db):
    x = x / (np.max(np.abs(x)) + 1e-12) * 10 ** (peak_db / 20)
    if x.ndim == 1:
        x = stereo(x)
    OUT.mkdir(parents=True, exist_ok=True)
    wavfile.write(OUT / f"{name}.wav", SR, (x * 32767).astype(np.int16))
    print(f"{name}.wav  {len(x) / SR:.2f} s  peak {peak_db} dBFS")


# The set is deliberately smooth: no sharp noise attacks, no bright clicks, everything low-passed and quiet
# (peaks -26 to -15 dBFS), so the effects support the music instead of sitting on top of it.

# whoosh: scene transitions and big slides. A soft, airy breath: dark noise rising then falling, slow fade in and out.
n = int(0.7 * SR)
up = lp(sweep_noise(0.7, 220, 1800, 0.45), 2600)
e = np.sin(np.linspace(0, np.pi, n)) ** 2.2
save("whoosh", stereo(up * e, np.linspace(-0.5, 0.5, n)), -19)

# soft swoosh: lines and arrows drawing. Even softer and shorter, centred.
n = int(0.45 * SR)
sw = lp(sweep_noise(0.45, 300, 1400, 0.4), 1800)
save("swoosh", sw * np.sin(np.linspace(0, np.pi, n)) ** 2.5, -23)

# soft click: cursor clicks. A muted "tok": a low sine with a rounded attack, no noise.
tt = t(0.06)
click = np.sin(2 * np.pi * 900 * tt) * np.exp(-tt * 90) * np.minimum(tt / 0.002, 1)
click += np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 160) * 0.2
save("click", click, -22)

# typing ticks: 6 s of very soft, muffled key taps at an irregular rhythm (trimmed to each typing span)
total = np.zeros(int(6 * SR))
pos = 0.02
while pos < 5.95:
    k = t(0.03)
    f = rng.uniform(1300, 1900)
    tick = np.sin(2 * np.pi * f * k) * np.exp(-k * 260) * np.minimum(k / 0.0015, 1)
    tick += lp(rng.standard_normal(len(k)), 2500) * np.exp(-k * 300) * 0.15
    i = int(pos * SR)
    total[i:i + len(k)] += tick * rng.uniform(0.5, 1.0)
    pos += rng.uniform(0.05, 0.09)
save("typing", total, -27)

# pop: cards, messages, icons appearing. A round, low "bloop": sine gliding 560 -> 380 Hz with a gentle attack.
tt = t(0.16)
freq = 380 + 180 * np.exp(-tt * 30)
pop = np.sin(2 * np.pi * np.cumsum(freq) / SR) * env(len(tt), 0.006, 0.154, 2.0)
save("pop", lp(pop, 2000), -21)

# shimmer / rise: logo reveal and the Meta diagram. A warm swell: soft sine chord fading in, no bright partials.
tt = t(2.2)
sh = np.zeros(len(tt))
for f0, a in [(440, 1), (659.3, .6), (880, .45), (1318.5, .2)]:
    for det in (-0.003, 0.003):
        sh += a * np.sin(2 * np.pi * f0 * (1 + det) * tt)
sh *= np.minimum(tt / 1.1, 1) ** 2 * np.exp(-np.maximum(tt - 1.1, 0) * 2.6)
echo = np.zeros_like(sh)
for d, g in [(0.13, .35), (0.27, .2)]:
    i = int(d * SR)
    echo[i:] += sh[:-i] * g
save("shimmer", stereo(lp(sh + echo, 3000), 0.2 * np.sin(2 * np.pi * 0.5 * tt)), -20)

# impact / bass hit: key words and the outro. A deep, round boom: sub sine with a slow pitch drop, no click.
tt = t(1.8)
f = 40 + 35 * np.exp(-tt * 10)
boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.4) * np.minimum(tt / 0.008, 1)
tail = lp(rng.standard_normal(len(tt)), 250) * np.exp(-tt * 4) * 0.08
save("impact", lp(np.tanh((boom + tail) * 1.2), 500), -15)
