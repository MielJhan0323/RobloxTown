#!/usr/bin/env python3
"""Add an end-card of viewer choices (numbered red-outlined boxes that slide in) to a finished video.

  python tools/choices.py <slug> "OPEN THE FRONT DOOR" "OPEN THE BACK DOOR" "DON'T OPEN ANY DOOR" [--hold 4] [--lead 2.6]

Reads output/<slug>.mp4 (kept as output/<slug>_noquiz.mp4), writes output/<slug>.mp4 with the boxes popping in
`lead` seconds before the end and the last frame held `hold` extra seconds.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from common import OUTPUT, TOOLS, cache_dir  # noqa: E402


def card(text, n, path, W=980, H=118):
    font = ImageFont.truetype(str(TOOLS / "fonts" / "Montserrat-ExtraBold.otf"), 44 if len(text) < 24 else 38)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3, 3, W - 4, H - 4], radius=18, fill=(14, 12, 14, 235), outline=(210, 40, 40, 255), width=4)
    d.rounded_rectangle([20, 18, 102, H - 18], radius=12, fill=(215, 55, 45, 255))
    d.text((61, H // 2), str(n), font=font, fill="white", anchor="mm")
    d.text((128, H // 2 + 2), text, font=font, fill="white", anchor="lm")
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("options", nargs="+")
    ap.add_argument("--hold", type=float, default=4.0)
    ap.add_argument("--lead", type=float, default=2.6)
    a = ap.parse_args()
    src = OUTPUT / f"{a.slug}_noquiz.mp4"
    if not src.exists():
        (OUTPUT / f"{a.slug}.mp4").replace(src)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                               capture_output=True, text=True).stdout)
    s0 = dur - a.lead
    cd = cache_dir(a.slug)
    inputs, chain, prev = ["-i", str(src)], [f"[0:v]tpad=stop_mode=clone:stop_duration={a.hold},format=yuv420p[v0]"], "v0"
    y0 = 1460 - 140 * (len(a.options) - 1)
    for i, t in enumerate(a.options, 1):
        p = cd / f"choice{i}.png"
        card(t, i, p)
        inputs += ["-loop", "1", "-i", str(p)]
        st = s0 + 0.35 * (i - 1)
        chain.append(f"[{i}:v]format=rgba,fade=t=in:st={st:.2f}:d=0.25:alpha=1[o{i}]")
        chain.append(f"[{prev}][o{i}]overlay=x='(W-w)/2+if(lt(t,{st + 0.25:.2f}),(1-(t-{st:.2f})/0.25)*-120,0)':"
                     f"y={y0 + 140 * (i - 1)}:enable='gte(t,{st:.2f})':shortest=1[c{i}]")
        prev = f"c{i}"
    chain.append(f"[0:a]apad=pad_dur={a.hold}[aud]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chain), "-map", f"[{prev}]",
                    "-map", "[aud]", "-t", f"{dur + a.hold:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUTPUT / f"{a.slug}.mp4")], check=True)
    print("choices ->", OUTPUT / f"{a.slug}.mp4")


if __name__ == "__main__":
    main()
