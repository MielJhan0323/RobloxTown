"""closet-monster ("The Monster in My Closet") - every closet has a monster; his was empty... because the
monster is him, twelve years in the past. Drone-style cameras (moves mid-shot) and lively acting.

Sets: the house from nothing_happens (bedroom + kitchen) with a wardrobe closet added in the bedroom's front-right
corner; a glowing tunnel void for the fall. Baby = Smallkid scaled down, hair hidden.
"""
import math
import random

import bpy
from mathutils import Vector

import kit
import rblx
from rblx import attach, kf
from stories.nothing_happens import H, WIN, house, text

R = math.radians
V = Vector
PACK = "alpha-mark"
HX, HY = H
CLO = V((HX + 6.6, HY - 5.0, 0))      # wardrobe centre (front faces -X)
FRONT_X = CLO.x - 1.25                # wardrobe front plane
FRIDGE = V((HX - 17.5, HY + 4.6, 0))
TUNNEL = V((-900.0, -3505.0, 0))


# ---------------------------------------------------------------- set dressing
def wardrobe(S, open_f=None, close_f=None, ajar=None, inner_glow=False, note=False):
    wood = kit.mat("wardrobe", (0.62, 0.42, 0.26), rough=0.7)
    dark = kit.mat("wardin", (0.05, 0.04, 0.04), rough=0.9)
    x, y = CLO.x, CLO.y
    kit.box((2.5, 0.25, 8.4), (x, y - 1.9, 4.2), wood, 0.04)      # sides
    kit.box((2.5, 0.25, 8.4), (x, y + 1.9, 4.2), wood, 0.04)
    kit.box((0.25, 4.0, 8.4), (x + 1.15, y, 4.2), dark, 0)       # back
    kit.box((2.5, 4.0, 0.3), (x, y, 8.3), wood, 0.04)            # top
    kit.box((2.5, 4.0, 0.3), (x, y, 0.15), wood, 0.02)           # floor
    kit.box((0.1, 3.5, 0.1), (x + 0.2, y, 7.2), kit.mat("rod", (0.6, 0.6, 0.62), metal=0.7), 0)
    for k2, col in enumerate(((0.8, 0.3, 0.3), (0.3, 0.5, 0.8), (0.9, 0.8, 0.3))):
        kit.box((0.15, 1.0, 1.6), (x + 0.25, y - 1.0 + k2 * 1.0, 6.3), kit.mat("shirt%d" % k2, col), 0.05)
    doors = {}
    for side, sy in (("L", -1), ("R", 1)):
        hinge = kit.empty((FRONT_X, y + sy * 1.9, 4.2), name="hinge" + side)
        d = kit.box((0.18, 1.88, 8.0), (FRONT_X, y + sy * 0.95, 4.2), wood, 0.03)
        knob = kit.sphere(0.13, (FRONT_X - 0.15, y + sy * 0.15, 4.2), kit.mat("knob", (0.85, 0.7, 0.3), metal=0.8), seg=10)
        attach(d, hinge)
        attach(knob, hinge)
        if note and side == "L":
            n = kit.box((0.04, 0.9, 1.1), (FRONT_X + 0.12, y - 0.95, 4.6), kit.mat("oldnote", (0.92, 0.82, 0.5)), 0)
            attach(n, hinge)
        doors[side] = hinge
        sign = -sy
        if ajar is not None:
            hinge.rotation_euler = (0, 0, R(sign * ajar))
        if open_f is not None:
            kit.key(hinge, 1, rot=(0, 0, sign * (ajar or 0)))
            kit.key(hinge, open_f, rot=(0, 0, sign * (ajar or 0)))
            kit.key(hinge, open_f + 6, rot=(0, 0, sign * 105))
        if close_f is not None:
            kit.key(hinge, close_f, rot=(0, 0, sign * 105))
            kit.key(hinge, close_f + 6, rot=(0, 0, 0))
    if inner_glow:
        kit.point((x + 0.3, y, 1.0), (0.4, 1.0, 0.8), 600, 1.0)
    return doors


def house_set(night=True, past=False):
    S = rblx.Stage(PACK, "night" if night else "morning")
    h = house(S, night)
    if night:
        bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.75
    for o in bpy.data.objects:   # the vent from the old story isn't part of this house
        if o.name.startswith(("venthole",)) or o in h.get("grille", []) or o in h.get("walkie", []):
            o.hide_render = True
    for o in h.get("grille", []) + h.get("walkie", []):
        o.hide_render = True
    h["shadow"].hide_render = True
    enclose(h)
    if past:   # twelve years ago: the room is a nursery
        nursery(S, h, night)
    return S, h


def enclose(h):
    """The house set is a 3-walled dollhouse open toward -Y. Close every room: floor, side/partition walls,
    a front wall and ceiling 7.6 studs further out, so no camera ever sees the cut edge or the void."""
    def mat_of(prefix, fallback):
        for m in bpy.data.materials:
            if m.name.startswith(prefix):
                return m
        return kit.mat(prefix, fallback, rough=0.9)
    rooms = [(HX - 8, HX + 8, mat_of("hwall", (0.4, 0.45, 0.62)), "hwood"),
             (HX - 14, HX - 8, mat_of("hhall", (0.85, 0.78, 0.6)), "hrug"),
             (HX - 30, HX - 14, mat_of("hkit", (0.95, 0.92, 0.85)), "htile")]
    y0, y1 = HY - 7.0, HY - 14.6
    cy, dy = (y0 + y1) / 2, y0 - y1
    white = mat_of("hwhite", (0.95, 0.95, 0.95))
    for x0, x1, wm, fl in rooms:
        w = x1 - x0
        floor = kit.box((w, dy, 0.3), ((x0 + x1) / 2, cy, -0.15), None, 0)
        floor.data.materials.append(mat_of(fl, (0.55, 0.36, 0.22)))
        f = kit.box((w + 0.6, 0.6, 12), ((x0 + x1) / 2, y1, 6), None, 0)
        f.data.materials.append(wm)
        for x in (x0, x1):
            sw = kit.box((0.6, dy + 0.6, 12), (x, cy, 6), None, 0)
            sw.data.materials.append(wm)
    c = kit.box((38.6, dy + 0.6, 0.4), (HX - 11, cy, 12.2), None, 0)
    c.data.materials.append(white)


def nursery(S, h, night=True):
    """Closed-in baby room: pastel walls, front wall (no cut-off edge), crib, mobile, rocking chair, toys."""
    for o in h.get("bed_furniture", []):
        o.hide_render = True
    pastel = (0.93, 0.85, 0.6)
    for m in bpy.data.materials:
        if m.name.startswith("hwall"):
            m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*pastel, 1)
    wall = kit.mat("nwall", pastel, rough=0.9)
    wood = kit.mat("nfloor", (0.55, 0.36, 0.22), rough=0.7)
    white = kit.mat("nwhite", (0.97, 0.97, 0.97), rough=0.6)
    kit.box((0.6, 3.1, 7.6), (HX - 8, HY - 3.0, 3.8), wall, 0)               # close the doorway: one room only
    kit.box((16.6, 0.35, 1.0), (HX, HY - 14.2, 0.5), white, 0)                # skirting
    for x in (HX - 8, HX + 8):                                                # skirting on the sides
        kit.box((0.35, 22, 1.0), (x + (0.35 if x < HX else -0.35), HY - 3.5, 0.5), white, 0)
    # wallpaper stripe + stars
    kit.box((16.4, 0.12, 0.6), (HX, HY + 6.65, 7.6), kit.mat("nstripe", (0.6, 0.78, 0.95)), 0)
    rnd = random.Random(3)
    star = kit.mat("nstar", (1, 0.9, 0.4), emit=1.5 if night else 0.3, emit_color=(1, 0.9, 0.4))
    for _ in range(14):
        kit.box((0.35, 0.08, 0.35), (HX + rnd.uniform(-7.5, 7.5), HY + 6.62, rnd.uniform(8.5, 11.5)), star, 0).rotation_euler = (0, R(45), 0)
    # rug
    kit.cyl(3.6, 0.05, (HX + 1, HY - 2.5, 0.03), kit.mat("nrug", (0.95, 0.7, 0.78), rough=0.95), verts=32)
    crib((HX + 1.0, HY - 1.0))
    # mobile over the crib (slowly turning)
    piv = kit.empty((HX + 1.0, HY - 1.0, 8.6), name="mobile")
    kit.cyl(0.05, 3.4, (HX + 1.0, HY - 1.0, 10.4), white, verts=6)
    bar = kit.box((3.0, 0.08, 0.08), (HX + 1.0, HY - 1.0, 8.6), white, 0)
    attach(bar, piv)
    for k2, (dx, col) in enumerate(((-1.4, (1, 0.85, 0.3)), (1.4, (0.6, 0.8, 1.0)), (0, (1, 0.6, 0.7)))):
        dy = 0 if k2 < 2 else 1.4
        st = kit.cyl(0.02, 1.0, (HX + 1.0 + dx, HY - 1.0 + dy, 8.1), white, verts=4)
        orn = kit.sphere(0.35, (HX + 1.0 + dx, HY - 1.0 + dy, 7.5), kit.mat("norn%d" % k2, col, emit=0.8 if night else 0.1,
                                                                             emit_color=col), seg=10)
        attach(st, piv)
        attach(orn, piv)
    kit.key(piv, 1, rot=(0, 0, 0))
    kit.key(piv, 400, rot=(0, 0, 360))
    for fc in piv.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    # rocking chair
    cw = kit.mat("nrock", (0.75, 0.55, 0.38), rough=0.6)
    rx, ry = HX - 5.0, HY - 8.0
    kit.box((2.4, 2.2, 0.3), (rx, ry, 1.8), cw, 0.05)
    kit.box((2.4, 0.3, 2.8), (rx, ry + 1.0, 3.3), cw, 0.05)
    kit.box((2.2, 2.0, 0.35), (rx, ry, 2.05), kit.mat("ncush", (0.6, 0.78, 0.95)), 0.12)
    for dx in (-1.1, 1.1):
        kit.box((0.2, 0.2, 1.7), (rx + dx, ry - 0.8, 0.9), cw, 0)
        kit.box((0.2, 0.2, 1.7), (rx + dx, ry + 0.8, 0.9), cw, 0)
        rk = kit.box((0.25, 3.4, 0.2), (rx + dx, ry, 0.15), cw, 0.05)
        rk.rotation_euler = (R(4), 0, 0)
    # dresser + lamp (warm nightlight)
    kit.box((2.2, 4.0, 3.2), (HX - 6.6, HY + 3.5, 1.6), kit.mat("ndress", (0.97, 0.94, 0.9)), 0.06)
    for dz in (0.9, 2.2):
        kit.box((0.1, 3.6, 0.9), (HX - 5.48, HY + 3.5, dz), kit.mat("ndrawer", (0.9, 0.86, 0.8)), 0.03)
    kit.cyl(0.25, 0.9, (HX - 6.6, HY + 4.3, 3.65), white, verts=10)
    kit.cyl(0.7, 0.8, (HX - 6.6, HY + 4.3, 4.5), kit.mat("nshade", (1, 0.85, 0.6), emit=3 if night else 0.5,
                                                           emit_color=(1, 0.85, 0.6)), verts=16, r2=0.45)
    kit.point((HX - 6.3, HY + 3.8, 4.8), (1, 0.78, 0.5), 220 if night else 60, 0.8)
    # toy blocks + teddy bear
    cols = [(0.9, 0.3, 0.3), (0.3, 0.6, 0.95), (0.95, 0.85, 0.25), (0.35, 0.8, 0.4)]
    for k2, (bx, by, bz) in enumerate(((-2.5, -4.5, 0.4), (-1.6, -4.3, 0.4), (-2.05, -4.4, 1.2), (-3.3, -5.4, 0.4))):
        blk = kit.box((0.8, 0.8, 0.8), (HX + bx, HY + by, bz), kit.mat("nblock%d" % k2, cols[k2]), 0.06)
        blk.rotation_euler = (0, 0, R(rnd.uniform(-20, 20)))
    fur = kit.mat("nbear", (0.7, 0.48, 0.28), rough=0.9)
    tx, ty = HX + 4.0, HY - 5.5
    kit.sphere(0.6, (tx, ty, 0.6), fur, seg=12)
    kit.sphere(0.45, (tx, ty - 0.05, 1.45), fur, seg=12)
    for dx in (-0.32, 0.32):
        kit.sphere(0.17, (tx + dx, ty, 1.85), fur, seg=8)
    kit.sphere(0.07, (tx - 0.15, ty - 0.42, 1.55), kit.mat("nbeye", (0.05, 0.05, 0.05)), seg=6)
    kit.sphere(0.07, (tx + 0.15, ty - 0.42, 1.55), kit.mat("nbeye", (0.05, 0.05, 0.05)), seg=6)
    if night:   # soft fill so the night nursery reads
        kit.point((HX, HY - 6, 9), (0.75, 0.8, 1.0), 160, 3.0)


def crib(loc):
    wood = kit.mat("crib", (0.95, 0.95, 0.92))
    x, y = loc[0], loc[1]
    kit.box((3.0, 4.6, 0.3), (x, y, 1.6), wood, 0.03)
    kit.box((2.8, 4.4, 0.35), (x, y, 1.9), kit.mat("cribmat", (0.6, 0.75, 0.95)), 0.1)
    for k2 in range(9):
        for sx in (-1.45, 1.45):
            kit.box((0.12, 0.12, 2.0), (x + sx, y - 2.2 + k2 * 0.55, 2.6), wood, 0)
    for sy in (-2.25, 2.25):
        kit.box((3.0, 0.15, 2.4), (x, y + sy, 2.8), wood, 0.02)
    for sx in (-1.45, 1.45):
        kit.box((0.15, 4.6, 0.15), (x + sx, y, 3.6), wood, 0)
    for sx in (-1.3, 1.3):
        for sy in (-2.1, 2.1):
            kit.box((0.2, 0.2, 1.6), (x + sx, y + sy, 0.8), wood, 0)


def baby(S, loc, expr="crying"):
    b = S.char("Smallkid", (loc[0], loc[1], loc[2]), 0, expr)
    b.root.scale = (0.5, 0.5, 0.5)
    for o in b.head.children:
        if o.name.startswith("Handle"):
            o.hide_render = True
    b.lie(1, face_down=False)
    return b


def monster(loc, color, yaw=0, eyes=2, horns=True, name="mon", scale=1.0):
    """Friendly blocky monster: round body, big googly eyes, little horns, stubby arms. Returns (root, arms)."""
    root = kit.empty(loc, name=name)
    body = kit.mat(name + "_fur", color, rough=0.8)
    x, y, z = loc
    s = scale
    parts = [kit.sphere(1.6 * s, (x, y, z + 2.0 * s), body, scale=(1, 0.9, 1.15), seg=18)]
    for k2 in range(eyes):
        ex = x + (k2 - (eyes - 1) / 2) * 0.9 * s
        parts.append(kit.sphere(0.5 * s, (ex, y - 1.35 * s, z + 2.7 * s), kit.mat("meye", (1, 1, 1), rough=0.3), seg=14))
        parts.append(kit.sphere(0.22 * s, (ex, y - 1.78 * s, z + 2.7 * s), kit.mat("mpupil", (0.05, 0.05, 0.08)), seg=10))
    parts.append(kit.box((1.2 * s, 0.2 * s, 0.35 * s), (x, y - 1.45 * s, z + 1.7 * s), kit.mat("mmouth", (0.2, 0.05, 0.08)), 0.1))
    parts.append(kit.box((0.25 * s, 0.22 * s, 0.25 * s), (x - 0.3 * s, y - 1.5 * s, z + 1.85 * s), kit.mat("mtooth", (1, 1, 1)), 0.03))
    parts.append(kit.box((0.25 * s, 0.22 * s, 0.25 * s), (x + 0.3 * s, y - 1.5 * s, z + 1.85 * s), kit.mat("mtooth", (1, 1, 1)), 0.03))
    if horns:
        for sx in (-0.8, 0.8):
            parts.append(kit.cyl(0.25 * s, 0.9 * s, (x + sx * s, y, z + 3.9 * s), kit.mat("mhorn", (0.95, 0.9, 0.75)), verts=8, r2=0.0))
    for sx in (-0.6, 0.6):
        parts.append(kit.box((0.6 * s, 0.6 * s, 0.6 * s), (x + sx * s, y - 0.2 * s, z + 0.3 * s), body, 0.2))
    arms = []
    for sx in (-1, 1):
        a = kit.empty((x + sx * 1.5 * s, y, z + 2.2 * s), name=name + "_arm")
        arm = kit.box((0.5 * s, 0.5 * s, 1.4 * s), (x + sx * 1.7 * s, y, z + 1.6 * s), body, 0.2)
        attach(arm, a)
        attach(a, root)
        arms.append(a)
    for o in parts:
        attach(o, root)
    root.rotation_euler = (0, 0, R(yaw))
    return root, arms


def bob(obj, frames, amp=0.25, period=14, start=1):
    base = V(obj.location)
    for j, f in enumerate(range(start, frames + 12, max(2, period // 2))):
        obj.location = base + V((0, 0, amp if j % 2 else 0))
        obj.keyframe_insert("location", frame=f)


def wave_arm(arm, frames, period=8, a=(40, 110)):
    for j, f in enumerate(range(1, frames + 12, period)):
        arm.rotation_euler = (0, R(a[j % 2]), 0)
        arm.keyframe_insert("rotation_euler", frame=f)


def zzz(loc, frames):
    for k2 in range(3):
        t = text("Z", (loc[0], loc[1] - 0.2 * k2, loc[2] + k2 * 0.9), size=0.6 + k2 * 0.25, color=(1, 1, 1), emit=1.5)
        kit.key(t, 1, loc=tuple(t.location))
        kit.key(t, frames, loc=(t.location.x + 0.5, t.location.y, t.location.z + 1.5))


def notes(loc, frames, n=4):
    for k2 in range(n):
        t = text("♪", (loc[0], loc[1], loc[2]), size=0.7, color=(1, 0.95, 0.6), emit=2)
        f0 = 1 + k2 * max(4, frames // (n + 1))
        kit.key(t, f0, loc=(loc[0], loc[1], loc[2]), scale=(0.2, 0.2, 0.2))
        kit.key(t, f0 + 18, loc=(loc[0] - 0.8 * (k2 % 2), loc[1] - 1.5, loc[2] + 1.6), scale=(1, 1, 1))


def clock(time, loc=(HX - 24.5, HY + 6.6, 7.5)):
    kit.box((3.2, 0.3, 1.5), (loc[0], loc[1] + 0.2, loc[2]), kit.mat("clockb", (0.08, 0.08, 0.1)), 0.06)
    return text(time, (loc[0], loc[1], loc[2] - 0.45), size=0.95, color=(1, 0.25, 0.2), emit=6)


def sticky(loc, lines=("Love you.", "Microwave", "2 min.")):
    kit.box((1.9, 0.05, 1.9), loc, kit.mat("sticky", (1, 0.92, 0.35)), 0)
    for k2, ln in enumerate(lines):
        text(ln, (loc[0], loc[1] - 0.06, loc[2] + 0.55 - k2 * 0.5), size=0.32, color=(0.15, 0.15, 0.2))


def fridge_note():
    sticky((FRIDGE.x + 0.2, FRIDGE.y - 1.32, 5.2))


def cookie_plate(loc, crumbs=False):
    kit.cyl(0.9, 0.1, loc, kit.mat("plate", (0.97, 0.97, 0.97)), verts=20)
    if crumbs:
        rnd = random.Random(2)
        for _ in range(8):
            kit.box((0.1, 0.1, 0.06), (loc[0] + rnd.uniform(-0.5, 0.5), loc[1] + rnd.uniform(-0.5, 0.5), loc[2] + 0.08),
                    kit.mat("crumb", (0.6, 0.4, 0.2)), 0)
        return
    for k2 in range(3):
        kit.cyl(0.32, 0.1, (loc[0] - 0.4 + k2 * 0.4, loc[1] + (0.2 if k2 == 1 else -0.1), loc[2] + 0.1),
                kit.mat("cookie", (0.7, 0.45, 0.2)), verts=14)


def tunnel(S, depth=80):
    rnd = random.Random(1)
    for k2 in range(28):
        z = -k2 * (depth / 28)
        col = (0.3 + 0.4 * (k2 % 3 == 0), 1.0, 0.8 - 0.3 * (k2 % 2))
        kit.torus(5 - (k2 % 4) * 0.3, 0.25, (TUNNEL.x, TUNNEL.y, z), kit.mat("ring%d" % (k2 % 3), col, emit=6, emit_color=col),
                  rot=(0, 0, rnd.uniform(0, 90)))
    kit.point((TUNNEL.x, TUNNEL.y, -depth), (0.5, 1.0, 0.8), 30000, 5.0)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.05


# ---------------------------------------------------------------- shots
def s01(k, F):  # In this town, every closet has a monster in it.  (drone flies up to the lit window)
    S, h = house_set(night=True)
    kit.point((WIN[0], HY + 3, 6), (1, 0.85, 0.5), 300, 1.0)
    S.drone([(1, (WIN[0] - 20, HY + 40, 16), (WIN[0], HY + 7, 6)),
             (F, (WIN[0] - 4, HY + 16, 7.5), (WIN[0], HY + 7, 6))], lens=30)
    return S


def s02(k, F):  # They're not scary. They're roommates.
    S, h = house_set(night=False)
    wardrobe(S, ajar=100)
    m, arms = monster((CLO.x - 0.2, CLO.y, 0.3), (0.55, 0.35, 0.85), yaw=-90, name="purp")
    bob(m, F)
    wave_arm(arms[1], F)
    kid = S.char("Prey1", (CLO.x - 4.5, CLO.y - 0.5), -90 - 180 + 360, "laugh")
    kid.key_root(1, yaw=90)
    kid.arm("R", 1, 0, 120)
    S.orbit((CLO.x - 2.5, CLO.y, 3.2), 11, 5.5, -60, -20, 1, F, lens=30)
    return S


def s03(k, F):  # Some steal socks.
    S, h = house_set(night=True)
    m, arms = monster((HX + 1, HY - 3, 0), (0.55, 0.35, 0.85), yaw=-60, name="purp")
    sock = kit.box((0.5, 0.3, 1.2), (HX + 1 + 1.9, HY - 3, 2.0), kit.mat("sock", (0.95, 0.3, 0.4)), 0.1)
    attach(sock, arms[1])
    kit.key(m, 1, loc=(HX + 1, HY - 3, 0))
    kit.key(m, F, loc=(HX + 4.5, HY - 4.5, 0))
    for j, f in enumerate(range(1, F + 2, 6)):   # tiptoe hop
        m.location.z = 0.4 if j % 2 else 0
        m.keyframe_insert("location", index=2, frame=f)
    S.drone([(1, (HX - 6, HY - 10, 4), (HX + 1, HY - 3, 2)), (F, (HX - 2, HY - 11, 6), (HX + 4, HY - 4.5, 2))], lens=30)
    return S


def s04(k, F):  # Some snore so loud the hangers rattle.
    S, h = house_set(night=True)
    wardrobe(S, ajar=100)
    m, arms = monster((CLO.x - 0.3, CLO.y, 0.3), (0.3, 0.7, 0.35), yaw=-90, name="green", scale=0.9)
    for j, f in enumerate(range(1, F + 2, 8)):
        m.scale = (1, 1, 1.08 if j % 2 else 0.95)
        m.keyframe_insert("scale", frame=f)
    zzz((CLO.x - 1.6, CLO.y, 4.5), F)
    S.cam_at(V((CLO.x - 9, CLO.y - 4, 5)), V((CLO.x, CLO.y, 3.5)), lens=30)
    S.shake(1, F, 0.06)
    return S


def s05(k, F):  # My cousin's monster does his homework.
    S, h = house_set(night=False)
    c = S.char("Cousin", (HX + 4.6, HY - 1.6, 2.7), 0, "smirk")
    c.lie(1, face_down=False)
    c.arm("L", 1, 150, -30)
    m, arms = monster((HX - 5.2, HY + 3.0, 0.3), (0.95, 0.55, 0.2), yaw=180, name="orange", scale=0.8)
    for j, f in enumerate(range(1, F + 2, 4)):
        arms[1].rotation_euler = (R(60 + (10 if j % 2 else -10)), 0, 0)
        arms[1].keyframe_insert("rotation_euler", frame=f)
    S.orbit((HX - 0.5, HY + 1.5, 2.6), 13, 6.5, -30, 15, 1, F, lens=28)
    return S


def s06(k, F):  # Badly.
    S, h = house_set(night=False)
    S.cam_at(V((HX - 5.6, HY + 3.0, 6.5)), V((HX - 5.6, HY + 5.0, 3.2)), lens=36, allow_close=True)
    return S


def s07(k, F):  # You get your monster the day you're born.
    S, h = house_set(night=False, past=True)
    baby(S, (HX + 1.0, HY - 2.4, 2.4), "laugh")
    wardrobe(S, ajar=45)
    m, arms = monster((CLO.x - 0.8, CLO.y, 0.3), (0.3, 0.75, 0.9), yaw=-90, name="blue", scale=0.75)
    wave_arm(arms[1], F)
    bob(m, F, 0.15)
    S.drone([(1, (HX - 6, HY - 10, 7), (HX + 2.5, HY - 2, 2.5)), (F, (HX - 3, HY - 8, 5), (HX + 3.5, HY - 3, 2.5))], lens=30)
    return S


def s08(k, F):  # It moves in, and it never leaves.
    S, h = house_set(night=False)
    wardrobe(S, ajar=100)
    m, arms = monster((CLO.x - 6, CLO.y - 1, 0.3), (0.3, 0.75, 0.9), yaw=-90, name="blue", scale=0.8)
    case = kit.box((1.6, 0.6, 1.2), (CLO.x - 6 + 1.6, CLO.y - 1, 1.6), kit.mat("suitcase", (0.75, 0.25, 0.2)), 0.08)
    attach(case, arms[1])
    kit.key(m, 1, loc=(CLO.x - 6, CLO.y - 1, 0.3))
    kit.key(m, F, loc=(CLO.x - 0.6, CLO.y, 0.3))
    S.cam_at(V((CLO.x - 8, CLO.y - 9, 5)), V((CLO.x - 2.5, CLO.y, 2.5)), lens=28)
    return S


def s09(k, F):  # But my closet was empty.
    S, h = house_set(night=True)
    n = S.char("Narrator", (CLO.x - 3.2, CLO.y), 90, "neutral")
    wardrobe(S, open_f=kf(4))
    n.arm("R", 1, 0)
    n.arm("R", 4, 80)
    n.arm("R", 12, 10)
    n.faces([(1, "neutral"), (kf(10), "sad")])
    S.drone([(1, (CLO.x - 10, CLO.y - 6, 5), (CLO.x - 1.5, CLO.y, 3)),
             (F, (CLO.x - 0.2, CLO.y - 0.4, 4.6), (CLO.x - 3.2, CLO.y, 4.2))], lens=26, allow_close=True)
    return S


def kitchen_alone(S, expr="sad", head_down=False):
    n = S.char("Narrator", (HX - 24.5, HY + 2.6), 180, expr)
    if head_down:
        n.lean(1, 25)
        n.arm("L", 1, 80, -20)
        n.arm("R", 1, 80, -20)
    return n


def s10(k, F):  # Dad worked late. Every night.
    S, h = house_set(night=True)
    kit.point((HX - 24.5, HY + 1, 9), (1, 0.85, 0.6), 250, 1.5)
    n = kitchen_alone(S, "sad")
    clock("9:47")
    for x in (-27.5, -21.5):
        kit.box((1.6, 1.6, 2.2), (HX + x, HY + 1.5, 1.1), kit.mat("chair", (0.5, 0.33, 0.2)), 0.04)
    S.drone([(1, (HX - 24.5, HY - 12, 8), (HX - 24.5, HY + 3, 4)), (F, (HX - 22, HY - 8, 5.5), (HX - 24.5, HY + 3, 4))], lens=30)
    return S


def s11(k, F):  # Mom worked even later.
    S, h = house_set(night=True)
    kit.point((HX - 24.5, HY + 1, 9), (1, 0.85, 0.6), 200, 1.5)
    n = kitchen_alone(S, "tired", head_down=True)
    clock("11:58")
    S.cam_at(V((HX - 21.5, HY - 7, 6)), V((HX - 24.5, HY + 3.5, 4.5)), lens=30)
    return S


def s12(k, F):  # Dinner was a sticky note on the fridge.
    S, h = house_set(night=True)
    kit.point((FRIDGE.x, FRIDGE.y - 4, 6), (1, 0.85, 0.6), 200, 1.0)
    fridge_note()
    S.drone([(1, (FRIDGE.x - 3, FRIDGE.y - 9, 5), (FRIDGE.x, FRIDGE.y, 4.5)),
             (F, (FRIDGE.x + 0.2, FRIDGE.y - 4.5, 5.3), (FRIDGE.x + 0.2, FRIDGE.y - 1.3, 5.2))], lens=34, allow_close=True)
    return S


def s13(k, F):  # "Love you. Microwave for two minutes."
    S, h = house_set(night=True)
    kit.point((FRIDGE.x, FRIDGE.y - 4, 6), (1, 0.85, 0.6), 200, 1.0)
    fridge_note()
    n = S.char("Narrator", (FRIDGE.x + 0.4, FRIDGE.y - 4.6), 180, "sad")
    n.look(1, 0, 12)
    S.cam_at(V((FRIDGE.x - 4, FRIDGE.y - 9, 6)), V((FRIDGE.x, FRIDGE.y - 2.5, 4.2)), lens=30)
    return S


def s14(k, F):  # So I really wanted a monster. Just someone to talk to.
    S, h = house_set(night=True)
    wardrobe(S)
    n = S.char("Narrator", (HX + 4.6, HY + 3.2, 0.7), -60, "sad")
    n.sit(1)
    n.look(1, -20, -5)
    S.orbit((HX + 4.5, HY - 1, 3.2), 13, 6, -50, -5, 1, F, lens=28)
    return S


def s15(k, F):  # I left cookies.
    S, h = house_set(night=True)
    wardrobe(S)
    n = S.char("Narrator", (CLO.x - 3.4, CLO.y), 90, "smile")
    n.lean(1, 0)
    n.lean(kf(8), 35)
    n.arm("R", 1, 30)
    n.arm("R", kf(8), 70)
    cookie_plate((CLO.x - 1.9, CLO.y, 0.1))
    S.cam_at(V((CLO.x - 6, CLO.y - 6, 3.5)), V((CLO.x - 2.2, CLO.y, 1.6)), lens=30)
    return S


def s16(k, F):  # I left the nightlight on.
    S, h = house_set(night=True)
    wardrobe(S)
    nl = kit.sphere(0.35, (CLO.x - 1.6, CLO.y + 2.6, 1.0), kit.mat("nl", (1, 0.85, 0.4), emit=0.0001, emit_color=(1, 0.85, 0.4)))
    sock = nl.active_material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    sock.default_value = 0
    sock.keyframe_insert("default_value", frame=kf(6) - 1)
    sock.default_value = 25
    sock.keyframe_insert("default_value", frame=kf(6))
    L = kit.point((CLO.x - 1.8, CLO.y + 2.6, 1.2), (1, 0.8, 0.45), 0, 0.3)
    L.data.keyframe_insert("energy", frame=kf(6) - 1)
    L.data.energy = 150
    L.data.keyframe_insert("energy", frame=kf(6))
    cookie_plate((CLO.x - 1.9, CLO.y, 0.1))
    S.cam_at(V((CLO.x - 7, CLO.y + 4, 3)), V((CLO.x - 1.5, CLO.y + 1, 1.5)), lens=30)
    return S


def s17(k, F):  # I even made a sign: "Monster Wanted."
    S, h = house_set(night=True)
    wardrobe(S)
    n = S.char("Narrator", (CLO.x - 4, CLO.y - 0.5), 90, "smile")
    board = kit.box((0.12, 3.2, 2.0), tuple(n.world((0, 1.5, 3.2))), kit.mat("signb", (0.97, 0.97, 0.95)), 0.03)
    t1 = text("MONSTER", tuple(n.world((0, 1.62, 3.6))), rot=(90, 0, n.root.rotation_euler.z * 57.3 - 180), size=0.5, color=(0.8, 0.15, 0.15))
    t2 = text("WANTED", tuple(n.world((0, 1.62, 2.9))), rot=(90, 0, n.root.rotation_euler.z * 57.3 - 180), size=0.5, color=(0.8, 0.15, 0.15))
    for o in (board, t1, t2):
        attach(o, n.body)
    n.arm("L", 1, 85, 10)
    n.arm("R", 1, 85, 10)
    for j, f in enumerate(range(1, F + 2, 8)):
        n.lean(f, 4 if j % 2 else -2)
    S.cam_at(V((CLO.x - 11, CLO.y - 1, 4.2)), V((CLO.x - 4, CLO.y - 0.5, 3.2)), lens=30)
    return S


def s18(k, F):  # Every night, I opened the closet. Nothing.
    S, h = house_set(night=True)
    n = S.char("Narrator", (CLO.x - 3.2, CLO.y), 90, "smile")
    wardrobe(S, open_f=kf(5))
    n.faces([(1, "smile"), (kf(12), "sad")])
    n.arm("R", 5, 80)
    n.arm("R", 14, 10)
    S.drone([(1, (CLO.x - 3, CLO.y - 0.2, 4.5), (CLO.x - 7, CLO.y, 3.5)),
             (F, (CLO.x - 0.3, CLO.y - 0.2, 4.8), (CLO.x - 6, CLO.y, 4.0))], lens=26, allow_close=True)  # from INSIDE the closet
    return S


def s19(k, F):  # The cookies were always gone by morning, though.
    S, h = house_set(night=False)
    wardrobe(S)
    cookie_plate((CLO.x - 1.9, CLO.y, 0.1), crumbs=True)
    n = S.char("Narrator", (CLO.x - 4.5, CLO.y - 1.5), 60, "shocked")
    n.look(1, 0, -25)
    S.drone([(1, (CLO.x - 2.5, CLO.y - 3, 2.2), (CLO.x - 1.9, CLO.y, 0.2)),
             (F, (CLO.x - 8, CLO.y - 7, 5), (CLO.x - 3.5, CLO.y - 1, 2.5))], lens=30, allow_close=True)
    return S


def s20(k, F):  # And Mom said when I was a baby, I never cried at night.
    S, h = house_set(night=True, past=True)
    b = baby(S, (HX + 1.0, HY - 2.4, 2.4), "smile_blink")
    wardrobe(S, ajar=4)
    S.orbit((HX + 1, HY - 1, 2.4), 10, 6.5, -40, 20, 1, F, lens=30)
    return S


def s21(k, F):  # Something always hummed me back to sleep.
    S, h = house_set(night=True, past=True)
    baby(S, (HX + 1.0, HY - 2.4, 2.4), "smile_blink")
    wardrobe(S, ajar=6)
    kit.point((CLO.x, CLO.y, 4.2), (0.5, 0.9, 1.0), 40, 0.5)
    notes((FRONT_X - 0.3, CLO.y - 1.2, 4.6), F)
    S.cam_at(V((HX - 4, HY - 9, 5.5)), V((HX + 3.5, HY - 3, 3)), lens=28)
    return S


def s22(k, F):  # On my twelfth birthday, nobody came home.
    S, h = house_set(night=True)
    n = kitchen_alone(S, "sad")
    cup = kit.cyl(0.6, 0.6, (HX - 24.5, HY + 4.3, 3.8), kit.mat("cupcake", (0.95, 0.6, 0.75)), verts=16)
    kit.cyl(0.06, 0.6, (HX - 24.5, HY + 4.3, 4.4), kit.mat("candle", (0.4, 0.7, 1.0)), verts=6)
    kit.point((HX - 24.5, HY + 4.3, 4.9), (1, 0.7, 0.3), 60, 0.1)
    kit.sphere(0.1, (HX - 24.5, HY + 4.3, 4.8), kit.mat("flame", (1, 0.7, 0.2), emit=20, emit_color=(1, 0.7, 0.2)), seg=8)
    S.drone([(1, (HX - 24.5, HY - 2.5, 5.2), (HX - 24.5, HY + 3.5, 4.2)),
             (F, (HX - 18, HY - 13, 10), (HX - 24, HY + 2, 3))], lens=30, allow_close=True)   # pull back: he's alone
    return S


def s23(k, F):  # But taped inside my closet door, I found a note.
    S, h = house_set(night=True)
    n = S.char("Narrator", (CLO.x - 3.4, CLO.y - 0.6), 90, "neutral")
    wardrobe(S, open_f=kf(3), note=True)
    n.faces([(1, "neutral"), (kf(10), "shocked")])
    n.look(kf(10), 25, 0)
    S.cam_at(V((CLO.x - 0.3, CLO.y + 1.2, 5.0)), V((CLO.x - 3.4, CLO.y - 0.6, 4.2)), lens=26, allow_close=True)
    return S


def note_close(F):
    S, h = house_set(night=True)
    kit.box((0.04, 2.6, 3.0), (HX, HY, 4), kit.mat("oldnote", (0.92, 0.82, 0.5)), 0)
    for k2, ln in enumerate(("Don't open the", "closet at", "midnight.", "Trust me.")):
        text(ln, (HX - 0.05, HY, 5.0 - k2 * 0.62), rot=(90, 0, -90), size=0.38, color=(0.15, 0.12, 0.3))
    kit.point((HX - 3, HY - 1, 5), (1, 0.9, 0.7), 120, 1.0)
    S.drone([(1, (HX - 3.2, HY - 0.8, 4.4), (HX, HY, 4.0)), (F, (HX - 2.6, HY + 0.4, 4.1), (HX, HY, 4.0))], lens=36,
            allow_close=True)
    return S


def s24(k, F):  # Old. Yellow. In my handwriting.
    return note_close(F)


def s25(k, F):  # "Don't open the closet at midnight. Trust me."
    return note_close(F)


def s26(k, F):  # I didn't write that. At least... not yet.
    S, h = house_set(night=True)
    wardrobe(S, ajar=105, note=True)
    n = S.char("Narrator", (CLO.x - 3.4, CLO.y - 0.6), 90, "worried")
    n.look(1, 0, -10)
    n.faces([(1, "worried"), (kf(F * 0.55), "scared")])
    S.drone([(1, (CLO.x - 0.3, CLO.y + 1.3, 5.2), (CLO.x - 3.4, CLO.y - 0.6, 4.4)),
             (F, (CLO.x - 0.4, CLO.y - 0.5, 4.8), (CLO.x - 3.4, CLO.y - 0.6, 4.4))], lens=28, allow_close=True)
    return S


def s27(k, F):  # At midnight, I opened it anyway.
    S, h = house_set(night=True)
    n = S.char("Narrator", (CLO.x - 3.2, CLO.y), 90, "determined")
    wardrobe(S, open_f=kf(F * 0.5), inner_glow=True)
    n.arm("L", kf(F * 0.45), 80)
    n.arm("R", kf(F * 0.45), 80)
    S.drone([(1, (CLO.x - 12, CLO.y + 4, 8), (CLO.x - 1, CLO.y, 4)), (F, (CLO.x - 8, CLO.y - 3, 4.5), (CLO.x - 1, CLO.y, 3.5))],
            lens=28)
    return S


def s28(k, F):  # I just didn't want to be alone.
    S, h = house_set(night=True)
    wardrobe(S, ajar=105, inner_glow=True)
    n = S.char("Narrator", (CLO.x - 3.0, CLO.y), 90, "sad")
    S.cam_at(V((FRONT_X + 0.5, CLO.y - 1.0, 4.9)), n.head_pt() - V((0, 0, 0.8)), lens=28, allow_close=True)
    return S


def s29(k, F):  # It wasn't empty anymore. It was a tunnel, glowing at the bottom.
    S = rblx.Stage(PACK, "night")
    tunnel(S)
    S.drone([(1, (TUNNEL.x, TUNNEL.y - 0.5, 14), (TUNNEL.x, TUNNEL.y, -10)),
             (F, (TUNNEL.x, TUNNEL.y - 0.3, 4), (TUNNEL.x, TUNNEL.y, -30))], lens=24, allow_close=True)
    return S


def s30(k, F):  # I fell, and fell,  (spiralling drone follows him down)
    S = rblx.Stage(PACK, "night")
    tunnel(S)
    n = S.char("Narrator", (TUNNEL.x, TUNNEL.y, 0), 0, "scared")
    n.arm("L", 1, 170, 30)
    n.arm("R", 1, 170, 30)
    n.leg("L", 1, 30)
    n.leg("R", 1, -20)
    keys = []
    for i in range(9):
        t = i / 8
        f = round(1 + (F - 1) * t)
        z = -t * 45
        n.key_root(f, (TUNNEL.x, TUNNEL.y, z), yaw=t * 540, tilt=20 * math.sin(t * 6))
        a = t * 4 * math.pi
        keys.append((f, (TUNNEL.x + 3.2 * math.sin(a), TUNNEL.y - 3.2 * math.cos(a), z + 6), (TUNNEL.x, TUNNEL.y, z + 2)))
    S.drone(keys, lens=26, allow_close=True)
    return S


def s31(k, F):  # and landed... in a closet.
    S, h = house_set(night=True, past=True)
    wardrobe(S)
    n = S.char("Narrator", (CLO.x - 0.1, CLO.y, 9), 90, "shocked")
    n.key_root(1, (CLO.x - 0.1, CLO.y, 9))
    n.key_root(kf(6), (CLO.x - 0.1, CLO.y, -1.2))
    n.sit(kf(6))
    kit.point((CLO.x - 0.4, CLO.y, 3), (0.5, 1, 0.8), 60, 0.5)
    S.cam_at(V((CLO.x - 0.6, CLO.y - 1.6, 6.5)), V((CLO.x, CLO.y, 2)), lens=24, allow_close=True)
    S.shake(kf(6), kf(6) + 8, 0.15)
    return S


def s32(k, F):  # My closet. Twelve years ago.
    S, h = house_set(night=True, past=True)
    baby(S, (HX + 1.0, HY - 2.4, 2.4), "crying")
    wardrobe(S, ajar=5)
    S.drone([(1, (CLO.x - 3, CLO.y - 8, 6), (CLO.x - 1, CLO.y, 4)), (F, (HX - 6, HY - 12, 10), (HX + 3, HY - 2, 2.5))], lens=28)
    return S


def s33(k, F):  # Through the crack in the door, there was a crib.  (POV from inside the closet)
    S, h = house_set(night=True, past=True)
    baby(S, (HX + 1.0, HY - 2.4, 2.4), "crying")
    wardrobe(S, ajar=85)
    S.drone([(1, (CLO.x - 0.2, CLO.y, 4.4), (CLO.x - 4, CLO.y + 0.5, 3)),
             (F, (FRONT_X + 0.3, CLO.y, 4.2), (HX + 1, HY - 1, 2.5))], lens=34, allow_close=True)
    return S


def s34(k, F):  # And a baby. Crying. Me.
    S, h = house_set(night=True, past=True)
    b = baby(S, (HX + 1.0, HY - 2.4, 2.4), "crying")
    for j, f in enumerate(range(1, F + 2, 4)):
        b.arm("L", f, 150 if j % 2 else 100)
        b.arm("R", f, 100 if j % 2 else 150)
    S.cam_at(V((HX + 1.0, HY - 5.0, 4.8)), V((HX + 1.0, HY - 2.0, 2.4)), lens=30, allow_close=True)
    return S


def s35(k, F):  # My closet was never empty. Its monster was just hiding.  (pull back from crib to the eyes in the crack)
    S, h = house_set(night=True, past=True)
    baby(S, (HX + 1.0, HY - 2.4, 2.4), "smile_blink")
    wardrobe(S, ajar=7)
    n = S.char("Narrator", (CLO.x - 0.1, CLO.y + 0.3), -90, "sad")
    kit.point((FRONT_X - 0.2, CLO.y, 5), (0.5, 0.7, 1.0), 25, 0.2)
    S.drone([(1, (HX + 1, HY - 5, 5.5), (HX + 1, HY - 1.5, 2.4)), (F, (HX - 3, HY - 10, 6), (FRONT_X, CLO.y + 0.2, 4.5))],
            lens=30)
    return S


def in_closet(S, expr="sad", hand=None):
    wardrobe(S, ajar=7)
    n = S.char("Narrator", (CLO.x - 0.1, CLO.y + 0.3), -90, expr)   # facing the doors
    kit.point((CLO.x - 0.2, CLO.y, 6.5), (0.4, 0.5, 0.9), 30, 0.3)
    return n


def s36(k, F):  # I could have knocked.
    S, h = house_set(night=True, past=True)
    n = in_closet(S, "sad")
    n.arm("R", 1, 20)
    n.arm("R", kf(F * 0.5), 95, 10)
    S.cam_at(V((CLO.x + 0.7, CLO.y - 1.3, 5.0)), V((FRONT_X, CLO.y + 0.4, 4.4)), lens=26, allow_close=True)
    return S


def s37(k, F):  # Every single night, I could have knocked.  (drone circles the closet from the room)
    S, h = house_set(night=True, past=True)
    baby(S, (HX + 1.0, HY - 2.4, 2.4), "smile_blink")
    in_closet(S, "sad")
    S.orbit((FRONT_X - 1, CLO.y, 4), 10, 5.5, -120, -40, 1, F, lens=28)
    return S


def s38(k, F):  # But if he'd had a friend, he never would've opened that door at midnight.
    S, h = house_set(night=True)
    wardrobe(S, open_f=kf(F * 0.5), inner_glow=True)
    clock("12:00", loc=(CLO.x - 5, HY + 6.6, 8))
    S.drone([(1, (CLO.x - 12, CLO.y - 8, 7), (CLO.x - 1, CLO.y, 4)), (F, (CLO.x - 7, CLO.y - 2, 4.5), (CLO.x, CLO.y, 4))], lens=28)
    return S


def s39(k, F):  # And I'd never be here to hum when he cries.
    S, h = house_set(night=True, past=True)
    baby(S, (HX + 1.0, HY - 2.4, 2.4), "smile_blink")
    n = in_closet(S, "smile")
    notes((FRONT_X - 0.3, CLO.y - 0.3, 4.8), F)
    n.look(1, 0, -10)
    S.cam_at(V((HX - 3, HY - 10, 6)), V((HX + 3.5, HY - 3, 3.2)), lens=28)
    return S


def s40(k, F):  # So I stayed in the dark.
    S, h = house_set(night=True, past=True)
    wardrobe(S, ajar=4)
    n = S.char("Narrator", (CLO.x, CLO.y + 0.3, -0.8), -90, "sad")
    n.sit(1)
    n.arm("L", 1, 75, -40)
    n.arm("R", 1, 75, -40)
    kit.point((FRONT_X - 0.2, CLO.y, 4.5), (0.5, 0.6, 1.0), 40, 0.2)
    S.drone([(1, (CLO.x - 0.6, CLO.y - 1.5, 6.5), (CLO.x, CLO.y, 2.5)), (F, (CLO.x - 0.7, CLO.y - 1.3, 4.8), (CLO.x, CLO.y, 2.2))],
            lens=26, allow_close=True)
    return S


def s41(k, F):  # I ate the cookies.
    S, h = house_set(night=True, past=True)
    cookie_plate((CLO.x - 1.9, CLO.y, 0.1))
    n = in_closet(S, "smirk")
    n.arm("R", 1, 30)
    n.arm("R", kf(F * 0.4), 70, 0)
    n.arm("R", kf(F * 0.8), 140, 0)
    S.cam_at(V((CLO.x - 6, CLO.y - 5, 3)), V((CLO.x - 1.6, CLO.y, 2)), lens=28)
    return S


def s42(k, F):  # I read the sticky notes too.
    S, h = house_set(night=True)
    kit.point((FRIDGE.x, FRIDGE.y - 4, 6), (0.6, 0.7, 1.0), 120, 1.0)
    fridge_note()
    sticky((FRIDGE.x - 0.9, FRIDGE.y - 1.32, 3.0), lines=("Sorry!", "Late again.", "Mom"))
    S.drone([(1, (FRIDGE.x + 0.2, FRIDGE.y - 4.4, 5.3), (FRIDGE.x, FRIDGE.y - 1.3, 4.6)),
             (F, (FRIDGE.x - 2.5, FRIDGE.y - 8, 5), (FRIDGE.x, FRIDGE.y - 1.3, 4.2))], lens=34, allow_close=True)
    return S


def s43(k, F):  # Tonight, he turns twelve. Nobody's coming home.
    S, h = house_set(night=True)
    cup = kit.cyl(0.6, 0.6, (HX - 24.5, HY + 4.3, 3.8), kit.mat("cupcake", (0.95, 0.6, 0.75)), verts=16)
    kit.cyl(0.06, 0.6, (HX - 24.5, HY + 4.3, 4.4), kit.mat("candle", (0.4, 0.7, 1.0)), verts=6)
    kit.sphere(0.1, (HX - 24.5, HY + 4.3, 4.8), kit.mat("flame", (1, 0.7, 0.2), emit=20, emit_color=(1, 0.7, 0.2)), seg=8)
    kit.point((HX - 24.5, HY + 4.3, 4.9), (1, 0.7, 0.3), 60, 0.1)
    clock("11:59")
    S.orbit((HX - 24.5, HY + 3, 3.6), 11, 6, -30, 30, 1, F, lens=30)
    return S


def s44(k, F):  # I'm taping a note inside the door. In my handwriting.
    S, h = house_set(night=True)
    doors = wardrobe(S, ajar=40, note=False)
    n = S.char("Narrator", (CLO.x - 0.2, CLO.y - 0.2), 90 + 30, "sad")
    nt = kit.box((0.04, 0.9, 1.1), tuple(n.world((-1.5, 1.0, 2.8))), kit.mat("oldnote", (0.92, 0.82, 0.5)), 0)
    attach(nt, n.arms["L"])
    n.arm("L", 1, 70, -20)
    n.arm("L", kf(F * 0.6), 95, -10)
    S.cam_at(V((CLO.x - 5.5, CLO.y + 4.5, 5.0)), V((CLO.x - 0.8, CLO.y - 0.5, 4)), lens=28)
    return S


def s45(k, F):  # "Don't open the closet at midnight. Trust me."
    return note_close(F)


def s46(k, F):  # He won't listen.
    S, h = house_set(night=True)
    wardrobe(S)
    clock("11:59", loc=(CLO.x - 5, HY + 6.6, 8))
    S.drone([(1, (CLO.x - 14, CLO.y - 8, 6), (CLO.x - 1, CLO.y, 4)), (F, (CLO.x - 6, CLO.y - 2, 4.4), (CLO.x - 1, CLO.y, 4.2))],
            lens=28)
    return S


def s47(k, F):  # I didn't.
    S, h = house_set(night=True)
    wardrobe(S, open_f=kf(4), inner_glow=True)
    clock("12:00", loc=(CLO.x - 5, HY + 6.6, 8))
    S.cam_at(V((CLO.x - 6, CLO.y - 2, 4.4)), V((CLO.x - 1, CLO.y, 4.2)), lens=28)
    S.flash_light((FRONT_X - 0.5, CLO.y, 4), kf(8), None, (0.5, 1, 0.8), 3000)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 48)}
