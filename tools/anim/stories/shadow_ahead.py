"""shadow-ahead ("The Shadow Ahead", Part 1) - In this town, your shadow moves ten seconds before you do.

Cast (tools/anim/cast.py): Milo, Rio, Pip, Mom, Dev, Juno, Wren.
Sets: Main Street (exported town), the kitchen (the_knock_2), Milo's bedroom + the train tracks (built here).

Shadows are fake on purpose: a spare character model painted flat black and squashed onto the ground or a wall,
so it can move on its own (ahead of its owner). Real character shadows are switched off so ours are the only ones.
"""
import math

import bpy
from mathutils import Vector

import kit
import rblx
from cast import C, place
from rblx import kf
from stories.nothing_happens import text
from stories.the_knock_2 import KIT, kitchen

R = math.radians
V = Vector
PACK = "alpha-mark"
SUN_DIR = V((-0.22, -0.97, 0)).normalized()    # where ground shadows fall: along the sidewalk
STREET_X = 10.6                                 # right sidewalk of Main Street (x 8..13.5, top at z 0.6)
BED = V((-1500.0, -3505.0, 0))                  # Milo's bedroom (built here)
TR = V((-1700.0, -3505.0, 0))                   # train tracks: rails along X at y = TR.y, road crossing at x = TR.x
POOL = ["Crowd2", "Crowd4", "Cousin", "Kai", "Prey1", "Crowd1", "Prey3", "Smallkid", "Crowd3", "Prey2", "Narrator"]


# ---------------------------------------------------------------- post-render-setup hooks
_orig_hide_unused = rblx.Stage.hide_unused


def _hide_unused(self):
    _orig_hide_unused(self)                      # bakes faces / blinks, adds the life layer
    for fn in getattr(self, "post_hooks", []):
        fn()


rblx.Stage.hide_unused = _hide_unused


def _desc(o):
    out = [o]
    for ch in o.children:
        out += _desc(ch)
    return out


def _char_objs(c):
    objs = set(_desc(c.root))
    col = bpy.data.collections.get("CH_" + c.name)
    if col:
        objs.update(col.all_objects)
    for h in c.heads.values():
        objs.update(_desc(h))
    return [o for o in objs if o.type == "MESH"]


def stage(light="day"):
    S = rblx.Stage(PACK, light)
    S.post_hooks = [lambda: _no_real_shadows(S)]
    S.shadows = []
    S.allow_close = set()
    return S


def _no_real_shadows(S):
    shadow_names = {c.name for c in S.shadows}
    for c in S.chars.values():
        if c.name in shadow_names:
            continue
        for o in _char_objs(c):
            for sl in o.material_slots:
                if sl.material:
                    sl.material.shadow_method = "NONE"


def allow(S, *names):
    for a in names:
        for b in names:
            if a != b:
                S.allow_close.add((a, b))


# ---------------------------------------------------------------- shadows
def shadow(S, at, direction=None, wall_normal=None, length=1.35, model=None, alpha=1.0, owner=None):
    """A moving shadow. Ground: feet at `at`, body lying flat along `direction` (default SUN_DIR).
    Wall: standing at `at` flat against a wall whose normal (into the room) is `wall_normal`.
    Returns the Char - animate it like any character (use arm 'out' / leg 'out' moves: they read in silhouette)."""
    used = set(S.chars)
    model = model or next(m for m in POOL if m not in used)
    x, y = at[0], at[1]
    z = at[2] if len(at) > 2 else (owner.pos.z if owner is not None else S.ground(x, y))
    if wall_normal is None:
        d = V(direction or SUN_DIR).normalized()
        yaw = math.degrees(math.atan2(d.x, -d.y))
        c = S.char(model, (x, y, z + 0.04), yaw, "neutral")
        c.root.rotation_euler.x = R(-90)
        c.root.scale = (1, 0.03, length)
    else:
        n = V(wall_normal).normalized()
        yaw = math.degrees(math.atan2(-n.x, n.y))
        c = S.char(model, (x, y, z), yaw, "neutral")
        c.root.scale = (1, 0.03, 1)
    m = kit.mat("shadowmat_%s" % model, (0.012, 0.012, 0.02), rough=1.0, alpha=alpha if alpha < 1 else 0.999)
    m.shadow_method = "NONE"

    def blacken():
        for o in _char_objs(c):
            for sl in o.material_slots:
                sl.link = "OBJECT"
                sl.material = m
    S.post_hooks.append(blacken)
    S.shadows.append(c)
    c.shadow_mat = m
    if owner is not None:
        allow(S, owner.name, c.name)
    for other in list(S.chars):
        allow(S, other, c.name)
    return c


def fade_shadow(c, f0, f1):
    """Fade a shadow out (its own material alpha), e.g. stepping onto the tracks."""
    b = c.shadow_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
    a0 = b.default_value
    for f, v in ((f0, a0), (f1, 0.0)):
        b.default_value = v
        b.keyframe_insert("default_value", frame=f)


def wave(c, f0, f1, side="R", every=8, base=150, amp=25):
    for j, f in enumerate(range(f0, f1 + 1, every)):
        c.arm(side, f, 0, base + (amp if j % 2 else -amp))


def shuffle(c, f0, f1, every=6, amp=18):
    """Walking as a flat shadow: legs + arms swing sideways (reads in silhouette)."""
    for j, f in enumerate(range(f0, f1 + 1, every)):
        s = amp if j % 2 else -amp
        c.leg("L", f, 0, s)
        c.leg("R", f, 0, -s)
        c.arm("L", f, 0, 10 + max(0, -s))
        c.arm("R", f, 0, 10 + max(0, s))


def slide(c, f0, f1, to, z=None):
    p = c.pos
    c.key_root(f0, (p.x, p.y, p.z if z is None else z))
    c.key_root(f1, (to[0], to[1], p.z if z is None else z))


# ---------------------------------------------------------------- sets
def street(light="day"):
    S = stage(light)
    for k2, ty in enumerate((-3548, -3522, -3496)):
        kit.tree((STREET_X + 2.3, ty), 1.3)
    return S


def crack(y):
    kit.box((3.2, 0.25, 0.04), (STREET_X, y, 0.63), kit.mat("crack", (0.12, 0.12, 0.13)), 0)


def bedroom(S, lamp=True):
    x, y = BED.x, BED.y
    wall = kit.mat("bwall", (0.55, 0.6, 0.78), rough=0.9)
    kit.box((16, 16, 0.3), (x, y, -0.15), kit.mat("bfloor", (0.5, 0.36, 0.24), rough=0.7), 0)
    kit.box((16, 0.6, 11), (x, y + 6.3, 5.5), wall, 0)        # back wall (the shadow lives here), faces -Y
    for wx in (-8.3, 8.3):
        kit.box((0.6, 16, 11), (x + wx, y, 5.5), wall, 0)
    kit.box((16.6, 0.6, 11), (x, y - 8.3, 5.5), wall, 0)
    kit.box((16.6, 16.6, 0.4), (x, y, 11.2), kit.mat("bceil", (0.85, 0.85, 0.88)), 0)
    # bed against the right wall, foot toward -Y
    kit.box((4.6, 8.0, 1.6), (x + 5.4, y + 1.5, 0.8), kit.mat("bedframe", (0.45, 0.3, 0.2)), 0.05)
    kit.box((4.4, 7.6, 0.8), (x + 5.4, y + 1.5, 1.9), kit.mat("blanket", (0.25, 0.45, 0.75), rough=0.9), 0.15)
    kit.box((3.2, 1.6, 0.7), (x + 5.4, y + 4.6, 2.5), kit.mat("pillow", (0.95, 0.95, 0.95)), 0.2)
    # window with night sky on the left wall, nightstand + lamp
    kit.box((0.1, 4, 3.6), (x - 7.95, y + 0.5, 6.2), kit.mat("bwin", (0.08, 0.1, 0.25), emit=0.8, emit_color=(0.15, 0.2, 0.5)), 0)
    kit.box((2, 2, 2), (x + 2.2, y + 4.8, 1.0), kit.mat("nstand", (0.5, 0.36, 0.22)), 0.05)
    kit.cyl(0.6, 1.2, (x + 2.2, y + 4.8, 2.7), kit.mat("lampshade", (1, 0.9, 0.7), emit=2.5 if lamp else 0, emit_color=(1, 0.85, 0.6)), verts=16)
    if lamp:
        kit.point((x + 2.2, y + 3.8, 3.2), (1, 0.82, 0.55), 260, 2.0)
    kit.point((x, y - 6, 8), (0.55, 0.6, 1.0), 120, 4.0)
    # a poster + desk so the room reads as a kid's room
    kit.box((2.6, 0.1, 3.4), (x - 4.5, y + 5.95, 6.5), kit.mat("poster", (0.9, 0.4, 0.2)), 0.02)
    kit.box((4.2, 2.2, 0.3), (x - 5.4, y - 3.0, 3.0), kit.mat("desk", (0.6, 0.45, 0.3)), 0.03)


def tracks(S):
    x, y = TR.x, TR.y
    kit.box((260, 160, 0.4), (x, y, -0.2), kit.mat("tgrass", (0.5, 0.66, 0.34), rough=0.95), 0)
    kit.box((260, 7, 0.5), (x, y, 0.05), kit.mat("gravel", (0.62, 0.58, 0.54), rough=1.0), 0)
    wood = kit.mat("sleeper", (0.35, 0.25, 0.18), rough=0.9)
    for i in range(-80, 81):
        kit.box((0.7, 5.2, 0.25), (x + i * 1.6, y, 0.42), wood, 0)
    steel = kit.mat("rail", (0.6, 0.6, 0.62), metal=0.9, rough=0.3)
    for ry in (-1.6, 1.6):
        kit.box((260, 0.3, 0.35), (x, y + ry, 0.7), steel, 0)
    kit.box((9, 40, 0.3), (x, y - 26, 0.05), kit.mat("tasph", (0.2, 0.2, 0.22), rough=0.9), 0)   # road to the crossing
    # crossing sign (white X on a post) + light
    post = kit.mat("tpost", (0.85, 0.85, 0.85))
    kit.box((0.3, 0.3, 7), (x + 6, y - 5, 3.5), post, 0)
    for a in (35, -35):
        b = kit.box((3.6, 0.2, 0.55), (x + 6, y - 5.15, 6.2), kit.mat("xsign", (0.95, 0.95, 0.95)), 0.02)
        b.rotation_euler = (0, R(a), 0)
    for dx in (-0.6, 0.6):
        kit.sphere(0.35, (x + 6 + dx, y - 5.25, 4.9), kit.mat("xlight", (0.9, 0.1, 0.1), emit=1.5, emit_color=(1, 0.1, 0.1)), seg=10)
    # schedule board
    kit.box((0.25, 0.25, 4.5), (x + 11, y - 7, 2.25), post, 0)
    kit.box((4.6, 0.25, 3.0), (x + 11, y - 7.1, 5.6), kit.mat("board", (0.12, 0.2, 0.32)), 0.04)
    text("NEXT TRAIN", (x + 11, y - 7.25, 6.3), size=0.6, color=(1, 1, 1), emit=1.0)
    text("4:15", (x + 11, y - 7.25, 4.75), size=1.2, color=(1, 0.8, 0.2), emit=2.5)
    # fence far side + a few trees
    kit.fence(x - 40, x + 40, y + 12, 1.2)
    for tx in (-24, -9, 14, 30):
        kit.tree((x + tx, y + 18), 1.6)


# ---------------------------------------------------------------- shots
def s01(k, F):  # In this town, your shadow moves ten seconds before you do.
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3540), 200, "smile")
    sh = shadow(S, (STREET_X, -3540), owner=milo)
    go = kf(F * 0.35)
    shuffle(sh, go, F)
    slide(sh, go, F, (STREET_X + SUN_DIR.x * 7, -3540 + SUN_DIR.y * 7))
    milo.look(kf(F * 0.5), -20, -25)
    S.drone([(1, V((STREET_X - 7, -3527, 12)), V((STREET_X + 1, -3542, 1))),
             (F, V((STREET_X - 5, -3532, 6)), V((STREET_X + 2, -3545, 1.0)))], lens=26)
    return S


def s02(k, F):  # So nobody ever trips. Your shadow trips first,
    S = street("day")
    crack(-3534)
    dev = place(S, "Dev", (STREET_X, -3528), 180, "smile")
    dev.walk(1, kf(F * 0.5), (STREET_X, -3531.5))
    sh = shadow(S, (STREET_X, -3531.5), owner=dev)
    trip = kf(F * 0.25)
    sh.arm("L", trip, 0, 160)
    sh.arm("R", trip, 0, 160)
    sh.leg("L", trip, 0, 30)
    slide(sh, trip, trip + 8, (STREET_X + 0.6, -3533.5))
    dev.face(kf(F * 0.55), "shocked")
    dev.look(kf(F * 0.55), 0, -30)
    wren = place(S, "Wren", (-7.5, -3500), 170, "neutral")      # easter egg, far background
    S.cam_at(V((STREET_X - 6, -3543, 3.4)), V((STREET_X, -3531, 1.8)), lens=30)
    return S


def s03(k, F):  # and you just step over it.
    S = street("day")
    crack(-3534)
    dev = place(S, "Dev", (STREET_X, -3532), 180, "smirk")
    dev.walk(1, F, (STREET_X, -3538))
    dev.leg("L", kf(F * 0.3), 60)
    sh = shadow(S, (STREET_X, -3536), owner=dev)
    shuffle(sh, 1, F)
    slide(sh, 1, F, (STREET_X, -3540))
    S.cam_at(V((STREET_X - 7, -3536, 3.0)), V((STREET_X, -3535, 2.0)), lens=32)
    return S


def s04(k, F):  # Hide and seek? Impossible. Your shadow always peeks out first.
    S = stage("day")
    tx, ty = STREET_X, -3535
    kit.tree((tx, ty), 1.5)
    rio = place(S, "Rio", (tx, ty + 1.9), 0, "smirk")             # hiding behind the tree
    sh = shadow(S, (tx, ty + 1.9), direction=(0, -1, 0), owner=rio, length=1.7)
    wave(sh, kf(F * 0.3), F, side="L", every=6)
    juno = place(S, "Juno", (tx - 1.0, ty - 12), 0, "laugh")
    juno.arm("R", kf(F * 0.45), 90)
    juno.look(kf(F * 0.4), 0, -20)
    S.cam_at(V((tx - 7.5, ty - 15, 6.0)), V((tx, ty - 3.5, 0.8)), lens=26)
    return S


def kitchen_set():
    S = stage("morning")
    kitchen(S, clock_time="7:42", morning=True)
    return S


def wall_shadow(S, owner, wx_off, y, model=None):
    """Shadow standing flat on the kitchen's left wall (inner face at KIT.x - 8.0)."""
    return shadow(S, (KIT.x - 7.95, y, 0.0), wall_normal=(1, 0, 0), model=model, owner=owner)


def s05(k, F):  # And my mom catches me at the cookie jar before I even get there.
    S = kitchen_set()
    jar = kit.cyl(0.6, 1.2, (KIT.x - 6.6, KIT.y + 6.4, 4.25), kit.mat("jar", (0.85, 0.75, 0.6), alpha=0.85), verts=16)
    milo = place(S, "Milo", (KIT.x - 4.2, KIT.y + 1.0), 300, "smirk")
    milo.walk(1, kf(F * 0.4), (KIT.x - 5.0, KIT.y + 3.0))
    milo.arm("L", kf(F * 0.4), 70)
    milo.face(kf(F * 0.55), "shocked")
    sh = wall_shadow(S, milo, 0, KIT.y + 4.2)
    sh.arm("L", 1, 0, 100)
    mom = place(S, "Mom", (KIT.x - 5.6, KIT.y - 3.0), 300, "angry")
    mom.arm("R", kf(F * 0.3), 100, 20)
    S.cam_at(V((KIT.x + 4, KIT.y - 7, 5.5)), V((KIT.x - 6.5, KIT.y + 2.5, 3.5)), lens=26)
    return S


def s06(k, F):  # My shadow was normal. Ten seconds ahead. Always ten.
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3520), 180, "smile")
    milo.walk(1, F, (STREET_X, -3534))
    sh = shadow(S, (STREET_X, -3521.5), owner=milo)
    shuffle(sh, 1, F)
    slide(sh, 1, F, (STREET_X, -3536))
    S.drone([(1, V((STREET_X - 7, -3530, 4.2)), V((STREET_X, -3522, 1.6))),
             (F, V((STREET_X - 7, -3542, 4.2)), V((STREET_X, -3535, 1.6)))], lens=30)
    return S


def s07(k, F):  # Until Tuesday.
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3530), 180, "neutral")
    milo.walk(kf(F * 0.4), F, (STREET_X, -3533))
    sh = shadow(S, (STREET_X, -3530), owner=milo)
    S.cam_at(V((STREET_X - 3.5, -3538, 2.6)), V((STREET_X + 0.5, -3531, 0.3)), lens=30, allow_close=True)
    return S


def s08(k, F):  # I waved. My shadow didn't.
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3533), 200, "smile")
    wave(milo, kf(F * 0.2), F, side="R")
    shadow(S, (STREET_X - 0.4, -3530), owner=milo)
    milo.face(kf(F * 0.6), "worried")
    S.cam_at(V((STREET_X - 8, -3545, 5)), V((STREET_X + 0.5, -3532, 1.4)), lens=30)
    return S


def s09(k, F):  # I jumped. It just stood there... like it was waiting for something.
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3533), 200, "worried")
    p = milo.pos
    for f, z in ((kf(F * 0.15), 0), (kf(F * 0.25), 2.2), (kf(F * 0.35), 0)):
        milo.key_root(f, (p.x, p.y, p.z + z))
    shadow(S, (STREET_X - 0.4, -3530), owner=milo)
    milo.look(kf(F * 0.5), -30, -30)
    S.drone([(1, V((STREET_X - 10, -3546, 6)), V((STREET_X, -3532, 1))),
             (F, V((STREET_X - 7, -3541, 4.2)), V((STREET_X, -3531, 0.8)))], lens=30)
    return S


def s10(k, F):  # My best friend Rio poked it with his shoe. "Bro. Is it broken?"
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3533), 200, "worried")
    sh = shadow(S, (STREET_X - 0.4, -3530), owner=milo)
    rio = place(S, "Rio", (STREET_X - 3.5, -3524), 160, "laugh")
    rio.leg("R", kf(F * 0.3), 50)
    rio.leg("R", kf(F * 0.45), 10)
    rio.leg("R", kf(F * 0.6), 50)
    rio.look(1, 0, -30)
    rio.talk(kf(F * 0.55), kf(F * 0.9), base="laugh")
    allow(S, "Narrator", "Crowd3", sh.name)
    S.cam_at(V((STREET_X - 9, -3536, 4.0)), V((STREET_X - 2.5, -3527, 1.4)), lens=30)
    return S


def bed_set(lamp=True):
    S = stage("night")
    bedroom(S, lamp)
    return S


def bed_milo(S, sit=False, expr="tired"):
    milo = place(S, "Milo", (BED.x + 5.4, BED.y + 2.5, 2.2), 0, expr)
    if sit:
        milo.sit(1)
    else:
        milo.lie(1, face_down=False)
    return milo


def wall_milo_shadow(S, milo):
    return shadow(S, (BED.x - 1.5, BED.y + 5.95, 0.4), wall_normal=(0, -1, 0), owner=milo)


def brushing(sh, f0, f1):
    sh.arm("R", f0, 0, 140)
    for j, f in enumerate(range(f0, f1 + 1, 4)):
        sh.arm("R", f, 0, 140 + (12 if j % 2 else -12))


def s11(k, F):  # That night, I saw it on my bedroom wall. Brushing its teeth.
    S = bed_set()
    milo = bed_milo(S)
    sh = wall_milo_shadow(S, milo)
    brushing(sh, 1, F)
    S.drone([(1, V((BED.x + 2, BED.y - 7, 6.5)), V((BED.x - 1.5, BED.y + 5.5, 4))),
             (F, V((BED.x + 1, BED.y - 4.5, 5.5)), V((BED.x - 1.5, BED.y + 5.5, 4)))], lens=26)
    return S


def s12(k, F):  # But I'd already brushed mine.
    S = bed_set()
    milo = bed_milo(S, sit=True, expr="tired")
    milo.face(kf(F * 0.3), "shocked")
    milo.look(kf(F * 0.3), 40, 0)
    sh = wall_milo_shadow(S, milo)
    brushing(sh, 1, F)
    S.cam_at(V((BED.x + 3.0, BED.y - 4.5, 6.8)), milo.head_pt() - V((0, 0, 0.8)), lens=30)
    return S


def s13(k, F):  # It wasn't ten seconds ahead anymore. It was doing tomorrow.
    S = bed_set()
    milo = bed_milo(S, sit=True, expr="scared")
    sh = wall_milo_shadow(S, milo)
    brushing(sh, 1, kf(F * 0.4))
    sh.arm("R", kf(F * 0.5), 0, 10)
    sh.look(kf(F * 0.6), 0, 0)
    sh.look(kf(F * 0.75), 60, 0)
    S.drone([(1, V((BED.x - 1.5, BED.y - 4, 5.5)), V((BED.x - 1.5, BED.y + 6, 4.5))),
             (F, V((BED.x - 1.5, BED.y - 0.5, 5.2)), V((BED.x - 1.5, BED.y + 6, 4.8)))], lens=30, allow_close=True)
    return S


def table(S):
    kit.box((5, 3.4, 0.3), (KIT.x + 1, KIT.y - 1, 2.6), kit.mat("ktable", (0.6, 0.45, 0.3)), 0.04)
    for dx in (-2.2, 2.2):
        for dy in (-1.4, 1.4):
            kit.box((0.25, 0.25, 2.5), (KIT.x + 1 + dx, KIT.y - 1 + dy, 1.25), kit.mat("ktable", (0.6, 0.45, 0.3)), 0)
    kit.cyl(0.7, 0.5, (KIT.x - 0.2, KIT.y - 1, 3.0), kit.mat("bowl", (0.95, 0.95, 0.95)), verts=16)


def s14(k, F):  # The next morning, I copied everything it did. Same cereal.
    S = kitchen_set()
    table(S)
    milo = place(S, "Milo", (KIT.x - 2.2, KIT.y - 1, 0), 270, "neutral")
    sh = wall_shadow(S, milo, 0, KIT.y - 1)
    for j, f in enumerate(range(1, F, 14)):
        sh.arm("R", f, 0, 120 if j % 2 else 40)
        milo.arm("R", f + 7, 120 if j % 2 else 40)
    S.cam_at(V((KIT.x + 6, KIT.y - 8, 5.5)), V((KIT.x - 5, KIT.y, 3.5)), lens=26)
    return S


def s15(k, F):  # Same shoelaces. Same sneeze.
    S = kitchen_set()
    table(S)
    milo = place(S, "Milo", (KIT.x - 3.0, KIT.y + 1.5, 0), 270, "neutral")
    sh = wall_shadow(S, milo, 0, KIT.y + 1.5)
    tie, sneeze = kf(F * 0.15), kf(F * 0.6)
    for c, d in ((sh, 0), (milo, 6)):
        c.lean(tie + d, 35)
        c.arm("L", tie + d, 60 if c is milo else 0, 0 if c is milo else 60)
        c.lean(sneeze - 10 + d, 0)
        c.lean(sneeze + d, -12)
        c.lean(sneeze + 4 + d, 22)
        c.lean(sneeze + 10 + d, 0)
    milo.face(sneeze + 6, "embarrassed")
    pip = place(S, "Pip", (KIT.x + 2.5, KIT.y - 2.5, 0), 300, "neutral")
    pip.face(sneeze + 10, "shocked")
    S.cam_at(V((KIT.x + 7, KIT.y - 7, 5.0)), V((KIT.x - 4.5, KIT.y + 1.0, 3.0)), lens=26)
    return S


def s16(k, F):  # It was right. Every single time.
    S = kitchen_set()
    milo = place(S, "Milo", (KIT.x - 3.5, KIT.y + 1.5, 0), 270, "worried")
    sh = wall_shadow(S, milo, 0, KIT.y + 1.5)
    milo.look(1, 0, 0)
    milo.look(kf(F * 0.4), -35, 5)
    sh.look(kf(F * 0.25), 35, 0)
    S.cam_at(V((KIT.x + 4.5, KIT.y - 3.5, 5.0)), milo.head_pt() - V((0, 0, 1.0)), lens=30)
    return S


def s17(k, F):  # Then, after school, my shadow started running.
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3508), 180, "shocked")
    sh = shadow(S, (STREET_X, -3508), direction=(0, -1, 0), owner=milo)
    go = kf(F * 0.15)
    shuffle(sh, go, F, every=4, amp=28)
    slide(sh, go, F, (STREET_X, -3540))
    milo.arm("R", kf(F * 0.4), 90)
    S.drone([(1, V((STREET_X - 6, -3499, 6)), V((STREET_X, -3512, 1))),
             (F, V((STREET_X - 6, -3503, 9)), V((STREET_X, -3530, 0.5)))], lens=26)
    return S


def s18(k, F):  # Rio and I chased it across town, all the way to the train tracks.
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3500), 180, "determined")
    rio = place(S, "Rio", (STREET_X - 3.8, -3497), 180, "laugh")
    milo.run(1, F, (STREET_X, -3556))
    rio.run(1, F, (STREET_X - 3.8, -3552))
    allow(S, "Narrator", "Crowd3")
    S.drone([(1, V((STREET_X - 12, -3512, 4)), V((STREET_X - 1, -3500, 2.5))),
             (F, V((STREET_X - 12, -3566, 5)), V((STREET_X - 1, -3554, 2.5)))], lens=26)
    return S


def track_set():
    S = stage("sunset")
    tracks(S)
    return S


def s19(k, F):  # There, it stopped. It turned around.
    S = track_set()
    sh = shadow(S, (TR.x - 9, TR.y - 5.2), direction=(-1, 0, 0), model="Prey2")
    turn = kf(F * 0.5)
    sh.look(turn - 6, 0, 0)
    sh.look(turn, 70, 0)
    S.cam_at(V((TR.x - 9, TR.y - 17, 4.8)), V((TR.x - 12, TR.y - 5, 0.3)), lens=30)
    return S


def s20(k, F):  # And it waved goodbye.
    S = track_set()
    milo = place(S, "Milo", (TR.x + 2, TR.y - 13), 50, "scared")
    sh = shadow(S, (TR.x - 9, TR.y - 5.2), direction=(-1, 0, 0), owner=milo)
    wave(sh, kf(F * 0.15), F, side="R", every=10, base=140, amp=30)
    S.cam_at(V((TR.x + 1, TR.y - 21, 5.5)), V((TR.x - 9, TR.y - 5, 0.8)), lens=30)
    return S


def s21(k, F):  # Then it stepped onto the tracks... and faded away.
    S = track_set()
    sh = shadow(S, (TR.x - 9, TR.y - 5.2), direction=(-1, 0, 0), model="Prey2")
    shuffle(sh, 1, kf(F * 0.5))
    slide(sh, 1, kf(F * 0.5), (TR.x - 9, TR.y + 0.2), z=0.6)
    fade_shadow(sh, kf(F * 0.45), kf(F * 0.85))
    S.cam_at(V((TR.x - 3, TR.y - 15, 6)), V((TR.x - 10, TR.y - 1.5, 0.5)), lens=30)
    return S


def s22(k, F):  # Across the tracks, a girl in a white hoodie was waving too.
    S = track_set()
    wren = place(S, "Wren", (TR.x - 2, TR.y + 8), 180, "neutral")
    wave(wren, kf(F * 0.2), F, side="R", every=12, base=150, amp=20)
    S.drone([(1, V((TR.x - 2, TR.y - 18, 4.2)), V((TR.x - 2, TR.y + 8, 3.6))),
             (F, V((TR.x - 2, TR.y - 9, 4.0)), V((TR.x - 2, TR.y + 8, 3.8)))], lens=34)
    return S


def kids_at_tracks(S, pip_expr="worried"):
    milo = place(S, "Milo", (TR.x - 3, TR.y - 9), 0, "scared")
    rio = place(S, "Rio", (TR.x + 1.5, TR.y - 9.5), 0, "worried")
    pip = place(S, "Pip", (TR.x - 6.2, TR.y - 10.5), 330, pip_expr)
    allow(S, "Narrator", "Crowd3", "Smallkid")
    return milo, rio, pip


def s23(k, F):  # My little sister Pip grabbed my hand. "Milo... where's your shadow?"
    S = track_set()
    milo, rio, pip = kids_at_tracks(S)
    pip.arm("R", kf(F * 0.2), 40, -30)
    pip.look(kf(F * 0.4), 0, -35)
    pip.talk(kf(F * 0.45), kf(F * 0.9), base="worried")
    milo.look(kf(F * 0.3), 30, -10)
    for c, xy in ((rio, (TR.x + 1.5, TR.y - 9.5)), (pip, (TR.x - 6.2, TR.y - 10.5))):
        shadow(S, xy, owner=c, direction=(0.5, -0.86, 0), length=1.25)
    S.cam_at(V((TR.x - 6, TR.y - 21, 4.5)), V((TR.x - 3, TR.y - 9.5, 2.6)), lens=32)
    return S


def s24(k, F):  # I looked down.
    S = track_set()
    milo, rio, pip = kids_at_tracks(S)
    milo.look(kf(F * 0.2), 0, -45)
    S.cam(milo.head_pt() - V((0, 0, 1.0)), dist=7, yaw=180, height=milo.head_pt().z + 0.5, lens=34)
    return S


def s25(k, F):  # I didn't have one.
    S = track_set()
    milo, rio, pip = kids_at_tracks(S, "scared")
    for c, xy in ((rio, (TR.x + 1.5, TR.y - 9.5)), (pip, (TR.x - 6.2, TR.y - 10.5))):
        shadow(S, xy, owner=c, direction=(0.5, -0.86, 0), length=1.3)
    milo.look(1, 0, -45)
    S.drone([(1, V((TR.x - 2.5, TR.y - 12.5, 22)), V((TR.x - 2.5, TR.y - 10.5, 0))),
             (F, V((TR.x - 2.8, TR.y - 11.0, 14)), V((TR.x - 2.8, TR.y - 10.0, 0)))], lens=30, allow_close=True)
    return S


def s26(k, F):  # The next train comes tomorrow. Four fifteen.
    S = track_set()
    S.drone([(1, V((TR.x + 11, TR.y - 15, 5.4)), V((TR.x + 11, TR.y - 7, 5.4))),
             (F, V((TR.x + 11, TR.y - 12.5, 5.2)), V((TR.x + 11, TR.y - 7, 5.0)))], lens=34, allow_close=True)
    return S


def s27(k, F):  # What do I do?
    S = track_set()
    milo = place(S, "Milo", (TR.x - 3, TR.y - 9), 0, "scared")
    milo.look(kf(F * 0.4), 0, -20)
    S.drone([(1, V((TR.x - 3, TR.y - 15, 4.4)), V((TR.x - 3, TR.y - 9, 3.6))),
             (F, V((TR.x - 1, TR.y - 26, 7.5)), V((TR.x - 3, TR.y - 6, 2.5)))], lens=30)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 28)}
