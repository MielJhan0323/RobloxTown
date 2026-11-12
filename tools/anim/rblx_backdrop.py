#!/usr/bin/env python3
"""Paint 360-degree backdrop images (sky + clouds + mountain ranges + forest line) for the Blender stages.

  python tools/anim/rblx_backdrop.py output/models/<pack>

Writes <pack>/backdrops/<mood>.png (equirectangular, horizon in the middle). Used as the world background by
rblx.Stage, so distant scenery costs nothing to render. Original procedural painting.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 4096, 2048
HZ = H // 2  # horizon row

MOODS = {
    #          sky top           sky horizon        far mtn           near mtn          forest           ground          clouds
    "day":     ((70, 130, 230), (190, 220, 250), (140, 165, 200), (95, 130, 110), (40, 95, 50), (70, 120, 55), (255, 255, 255)),
    "morning": ((110, 160, 235), (250, 225, 190), (165, 170, 200), (110, 135, 115), (45, 100, 55), (80, 125, 60), (255, 245, 235)),
    "sunset":  ((80, 70, 140), (255, 160, 90), (150, 110, 140), (95, 75, 95), (45, 50, 55), (70, 70, 50), (255, 190, 150)),
    "dusk":    ((45, 50, 100), (220, 140, 120), (110, 95, 130), (70, 65, 95), (35, 40, 55), (45, 50, 45), (230, 170, 170)),
    "night":   ((8, 12, 35), (40, 55, 100), (40, 50, 85), (25, 32, 55), (12, 20, 28), (15, 22, 25), (90, 100, 140)),
    "rain":    ((95, 105, 120), (165, 172, 182), (120, 128, 140), (85, 98, 100), (45, 65, 55), (60, 80, 60), (200, 205, 212)),
    "dusty":   ((150, 135, 115), (225, 200, 165), (175, 155, 135), (130, 115, 100), (70, 80, 55), (110, 100, 70), (240, 225, 200)),
}


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ridge(rnd, base, amp, octaves=5, freq=3):
    """Height profile across the full 360 (wraps)."""
    phases = [(rnd.uniform(0, 6.28), freq * (2 ** o), amp / (1.8 ** o)) for o in range(octaves)]
    out = []
    for x in range(W):
        a = x / W * 2 * math.pi
        out.append(base + sum(A * math.sin(f * a + p) for p, f, A in phases))
    return out


def paint(mood, seed=7):
    top, hor, far, near, forest, ground, cloud = MOODS[mood]
    rnd = random.Random(seed)
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(HZ + 1):  # sky gradient
        t = (y / HZ) ** 1.6
        d.line([(0, y), (W, y)], fill=lerp(top, hor, t))
    for y in range(HZ, H):
        d.line([(0, y), (W, y)], fill=lerp(ground, tuple(int(c * 0.7) for c in ground), (y - HZ) / (H - HZ)))
    if mood == "night":
        for _ in range(900):
            x, y = rnd.randrange(W), rnd.randrange(int(HZ * 0.85))
            r = rnd.choice((1, 1, 1, 2))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(230, 235, 255))
    # clouds
    cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cl)
    for _ in range(40):
        cx, cy = rnd.randrange(W), rnd.randint(int(HZ * 0.35), int(HZ * 0.82))
        for _ in range(7):
            rx, ry = rnd.randint(60, 170), rnd.randint(25, 60)
            ox, oy = rnd.randint(-160, 160), rnd.randint(-25, 25)
            cd.ellipse([cx + ox - rx, cy + oy - ry, cx + ox + rx, cy + oy + ry], fill=cloud + (120 if mood != "night" else 40,))
    im.paste(cl.filter(ImageFilter.GaussianBlur(14)), (0, 0), cl.filter(ImageFilter.GaussianBlur(14)))
    # mountain ranges (far, near) + snow caps on the far range
    for col, base, amp, snow in ((far, HZ - 210, 170, mood not in ("night",)), (near, HZ - 90, 95, False)):
        prof = ridge(rnd, base, amp)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.polygon([(0, H)] + [(x, prof[x]) for x in range(0, W, 4)] + [(W, prof[-1]), (W, H)], fill=col + (255,))
        if snow:
            capc = lerp(col, (250, 250, 255), 0.75)
            lo = min(prof)
            for x in range(0, W, 4):
                if prof[x] < lo + 55:
                    ld.line([(x, prof[x]), (x, lo + 55 + (prof[x] - lo) * 0.3)], fill=capc + (255,), width=4)
        im.paste(layer, (0, 0), layer)
    # forest line: rows of pine triangles hugging the horizon
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for row, (dy, shade) in enumerate(((-6, 0.85), (10, 1.0))):
        x = rnd.randint(0, 20)
        while x < W + 40:
            h = rnd.randint(40, 95)
            w = h * rnd.uniform(0.38, 0.5)
            c = tuple(int(v * shade * rnd.uniform(0.85, 1.1)) for v in forest)
            y0 = HZ + dy
            ld.polygon([(x - w / 2, y0), (x + w / 2, y0), (x, y0 - h)], fill=c + (255,))
            x += int(w * rnd.uniform(0.45, 0.8))
    ld.rectangle([0, HZ + 4, W, HZ + 30], fill=forest + (255,))
    im.paste(layer, (0, 0), layer)
    return im.filter(ImageFilter.GaussianBlur(1.2))


def main():
    out = Path(sys.argv[1]) / "backdrops"
    out.mkdir(parents=True, exist_ok=True)
    for mood in MOODS:
        paint(mood).save(out / f"{mood}.png")
    print("backdrops ->", out)


if __name__ == "__main__":
    main()
