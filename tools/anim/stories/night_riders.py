"""night-riders ("Night Riders") - lyric video for Aneesa - "Raat Ka Nasha" (song 0:10.3-0:45.3).

His last night in town. Two friends ride bikes through the dark streets; every street lamp flicks on as
they pass. They race the clock, launch off a ramp ("I don't chase, I don't wait, I decide") and on the drop
("Raat ka nasha") the whole town lights up with fireworks. They end on the hill, watching.

Shots are cut to the song's beats (~102 BPM). Narrator = the one leaving, Rio = Crowd3.
Sets (reused): the main street with its lamps (the_knock), our house/porch (the_knock) for the moving truck.
"""
import math
import random

import bpy
from mathutils import Vector

import kit
import rblx
from rblx import attach, kf
from stories.five_seconds import car
from stories.nothing_happens import text
from stories.the_knock import P, porch, stage

R = math.radians
V = Vector
PACK = "alpha-mark"
RIO = "Crowd3"
X_ME, X_RIO = 3.6, -0.6           # lanes on the main street (riding toward +Y)
Y0, Y_RAMP = -3590.0, -3470.0      # street start / ramp at the far end
HILL = V((1.5, Y_RAMP + 16, 0))    # little grass hill past the ramp, looking back down the street


# ---------------------------------------------------------------- lights
def night():
    S = stage("night")
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.1
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.data.type == "SUN":
            o.data.energy *= 1.8
    return S


def hill_z(x, y):
    """Ground height on the hill ellipsoid (centre HILL + (0, 8, -10.5), radii 22.4 x 16.8 x 14)."""
    dx, dy = (x - HILL.x) / 22.4, (y - HILL.y - 8) / 16.8
    q = 1 - dx * dx - dy * dy
    return max(0.0, -10.5 + 14 * math.sqrt(q)) if q > 0 else 0.0


def bulbs():
    return [o for o in bpy.data.objects if o.name.startswith("Lampbulb")]


def _bulb_switch(o, f_on, k, power=600):
    m = kit.mat("nrbulb%d" % k, (1, 0.9, 0.6), emit=0.0001, emit_color=(1, 0.85, 0.5))
    o.data.materials.clear()
    o.data.materials.append(m)
    sock = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    c = o.matrix_world.translation
    L = kit.point(tuple(c - V((0, 0, 0.6))), (1, 0.85, 0.55), 0, 1.0)
    keys = [(1, 0.0, 0)] if f_on is None else ([(1, 12.0, power)] if f_on <= 1 else
                                              [(1, 0.0, 0), (f_on - 1, 0.0, 0), (f_on, 14.0, power),
                                               (f_on + 2, 2.0, power * 0.3), (f_on + 4, 12.0, power)])
    for f, e, p in keys:
        sock.default_value = e
        sock.keyframe_insert("default_value", frame=max(1, f))
        L.data.energy = p
        L.data.keyframe_insert("energy", frame=max(1, f))


def lamps_follow(y_at, F, lead=4.0):
    """Every lamp flicks on the moment the riders reach it. y_at(f) = riders' y at frame f."""
    for k, o in enumerate(bulbs()):
        by = o.matrix_world.translation.y
        f_on = None
        for f in range(1, F + 1):
            if y_at(f) + lead >= by:
                f_on = f
                break
        _bulb_switch(o, f_on, k)


def lamps_all(f_on=1):
    for k, o in enumerate(bulbs()):
        _bulb_switch(o, f_on, k, power=800)


def lamps_off():
    for k, o in enumerate(bulbs()):
        _bulb_switch(o, None, k)


def fireworks(center, f0, color, n=40, r=11.0, life=28, seed=1):
    """A burst of glowing sparks flying out from center at f0, falling and fading."""
    rnd = random.Random(seed)
    m = kit.mat("fw%d" % seed, color, emit=18, emit_color=color)
    cx, cy, cz = center
    flash = kit.point(center, color, 0, 2.0)
    for f, e in ((max(1, f0 - 1), 0), (f0, 30000), (f0 + life, 0)):
        flash.data.energy = e
        flash.data.keyframe_insert("energy", frame=f)
    for i in range(n):
        th, ph = rnd.uniform(0, 2 * math.pi), math.acos(rnd.uniform(-1, 1))
        d = V((math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph))) * r * rnd.uniform(0.75, 1.0)
        s = kit.sphere(0.45, center, m, seg=6)
        kit.key(s, 1, loc=center, scale=(0.01, 0.01, 0.01))
        kit.key(s, max(1, f0 - 1), loc=center, scale=(0.01, 0.01, 0.01))
        kit.key(s, f0, loc=center, scale=(1, 1, 1))
        kit.key(s, f0 + life // 2, loc=(cx + d.x, cy + d.y, cz + d.z), scale=(1, 1, 1))
        kit.key(s, f0 + life, loc=(cx + d.x * 1.15, cy + d.y * 1.15, cz + d.z - 3.0), scale=(0.01, 0.01, 0.01))


def show_fireworks(f0, every=7, count=6, near_y=Y_RAMP - 30, seed=3):
    cols = [(1, 0.35, 0.5), (0.4, 0.8, 1), (1, 0.85, 0.3), (0.6, 1, 0.5), (0.9, 0.5, 1), (1, 0.6, 0.25)]
    rnd = random.Random(seed)
    for i in range(count):
        c = (rnd.uniform(-18, 22), near_y + rnd.uniform(-20, 20), rnd.uniform(18, 30))
        fireworks(c, f0 + i * every, cols[i % len(cols)], seed=seed * 10 + i)


# ---------------------------------------------------------------- bikes
def bike(c, color):
    """Bike under a rider, built in the rider's frame and parented to them (moves with key_root)."""
    frame_m = kit.mat("bike" + str(color), color, rough=0.3, emit=0.6, emit_color=color)
    tyre = kit.mat("tyre", (0.05, 0.05, 0.06), rough=0.9)
    yaw = math.degrees(c.root.rotation_euler.z - math.pi)
    parts = []
    for ly in (-2.0, 2.0):                       # wheels (front = +ly)
        w = kit.cyl(1.05, 0.3, tuple(c.world((0, ly, 0.65))), tyre, verts=20, rot=(0, 90, 0))
        w.rotation_euler = (0, R(90), R(yaw))
        parts.append(w)
        hub = kit.cyl(0.55, 0.34, tuple(c.world((0, ly, 0.65))), frame_m, verts=10, rot=(0, 90, 0))
        hub.rotation_euler = (0, R(90), R(yaw))
        parts.append(hub)
    for loc, size in (((0, 0, 1.5), (0.3, 3.8, 0.3)), ((0, -0.5, 1.95), (1.0, 1.1, 0.22)),   # top tube, saddle
                      ((0, 1.9, 1.5), (0.3, 0.3, 1.9)), ((0, 1.9, 2.55), (2.6, 0.25, 0.25)),   # fork, handlebar
                      ((0, -0.5, 1.15), (0.3, 0.3, 1.3))):
        b = kit.box(size, tuple(c.world(loc)), frame_m, 0.05)
        b.rotation_euler = (0, 0, R(yaw))
        parts.append(b)
    for p in parts:
        attach(p, c.root)
    return parts


def rider(S, name, x, y, expr="smile", color=(0.85, 0.15, 0.15)):
    """Character seated on a bike facing +Y (yaw 180): hips on the saddle, hands on the bar."""
    c = S.char(name, (x, y, 0.15), 180, expr)
    bike(c, color)
    for s in "LR":
        c.arm(s, 1, 70, 10)
    c.leg("L", 1, 80)
    c.leg("R", 1, 45)
    return c


def pedal(c, f0, f1, every=6):
    for j, f in enumerate(range(f0, f1 + 1, every)):
        a, b = (85, 40) if j % 2 else (40, 85)
        c.leg("L", f, a)
        c.leg("R", f, b)


def ride(c, f0, f1, y0, y1, x=None, z=0.15):
    x = c.pos.x if x is None else x
    c.key_root(f0, (x, y0, z))
    c.key_root(f1, (x, y1, z))
    for fc in c.root.animation_data.action.fcurves:
        if fc.data_path == "location":
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    pedal(c, f0, f1)


def pair(S, y, me_expr="smile", rio_expr="laugh"):
    me = rider(S, "Narrator", X_ME, y, me_expr, (0.2, 0.45, 0.9))
    rio = rider(S, RIO, X_RIO, y, rio_expr, (0.9, 0.2, 0.2))
    S.allow_close = {("Narrator", RIO), (RIO, "Narrator")}
    return me, rio


def ramp():
    m = kit.mat("ramp", (0.55, 0.38, 0.22), rough=0.8)
    r = kit.box((9, 6, 0.4), (1.5, Y_RAMP - 1.5, 1.0), m, 0.03)
    r.rotation_euler = (R(18), 0, 0)
    kit.box((9, 0.4, 2.0), (1.5, Y_RAMP + 1.3, 1.0), m, 0)


def hill():
    g = kit.mat("hillgrass", (0.18, 0.4, 0.18), rough=0.95)
    kit.sphere(14, (HILL.x, HILL.y + 8, -10.5), g, scale=(1.6, 1.2, 1.0), seg=24)


# ---------------------------------------------------------------- shots
def s01(k, F):  # "City lights on your skin" - dark street, two kids on bikes; the first lamp flicks on
    S = night()
    lamps_off()
    me, rio = pair(S, Y0 + 2, "smile", "smile")
    rio.look(1, -30, 0)
    me.look(kf(F * 0.4), 30, 0)
    near = sorted(bulbs(), key=lambda o: (o.matrix_world.translation - V((1.5, Y0 + 2, 0))).length)[0]
    _bulb_switch(near, kf(F * 0.3), 99)
    S.drone([(1, V((9, Y0 + 12, 3.0)), V((1.5, Y0 + 1, 2.6))),
             (F, V((7, Y0 + 9, 3.6)), V((1.5, Y0 + 1, 2.8)))], lens=30)
    return S


def s02(k, F):  # "windows down, let it in" - they push off, lamps light up as they pass
    S = night()
    me, rio = pair(S, Y0 + 2)
    ya, yb = Y0 + 2, Y0 + 26
    ride(me, 1, F, ya, yb)
    ride(rio, 1, F, ya - 1.5, yb - 1.5)
    lamps_follow(lambda f: ya + (yb - ya) * (f - 1) / max(1, F - 1), F)
    S.drone([(1, V((8.5, Y0 + 16, 3.4)), V((1.5, Y0 + 3, 2.4))),
             (F, V((8.0, Y0 + 38, 4.0)), V((1.5, Y0 + 24, 2.4)))], lens=30)
    return S


def s03(k, F):  # "No tomorrow in our hands" - side tracking drone
    S = night()
    ya, yb = Y0 + 26, Y0 + 50
    me, rio = pair(S, ya)
    ride(me, 1, F, ya, yb)
    ride(rio, 1, F, ya - 1, yb - 1)
    lamps_follow(lambda f: ya + (yb - ya) * (f - 1) / max(1, F - 1), F)
    rio.look(kf(F * 0.3), -40, 0)
    rio.arm("L", kf(F * 0.3), 150, 20)
    S.drone([(1, V((11.0, ya - 1, 3.4)), V((1.5, ya, 2.4))),
             (F, V((11.0, yb - 1, 3.8)), V((1.5, yb, 2.4)))], lens=22, allow_close=True)
    return S


def s04(k, F):  # "just this feeling pulling us in" - Rio laughing, close front
    S = night()
    ya, yb = Y0 + 50, Y0 + 66
    me, rio = pair(S, ya, "smile", "laugh")
    ride(me, 1, F, ya, yb)
    ride(rio, 1, F, ya, yb)
    lamps_all(1)
    rio.look(1, -25, 5)
    S.drone([(1, rio.head_pt() + V((2.5, 5.0, -0.6)), rio.head_pt() - V((0, 0, 1.2))),
             (F, rio.head_pt() + V((2.2, yb - ya + 5.0, -0.6)), rio.head_pt() + V((0, yb - ya, -1.2)))], lens=30)
    return S


def s05(k, F):  # "You don't ask where this is going" - high drone, lamps lighting in a chain below
    S = night()
    ya, yb = Y0 + 40, Y0 + 75
    me, rio = pair(S, ya)
    ride(me, 1, F, ya, yb)
    ride(rio, 1, F, ya - 1, yb - 1)
    lamps_follow(lambda f: ya + (yb - ya) * (f - 1) / max(1, F - 1), F, lead=8)
    S.drone([(1, V((1.5, ya - 14, 24)), V((1.5, ya + 6, 0))),
             (F, V((1.5, yb - 12, 22)), V((1.5, yb + 8, 0)))], lens=26)
    return S


def s06(k, F):  # "you don't need to know my past" - his house: moving truck, boxes, SOLD sign
    S = night()
    porch(S, lit=True)
    truck = car((P.x - 13, P.y - 12, 0), color=(0.95, 0.95, 0.95), yaw=0)
    truck.scale = (1.5, 1.6, 1.5)
    box = kit.mat("cardboard", (0.72, 0.52, 0.32), 0.85)
    for i, (bx, by, bz) in enumerate(((-3, -3, 0.6), (-1.6, -3.4, 0.6), (-2.4, -3.1, 1.8), (2.5, -3.2, 0.6))):
        kit.box((1.4, 1.4, 1.2), (P.x + bx, P.y + by, bz), box, 0.04)
    kit.box((0.2, 0.2, 3.2), (P.x + 9, P.y - 8, 1.6), kit.mat("post", (0.9, 0.9, 0.9)), 0)
    kit.box((3.0, 0.15, 1.8), (P.x + 9, P.y - 8.1, 3.3), kit.mat("signr", (0.85, 0.12, 0.12)), 0.03)
    text("SOLD", (P.x + 9, P.y - 8.25, 2.95), rot=(90, 0, 0), size=0.9, color=(1, 1, 1), emit=1.5)
    S.drone([(1, V((P.x + 4, P.y - 26, 5)), V((P.x, P.y - 2, 4))),
             (F, V((P.x + 1, P.y - 21, 4.5)), V((P.x + 2, P.y - 2, 4)))], lens=28)
    return S


def s07(k, F):  # "Every second getting closer" - racing, low camera behind, fast pedalling
    S = night()
    ya, yb = Y0 + 66, Y0 + 92
    me, rio = pair(S, ya, "determined", "laugh")
    ride(me, 1, F, ya, yb)
    ride(rio, 1, F, ya + 1, yb + 3)
    for c in (me, rio):
        pedal(c, 1, F, every=3)
        c.lean(1, 18)
    lamps_all(1)
    S.drone([(1, V((7.5, ya - 7, 1.8)), V((1.5, ya + 4, 2.2))),
             (F, V((7.0, yb - 5, 2.0)), V((1.5, yb + 6, 2.4)))], lens=24, allow_close=True)
    return S


def s08(k, F):  # "like we're running out of time" - town clock 11:59 -> 12:00 on "time"
    S = night()
    cx, cy, cz = 0.0, Y_RAMP + 40, 22.0
    stone = kit.mat("tower", (0.55, 0.5, 0.48), rough=0.9)
    kit.box((10, 6, 30), (cx, cy + 3, 11), stone, 0.05)
    kit.cyl(3.6, 0.4, (cx, cy - 0.1, cz), kit.mat("clockface", (1, 0.96, 0.85), emit=1.5, emit_color=(1, 0.95, 0.8)),
            verts=40, rot=(90, 0, 0))
    hand = kit.mat("hand", (0.05, 0.05, 0.06))
    piv = kit.empty((cx, cy - 0.45, cz), name="minpiv")
    mh = kit.box((0.22, 0.12, 3.0), (cx, cy - 0.45, cz + 1.4), hand, 0)
    attach(mh, piv)
    hh = kit.box((0.3, 0.12, 2.0), (cx, cy - 0.5, cz + 0.9), hand, 0)
    hh.rotation_euler = (0, R(-3), 0)
    hp = kit.empty((cx, cy - 0.5, cz), name="hpiv")
    attach(hh, hp)
    hp.rotation_euler = (0, R(-3), 0)
    tick = kf(55)            # lands on "time" (song 29.34 s)
    kit.key(piv, 1, rot=(0, 6, 0))
    kit.key(piv, tick - 1, rot=(0, 6, 0))
    kit.key(piv, tick, rot=(0, 0, 0))
    S.drone([(1, V((cx + 2, cy - 22, cz - 4)), V((cx, cy, cz))),
             (F, V((cx + 1, cy - 14, cz - 1.5)), V((cx, cy, cz)))], lens=34, allow_close=True)
    return S


def s09(k, F):  # "You look calm, but I feel it..." - Narrator calm, then a sad look at Rio
    S = night()
    ya, yb = Y0 + 92, Y0 + 104
    me, rio = pair(S, ya, "smile", "laugh")
    ride(me, 1, F, ya, yb)
    ride(rio, 1, F, ya, yb)
    lamps_all(1)
    me.look(kf(F * 0.4), -35, 0)
    me.face(kf(F * 0.45), "sad")
    S.drone([(1, me.head_pt() + V((4.0, 6.5, -0.6)), me.head_pt() - V((0, 0, 1.2))),
             (F, me.head_pt() + V((3.5, yb - ya + 6, -0.5)), me.head_pt() + V((0, yb - ya, -1.2)))], lens=30)
    return S


def s10(k, F):  # "...every breath you try to hide" - the ramp ahead, they look at each other, nod
    S = night()
    ramp()
    ya, yb = Y_RAMP - 26, Y_RAMP - 14
    me, rio = pair(S, ya, "smile", "smile")
    ride(me, 1, F, ya, yb)
    ride(rio, 1, F, ya, yb)
    lamps_all(1)
    me.look(kf(F * 0.3), -30, 0)
    rio.look(kf(F * 0.3), 30, 0)
    me.face(kf(F * 0.55), "determined")
    rio.face(kf(F * 0.55), "determined")
    S.drone([(1, V((7.0, Y_RAMP + 3, 3.0)), V((1.5, ya, 2.4))),
             (F, V((6.5, Y_RAMP - 2, 3.4)), V((1.5, yb, 2.4)))], lens=30)
    return S


def s11(k, F):  # "I don't chase, I don't wait, I decide" - off the ramp, slow arc, camera swings round
    S = night()
    ramp()
    hill()
    lamps_all(1)
    me, rio = pair(S, Y_RAMP - 10, "determined", "shocked")
    up = kf(F * 0.25)
    for c, x in ((me, X_ME), (rio, X_RIO)):
        c.key_root(1, (x, Y_RAMP - 10, 0.15))
        c.key_root(up, (x, Y_RAMP - 1, 2.4))
        c.key_root(kf(F * 0.65), (x, Y_RAMP + 8, 7.0))
        c.key_root(F, (x, Y_RAMP + 13, 6.2))
        c.arm("L", kf(F * 0.5), 160, 30)
        c.leg("L", kf(F * 0.5), 20)
        c.leg("R", kf(F * 0.5), 100)
    rio.face(kf(F * 0.5), "laugh")
    me.face(kf(F * 0.5), "laugh")
    S.drone([(1, V((8.5, Y_RAMP - 12, 2.5)), V((1.5, Y_RAMP - 4, 2.5))),
             (F, V((8.5, Y_RAMP + 6, 4.5)), V((1.5, Y_RAMP + 11, 7.5)))], lens=24, allow_close=True)
    return S


def on_hill(S, sit=True):
    xm, xr = HILL.x + 2.3, HILL.x - 2.3
    me = S.char("Narrator", (xm, HILL.y + 3, hill_z(xm, HILL.y + 3)), 0, "laugh")
    rio = S.char(RIO, (xr, HILL.y + 3, hill_z(xr, HILL.y + 3)), 0, "laugh")
    S.allow_close = {("Narrator", RIO), (RIO, "Narrator")}
    if sit:
        for c in (me, rio):
            c.sit(1)
            c.key_root(1, (c.pos.x, c.pos.y, c.pos.z - 0.2))
    return me, rio


def s12(k, F):  # DROP "Raat ka nasha" - the whole town lights up at once + fireworks, camera pulls back
    S = night()
    drop = kf(23)
    lamps_off()
    lamps_all(drop)
    hill()
    show_fireworks(drop, every=5, count=8, near_y=Y_RAMP - 45, seed=4)
    me, rio = on_hill(S, sit=False)
    for c in (me, rio):
        c.arm("R", drop, 170, 20)
        c.arm("L", drop, 170, 20)
    S.drone([(1, V((1.5, HILL.y + 10, 5.5)), V((1.5, HILL.y - 20, 6))),
             (F, V((1.5, HILL.y + 20, 14)), V((1.5, HILL.y - 50, 14)))], lens=24, allow_close=True)
    return S


def s13(k, F):  # "Raat ka nasha" - on the hill, watching the fireworks over the glowing town
    S = night()
    lamps_all(1)
    hill()
    show_fireworks(1, every=8, count=6, near_y=Y_RAMP - 45, seed=7)
    me, rio = on_hill(S)
    rio.arm("L", kf(F * 0.3), 150, 60)
    me.look(kf(F * 0.5), 25, 5)
    me.face(kf(F * 0.5), "sad")
    rio.look(kf(F * 0.6), -25, 0)
    S.drone([(1, V((1.5, HILL.y + 11, 6.0)), V((1.5, HILL.y - 30, 12))),
             (F, V((1.5, HILL.y + 14, 7.0)), V((1.5, HILL.y - 30, 14)))], lens=28, allow_close=True)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 14)}
