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
    import re
    par = re.sub(r"\b(Mr|Mrs|Ms|Dr|St)\.", lambda m: m.group(1) + "\u2024", par)  # protect abbreviations
    parts, start = [], 0
    for m in re.finditer(r'[.!?]["\u201d]?(?=\s+["\u201c]?[A-Z])', par):
        parts.append(par[start:m.end()])
        start = m.end()
    parts.append(par[start:])
    return [p.replace("\u2024", ".").strip() for p in parts if p.strip()]


def synth_kokoro(slug: str, voice: str = "am_adam:0.5,am_liam:0.5", speed: float = 0.72,
                 pause: float = 0.42, para_pause: float = 0.8, stretch: float = 1.0) -> Path:
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
    out_parts, sr = [], 24000
    sil = lambda sec: np.zeros(int(sec * stretch * sr), np.float32)
    out_parts.append(sil(0.2))
    for pi, par in enumerate(_narration_paragraphs(slug)):
        if pi:
            out_parts.append(sil(para_pause - pause))
        for sent in _sentences(par):
            short = len(sent.split()) <= 3
            if short:
                out_parts.append(sil(0.22))
            audio, sr = k.create(sent, voice=style, speed=speed * (0.9 if short else 1.0), lang="en-us")
            out_parts += [audio.astype(np.float32), sil(pause)]
    out = OUTPUT / "stock" / "voice" / f"{slug}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), np.concatenate(out_parts), sr)
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
                     a.speed if a.speed != 0.92 else float(vc.get("kokoro_speed", 0.72)), stretch=stretch)
    else:
        synth(a.slug, a.voice or "ryan", a.speed, a.pause, a.pitch)
