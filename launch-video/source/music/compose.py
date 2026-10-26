"""compose.py: the launch video's soundtrack, an original big-beat cue.

Everything is synthesised here from scratch with numpy (no samples, no
borrowed melody), so the track is ours to publish. Deterministic: the same
seed always renders the same file.

    python3 compose.py out.wav
    then set it to -14 LUFS (loudnorm, plus a trim if needed) before laying it under
    the picture; the README has the exact commands. soundtrack.m4a is the result.

120 BPM, E minor, bars every 2 s from t = 1.2 s so the downbeats land on the
video's cuts (3.2, 13.2, 18.2, 23.2 s) and the drop lands on the cell burst
(11.2 s). 30.0 s long, stereo, 44.1 kHz.
"""
import sys, wave
import numpy as np

SR = 44100
LEN = 30.0
N = int(SR * LEN)
BPM = 120.0
BEAT = 60.0 / BPM          # 0.5 s
STEP = BEAT / 4            # a 16th
T0 = 1.2                   # first downbeat
rng = np.random.default_rng(7)

L = np.zeros(N); R = np.zeros(N)          # master
drums = np.zeros(N); bass = np.zeros(N); synth = np.zeros((2, N)); fx = np.zeros((2, N))
duck = np.ones(N)                          # sidechain gain, driven by the kicks

def bar(b, step=0.0):
    """time of bar b (0 = the downbeat at T0) plus a number of 16th steps"""
    return T0 + b * 4 * BEAT + step * STEP

def put(buf, t, sig, gain=1.0):
    i, n = int(round(t * SR)), sig.shape[-1]
    if i >= buf.shape[-1] or i + n <= 0: return
    a, b = max(i, 0), min(i + n, buf.shape[-1])
    buf[..., a:b] += gain * sig[..., a - i:b - i]

def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo: m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x))

def tt(sec): return np.arange(int(sec * SR)) / SR

# ---------------- drum voices ----------------
def kick():
    t = tt(0.5)
    f = 46 + 115 * np.exp(-t * 30)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    click = fft_filter(rng.standard_normal(len(t)), lo=2000) * np.exp(-t * 400) * 0.35
    return np.tanh(1.8 * (s + click)) * 0.95

def snare(bright=1.0):
    t = tt(0.32)
    body = np.sin(2 * np.pi * 188 * t) * np.exp(-t * 24) * 0.55 + np.sin(2 * np.pi * 332 * t) * np.exp(-t * 32) * 0.25
    nz = fft_filter(rng.standard_normal(len(t)), lo=1400, hi=9000 * bright) * np.exp(-t * 15) * 0.9
    return np.tanh(1.4 * (body + nz))

def hat(open_=False):
    t = tt(0.4 if open_ else 0.07)
    nz = fft_filter(rng.standard_normal(len(t)), lo=7500)
    return nz * np.exp(-t * (11 if open_ else 70)) * 0.32

def crash():
    t = tt(2.6)
    a = fft_filter(rng.standard_normal(len(t)), lo=3500) * np.exp(-t * 1.9)
    b = fft_filter(rng.standard_normal(len(t)), lo=3500) * np.exp(-t * 1.9)
    return np.vstack([a, b]) * 0.28

K, S, Sg, H, HO, C = kick(), snare(), snare(0.6), hat(), hat(True), crash()

def hit_kick(t, g=1.0):
    put(drums, t, K, g)
    i = int(t * SR); n = int(0.28 * SR)
    if 0 <= i < N:
        e = 1 - 0.4 * np.exp(-np.arange(min(n, N - i)) / SR / 0.09)
        duck[i:i + len(e)] = np.minimum(duck[i:i + len(e)], e)

# a funky break, 16 steps: (kick velocities), (snare velocities), (closed hat velocities)
BREAK_K = {0: 1.0, 6: 0.8, 10: 0.95}
BREAK_S = {4: 1.0, 12: 1.0, 7: 0.28, 9: 0.22, 15: 0.32}
def break_bar(b, hats16=False, kicks=True, snares=True, open14=True, g=1.0):
    for s, v in BREAK_K.items():
        if kicks: hit_kick(bar(b, s), v * g)
    for s, v in BREAK_S.items():
        if snares: put(drums, bar(b, s), S if v > 0.5 else Sg, v * g)
    for s in range(16):
        if s % 2 == 0 or hats16:
            swing = 0.012 if s % 2 else 0.0
            put(drums, bar(b, s) + swing, H, (0.9 if s % 4 == 2 else 0.55 if s % 2 == 0 else 0.3) * g)
    if open14: put(drums, bar(b, 14), HO, 0.6 * g)

def roll(b0, b1, g0=0.25, g1=1.0):
    """a snare roll that speeds up: 8ths, then 16ths, then 32nds, getting louder"""
    t, end = bar(b0), bar(b1)
    while t < end - 1e-6:
        k = (t - bar(b0)) / (end - bar(b0))
        put(drums, t, S, g0 + (g1 - g0) * k)
        t += STEP * (2 if k < 0.4 else 1 if k < 0.75 else 0.5)

# ---------------- acid bass: a saw through a resonant state-variable filter ----------------
E2 = 82.41
RIFF = [0, 0, 12, 0, 3, 0, 10, 0, 0, 7, 0, 12, 5, 3, 0, -2]          # semitones over E2, one bar of 16ths
ACCENT = {0, 2, 6, 11, 13}
SLIDE = {2, 10}

def acid(b_from, b_to, cut_from, cut_to, oct_=0, reso=0.82, g=1.0):
    n0, n1 = int(bar(b_from) * SR), int(bar(b_to) * SR)
    n1 = min(n1, N)
    freq = np.zeros(n1 - n0); amp = np.zeros(n1 - n0); cenv = np.zeros(n1 - n0)
    nsteps = int(round((bar(b_to) - bar(b_from)) / STEP))
    prev = None
    for k in range(nsteps):
        s = k % 16
        a = int(round(k * STEP * SR)); b = min(int(round((k + 1) * STEP * SR)), len(freq))
        if a >= len(freq): break
        f = E2 * 2 ** ((RIFF[s] + 12 * oct_) / 12)
        seg = np.arange(b - a) / SR
        if s in SLIDE and prev: freq[a:b] = prev * (f / prev) ** np.minimum(seg / 0.05, 1)
        else: freq[a:b] = f
        gate = int((b - a) * (1.0 if s in SLIDE else 0.72))
        amp[a:a + gate] = 1.0 if s in ACCENT else 0.7
        cenv[a:b] = np.exp(-seg * (9 if s in ACCENT else 14)) * (1.6 if s in ACCENT else 1.0)
        prev = f
    ph = np.cumsum(freq) / SR
    saw = 2 * (ph % 1.0) - 1
    # smooth the gate so notes don't click
    k = int(0.003 * SR); amp = np.convolve(amp, np.ones(k) / k, mode='same')
    base = np.linspace(cut_from, cut_to, len(saw))
    cutoff = np.clip(base * (1 + 2.5 * cenv), 60, 9000)
    lp = bp = 0.0; out = np.zeros(len(saw)); q = 1 - reso
    fcoef = 2 * np.sin(np.pi * cutoff / (SR * 2))
    for i in range(len(saw)):                      # Chamberlin SVF, oversampled x2
        x = saw[i]
        for _ in (0, 1):
            hp = x - lp - q * bp
            bp += fcoef[i] * hp
            lp += fcoef[i] * bp
        out[i] = lp
    out = np.tanh(2.2 * out) * amp
    bass[n0:n1] += g * out[:n1 - n0]

# ---------------- chord stabs: detuned, band-limited saws ----------------
def stab(t, chord=(52, 55, 59, 64), dur=0.55, bright=1.0, g=1.0):
    tt_ = tt(dur + 0.6)
    env = np.minimum(tt_ / 0.004, 1) * np.exp(-tt_ * 5.5 / dur)
    out = np.zeros((2, len(tt_)))
    for m in chord:
        f0 = 440 * 2 ** ((m - 69) / 12)
        for c, det in ((0, -0.07), (1, 0.07), (0, 0.0), (1, 0.0)):
            f = f0 * 2 ** (det / 12)
            v = np.zeros(len(tt_))
            for h in range(1, 28):
                if f * h > 15000: break
                v += np.sin(2 * np.pi * f * h * tt_ + h) / h * np.exp(-h * 0.11 / bright) * np.exp(-tt_ * h * 0.9)
            out[c] += v
    out *= env / len(chord) * 0.55
    put(synth, t, out, g)

# a held, detuned chord under the drop: the room filling up
def pad(t_from, t_to, chord=(40, 52, 55, 59), g=1.0):
    t = tt(t_to - t_from)
    env = np.minimum(t / 0.25, 1) * np.minimum((t[-1] - t) / 0.3, 1)
    out = np.zeros((2, len(t)))
    for m in chord:
        f0 = 440 * 2 ** ((m - 69) / 12)
        for c, det in ((0, -0.11), (1, 0.11), (0, 0.04), (1, -0.04)):
            f = f0 * 2 ** (det / 12); v = np.zeros(len(t))
            for h in range(1, 16):
                if f * h > 6000: break
                v += np.sin(2 * np.pi * f * h * t + h * 1.7) / h * np.exp(-h * 0.25)
            out[c] += v
    put(synth, t_from, out * env / len(chord) * 0.22, g)

# ---------------- risers and textures ----------------
def riser(t_from, t_to, g=1.0):
    n = int((t_to - t_from) * SR); x = rng.standard_normal(n)
    k = np.linspace(0, 1, n)
    cutoff = 300 * (9000 / 300) ** k
    lp = bp = 0.0; out = np.zeros(n); fco = 2 * np.sin(np.pi * cutoff / (SR * 2))
    for i in range(n):
        hp = x[i] - lp - 0.35 * bp; bp += fco[i] * hp; lp += fco[i] * bp; out[i] = bp
    out *= k ** 2 * 0.35
    pitch = 110 * (880 / 110) ** k
    tone = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * 0.12 * k ** 1.5
    put(fx, t_from, np.vstack([out + tone, np.roll(out, 90) + tone]), g)

def crackle(t_from, t_to, g=0.06):
    n = int((t_to - t_from) * SR); x = np.zeros(n)
    idx = rng.integers(0, n, int((t_to - t_from) * 60)); x[idx] = rng.standard_normal(len(idx))
    x = fft_filter(x, lo=900, hi=7000)
    put(fx, t_from, np.vstack([x, np.roll(x, 37)]), g)

def swell(t_from, t_to, g=0.5):
    n = int((t_to - t_from) * SR); k = np.linspace(0, 1, n)
    nz = fft_filter(rng.standard_normal(n), lo=2500) * k ** 3
    put(fx, t_from, np.vstack([nz, np.roll(nz, 50)]), g * 0.3)

# ================= the arrangement =================
# 0 – 1.2  intro: crackle, a cymbal swell into the first downbeat
crackle(0, 3.2); swell(0.15, T0, 0.8)
# bar 0 (1.2 – 3.2), the logo: a first stab, a thin filtered break
stab(bar(0), bright=0.45, g=0.8); put(fx, bar(0), C, 0.35)
break_bar(0, kicks=False, g=0.45)
# bars 1–2 (3.2 – 7.2), the headline: the break comes in, sub hits on the one
put(fx, bar(1), C, 0.6); stab(bar(1), g=0.75)
for b in (1, 2):
    break_bar(b, g=0.6)
    put(bass, bar(b), np.sin(2 * np.pi * 41.2 * tt(0.7)) * np.exp(-tt(0.7) * 5), 0.45)
# bar 3 (7.2 – 9.2): the acid line enters, filter closed and opening
break_bar(3, g=0.7)
acid(3, 4, 220, 700, g=0.55)
# bar 4 (9.2 – 11.2): the build: roll, riser, acid opening, kick out for the last beat
acid(4, 5, 700, 2200, g=0.7)
for s in (0, 6): hit_kick(bar(4, s), 0.7)
roll(4, 4.875, 0.12, 0.55); riser(bar(4) - 0.6, bar(5) - 0.12, 0.6)
# 11.2 THE DROP, as the cell bursts
put(fx, bar(5), C, 1.0); stab(bar(5), dur=0.9, bright=1.4, g=1.5)
boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-tt(1.2) * 6)) / SR) * np.exp(-tt(1.2) * 2.6)
put(bass, bar(5), boom, 0.9)
for b in range(5, 11):                                   # 11.2 – 23.2
    break_bar(b, hats16=True, g=1.0)
    acid(b, b + 1, 900 if b < 8 else 1300, 1500 if b < 8 else 2400, oct_=1 if b in (9, 10) else 0)
for b, s in ((6, 0), (7, 0), (7, 8), (8, 0), (9, 0)):    # stabs on the cuts (13.2, 18.2) and bar heads
    stab(bar(b, s), g=0.9)
pad(bar(5), bar(11), g=1.0)                             # 11.2 – 23.2: held under the whole drop
roll(10.5, 11, 0.3, 0.9)                                # fill into the call to action
# 23.2 – 27.2: the call to action, stripped back
put(fx, bar(11), C, 0.8); stab(bar(11), dur=0.8, g=1.0)
for b in (11, 12):
    break_bar(b, snares=(b == 12), g=0.8)
    acid(b, b + 1, 600, 900, g=0.8)
# 27.2 – 29.2: one last lift, then the final hit and its tail
break_bar(13, hats16=True, g=0.95); acid(13, 14, 900, 2600)
riser(bar(13), bar(14) - 0.05, 0.7)
put(fx, bar(14), C, 1.0); stab(bar(14), dur=1.0, bright=1.3, g=1.5); hit_kick(bar(14), 1.0)
put(bass, bar(14), boom, 0.8)

# ================= mix =================
drums_bus = np.tanh(drums) * 0.75
bass_bus = bass * duck * 0.42
synth_bus = synth * duck * 1.0
fx_bus = fx * 0.8
L = drums_bus + bass_bus + synth_bus[0] + fx_bus[0]
R = drums_bus + bass_bus + synth_bus[1] + fx_bus[1]
mix = np.vstack([L, R])
# a breath of near silence just before the drop
gap = np.ones(N); a, b = int((bar(5) - 0.11) * SR), int(bar(5) * SR)
gap[a:b] = 0.06; gap[a - 400:a] = np.linspace(1, 0.06, 400)
mix *= gap
fade = np.ones(N); nf = int(0.35 * SR); fade[-nf:] = np.linspace(1, 0, nf) ** 2
fi = int(0.05 * SR); fade[:fi] *= np.linspace(0, 1, fi)
mix *= fade
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.4) / np.tanh(1.4)   # gentle peak rounding only
mix *= 0.5                                              # headroom; final loudness is set by loudnorm

out = sys.argv[1] if len(sys.argv) > 1 else 'soundtrack.wav'
pcm = (np.clip(mix.T, -1, 1) * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', out, f'{N / SR:.1f}s')
