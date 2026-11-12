#!/usr/bin/env python3
"""Render animated 3D stand-in shots (Blender + tools/anim/stories/<slug>.py).

  python tools/animate.py <slug> [shots...] [--jobs 2] [--force] [--res 540x960] [--samples 8]
  python tools/animate.py <slug> 5 12 --stills      # one PNG per shot for a quick look

Clips go to output/anim/<slug>/shot_XX.mp4, sized to each shot's planned length
(+0.6 s for transitions). The edit uses them wherever raw/<slug>/shot_XX.mp4
(your Roblox Studio recording) doesn't exist yet.
Setup: apt-get install -y blender xvfb
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import EDITS, OUTPUT, TOOLS, load_json, log  # noqa: E402

PAD = 0.6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("shots", nargs="*", type=int)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--res", default="540x960")
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--stills", action="store_true")
    a = ap.parse_args()
    plan = load_json(EDITS / f"{a.slug}.json")
    if not plan:
        raise SystemExit(f"run tools/plan.py {a.slug} first (shot lengths come from the plan)")
    w, h = a.res.split("x")
    outdir = OUTPUT / "anim" / a.slug
    outdir.mkdir(parents=True, exist_ok=True)
    todo = []
    for s in plan["shots"]:
        if a.shots and s["n"] not in a.shots:
            continue
        # ITT_DUR_SCALE > 1 renders longer clips (e.g. before the real voice exists; the edit trims them)
        scale = float(__import__("os").environ.get("ITT_DUR_SCALE", "1"))
        frames = int(math.ceil((s["dur"] * scale + PAD) * 30))
        out = outdir / (f"still_{s['n']:02d}.png" if a.stills else f"shot_{s['n']:02d}.mp4")
        if out.exists() and not a.force:
            continue
        todo.append((s["n"], frames, out))

    def job(t):
        n, frames, out = t
        tmp = out.with_name(out.stem + ".part" + out.suffix)
        cmd = ["xvfb-run", "-a", "-s", "-screen 0 1280x1024x24", "blender", "-b", "--factory-startup",
               "-P", str(TOOLS / "anim" / "render_shot.py"), "--", a.slug, str(n), str(frames), str(tmp), w, h,
               str(a.samples)] + ([str(max(1, frames // 2))] if a.stills else [])
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not tmp.exists():
            err = [l for l in (r.stdout + r.stderr).splitlines() if "Error" in l or "Traceback" in l or "line" in l][-12:]
            log(f"shot {n} FAILED:\n" + "\n".join(err))
            return n, False
        tmp.replace(out)
        log(f"shot {n:02d}: {frames} frames in {time.time() - t0:.0f}s")
        return n, True

    log(f"rendering {len(todo)} shots ({sum(t[1] for t in todo)} frames) with {a.jobs} jobs ...")
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(job, todo))
    bad = [n for n, ok in res if not ok]
    if bad:
        raise SystemExit(f"failed shots: {bad}")


if __name__ == "__main__":
    main()
