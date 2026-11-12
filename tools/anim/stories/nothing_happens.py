"""nothing-happens ("Nothing Happens Here") - everything is normal; spooky build-up, ordinary payoff.

Sets: A = exported town street (road x -8..8, sidewalks to +-14, shops x +-15..25, y -3580..-3420)
      B = house built here at H (bedroom / hallway / kitchen open toward -Y like a dollhouse, front yard + tree at +Y).
Characters face -Y at yaw 0; kit.camera yaw 0 sits at -Y, yaw 180 at +Y.
"""
import math
import random

import bpy
from mathutils import Vector

import kit
import rblx
from rblx import attach, kf

R = math.radians
V = Vector
H = (-520.0, -3505.0)      # bedroom centre
WIN = (H[0] - 2.0, H[1] + 7.0, 6.0)   # window centre (back wall)
PACK = "alpha-mark"         # exported model pack


# ---------------------------------------------------------------- helpers
def img_plane(path, size, loc, rot=(90, 0, 0), alpha=True, emit=0.0, name="img"):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot])
    p = bpy.context.active_object
    p.name = name
    p.scale = (size[0], size[1], 1)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.blend_method = "HASHED" if alpha else "OPAQUE"
    m.shadow_method = "NONE"
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(str(path), check_existing=True)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if alpha:
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    if emit:
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color" if "Emission Color" in b.inputs else "Emission"])
        b.inputs["Emission Strength"].default_value = emit
    p.data.materials.append(m)
    return p


def text(body, loc, rot=(90, 0, 0), size=1.0, color=(1, 1, 1), emit=0.0):
    bpy.ops.object.text_add(location=loc, rotation=[R(a) for a in rot])
    t = bpy.context.object
    t.data.body = body
    t.data.size = size
    t.data.extrude = 0.04
    t.data.align_x = "CENTER"
    t.data.materials.append(kit.mat("txt" + body, color, emit=emit, emit_color=color if emit else None))
    return t


def decal_path(name):
    return rblx.ROOT / "output" / "models" / PACK / "decals" / f"{name}.png"


def sway(obj, frames, amp=(3, 0, 4), period=24, seed=0, start=1):
    """Keyed sway (branches in the wind)."""
    rnd = random.Random(seed)
    base = Vector(obj.rotation_euler)
    f = start
    while f <= frames + 15:
        k = math.sin(f / period * 2 * math.pi + seed)
        obj.rotation_euler = (base.x + R(amp[0] * k + rnd.uniform(-0.6, 0.6)), base.y + R(amp[1] * k),
                              base.z + R(amp[2] * k + rnd.uniform(-0.6, 0.6)))
        obj.keyframe_insert("rotation_euler", frame=f)
        f += 4


# ---------------------------------------------------------------- set B: the house
def house(S, night=True):
    hx, hy = H
    out = {}
    wood = kit.mat("hwood", (0.55, 0.36, 0.22), rough=0.7)
    wall = kit.mat("hwall", (0.55, 0.62, 0.85) if night else (0.72, 0.8, 0.98), rough=0.9)
    hall_wall = kit.mat("hhall", (0.85, 0.78, 0.6), rough=0.9)
    kit_wall = kit.mat("hkit", (0.95, 0.92, 0.85), rough=0.9)
    white = kit.mat("hwhite", (0.95, 0.95, 0.95), rough=0.6)
    # floors
    kit.box((16, 14, 0.3), (hx, hy, -0.15), wood, 0)
    kit.box((6, 14, 0.3), (hx - 11, hy, -0.15), kit.mat("hrug", (0.5, 0.22, 0.2)), 0)
    kit.box((16, 14, 0.3), (hx - 22, hy, -0.15), kit.mat("htile", (0.85, 0.85, 0.8), rough=0.4), 0)
    # back wall with a window hole (bedroom), back walls for hall + kitchen
    wx0, wx1 = WIN[0] - 2.5, WIN[0] + 2.5
    by = hy + 7
    kit.box((wx0 - (hx - 8), 0.6, 12), ((hx - 8 + wx0) / 2, by, 6), wall, 0)
    kit.box(((hx + 8) - wx1, 0.6, 12), ((wx1 + hx + 8) / 2, by, 6), wall, 0)
    kit.box((5, 0.6, 3.5), (WIN[0], by, 1.75), wall, 0)
    kit.box((5, 0.6, 3.5), (WIN[0], by, 10.25), wall, 0)
    kit.box((5.4, 0.8, 0.3), (WIN[0], by - 0.1, 3.5), white, 0.03)       # sill
    for dx in (-2.6, 2.6):
        kit.box((0.25, 0.8, 5.2), (WIN[0] + dx, by, 6), white, 0)
    kit.box((5.4, 0.8, 0.25), (WIN[0], by, 8.6), white, 0)
    kit.box((0.18, 0.7, 5), (WIN[0], by, 6), white, 0)                    # mullion
    glass = kit.mat("hglass", (0.6, 0.75, 1.0), rough=0.05, alpha=0.18)
    kit.box((5, 0.08, 5), (WIN[0], by, 6), glass, 0)
    kit.box((6, 0.6, 12), (hx - 11, by, 6), hall_wall, 0)
    kit.box((16, 0.6, 12), (hx - 22, by, 6), kit_wall, 0)
    # side walls + inner walls with doorways (open toward -Y)
    kit.box((0.6, 14, 12), (hx + 8, hy, 6), wall, 0)
    for x, m in ((hx - 8, wall), (hx - 14, hall_wall)):
        kit.box((0.6, 8.5, 12), (x, hy + 2.75, 6), m, 0)
        kit.box((0.6, 3.0, 4.5), (x, hy - 3.0, 9.75), m, 0)
        kit.box((0.6, 2.0, 12), (x, hy - 6.0, 6), m, 0)
    kit.box((0.6, 14, 12), (hx - 30, hy, 6), kit_wall, 0)
    # ceiling (keeps the moon out) + roof seen from the yard
    kit.box((38.6, 14.6, 0.4), (hx - 11, hy, 12.2), white, 0)
    roof = kit.mat("hroof", (0.45, 0.2, 0.18), rough=0.8)
    for sgn in (-1, 1):
        r = kit.box((39.5, 9.5, 0.6), (hx - 11, hy + sgn * 3.6, 15.0), roof, 0.03)
        r.rotation_euler = (R(-sgn * 35), 0, 0)
    # bedroom furniture
    kit.box((5, 8, 1.4), (hx + 4.6, hy + 1.6, 0.7), wood, 0.05)                        # bed frame
    kit.box((4.8, 7.8, 0.8), (hx + 4.6, hy + 1.6, 1.8), white, 0.1)                     # mattress
    kit.box((5, 0.5, 4.2), (hx + 4.6, hy + 5.6, 2.1), wood, 0.05)                       # headboard
    kit.box((2.8, 1.2, 0.6), (hx + 4.6, hy + 4.6, 2.45), white, 0.2)                    # pillow
    out["blanket"] = kit.box((4.9, 4.8, 0.5), (hx + 4.6, hy + 0.2, 2.35), kit.mat("blanket", (0.35, 0.45, 0.85)), 0.12)
    kit.box((2.2, 2.0, 2.4), (hx + 0.9, hy + 5.6, 1.2), wood, 0.05)                     # nightstand
    out["clock"] = text("3:00", (hx + 0.9, hy + 4.55, 2.75), size=0.8, color=(1, 0.1, 0.08), emit=6)
    kit.box((1.8, 0.6, 1.0), (hx + 0.9, hy + 4.9, 2.9), kit.mat("clockbody", (0.05, 0.05, 0.06)), 0.05)
    kit.box((5, 2.6, 0.3), (hx - 5.2, hy + 5.4, 3.0), wood, 0.03)                       # desk
    for lx in (-2.2, 2.2):
        kit.box((0.3, 2.2, 3.0), (hx - 5.2 + lx, hy + 5.4, 1.5), wood, 0)
    out["map"] = img_plane(decal_path("ghostmap"), (2.4, 1.8), (hx - 5.6, hy + 5.0, 3.17), rot=(0, 0, 0), alpha=False,
                           name="ghostmap")
    kit.box((1.6, 1.6, 0.12), (hx - 3.6, hy + 5.4, 3.2), kit.mat("paper", (0.97, 0.95, 0.88)), 0)
    kit.box((1.6, 1.4, 2.0), (hx - 5.2, hy + 3.2, 1.0), wood, 0.03)                     # chair
    # curtains (closed) - two halves, animatable
    cur = kit.mat("curtain", (0.55, 0.15, 0.2), rough=0.9)
    out["curL"] = kit.box((2.7, 0.25, 5.6), (WIN[0] - 1.3, by - 0.5, 6), cur, 0.05)
    out["curR"] = kit.box((2.7, 0.25, 5.6), (WIN[0] + 1.3, by - 0.5, 6), cur, 0.05)
    kit.box((7.5, 0.2, 0.2), (WIN[0], by - 0.5, 8.9), white, 0)
    # branch shadow seen on the curtain
    out["shadow"] = img_plane(decal_path("branch_shadow"), (5.2, 5.2), (WIN[0], by - 0.66, 6), rot=(90, 0, 0),
                              name="branch_shadow")
    # vent (right wall) + walkie-talkie hidden inside
    vx = hx + 7.65
    vent_y, vent_z = hy - 4.0, 4.3
    kit.box((0.15, 2.2, 1.4), (vx + 0.1, vent_y, vent_z), kit.mat("venthole", (0.02, 0.02, 0.03)), 0)
    out["grille"] = []
    gm = kit.mat("grille", (0.8, 0.8, 0.82), metal=0.5, rough=0.4)
    out["grille"].append(kit.box((0.12, 2.4, 0.14), (vx, vent_y, vent_z + 0.75), gm, 0))
    out["grille"].append(kit.box((0.12, 2.4, 0.14), (vx, vent_y, vent_z - 0.75), gm, 0))
    for k in range(5):
        out["grille"].append(kit.box((0.1, 2.3, 0.12), (vx - 0.02, vent_y, vent_z - 0.5 + k * 0.25), gm, 0))
    wk = kit.mat("walkie", (0.1, 0.12, 0.1))
    out["walkie"] = [kit.box((0.4, 0.8, 1.0), (vx + 0.1, vent_y, vent_z - 0.1), wk, 0.05),
                     kit.cyl(0.06, 0.8, (vx + 0.1, vent_y + 0.25, vent_z + 0.7), wk, verts=8),
                     kit.sphere(0.08, (vx - 0.12, vent_y - 0.2, vent_z + 0.2), kit.mat("led", (0.1, 1, 0.2), emit=8,
                                                                                     emit_color=(0.1, 1, 0.2)), seg=8)]
    # hallway: pictures + a little night light
    for k, col in enumerate(((0.8, 0.5, 0.3), (0.3, 0.6, 0.8))):
        kit.box((1.8, 0.15, 1.4), (hx - 12 + k * 2.2, by - 0.4, 6.5), kit.mat("pic%d" % k, col), 0.02)
    # kitchen: counter, cookie jar, fridge with hinged door
    kit.box((9, 2.6, 3.2), (hx - 24.5, hy + 5.4, 1.6), kit.mat("counter", (0.92, 0.92, 0.9)), 0.04)
    kit.box((9.2, 2.8, 0.3), (hx - 24.5, hy + 5.4, 3.3), kit.mat("ctop", (0.3, 0.3, 0.35)), 0.02)
    out["jar"] = kit.cyl(0.6, 1.2, (hx - 22, hy + 5.2, 4.05), kit.mat("jar", (0.8, 0.9, 1.0), alpha=0.5), verts=16)
    fx, fy = hx - 17.5, hy + 4.6
    fr = kit.mat("fridge", (0.92, 0.94, 0.96), rough=0.3)
    kit.box((3.2, 2.6, 7.6), (fx, fy + 0.3, 3.8), fr, 0.08)
    kit.box((2.8, 0.1, 7.0), (fx, fy - 0.98, 3.8), kit.mat("fridgein", (1, 0.97, 0.85), emit=3,
                                                            emit_color=(1, 0.95, 0.8)), 0)
    hinge = kit.empty((fx - 1.6, fy - 1.05, 3.8), name="fridge_hinge")
    door = kit.box((3.2, 0.3, 7.6), (fx, fy - 1.15, 3.8), fr, 0.06)
    attach(door, hinge)
    out["fridge_hinge"] = hinge
    out["fridge_light"] = kit.point((fx, fy - 2.5, 4.5), (1, 0.92, 0.75), 0, 2.0)
    for k in range(3):
        kit.box((0.4, 0.2, 0.8), (fx + 0.9 - k * 0.15, fy - 0.9, 3.0 + k * 1.6), kit.mat("milk", (0.95, 0.95, 1.0)), 0.04)
    # front yard + tree (outside, +Y) with a branch reaching to the window
    kit.box((90, 50, 0.4), (hx - 10, hy + 32, -0.2), kit.mat("grass", (0.25, 0.55, 0.22), rough=0.9), 0)
    tx, ty = WIN[0] + 1.5, hy + 13
    bark = kit.mat("bark", (0.32, 0.2, 0.12), rough=0.9)
    leaves = kit.mat("leaves", (0.15, 0.42, 0.16), rough=0.8)
    kit.cyl(1.0, 16, (tx, ty, 8), bark, verts=10)
    for k in range(9):
        a = k / 9 * 2 * math.pi
        kit.box((4.5, 4.5, 4.5), (tx + math.cos(a) * 3.2, ty + math.sin(a) * 3.2, 16 + (k % 3)), leaves, 0.2)
    piv = kit.empty((tx, ty, 6.2), name="branch_pivot")
    L = (V((WIN[0] - 0.6, by + 0.45, 6.6)) - V((tx, ty, 6.2)))
    br = kit.cyl(0.28, L.length, tuple(V((tx, ty, 6.2)) + L / 2), bark, verts=8)
    br.rotation_euler = L.to_track_quat("Z", "Y").to_euler()
    attach(br, piv)
    tip = V((tx, ty, 6.2)) + L
    for k in range(4):
        tw = kit.cyl(0.1, 1.6, tuple(tip + V((math.cos(k) * 0.6, -0.1, math.sin(k * 1.7) * 0.6))), bark, verts=6,
                     rot=(70 + k * 25, 0, k * 40))
        attach(tw, piv)
        lf = kit.box((0.9, 0.9, 0.9), tuple(tip + V((math.cos(k) * 1.2, 0.2, math.sin(k * 1.7) * 1.1))), leaves, 0.1)
        attach(lf, piv)
    out["branch"] = piv
    # night lighting: moonlight through the window + cool fill
    if night:
        kit.spot((WIN[0] + 3, hy + 30, 16), (WIN[0], hy + 2, 1), (0.55, 0.65, 1.0), 9000, 30, 0.6, 0.6)
        kit.point((hx, hy - 2, 9), (0.4, 0.5, 1.0), 120, 3.0)
        kit.point((hx - 11, hy - 2, 9), (0.4, 0.5, 1.0), 60, 3.0)
        kit.point((hx - 22, hy - 2, 9), (0.4, 0.5, 1.0), 60, 3.0)
    else:
        for x in (hx, hx - 11, hx - 22):
            kit.point((x, hy - 2, 10), (1, 0.92, 0.8), 600, 3.0)
        kit.spot((WIN[0] + 3, hy + 30, 16), (WIN[0], hy + 2, 1), (1, 0.85, 0.6), 14000, 30, 0.6, 0.6)
    return out


def flashlight(c, side="R", on_f=1, power=1500):
    """Flashlight in the hand: a small cylinder + spot light pointing along the arm."""
    arm = c.arms[side]
    hand = c.world((1.5 if side == "R" else -1.5, 0.2, c.meta["shoulder"] - c.meta["arm_len"] - 0.1))
    body = kit.cyl(0.18, 0.9, tuple(hand), kit.mat("flash", (0.15, 0.15, 0.18)), verts=10)
    attach(body, arm)
    d = bpy.data.lights.new("flash", "SPOT")
    d.energy = 0
    d.spot_size = R(35)
    d.spot_blend = 0.5
    d.color = (1, 0.95, 0.8)
    L = bpy.data.objects.new("flash", d)
    bpy.context.collection.objects.link(L)
    L.location = hand
    L.rotation_euler = (0, 0, 0)   # spot points down -Z = along the hanging arm
    attach(L, arm)
    d.keyframe_insert("energy", frame=max(0, on_f - 1))
    d.energy = power
    d.keyframe_insert("energy", frame=on_f)
    return L


def night_house():
    S = rblx.Stage(PACK, "night")
    return S, house(S, True)


def day_house():
    S = rblx.Stage(PACK, "morning")
    return S, house(S, False)


# ---------------------------------------------------------------- street props (set A)
def street_props(S, spooky=False):
    out = {}
    # dentist sign + giant tooth on the shop at x 15..25, y -3527..-3513 (facade faces -X)
    if not spooky:
        text("DENTIST", (14.7, -3520, 8.6), rot=(90, 0, -90), size=1.6, color=(0.1, 0.35, 0.8))
        kit.box((0.3, 8, 2.4), (14.85, -3520, 9.1), kit.mat("signboard", (0.97, 0.97, 0.97)), 0.05)
        t = kit.mat("tooth", (1, 1, 1), rough=0.3)
        kit.box((0.8, 2.4, 2.2), (14.4, -3520, 12.4), t, 0.4)
        for dy in (-0.7, 0.7):
            kit.box((0.8, 0.9, 1.4), (14.4, -3520 + dy, 10.9), t, 0.35)
    # well (sidewalk, x -11)
    stone = kit.mat("stone", (0.55, 0.55, 0.58), rough=0.9)
    kit.cyl(1.6, 2.4, (-11, -3540, 1.2), stone, verts=16)
    kit.cyl(1.25, 0.2, (-11, -3540, 2.3), kit.mat("water", (0.1, 0.3, 0.45), rough=0.1), verts=16)
    gold = kit.mat("penny", (0.85, 0.5, 0.2), metal=0.8, rough=0.3)
    rnd = random.Random(3)
    for k in range(18):
        kit.cyl(0.18, 0.05, (-11 + rnd.uniform(-0.9, 0.9), -3540 + rnd.uniform(-0.9, 0.9), 2.42), gold, verts=10)
    for dx in (-1.5, 1.5):
        kit.box((0.25, 0.25, 4), (-11 + dx, -3540, 4.2), kit.mat("wellwood", (0.45, 0.3, 0.2)), 0)
    kit.box((3.8, 2.2, 0.3), (-11, -3540, 6.3), kit.mat("wellroof", (0.6, 0.2, 0.15)), 0.03)
    # fortune teller table (sidewalk, x 11)
    kit.box((3.2, 2.2, 0.25), (11, -3556, 2.6), kit.mat("cloth", (0.4, 0.1, 0.5)), 0.03)
    kit.box((3.0, 2.0, 2.5), (11, -3556, 1.25), kit.mat("cloth2", (0.3, 0.05, 0.4)), 0)
    out["ball"] = kit.sphere(0.7, (11, -3556.3, 3.45), kit.mat("crystal", (0.6, 0.5, 1.0), emit=2.5,
                                                                emit_color=(0.6, 0.4, 1.0), alpha=0.85))
    text("FORTUNES", (11, -3557.2, 0.9), size=0.45, color=(1, 0.85, 0.3), emit=1)
    # pigeon (sidewalk, x 10, y -3500)
    pg = kit.mat("pigeon", (0.55, 0.57, 0.65), rough=0.6)
    body = kit.box((0.7, 1.1, 0.7), (10, -3500, 0.95), pg, 0.15)
    head = kit.box((0.45, 0.45, 0.45), (10, -3500.6, 1.45), kit.mat("pighead", (0.35, 0.45, 0.5)), 0.1)
    kit.box((0.12, 0.25, 0.12), (10, -3500.9, 1.4), kit.mat("beak", (0.95, 0.6, 0.2)), 0)
    out["pigeon"] = (body, head)
    return out


# ---------------------------------------------------------------- shots
def s01(k, F):  # In this town,  (street, kids walking)
    S = rblx.Stage(PACK, "morning")
    street_props(S)
    for nm, x, y in (("Narrator", 11, -3478), ("Smallkid", 12.6, -3479), ("Crowd2", 9.6, -3472), ("Prey1", 12.4, -3468)):
        c = S.char(nm, (x, y), 0, "smile")
        c.walk(1, F, (x, y - 5))
    S.cam(V((11.0, -3478, 3.0)), dist=16, yaw=-28, height=5.0, lens=38, fstop=None)
    return S


def s02(k, F):  # everything is normal. (kids wave)
    S = rblx.Stage(PACK, "morning")
    for i, (nm, x) in enumerate((("Crowd2", 9.0), ("Narrator", 11.2), ("Smallkid", 13.0))):
        c = S.char(nm, (x, -3500), 0, "laugh" if i == 1 else "smile")
        f = 1
        j = 0
        while f <= F:
            c.arm("R", f, 0, 150 if j % 2 else 120)
            f += 8
            j += 1
    S.cam(V((11.0, -3500, 3.2)), dist=11, yaw=-5, height=4.0, lens=38)
    return S


def s03(k, F):  # The haunted mansion
    S = rblx.Stage(PACK, "night")
    kit.point((13, -3520, 6), (0.4, 1.0, 0.5), 400, 1.0)
    kit.point((12, -3516, 14), (0.7, 0.3, 1.0), 600, 2.0)
    S.cam_at(V((-2, -3532, 1.5)), V((18, -3520, 9)), lens=26, fstop=None)
    S.shake(1, F, 0.04)
    return S


def s04(k, F):  # is just a dentist's office.
    S = rblx.Stage(PACK, "day")
    street_props(S)
    c = S.char("Prey3", (13.4, -3520), -90, "laugh")
    c.arm("R", 1, 0, 140)
    c.arm("L", 1, 0, 140)
    S.cam_at(V((2, -3526, 4.0)), V((14.5, -3520, 7.5)), lens=28, fstop=None)
    return S


def s05(k, F):  # The cursed well is full of pennies.
    S = rblx.Stage(PACK, "day")
    street_props(S)
    c = S.char("Crowd2", (-11, -3543.3), 0 + 180, "smile")
    c.arm("R", 1, 20)
    c.arm("R", kf(12), 120)
    c.arm("R", kf(20), 60)
    coin = kit.cyl(0.18, 0.05, tuple(c.world((1.5, 0.6, 4.6))), kit.mat("penny2", (0.85, 0.5, 0.2), metal=0.8), verts=10)
    kit.key(coin, kf(12), loc=tuple(coin.location))
    kit.key(coin, kf(22), loc=(-11.2, -3541.5, 6.0))
    kit.key(coin, kf(32), loc=(-11.0, -3540, 2.45))
    S.cam(V((-11, -3541.5, 2.8)), dist=10, yaw=160, height=5.5, lens=34)
    return S


def s06(k, F):  # The fortune teller only predicts rain,
    S = rblx.Stage(PACK, "dusk")
    p = street_props(S)
    c = S.char("Crowd1", (11, -3554.3), 180, "smirk")
    c.arm("L", 1, 70, -15)
    c.arm("R", 1, 70, -15)
    f = 1
    while f <= F:
        c.arm("L", f, 70, -15 + (6 if (f // 8) % 2 else -6))
        c.arm("R", f, 70, -15 + (-6 if (f // 8) % 2 else 6))
        f += 8
    kit.point((11, -3556.5, 3.6), (0.6, 0.4, 1.0), 120, 0.5)
    S.cam(V((11, -3555.5, 3.6)), dist=8, yaw=160, height=4.4, lens=36)
    return S


def s07(k, F):  # and she's usually right. (rain, umbrella)
    S = rblx.Stage(PACK, "rain")
    street_props(S)
    teller = S.char("Crowd1", (11, -3552), 180, "smirk")
    um = kit.mat("umbrella", (0.7, 0.2, 0.8))
    canopy = kit.cyl(2.2, 0.8, tuple(teller.world((1.3, 0.4, 7.2))), um, verts=10, r2=0.1)
    stick = kit.cyl(0.07, 3.0, tuple(teller.world((1.5, 0.3, 5.6))), kit.mat("stick", (0.2, 0.2, 0.2)), verts=6)
    teller.arm("R", 1, 150)
    attach(canopy, teller.arms["R"])
    attach(stick, teller.arms["R"])
    for nm, x, y in (("Narrator", 8.6, -3550.5), ("Crowd2", 13.4, -3550.2)):
        c = S.char(nm, (x, y), 180 + (25 if x < 11 else -25), "shocked")
        c.arm("L", 1, 160)
        c.arm("R", 1, 160)
        c.look(1, 0, 25)
    S.rain(F, (11, -3551, 0), radius=9, n=500, height=12)
    S.cam(V((11, -3551, 3.4)), dist=13, yaw=180, height=5.0, lens=32)
    return S


def s08(k, F):  # Then, the tapping started. (house at night from the yard)
    S, h = night_house()
    sway(h["branch"], F, amp=(2, 0, 3), period=20, seed=1)
    kit.point((WIN[0], H[1] + 3, 6), (0.3, 0.35, 0.6), 80, 1.0)
    S.cam_at(V((WIN[0] - 12, H[1] + 27, 5.5)), V((WIN[0], H[1] + 7, 7)), lens=30, fstop=None)
    return S


def s09(k, F):  # Tap. Tap. Tap. (curtain + branch shadow)
    S, h = night_house()
    f = 1
    while f <= F:
        for dx, ang in ((0.0, 0), (0.25, -4)):
            h["shadow"].location.x = WIN[0] + dx
            h["shadow"].rotation_euler = (R(90), R(ang), 0)
            h["shadow"].keyframe_insert("location", frame=f)
            h["shadow"].keyframe_insert("rotation_euler", frame=f)
            f += 8
    S.cam_at(V((WIN[0] - 1.5, H[1] - 2, 5.6)), V((WIN[0], H[1] + 6.5, 6)), lens=32)
    return S


def s10(k, F):  # Every night at three a.m.,
    S, h = night_house()
    S.cam_at(V((H[0] + 0.9, H[1] + 1.8, 3.6)), V((H[0] + 0.9, H[1] + 4.6, 3.05)), lens=40, fstop=2.0)
    return S


def in_bed(S, expr="shocked", sit=False):
    hx, hy = H
    if sit:
        n = S.char("Narrator", (hx + 4.6, hy + 3.2, 2.2 - 1.5), 0, expr)
        n.sit(1)
    else:
        n = S.char("Narrator", (hx + 4.6, hy - 1.6, 2.7), 0, expr)
        n.lie(1, face_down=False)
    return n


def s11(k, F):  # on my bedroom window. (eyes open in bed)
    S, h = night_house()
    n = in_bed(S, "shocked")
    n.look(1, 30, 0)
    n.look(kf(16), 45, 0)
    S.cam_at(V((H[0] + 1.0, H[1] - 1.5, 7.5)), V((H[0] + 4.6, H[1] + 3.5, 2.8)), lens=30)
    return S


def s12(k, F):  # footsteps in the hall (sits up, looks at door)
    S, h = night_house()
    n = in_bed(S, "worried", sit=True)
    n.look(1, 0, 0)
    n.look(kf(18), -60, 0)
    n.faces([(1, "worried"), (kf(18), "scared")])
    n.arm("L", 1, 40, 10)
    n.arm("R", 1, 40, 10)
    S.cam_at(V((H[0] - 3.5, H[1] - 6, 6.0)), V((H[0] + 3.0, H[1], 3.6)), lens=28)
    return S


def s13(k, F):  # On the third night, (dark hallway)
    S, h = night_house()
    kit.point((H[0] - 11, H[1] + 5, 1.0), (1, 0.7, 0.3), 25, 0.3)
    S.cam_at(V((H[0] - 11, H[1] - 6.5, 5.0)), V((H[0] - 11, H[1] + 6, 4.0)), lens=24, fstop=None)
    return S


def s14(k, F):  # the fridge was glowing in the dark.
    S, h = night_house()
    hinge = h["fridge_hinge"]
    kit.key(hinge, 1, rot=(0, 0, -35))
    h["fridge_light"].data.energy = 1500
    S.cam_at(V((H[0] - 22, H[1] - 6.5, 5.0)), V((H[0] - 17.5, H[1] + 3.5, 4.0)), lens=30, fstop=None)
    return S


def s15(k, F):  # vent started whispering (ear to the vent)
    S, h = night_house()
    n = S.char("Narrator", (H[0] + 6.4, H[1] - 4.0), -90 - 180, "worried")  # facing +X (the wall)
    n.lean(1, 10, -12)
    n.look(1, 0, 0, -25)
    S.cam_at(V((H[0] + 1.5, H[1] - 9, 5.4)), V((H[0] + 6.8, H[1] - 4, 4.0)), lens=32)
    return S


def s16(k, F):  # "Over. Do you copy? Over." (vent close)
    S, h = night_house()
    for o in h["walkie"]:
        o.hide_render = True
    L = kit.point((H[0] + 8.3, H[1] - 4.0, 4.3), (0.3, 1.0, 0.4), 0, 0.2)
    for f in range(1, F + 2, 6):
        L.data.energy = 25 if (f // 6) % 2 else 2
        L.data.keyframe_insert("energy", frame=f)
    S.cam_at(V((H[0] + 4.0, H[1] - 5.5, 4.4)), V((H[0] + 7.7, H[1] - 4.0, 4.3)), lens=38, fstop=2.2)
    return S


def s17(k, F):  # I stopped sleeping. (under the blanket, flashlight)
    S, h = night_house()
    n = in_bed(S, "tired", sit=True)
    n.arm("R", 1, 80, -10)
    flashlight(n, "R", 1, 800)
    S.cam_at(V((H[0] + 2.5, H[1] - 6.5, 5.0)), V((H[0] + 4.6, H[1] - 1.0, 4.4)), lens=30)
    return S


def s18(k, F):  # I drew maps of every sound. (desk)
    S, h = night_house()
    n = S.char("Narrator", (H[0] - 5.4, H[1] + 2.8, 2.0 - 1.5), 180, "tired")
    n.sit(1)
    f = 1
    while f <= F:
        n.arm("R", f, 80 + (6 if (f // 6) % 2 else 0), -8 + (4 if (f // 6) % 2 else -4))
        f += 6
    n.arm("L", 1, 70, -5)
    n.look(1, 0, -30)
    kit.point((H[0] - 4.0, H[1] + 5.8, 5.0), (1, 0.8, 0.5), 120, 0.4)
    S.cam_at(V((H[0] - 7.0, H[1] + 1.8, 8.6)), V((H[0] - 5.5, H[1] + 5.0, 3.2)), lens=30)
    return S


def s19(k, F):  # Cousin: built on an old graveyard (flashlight under chin)
    S, h = night_house()
    c = S.char("Cousin", (H[0] - 1.0, H[1] - 2.0), 0, "smirk")
    c.arm("R", 1, 75, -25)
    up = kit.spot(tuple(c.world((0.3, 1.2, 2.6))), tuple(c.head_pt() + V((0, 0, 0.6))), (1, 0.85, 0.6), 600, 35, 0.4, 0.1)
    c.talk(4, F, base="smirk")
    n = S.char("Narrator", (H[0] + 2.8, H[1] - 0.4), -120, "scared")
    S.cam_at(V((H[0] - 1.8, H[1] - 9, 4.6)), c.head_pt() - V((0, 0, 0.8)), lens=34)
    return S


def s20(k, F):  # My cousin also thinks pigeons are robots.
    S = rblx.Stage(PACK, "day")
    p = street_props(S)
    c = S.char("Cousin", (11.5, -3503), 160, "shocked")
    c.point(1, "R", up=-15)
    c.talk(kf(10), F, base="shocked")
    body, head = p["pigeon"]
    f = 1
    while f <= F:
        head.rotation_euler = (R(25 if (f // 6) % 2 else -10), 0, 0)
        head.keyframe_insert("rotation_euler", frame=f)
        f += 6
    S.cam_at(V((4.5, -3493.5, 4.6)), V((10.6, -3501.5, 2.4)), lens=28)
    return S


def s21(k, F):  # On the seventh night, (wide bedroom)
    S, h = night_house()
    n = in_bed(S, "scared")
    n.look(1, 40, 0)
    sway(h["shadow"], F, amp=(0, 4, 0), period=16)
    S.cam_at(V((H[0] - 2, H[1] - 10, 7.5)), V((H[0] + 1.5, H[1] + 2.5, 4.0)), lens=24, fstop=None)
    return S


def s22(k, F):  # the tapping got louder. (shadow claw, punch)
    S, h = night_house()
    sh = h["shadow"]
    sh.scale = (6.5, 6.5, 1)
    sway(sh, F, amp=(0, 7, 0), period=8)
    S.cam_at(V((WIN[0] - 0.5, H[1] - 0.5, 6.0)), V((WIN[0], H[1] + 6.5, 6.2)), lens=32)
    S.shake(1, F, 0.08)
    return S


def s23(k, F):  # I grabbed my flashlight.
    S, h = night_house()
    n = in_bed(S, "determined", sit=True)
    n.arm("R", 1, 20, 10)
    n.arm("R", kf(12), 85, 0)
    flashlight(n, "R", kf(14), 2500)
    S.cam_at(V((H[0] + 1.0, H[1] - 5.0, 5.2)), n.world((1.4, 1.0, 3.6)), lens=32)
    return S


def at_curtain(S, expr="scared"):
    n = S.char("Narrator", (WIN[0] + 0.2, H[1] + 3.8), 180, expr)
    return n


def s24(k, F):  # I counted to three.
    S, h = night_house()
    n = at_curtain(S)
    n.arm("L", 1, 60, 5)
    n.arm("R", 1, 85)
    flashlight(n, "R", 1, 2000)
    n.lean(1, 6)
    for i, f in enumerate((1, kf(F * 0.33), kf(F * 0.66))):
        n.look(f, 0, -5 + i * 3)
    S.cam_at(V((WIN[0] + 3.5, H[1] - 3.0, 5.6)), n.head_pt() + V((0, 1.0, -0.6)), lens=30)
    return S


def s25(k, F):  # And I ripped the curtain open.
    S, h = night_house()
    n = at_curtain(S, "determined")
    flashlight(n, "R", 1, 2000)
    n.arm("R", 1, 85)
    n.arm("L", 1, 60, 5)
    fo = kf(F * 0.35)
    n.arm("L", fo, 70, 70)
    for side, dx in (("curL", -2.6), ("curR", 2.6)):
        o = h[side]
        kit.key(o, max(1, fo - 2), loc=tuple(o.location), scale=(1, 1, 1))
        kit.key(o, fo + 4, loc=(o.location.x + dx, o.location.y, o.location.z), scale=(0.35, 1, 1))
    S.show(h["shadow"], 1, True)
    S.show(h["shadow"], fo + 2, False)
    n.faces([(1, "determined"), (fo + 2, "shocked")])
    S.cam_at(V((WIN[0] - 4.0, H[1] - 3.0, 5.4)), V((WIN[0], H[1] + 6, 6.0)), lens=28, fstop=None)
    return S


def open_curtains(h):
    for side, dx in (("curL", -2.6), ("curR", 2.6)):
        o = h[side]
        o.location.x += dx
        o.scale = (0.35, 1, 1)
    h["shadow"].hide_render = True


def s26(k, F):  # It was a branch.
    S, h = night_house()
    open_curtains(h)
    sway(h["branch"], F, amp=(1.5, 0, 2.2), period=12, seed=2)
    kit.point((WIN[0], H[1] + 6, 6.5), (1, 0.95, 0.8), 150, 0.5)  # the flashlight beam on it
    S.cam_at(V((WIN[0] - 0.4, H[1] + 2.0, 6.2)), V((WIN[0] - 0.4, H[1] + 7.5, 6.5)), lens=34, fstop=2.4)
    return S


def s27(k, F):  # Just a branch, scratching the glass in the wind.
    S, h = night_house()
    open_curtains(h)
    sway(h["branch"], F, amp=(2.5, 0, 4), period=14, seed=3)
    S.cam_at(V((WIN[0] - 11, H[1] + 23, 8)), V((WIN[0], H[1] + 8, 6.5)), lens=30, fstop=None)
    return S


def s28(k, F):  # little sister, sneaking cookies (hallway)
    S, h = night_house()
    kit.point((H[0] - 11, H[1] + 4, 1.0), (1, 0.7, 0.3), 40, 0.3)
    c = S.char("Smallkid", (H[0] - 11, H[1] + 3), 0, "smirk")
    c.walk(1, F, (H[0] - 11, H[1] - 1.5), swing=18)
    jar = kit.cyl(0.55, 1.1, tuple(c.world((0, 1.0, 2.2))), kit.mat("jar2", (0.8, 0.9, 1.0), alpha=0.6), verts=14)
    cookies = kit.cyl(0.5, 0.5, tuple(c.world((0, 1.0, 2.0))), kit.mat("cookie", (0.65, 0.4, 0.2)), verts=14)
    attach(jar, c.body)
    attach(cookies, c.body)
    for f in range(1, F + 2, 15):
        c.arm("L", f, 70, -15)
        c.arm("R", f, 70, -15)
    S.cam_at(V((H[0] - 11, H[1] - 8, 4.0)), c.chest_pt() + V((0, 0, 0.4)), lens=30)
    return S


def s29(k, F):  # little sister, sneaking milk (fridge)
    S, h = night_house()
    kit.key(h["fridge_hinge"], 1, rot=(0, 0, -95))
    h["fridge_light"].data.energy = 1800
    c = S.char("Smallkid", (H[0] - 17.6, H[1] + 1.2), 180, "laugh")
    milk = kit.box((0.7, 0.7, 1.3), tuple(c.world((1.5, 0.6, 2.0))), kit.mat("milk2", (0.97, 0.97, 1.0)), 0.05)
    c.arm("R", 1, 40)
    attach(milk, c.arms["R"])
    c.arm("R", kf(12), 150, -20)   # drinking
    c.look(kf(12), 0, 20)
    S.cam_at(V((H[0] - 21.5, H[1] - 6.0, 4.5)), c.head_pt() - V((0, 0, 1.2)), lens=28)
    return S


def s30(k, F):  # the whispers were the walkie-talkie
    S, h = night_house()
    for o in h["grille"]:
        o.hide_render = True
    L = kit.point((H[0] + 7.0, H[1] - 4.0, 4.4), (1, 0.95, 0.85), 60, 0.5)
    S.cam_at(V((H[0] + 4.5, H[1] - 5.5, 4.6)), V((H[0] + 7.8, H[1] - 4.0, 4.2)), lens=40, fstop=2.4)
    return S


def s31(k, F):  # stuck in the vent since summer. (Cousin embarrassed)
    S, h = night_house()
    for o in h["grille"]:
        o.hide_render = True
    c = S.char("Cousin", (H[0] + 2.0, H[1] - 3.0), -40, "embarrassed")
    c.arm("R", 1, 150, 25)
    w = kit.box((0.4, 0.4, 1.0), tuple(c.world((-1.5, 0.6, 2.4))), kit.mat("walkie2", (0.1, 0.12, 0.1)), 0.05)
    c.arm("L", 1, 50)
    attach(w, c.arms["L"])
    n = S.char("Narrator", (H[0] - 1.5, H[1] - 1.5), 40, "angry")
    n.arm("L", 1, 75, -40)
    n.arm("R", 1, 70, -45)
    S.cam_at(V((H[0] + 0.5, H[1] - 11, 4.6)), V((H[0] + 0.3, H[1] - 2.2, 3.6)), lens=30)
    return S


def s32(k, F):  # The next day, I trimmed the tree.
    S, h = day_house()
    tx = WIN[0] + 1.5
    n = S.char("Narrator", (WIN[0] - 2.5, H[1] + 10.5), 180 + 40, "smile")
    c = S.char("Cousin", (WIN[0] - 5.0, H[1] + 13), 180 + 70, "laugh")
    shears = kit.mat("shears", (0.6, 0.6, 0.65), metal=0.7)
    for side in ("L", "R"):
        b = kit.box((0.15, 0.15, 2.2), tuple(n.world((1.5 if side == "R" else -1.5, 0.2, 1.2))), shears, 0.02)
        attach(b, n.arms[side])
    for f in range(1, F + 2, 6):
        o = 20 if (f // 6) % 2 else 5
        n.arm("L", f, 110, o)
        n.arm("R", f, 110, o)
    br = h["branch"]
    kit.key(br, 1, loc=tuple(br.location), rot=(0, 0, 0))
    kit.key(br, kf(F * 0.55), loc=tuple(br.location), rot=(0, 0, 0))
    kit.key(br, kf(F * 0.9), loc=(br.location.x, br.location.y, br.location.z - 5.5), rot=(25, 0, 10))
    S.cam_at(V((WIN[0] - 13, H[1] + 22, 6.0)), V((WIN[0] - 1.5, H[1] + 10.5, 4.5)), lens=30, fstop=None)
    return S


def s33(k, F):  # slept for eleven hours (morning sun)
    S, h = day_house()
    open_curtains(h)
    h["branch"].hide_render = True
    for o in h["branch"].children:
        o.hide_render = True
    n = in_bed(S, "smile_blink")
    n.look(1, 15, 0)
    S.cam_at(V((H[0] + 1.0, H[1] - 1.5, 7.5)), V((H[0] + 4.6, H[1] + 3.5, 2.8)), lens=30)
    return S


def s34(k, F):  # In this town, everything is normal. (street, sunset)
    S = rblx.Stage(PACK, "sunset")
    street_props(S)
    for nm, x, y in (("Prey1", 9.6, -3500), ("Crowd2", 12.6, -3497), ("Crowd3", 10.4, -3492), ("Prey3", 12.4, -3504)):
        c = S.char(nm, (x, y), 0, "smile")
        c.walk(1, F, (x, y - 4))
    S.cam(V((11, -3502, 3.5)), dist=20, yaw=-22, height=6.0, lens=32, fstop=None)
    return S


def s35(k, F):  # And honestly? I like it that way.
    S = rblx.Stage(PACK, "sunset")
    n = S.char("Narrator", (10.6, -3505), -10, "laugh")
    s = S.char("Smallkid", (12.6, -3505.4), 10, "smile")
    n.look(1, 0, 5)
    n.talk(kf(F * 0.4), F, base="laugh")
    for f in range(1, F + 2, 8):
        s.arm("R", f, 0, 150 if (f // 8) % 2 else 120)
    n.arm("L", 1, 0, 25)
    S.cam(V((11.5, -3505, 3.4)), dist=10, yaw=0, height=4.2, lens=36)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 36)}
