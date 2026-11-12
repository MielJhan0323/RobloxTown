"""nothing-happens ("Completely Normal") - build-ups that end in something ordinary.

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
    wall = kit.mat("hwall", (0.4, 0.45, 0.62) if night else (0.72, 0.8, 0.98), rough=0.9)
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
        kit.point((hx, hy - 2, 9), (0.75, 0.8, 1.0), 90, 3.0)
        kit.point((hx - 11, hy - 2, 9), (0.5, 0.6, 1.0), 25, 3.0)
        kit.point((hx - 22, hy - 2, 9), (0.5, 0.6, 1.0), 25, 3.0)
    else:
        for x in (hx, hx - 11, hx - 22):
            kit.point((x, hy - 2, 10), (1, 0.92, 0.8), 220, 3.0)
        kit.spot((WIN[0] + 3, hy + 30, 16), (WIN[0], hy + 2, 1), (1, 0.85, 0.6), 6000, 30, 0.6, 0.6)
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
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.75
    return S, house(S, True)


def day_house():
    S = rblx.Stage(PACK, "morning")
    h = house(S, False)
    open_curtains(h)
    bpy.context.scene.view_settings.exposure = -0.6
    return S, h


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


def in_bed(S, expr="shocked", sit=False):
    hx, hy = H
    if sit:
        n = S.char("Narrator", (hx + 4.6, hy + 3.2, 2.2 - 1.5), 0, expr)
        n.sit(1)
    else:
        n = S.char("Narrator", (hx + 4.6, hy - 1.6, 2.7), 0, expr)
        n.lie(1, face_down=False)
    return n


def at_curtain(S, expr="scared"):
    n = S.char("Narrator", (WIN[0] + 0.2, H[1] + 3.8), 180, expr)
    return n


def open_curtains(h):
    for side, dx in (("curL", -2.6), ("curR", 2.6)):
        o = h[side]
        o.location.x += dx
        o.scale = (0.35, 1, 1)
    h["shadow"].hide_render = True


# ---------------------------------------------------------------- extra props / effects
def snow(S, frames, center, radius=10, n=350, height=12):
    m = kit.mat("snow", (1, 1, 1), rough=0.9)
    rnd = random.Random(8)
    flakes = [kit.box((0.12, 0.12, 0.12), (0, 0, 0), m, 0) for _ in range(n)]
    for o in flakes:
        x, y, z = (center[0] + rnd.uniform(-radius, radius), center[1] + rnd.uniform(-radius, radius),
                   center[2] + rnd.uniform(0, height))
        kit.key(o, 1, loc=(x, y, z))
        kit.key(o, frames + 15, loc=(x + rnd.uniform(-1, 1), y, z - rnd.uniform(3, 5)))
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    return flakes


def darken_sky(S, f0, f1):
    """Key the world + sun from day to night between f0 and f1."""
    w = bpy.context.scene.world
    bg = w.node_tree.nodes["Background"]
    sun = [o for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SUN"][0]
    cam_bg = w.node_tree.nodes.get("BACKDROP")
    for f, st, se in ((f0, 1.0, 3.2), (f1, 0.18, 0.35)):
        bg.inputs[1].default_value = st
        bg.inputs[1].keyframe_insert("default_value", frame=f)
        if cam_bg:
            cam_bg.inputs[1].default_value = 1.0 if st > 0.5 else 0.15
            cam_bg.inputs[1].keyframe_insert("default_value", frame=f)
        sun.data.energy = se
        sun.data.keyframe_insert("energy", frame=f)


def lamps_on(S, f0=1, gap=0, near=None):
    """Street lamp bulbs light up (one by one when gap > 0)."""
    bulbs = [o for o in bpy.data.objects if o.name.startswith("Lampbulb")]
    if near is not None:
        bulbs.sort(key=lambda o: (o.matrix_world.translation - V(near)).length)
    for k, o in enumerate(bulbs):
        m = kit.mat("bulb%d" % k, (1, 0.9, 0.6), emit=0.0001, emit_color=(1, 0.85, 0.5))
        o.data.materials.clear()
        o.data.materials.append(m)
        nodes = m.node_tree.nodes
        b = next(n for n in nodes if n.type in ("BSDF_PRINCIPLED", "EMISSION"))
        sock = b.inputs["Emission Strength"] if "Emission Strength" in b.inputs else b.inputs["Strength"]
        on = f0 + k * gap
        sock.default_value = 0.0
        sock.keyframe_insert("default_value", frame=max(0, on - 1))
        sock.default_value = 12.0
        sock.keyframe_insert("default_value", frame=on)
        if gap:  # flicker
            sock.default_value = 0.5
            sock.keyframe_insert("default_value", frame=on + 2)
            sock.default_value = 12.0
            sock.keyframe_insert("default_value", frame=on + 4)
        c = o.matrix_world.translation
        L = kit.point(tuple(c - V((0, 0, 0.6))), (1, 0.85, 0.55), 0, 1.0)
        L.data.keyframe_insert("energy", frame=max(0, on - 1))
        L.data.energy = 600
        L.data.keyframe_insert("energy", frame=on)


def mail_cap(c):
    blue = kit.mat("mailblue", (0.15, 0.25, 0.6))
    top = c.head_pt() + V((0, 0, 0.75))
    cap = kit.box((1.5, 1.5, 0.5), tuple(top), blue, 0.12)
    brim = kit.box((1.3, 0.8, 0.12), tuple(top + c.world((0, 0.9, 0)) - c.pos + V((0, 0, -0.2))), blue, 0.04)
    attach(cap, c.neck)
    attach(brim, c.neck)
    bag = kit.box((1.3, 0.6, 1.4), tuple(c.world((-1.0, 0.2, 2.2))), kit.mat("mailbag", (0.55, 0.35, 0.2)), 0.1)
    attach(bag, c.body)


def kids_street(S, specs, F, walk=True):
    out = {}
    for nm, x, y, expr in specs:
        c = S.char(nm, (x, y), 0, expr)
        if walk:
            c.walk(1, F, (x, y - 4))
        out[nm] = c
    return out


STREET_KIDS = [("Narrator", 11, -3478, "smile"), ("Smallkid", 12.6, -3479, "smile"), ("Crowd2", 9.6, -3472, "smile"),
               ("Prey1", 12.4, -3468, "smile")]


# ---------------------------------------------------------------- shots
def s01(k, F):  # In this town,
    S = rblx.Stage(PACK, "morning")
    kids_street(S, STREET_KIDS, F)
    S.cam(V((11.0, -3478, 3.0)), dist=16, yaw=-28, height=5.0, lens=38, fstop=None)
    return S


def s02(k, F):  # everything is completely normal.
    S = rblx.Stage(PACK, "morning")
    for i, (nm, x) in enumerate((("Crowd2", 9.0), ("Narrator", 11.2), ("Smallkid", 13.0))):
        c = S.char(nm, (x, -3500), 0, "laugh" if i == 1 else "smile")
        for j, f in enumerate(range(1, F + 2, 8)):
            c.arm("R", f, 0, 150 if j % 2 else 120)
    S.cam(V((11.0, -3500, 3.2)), dist=11, yaw=-5, height=4.0, lens=38)
    return S


def umbrella(c, color):
    um = kit.mat("umb" + str(color), color)
    canopy = kit.cyl(2.0, 0.7, tuple(c.world((1.3, 0.4, 7.0))), um, verts=10, r2=0.1)
    stick = kit.cyl(0.07, 3.0, tuple(c.world((1.5, 0.3, 5.4))), kit.mat("stick", (0.2, 0.2, 0.2)), verts=6)
    attach(canopy, c.arms["R"])
    attach(stick, c.arms["R"])
    c.arm("R", 1, 150)


def s03(k, F):  # It rains.
    S = rblx.Stage(PACK, "rain")
    cs = kids_street(S, [("Narrator", 11, -3500, "neutral"), ("Crowd2", 12.8, -3496, "neutral"), ("Prey1", 9.4, -3494, "neutral")], F)
    for c, col in zip(cs.values(), ((0.2, 0.4, 0.9), (0.9, 0.3, 0.3), (0.95, 0.8, 0.2))):
        umbrella(c, col)
    S.rain(F, (11, -3500, 0), radius=10, n=550)
    S.cam(V((11, -3499, 3.4)), dist=15, yaw=12, height=5.0, lens=32)
    return S


def s04(k, F):  # It gets sunny.
    S = rblx.Stage(PACK, "day")
    cs = kids_street(S, [("Narrator", 11, -3500, "smile"), ("Smallkid", 12.8, -3500.5, "laugh")], F, walk=False)
    for c in cs.values():
        c.arm("L", 1, 150, -30)   # shading eyes
        c.look(1, 0, 15)
    kit.sphere(4, (40, -3420, 60), kit.mat("sun", (1, 0.95, 0.6), emit=15, emit_color=(1, 0.9, 0.5)))
    S.cam(V((11.8, -3500, 4.0)), dist=10, yaw=-10, height=3.5, lens=32)
    return S


def s05(k, F):  # Sometimes, it gets cold.
    S = rblx.Stage(PACK, "dusk")
    cs = kids_street(S, [("Narrator", 11, -3500, "sad"), ("Prey1", 12.8, -3500.5, "sad"), ("Crowd2", 9.3, -3501, "sad")], F, walk=False)
    for c in cs.values():
        c.arm("L", 1, 70, -45)
        c.arm("R", 1, 70, -45)
        for j, f in enumerate(range(1, F + 2, 3)):   # shivering
            c.lean(f, 0, 3 if j % 2 else -3)
    snow(S, F, (11, -3500, 0), radius=9)
    S.cam(V((11, -3500, 3.4)), dist=11, yaw=-5, height=4.2, lens=34)
    return S


def s06(k, F):  # Until one day, the sky turned dark.
    S = rblx.Stage(PACK, "day")
    darken_sky(S, 1, F)
    S.cam_at(V((0, -3560, 2.0)), V((0, -3480, 14)), lens=24, fstop=None)
    return S


def s07(k, F):  # The birds went quiet.
    S = rblx.Stage(PACK, "dusk")
    pg = kit.mat("pigeon", (0.55, 0.57, 0.65), rough=0.6)
    body = kit.box((0.7, 1.1, 0.7), (8.6, -3530, 9.75), pg, 0.15)
    head = kit.box((0.45, 0.45, 0.45), (8.6, -3530.6, 10.25), kit.mat("pighead", (0.35, 0.45, 0.5)), 0.1)
    kit.box((0.12, 0.25, 0.12), (8.6, -3530.9, 10.2), kit.mat("beak", (0.95, 0.6, 0.2)), 0)
    for j, f in enumerate(range(1, F // 2, 6)):
        head.rotation_euler = (R(20 if j % 2 else -10), 0, 0)
        head.keyframe_insert("rotation_euler", frame=f)
    head.rotation_euler = (0, 0, R(60))
    head.keyframe_insert("rotation_euler", frame=F // 2 + 3)
    S.cam_at(V((4.0, -3536, 9.0)), V((8.6, -3530.3, 9.9)), lens=40, fstop=2.8)
    return S


def s08(k, F):  # The streetlights flickered on, one by one.
    S = rblx.Stage(PACK, "night")
    lamps_on(S, 3, gap=max(2, F // 9), near=(0, -3580, 0))
    S.cam_at(V((0, -3585, 4.5)), V((0, -3520, 5)), lens=26, fstop=None)
    return S


def s09(k, F):  # Everyone looked up.
    S = rblx.Stage(PACK, "night")
    lamps_on(S)
    cs = kids_street(S, [("Narrator", 11, -3500, "shocked"), ("Smallkid", 12.8, -3500.5, "shocked"),
                         ("Crowd2", 9.3, -3499, "shocked"), ("Prey1", 12, -3497, "shocked")], F, walk=False)
    for c in cs.values():
        c.look(1, 0, 0)
        c.look(kf(10), 0, 35)
    S.cam(V((11, -3500, 3.4)), dist=10, yaw=-5, height=2.6, lens=32)
    return S


def s10(k, F):  # It was just night time.
    S = rblx.Stage(PACK, "night")
    lamps_on(S)
    kit.sphere(5, (-60, -3380, 70), kit.mat("moon", (1, 1, 0.9), emit=6, emit_color=(0.9, 0.95, 1)))
    cs = kids_street(S, [("Narrator", 11, -3500, "neutral"), ("Smallkid", 12.8, -3500.5, "neutral"),
                         ("Crowd2", 9.3, -3499, "neutral"), ("Prey1", 12, -3497, "neutral")], F, walk=False)
    for c in cs.values():   # shrug
        c.arm("L", kf(8), 30, 35)
        c.arm("R", kf(8), 30, 35)
        c.look(kf(8), 0, -5)
    S.cam(V((9, -3500, 4)), dist=17, yaw=-25, height=5.0, lens=28, fstop=None)
    return S


def s11(k, F):  # footsteps behind me
    S = rblx.Stage(PACK, "night")
    lamps_on(S)
    n = S.char("Narrator", (11, -3500), 0, "worried")
    n.walk(1, F, (11, -3504), swing=22)
    n.look(kf(F * 0.5), 30, 0)
    S.cam(V((11, -3502, 3.6)), dist=9, yaw=-10, height=4.4, lens=34)
    return S


def s12(k, F):  # Slow. Heavy. Getting closer. (big shadow on the sidewalk)
    S = rblx.Stage(PACK, "night")
    m = S.char("Crowd4", (11, -3488), 0, "neutral")
    m.walk(1, F, (11, -3492), swing=20)
    S.char("Narrator", (11, -3497), 0, "worried")
    kit.spot((11, -3480, 4.0), (11, -3500, 0), (1, 0.85, 0.6), 6000, 40, 0.3, 0.05)
    S.cam_at(V((9.2, -3500, 0.8)), V((11, -3492, 2.2)), lens=26)
    S.hide("Lampbulb")
    return S


def s13(k, F):  # I turned around.
    S = rblx.Stage(PACK, "night")
    lamps_on(S)
    n = S.char("Narrator", (11, -3500), 0, "scared")
    n.key_root(1, yaw=0)
    n.key_root(kf(10), yaw=180)
    S.cam(n.head_pt() - V((0, 0, 0.8)), dist=6, yaw=180, height=n.head_pt().z, lens=40)
    return S


def mailman(S, xy=(11, -3496.5)):
    m = S.char("Crowd4", xy, 0, "smile")
    mail_cap(m)
    return m


def s14(k, F):  # It was the mailman.
    S = rblx.Stage(PACK, "night")
    lamps_on(S)
    m = mailman(S)
    m.arm("R", 1, 0, 20)
    m.arm("R", kf(8), 0, 140)  # wave
    S.cam(m.head_pt() - V((0, 0, 1.4)), dist=8, yaw=0, height=m.head_pt().z - 0.4, lens=36)
    return S


def s15(k, F):  # He had a package for my mom.
    S = rblx.Stage(PACK, "night")
    lamps_on(S)
    m = mailman(S)
    n = S.char("Narrator", (11, -3500), 180, "tired")
    box = kit.box((1.6, 1.2, 1.2), tuple(m.world((0, 1.6, 3.0))), kit.mat("parcel", (0.75, 0.55, 0.3)), 0.05)
    kit.box((1.62, 0.2, 1.22), tuple(m.world((0, 1.6, 3.0))), kit.mat("tape", (0.9, 0.85, 0.6)), 0)
    m.arm("L", 1, 75)
    m.arm("R", 1, 75)
    S.cam(V((11, -3498.3, 3.8)), dist=10, yaw=-75, height=4.6, lens=32)
    return S


def s16(k, F):  # That night, something tapped on my window.
    S, h = night_house()
    sway(h["shadow"], F, amp=(0, 4, 0), period=10)
    S.cam_at(V((H[0] - 3, H[1] - 8, 6.5)), V((WIN[0], H[1] + 6, 6)), lens=28, fstop=None)
    return S


def s17(k, F):  # Tap. Tap. Tap.
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


def s18(k, F):  # I hid under my blanket.
    S, h = night_house()
    n = in_bed(S, "scared")
    bl = h["blanket"]
    kit.key(bl, 1, loc=tuple(bl.location), scale=(1, 1, 1))
    kit.key(bl, kf(12), loc=(bl.location.x, bl.location.y + 2.6, bl.location.z + 0.3), scale=(1.0, 1.25, 1.6))
    S.cam_at(V((H[0] + 1.0, H[1] - 1.5, 7.5)), V((H[0] + 4.6, H[1] + 3.0, 2.8)), lens=30)
    return S


def s19(k, F):  # I counted to three.
    S, h = night_house()
    n = at_curtain(S)
    n.arm("L", 1, 60, 5)
    n.arm("R", 1, 85)
    flashlight(n, "R", 1, 2000)
    n.lean(1, 6)
    S.cam_at(V((WIN[0] + 3.5, H[1] - 3.0, 5.6)), n.head_pt() + V((0, 1.0, -0.6)), lens=30)
    return S


def s20(k, F):  # I ripped the curtain open.
    S, h = night_house()
    n = at_curtain(S, "determined")
    flashlight(n, "R", 1, 2000)
    n.arm("R", 1, 85)
    n.arm("L", 1, 60, 5)
    fo = kf(F * 0.3)
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


def s21(k, F):  # It was a branch.
    S, h = night_house()
    open_curtains(h)
    sway(h["branch"], F, amp=(1.5, 0, 2.2), period=12, seed=2)
    kit.point((WIN[0], H[1] + 6, 6.5), (1, 0.95, 0.8), 150, 0.5)
    S.cam_at(V((WIN[0] - 0.4, H[1] + 2.0, 6.2)), V((WIN[0] - 0.4, H[1] + 7.5, 6.5)), lens=34, fstop=2.4)
    return S


def cups(S, slide_f=None):
    out = []
    for k2 in range(3):
        c = kit.cyl(0.35, 0.8, (H[0] - 27 + k2 * 1.4, H[1] + 4.6, 3.85), kit.mat("cup%d" % k2,
                    ((0.9, 0.3, 0.3), (0.3, 0.6, 0.9), (0.95, 0.8, 0.2))[k2]), verts=12)
        out.append(c)
        if slide_f:
            p0 = V(c.location)
            kit.key(c, 1, loc=tuple(p0), rot=(0, 0, 0))
            kit.key(c, slide_f, loc=tuple(p0 + V((0, -1.1, 0))), rot=(0, 0, 0))
            kit.key(c, slide_f + 8, loc=tuple(p0 + V((0, -2.0, -3.4))), rot=(80, 0, 20 * k2))
    return out


def s22(k, F):  # The next morning, the ground started shaking.
    S, h = day_house()
    n = S.char("Narrator", (H[0] - 24, H[1] + 1.5), 0, "shocked")
    cups(S)
    n.arm("L", 1, 30, 30)
    n.arm("R", 1, 30, 30)
    S.cam_at(V((H[0] - 21, H[1] - 7, 5.0)), n.head_pt() - V((0, 0, 1.5)), lens=28)
    S.shake(1, F, 0.18)
    return S


def s23(k, F):  # The windows rattled.
    S, h = day_house()
    S.cam_at(V((WIN[0] - 1.0, H[1] - 1.0, 6.0)), V((WIN[0], H[1] + 6.5, 6.0)), lens=30)
    S.shake(1, F, 0.25)
    return S


def s24(k, F):  # The cups slid off the table.
    S, h = day_house()
    cups(S, slide_f=kf(F * 0.3))
    S.cam_at(V((H[0] - 25.5, H[1] - 1.5, 4.8)), V((H[0] - 25.6, H[1] + 4.0, 3.6)), lens=30)
    S.shake(1, F, 0.12)
    return S


def s25(k, F):  # It was the garbage truck.
    S = rblx.Stage(PACK, "morning")
    t = kit.empty((0, 0, 0), name="gtruck")
    green = kit.mat("gtruck", (0.2, 0.55, 0.25), rough=0.5)
    parts = [kit.box((7, 14, 8), (-4, -3532, 5.0), green, 0.15),
             kit.box((7, 5, 6), (-4, -3522.5, 4.0), kit.mat("gcab", (0.95, 0.95, 0.95)), 0.2),
             kit.box((6, 0.3, 2.6), (-4, -3520.0, 5.2), kit.mat("gwin", (0.3, 0.45, 0.6), rough=0.05), 0.05)]
    for y in (-3536, -3528, -3522.5):
        for x in (-7.6, -0.4):
            parts.append(kit.cyl(1.5, 0.9, (x, y, 1.5), kit.mat("tire", (0.04, 0.04, 0.04)), 16, rot=(0, 90, 0)))
    for o in parts:
        attach(o, t)
    kit.key(t, 1, loc=(0, -10, 0))
    kit.key(t, F, loc=(0, 8, 0))
    S.cam_at(V((12.0, -3506, 5)), V((-4, -3528, 5)), lens=24, fstop=None)
    S.shake(1, F, 0.08)
    return S


def s26(k, F):  # It comes every Tuesday.
    S, h = day_house()
    n = S.char("Narrator", (H[0] - 24, H[1] + 1.5), 0, "tired")
    n.arm("L", 1, 75, -40)
    n.arm("R", 1, 70, -45)
    S.cam_at(V((H[0] - 22.5, H[1] - 6, 4.4)), n.head_pt() - V((0, 0, 1.4)), lens=32)
    return S


def s27(k, F):  # Then, my little sister disappeared.
    S, h = night_house()
    h["blanket"].rotation_euler = (0, R(-8), 0)
    h["blanket"].location.x += 0.6
    S.cam_at(V((H[0] - 1.5, H[1] - 6.5, 6.5)), V((H[0] + 4.6, H[1] + 2.0, 2.5)), lens=28)
    return S


def s28(k, F):  # Her bed was empty. Her shoes were gone.
    S, h = night_house()
    S.cam_at(V((H[0] + 2.0, H[1] - 1.0, 5.0)), V((H[0] + 4.6, H[1] + 3.5, 2.6)), lens=34, fstop=2.4)
    return S


def s29(k, F):  # The front door was wide open.
    S, h = night_house()
    kit.box((0.4, 3.0, 7.2), (H[0] - 14, H[1] - 4.5, 3.6), kit.mat("doorpanel", (0.55, 0.36, 0.22)), 0.03).rotation_euler = (0, 0, R(70))
    kit.spot((H[0] - 20, H[1] - 3, 6), (H[0] - 11, H[1] - 1, 0), (1, 0.85, 0.6), 4000, 40, 0.5, 0.2)
    S.cam_at(V((H[0] - 8.5, H[1] - 7, 5.0)), V((H[0] - 14, H[1] - 2.5, 3.5)), lens=26)
    return S


def s30(k, F):  # She was in the backyard, eating a popsicle.
    S, h = day_house()
    c = S.char("Smallkid", (WIN[0] - 4.0, H[1] + 12.5), 200, "laugh")
    stick = kit.cyl(0.06, 0.8, tuple(c.world((1.5, 0.5, 2.6))), kit.mat("pstick", (0.9, 0.8, 0.6)), verts=6)
    ice = kit.box((0.45, 0.25, 0.9), tuple(c.world((1.5, 0.5, 3.3))), kit.mat("ice", (0.95, 0.3, 0.5), rough=0.3), 0.1)
    attach(stick, c.arms["R"])
    attach(ice, c.arms["R"])
    for j, f in enumerate(range(1, F + 2, 10)):
        c.arm("R", f, 135 if j % 2 else 120, -15)
    S.cam(c.chest_pt() + V((0, 0, 0.4)), dist=8, yaw=200, lens=34)
    return S


def s31(k, F):  # By now, I'd stopped expecting anything.
    S, h = night_house()
    n = in_bed(S, "tired", sit=True)
    n.arm("L", 1, 75, -40)
    n.arm("R", 1, 70, -45)
    S.cam_at(V((H[0] + 2.4, H[1] - 6.5, 5.5)), n.head_pt() - V((0, 0, 1.2)), lens=32)
    return S


def purple_outside(S, f_on=1):
    L = kit.point((WIN[0], H[1] + 12, 7), (0.7, 0.3, 1.0), 0, 2.0)
    L.data.keyframe_insert("energy", frame=max(0, f_on - 1))
    L.data.energy = 700
    L.data.keyframe_insert("energy", frame=f_on + 6)
    return L


def s32(k, F):  # So when the sky turned purple,
    S, h = night_house()
    open_curtains(h)
    h["branch"].hide_render = True
    for o in h["branch"].children:
        o.hide_render = True
    purple_outside(S, 1)
    S.cam_at(V((WIN[0] - 0.5, H[1] - 1.0, 6.0)), V((WIN[0], H[1] + 7, 6.5)), lens=30)
    return S


def s33(k, F):  # and the ground started glowing,
    S, h = night_house()
    g = kit.box((30, 22, 0.1), (WIN[0], H[1] + 20, 0.06), kit.mat("glowground", (0.3, 1.0, 0.5), emit=0.0001,
                                                                       emit_color=(0.3, 1.0, 0.5)), 0)
    b = g.active_material.node_tree.nodes["Principled BSDF"]
    sock = b.inputs["Emission Strength"]
    sock.default_value = 0
    sock.keyframe_insert("default_value", frame=1)
    sock.default_value = 1.5
    sock.keyframe_insert("default_value", frame=F)
    purple_outside(S, 1)
    S.cam_at(V((WIN[0] - 11, H[1] + 23, 8)), V((WIN[0], H[1] + 12, 2)), lens=28, fstop=None)
    return S


def s34(k, F):  # and a voice said my name,
    S, h = night_house()
    open_curtains(h)
    n = in_bed(S, "neutral", sit=True)
    kit.spot((WIN[0], H[1] + 14, 9), (H[0] + 4.6, H[1] + 2.5, 3), (0.75, 0.4, 1.0), 20000, 18, 0.2, 0.1)
    n.look(1, 30, 10)
    S.cam_at(V((H[0] - 1.0, H[1] - 6.0, 6.5)), V((H[0] + 3.5, H[1] + 2.5, 3.8)), lens=28)
    return S


def s35(k, F):  # I just went back to sleep.
    S, h = night_house()
    open_curtains(h)
    purple_outside(S, 1)
    n = in_bed(S, "tired")
    n.faces([(1, "tired"), (kf(F * 0.5), "smile_blink")])
    bl = h["blanket"]
    kit.key(bl, 1, loc=tuple(bl.location), scale=(1, 1, 1))
    kit.key(bl, kf(F * 0.4), loc=(bl.location.x, bl.location.y + 2.2, bl.location.z), scale=(1, 1.2, 1))
    S.cam_at(V((H[0] + 1.0, H[1] - 1.5, 7.5)), V((H[0] + 4.6, H[1] + 3.0, 2.8)), lens=30)
    return S


def s36(k, F):  # In this town, everything is completely normal.
    S = rblx.Stage(PACK, "day")
    for nm, x, y in (("Prey1", 9.6, -3500), ("Crowd2", 12.6, -3497), ("Narrator", 10.4, -3492), ("Smallkid", 12.4, -3504)):
        c = S.char(nm, (x, y), 0, "smile")
        c.walk(1, F, (x, y - 4))
    S.cam(V((11, -3502, 3.5)), dist=20, yaw=-22, height=6.0, lens=32, fstop=None)
    return S


def s37(k, F):  # Probably.
    S = rblx.Stage(PACK, "sunset")
    for k2 in range(3):
        o = kit.sphere(1.2, (-20 + k2 * 6, -3400, 60 + k2 * 3), kit.mat("ufo%d" % k2, (0.7, 0.4, 1.0), emit=0.0001,
                                                                         emit_color=(0.7, 0.4, 1.0)))
        sock = o.active_material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        for j, f in enumerate(range(1 + k2 * 3, F + 2, 9)):
            sock.default_value = 25 if j % 2 == 0 else 0.5
            sock.keyframe_insert("default_value", frame=f)
        kit.key(o, 1, loc=tuple(o.location))
        kit.key(o, F, loc=(o.location.x + 8, o.location.y, o.location.z + 2))
    S.cam_at(V((0, -3560, 3)), V((-10, -3400, 55)), lens=30, fstop=None)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 38)}
