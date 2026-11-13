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
EYE_Y, MOUTH_Y = 0.32, 0.66
EYE_DX = 0.105
EXPR = ["smile", "neutral", "smirk", "worried", "sad", "shocked", "angry", "crying", "talk",
        "determined", "laugh", "embarrassed", "tired", "scared"]
K = (38, 24, 20, 255)          # dark brown ink, like the reference
WHITE = (255, 255, 255, 255)


def P(x, y):
    return (x * W * SS, y * H * SS)


# ---- expressive cartoon style: big white eyes with thick outlines + small pupils, open toothy mouths ----
OUT = int(4 * SS)          # outline width
TONGUE = (220, 90, 100, 255)
MOUTH_IN = (60, 20, 25, 255)


def ell(d, cx, cy, rx, ry, fill, outline=K, width=OUT):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=outline, width=width)


def eye(d, x, y, kind="normal", look=(0.0, 0.0), lid=0.0, side=1):
    """kind: normal|wide|closed|closed_happy|half. look: pupil offset (-1..1). lid: 0..1 upper lid droop."""
    rx = ry = 0.075 * W * SS          # round eyes
    cx, cy = P(x, y)
    if kind == "closed_happy":   # ^ ^
        d.arc([cx - rx, cy - ry * 0.6, cx + rx, cy + ry * 1.0], 200, 340, fill=K, width=OUT + 2 * SS)
        return
    if kind == "closed":        # blink / crying: curved shut line
        d.arc([cx - rx, cy - ry * 1.2, cx + rx, cy + ry * 0.4], 20, 160, fill=K, width=OUT + 2 * SS)
        return
    if kind == "wide":
        rx = ry = rx * 1.1
    ell(d, cx, cy, rx, ry, WHITE)
    pr = rx * (0.13 if kind == "wide" else 0.17)   # tiny pupil dot
    px, py = cx + look[0] * rx * 0.45, cy + look[1] * ry * 0.45
    d.ellipse([px - pr, py - pr * 1.15, px + pr, py + pr * 1.15], fill=K)
    if kind == "half":
        lid = max(lid, 0.5)
    if lid > 0:               # skin-coloured upper lid with an outline edge
        top = cy - ry - OUT
        edge = cy - ry + 2 * ry * lid
        d.rectangle([cx - rx - OUT, top - 4, cx + rx + OUT, edge], fill=SKIN[0])
        d.line([cx - rx, edge, cx + rx, edge + side * 0.0], fill=K, width=OUT)


def brow(d, x, y, tilt, side, lift=0.0, arch=False):
    """Thin expressive brow. tilt>0: inner end down (angry); tilt<0: inner end up (worried)."""
    cx, cy = P(x, y - 0.16 - lift)
    w = 0.085 * W * SS
    inner = 1 if side == "L" else -1
    dy = tilt * 0.035 * H * SS
    if arch:
        d.arc([cx - w, cy - w * 0.3 + inner * w * 0.08, cx + w, cy + w * 0.55], 205, 335, fill=K, width=int(5 * SS))
    else:
        d.line([cx - w * inner, cy - dy, cx + w * inner, cy + dy], fill=K, width=int(5 * SS))


def open_mouth(d, cx, cy, w, h, teeth=True, tongue=True, frown=False):
    """D-shaped open mouth with outline, dark inside, top teeth and a tongue."""
    box = [cx - w, cy - h, cx + w, cy + h]
    start, end = (180, 360) if frown else (0, 180)
    d.chord([box[0], box[1] - (h if not frown else 0), box[2], box[3] + (0 if not frown else h)], start, end,
            fill=MOUTH_IN, outline=K, width=OUT)
    if teeth and not frown:
        d.rectangle([cx - w * 0.78, cy - h * 0.05, cx + w * 0.78, cy + h * 0.32], fill=WHITE)
        d.chord([box[0], box[1] - h, box[2], box[3]], 0, 180, outline=K, width=OUT)
    if tongue and not frown:
        d.chord([cx - w * 0.45, cy + h * 0.35, cx + w * 0.45, cy + h * 1.15], 180, 360, fill=TONGUE)


def mouth(d, kind):
    cx, cy = P(CX + 0.04, MOUTH_Y)   # lopsided, a little to one side
    w = 0.15 * W * SS
    lw = OUT + 2 * SS
    if kind == "smile":
        import math as _m
        rot = _m.radians(-9)
        c0 = (cx, cy - w * 0.15)

        def R(px, py):
            dx, dy = px - c0[0], py - c0[1]
            return (c0[0] + dx * _m.cos(rot) - dy * _m.sin(rot), c0[1] + dx * _m.sin(rot) + dy * _m.cos(rot))
        lower = [R(c0[0] + w * _m.cos(_m.pi * t / 20), c0[1] + w * 0.62 * _m.sin(_m.pi * t / 20)) for t in range(21)]
        d.polygon(lower, fill=K)
        teeth = [R(c0[0] + w * 0.86 * _m.cos(_m.pi * t / 20), c0[1] + w * 0.28 * _m.sin(_m.pi * t / 20)) for t in range(21)]
        d.polygon(teeth, fill=WHITE)
    elif kind == "laugh":
        open_mouth(d, cx, cy - w * 0.05, w * 1.15, w * 0.62)
    elif kind == "talk":
        open_mouth(d, cx, cy, w * 0.7, w * 0.42, teeth=True)
    elif kind == "neutral":
        d.arc([cx - w * 0.55, cy - w * 0.35, cx + w * 0.55, cy + w * 0.2], 20, 160, fill=K, width=lw)
    elif kind == "smirk":
        d.arc([cx - w * 0.3, cy - w * 0.55, cx + w * 0.9, cy + w * 0.2], 15, 120, fill=K, width=lw)
    elif kind in ("sad", "crying"):
        if kind == "crying":
            d.chord([cx - w * 0.6, cy - w * 0.05, cx + w * 0.6, cy + w * 0.7], 180, 360, fill=MOUTH_IN, outline=K, width=lw)
        else:
            d.arc([cx - w * 0.5, cy, cx + w * 0.5, cy + w * 0.6], 200, 340, fill=K, width=lw)
    elif kind in ("worried", "scared"):
        d.chord([cx - w * 0.55, cy - w * 0.15, cx + w * 0.55, cy + w * 0.4], 180, 360, fill=MOUTH_IN, outline=K, width=lw)
        d.rectangle([cx - w * 0.4, cy - w * 0.0, cx + w * 0.4, cy + w * 0.12], fill=WHITE)
    elif kind == "shocked":
        ell(d, cx, cy + w * 0.1, w * 0.32, w * 0.45, MOUTH_IN)
    elif kind == "angry":
        d.rounded_rectangle([cx - w * 0.6, cy - w * 0.2, cx + w * 0.6, cy + w * 0.25], radius=10 * SS, fill=WHITE,
                            outline=K, width=lw)
        d.line([cx - w * 0.6, cy + w * 0.02, cx + w * 0.6, cy + w * 0.02], fill=K, width=int(4 * SS))
    elif kind == "determined":
        d.line([cx - w * 0.5, cy + w * 0.08, cx + w * 0.5, cy - w * 0.02], fill=K, width=lw)
    elif kind in ("embarrassed", "tired"):
        d.arc([cx - w * 0.4, cy - w * 0.3, cx + w * 0.4, cy + w * 0.2], 20, 160, fill=K, width=lw)


SKIN = [(0, 0, 0, 255)]


def face(skin, expr, blink=False):
    SKIN[0] = skin
    im = Image.new("RGBA", (W * SS, H * SS), skin)
    d = ImageDraw.Draw(im)
    xl, xr = CX - EYE_DX, CX + EYE_DX
    if blink:
        eye(d, xl, EYE_Y, "closed"); eye(d, xr, EYE_Y, "closed")
    elif expr in ("laugh", "embarrassed"):
        eye(d, xl, EYE_Y, "closed_happy"); eye(d, xr, EYE_Y, "closed_happy")
    elif expr == "crying":
        eye(d, xl, EYE_Y, "closed"); eye(d, xr, EYE_Y, "closed")
    elif expr in ("shocked", "scared"):
        eye(d, xl, EYE_Y, "wide"); eye(d, xr, EYE_Y, "wide")
    elif expr == "smirk":
        eye(d, xl, EYE_Y, "normal", look=(0.4, 0), lid=0.45); eye(d, xr, EYE_Y, "normal", look=(0.4, 0), lid=0.2)
    elif expr in ("tired", "sad"):
        lid = 0.5 if expr == "tired" else 0.3
        eye(d, xl, EYE_Y, "normal", look=(0, 0.5), lid=lid); eye(d, xr, EYE_Y, "normal", look=(0, 0.5), lid=lid)
    elif expr in ("angry", "determined"):
        eye(d, xl, EYE_Y, "normal", look=(0.15, 0), lid=0.25); eye(d, xr, EYE_Y, "normal", look=(-0.15, 0), lid=0.25)
    elif expr == "worried":
        eye(d, xl, EYE_Y, "normal", look=(-0.3, 0.1)); eye(d, xr, EYE_Y, "normal", look=(-0.3, 0.1))
    else:
        eye(d, xl, EYE_Y, "normal", look=(0.15, -0.1)); eye(d, xr, EYE_Y, "normal", look=(0.15, -0.1))
    tilt = {"angry": 1.1, "determined": 0.8, "smirk": 0.3, "sad": -0.9, "worried": -1.0, "crying": -1.0,
            "scared": -0.9, "tired": -0.3}.get(expr)
    if expr in ("shocked", "smile", "laugh", "talk", "neutral", "embarrassed"):
        lift = 0.035 if expr == "shocked" else 0.0
        brow(d, xl, EYE_Y, 0, "L", lift, arch=True)
        brow(d, xr, EYE_Y, 0, "R", lift, arch=True)
    elif tilt is not None:
        brow(d, xl, EYE_Y, tilt, "L")
        brow(d, xr, EYE_Y, tilt if expr != "smirk" else -0.4, "R")
    mouth(d, expr)
    if expr == "crying":
        for x in (xl, xr):
            cx, cy = P(x, EYE_Y + 0.03)
            d.rounded_rectangle([cx - 0.022 * W * SS, cy, cx + 0.022 * W * SS, cy + 0.24 * H * SS], radius=10 * SS,
                                fill=(110, 185, 255, 255), outline=(60, 120, 200, 255), width=3 * SS)
    if expr in ("embarrassed", "laugh"):
        for x in (xl - 0.05, xr + 0.05):
            cx, cy = P(x, EYE_Y + 0.14)
            r = 0.05 * W * SS
            d.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 0.55], fill=(240, 110, 120, 160))
    if expr == "scared":
        cx, cy = P(xr + 0.11, EYE_Y - 0.06)
        d.ellipse([cx - 14 * SS, cy, cx + 14 * SS, cy + 34 * SS], fill=(130, 195, 255, 255), outline=(60, 120, 200, 255),
                  width=3 * SS)
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
