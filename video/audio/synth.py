"""Small synthesiser used by make_music.py: drums, bass, pads, plucks, risers, a reverb, all with numpy."""
import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
rng = np.random.default_rng(11)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(sec):
    return np.arange(int(sec * SR)) / SR


def lp(x, f, order=2):
    return sosfilt(butter(order, min(f, SR / 2 - 200), btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


class Track:
    """A stereo buffer of a fixed length; place() mixes a mono or stereo sound at a time, with gain and pan."""

    def __init__(self, seconds):
        self.n = int(round(seconds * SR))
        self.buf = np.zeros((self.n, 2))

    def place(self, x, t0, gain=1.0, pan=0.0):
        i = int(round(t0 * SR))
        if i >= self.n or gain == 0:
            return
        if x.ndim == 1:
            p = (pan + 1) * np.pi / 4
            x = np.stack([x * np.cos(p), x * np.sin(p)], axis=1)
        j = min(self.n, i + len(x))
        if i < 0:
            x, i = x[-i:], 0
        self.buf[i:j] += x[: j - i] * gain


# ---- drums
def kick(punch=1.0, length=0.38):
    t = tt(length)
    f = 48 + 110 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 400) * 0.25 * punch
    return np.tanh((body + click) * 1.6)


def soft_kick():
    t = tt(0.45)
    f = 44 + 60 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)


def clap():
    t = tt(0.25)
    x = np.zeros(len(t))
    for d in (0, 0.011, 0.022):
        i = int(d * SR)
        x[i:] += rng.standard_normal(len(t) - i) * np.exp(-t[: len(t) - i] * 60)
    x += rng.standard_normal(len(t)) * np.exp(-t * 18) * 0.35
    return bp(x, 900, 3200)


def hat(open_=False):
    t = tt(0.28 if open_ else 0.05)
    return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * (14 if open_ else 110))


def rim():
    t = tt(0.06)
    return bp(rng.standard_normal(len(t)), 1500, 4000) * np.exp(-t * 90) + np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 120) * 0.4


def crash(length=1.6):
    t = tt(length)
    return hp(rng.standard_normal(len(t)), 4500) * np.exp(-t * 2.2)


def snare_roll(length, start_rate=4, end_rate=16):
    """Snare hits speeding up (hits per second), for build-ups."""
    out = np.zeros(int(length * SR))
    t, hit = 0.0, hp(clap(), 300) * 0.7
    while t < length:
        k = t / length
        i = int(t * SR)
        seg = hit[: len(out) - i] * (0.35 + 0.65 * k)
        out[i:i + len(seg)] += seg
        t += 1 / (start_rate + (end_rate - start_rate) * k ** 2)
    return out


def riser(length, f0=200, f1=4000):
    t = tt(length)
    k = t / length
    noise = rng.standard_normal(len(t))
    out = np.zeros(len(t))
    block = 2048
    for i in range(0, len(t), block):
        fc = f0 * (f1 / f0) ** k[i]
        seg = noise[max(0, i - 4096):i + block]
        out[i:i + block] = bp(seg, max(60, fc * 0.6), min(SR / 2 - 200, fc * 1.4))[-min(block, len(t) - i):]
    tone = np.sin(2 * np.pi * np.cumsum(f0 / 2 * (f1 / f0) ** (k * 0.5)) / SR) * 0.25
    return (out + tone) * k ** 2


# ---- tonal
def saw(freq, length, detune=0.0):
    t = tt(length)
    ph = (freq * (1 + detune) * t + rng.uniform()) % 1.0
    return 2 * ph - 1


def adsr(n, a, d, s, r):
    e = np.full(n, float(s))
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e[:a] = np.linspace(0, 1, a)
    e[a:a + d] = np.linspace(1, s, len(e[a:a + d]))
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def pad(notes, length, cutoff=1800, attack=0.4, release=0.6, voices=(-0.006, 0.0, 0.006)):
    """A soft chord: detuned saws per note, low-passed, slow attack. Returns stereo (spread detunes)."""
    n = int(length * SR)
    left, right = np.zeros(n), np.zeros(n)
    for m in notes:
        for j, d in enumerate(voices):
            s = saw(hz(m), length, d)
            if j % 2 == 0:
                left += s
            else:
                right += s
            if j == 1:
                left += s * 0.5
                right += s * 0.5
    e = adsr(n, attack, 0.2, 1.0, release)
    out = np.stack([lp(left, cutoff), lp(right, cutoff)], axis=1) * e[:, None]
    return out / (len(notes) * len(voices))


def pluck(freq, length=0.3, cutoff=2600, decay=9.0):
    t = tt(length)
    s = saw(freq, length) * 0.6 + np.sin(2 * np.pi * freq * t) * 0.4
    return lp(s, cutoff) * np.exp(-t * decay) * adsr(len(t), 0.003, 0.02, 1, 0.02)


def bell(freq, length=1.6):
    t = tt(length)
    x = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t * dcy) for r, a, dcy in [(1, 1, 2.2), (2.01, .45, 3.5), (3.02, .25, 5), (4.2, .12, 7)])
    return x * adsr(len(t), 0.004, 0.05, 1, 0.05)


def sub(freq, length, attack=0.05, release=0.2):
    t = tt(length)
    return np.sin(2 * np.pi * freq * t) * adsr(len(t), attack, 0.05, 1, release)


def reverb(x, seconds=1.8, mix=0.25, damp=3000):
    """Stereo reverb: convolution with decaying, low-passed noise (different noise per side)."""
    t = tt(seconds)
    out = np.zeros_like(x)
    for ch in range(2):
        ir = lp(rng.standard_normal(len(t)), damp) * np.exp(-t * (6.9 / seconds))
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return x * (1 - mix) + out * mix


def to_rms(x, db):
    """Scale so the loud parts sit at `db` dBFS RMS (measured on the louder half, so silences do not count)."""
    frames = x.reshape(-1, 2)
    win = SR // 2
    r = [np.sqrt(np.mean(frames[i:i + win] ** 2)) for i in range(0, len(frames) - win, win)]
    loud = np.percentile(r, 75)
    return x * (10 ** (db / 20) / (loud + 1e-12))
