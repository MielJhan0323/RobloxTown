#!/usr/bin/env python3
"""Synthesize original (hence royalty-free) stand-in music, ambience and SFX
into output/stock/ so drafts never render silent. Real files in audio/music and
audio/sfx always take priority; plan.py only falls back to output/stock/.

  python tools/stock_audio.py

music/soft_piano_stock.wav  ~3 min gentle piano + string pad (C-G-Am-F)
sfx/amb_waves, amb_wind, amb_town, magic_shimmer, door_knock, click
"""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import OUTPUT, log  # noqa: E402

SR = 48000
STOCK = OUTPUT / "stock"
rng = np.random.default_rng(11)


def write(path: Path, x: np.ndarray):
    path.parent.mkdir(parents=True, exist_ok=True)
    if x.ndim == 1:
        x = np.stack([x, x], -1)
    x = x / (np.abs(x).max() + 1e-9) * 0.85
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def piano_note(f, dur, vel=1.0):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 2.2) * (1 - np.exp(-t * 400))
    tone = sum(a * np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k * k)) for k, a in ((1, 1), (2, 0.45), (3, 0.18), (4, 0.08), (5, 0.04)))
    return tone * env * vel


def reverb(x, mix=0.35):
    out = x.copy()
    for d, g in ((0.031, 0.5), (0.047, 0.45), (0.071, 0.4), (0.113, 0.33), (0.167, 0.27), (0.241, 0.2), (0.353, 0.14)):
        k = int(d * SR)
        y = np.zeros_like(x)
        y[k:] = x[:-k] * g
        out += y * mix * 2
    return out


def smooth_noise(n, cutoff_hz):
    """Cheap low-passed noise via FFT shaping."""
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec *= 1 / (1 + (f / cutoff_hz) ** 2)
    return np.fft.irfft(spec, n)


def music(total=180.0):
    bpm = 72
    beat = 60 / bpm
    chords = [[48, 55, 60, 64, 67], [43, 50, 59, 62, 67], [45, 52, 57, 60, 64], [41, 48, 57, 60, 65]]  # C G Am F
    mel = [76, 74, 72, 74, 79, 77, 76, 74, 72, 71, 72, 76, 77, 76, 74, 72]
    n = int(total * SR)
    L, R = np.zeros(n + SR * 4), np.zeros(n + SR * 4)
    bar = 4 * beat
    t0, b = 0.0, 0
    while t0 < total:
        ch = chords[b % 4]
        # pad
        tt = np.arange(int(bar * SR)) / SR
        pad = sum(np.sin(2 * np.pi * midi(m) * tt) for m in ch[1:4]) * 0.05
        pad *= np.minimum(1, tt / 1.2) * np.minimum(1, (bar - tt) / 0.8)
        i = int(t0 * SR)
        L[i:i + len(pad)] += pad
        R[i:i + len(pad)] += pad
        # bass + arpeggio
        for k, m in enumerate([ch[0], ch[2], ch[3], ch[4], ch[3], ch[2], ch[1], ch[2]]):
            nt = piano_note(midi(m + (0 if k else 0)), 2.5, 0.55 if k else 0.8)
            j = int((t0 + k * beat / 2) * SR)
            pan = 0.35 + 0.3 * (k % 2)
            L[j:j + len(nt)] += nt * (1 - pan)
            R[j:j + len(nt)] += nt * pan
        # sparse melody from bar 4 on
        if b >= 4 and b % 2 == 0:
            for k in range(2):
                m = mel[(b + k) % len(mel)]
                nt = piano_note(midi(m), 3.0, 0.5)
                j = int((t0 + k * 2 * beat) * SR)
                L[j:j + len(nt)] += nt * 0.5
                R[j:j + len(nt)] += nt * 0.5
        t0 += bar
        b += 1
    x = np.stack([reverb(L[:n]), reverb(R[:n])], -1)
    fade = np.minimum(1, np.arange(n) / (2 * SR))[:, None]
    return x * fade


def waves(d=60.0):
    n = int(d * SR)
    t = np.arange(n) / SR
    body = smooth_noise(n, 500)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 7.5) ** 2
    hiss = smooth_noise(n, 3000) * 0.3 * np.maximum(0, np.sin(2 * np.pi * t / 7.5 - 0.6)) ** 4
    return np.stack([body * swell + hiss, np.roll(body, 900) * swell + hiss], -1)


def wind(d=60.0):
    n = int(d * SR)
    t = np.arange(n) / SR
    w = smooth_noise(n, 350) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 11 + np.sin(t / 3)))
    return w


def town(d=60.0):
    n = int(d * SR)
    x = smooth_noise(n, 900) * 0.6
    for _ in range(int(d / 2)):  # distant soft chatter-ish bumps
        j = rng.integers(0, n - SR)
        L = int(rng.uniform(0.1, 0.3) * SR)
        f = rng.uniform(180, 320)
        tt = np.arange(L) / SR
        x[j:j + L] += 0.15 * np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / tt[-1])
    return x


def shimmer():
    out = np.zeros(int(2.0 * SR))
    for k, m in enumerate([84, 88, 91, 96, 100, 103]):
        t = np.arange(int(1.4 * SR)) / SR
        nt = np.sin(2 * np.pi * midi(m) * t) * np.exp(-t * 3.5) * (1 - np.exp(-t * 200))
        j = int(k * 0.06 * SR)
        out[j:j + len(nt)] += nt * 0.5
    return reverb(out, 0.5)


def knock():
    out = np.zeros(int(1.0 * SR))
    for j0 in (0.0, 0.22, 0.42):
        t = np.arange(int(0.18 * SR)) / SR
        th = (np.sin(2 * np.pi * 110 * t) + 0.5 * smooth_noise(len(t), 800)) * np.exp(-t * 35)
        j = int(j0 * SR)
        out[j:j + len(th)] += th
    return reverb(out, 0.2)


def click():
    t = np.arange(int(0.08 * SR)) / SR
    return smooth_noise(len(t), 4000) * np.exp(-t * 120)


def env_exp(n, k):
    return np.exp(-np.arange(n) / SR * k)


def boom():
    """Deep comedic boom (original 'vine boom'-style hit): pitch-dropping sub + click + saturated tail."""
    d = 1.6
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 95 * np.exp(-t * 2.2) + 38
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env_exp(n, 2.4)
    body += 0.5 * np.sin(2 * ph) * env_exp(n, 5)
    click = smooth_noise(n, 2500) * env_exp(n, 60) * 0.6
    x = np.tanh(2.6 * (body + click))
    return reverb(x, 0.25)


def whoosh(d=0.7, up=True):
    n = int(d * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    spec = np.fft.rfft(noise)
    out = np.zeros(n)
    # sweep a band through the noise in 8 slices for a moving whoosh
    for i in range(8):
        a, b = i * n // 8, (i + 1) * n // 8
        fc = (300 + 3500 * (i / 7)) if up else (3800 - 3500 * (i / 7))
        seg = np.fft.rfft(noise[a:b])
        fr = np.fft.rfftfreq(b - a, 1 / SR)
        seg *= np.exp(-((fr - fc) / (fc * 0.6)) ** 2)
        out[a:b] = np.fft.irfft(seg, b - a)
    shape = np.sin(np.pi * t / d) ** 2
    out = np.convolve(out * shape, np.ones(64) / 64, "same")
    return np.stack([out * (1 - t / d * 0.6), out * (0.4 + t / d * 0.6)], -1)


def impact():
    """Cinematic reveal hit: low thud + noise burst + long tail."""
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    thud = np.sin(2 * np.pi * (55 * np.exp(-t * 1.5) + 30) * t) * env_exp(n, 1.8)
    burst = smooth_noise(n, 1200) * env_exp(n, 9) * 0.8
    return reverb(np.tanh(1.8 * (thud + burst)), 0.45)


def heartbeat(beats=4, bpm=62):
    n = int((beats * 60 / bpm + 0.6) * SR)
    out = np.zeros(n)
    for b in range(beats):
        for off, amp in ((0.0, 1.0), (0.24, 0.7)):
            j = int((b * 60 / bpm + off) * SR)
            m = int(0.18 * SR)
            t = np.arange(m) / SR
            hit = np.sin(2 * np.pi * (60 * np.exp(-t * 8) + 35) * t) * np.exp(-t * 22) * amp
            out[j:j + m] += hit[: max(0, min(m, n - j))]
    return np.tanh(1.5 * out)


def beeps(k=3, gap=0.9):
    n = int((k * gap + 0.3) * SR)
    out = np.zeros(n)
    for i in range(k):
        j = int(i * gap * SR)
        m = int(0.14 * SR)
        t = np.arange(m) / SR
        out[j:j + m] += np.sin(2 * np.pi * 1046 * t) * np.minimum(1, (m - np.arange(m)) / (0.02 * SR)) * np.minimum(1, np.arange(m) / (0.004 * SR))
    return reverb(out * 0.6, 0.2)


def pop():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 * np.exp(-t * 30) + 300) * t) * env_exp(n, 25)


def ticks(k=10, gap=0.11):
    n = int((k * gap + 0.1) * SR)
    out = np.zeros(n)
    for i in range(k):
        j = int(i * gap * SR)
        m = int(0.03 * SR)
        out[j:j + m] += smooth_noise(m, 5000) * env_exp(m, 200) * (0.6 + 0.4 * (i % 2))
    return out


def riser(d=1.4):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 200 + 1400 * (t / d) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    hiss = smooth_noise(n, 4000) * 0.5
    return (tone + hiss) * (t / d) ** 2


def main():
    write(STOCK / "music" / "soft_piano_stock.wav", music())
    write(STOCK / "sfx" / "amb_waves_stock.wav", waves())
    write(STOCK / "sfx" / "amb_wind_stock.wav", wind())
    write(STOCK / "sfx" / "amb_town_stock.wav", town())
    write(STOCK / "sfx" / "magic_shimmer_stock.wav", shimmer())
    write(STOCK / "sfx" / "door_knock_stock.wav", knock())
    write(STOCK / "sfx" / "click_stock.wav", click())
    write(STOCK / "sfx" / "boom_stock.wav", boom())
    write(STOCK / "sfx" / "whoosh_stock.wav", whoosh(0.7, True))
    write(STOCK / "sfx" / "whoosh_down_stock.wav", whoosh(0.8, False))
    write(STOCK / "sfx" / "impact_stock.wav", impact())
    write(STOCK / "sfx" / "heartbeat_stock.wav", heartbeat())
    write(STOCK / "sfx" / "monitor_beep_stock.wav", beeps())
    write(STOCK / "sfx" / "pop_stock.wav", pop())
    write(STOCK / "sfx" / "ticks_stock.wav", ticks())
    write(STOCK / "sfx" / "riser_stock.wav", riser())
    log(f"stock audio -> {STOCK}")


if __name__ == "__main__":
    main()
