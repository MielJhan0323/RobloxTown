#!/usr/bin/env python3
"""Render a story end to end.

  python tools/render.py <slug>            final 1080x1920 -> output/<slug>.mp4
  python tools/render.py <slug> --preview  540x960 ultrafast -> output/<slug>_preview.mp4
  options: --retranscribe  --stills N (grab N check frames)  --whisper-model small.en

Steps: transcribe (if the voice changed) -> plan -> captions -> audio -> video.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import audio  # noqa: E402
import captions  # noqa: E402
import plan as planner  # noqa: E402
import video  # noqa: E402
from common import EDITS, ROOT, cache_dir, load_json, log, probe_duration, run, voice_path  # noqa: E402


def fmt(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:05.2f}"


def shot_table(data: dict) -> str:
    rows = ["| # | time | len | shot | transition | motion | text |", "|---|---|---|---|---|---|---|"]
    for s in data["shots"]:
        e = planner.effective(s)
        src = Path(e["src"]).name if e.get("src") else "PLACEHOLDER"
        rows.append(f"| {s['n']} | {fmt(s['start'])}-{fmt(s['end'])} | {s['dur']:.1f}s | {src} | "
                    f"{e.get('transition')} | {e.get('motion')} | {s['text'][:60]} |")
    return "\n".join(rows)


def stills(slug: str, video_path: Path, data: dict, n: int) -> list[Path]:
    d = cache_dir(slug) / "check"
    d.mkdir(exist_ok=True)
    for p in d.glob("*.jpg"):
        p.unlink()
    shots = data["shots"]
    pick = [shots[round(i * (len(shots) - 1) / max(1, n - 1))] for i in range(n)]
    out = []
    for s in pick:
        t = s["start"] + min(0.6, s["dur"] / 2)
        p = d / f"t{t:06.2f}_shot{s['n']:02d}.jpg"
        run(["ffmpeg", "-ss", f"{t:.3f}", "-i", video_path, "-frames:v", 1, "-q:v", 3, p])
        out.append(p)
    log(f"check frames -> {d.relative_to(ROOT)}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--retranscribe", action="store_true")
    ap.add_argument("--whisper-model", default="small.en")
    ap.add_argument("--stills", type=int, default=0)
    a = ap.parse_args()
    slug = a.slug

    from common import apply_voice_fx
    apply_voice_fx(slug)
    vp = voice_path(slug)
    wj = EDITS / f"{slug}.words.json"
    if vp and (a.retranscribe or not wj.exists() or wj.stat().st_mtime < vp.stat().st_mtime):
        import transcribe
        transcribe.transcribe(slug, a.whisper_model)
    elif not vp:
        log(f"no voice at audio/voice/{slug}.mp3 yet - rendering a silent animatic with estimated timing")

    data = planner.plan(slug)
    captions.build(slug)
    mix = audio.mix(slug)
    out = video.render(slug, preview=a.preview, audio=mix)

    data = load_json(EDITS / f"{slug}.json")
    missing = [s["n"] for s in data["shots"] if not planner.effective(s).get("src")]
    print(f"\nOUTPUT: {out.relative_to(ROOT)}  ({fmt(probe_duration(out))})")
    print(shot_table(data))
    if missing:
        print("\nMissing raw shots (placeholders used): " + ", ".join(f"raw/{slug}/shot_{n:02d}.mp4" for n in missing))
    if a.stills:
        for p in stills(slug, out, data, a.stills):
            print(p)


if __name__ == "__main__":
    main()
