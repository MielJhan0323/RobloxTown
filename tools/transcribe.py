#!/usr/bin/env python3
"""Voice track -> word timestamps.  edits/<slug>.words.json

usage: python tools/transcribe.py <slug> [--model small.en]
"""
from __future__ import annotations

import argparse
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import EDITS, log, parse_script, save_json, voice_path  # noqa: E402


def transcribe(slug: str, model_name: str = "small.en") -> list[dict]:
    vp = voice_path(slug)
    if not vp:
        raise SystemExit(f"no voice file audio/voice/{slug}.mp3 (or .wav)")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("pip install faster-whisper")

    # Bias recognition toward the script's spelling (character names etc.)
    prompt = None
    try:
        sc = parse_script(slug)
        prompt = " ".join(s["text"] for s in sc["shots"])[:800]
    except SystemExit:
        pass

    log(f"transcribing {vp.name} with {model_name} ...")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    # decode with ffmpeg ourselves (avoids PyAV version issues)
    import subprocess
    import numpy as np
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(vp), "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    samples = np.frombuffer(pcm, np.float32)
    segments, info = model.transcribe(
        samples, language="en", word_timestamps=True, vad_filter=False,
        initial_prompt=prompt, beam_size=5,
    )
    words = []
    for seg in segments:
        for w in seg.words or []:
            t = w.word.strip()
            if t:
                words.append({"word": t, "start": round(w.start, 3), "end": round(w.end, 3)})
    save_json(EDITS / f"{slug}.words.json", {"voice": str(vp.name), "duration": round(info.duration, 3), "words": words})
    log(f"{len(words)} words -> edits/{slug}.words.json")
    return words


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--model", default="small.en")
    a = ap.parse_args()
    transcribe(a.slug, a.model)
