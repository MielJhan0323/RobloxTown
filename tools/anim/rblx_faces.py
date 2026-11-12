#!/usr/bin/env python3
"""Draw classic-decal style face textures for the exported Roblox characters.

  python tools/anim/rblx_faces.py output/models/<slug>/assets.json

Reads each character's skin colour from its atlas (face square from rblx_build.py) and writes
<dir>/faces/<Name>/<expr>.png for every expression in EXPR. Original drawings (simple shapes).
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SS = 4                      # supersampling
W, H = 400, 448             # face square (same aspect as the atlas UV island)
CX = 0.53                   # face centre (fraction of width), measured from the exported default face
EYE_Y, MOUTH_Y = 0.30, 0.64
EYE_DX = 0.11
EXPR = ["smile", "neutral", "smirk", "worried", "sad", "shocked", "angry", "crying", "talk",
        "determined", "laugh", "embarrassed", "tired", "scared"]
K = (12, 12, 14, 255)
WHITE = (255, 255, 255, 255)


def P(x, y):
    return (x * W * SS, y * H * SS)


def eye(d, x, y, kind="normal"):
    rx, ry = 0.042 * W * SS, 0.072 * H * SS
    cx, cy = P(x, y)
    if kind == "closed_happy":   # ^ ^
        d.arc([cx - rx * 1.4, cy - ry * 0.6, cx + rx * 1.4, cy + ry * 1.4], 200, 340, fill=K, width=int(9 * SS))
        return
    if kind == "closed":
        d.line([cx - rx * 1.3, cy, cx + rx * 1.3, cy], fill=K, width=int(8 * SS))
        return
    if kind == "wide":
        rx, ry = rx * 1.45, ry * 1.25
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=WHITE, outline=K, width=int(5 * SS))
        r = rx * 0.45
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=K)
        return
    if kind == "half":
        ry *= 0.6
        cy += ry * 0.5
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=K)
    h = rx * 0.42
    d.ellipse([cx - rx * 0.35 - h / 2, cy - ry * 0.45 - h / 2, cx - rx * 0.35 + h / 2, cy - ry * 0.45 + h / 2], fill=WHITE)


def brow(d, x, y, tilt, side, lift=0.0):
    """tilt>0: inner end down (angry); tilt<0: inner end up (sad/worried)."""
    cx, cy = P(x, y - 0.11 - lift)
    w = 0.07 * W * SS
    inner = 1 if side == "L" else -1   # inner end is toward the face centre
    dy = tilt * 0.03 * H * SS
    d.line([cx - w * inner, cy - dy, cx + w * inner, cy + dy], fill=K, width=int(14 * SS))


def mouth(d, kind):
    cx, cy = P(CX, MOUTH_Y)
    w = 0.27 * W * SS
    lw = int(12 * SS)
    if kind == "smile":
        d.chord([cx - w, cy - w * 0.55, cx + w, cy + w * 0.45], 0, 180, fill=K)
        d.chord([cx - w * 0.82, cy - w * 0.45, cx + w * 0.82, cy + w * 0.1], 0, 180, fill=WHITE)
    elif kind == "neutral":
        d.arc([cx - w * 0.6, cy - w * 0.35, cx + w * 0.6, cy + w * 0.2], 20, 160, fill=K, width=lw)
    elif kind == "smirk":
        d.arc([cx - w * 0.6, cy - w * 0.5, cx + w * 0.9, cy + w * 0.15], 10, 110, fill=K, width=lw)
        d.line([cx - w * 0.6, cy - w * 0.05, cx + w * 0.1, cy + w * 0.12], fill=K, width=lw)
    elif kind in ("sad", "crying"):
        d.arc([cx - w * 0.55, cy, cx + w * 0.55, cy + w * 0.7], 200, 340, fill=K, width=lw)
    elif kind in ("worried", "scared"):
        pts = [(cx - w * 0.55 + i * w * 0.22, cy + (w * 0.08 if i % 2 else -w * 0.08)) for i in range(6)]
        d.line(pts, fill=K, width=int(7 * SS), joint="curve")
    elif kind == "shocked":
        d.ellipse([cx - w * 0.25, cy - w * 0.3, cx + w * 0.25, cy + w * 0.4], fill=K)
    elif kind == "angry":
        d.chord([cx - w * 0.6, cy - w * 0.05, cx + w * 0.6, cy + w * 0.8], 180, 360, fill=K)
        d.rectangle([cx - w * 0.45, cy + w * 0.05, cx + w * 0.45, cy + w * 0.17], fill=WHITE)
    elif kind == "talk":
        d.ellipse([cx - w * 0.38, cy - w * 0.2, cx + w * 0.38, cy + w * 0.42], fill=K)
        d.chord([cx - w * 0.25, cy + w * 0.12, cx + w * 0.25, cy + w * 0.42], 180, 360, fill=(215, 80, 90, 255))
    elif kind == "determined":
        d.line([cx - w * 0.5, cy + w * 0.05, cx + w * 0.5, cy - w * 0.02], fill=K, width=lw)
    elif kind == "laugh":
        d.chord([cx - w, cy - w * 0.6, cx + w, cy + w * 0.9], 0, 180, fill=K)
        d.chord([cx - w * 0.85, cy - w * 0.5, cx + w * 0.85, cy + w * 0.05], 0, 180, fill=WHITE)
        d.chord([cx - w * 0.4, cy + w * 0.2, cx + w * 0.4, cy + w * 0.7], 180, 360, fill=(215, 80, 90, 255))
    elif kind in ("embarrassed", "tired"):
        d.arc([cx - w * 0.45, cy - w * 0.3, cx + w * 0.45, cy + w * 0.2], 20, 160, fill=K, width=lw)


def face(skin, expr, blink=False):
    im = Image.new("RGBA", (W * SS, H * SS), skin)
    d = ImageDraw.Draw(im)
    xl, xr = CX - EYE_DX, CX + EYE_DX
    ek = {"shocked": "wide", "scared": "wide", "laugh": "closed_happy", "embarrassed": "closed_happy",
          "tired": "half", "crying": "closed"}.get(expr, "normal")
    if blink:
        eye(d, xl, EYE_Y, "closed"); eye(d, xr, EYE_Y, "closed")
    elif expr == "smirk":
        eye(d, xl, EYE_Y, "half"); eye(d, xr, EYE_Y, "normal")
    else:
        eye(d, xl, EYE_Y, ek); eye(d, xr, EYE_Y, ek)
    tilt = {"angry": 1.0, "determined": 0.7, "smirk": 0.35, "sad": -0.8, "worried": -1.0, "crying": -1.0,
            "scared": -0.9, "shocked": 0.0, "tired": -0.3}.get(expr)
    if tilt is not None:
        lift = 0.03 if expr in ("shocked", "scared") else 0.0
        brow(d, xl, EYE_Y, tilt, "L", lift)
        brow(d, xr, EYE_Y, tilt if expr != "smirk" else -0.2, "R", lift)
    mouth(d, expr)
    if expr == "crying":
        for x in (xl, xr):
            cx, cy = P(x, EYE_Y + 0.04)
            d.rounded_rectangle([cx - 0.018 * W * SS, cy, cx + 0.018 * W * SS, cy + 0.2 * H * SS], radius=8 * SS,
                                fill=(110, 185, 255, 255))
    if expr in ("embarrassed", "laugh"):
        for x in (xl - 0.04, xr + 0.04):
            cx, cy = P(x, EYE_Y + 0.13)
            r = 0.045 * W * SS
            d.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6], fill=(240, 110, 120, 150))
    if expr == "scared":
        cx, cy = P(xr + 0.09, EYE_Y - 0.05)
        d.ellipse([cx - 14 * SS, cy, cx + 14 * SS, cy + 34 * SS], fill=(130, 195, 255, 255))
    return im.resize((W, H), Image.LANCZOS)


def decals(out):
    """Wrist marks (original simple drawings): leaf, claw, crown, marker (drawn claw), streaks (running ink)."""
    out.mkdir(parents=True, exist_ok=True)
    N = 512 * 2

    def canvas():
        return Image.new("RGBA", (N, N), (0, 0, 0, 0))

    def save(im, name):
        im.resize((512, 512), Image.LANCZOS).save(out / f"{name}.png")

    # leaf
    im = canvas(); d = ImageDraw.Draw(im)
    pts = []
    import math
    for i in range(61):
        t = i / 60 * math.pi
        pts.append((N / 2 + math.cos(t) * N * 0.36, N / 2 - math.sin(t) * math.sin(t) * N * 0.0 + (math.sin(t) * N * 0.2)))
    leaf = [(N * 0.14, N * 0.62)]
    for i in range(41):
        t = i / 40
        leaf.append((N * (0.14 + 0.72 * t), N * (0.62 - 0.42 * math.sin(math.pi * t) - 0.18 * t)))
    for i in range(41):
        t = 1 - i / 40
        leaf.append((N * (0.14 + 0.72 * t), N * (0.62 + 0.10 * math.sin(math.pi * t) - 0.18 * t)))
    d.polygon(leaf, fill=(60, 190, 70, 255), outline=(20, 90, 30, 255), width=18)
    d.line([(N * 0.14, N * 0.62), (N * 0.8, N * 0.47)], fill=(20, 100, 35, 255), width=16)
    d.line([(N * 0.06, N * 0.7), (N * 0.16, N * 0.62)], fill=(20, 100, 35, 255), width=22)
    save(im, "leaf")
    # claw: three slashes
    for name, col, outl in (("claw", (220, 30, 35, 255), (90, 0, 0, 255)), ("marker", (15, 15, 18, 255), None)):
        im = canvas(); d = ImageDraw.Draw(im)
        for k in range(3):
            x = N * (0.28 + k * 0.2)
            poly = [(x + N * 0.1, N * 0.12), (x + N * 0.04, N * 0.13), (x - N * 0.12, N * 0.86), (x - N * 0.07, N * 0.88)]
            d.polygon(poly, fill=col, outline=outl, width=10 if outl else 0)
        if name == "marker":
            im = im.filter(ImageFilter.GaussianBlur(3))
        save(im, name)
    # crown
    im = canvas(); d = ImageDraw.Draw(im)
    c = [(N * 0.12, N * 0.75), (N * 0.12, N * 0.3), (N * 0.31, N * 0.5), (N * 0.5, N * 0.18), (N * 0.69, N * 0.5),
         (N * 0.88, N * 0.3), (N * 0.88, N * 0.75)]
    d.polygon(c, fill=(255, 205, 40, 255), outline=(150, 95, 0, 255), width=20)
    d.rectangle([N * 0.12, N * 0.72, N * 0.88, N * 0.84], fill=(240, 175, 20, 255), outline=(150, 95, 0, 255), width=16)
    for x, col in ((0.3, (230, 40, 60)), (0.5, (60, 120, 255)), (0.7, (230, 40, 60))):
        d.ellipse([N * (x - 0.05), N * 0.55, N * (x + 0.05), N * 0.65], fill=col + (255,))
    save(im, "crown")
    # streaks: the marker claw running down
    im = canvas(); d = ImageDraw.Draw(im)
    for k in range(3):
        x = N * (0.25 + k * 0.22)
        d.rounded_rectangle([x - N * 0.035, N * 0.05, x + N * 0.035, N * (0.75 + 0.08 * (k % 2))], radius=30, fill=(20, 20, 24, 210))
        d.ellipse([x - N * 0.05, N * (0.7 + 0.08 * (k % 2)), x + N * 0.05, N * (0.82 + 0.08 * (k % 2))], fill=(20, 20, 24, 220))
    save(im.filter(ImageFilter.GaussianBlur(4)), "streaks")

    # branch shadow (spooky claw-like silhouette seen through a curtain) - nothing-happens
    import math as _m
    import random as _r
    rnd = _r.Random(5)
    im = canvas(); d = ImageDraw.Draw(im)

    def limb(x, y, ang, length, w, depth):
        x2, y2 = x + _m.cos(ang) * length, y + _m.sin(ang) * length
        d.line([(x, y), (x2, y2)], fill=(10, 12, 25, 235), width=int(w))
        if depth:
            for k in range(rnd.choice((2, 3))):
                limb(x2, y2, ang + rnd.uniform(-0.75, 0.75), length * rnd.uniform(0.55, 0.75), w * 0.62, depth - 1)
    limb(N * 1.02, N * 0.55, _m.pi + 0.15, N * 0.42, 60, 4)
    save(im.filter(ImageFilter.GaussianBlur(9)), "branch_shadow")
    # "ghost map": paper with a house plan, red X's and question marks
    im = Image.new("RGBA", (N, N), (246, 240, 220, 255)); d = ImageDraw.Draw(im)
    for r in [(0.1, 0.15, 0.55, 0.6), (0.55, 0.15, 0.9, 0.45), (0.55, 0.45, 0.9, 0.85), (0.1, 0.6, 0.55, 0.85)]:
        d.rectangle([N * r[0], N * r[1], N * r[2], N * r[3]], outline=(40, 50, 110, 255), width=12)
    for x, y in ((0.3, 0.35), (0.75, 0.3), (0.72, 0.68), (0.32, 0.73)):
        cx, cy = N * x, N * y
        d.line([cx - 40, cy - 40, cx + 40, cy + 40], fill=(210, 30, 30, 255), width=16)
        d.line([cx - 40, cy + 40, cx + 40, cy - 40], fill=(210, 30, 30, 255), width=16)
    d.line([(N * 0.3, N * 0.35), (N * 0.75, N * 0.3), (N * 0.72, N * 0.68), (N * 0.32, N * 0.73)], fill=(210, 30, 30, 200), width=7)
    for x, y in ((0.18, 0.22), (0.82, 0.55), (0.45, 0.9)):
        d.text((N * x, N * y), "?", fill=(210, 30, 30, 255))
        d.ellipse([N * x - 30, N * y - 30, N * x + 30, N * y + 30], outline=(210, 30, 30, 255), width=8)
    save(im, "ghostmap")


def main():
    meta_p = Path(sys.argv[1])
    meta = json.loads(meta_p.read_text())
    out = meta_p.parent / "faces"
    for name, m in meta.items():
        a = Image.open(m["atlas"]).convert("RGBA")
        aw, ah = a.size
        u0, u1, v0, v1 = m["face_uv"]
        skin = a.getpixel((round(u0 * aw) + 3, round((1 - v1) * ah) + 3))
        skin = tuple(skin[:3]) + (255,)
        d = out / name
        d.mkdir(parents=True, exist_ok=True)
        for e in EXPR:
            face(skin, e).save(d / f"{e}.png")
            if e not in ("laugh", "embarrassed", "crying"):
                face(skin, e, blink=True).save(d / f"{e}_blink.png")
    decals(meta_p.parent / "decals")
    print("faces ->", out)


if __name__ == "__main__":
    main()
