#!/usr/bin/env python3
"""Music-promo cut: no narration, the story is told in on-screen text, the song is added on the platform.

  python tools/music_edit.py <slug> [--song song.mp3 --song-start 12.5]

Reads edits/<slug>.json  {"credit": "Song: artist - title", "shots": [{"n", "dur", "text", "src"?}, ...]}
Writes output/<slug>.mp4            1080x1920 30fps, SILENT audio track (add the official sound in-app)
       output/<slug>_with_song.mp4  preview only, if --song is given (never post this one - use the platform audio)
Story text sits in the upper third (pops in per shot); the song credit stays bottom-centre for the whole video.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import EDITS, OUTPUT, ROOT, load_json, log  # noqa: E402

W, H, FPS = 1080, 1920, 30


def font_dir() -> Path:
    a = ROOT / "assets" / "fonts"
    if a.exists() and any(a.glob("*.[ot]tf")):
        return a
    return Path(__file__).parent / "fonts"


def ts(t: float) -> str:
    h, r = divmod(max(0.0, t), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass(plan: dict, path: Path, total: float):
    font = "Montserrat ExtraBold"
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Story,{font},74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,6,3,8,90,90,330,1",
        f"Style: Credit,{font},56,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,3,14,0,2,80,80,170,1",
        # lyrics: lower-middle of the frame (chest height, under the faces), words revealed on their beat
        f"Style: Lyric,{font},78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,6,3,2,80,80,560,1",
        f"Style: Hook,{font},108,&H0040D8FF,&H00FFFFFF,&H00301040,&H80000000,0,0,0,0,100,100,6,0,1,9,4,5,40,40,0,1",
        f"Style: HookSub,{font},52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,5,2,5,40,40,0,1",
        f"Style: Top,{font},80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,6,3,8,80,80,210,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    off = float(plan.get("song_start", 0.0))      # lyric times are song times
    hook = plan.get("top_hook")
    if hook:
        lines.append(f"Dialogue: 2,{ts(0)},{ts(hook.get('t1', 2.5))},Top,,0,0,0,,"
                     r"{\fad(0,200)\fscx90\fscy90\t(0,160,\fscx100\fscy100)}" + hook["text"])
    lyr = [] if plan.get("lyrics_3d") else plan.get("lyrics", [])   # 3D lyrics live in the shots themselves
    for i, ln in enumerate(lyr):
        t0 = float(ln["t0"]) - off
        nxt = float(lyr[i + 1]["t0"]) - off if i + 1 < len(lyr) else total
        t1 = min(max(float(ln.get("t1", nxt)) - off + 0.35, t0 + 0.8), nxt, total)
        if t1 <= 0 or t0 >= total:
            continue
        if ln.get("hook"):    # big glowing title-style hook, words slam in
            parts = []
            for w, wt in ln["words"]:
                ms = int(max(0.0, (float(wt) - off - t0)) * 1000)
                parts.append(r"{\alpha&HFF&\fscx140\fscy140\t(%d,%d,\alpha&H00&\fscx100\fscy100)}%s" % (ms, ms + 110, w))
            lines.append(f"Dialogue: 3,{ts(max(0, t0))},{ts(t1)},Hook,,0,0,0,," + r"{\q2\pos(540,800)\blur1.5}" + " ".join(parts))
            if ln.get("sub"):
                lines.append(f"Dialogue: 3,{ts(max(0, t0) + 0.4)},{ts(t1)},HookSub,,0,0,0,,"
                             r"{\q2\pos(540,915)\fad(200,150)}" + ln["sub"])
            continue
        parts = []
        for w, wt in ln["words"]:     # each word fades + pops in on its sung time
            ms = int(max(0.0, (float(wt) - off - t0)) * 1000)
            parts.append(r"{\alpha&HFF&\t(%d,%d,\alpha&H00&)}%s" % (ms, ms + 90, w))
        lines.append(f"Dialogue: 1,{ts(max(0, t0))},{ts(t1)},Lyric,,0,0,0,," + r"{\fad(0,120)}" + " ".join(parts))
    t = 0.0
    for s in plan["shots"]:
        d = float(s["dur"])
        if s.get("text"):
            pop = r"{\fad(120,120)\fscx88\fscy88\t(0,140,\fscx100\fscy100)}"
            lines.append(f"Dialogue: 1,{ts(t + 0.08)},{ts(t + d - 0.05)},Story,,0,0,0,,{pop}{s['text']}")
        t += d
    if plan.get("credit"):
        lines.append(f"Dialogue: 0,{ts(0)},{ts(total)},Credit,,0,0,0,,{plan['credit']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--song", help="local copy of the song, for a timing preview only")
    ap.add_argument("--song-start", type=float, default=None, help="where in the song the video starts (s)")
    a = ap.parse_args()
    plan = load_json(EDITS / f"{a.slug}.json")
    if not plan:
        raise SystemExit(f"edits/{a.slug}.json missing")
    shots = plan["shots"]
    total = sum(float(s["dur"]) for s in shots)
    cache = OUTPUT / "cache" / a.slug
    cache.mkdir(parents=True, exist_ok=True)
    ass = cache / "music_text.ass"
    write_ass(plan, ass, total)

    ins, chains = [], []
    for i, s in enumerate(shots):
        src = ROOT / f"raw/{a.slug}/shot_{s['n']:02d}.mp4"
        if not src.exists():
            src = ROOT / (s.get("src") or f"output/anim/{a.slug}/shot_{s['n']:02d}.mp4")
        ins += ["-i", str(src)]
        chains.append(f"[{i}:v]trim=0:{s['dur']},setpts=PTS-STARTPTS,fps={FPS},"
                      f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[v{i}]")
    cat = "".join(f"[v{i}]" for i in range(len(shots))) + f"concat=n={len(shots)}:v=1:a=0[cat]"
    sub = str(ass).replace(":", r"\:")
    fdir = str(font_dir()).replace(":", r"\:")
    look = (f"[cat]eq=saturation=1.08:contrast=1.04,vignette=PI/5,"
            f"subtitles='{sub}':fontsdir='{fdir}'[out]")
    fc = ";".join(chains + [cat, look])
    out = OUTPUT / f"{a.slug}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-f", "lavfi", "-t", f"{total:.3f}", "-i",
           "anullsrc=channel_layout=stereo:sample_rate=48000",
           "-filter_complex", fc, "-map", "[out]", "-map", f"{len(shots)}:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    log(f"music edit -> {out}  ({total:.1f}s, silent track - add the official sound in-app)")
    if a.song:
        prev = OUTPUT / f"{a.slug}_with_song.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-ss", str(a.song_start if a.song_start is not None else plan.get("song_start", 0.0)), "-i", a.song,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-af", f"afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5", "-t", f"{total:.3f}", str(prev)],
                       check=True)
        log(f"preview with song -> {prev}  (for checking only - post the silent one with the platform sound)")


if __name__ == "__main__":
    main()
