#!/usr/bin/env python3
"""Stand-in narration with a free local neural voice (Piper), for drafts when
ElevenLabs isn't available. Writes output/stock/voice/<slug>.wav; a real voice
in audio/voice/<slug>.mp3 always takes priority.

  python tools/tts_local.py <slug> [--voice ryan|lessac] [--speed 0.92] [--pause 0.45] [--pitch 3]

Setup: pip install piper-tts  (voice models download from Hugging Face on first use)
"""
from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUTPUT, log, parse_script  # noqa: E402

VOICES = {"ryan": ("ryan", "high"), "lessac": ("lessac", "high"), "amy": ("amy", "medium")}


def model_path(name: str) -> Path:
    v, q = VOICES[name]
    rel = f"en/en_US/{v}/{q}/en_US-{v}-{q}"
    d = OUTPUT / "stock" / "piper"
    p = d / f"{rel}.onnx"
    if not p.exists():
        from huggingface_hub import hf_hub_download
        for ext in (".onnx", ".onnx.json"):
            hf_hub_download("rhasspy/piper-voices", rel + ext, local_dir=str(d))
    return p


def tts_text(text: str) -> str:
    """Piper mangles one-word sentences ("People.", "Home."): fold them into the
    previous sentence with a comma. Captions/script are unaffected."""
    import re
    sents = re.findall(r'[^.!?]+[.!?]+["\u201d]?', text) or [text]
    out = []
    for snt in (x.strip() for x in sents):
        if out and len(re.findall(r"[A-Za-z']+", snt)) <= 1:
            out[-1] = out[-1].rstrip('.!?"\u201d ') + ", " + snt.lstrip('"\u201c')
        else:
            out.append(snt)
    return " ".join(out)


def _narration_paragraphs(slug: str) -> list[str]:
    """Paragraphs from the script's '## Narration' section (falls back to the shot text)."""
    import re
    from common import SCRIPTS
    md = (SCRIPTS / f"{slug}.md").read_text()
    m = re.search(r"^## Narration\s*\n(.*?)(?=^## )", md, re.S | re.M)
    if m:
        paras = [" ".join(p.split()) for p in m.group(1).strip().split("\n\n") if p.strip()]
        if paras:
            return paras
    return [" ".join(s["text"] for s in parse_script(slug)["shots"])]


def _sentences(par: str) -> list[str]:
    """Split into sentences; quoted speech ("New house. New street.") stays together."""
    import re
    par = re.sub(r"\b(Mr|Mrs|Ms|Dr|St)\.", lambda m: m.group(1) + "\u2024", par)  # protect abbreviations
    parts, start, inq = [], 0, False
    for i, ch in enumerate(par):
        if ch in '"\u201c\u201d':
            inq = not inq if ch == '"' else ch == "\u201c"
        if ch in ".!?" and not inq:
            j = i + 1
            if j < len(par) and par[j] in '"\u201d':
                j += 1
            if j >= len(par) or (par[j] == " " and re.match(r' +["\u201c]?[A-Z]', par[j:])):
                parts.append(par[start:j])
                start = j
        elif ch in '"\u201d' and not inq and i + 1 < len(par) and par[i - 1] in ".!?":
            if re.match(r' +["\u201c]?[A-Z]', par[i + 1:]):
                parts.append(par[start:i + 1])
                start = i + 1
    parts.append(par[start:])
    return [p.replace("\u2024", ".").strip() for p in parts if p.strip()]


def _chunks(sentence: str) -> list[str]:
    """Separate quoted speech from its tag: '"Are you lost?" I whispered.' -> 2 chunks."""
    import re
    m = re.match(r'^(["\u201c][^"\u201d]+["\u201d])\s+(.+)$', sentence)
    if m:
        return [m.group(1), m.group(2)]
    m = re.match(r'^(.+?)\s+(["\u201c][^"\u201d]+["\u201d])$', sentence)
    if m:
        return [m.group(1), m.group(2)]
    return [sentence]


def _delivery(slug: str) -> dict:
    """'## Delivery' table in the script: line -> (tone, say_as)."""
    import re
    from common import SCRIPTS
    md = (SCRIPTS / f"{slug}.md").read_text()
    m = re.search(r"^## Delivery\s*\n(.*?)(?=^## |\Z)", md, re.S | re.M)
    out = {}
    for line in (m.group(1) if m else "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and cells[0] not in ("Line",) and not set(cells[0]) <= set("-: "):
            out[_key(cells[0])] = (cells[1].lower() or "neutral", cells[2] if len(cells) > 2 and cells[2] else "")
    return out


def _key(t: str) -> str:
    import re
    return re.sub(r"[^a-z0-9' ]", "", t.lower().replace("\u2019", "'")).strip()


# tone -> (speed multiplier, gain dB, extra voice weights mixed into the base blend)
TONES = {
    "neutral": (1.00, 0.0, {}), "curious": (0.97, 0.0, {}), "warm": (0.95, 0.0, {}),
    "excited": (1.06, 1.5, {"am_puck": 0.35}), "funny": (1.03, 0.5, {"am_puck": 0.2}),
    "sad": (0.90, -1.5, {"am_adam": 0.25}), "soft": (0.92, -2.5, {}),
    "whisper": (0.86, -6.0, {}), "dramatic": (0.93, 0.0, {}),
}


def widen_intonation(audio, sr: int, k: float):
    """Exaggerate the pitch movement of one sentence by k around its own average (WORLD vocoder;
    timbre and timing untouched). k=1.4 -> 40% livelier intonation. pip install pyworld"""
    import numpy as np
    import pyworld as pw
    x = audio.astype(np.float64)
    f0, t = pw.dio(x, sr, frame_period=5.0)
    f0 = pw.stonemask(x, f0, t, sr)
    sp = pw.cheaptrick(x, f0, t, sr)
    ap = pw.d4c(x, f0, t, sr)
    v = f0 > 0
    if v.sum() > 5:
        lf = np.log(f0[v])
        base = np.median(lf)
        f0[v] = np.exp(base + k * (lf - base))
    y = pw.synthesize(f0, sp, ap, sr, frame_period=5.0)
    return y.astype(np.float32)[: len(audio)]


def synth_kokoro(slug: str, voice: str = "am_adam:0.5,am_liam:0.5", speed: float = 1.0,
                 pause: float = 0.0, para_pause: float = 0.15, stretch: float = 1.0,
                 short_beat: float = 0.0, expressive: float = 1.0) -> Path:
    """Kokoro (pip install kokoro-onnx soundfile), sentence by sentence with real pauses.

    voice: a Kokoro voice ("am_adam") or a blend ("am_adam:0.5,am_liam:0.5").
    stretch: pauses are multiplied by this (set it to the voice_fx resample factor so
    they end up the intended length after the pitch-up speeds the audio up).
    Short dramatic sentences (<= 3 words) get a beat before them and are read slower.
    """
    import numpy as np
    import soundfile as sf
    from huggingface_hub import hf_hub_download
    from kokoro_onnx import Kokoro
    d = OUTPUT / "stock" / "kokoro"
    for f in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        if not (d / f).exists():
            hf_hub_download("fastrtc/kokoro-onnx", f, local_dir=str(d))
    k = Kokoro(str(d / "kokoro-v1.0.onnx"), str(d / "voices-v1.0.bin"))
    if ":" in voice or "," in voice:
        style = None
        for part in voice.split(","):
            name, w = (part.split(":") + ["1"])[:2]
            v = k.get_voice_style(name.strip()) * float(w)
            style = v if style is None else style + v
    else:
        style = voice
    out_parts, sr, sent_times = [], 24000, []
    sil = lambda sec: np.zeros(int(sec * stretch * sr), np.float32)
    out_parts.append(sil(0.2))
    def trim(a, sr):  # cut Kokoro's padding gently, then fade the edges so joins never click
        win = int(0.01 * sr)
        env = np.convolve(np.abs(a), np.ones(win) / win, "same")
        idx = np.where(env > max(5e-5, env.max() * 0.01))[0]
        if len(idx):
            pad = int(0.04 * sr)
            a = a[max(0, idx[0] - pad): idx[-1] + pad]
        f = min(int(0.008 * sr), len(a) // 4)
        if f > 1:
            a = a.copy()
            a[:f] *= np.linspace(0, 1, f)
            a[-f:] *= np.linspace(1, 0, f)
        return a

    def gap_after(text):  # pause length from the punctuation that ends the chunk
        t = text.rstrip('"\u201d ')
        if t.endswith("..."):
            return 0.30
        return {"?": 0.24, "!": 0.22, ".": 0.20, ",": 0.10}.get(t[-1:], 0.08)

    base_style = style
    styles = {}

    def style_for(tone):
        extra = TONES.get(tone, TONES["neutral"])[2]
        if not extra or isinstance(base_style, str):
            return base_style
        if tone not in styles:
            w = 1.0 + sum(extra.values())
            mix = base_style.copy()
            for name, wt in extra.items():
                mix = mix + k.get_voice_style(name) * wt
            styles[tone] = mix / w
        return styles[tone]

    deliv = _delivery(slug)
    for pi, par in enumerate(_narration_paragraphs(slug)):
        if pi:
            out_parts.append(sil(para_pause))
        for sent in _sentences(par):
            chunks = _chunks(sent)
            for ci, chunk in enumerate(chunks):
                tone, say = deliv.get(_key(chunk), deliv.get(_key(sent), ("neutral", "")) if len(chunks) == 1 else ("neutral", ""))
                spd, gain, _ = TONES.get(tone, TONES["neutral"])
                text = say or chunk
                audio, sr = k.create(text.replace("\u201c", '"').replace("\u201d", '"'), voice=style_for(tone),
                                     speed=speed * spd, lang="en-us")
                audio = trim(audio.astype(np.float32), sr) * (10 ** (gain / 20))
                if expressive != 1.0:
                    audio = widen_intonation(audio, sr, expressive)
                t0 = sum(len(x) for x in out_parts) / sr
                sent_times.append({"text": chunk, "start": round(t0, 4), "end": round(t0 + len(audio) / sr, 4), "tone": tone})
                gap = 0.06 if ci + 1 < len(chunks) else gap_after(text)
                out_parts += [audio, sil(gap)]
    out = OUTPUT / "stock" / "voice" / f"{slug}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), np.concatenate(out_parts), sr)
    import json
    # exact sentence timings (before any voice_fx speed-up) -> reliable per-sentence transcription
    out.with_suffix(".sentences.json").write_text(json.dumps({"sr": sr, "sentences": sent_times}, indent=1))
    log(f"stand-in voice (kokoro {voice} x{speed}, sentence pauses) -> {out}")
    return out


def synth(slug: str, voice: str = "ryan", speed: float = 0.92, pause: float = 0.45, pitch: float = 0.0) -> Path:
    from piper import PiperVoice, SynthesisConfig
    sc = parse_script(slug)
    text = tts_text(" ".join(s["text"] for s in sc["shots"]))
    pv = PiperVoice.load(str(model_path(voice)))
    out = OUTPUT / "stock" / "voice" / f"{slug}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    cfg = SynthesisConfig(length_scale=1 / speed, noise_scale=0.7, noise_w_scale=0.9)
    first = True
    with wave.open(str(out), "wb") as wf:
        for chunk in pv.synthesize(text, syn_config=cfg):  # one chunk per sentence
            if first:
                wf.setframerate(chunk.sample_rate)
                wf.setsampwidth(chunk.sample_width)
                wf.setnchannels(chunk.sample_channels)
                wf.writeframes(b"\0" * int(0.25 * chunk.sample_rate) * chunk.sample_width)
                first = False
            wf.writeframes(chunk.audio_int16_bytes)
            wf.writeframes(b"\0" * int(pause * chunk.sample_rate) * chunk.sample_width)
    if pitch:  # semitones up (high-pitched kid narrator), tempo kept
        import subprocess
        tmp = out.with_suffix(".tmp.wav")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out), "-af",
                        f"rubberband=pitch={2 ** (pitch / 12):.4f}", str(tmp)], check=True)
        tmp.replace(out)
    log(f"stand-in voice ({voice}{f', +{pitch} st' if pitch else ''}) -> {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--engine", default="kokoro", choices=["kokoro", "piper"])
    ap.add_argument("--voice", default=None, help="kokoro: af_heart, af_bella, ...; piper: ryan, lessac, amy")
    ap.add_argument("--speed", type=float, default=0.92)
    ap.add_argument("--pause", type=float, default=0.45, help="silence between sentences (s)")
    ap.add_argument("--pitch", type=float, default=0.0, help="semitones up, e.g. 3 (girl) or 5 (boy) for a kid voice")
    a = ap.parse_args()
    if a.engine == "kokoro":
        cfg = __import__("common").config()
        vc, fx = cfg.get("voice", {}), cfg.get("voice_fx", {})
        stretch = 2 ** (float(fx.get("pitch_semitones", 0)) / 12) if fx.get("enabled") and fx.get("method") == "resample" else 1.0
        synth_kokoro(a.slug, a.voice or vc.get("kokoro_voice", "am_adam:0.5,am_liam:0.5"),
                     a.speed if a.speed != 0.92 else float(vc.get("kokoro_speed", 1.0)), stretch=stretch,
                     expressive=float(vc.get("expressive", 1.0)))
    else:
        synth(a.slug, a.voice or "ryan", a.speed, a.pause, a.pitch)
