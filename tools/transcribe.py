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
    from common import raw_voice_path
    src_voice = raw_voice_path(slug)
    if side.exists() and src_voice == STOCK / "voice" / f"{slug}.wav" and \
            side.stat().st_mtime >= src_voice.stat().st_mtime - 5:
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

    # Repair: Whisper sometimes drops a stretch of fast speech (and hallucinates filler like
    # "thank you for watching"). Find gaps with speech energy but no words; redo them in small pieces.
    junk = {"thank", "you", "for", "watching", "thanks", "subscribe"}
    speech = env > max(1e-6, np.percentile(env, 70) * 0.05)

    def voiced(t0, t1):
        a, b = int(t0 * 100), int(t1 * 100)
        return speech[a:b].mean() if b > a else 0.0

    for _ in range(2):
        words.sort(key=lambda w: w["start"])
        bounds = [0.0] + [x for w in words for x in (w["start"], w["end"])] + [n / sr]
        gaps = [(bounds[i], bounds[i + 1]) for i in range(0, len(bounds) - 1, 2)
                if bounds[i + 1] - bounds[i] > 1.2 and voiced(bounds[i], bounds[i + 1]) > 0.35]
        if not gaps:
            break
        for g0, g1 in gaps:
            # drop hallucinated filler words sitting inside/next to the gap
            words = [w for w in words if not (g0 - 1.5 <= w["start"] <= g1 + 1.5 and w["word"].lower().strip(".,!") in junk)]
            t = g0
            while t < g1 - 0.2:
                c0, c1 = int(max(0, t - 0.15) * sr), int(min(g1 + 0.15, t + 4.0) * sr)
                segs, _ = model.transcribe(samples[c0:c1], language="en", word_timestamps=True,
                                           beam_size=5, condition_on_previous_text=False, temperature=0.0)
                for seg in segs:
                    for w in seg.words or []:
                        tw = w.word.strip()
                        st_ = w.start + c0 / sr
                        if tw and g0 - 0.05 <= st_ <= g1 + 0.05:
                            words.append({"word": tw, "start": round(st_, 3), "end": round(w.end + c0 / sr, 3)})
                t += 4.0
        log(f"re-transcribed {len(gaps)} skipped stretch(es)")
    words.sort(key=lambda w: w["start"])

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
