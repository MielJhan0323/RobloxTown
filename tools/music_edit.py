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


# ---------------------------------------------------------------- perspective lyrics (CapCut-style "perspective text")
# Flat 2D text drawn on a black canvas, warped onto a quad, screen-blended over the shot, characters put back on top
# with their matte (output/anim/<slug>/matte_XX.mp4) so the words sit BEHIND them. Quads: TL, TR, BL, BR in 1080x1920.
QUADS = {
    "floor": [(250, 930), (830, 930), (-560, 1780), (1640, 1780)],      # lying on the road, receding
    "top":   [(80, 640), (1000, 640), (-150, 1660), (1230, 1660)],      # top-down shot: gentle tilt
    "back":  [(40, 150), (1040, 240), (40, 1350), (1040, 1260)],        # upright behind the characters, slight angle
    "hook":  [(70, 170), (1010, 170), (-30, 1330), (1110, 1330)],       # title leaning back over the skyline
}


def font_family() -> str:
    fd = font_dir()
    files = sorted(list(fd.glob("*.otf")) + list(fd.glob("*.ttf")))
    if files and fd.name == "fonts" and fd.parent.name == "assets":
        r = subprocess.run(["fc-scan", "--format", "%{family[0]}", str(files[0])], capture_output=True, text=True)
        if r.stdout.strip():
            return r.stdout.strip()
    return "Montserrat ExtraBold"


def wrap_words(words, max_chars):
    rows, cur, n = [], [], 0
    for w in words:
        if cur and n + len(w[0]) > max_chars:
            rows.append(cur); cur, n = [], 0
        cur.append(w); n += len(w[0]) + 1
    if cur:
        rows.append(cur)
    return rows


def shot_lyric_ass(plan, shot, path: Path):
    """ASS for one shot: its lyric lines, words revealed on their sung time, centred on a 1080x1920 canvas."""
    off = float(plan.get("song_start", 0.0))
    a, b = float(shot["start"]), float(shot["end"])
    mode = shot.get("lyric_mode", "floor")
    hook_mode = mode == "hook"
    font = font_family()
    size = {"floor": 130, "top": 120, "back": 104, "hook": 112}[mode]
    glow = "&H00FFB070&" if not hook_mode else "&H0030A0FF&"        # BGR: soft blue / warm gold
    main = "&H00FFFFFF&" if not hook_mode else "&H0060E0FF&"
    head = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
            "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: L,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,0,0,0,1",
            f"Style: S,{font},{int(size * 0.36)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,0,0,0,1",
            "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    lyr = [ln for ln in plan.get("lyrics", []) if bool(ln.get("hook")) == hook_mode]
    ev = []
    for i, ln in enumerate(lyr):
        l0, l1 = float(ln["t0"]) - off, float(ln.get("t1", ln["t0"])) - off
        if l0 >= b - 0.05 or l1 < a + 0.1:
            continue
        nxt = float(lyr[i + 1]["t0"]) - off if i + 1 < len(lyr) else 1e9
        t0, t1 = max(0.0, l0 - a), min(b - a, nxt - a, l1 - a + 0.6)
        words = [(w.upper(), max(0.0, float(t) - off - a)) for w, t in ln["words"] if float(t) - off < b - 0.05]
        if not words or t1 <= t0:
            continue
        rows = wrap_words(words, 22 if hook_mode else 12)
        def body(blur):
            out = []
            for r in rows:
                parts = []
                for w, wt in r:
                    ms = int(max(0.0, wt - t0) * 1000)
                    parts.append(r"{\alpha&HFF&\t(%d,%d,\alpha&H00&)}%s" % (ms, ms + 90, w))
                out.append(" ".join(parts))
            col = glow if blur else main
            return r"{\pos(540,960)\blur%d\1c%s}" % (blur, col) + r"\N".join(out)
        ev.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},L,,0,0,0,,{body(14)}")     # glow
        ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},L,,0,0,0,,{body(0)}")      # crisp letters
        if ln.get("sub"):
            y = 960 + int(size * 0.75 * len(rows)) + 20
            ev.append(f"Dialogue: 1,{ts(t0 + 0.4)},{ts(t1)},S,,0,0,0,," + r"{\pos(540,%d)\fad(200,0)}" % y + ln["sub"].upper())
    path.write_text("\n".join(head + ev) + "\n", encoding="utf-8")
    return bool(ev)


def esc(p) -> str:
    return str(p).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


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

    persp = plan.get("lyrics_layer") == "perspective"
    ins, chains = [], []
    fdir_ = esc(font_dir())
    for i, s in enumerate(shots):
        src = ROOT / f"raw/{a.slug}/shot_{s['n']:02d}.mp4"
        if not src.exists():
            src = ROOT / (s.get("src") or f"output/anim/{a.slug}/shot_{s['n']:02d}.mp4")
        si = len(ins) // 2                 # input index of this shot (mattes are interleaved)
        ins += ["-i", str(src)]
        base = (f"[{si}:v]trim=0:{s['dur']},setpts=PTS-STARTPTS,fps={FPS},"
                f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1")
        sass = cache / f"lyr_{s['n']:02d}.ass"
        matte = OUTPUT / "anim" / a.slug / f"matte_{s['n']:02d}.mp4"
        if not (persp and shot_lyric_ass(plan, s, sass)):
            chains.append(base + f"[v{i}]")
            continue
        q = s.get("lyric_quad") or QUADS[s.get("lyric_mode", "floor")]
        qs = ":".join(f"{x}:{y}" for x, y in q)
        d = float(s["dur"])
        chains.append(base + f",format=gbrp,split[sa{i}][sb{i}]")
        chains.append(f"color=c=black:s={W}x{H}:r={FPS}:d={d:.3f},format=rgb24,"
                      f"subtitles='{esc(sass)}':fontsdir='{fdir_}',"
                      f"perspective={qs}:sense=destination,format=gbrp[tx{i}]")
        chains.append(f"[sa{i}][tx{i}]blend=all_mode=screen[bl{i}]")
        if matte.exists():
            mi = len(ins) // 2
            ins += ["-i", str(matte)]
            chains.append(f"[{mi}:v]trim=0:{d},setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H},format=gray,"
                          f"lut=y='if(gt(val,110),255,0)',boxblur=1:1[mt{i}]")
            chains.append(f"[sb{i}]format=rgba[sc{i}];[sc{i}][mt{i}]alphamerge[ch{i}]")
            chains.append(f"[bl{i}]format=rgba[bb{i}];[bb{i}][ch{i}]overlay=0:0,format=yuv420p[v{i}]")
        else:
            chains.append(f"[sb{i}]nullsink;[bl{i}]format=yuv420p[v{i}]")
    cat = "".join(f"[v{i}]" for i in range(len(shots))) + f"concat=n={len(shots)}:v=1:a=0[cat]"
    sub = str(ass).replace(":", r"\:")
    fdir = str(font_dir()).replace(":", r"\:")
    look = (f"[cat]eq=saturation=1.08:contrast=1.04,vignette=PI/5,"
            f"subtitles='{sub}':fontsdir='{fdir}'[out]")
    fc = ";".join(chains + [cat, look])
    out = OUTPUT / f"{a.slug}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-f", "lavfi", "-t", f"{total:.3f}", "-i",
           "anullsrc=channel_layout=stereo:sample_rate=48000",
           "-filter_complex", fc, "-map", "[out]", "-map", f"{len(ins) // 2}:a",
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
