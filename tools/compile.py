#!/usr/bin/env python3
"""Join finished Shorts into a 16:9 YouTube compilation.

Each vertical Short sits centred on a blurred, zoomed, slightly darkened copy of
itself. 0.5 s fog transition between stories. Captions are already burned in.

  python tools/compile.py lost-hat signature-magic ocean-gives-back [--channel "Name"] [--out name]

Writes output/<name>.mp4 and output/<name>.txt (title + YouTube chapters).
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import EDITS, FPS, OUTPUT, ROOT, config, load_json, log, probe_duration, run  # noqa: E402
from video import build_fx_layer  # noqa: E402

CW, CH = 1920, 1080


def chapter_time(t: float) -> str:
    t = int(t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="+")
    ap.add_argument("--channel", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--fade", type=float, default=0.5)
    ap.add_argument("--preview", action="store_true", help="960x540 ultrafast")
    a = ap.parse_args()
    channel = a.channel or config().get("channel", "Your Channel")
    w, h = (960, 540) if a.preview else (CW, CH)
    name = a.out or f"compilation_{dt.date.today():%Y%m%d}"

    clips = []
    for slug in a.slugs:
        p = OUTPUT / f"{slug}.mp4"
        if not p.exists():
            raise SystemExit(f"missing {p.relative_to(ROOT)} - render it first (python tools/render.py {slug})")
        title = (load_json(EDITS / f"{slug}.json") or {}).get("title", slug)
        clips.append((slug, p, probe_duration(p), title))

    d = a.fade
    inputs, parts = [], []
    blur = max(10, int(40 * h / CH))
    for i, (_, p, dur, _) in enumerate(clips):
        inputs += ["-i", p]
        parts.append(
            f"[{i}:v]fps={FPS},settb=AVTB,setsar=1,split=2[bg{i}][fg{i}];"
            f"[bg{i}]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
            f"boxblur={blur}:2,eq=brightness=-0.07:saturation=0.9[b{i}];"
            f"[fg{i}]scale=-2:{h}:flags=lanczos[f{i}];"
            f"[b{i}][f{i}]overlay=(W-w)/2:0,format=yuv420p[v{i}];"
            f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS[a{i}]")

    vacc, aacc, length = "v0", "a0", clips[0][2]
    chapters = [(0.0, clips[0][3])]
    fog_events = []
    for i in range(1, len(clips)):
        off = length - d
        parts.append(f"[{vacc}][v{i}]xfade=transition=fade:duration={d}:offset={off:.3f}[vx{i}]")
        parts.append(f"[{aacc}][a{i}]acrossfade=d={d}:c1=tri:c2=tri[ax{i}]")
        fog_events.append({"kind": "fog", "t": off + d / 2, "d": d})
        chapters.append((off + d / 2, clips[i][3]))
        vacc, aacc, length = f"vx{i}", f"ax{i}", off + clips[i][2]

    total_frames = int(round(length * FPS))
    fx = build_fx_layer(f"_compile_{name}", fog_events, total_frames) if fog_events else None
    if fx:
        n = len(clips)
        inputs += ["-i", fx]
        parts.append(f"[{n}:v]scale={w}:{h},format=gbrp[fx];[{vacc}]format=gbrp[base];"
                     f"[base][fx]blend=all_mode=screen:shortest=1,format=yuv420p[vout]")
    else:
        parts.append(f"[{vacc}]null[vout]")

    out = OUTPUT / f"{name}{'_preview' if a.preview else ''}.mp4"
    gfile = OUTPUT / "cache" / f"{name}_graph.txt"
    gfile.parent.mkdir(parents=True, exist_ok=True)
    gfile.write_text(";\n".join(parts))
    log(f"compiling {len(clips)} stories ({chapter_time(length)}) ...")
    run(["ffmpeg", *inputs, "-filter_complex_script", gfile, "-map", "[vout]", "-map", f"[{aacc}]",
         "-c:v", "libx264", "-preset", "ultrafast" if a.preview else "medium", "-crf", "26" if a.preview else "18",
         "-pix_fmt", "yuv420p", "-r", FPS, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])

    title = f"In This Town Roblox Story Compilation - {channel}"
    txt = [title, "", "Chapters:"] + [f"{chapter_time(t)} {name_}" for t, name_ in chapters]
    (OUTPUT / f"{name}.txt").write_text("\n".join(txt) + "\n")
    print(f"OUTPUT: {out.relative_to(ROOT)}  ({chapter_time(probe_duration(out))})")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
