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


def yaw_to(a, b):
    """Rig yaw that makes a character at a face toward b (forward is -Y at yaw 0)."""
    return math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1])))


def face(c, target, f=None):
    """Turn a character toward a point (the camera, another character...)."""
    y = yaw_to(c.pos, target)
    c.root.rotation_euler.z = math.pi + R(y)
    if f is not None:
        c.key_root(f, yaw=y)


def allow(S, *names):
    for a in names:
        for b in names:
            if a != b:
                S.allow_close.add((a, b))


# ---------------------------------------------------------------- shadows
# A shadow is a spare character standing upright (posed like a person), whose whole rig is PROJECTED flat onto
# the ground or a wall along the light direction (a projection matrix in the root's parent-inverse). So feet stay
# attached, poses read as real silhouettes, and it can either copy its owner a few frames AHEAD (follow) or act on
# its own (free). Life-layer noise is stripped from shadow rigs so they don't jitter.
from mathutils import Matrix  # noqa: E402

LIGHT = {"street": V((-0.3, -1.3, -1.0)), "tracks": V((-0.45, -1.4, -1.0)),
         "kitchen": V((-1.0, 0.12, -0.18)), "bedroom": V((0.08, 1.0, -0.14))}
EPS = 0.004


def _proj_ground(L, z0):
    a, b = L.x / L.z, L.y / L.z
    return Matrix(((1, 0, -a, a * z0), (0, 1, -b, b * z0), (0, 0, EPS, z0 * (1 - EPS) + 0.03), (0, 0, 0, 1)))


def _proj_wall_x(L, wx, side=1):
    a, b = L.y / L.x, L.z / L.x
    return Matrix(((EPS, 0, 0, wx * (1 - EPS) + 0.03 * side), (-a, 1, 0, a * wx), (-b, 0, 1, b * wx), (0, 0, 0, 1)))


def _proj_wall_y(L, wy, side=-1):
    a, b = L.x / L.y, L.z / L.y
    return Matrix(((1, -a, 0, a * wy), (0, EPS, 0, wy * (1 - EPS) + 0.03 * side), (0, -b, 1, b * wy), (0, 0, 0, 1)))


def _parts(c):
    return [c.root, c.body, c.neck, c.arms["L"], c.arms["R"], c.legs["L"], c.legs["R"]]


def make_shadow(S, at, yaw, light, plane=("ground", 0.0), model=None):
    """Shadow rig standing at `at` facing `yaw`, projected onto plane ("ground", z0) | ("wall_x", x) | ("wall_y", y)."""
    used = set(S.chars)
    model = model or next(m for m in POOL if m not in used)
    c = S.char(model, at, yaw, "neutral")
    kind, v = plane
    L = V(light)
    P = _proj_ground(L, v) if kind == "ground" else (_proj_wall_x(L, v) if kind == "wall_x" else _proj_wall_y(L, v))
    c.root.parent = None
    c.root.matrix_parent_inverse = Matrix.Identity(4)
    e = kit.empty((0, 0, 0), name="shadowproj_" + model)
    c.root.parent = e
    c.root.matrix_parent_inverse = P
    m = kit.mat("shadowmat", (0.012, 0.012, 0.02), rough=1.0)
    m.shadow_method = "NONE"

    def finish():
        for o in _parts(c):                              # no jitter on shadows
            ad = o.animation_data
            if ad and ad.action:
                for fc in ad.action.fcurves:
                    for md in list(fc.modifiers):
                        fc.modifiers.remove(md)
        for o in _char_objs(c):
            for sl in o.material_slots:
                sl.link = "OBJECT"
                sl.material = m
    S.post_hooks.append(finish)
    S.shadows.append(c)
    for other in list(S.chars):
        allow(S, other, c.name)
    return c


def follow(S, owner, light, plane=None, lead=6, model=None, after=None):
    """Shadow that copies its owner's whole animation `lead` frames AHEAD (the town's rule), feet attached."""
    plane = plane or ("ground", owner.pos.z)
    yaw = math.degrees(owner.root.rotation_euler.z - math.pi)
    sh = make_shadow(S, tuple(owner.pos), yaw, light, plane, model)

    def copy():
        for src, dst in zip(_parts(owner), _parts(sh)):
            sad = src.animation_data
            if not (sad and sad.action):
                continue
            dad = dst.animation_data or dst.animation_data_create()
            if not dad.action:
                dad.action = bpy.data.actions.new(dst.name + "_shadow")
            for fc in sad.action.fcurves:
                off = 0 if (src is owner.root and fc.data_path == "location") else lead   # feet stay attached
                d = dad.action.fcurves.find(fc.data_path, index=fc.array_index)
                if d is None:
                    d = dad.action.fcurves.new(fc.data_path, index=fc.array_index)
                d.keyframe_points.clear()
                for kp in fc.keyframe_points:
                    k = d.keyframe_points.insert(kp.co.x - off, kp.co.y)
                    k.interpolation = kp.interpolation
        if after:
            after(sh)
    S.post_hooks.insert(0, copy)          # copy before the shadow's own clean-up hook runs
    return sh


def fade_shadow(c, f0, f1):
    """Fade a shadow out (own material copy, alpha), e.g. stepping onto the tracks."""
    m = kit.mat("shadowfade_" + c.name, (0.012, 0.012, 0.02), rough=1.0, alpha=0.999)
    m.shadow_method = "NONE"
    b = m.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
    for f, v in ((f0, 1.0), (f1, 0.0)):
        b.default_value = v
        b.keyframe_insert("default_value", frame=f)

    def apply():
        for o in _char_objs(c):
            for sl in o.material_slots:
                sl.link = "OBJECT"
                sl.material = m
    c.S.post_hooks.append(apply)


def wave(c, f0, f1, side="R", every=8, base=160, amp=22):
    for j, f in enumerate(range(f0, f1 + 1, every)):
        c.arm(side, f, 0, base + (amp if j % 2 else -amp))


def slide(c, f0, f1, to, z=None):
    p = c.pos
    c.key_root(f0, (p.x, p.y, p.z if z is None else z))
    c.key_root(f1, (to[0], to[1], p.z if z is None else z))


# ---------------------------------------------------------------- sets
def street(light="day"):
    return stage(light)


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
ST = LIGHT["street"]
TL = LIGHT["tracks"]
KW = ("wall_x", KIT.x - 7.98)            # kitchen left wall (inner face)
BW = ("wall_y", BED.y + 5.98)            # bedroom back wall (inner face)
KL = V((-1.0, 0.12, 0.0))
BL = V((0.06, 1.0, 0.0))


def walker(S, who, a, b, f0, f1, expr="smile", run=False):
    """Character that walks/runs from a to b FACING its direction of travel."""
    c = place(S, who, a, yaw_to(a, b), expr)
    (c.run if run else c.walk)(f0, f1, b)
    return c


def s01(k, F):  # In this town, your shadow moves ten seconds before you do.
    S = street("day")
    cam = V((STREET_X - 6, -3528, 9))
    milo = place(S, "Milo", (STREET_X, -3538), 0, "smile")
    face(milo, cam)
    sh = make_shadow(S, (STREET_X, -3538, 0.6), 0, ST, ("ground", 0.6))
    sh.walk(kf(F * 0.3), F, (STREET_X - 0.4, -3547, 0.6))
    milo.look(kf(F * 0.45), 15, -30)
    milo.face(kf(F * 0.55), "shocked")
    S.drone([(1, cam, V((STREET_X, -3541, 1))), (F, V((STREET_X - 5, -3531, 6)), V((STREET_X, -3544, 1.0)))], lens=26)
    return S


def s02(k, F):  # So nobody ever trips. Your shadow trips first,
    S = street("day")
    crack(-3536)
    stop = kf(F * 0.55)
    dev = walker(S, "Dev", (STREET_X, -3527), (STREET_X, -3533.5), 1, stop)
    dev.face(stop, "shocked")
    dev.look(stop, 0, -30)

    def trip(sh):
        t = kf(F * 0.3)
        sh.lean(t, 0)
        sh.lean(t + 6, 55)
        for sd in "LR":
            sh.arm(sd, t + 4, 150, 30)
        sh.leg("R", t + 4, -40)
    follow(S, dev, ST, lead=10, after=trip)
    place(S, "Wren", (-11.5, -3505), 0, "neutral")
    S.cam_at(V((STREET_X - 4.5, -3547, 3.6)), V((STREET_X, -3532, 2.0)), lens=30)
    return S


def s03(k, F):  # and you just step over it.
    S = street("day")
    crack(-3536)
    dev = walker(S, "Dev", (STREET_X, -3533.5), (STREET_X, -3540), 1, F, "smirk")
    dev.leg("L", kf(F * 0.35), 70)
    follow(S, dev, ST, lead=8)
    S.cam_at(V((STREET_X - 5, -3548, 3.2)), V((STREET_X, -3537, 1.8)), lens=30)
    return S


def s04(k, F):  # Hide and seek? Impossible. Your shadow always peeks out first.
    S = stage("day")
    tx, ty = STREET_X, -3535
    kit.tree((tx, ty), 1.5)
    place(S, "Rio", (tx, ty + 1.9), 0, "smirk")
    sh = make_shadow(S, (tx, ty + 1.9, 0.6), 0, V((-0.15, -1.7, -1.0)), ("ground", 0.6))
    sh.lean(kf(F * 0.25), 25, -20)
    wave(sh, kf(F * 0.3), F, side="L", every=6)
    juno = place(S, "Juno", (tx - 1.5, ty - 11), 180, "laugh")
    follow(S, juno, ST, lead=6)
    juno.arm("R", kf(F * 0.45), 90)
    S.cam_at(V((tx - 12, ty - 3, 5.0)), V((tx - 1.0, ty - 6, 1.6)), lens=24)
    return S


def kitchen_set():
    S = stage("morning")
    kitchen(S, clock_time="7:42", morning=True)
    return S


def s05(k, F):  # And my mom catches me at the cookie jar before I even get there.
    S = kitchen_set()
    kit.cyl(0.6, 1.2, (KIT.x - 6.6, KIT.y + 6.4, 4.25), kit.mat("jar", (0.85, 0.75, 0.6)), verts=16)
    reach = kf(F * 0.45)
    milo = walker(S, "Milo", (KIT.x - 3.0, KIT.y - 1.0, 0), (KIT.x - 4.8, KIT.y + 3.6, 0), 1, reach, "smirk")
    milo.arm("R", reach, 80)
    milo.face(reach, "shocked")
    follow(S, milo, KL, KW, lead=14)
    mom = place(S, "Mom", (KIT.x - 5.8, KIT.y - 3.0, 0), 0, "angry")
    face(mom, (KIT.x - 4.8, KIT.y + 3.6))
    mom.arm("L", kf(F * 0.3), 100, -25)
    follow(S, mom, KL, KW, lead=6)
    S.cam_at(V((KIT.x + 5, KIT.y + 3, 6.0)), V((KIT.x - 5.5, KIT.y + 0.5, 3.0)), lens=24)
    return S


def s06(k, F):  # My shadow was normal. Ten seconds ahead. Always ten.
    S = street("day")
    milo = walker(S, "Milo", (STREET_X, -3520), (STREET_X, -3534), 1, F)
    follow(S, milo, ST, lead=8)
    S.drone([(1, V((STREET_X + 1.5, -3531, 8.5)), V((STREET_X, -3521, 1.2))),
             (F, V((STREET_X + 1.5, -3545, 8.5)), V((STREET_X, -3535, 1.2)))], lens=26, allow_close=True)
    return S


def stuck_shadow(S, x, y):
    return make_shadow(S, (x, y, 0.6), 0, ST, ("ground", 0.6))


def s07(k, F):  # Until Tuesday.
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3530), 0, "neutral")
    milo.walk(kf(F * 0.4), F, (STREET_X, -3534))
    stuck_shadow(S, STREET_X, -3530)
    S.cam_at(V((STREET_X - 3, -3543, 3.6)), V((STREET_X, -3533, 1.0)), lens=30, allow_close=True)
    return S


def s08(k, F):  # I waved. My shadow didn't.
    S = street("day")
    cam = V((STREET_X - 6, -3547, 4.6))
    milo = place(S, "Milo", (STREET_X, -3535), 0, "smile")
    face(milo, cam)
    wave(milo, kf(F * 0.2), F, side="R")
    milo.face(kf(F * 0.6), "worried")
    stuck_shadow(S, STREET_X, -3531)
    S.cam_at(cam, V((STREET_X, -3533, 1.6)), lens=30)
    return S


def s09(k, F):  # I jumped. It just stood there... like it was waiting for something.
    S = street("day")
    cam = V((STREET_X - 8, -3549, 6))
    milo = place(S, "Milo", (STREET_X, -3535), 0, "worried")
    face(milo, cam)
    p = milo.pos
    for f, z in ((kf(F * 0.15), 0), (kf(F * 0.25), 2.2), (kf(F * 0.35), 0)):
        milo.key_root(f, (p.x, p.y, p.z + z))
    stuck_shadow(S, STREET_X, -3531)
    milo.look(kf(F * 0.5), 20, -30)
    S.drone([(1, cam, V((STREET_X, -3533, 1.2))), (F, V((STREET_X - 6, -3544, 4.2)), V((STREET_X, -3532, 1.0)))], lens=30)
    return S


def s10(k, F):  # My best friend Rio poked it with his shoe. "Bro. Is it broken?"
    S = street("day")
    cam = V((STREET_X + 1.5, -3543, 4.2))
    milo = place(S, "Milo", (STREET_X + 1.6, -3535), 0, "worried")
    face(milo, cam)
    stuck_shadow(S, STREET_X, -3531)
    rio = place(S, "Rio", (STREET_X - 3.0, -3531), 0, "laugh")
    face(rio, (STREET_X, -3531))
    follow(S, rio, ST, lead=6)
    for f, a in ((kf(F * 0.25), 50), (kf(F * 0.4), 10), (kf(F * 0.55), 50), (kf(F * 0.7), 10)):
        rio.leg("R", f, a)
    rio.look(1, -20, -30)
    rio.look(kf(F * 0.55), -45, 0)
    rio.talk(kf(F * 0.55), kf(F * 0.9), base="laugh")
    allow(S, "Narrator", "Crowd3")
    S.cam_at(cam, V((STREET_X - 1.0, -3532, 1.4)), lens=28)
    return S


def bed_set(lamp=True):
    S = stage("night")
    bedroom(S, lamp)
    return S


def bed_milo(S, sit=False, expr="tired"):
    if sit:     # on the edge of the bed, turned toward the shadow on the wall
        milo = place(S, "Milo", (BED.x + 2.9, BED.y + 1.0, 2.3 - 1.5), 0, expr)   # hips on the mattress (top 2.3)
        face(milo, (BED.x - 1.5, BED.y + 5.9))
        milo.sit(1)
    else:       # under the blanket, head on the pillow
        milo = place(S, "Milo", (BED.x + 5.4, BED.y + 3.8, 2.3), 180, expr)
        milo.lie(1, face_down=False)
    return milo


def wall_milo_shadow(S):
    """Milo's shadow on the bedroom wall, standing on its own (no one is casting it)."""
    return make_shadow(S, (BED.x - 1.5, BED.y + 3.0, 0.0), 180, BL, BW)


def brushing(sh, f0, f1):
    sh.arm("R", f0, 120, -40)
    for j, f in enumerate(range(f0, f1 + 1, 4)):
        sh.arm("R", f, 120, -40 + (14 if j % 2 else -14))


def s11(k, F):  # That night, I saw it on my bedroom wall. Brushing its teeth.
    S = bed_set()
    bed_milo(S)
    sh = wall_milo_shadow(S)
    brushing(sh, 1, F)
    S.drone([(1, V((BED.x + 2, BED.y - 7, 6.5)), V((BED.x - 1.5, BED.y + 5.5, 4))),
             (F, V((BED.x + 1, BED.y - 4.5, 5.5)), V((BED.x - 1.5, BED.y + 5.5, 4)))], lens=26)
    return S


def s12(k, F):  # But I'd already brushed mine.
    S = bed_set()
    milo = bed_milo(S, sit=True, expr="tired")
    milo.face(kf(F * 0.3), "shocked")
    milo.look(kf(F * 0.3), 40, 0)
    sh = wall_milo_shadow(S)
    brushing(sh, 1, F)
    S.cam_at(V((BED.x - 3.5, BED.y - 5.5, 5.4)), V((BED.x + 1.6, BED.y + 2.6, 3.2)), lens=24)
    return S


def s13(k, F):  # It wasn't ten seconds ahead anymore. It was doing tomorrow.
    S = bed_set()
    bed_milo(S, sit=True, expr="scared")
    sh = wall_milo_shadow(S)
    brushing(sh, 1, kf(F * 0.4))
    sh.arm("R", kf(F * 0.5), 0, 0)
    sh.look(kf(F * 0.6), 0, 0)
    sh.look(kf(F * 0.75), 70, 0)
    S.drone([(1, V((BED.x - 1.5, BED.y - 4, 5.5)), V((BED.x - 1.5, BED.y + 6, 4.5))),
             (F, V((BED.x - 1.5, BED.y - 0.5, 5.2)), V((BED.x - 1.5, BED.y + 6, 4.8)))], lens=30, allow_close=True)
    return S


def table(S):
    m = kit.mat("ktable", (0.6, 0.45, 0.3))
    kit.box((5, 3.4, 0.3), (KIT.x + 1, KIT.y - 1, 2.6), m, 0.04)
    for dx in (-2.2, 2.2):
        for dy in (-1.4, 1.4):
            kit.box((0.25, 0.25, 2.5), (KIT.x + 1 + dx, KIT.y - 1 + dy, 1.25), m, 0)
    kit.cyl(0.7, 0.5, (KIT.x - 0.2, KIT.y - 1, 3.0), kit.mat("bowl", (0.95, 0.95, 0.95)), verts=16)


def s14(k, F):  # The next morning, I copied everything it did. Same cereal.
    S = kitchen_set()
    table(S)
    milo = place(S, "Milo", (KIT.x - 2.4, KIT.y - 1, 0), 270, "neutral")
    for j, f in enumerate(range(1, F, 12)):
        milo.arm("R", f, 110 if j % 2 else 45)
    follow(S, milo, KL, KW, lead=8)
    S.cam_at(V((KIT.x - 5, KIT.y - 7.5, 5.5)), V((KIT.x - 5, KIT.y + 0.5, 3.2)), lens=24)
    return S


def s15(k, F):  # Same shoelaces. Same sneeze.
    S = kitchen_set()
    table(S)
    milo = place(S, "Milo", (KIT.x - 3.0, KIT.y + 1.5, 0), 270, "neutral")
    tie, sneeze = kf(F * 0.15), kf(F * 0.6)
    milo.lean(tie, 40)
    milo.arm("L", tie, 70)
    milo.arm("R", tie, 70)
    milo.lean(sneeze - 10, 0)
    for sd in "LR":
        milo.arm(sd, sneeze - 10, 0)
    milo.lean(sneeze, -14)
    milo.lean(sneeze + 4, 24)
    milo.lean(sneeze + 10, 0)
    milo.face(sneeze + 4, "embarrassed")
    follow(S, milo, KL, KW, lead=8)
    pip = place(S, "Pip", (KIT.x + 2.5, KIT.y - 2.5, 0), 300, "neutral")
    pip.face(sneeze + 10, "shocked")
    follow(S, pip, KL, KW, lead=6)
    S.cam_at(V((KIT.x - 5, KIT.y - 7.0, 5.5)), V((KIT.x - 5, KIT.y + 1.5, 3.2)), lens=24)
    return S


def s16(k, F):  # It was right. Every single time.
    S = kitchen_set()
    milo = place(S, "Milo", (KIT.x - 3.5, KIT.y + 1.5, 0), 270, "worried")
    milo.look(kf(F * 0.4), -35, 5)
    sh = make_shadow(S, (KIT.x - 3.5, KIT.y + 1.5, 0), 270, KL, KW)
    sh.look(kf(F * 0.25), -60, 0)                      # it looks at him first
    S.cam_at(V((KIT.x - 5.5, KIT.y - 5.0, 5.2)), V((KIT.x - 5.0, KIT.y + 2.0, 3.6)), lens=26)
    return S


def s17(k, F):  # Then, after school, my shadow started running.
    S = street("day")
    milo = place(S, "Milo", (STREET_X, -3508), 180, "shocked")
    sh = make_shadow(S, (STREET_X, -3508, 0.6), 0, ST, ("ground", 0.6))
    go = kf(F * 0.15)
    sh.run(go, F, (STREET_X, -3536, 0.6))
    milo.arm("R", kf(F * 0.4), 90)
    S.drone([(1, V((STREET_X - 6, -3499, 6)), V((STREET_X, -3512, 1))),
             (F, V((STREET_X - 6, -3503, 9)), V((STREET_X, -3530, 0.5)))], lens=26)
    return S


def s18(k, F):  # Rio and I chased it across town, all the way to the train tracks.
    S = street("day")
    milo = walker(S, "Milo", (STREET_X, -3500), (STREET_X, -3556), 1, F, "determined", run=True)
    rio = walker(S, "Rio", (STREET_X - 3.8, -3497), (STREET_X - 3.8, -3552), 1, F, "laugh", run=True)
    follow(S, rio, ST, ("ground", 0.2), lead=6)          # Rio still has his; Milo's is gone
    allow(S, "Narrator", "Crowd3")
    S.drone([(1, V((STREET_X - 9, -3514, 4)), V((STREET_X - 2, -3500, 2.5))),
             (F, V((STREET_X - 9, -3568, 5)), V((STREET_X - 2, -3554, 2.5)))], lens=26)
    return S


def track_set():
    S = stage("sunset")
    tracks(S)
    return S


def track_shadow(S, x, y, yaw=270):
    return make_shadow(S, (x, y, 0.0), yaw, TL, ("ground", 0.0), model="Prey2")


def s19(k, F):  # There, it stopped. It turned around.
    S = track_set()
    west = yaw_to((0, 0), (-1, 0))
    sh = track_shadow(S, TR.x - 2, TR.y - 5.5, yaw=west)
    sh.walk(1, kf(F * 0.3), (TR.x - 5, TR.y - 5.5, 0.0))
    turn = kf(F * 0.55)
    sh.key_root(turn, yaw=west)
    sh.key_root(turn + 8, yaw=0)
    S.cam_at(V((TR.x - 6, TR.y - 22, 8.5)), V((TR.x - 5, TR.y - 9, 0.3)), lens=30)
    return S


def s20(k, F):  # And it waved goodbye.
    S = track_set()
    sh = track_shadow(S, TR.x - 5, TR.y - 5.5, yaw=0)
    wave(sh, kf(F * 0.15), F, side="R", every=10, base=165, amp=25)
    S.cam_at(V((TR.x - 3, TR.y - 22, 8.5)), V((TR.x - 5.5, TR.y - 9, 0.6)), lens=30)
    return S


def s21(k, F):  # Then it stepped onto the tracks... and faded away.
    S = track_set()
    sh = track_shadow(S, TR.x - 5, TR.y - 5.5, yaw=180)
    sh.walk(1, kf(F * 0.5), (TR.x - 5, TR.y - 0.5, 0.0))
    fade_shadow(sh, kf(F * 0.45), kf(F * 0.85))
    S.cam_at(V((TR.x - 2, TR.y - 20, 8.5)), V((TR.x - 5, TR.y - 4, 0.5)), lens=30)
    return S


def s22(k, F):  # Across the tracks, a girl in a white hoodie was waving too.
    S = track_set()
    wren = place(S, "Wren", (TR.x - 2, TR.y + 8), 0, "neutral")    # no shadow (series clue)
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
    follow(S, rio, TL, ("ground", 0.0), lead=6)
    follow(S, pip, TL, ("ground", 0.0), lead=6)
    S.cam_at(V((TR.x - 6, TR.y - 21, 4.5)), V((TR.x - 3, TR.y - 9.5, 2.6)), lens=32)
    return S


def s24(k, F):  # I looked down.
    S = track_set()
    milo, rio, pip = kids_at_tracks(S)
    follow(S, rio, TL, ("ground", 0.0), lead=6)
    follow(S, pip, TL, ("ground", 0.0), lead=6)
    milo.look(kf(F * 0.2), 0, -45)
    S.cam_at(V((TR.x - 1, TR.y - 15.5, 4.6)), milo.head_pt() - V((0, 0, 0.6)), lens=32)
    return S


def s25(k, F):  # I didn't have one.
    S = track_set()
    milo, rio, pip = kids_at_tracks(S, "scared")
    follow(S, rio, TL, ("ground", 0.0), lead=6)
    follow(S, pip, TL, ("ground", 0.0), lead=6)
    milo.look(1, 0, -45)
    S.drone([(1, V((TR.x - 3.5, TR.y - 11.5, 24)), V((TR.x - 3.5, TR.y - 10.0, 0))),
             (F, V((TR.x - 3.5, TR.y - 10.5, 16)), V((TR.x - 3.5, TR.y - 9.8, 0)))], lens=30, allow_close=True)
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
