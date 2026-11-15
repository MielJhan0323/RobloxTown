"""the-seat ("The Seat") - silent music edit demo (song carries the audio, story told in on-screen text).

In this town, benches remember who sat on them. Me + Rio, every day. He moves away; the bench keeps his side warm.
Five years on I still sit on the left... and one day the right side glows again.

Set (reused): the street bench + burger stand from five_seconds. Rio = Crowd3.
"Memory glow" = a soft warm cushion of light on the seat where someone used to sit.
"""
import math

from mathutils import Vector

import kit
import rblx
from rblx import kf
from stories.five_seconds import BENCH, RIO, bench_and_stand, car

R = math.radians
V = Vector
PACK = "alpha-mark"
L_DY, R_DY = 1.25, -1.25          # bench faces +X: my seat (his left) is +Y, Rio's is -Y


def street(light):
    S = rblx.Stage(PACK, light)
    bench_and_stand(S)
    return S


def memory_glow(S, dy, f_on=1, f_full=None, power=1.0, color=(1, 0.8, 0.45)):
    """Warm glowing patch on the seat (+ a little light) where someone sat. Fades in f_on -> f_full."""
    m = kit.mat("memglow%d" % int(dy * 10), color, emit=0, emit_color=color, alpha=0.75)
    pad = kit.box((1.1, 1.6, 0.06), (BENCH.x, BENCH.y + dy, 1.86), m, 0.25)
    back = kit.box((0.06, 1.6, 1.0), (BENCH.x - 0.56, BENCH.y + dy, 2.55), m, 0.25)
    L = kit.point((BENCH.x + 0.4, BENCH.y + dy, 2.4), color, 0, 1.0)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*color, 1)
    em = b.inputs["Emission Strength"]
    for o in (pad, back):              # invisible until the memory lights up
        S.show(o, 1, False)
        S.show(o, max(1, f_on), True)
    f_full = f_full or f_on + 1
    for f, k in ((max(1, f_on), 0.0), (f_full, 1.0)):
        em.default_value = 1.4 * power * k
        em.keyframe_insert("default_value", frame=f)
        L.data.energy = 35 * power * k
        L.data.keyframe_insert("energy", frame=f)
    return pad, back, L


def sit(S, name, dy, expr, scale=1.0):
    c = S.char(name, (BENCH.x - 0.1, BENCH.y + dy, 1.85 - 1.5), 90, expr)
    if scale != 1.0:
        c.root.scale = (scale, scale, scale)
    c.sit(1)
    return c


def front(S, dist=12, yaw=90, h=4.2, lens=32, side=0.0):
    return S.cam(V((BENCH.x + 0.5, BENCH.y + side, 3.0)), dist=dist, yaw=yaw, height=h, lens=lens)


def falling_leaves(S, F, n=40):
    kit.sparkle_particles((BENCH.x + 3, BENCH.y, 9), n=n, radius=9, frames=F + 10, color=(0.95, 0.5, 0.15))


# ---------------------------------------------------------------- shots
def s01(k, F):  # HOOK - In this town, benches remember who sat on them.
    S = street("dusk")
    memory_glow(S, L_DY, 1, kf(F * 0.25), 1.0)
    memory_glow(S, R_DY, kf(F * 0.15), kf(F * 0.45), 1.0)
    S.drone([(1, V((BENCH.x + 16, BENCH.y - 9, 7)), V((BENCH.x, BENCH.y, 2))),
             (F, V((BENCH.x + 9, BENCH.y - 3, 4.2)), V((BENCH.x, BENCH.y, 2.2)))], lens=30)
    return S


def s02(k, F):  # Every day after school: me and Rio.
    S = street("day")
    me = sit(S, "Narrator", L_DY, "laugh")
    rio = sit(S, RIO, R_DY, "smile")
    S.allow_close = {("Narrator", RIO), (RIO, "Narrator")}
    me.look(1, -25, 0)
    rio.look(1, 25, 0)
    rio.face(kf(F * 0.4), "laugh")
    me.arm("L", kf(F * 0.3), 60, 20)
    me.arm("L", kf(F * 0.6), 20, 0)
    S.drone([(1, V((BENCH.x + 11, BENCH.y + 4, 4.0)), V((BENCH.x, BENCH.y, 2.6))),
             (F, V((BENCH.x + 10, BENCH.y - 3, 4.4)), V((BENCH.x, BENCH.y, 2.6)))], lens=32)
    return S


def s03(k, F):  # Left side: me. Right side: him.
    S = street("sunset")
    memory_glow(S, L_DY, 1, kf(F * 0.2), 0.8)
    memory_glow(S, R_DY, kf(F * 0.4), kf(F * 0.6), 0.8)
    S.drone([(1, V((BENCH.x + 6, BENCH.y + 3, 4.5)), V((BENCH.x, BENCH.y + 1.2, 1.9))),
             (F, V((BENCH.x + 6, BENCH.y - 3, 4.5)), V((BENCH.x, BENCH.y - 1.2, 1.9)))], lens=34, allow_close=True)
    return S


def s04(k, F):  # Then his family moved away.
    S = street("sunset")
    me = S.char("Narrator", (BENCH.x + 2.5, BENCH.y + 2), 70, "sad")
    cr = car((-3.5, BENCH.y + 6, 0), color=(0.3, 0.45, 0.75), yaw=0)
    kit.key(cr, 1, loc=(-3.5, BENCH.y + 6, 0))
    kit.key(cr, F, loc=(-3.5, BENCH.y - 30, 0))
    me.arm("R", kf(F * 0.2), 160, 10)
    for j, f in enumerate(range(kf(F * 0.2), F, 8)):
        me.arm("R", f, 160, 10 + (15 if j % 2 else -15))
    me.look(1, 20, 0)
    me.look(F, -40, 0)
    S.cam_at(V((BENCH.x + 4, BENCH.y + 14, 4.5)), V((BENCH.x + 2, BENCH.y - 2, 2.8)), lens=30)
    return S


def s05(k, F):  # The bench kept his side warm.
    S = street("dusk")
    me = sit(S, "Narrator", L_DY, "sad")
    memory_glow(S, R_DY, 1, kf(F * 0.4), 0.7)
    me.look(1, 0, -10)
    me.look(kf(F * 0.5), -45, -15)
    front(S, dist=10, yaw=80, h=4.0, lens=34)
    return S


def s06(k, F):  # Five years on...  (time skip: drone rises over the street, leaves fall)
    S = street("sunset")
    falling_leaves(S, F, 60)
    S.drone([(1, V((BENCH.x + 6, BENCH.y - 6, 3.5)), V((BENCH.x, BENCH.y, 2))),
             (F, V((BENCH.x + 22, BENCH.y - 18, 16)), V((BENCH.x, BENCH.y, 1)))], lens=26)
    return S


def s07(k, F):  # I still sit on the left.
    S = street("dusk")
    falling_leaves(S, F, 25)
    me = S.char("Narrator", (BENCH.x + 4, BENCH.y + 9), 200, "tired")
    me.root.scale = (1.08, 1.08, 1.08)
    me.walk(1, kf(F * 0.55), (BENCH.x + 1.2, BENCH.y + L_DY))
    me.key_root(kf(F * 0.55), yaw=90)
    me.key_root(kf(F * 0.7), (BENCH.x - 0.1, BENCH.y + L_DY, 0.35), yaw=90)
    me.sit(kf(F * 0.7))
    front(S, dist=13, yaw=70, h=4.5, lens=30)
    return S


def s08(k, F):  # Today, the right side glowed.
    S = street("dusk")
    me = sit(S, "Narrator", L_DY, "tired", scale=1.08)
    memory_glow(S, R_DY, kf(F * 0.25), kf(F * 0.5), 1.4)
    me.face(kf(F * 0.5), "shocked")
    me.look(kf(F * 0.5), -50, -10)
    S.drone([(1, V((BENCH.x + 8, BENCH.y + 2, 3.6)), V((BENCH.x, BENCH.y, 2.6))),
             (F, V((BENCH.x + 6.5, BENCH.y + 1, 3.4)), V((BENCH.x, BENCH.y - 0.4, 2.5)))], lens=34)
    return S


def s09(k, F):  # "Hey. Sorry I'm late."
    S = street("sunset")
    falling_leaves(S, F, 20)
    me = sit(S, "Narrator", L_DY, "shocked", scale=1.08)
    rio = S.char(RIO, (BENCH.x + 3, BENCH.y - 6), 160, "smile")
    rio.root.scale = (1.08, 1.08, 1.08)
    S.allow_close = {("Narrator", RIO), (RIO, "Narrator")}
    rio.walk(1, kf(F * 0.35), (BENCH.x + 1.2, BENCH.y + R_DY))
    rio.key_root(kf(F * 0.35), yaw=90)
    rio.key_root(kf(F * 0.5), (BENCH.x - 0.1, BENCH.y + R_DY, 0.35), yaw=90)
    rio.sit(kf(F * 0.5))
    rio.look(kf(F * 0.55), 25, 0)
    me.look(1, -40, 0)
    me.face(kf(F * 0.6), "laugh")
    rio.face(kf(F * 0.6), "laugh")
    memory_glow(S, L_DY, 1, 2, 0.5)
    memory_glow(S, R_DY, 1, 2, 0.5)
    S.drone([(1, V((BENCH.x + 11, BENCH.y - 2, 4.2)), V((BENCH.x, BENCH.y - 1, 2.6))),
             (F, V((BENCH.x + 16, BENCH.y, 5.2)), V((BENCH.x, BENCH.y, 2.6)))], lens=30)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 10)}
