#!/usr/bin/env python3
"""Edit plan words -> one-word-at-a-time ASS captions  output/cache/<slug>/captions.ass

White bold rounded sans, ~4px black outline + soft shadow, centered at ~57% height,
tiny 90%->100% pop-in. No colors, no emojis.

usage: python tools/captions.py <slug>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import EDITS, H, W, cache_dir, config, load_json, log  # noqa: E402


def ts(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def clean(word: str, upper: bool) -> str:
    w = word.strip().strip('"“”')
    w = re.sub(r"[.,;:]+$", "", w)          # drop trailing soft punctuation, keep ?!
    w = re.sub(r"^[(\[]|[)\]]$", "", w)
    w = w.replace("{", "").replace("}", "")
    return w.upper() if upper else w


def build(slug: str) -> Path:
    cfg = config().get("captions", {})
    data = load_json(EDITS / f"{slug}.json")
    if not data:
        raise SystemExit(f"run plan.py {slug} first")
    over = (data.get("override") or {}).get("captions", {})
    cfg = {**cfg, **over}
    size = int(cfg.get("size", 76))
    outline = cfg.get("outline", 4)
    shadow = cfg.get("shadow", 3)
    y = int(H * float(cfg.get("y_pct", 0.575)))
    pop = int(cfg.get("pop_ms", 80))
    hold = float(cfg.get("max_hold", 0.9))
    font = cfg.get("font", "Montserrat ExtraBold")

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,1,0,1,{outline},{shadow},5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    words = data["words"]
    lines = []
    for i, w in enumerate(words):
        txt = clean(w["w"], cfg.get("uppercase", False))
        if not txt:
            continue
        start = w["s"]
        nxt = words[i + 1]["s"] if i + 1 < len(words) else data["duration"]
        end = min(nxt, max(w["e"], start + 0.12) + hold)
        if end - start < 0.06:
            end = start + 0.06
        anim = f"{{\\pos({W // 2},{y})\\fscx90\\fscy90\\t(0,{pop},\\fscx100\\fscy100)}}" if pop else f"{{\\pos({W // 2},{y})}}"
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Word,,0,0,0,,{anim}{txt}")
    out = cache_dir(slug) / "captions.ass"
    out.write_text(head + "\n".join(lines) + "\n")
    log(f"captions -> {out.relative_to(out.parents[3])} ({len(lines)} words)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    build(ap.parse_args().slug)
