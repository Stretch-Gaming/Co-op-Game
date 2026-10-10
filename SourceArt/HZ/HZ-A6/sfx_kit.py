"""HZ-A6: shared DSP helpers for make_sounds.py.

Plain numpy/scipy, no audio libraries. Everything that is random takes a numpy Generator,
so each sound is reproducible from its seed. Loops are built "circularly" (FFT filtering,
wrapped event placement, circular reverb), so the last sample flows into the first one
exactly as any sample flows into the next.
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
HERE = Path(__file__).resolve().parent
RAW = HERE / 'raw'


def db(x):
    return 10 ** (x / 20)


def t_axis(n):
    return np.arange(n) / SR


def secs(s):
    return int(round(s * SR))


# ----------------------------------------------------------------------------- raw sources

def load_raw(name, mono=True):
    """Decode raw/<name> (a Kenney OGG) with ffmpeg and resample it to 48 kHz.

    ffmpeg only decodes, at the file's own rate; resampling is scipy's polyphase filter,
    so the result doesn't depend on which resamplers the local ffmpeg was built with.
    Stereo is folded to mono by averaging; the Kenney files are near-mono.
    """
    src = RAW / name
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'decoded.wav'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(src), '-vn',
                        '-c:a', 'pcm_f32le', str(out)], check=True)
        sr, x = wavfile.read(out)
    x = x.astype(np.float64)
    if mono and x.ndim > 1:
        x = x.mean(axis=1)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g, axis=0)
    return x


def repitch(x, ratio):
    """Play x at `ratio` times its speed (0.8 = slower and lower). Polyphase resampling."""
    up, down = 1000, int(round(1000 * ratio))
    g = np.gcd(up, down)
    return signal.resample_poly(x, up // g, down // g)


# ----------------------------------------------------------------------------- noise and filters

def noise(rng, n):
    return rng.standard_normal(n)


def sos(kind, f, order=2):
    return signal.butter(order, f, btype=kind, fs=SR, output='sos')


def lp(x, f, order=2):
    return signal.sosfilt(sos('lowpass', f, order), x)


def hp(x, f, order=2):
    return signal.sosfilt(sos('highpass', f, order), x)


def bp(x, f1, f2, order=2):
    return signal.sosfilt(sos('bandpass', [f1, f2], order), x)


def peak_filter(x, f, q, gain=1.0):
    """Resonant band (2nd-order bandpass, RBJ constant-peak), scaled by gain."""
    b, a = signal.iirpeak(f, q, fs=SR)
    return gain * signal.lfilter(b, a, x)


def svf_bandpass(x, fc, q):
    """Time-varying state-variable bandpass (TPT form). fc may be an array, one value per sample."""
    fc = np.broadcast_to(np.asarray(fc, dtype=np.float64), x.shape)
    g = np.tan(np.pi * np.clip(fc, 10, SR * 0.45) / SR)
    k = 1.0 / q
    s1 = s2 = 0.0
    y = np.empty_like(x)
    for i in range(len(x)):
        gi = g[i]
        hpv = (x[i] - (k + gi) * s1 - s2) / (1 + k * gi + gi * gi)
        bpv = gi * hpv + s1
        s1 = gi * hpv + bpv
        lpv = gi * bpv + s2
        s2 = gi * bpv + lpv
        y[i] = bpv
    return y


# Circular (loop-safe) versions: zero-phase magnitude shaping in the FFT domain.

def fft_shape(x, gain_fn):
    """Multiply x's spectrum by gain_fn(freqs). Circular, so periodic in len(x)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * gain_fn(f), n=len(x))


def band_gain(f, lo=None, hi=None, order=2):
    """Butterworth-like magnitude: highpass at lo and/or lowpass at hi."""
    g = np.ones_like(f)
    if lo:
        r = (np.maximum(f, 1e-6) / lo) ** (2 * order)
        g *= np.sqrt(r / (1 + r))
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    return g


def periodic_smooth(rng, n, cutoff_hz):
    """Smooth random control signal that is exactly periodic in n samples, std 1."""
    x = fft_shape(rng.standard_normal(n), lambda f: np.exp(-0.5 * (f / cutoff_hz) ** 2))
    return x / (x.std() + 1e-12)


def add_wrapped(buf, ev, start):
    """Add ev into buf starting at start, wrapping past the end (for loops). buf may be (n,) or (n, ch)."""
    n = buf.shape[0]
    start %= n
    m = min(len(ev), n)
    first = min(m, n - start)
    buf[start:start + first] += ev[:first]
    if m > first:
        buf[:m - first] += ev[first:m]


def add_at(buf, ev, start):
    """Add ev into buf at start, clipped to buf's length."""
    end = min(len(buf), start + len(ev))
    if end > start:
        buf[start:end] += ev[:end - start]


# ----------------------------------------------------------------------------- envelopes

def env_exp(n, attack, decay):
    t = t_axis(n)
    a = 1 - np.exp(-t / max(attack, 1e-5))
    return a * np.exp(-t / decay)


def bell(n, center, width):
    t = t_axis(n)
    return np.exp(-0.5 * ((t - center) / width) ** 2)


def fade(x, fade_in=0.0005, fade_out=0.03):
    """Raised-cosine fades so a one-shot starts and ends on silence."""
    x = x.copy()
    a, b = secs(fade_in), secs(fade_out)
    if a > 0:
        x[:a] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    if b > 0:
        x[-b:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b))
    return x


def trim_tail(x, thresh_db=-60, pad=0.05):
    """Cut trailing silence below thresh (relative to peak), keeping pad seconds."""
    env = np.abs(x)
    above = np.nonzero(env > np.abs(x).max() * db(thresh_db))[0]
    end = min(len(x), above[-1] + secs(pad)) if len(above) else len(x)
    return x[:end]


# ----------------------------------------------------------------------------- building blocks

def modal(n, freqs, decays, amps, rng=None, detune=0.0):
    """Sum of exponentially decaying sines (a struck object). Starts at phase 0, so no click."""
    t = t_axis(n)
    y = np.zeros(n)
    for f, d, a in zip(freqs, decays, amps):
        if rng is not None and detune:
            f *= 1 + detune * rng.uniform(-1, 1)
        y += a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
    return y


def burst(rng, n, f1, f2, attack, decay):
    """Band-limited noise burst."""
    return bp(noise(rng, n), f1, f2) * env_exp(n, attack, decay)


def cave_ir(rng, rt60, length=None, early=True, bright=4000.0, channels=1):
    """A simple cave impulse response: a few early reflections, then exponentially decaying
    noise whose highs die faster than its lows. Unit energy per channel."""
    length = length or rt60 * 1.1
    n = secs(length)
    t = t_axis(n)
    out = []
    for _ in range(channels):
        lo = lp(noise(rng, n), 900) * np.exp(-6.91 * t / rt60)
        hi = hp(noise(rng, n), 900) * np.exp(-6.91 * t / (rt60 * 0.45))
        ir = lp(lo + 0.6 * hi, bright)
        ir *= 1 - np.exp(-t / 0.004)              # soft onset of the diffuse tail
        if early:
            for _ in range(6):
                d = secs(rng.uniform(0.012, 0.075))
                ir[d] += rng.uniform(0.3, 0.8) * rng.choice([-1, 1]) * np.sqrt(np.sum(ir ** 2) / n) * 40
        out.append(ir / np.sqrt(np.sum(ir ** 2)))
    return out[0] if channels == 1 else np.stack(out, axis=1)


def reverb(x, ir, wet_db, dry=1.0):
    """Linear convolution reverb; output is longer than x by the IR's length."""
    wet = signal.fftconvolve(x, ir) * db(wet_db)
    y = np.zeros(len(wet))
    y[:len(x)] += dry * x
    return y + wet


def reverb_circular(x, ir, wet_db, dry=1.0):
    """Circular convolution reverb for loops: tails past the end wrap to the start."""
    n = len(x)
    h = np.zeros(n)
    h[:len(ir)] = ir
    wet = np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(h), n=n)
    return dry * x + wet * db(wet_db)


def drip(rng, f0, rise, tau, n=None):
    """A water drop "plink": a sine whose pitch rises quickly (the bubble), with a tiny tick."""
    n = n or secs(0.25)
    t = t_axis(n)
    f = f0 * (1 + (rise - 1) * (1 - np.exp(-t / 0.018)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) * env_exp(n, 0.0006, tau)
    tick = hp(noise(rng, n), 2500) * env_exp(n, 0.0002, 0.0012) * 0.35
    return tone + tick


# ----------------------------------------------------------------------------- output

def normalize(x, peak_db=-3.0):
    return x * (db(peak_db) / (np.abs(x).max() + 1e-12))


def write_wav(path, x, seed=0):
    """Write 16-bit PCM with seeded TPDF dither. x is float in [-1, 1], shape (n,) or (n, 2)."""
    rng = np.random.default_rng(seed)
    d = (rng.uniform(-0.5, 0.5, x.shape) + rng.uniform(-0.5, 0.5, x.shape))
    q = np.clip(np.round(x * 32767 + d), -32768, 32767).astype(np.int16)
    wavfile.write(path, SR, q)
