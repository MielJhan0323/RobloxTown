#!/usr/bin/env python3
"""Edit plan -> picture.

1. Each shot: cover-crop to 9:16, fit the source clip to the shot length
   (trim, or slow down up to 2x then hold the last frame), add push-in / pan /
   punch-in, colour grade.  Missing shots get a blurred placeholder card.
2. Join: hard cuts, fog dissolves (xfade + drifting mist), flash and sparkle
   overlays for magic moments.
3. Final pass: FX layer (screen blend), vignette, one-word captions, audio mux.

usage: python tools/video.py <slug> [--preview]   (normally called by render.py)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from common import (EDITS, FPS, FX, H, ROOT, VIDEO_EXTS, W, cache_dir, config, font_dir,  # noqa: E402
                    font_file, load_json, log, probe_duration, run)
from plan import effective  # noqa: E402

GRADES = {
    # golden, nostalgic
    "warm": "colorbalance=rs=0.05:gs=0.01:bs=-0.06:rm=0.04:gm=0.0:bm=-0.05:rh=0.03:bh=-0.03,"
            "eq=contrast=1.04:saturation=1.12:gamma=1.02",
    # sad / night
    "cool": "colorbalance=rs=-0.05:gs=-0.01:bs=0.07:rm=-0.04:bm=0.05:rh=-0.02:bh=0.03,"
            "eq=contrast=1.03:saturation=0.82:brightness=-0.035",
    "neutral": "colorbalance=rs=0.02:bs=-0.02:rm=0.015:bm=-0.015,eq=contrast=1.03:saturation=1.06",
    "none": "null",
}
MOOD_RGB = {"warm": (232, 150, 70), "cool": (40, 60, 110), "neutral": (120, 110, 130)}
FX_W, FX_H = 360, 640  # resolution of the generated mist/flash/sparkle layer


# ------------------------------------------------------------------ helpers
def frames(t: float) -> int:
    return int(round(t * FPS))


def placeholder(slug: str, shot: dict, w: int, h: int) -> Path:
    """Blurred gradient card with the shot description (text kept above the caption zone)."""
    desc = shot.get("placeholder") or shot["text"]
    key = hashlib.md5(f"{desc}|{shot['grade']}|{shot['n']}|{w}x{h}|v2".encode()).hexdigest()[:10]
    out = cache_dir(slug) / f"ph_{shot['n']:02d}_{key}.png"
    if out.exists():
        return out
    rng = np.random.default_rng(shot["n"])
    base = np.array(MOOD_RGB.get(shot["grade"], MOOD_RGB["neutral"]), dtype=np.float32)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    img = base * (0.55 + 0.6 * (1 - yy)) + np.zeros((h, w, 3), np.float32)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for _ in range(9):  # soft bokeh blobs so motion is visible
        r = int(rng.uniform(0.08, 0.25) * w)
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        c = tuple(int(min(255, v * rng.uniform(1.0, 1.6))) for v in base)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(w * 0.06))
    d = ImageDraw.Draw(im)
    ff = font_file()
    s = w / 1080
    big = ImageFont.truetype(str(ff), int(110 * s)) if ff else ImageFont.load_default()
    small = ImageFont.truetype(str(ff), int(44 * s)) if ff else ImageFont.load_default()
    tiny = ImageFont.truetype(str(ff), int(34 * s)) if ff else ImageFont.load_default()
    y = int(h * 0.12)
    d.text((w // 2, y), "MISSING SHOT", font=tiny, fill=(255, 255, 255, 200), anchor="mm")
    d.text((w // 2, y + int(110 * s)), f"shot_{shot['n']:02d}", font=big, fill="white", anchor="mm",
           stroke_width=int(4 * s), stroke_fill="black")
    y += int(220 * s)
    for line in textwrap.wrap(desc, 30)[:7]:
        d.text((w // 2, y), line, font=small, fill="white", anchor="mm", stroke_width=int(3 * s), stroke_fill="black")
        y += int(58 * s)
    im.save(out)
    return out


def zoom_expr(motion: str, total: int, cfg: dict) -> tuple[str, str, str]:
    """Return (z(n), x-fraction(n), y-fraction(n)) ffmpeg expressions."""
    N = max(total - 1, 1)
    p, pan, punch, pt = cfg.get("push_in", 0.08), cfg.get("pan", 0.10), cfg.get("punch", 0.18), cfg.get("punch_time", 0.22)
    u = f"(n/{N})"
    if motion == "pull_out":  # rendered as a reversed push-in (ffmpeg 6 crashes on shrinking eval=frame scale)
        return f"(1+{p}*{u})", "0.5", "0.5"
    if motion == "drift":
        return f"(1.02+0.03*{u})", "0.5", "0.5"
    if motion == "punch":
        k = max(1, int(pt * FPS))
        e = f"(1-pow(1-min(n/{k},1),3))"
        return f"(1+{punch}*{e}+0.03*{u})", "0.5", "0.45"
    if motion.startswith("pan_"):
        z = f"(1+{pan})"
        d = motion[4:]
        if d == "right":
            return z, f"(0.15+0.7*{u})", "0.5"
        if d == "left":
            return z, f"(0.85-0.7*{u})", "0.5"
        if d == "up":
            return z, "0.5", f"(0.85-0.7*{u})"
        return z, "0.5", f"(0.15+0.7*{u})"
    return f"(1+{p}*{u})", "0.5", "0.5"  # push_in


def render_segment(slug: str, shot: dict, idx: int, nframes: int, w: int, h: int, preview: bool) -> Path:
    cfg = config()
    mcfg = cfg.get("motion", {})
    src = shot.get("src")
    src_path = (ROOT / src) if src else None
    if src_path and not src_path.exists():
        log(f"shot {shot['n']}: {src} not found, using placeholder")
        src_path = None
    T = nframes / FPS
    BW, BH = 2 * int(w * 1.2 / 2), 2 * int(h * 1.2 / 2)
    fx = float(shot.get("focus_x", 0.5))
    fy = float(shot.get("focus_y", 0.5))
    cover = (f"scale={BW}:{BH}:force_original_aspect_ratio=increase:flags=lanczos,"
             f"crop={BW}:{BH}:'(in_w-{BW})*{fx}':'(in_h-{BH})*{fy}',setsar=1")
    z, xf, yf = zoom_expr(shot.get("motion", "push_in"), nframes, mcfg)
    motion = (f"scale=w='2*trunc({w}*{z}/2)':h='2*trunc({h}*{z}/2)':eval=frame:flags=bicubic,"
              f"crop={w}:{h}:'(in_w-{w})*{xf}':'(in_h-{h})*{yf}',setsar=1")
    if shot.get("motion") == "pull_out":
        motion = f"reverse,{motion},reverse"
    grade = GRADES.get(shot.get("grade", "neutral"), GRADES["neutral"])
    if src_path:
        D = probe_duration(src_path)
        sin = float(shot.get("src_in", 0.0))
        avail = max(0.05, D - sin)
        speed = shot.get("speed")
        if speed is None:
            speed = 1.0 if avail >= T else max(0.5, avail / T)  # slow down up to 2x
        used = min(avail, T * speed)
        pts = f"setpts=(PTS-STARTPTS)/{speed}"
        pre = (f"[0:v]trim=start={sin}:duration={used:.3f},{pts},fps={FPS},"
               f"tpad=stop_mode=clone:stop_duration={T + 1:.3f},")
        inputs = ["-i", src_path]
        if speed < 0.999 or avail < T:
            log(f"shot {shot['n']}: clip {avail:.2f}s for {T:.2f}s -> speed {speed:.2f}" + (" + hold" if avail / speed < T - 0.02 else ""))
    else:
        ph = placeholder(slug, shot, BW, BH)
        pre = f"[0:v]fps={FPS},"
        inputs = ["-loop", "1", "-framerate", str(FPS), "-i", ph]
    key = hashlib.md5(json.dumps([shot, nframes, w, h, preview, str(src_path and src_path.stat().st_mtime), cfg.get("motion")],
                                 sort_keys=True, default=str).encode()).hexdigest()[:10]
    out = cache_dir(slug) / f"seg_{idx:03d}_{key}{'_p' if preview else ''}.mp4"
    if out.exists():
        return out
    graph = f"{pre}trim=end_frame={nframes},{cover},{motion},{grade},format=yuv420p[v]"
    tmp = out.with_suffix(".tmp")
    run(["ffmpeg", *inputs, "-filter_complex", graph, "-map", "[v]", "-frames:v", nframes, "-an",
         "-c:v", "libx264", "-preset", "ultrafast" if preview else "veryfast", "-crf", "20" if preview else "12",
         "-r", FPS, "-f", "mp4", tmp])
    tmp.replace(out)  # atomic: a failed render never leaves a half-written cache file
    return out


# ------------------------------------------------------------------ fx layer
def _fog_texture(rng, w, h):
    acc = np.zeros((h, w), np.float32)
    for scale, amp in ((6, 1.0), (12, 0.5), (24, 0.25)):
        small = rng.random((scale, max(2, int(scale * w / h)))).astype(np.float32)
        acc += amp * np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-6)
    return acc


def _asset_frames(kind: str, n: int, w: int, h: int):
    """Frames from assets/fx/<kind>*.(mp4|mov) if present: premultiplied RGB float [0,1]."""
    if not FX.exists():
        return None
    cands = sorted(p for p in FX.iterdir() if p.suffix.lower() in VIDEO_EXTS and p.stem.lower().startswith(kind))
    if not cands:
        return None
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(cands[0]), "-frames:v", str(n),
                        "-vf", f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                        "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8)
    k = a.size // (w * h * 4)
    if k == 0:
        return None
    a = a[: k * w * h * 4].reshape(k, h, w, 4).astype(np.float32) / 255
    return a[..., :3] * a[..., 3:4]


def fx_events(shots: list[dict], tcfg: dict) -> list[dict]:
    ev = []
    for s in shots[1:]:
        t = s.get("transition", "cut")
        if t == "fog":
            d = float(s.get("transition_dur", tcfg.get("fog", 0.45)))
            ev.append({"kind": "fog", "t": s["start"], "d": d})
        elif t == "flash":
            ev.append({"kind": "flash", "t": s["start"], "d": float(s.get("transition_dur", tcfg.get("flash", 0.25)))})
        elif t == "sparkle":
            ev.append({"kind": "flash", "t": s["start"], "d": 0.18, "peak": 0.45})
            ev.append({"kind": "sparkle", "t": s["start"], "d": float(s.get("transition_dur", tcfg.get("sparkle", 0.6)))})
    return ev


def build_fx_layer(slug: str, events: list[dict], total_frames: int) -> Path | None:
    if not events:
        return None
    key = hashlib.md5(json.dumps([events, total_frames, "v3"]).encode()).hexdigest()[:10]
    out = cache_dir(slug) / f"fx_{key}.mp4"
    if out.exists():
        return out
    w, h = FX_W, FX_H
    rng = np.random.default_rng(7)
    fog_tex = _fog_texture(rng, w * 2, h)
    # per-frame contributions
    layers: dict[int, np.ndarray] = {}

    def add(fi, img):
        if 0 <= fi < total_frames:
            layers[fi] = np.maximum(layers.get(fi, 0), img) if fi in layers else img

    blob = None
    for e in events:
        if e["kind"] == "fog":
            span = e["d"] * 1.6  # mist a bit longer than the dissolve itself
            f0, f1 = frames(e["t"] - span / 2), frames(e["t"] + span / 2)
            asset = _asset_frames("fog", f1 - f0, w, h)
            if asset is None:
                asset = _asset_frames("smoke", f1 - f0, w, h)
            for k, fi in enumerate(range(f0, f1)):
                u = (fi - f0) / max(1, f1 - f0 - 1)
                env = math.sin(math.pi * u) ** 1.3
                if asset is not None:
                    img = asset[min(k, len(asset) - 1)] * env
                else:
                    off = int(u * w * 0.5)
                    tex = fog_tex[:, off:off + w]
                    m = (0.35 + 0.65 * tex) * env * 0.92
                    img = np.stack([m, m * 0.97, m * 0.93], -1)
                add(fi, img)
        elif e["kind"] == "flash":
            f0 = frames(e["t"]) - 1
            n = max(2, frames(e["d"]))
            peak = e.get("peak", 0.9)
            for k in range(n + 1):
                env = peak * (1 - k / n) ** 2
                add(f0 + k, np.full((h, w, 3), env, np.float32) * np.array([1, 0.98, 0.94], np.float32))
        elif e["kind"] == "sparkle":
            f0, n = frames(e["t"] - 0.08), frames(e["d"])
            asset = _asset_frames("sparkle", n, w, h)
            if blob is None:
                r = 9
                yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
                blob = np.exp(-(xx ** 2 + yy ** 2) / 6.0) + 0.6 * np.exp(-(np.minimum(abs(xx), abs(yy)) ** 2) / 0.6) * np.exp(-(xx ** 2 + yy ** 2) / 40)
                blob = (blob / blob.max()).astype(np.float32)
            P = 70
            px, py = rng.uniform(0.1, 0.9, P) * w, rng.uniform(0.15, 0.85, P) * h
            ph, vy = rng.uniform(0, 2 * math.pi, P), rng.uniform(20, 70, P)
            for k in range(n):
                if asset is not None:
                    add(f0 + k, asset[min(k, len(asset) - 1)])
                    continue
                u = k / max(1, n - 1)
                env = math.sin(math.pi * min(1, u * 1.3)) if u < 0.77 else (1 - u) / 0.23
                img = np.zeros((h, w), np.float32)
                for i in range(P):
                    a = env * (0.5 + 0.5 * math.sin(ph[i] + k * 0.9))
                    x, y = int(px[i]), int(py[i] - vy[i] * u)
                    r = blob.shape[0] // 2
                    if r <= x < w - r and r <= y < h - r:
                        img[y - r:y + r + 1, x - r:x + r + 1] = np.maximum(img[y - r:y + r + 1, x - r:x + r + 1], blob * a)
                glow = np.asarray(Image.fromarray((img * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
                m = np.clip(img + glow * 0.8 + 0.08 * env, 0, 1)
                add(f0 + k, np.stack([m, m * 0.95, m * 0.8], -1))
    # stream: black except event frames
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "ultrafast",
                          "-crf", "8", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    black = np.zeros((h, w, 3), np.uint8).tobytes()
    for fi in range(total_frames):
        img = layers.get(fi)
        p.stdin.write(black if img is None else (np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("fx layer encode failed")
    return out


# ------------------------------------------------------------------ main
def render(slug: str, preview: bool = False, audio: Path | None = None, out: Path | None = None) -> Path:
    cfg = config()
    tcfg = cfg.get("transitions", {})
    data = load_json(EDITS / f"{slug}.json")
    if not data:
        raise SystemExit(f"run plan.py {slug} first")
    w, h = (540, 960) if preview else (W, H)
    shots = [effective(s) for s in data["shots"]]
    total_frames = frames(data["duration"])

    # frame boundaries follow the voice exactly; soft transitions borrow half
    # their length from each neighbour so the cut point stays on the word.
    bounds = [frames(s["start"]) for s in shots] + [total_frames]
    bounds[0] = 0
    ext = [[0, 0] for _ in shots]  # frames before / after
    fog_d = {}
    for i in range(1, len(shots)):
        if shots[i].get("transition") == "fog":
            d = float(shots[i].get("transition_dur", tcfg.get("fog", 0.45)))
            half = max(1, frames(d / 2))
            half = min(half, (bounds[i] - bounds[i - 1]) // 2, (bounds[i + 1] - bounds[i]) // 2)
            if half >= 1:
                ext[i - 1][1] = half
                ext[i][0] = half
                fog_d[i] = 2 * half
    segs = []
    for i, s in enumerate(shots):
        n = bounds[i + 1] - bounds[i] + ext[i][0] + ext[i][1]
        segs.append(render_segment(slug, s, i, max(1, n), w, h, preview))
        print(f"\r[itt] shots rendered {i + 1}/{len(shots)}", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)

    # ---- join graph: concat runs of hard cuts, xfade across fog boundaries
    groups = [[0]]
    for i in range(1, len(shots)):
        (groups.append([i]) if i in fog_d else groups[-1].append(i))
    parts, chain = [], []
    for k in range(len(shots)):
        parts.append(f"[{k}:v]setsar=1,settb=AVTB[s{k}]")
    for gi, g in enumerate(groups):
        lbl = f"g{gi}"
        if len(g) == 1:
            parts.append(f"[s{g[0]}]setpts=PTS-STARTPTS[{lbl}]")
        else:
            ins = "".join(f"[s{k}]" for k in g)
            parts.append(f"{ins}concat=n={len(g)}:v=1:a=0,settb=AVTB,setpts=PTS-STARTPTS[{lbl}]")
    acc, acc_len = "g0", sum(bounds[k + 1] - bounds[k] + ext[k][0] + ext[k][1] for k in groups[0])
    for gi in range(1, len(groups)):
        first = groups[gi][0]
        d = fog_d[first]
        glen = sum(bounds[k + 1] - bounds[k] + ext[k][0] + ext[k][1] for k in groups[gi])
        off = (acc_len - d) / FPS
        parts.append(f"[{acc}][g{gi}]xfade=transition=fade:duration={d / FPS:.4f}:offset={off:.4f}[x{gi}]")
        acc, acc_len = f"x{gi}", acc_len - d + glen
    nseg = len(segs)
    inputs = []
    for sp in segs:
        inputs += ["-i", sp]
    fxl = build_fx_layer(slug, fx_events(shots, tcfg), total_frames)
    cur = acc
    if fxl:
        inputs += ["-i", fxl]
        parts.append(f"[{nseg}:v]scale={w}:{h}:flags=bicubic,format=gbrp[fx];[{cur}]format=gbrp[base]")
        parts.append("[base][fx]blend=all_mode=screen:shortest=1,format=yuv420p[fxd]")
        cur = "fxd"
    ass = cache_dir(slug) / "captions.ass"
    sub = ""
    if ass.exists():
        esc = str(ass).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        fd = str(font_dir()).replace(":", "\\:")
        sub = f",subtitles='{esc}':fontsdir='{fd}'"
    parts.append(f"[{cur}]vignette=angle=PI/5.5,trim=end_frame={total_frames}{sub},format=yuv420p[vout]")
    graph = ";\n".join(parts)
    gfile = cache_dir(slug) / ("graph_preview.txt" if preview else "graph.txt")
    gfile.write_text(graph)
    out = out or (ROOT / "output" / f"{slug}{'_preview' if preview else ''}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    amap = []
    if audio:
        inputs += ["-i", audio]
        amap = ["-map", f"{nseg + (1 if fxl else 0)}:a", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    log("joining + captions" + (" + audio" if audio else "") + " ...")
    run(["ffmpeg", *inputs, "-filter_complex_script", gfile, "-map", "[vout]", *amap,
         "-c:v", "libx264", "-preset", "ultrafast" if preview else "medium", "-crf", "26" if preview else "18",
         "-pix_fmt", "yuv420p", "-r", FPS, "-movflags", "+faststart", "-frames:v", total_frames, out])
    log(f"video -> {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    render(a.slug, a.preview)
