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
    # Narration made by tts_local.py comes with exact sentence timings: transcribe one sentence
    # at a time (short clips are reliable), shifted onto the voice_fx timeline.
    from common import STOCK, config
    side = STOCK / "voice" / f"{slug}.sentences.json"
    fxc = config().get("voice_fx", {})
    speedup = 1.0
    if fxc.get("enabled") and fxc.get("method") == "resample":
        speedup = 2 ** (float(fxc.get("pitch_semitones", 0)) / 12) * float(fxc.get("tempo", 1.0))
    if side.exists() and (vp.name == "voice_fx.wav" or vp.parent == STOCK / "voice") and \
            side.stat().st_mtime >= (STOCK / "voice" / f"{slug}.wav").stat().st_mtime - 5:
        import json as _json
        sents = _json.loads(side.read_text())["sentences"]
        if vp.name != "voice_fx.wav":
            speedup = 1.0
        words, sr = [], 16000
        for st in sents:
            a, b = st["start"] / speedup, st["end"] / speedup
            i0, i1 = max(0, int((a - 0.05) * sr)), min(len(samples), int((b + 0.05) * sr))
            segs, _ = model.transcribe(samples[i0:i1], language="en", word_timestamps=True,
                                       initial_prompt=st["text"], beam_size=5, condition_on_previous_text=False)
            got = [(w.word.strip(), w.start + i0 / sr, w.end + i0 / sr) for sg in segs for w in (sg.words or []) if w.word.strip()]
            if not got:  # fall back: spread the sentence's words evenly over its span
                toks = st["text"].split()
                got = [(t, a + (b - a) * k / len(toks), a + (b - a) * (k + 1) / len(toks)) for k, t in enumerate(toks)]
            words += [{"word": t, "start": round(s0, 3), "end": round(s1, 3)} for t, s0, s1 in got]

        class _Info:
            duration = len(samples) / sr
        save_json(EDITS / f"{slug}.words.json", {"voice": str(vp.name), "duration": round(_Info.duration, 3), "words": words})
        log(f"{len(words)} words (per sentence) -> edits/{slug}.words.json")
        return words

    # Transcribe in ~8 s chunks cut at the quietest moment near each boundary: long fast
    # narration in one pass makes Whisper skip whole stretches.
    sr = 16000
    env = np.convolve(samples ** 2, np.ones(160) / 160, "same")[::160]  # 10 ms energy
    cuts, pos, n = [0], 0, len(samples)
    while pos + 11 * sr < n:
        lo, hi = (pos + 6 * sr) // 160, min(n, pos + 10 * sr) // 160
        q = lo + int(np.argmin(env[lo:hi]))
        pos = q * 160
        cuts.append(pos)
    cuts.append(n)
    words = []
    for c0, c1 in zip(cuts, cuts[1:]):
        segs, info = model.transcribe(
            samples[c0:c1], language="en", word_timestamps=True, vad_filter=False,
            initial_prompt=prompt, beam_size=5, condition_on_previous_text=False,
        )
        off = c0 / sr
        for seg in segs:
            for w in seg.words or []:
                t = w.word.strip()
                if t:
                    words.append({"word": t, "start": round(w.start + off, 3), "end": round(w.end + off, 3)})

    class _Info:
        duration = n / sr
    info = _Info()
    save_json(EDITS / f"{slug}.words.json", {"voice": str(vp.name), "duration": round(info.duration, 3), "words": words})
    log(f"{len(words)} words -> edits/{slug}.words.json")
    return words


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--model", default="small.en")
    a = ap.parse_args()
    transcribe(a.slug, a.model)
