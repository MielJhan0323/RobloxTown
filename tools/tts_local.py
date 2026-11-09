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


def synth_kokoro(slug: str, voice: str = "af_heart", speed: float = 1.5) -> Path:
    """Kokoro (pip install kokoro-onnx soundfile): far more natural than Piper."""
    import soundfile as sf
    from huggingface_hub import hf_hub_download
    from kokoro_onnx import Kokoro
    d = OUTPUT / "stock" / "kokoro"
    for f in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        if not (d / f).exists():
            hf_hub_download("fastrtc/kokoro-onnx", f, local_dir=str(d))
    k = Kokoro(str(d / "kokoro-v1.0.onnx"), str(d / "voices-v1.0.bin"))
    text = " ".join(s["text"] for s in parse_script(slug)["shots"])
    audio, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
    out = OUTPUT / "stock" / "voice" / f"{slug}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), audio, sr)
    log(f"stand-in voice (kokoro {voice} x{speed}) -> {out}")
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
        synth_kokoro(a.slug, a.voice or "af_heart", a.speed if a.speed != 0.92 else 1.5)
    else:
        synth(a.slug, a.voice or "ryan", a.speed, a.pause, a.pitch)
