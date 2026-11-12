"""five-seconds ("The Last Pickle") - one-second strength + danger sense; Rio gives his away.

Sets (reused): A street (bench + burger stand built here on the left sidewalk), canteen (from alpha_mark),
playground (exported). Rio = Crowd3. The accident is never shown: headlights, then the empty bench.
"""
import math
import random

import bpy
from mathutils import Vector

import kit
import rblx
from rblx import attach, kf
from stories.alpha_mark import CANTEEN, canteen
from stories.nothing_happens import H as HOUSE, day_house, text

R = math.radians
V = Vector
PACK = "alpha-mark"
RIO = "Crowd3"
BENCH = V((-11.2, -3505.0, 0))   # left sidewalk, facing the road (+X)
STAND = V((-11.5, -3496.0, 0))
PG = V((-250.0, -3505.0, 0))      # playground centre


# ---------------------------------------------------------------- props
def burger(loc, s=1.0):
    parts = [kit.cyl(0.42 * s, 0.18 * s, (loc[0], loc[1], loc[2]), kit.mat("bun", (0.85, 0.55, 0.25)), verts=16),
             kit.cyl(0.45 * s, 0.14 * s, (loc[0], loc[1], loc[2] + 0.15 * s), kit.mat("patty", (0.35, 0.18, 0.1)), verts=16),
             kit.box((0.8 * s, 0.8 * s, 0.05 * s), (loc[0], loc[1], loc[2] + 0.25 * s), kit.mat("cheese", (1, 0.8, 0.15)), 0),
             kit.cyl(0.46 * s, 0.06 * s, (loc[0], loc[1], loc[2] + 0.3 * s), kit.mat("lettuce", (0.35, 0.8, 0.25)), verts=16),
             kit.sphere(0.43 * s, (loc[0], loc[1], loc[2] + 0.4 * s), kit.mat("buntop", (0.88, 0.58, 0.28)),
                        scale=(1, 1, 0.55), seg=16)]
    root = kit.empty(loc, name="burger")
    for p in parts:
        attach(p, root)
    return root


def bench_and_stand(S):
    wood = kit.mat("bwood", (0.6, 0.38, 0.2), rough=0.7)
    iron = kit.mat("biron", (0.15, 0.15, 0.17), metal=0.5)
    bx, by = BENCH.x, BENCH.y
    kit.box((1.4, 5.0, 0.25), (bx, by, 1.7), wood, 0.04)          # seat
    kit.box((0.25, 5.0, 1.4), (bx - 0.7, by, 2.6), wood, 0.04)    # back
    for dy in (-2.2, 2.2):
        kit.box((1.2, 0.2, 1.6), (bx, by + dy, 0.8), iron, 0)
    # burger stand
    sx, sy = STAND.x, STAND.y
    kit.box((3.2, 4.2, 3.4), (sx - 0.4, sy, 1.7), kit.mat("stand", (0.95, 0.95, 0.92)), 0.06)
    kit.box((3.6, 4.6, 0.3), (sx - 0.2, sy, 3.5), kit.mat("counter2", (0.85, 0.2, 0.2)), 0.04)
    for k in range(5):
        kit.box((0.5, 4.8, 0.25), (sx + 0.9 - k * 0.0, sy, 6.2), kit.mat("awn%d" % (k % 2), (0.9, 0.15, 0.15) if k % 2 else
                                                                         (1, 1, 1)), 0)
    awn = kit.box((2.4, 5.0, 0.25), (sx + 0.6, sy, 6.0), kit.mat("awning", (0.9, 0.2, 0.18)), 0.04)
    awn.rotation_euler = (0, R(-14), 0)
    for dy in (-2.2, 2.2):
        kit.box((0.2, 0.2, 2.6), (sx + 1.5, sy + dy, 4.8), iron, 0)
    text("BURGERS", (sx + 1.3, sy, 7.0), rot=(90, 0, 90), size=0.9, color=(1, 0.85, 0.2), emit=1.2)
    burger((sx + 1.0, sy - 1.0, 3.75), 0.9)


def dog(loc, yaw=0):
    root = kit.empty(loc, name="dog")
    fur = kit.mat("fur", (0.75, 0.5, 0.25))
    parts = [kit.box((1.0, 2.0, 1.0), (loc[0], loc[1], loc[2] + 1.2), fur, 0.15),
             kit.box((0.9, 0.9, 0.9), (loc[0], loc[1] - 1.3, loc[2] + 1.9), fur, 0.15),
             kit.box((0.4, 0.5, 0.35), (loc[0], loc[1] - 1.85, loc[2] + 1.75), kit.mat("snout", (0.9, 0.75, 0.55)), 0.1),
             kit.box((0.18, 0.12, 0.15), (loc[0], loc[1] - 2.1, loc[2] + 1.85), kit.mat("nose", (0.05, 0.05, 0.05)), 0.03)]
    for dx in (-0.35, 0.35):
        parts.append(kit.box((0.2, 0.3, 0.5), (loc[0] + dx, loc[1] - 1.2, loc[2] + 2.45), kit.mat("ear", (0.5, 0.3, 0.15)), 0.05))
        parts.append(kit.box((0.12, 0.05, 0.12), (loc[0] + dx * 0.6, loc[1] - 1.76, loc[2] + 2.05), kit.mat("deye", (0.02, 0.02, 0.02)), 0))
        for dy in (-0.7, 0.7):
            parts.append(kit.box((0.3, 0.3, 0.75), (loc[0] + dx, loc[1] + dy, loc[2] + 0.38), fur, 0.05))
    tail = kit.box((0.15, 0.15, 0.8), (loc[0], loc[1] + 1.1, loc[2] + 1.9), fur, 0.05)
    tail.rotation_euler = (R(-35), 0, 0)
    parts.append(tail)
    for p in parts:
        attach(p, root)
    root.rotation_euler = (0, 0, R(yaw))
    return root, parts[1], tail


def glow_orb(loc, power=200):
    o = kit.sphere(0.45, loc, kit.mat("orb", (1, 0.85, 0.35), emit=12, emit_color=(1, 0.85, 0.35)), seg=16)
    L = kit.point(loc, (1, 0.8, 0.4), power, 0.3)
    attach(L, o)
    return o


def eye_glow(c, f_on=1, power=60):
    L = kit.point(tuple(c.head_pt() + c.world((0, 0.9, 0)) - c.pos), (1, 0.8, 0.3), 0, 0.2)
    attach(L, c.neck)
    L.data.keyframe_insert("energy", frame=max(0, f_on - 1))
    L.data.energy = power
    L.data.keyframe_insert("energy", frame=f_on)
    kit.sparkle_particles(tuple(c.head_pt()), n=18, radius=1.4, frames=120, color=(1, 0.85, 0.4))
    return L


def sit_bench(S, name, dy, expr, yaw=90):
    c = S.char(name, (BENCH.x - 0.1, BENCH.y + dy, 1.85 - 1.5), yaw, expr)
    c.sit(1)
    return c


def bench_cam(S, dist=11, yaw=90, h=4.2, lens=34):
    return S.cam(V((BENCH.x + 0.5, BENCH.y, 3.2)), dist=dist, yaw=yaw, height=h, lens=lens)


def street(light="sunset"):
    S = rblx.Stage(PACK, light)
    bench_and_stand(S)
    return S


# ---------------------------------------------------------------- shots
def s01(k, F):  # In this town,
    S = street("morning")
    for nm, x, y in (("Narrator", 11, -3478), ("Prey1", 12.6, -3479), (RIO, 9.6, -3472), ("Crowd1", 12.4, -3468)):
        c = S.char(nm, (x, y), 0, "smile")
        c.walk(1, F, (x, y - 5))
    S.cam(V((11.0, -3478, 3.0)), dist=16, yaw=-28, height=5.0, lens=38, fstop=None)
    return S


def s02(k, F):  # everyone gets one gift.
    S = street("morning")
    for i, (nm, x) in enumerate((("Prey1", 9.0), ("Narrator", 11.2), ("Crowd1", 13.2))):
        c = S.char(nm, (x, -3500), 0, "shocked" if i == 1 else "smile")
        c.arm("R", 1, 20)
        c.arm("R", kf(10), 90)
        c.look(kf(10), 0, -20)
        kit.sparkle_particles(tuple(c.world((1.4, 2.2, 3.0))), n=16, radius=0.8, frames=F + 10, color=(1, 0.9, 0.5))
    S.cam(V((11.0, -3500, 3.2)), dist=11, yaw=-5, height=4.0, lens=36)
    return S


def s03(k, F):  # Some kids can talk to dogs.
    S = street("morning")
    c = S.char("Prey1", (10.4, -3500), 60, "laugh")
    d, head, tail = dog((12.6, -3500.6, 0), yaw=-60)
    c.talk(4, F, base="laugh")
    for j, f in enumerate(range(1, F + 2, 5)):
        tail.rotation_euler = (R(-35), R(25 if j % 2 else -25), 0)
        tail.keyframe_insert("rotation_euler", frame=f)
        head.rotation_euler = (R(8 if j % 3 == 0 else -4), 0, 0)
        head.keyframe_insert("rotation_euler", frame=f)
    S.cam(V((11.5, -3500.3, 2.6)), dist=10, yaw=-10, height=3.8, lens=34)
    return S


def s04(k, F):  # Some can find anything you lose.
    S = street("morning")
    c = S.char("Crowd1", (11, -3500), 0, "smile")
    keys = kit.box((0.5, 0.15, 0.7), tuple(c.world((1.5, 0.2, 1.9))), kit.mat("keys", (1, 0.8, 0.2), metal=0.8), 0.05)
    attach(keys, c.arms["R"])
    c.arm("R", 1, 30)
    c.arm("R", kf(10), 160)
    c.faces([(1, "smile"), (kf(10), "laugh")])
    S.cam(c.chest_pt() + V((0, 0, 0.8)), dist=9, yaw=-10, lens=36)
    return S


def hand_burger(c, side="R"):
    b = burger(tuple(c.world((1.5 if side == "R" else -1.5, 0.3, c.meta["shoulder"] - c.meta["arm_len"] - 0.2))), 0.9)
    attach(b, c.arms[side])
    return b


def pickle(loc):
    kit.box((1.4, 1.4, 0.04), (loc[0], loc[1], loc[2]), kit.mat("napkin", (0.97, 0.97, 0.95)), 0)
    p = kit.cyl(0.32, 0.06, (loc[0], loc[1], loc[2] + 0.05), kit.mat("pickle", (0.45, 0.65, 0.2), rough=0.4), verts=14)
    return p


def s05(k, F):  # Mine? My toast always lands butter side up.
    S, h = day_house()
    hx, hy = HOUSE
    n = S.char("Narrator", (hx - 24, hy + 2.2), 0, "tired")
    toast = kit.box((1.0, 1.0, 0.2), tuple(n.world((1.5, 1.0, 2.8))), kit.mat("toast", (0.85, 0.6, 0.3)), 0.05)
    butter = kit.box((0.5, 0.5, 0.08), (toast.location.x, toast.location.y, toast.location.z + 0.14),
                     kit.mat("butter", (1, 0.9, 0.4)), 0.02)
    attach(butter, toast)
    p0 = V(toast.location)
    kit.key(toast, 1, loc=tuple(p0), rot=(0, 0, 0))
    kit.key(toast, kf(F * 0.3), loc=tuple(p0 + V((0.4, 0.8, -1.4))), rot=(200, 30, 0))
    kit.key(toast, kf(F * 0.55), loc=(p0.x + 0.6, p0.y + 1.2, 0.12), rot=(360, 0, 0))
    n.arm("R", 1, 70)
    n.arm("R", kf(F * 0.3), 30)
    n.look(kf(F * 0.4), 0, -30)
    S.cam(V((hx - 23.5, hy + 2, 2.6)), dist=10, yaw=10, height=4.2, lens=32)
    return S


def s06(k, F):  # Nobody claps for that.
    S, h = day_house()
    hx, hy = HOUSE
    n = S.char("Narrator", (hx - 24, hy + 2.2), 0, "sad")
    n.look(1, 0, -10)
    n.arm("L", 1, 0, 25)
    n.arm("R", 1, 0, 25)
    S.cam(n.head_pt() - V((0, 0, 1.4)), dist=9, yaw=-10, height=n.head_pt().z - 0.5, lens=32)
    return S


def s07(k, F):  # Rio's gift was different.
    S = street("sunset")
    r = S.char(RIO, (11, -3500), -10, "smile")
    kit.sparkle_particles(tuple(r.head_pt()), n=24, radius=2.0, frames=F + 10, color=(1, 0.85, 0.4))
    S.cam(r.chest_pt() + V((0, 0, 0.7)), dist=9, yaw=-10, lens=36)
    return S


def s08(k, F):  # He could feel when something was about to end.
    S = street("sunset")
    r = S.char(RIO, (11, -3500), -10, "neutral")
    r.look(1, 0, 10)
    eye_glow(r, kf(6), 14)
    S.cam(r.head_pt() - V((0, 0, 0.9)), dist=6.5, yaw=-10, height=r.head_pt().z - 0.3, lens=40)
    return S


def s09(k, F):  # The last day of summer.
    S = street("sunset")
    r = S.char(RIO, (10.5, -3505), 180, "smile")
    kit.sphere(5, (40, -3360, 22), kit.mat("sunball", (1, 0.6, 0.3), emit=12, emit_color=(1, 0.6, 0.3)))
    S.cam(V((10.5, -3505, 3.5)), dist=10, yaw=10, height=4.5, lens=30, fstop=None)
    return S


def s10(k, F):  # The last bite of a burger.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "smile", yaw=80)
    hand_burger(r, "R")
    r.arm("R", 1, 100, -10)
    r.arm("R", kf(F * 0.5), 125, -10)
    S.cam(r.head_pt() - V((0, 0, 1.0)), dist=6.5, yaw=80, height=r.head_pt().z - 0.2, lens=38)
    return S


def canteen_cup(S, tip_f, caught=None):
    cx, cy = CANTEEN
    cup = kit.cyl(0.35, 0.9, (cx - 7, cy + 0.2, 3.2), kit.mat("ccup", (0.3, 0.6, 0.95)), verts=14)
    kit.key(cup, 1, loc=tuple(cup.location), rot=(0, 0, 0))
    kit.key(cup, tip_f, loc=(cx - 7, cy + 0.2, 3.2), rot=(0, 0, 0))
    kit.key(cup, tip_f + 6, loc=(cx - 7, cy - 0.4, 3.0), rot=(-45, 0, 0))
    return cup


def s11(k, F):  # The second before a glass tips over.
    S = rblx.Stage(PACK, "day")
    cx, cy = canteen(S)
    canteen_cup(S, kf(F * 0.4))
    S.cam_at(V((cx - 4.5, cy - 4, 4.0)), V((cx - 7, cy + 0.2, 3.1)), lens=36, fstop=2.0)
    return S


def s12(k, F):  # He always caught it.
    S = rblx.Stage(PACK, "day")
    cx, cy = canteen(S)
    r = S.char(RIO, (cx - 7.3, cy - 2.4, 0.25), 0 + 180, "smirk")
    r.sit(1)
    cup = kit.cyl(0.35, 0.9, tuple(r.world((-1.5, 1.2, 2.6))), kit.mat("ccup", (0.3, 0.6, 0.95)), verts=14)
    attach(cup, r.arms["L"])
    r.arm("L", 1, 70, -10)
    S.cam(r.head_pt() - V((0, 0, 1.2)), dist=8, yaw=180 + 20, height=r.head_pt().z, lens=34)
    return S


def s13(k, F):  # Everyone wanted to sit next to Rio.
    S = rblx.Stage(PACK, "day")
    cx, cy = canteen(S)
    r = S.char(RIO, (cx - 8, cy + 2.4, 0.25), 180, "smile")
    r.sit(1)
    for i, (nm, dx, dy, yaw) in enumerate((("Prey1", -11, 2.4, 180), ("Crowd1", -5, 2.4, 180), ("Crowd2", -8, -2.4, 0),
                                            ("Prey2", -6, -2.4, 0), ("Crowd4", -10.5, -2.4, 0))):
        c = S.char(nm, (cx + dx, cy + dy, 0.25), yaw, "laugh")
        c.sit(1)
        c.talk(1 + i * 3, F, base="laugh")
    S.cam(V((cx - 8, cy, 3.0)), dist=14, yaw=-15, height=6, lens=30, fstop=None)
    return S


def s14(k, F):  # Somehow, he always sat next to me.
    S = rblx.Stage(PACK, "day")
    cx, cy = canteen(S)
    n = S.char("Narrator", (cx - 17.4, cy - 11.2, -0.3), 0, "sad")
    n.sit(1)
    r = S.char(RIO, (cx - 13.5, cy - 7.5), -135, "smile")
    r.walk(1, kf(F * 0.55), (cx - 15.6, cy - 11.2), swing=24)
    n.faces([(1, "sad"), (kf(F * 0.6), "shocked")])
    n.look(kf(F * 0.6), -40, 0)
    stool = kit.mat("stool", (0.55, 0.55, 0.6))
    for x in (-17.4, -15.6):
        kit.box((1.6, 1.2, 1.2), (cx + x, cy - 11.6, 0.6), stool, 0.03)
    S.cam(V((cx - 16.5, cy - 10.5, 2.6)), dist=12, yaw=15, height=4.8, lens=32)
    return S


def s15(k, F):  # I asked him for it. Just to try.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "smile", yaw=60)
    n = sit_bench(S, "Narrator", -1.2, "smile", yaw=120)
    n.talk(3, F, base="smile")
    n.arm("R", 1, 50, -20)
    bench_cam(S, dist=10, yaw=95, h=4.0)
    return S


def s16(k, F):  # Rio looked at me for a long time.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "neutral", yaw=45)
    r.look(1, -10, 0)
    S.cam(r.head_pt() - V((0, 0, 0.7)), dist=6, yaw=45, height=r.head_pt().z, lens=40)
    return S


def s17(k, F):  # Then he said, "Okay.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "smile", yaw=45)
    r.talk(kf(F * 0.4), F, base="smile")
    S.cam(r.head_pt() - V((0, 0, 0.7)), dist=6, yaw=45, height=r.head_pt().z, lens=40)
    return S


def s18(k, F):  # But you have to spend every minute with me."
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "smile", yaw=40)
    n = sit_bench(S, "Narrator", -1.2, "shocked", yaw=140)
    orb = glow_orb(tuple(r.world((1.5, 1.4, 2.6))), 150)
    attach(orb, r.arms["R"])
    r.arm("R", 1, 40)
    r.arm("R", kf(12), 85, -20)
    r.talk(3, F, base="smile")
    bench_cam(S, dist=9, yaw=90, h=4.0)
    return S


def s19(k, F):  # I said yes before he finished.
    S = street("sunset")
    n = sit_bench(S, "Narrator", -1.2, "laugh", yaw=140)
    orb = glow_orb(tuple(n.world((0, 1.6, 2.4))), 200)
    kit.key(orb, 1, loc=tuple(orb.location), scale=(1, 1, 1))
    kit.key(orb, F, loc=tuple(orb.location), scale=(0.2, 0.2, 0.2))
    n.arm("L", 1, 70, -20)
    n.arm("R", 1, 70, -20)
    for f in range(1, F + 2, 6):
        n.look(f, 0, 12 if (f // 6) % 2 else -8)  # eager nodding
    S.cam(n.head_pt() - V((0, 0, 1.1)), dist=6.5, yaw=140, height=n.head_pt().z - 0.2, lens=38)
    return S


def s20(k, F):  # With his gift, I knew exactly when every game would end.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 180, "smirk")
    eye_glow(n, kf(4), 12)
    for i, nm in enumerate(("Prey1", "Crowd2")):
        c = S.char(nm, (PG.x - 2.5 + i * 5, PG.y - 1.5), 180 + (-30 if i == 0 else 30), "shocked")
    S.cam(n.chest_pt() + V((0, 0, 0.6)), dist=11, yaw=180, height=4.2, lens=32)
    return S


def s21(k, F):  # When to jump. When to leave.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 90, "smirk")
    p = n.pos
    n.key_root(1, (p.x, p.y, p.z))
    n.key_root(kf(F * 0.25), (p.x + 1.5, p.y, p.z + 2.5))
    n.key_root(kf(F * 0.45), (p.x + 3, p.y, p.z))
    n.arm("L", kf(F * 0.25), 160)
    n.arm("R", kf(F * 0.25), 160)
    n.arm("L", kf(F * 0.45), 0)
    n.arm("R", kf(F * 0.45), 0)
    n.walk(kf(F * 0.5), F, (p.x + 7, p.y))
    S.cam(V((PG.x + 3, PG.y, 3)), dist=16, yaw=180, height=5, lens=30)
    return S


def s22(k, F):  # People finally clapped for me.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 180, "laugh")
    for i, nm in enumerate(("Prey1", "Crowd2", "Crowd1", "Smallkid", "Prey2")):
        a = 2.3 + i * 0.45
        c = S.char(nm, (PG.x + math.cos(a) * 5, PG.y + math.sin(a) * 5), 180 + (i - 2) * 22, "laugh")
        for j, f in enumerate(range(1, F + 2, 4)):   # clapping
            o = 0 if j % 2 else 25
            c.arm("L", f, 80, -o)
            c.arm("R", f, 80, -o)
    S.cam(V((PG.x, PG.y + 2, 3)), dist=14, yaw=180, height=5.5, lens=30)
    return S


def s23(k, F):  # Rio waited on our bench.
    S = street("dusk")
    r = sit_bench(S, RIO, 1.2, "sad")
    burger((BENCH.x + 0.1, BENCH.y - 0.8, 1.95), 0.8)
    S.cam(V((BENCH.x + 0.5, BENCH.y + 1, 3.0)), dist=17, yaw=75, height=5, lens=30, fstop=None)
    return S


def s24(k, F):  # He saved me the last pickle.
    S = street("dusk")
    pickle((BENCH.x + 0.1, BENCH.y - 1.0, 1.85))
    r = sit_bench(S, RIO, 1.2, "sad", yaw=110)
    S.cam_at(V((BENCH.x + 2.3, BENCH.y - 2.2, 3.4)), V((BENCH.x + 0.1, BENCH.y - 1.0, 1.9)), lens=40, fstop=2.0)
    return S


def s25(k, F):  # Every day, I said, "Tomorrow."
    S = rblx.Stage(PACK, "dusk")
    n = S.char("Narrator", (PG.x, PG.y), 180, "smile")
    n.talk(4, F, base="smile")
    for j, f in enumerate(range(1, F + 2, 6)):
        n.arm("R", f, 10, 120 if j % 2 else 90)
    for nm, dx in (("Crowd2", -2.2), ("Prey1", 2.3)):
        S.char(nm, (PG.x + dx, PG.y - 0.8), 180 + (-20 if dx < 0 else 20), "laugh")
    S.cam(n.head_pt() - V((0, 0, 1.6)), dist=9, yaw=180, height=n.head_pt().z - 0.6, lens=34)
    return S


def s26(k, F):  # Then, one afternoon, I felt it.
    S = rblx.Stage(PACK, "dusk")
    n = S.char("Narrator", (PG.x, PG.y), 180, "smile")
    n.faces([(1, "smile"), (kf(6), "shocked")])
    eye_glow(n, kf(6), 18)
    S.flash_light(tuple(n.head_pt() + V((0, 2, 0))), kf(6), kf(6) + 6, (1, 0.9, 0.6), 2500)
    S.cam(n.head_pt() - V((0, 0, 0.8)), dist=6, yaw=180, height=n.head_pt().z, lens=40)
    return S


def s27(k, F):  # A tug, like the last page of a book.
    S = rblx.Stage(PACK, "dusk")
    n = S.char("Narrator", (PG.x, PG.y), 180, "scared")
    n.arm("R", 1, 40, -10)
    n.arm("R", kf(8), 75, -45)   # hand to chest
    n.lean(kf(8), 12)
    S.cam(n.chest_pt() + V((0, 0, 0.4)), dist=7, yaw=180 + 15, lens=38)
    return S


def s28(k, F):  # It came from our bench.
    S = street("dusk")
    r = S.char(RIO, (BENCH.x + 1.8, BENCH.y - 2.0), 90, "smile")
    r.walk(1, F, (BENCH.x + 5.0, BENCH.y - 2.6), swing=22)
    burger((BENCH.x + 0.1, BENCH.y - 0.8, 1.95), 0.8)
    S.cam(V((BENCH.x + 2.5, BENCH.y, 3.0)), dist=17, yaw=70, height=5, lens=30, fstop=None)
    return S


def s29(k, F):  # I ran.
    S = rblx.Stage(PACK, "dusk")
    n = S.char("Narrator", (PG.x - 8, PG.y + 2), 90, "scared")
    n.run(1, F, (PG.x + 4, PG.y + 2))
    S.cam(V((PG.x - 2, PG.y + 2, 2.8)), dist=20, yaw=165, height=6, lens=28, fstop=None)
    return S


def s30(k, F):  # But Rio didn't feel the car coming. (headlights only)
    S = street("night")
    r = S.char(RIO, (-2.5, -3510), 90, "smile")
    r.walk(1, F, (-1.0, -3510), swing=20)
    for dx in (-1.2, 1.2):
        L = kit.spot((1.5 + dx, -3540, 1.6), (1.5, -3505, 1.4), (1, 0.95, 0.8), 0, 25, 0.25, 0.05)
        L.data.keyframe_insert("energy", frame=1)
        L.data.energy = 60000
        L.data.keyframe_insert("energy", frame=F)
        kit.key(L, 1, loc=(1.5 + dx, -3545, 1.6))
        kit.key(L, F, loc=(1.5 + dx, -3522, 1.6))
        g = kit.sphere(0.35, (1.5 + dx, -3545, 1.6), kit.mat("hl", (1, 1, 0.9), emit=40, emit_color=(1, 1, 0.9)), seg=10)
        kit.key(g, 1, loc=(1.5 + dx, -3545, 1.6))
        kit.key(g, F, loc=(1.5 + dx, -3522, 1.6))
    S.cam(V((-1.5, -3510, 3.0)), dist=12, yaw=150, height=4.5, lens=30, fstop=None)
    return S


def s31(k, F):  # He'd given that away.
    S = street("rain")
    burger((BENCH.x + 0.1, BENCH.y + 1.0, 1.95), 0.8)
    S.rain(F, tuple(BENCH + V((2, 0, 0))), radius=9, n=500)
    S.cam(V((BENCH.x + 0.5, BENCH.y, 2.5)), dist=15, yaw=75, height=4.5, lens=30, fstop=None)
    return S


def s32(k, F):  # Now I spend every afternoon on our bench.
    S = street("sunset")
    n = sit_bench(S, "Narrator", -1.2, "sad")
    bench_cam(S, dist=11, yaw=95, h=4.2)
    return S


def s33(k, F):  # I leave room on the left.
    S = street("sunset")
    n = sit_bench(S, "Narrator", -1.2, "sad", yaw=90)
    n.look(1, 35, -5)
    S.cam(V((BENCH.x + 0.5, BENCH.y, 3.0)), dist=20, yaw=90, height=6, lens=30, fstop=None)
    return S


def s34(k, F):  # I save him the last pickle.
    S = street("sunset")
    pickle((BENCH.x + 0.1, BENCH.y + 1.2, 1.85))
    S.cam_at(V((BENCH.x + 2.3, BENCH.y + 2.4, 3.4)), V((BENCH.x + 0.1, BENCH.y + 1.2, 1.9)), lens=40, fstop=2.0)
    return S


def s35(k, F):  # Every minute I promised. Just late.
    S = street("sunset")
    n = sit_bench(S, "Narrator", -1.2, "crying", yaw=105)
    n.look(1, 25, -10)
    pickle((BENCH.x + 0.1, BENCH.y + 1.2, 1.85))
    S.cam(n.head_pt() - V((0, 0, 0.8)), dist=6.5, yaw=105, height=n.head_pt().z, lens=38)
    return S


# ---------------------------------------------------------------- new beats (peer pressure version)
def b_together(k, F):  # Rio and I were always together.
    S = street("sunset")
    sit_bench(S, RIO, 1.2, "laugh", yaw=70)
    sit_bench(S, "Narrator", -1.2, "laugh", yaw=110)
    S.cam(V((BENCH.x + 0.5, BENCH.y + 2, 3.2)), dist=16, yaw=75, height=5.5, lens=30, fstop=None)
    return S


def b_lunch(k, F):  # At lunch.
    S = rblx.Stage(PACK, "day")
    cx, cy = canteen(S)
    stool = kit.mat("stool", (0.55, 0.55, 0.6))
    for x in (-17.4, -15.6):
        kit.box((1.6, 1.2, 1.2), (cx + x, cy - 11.6, 0.6), stool, 0.03)
    for nm, x in (("Narrator", -17.4), (RIO, -15.6)):
        c = S.char(nm, (cx + x, cy - 11.2, -0.3), 0, "smile")
        c.sit(1)
        c.arm("L", 1, 70)
        c.arm("R", 1, 70)
    S.cam(V((cx - 16.5, cy - 10.5, 2.6)), dist=11, yaw=10, height=4.8, lens=32)
    return S


def b_bench(k, F):  # On our bench.
    S = street("sunset")
    sit_bench(S, RIO, 1.2, "smile", yaw=75)
    sit_bench(S, "Narrator", -1.2, "smile", yaw=105)
    bench_cam(S, dist=10, yaw=90, h=4.0)
    return S


def b_pickle_give(k, F):  # He always saved me the last pickle.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "smile", yaw=40)
    n = sit_bench(S, "Narrator", -1.2, "laugh", yaw=140)
    pk = kit.cyl(0.3, 0.06, tuple(r.world((1.5, 0.4, 1.8))), kit.mat("pickle", (0.45, 0.65, 0.2)), verts=14, rot=(90, 0, 0))
    attach(pk, r.arms["R"])
    r.arm("R", 1, 40)
    r.arm("R", kf(10), 85, -25)
    S.cam(V((BENCH.x + 0.4, BENCH.y, 3.0)), dist=7, yaw=95, height=3.8, lens=36)
    return S


def b_laughing(k, F):  # Kids started laughing at us.
    S = rblx.Stage(PACK, "day")
    cx, cy = canteen(S)
    stool = kit.mat("stool", (0.55, 0.55, 0.6))
    for x in (-17.4, -15.6):
        kit.box((1.6, 1.2, 1.2), (cx + x, cy - 11.6, 0.6), stool, 0.03)
    for nm, x in (("Narrator", -17.4), (RIO, -15.6)):
        c = S.char(nm, (cx + x, cy - 11.2, -0.3), 0, "sad")
        c.sit(1)
    for i, (nm, x, y) in enumerate((("Crowd1", -13, -6), ("Crowd2", -11, -7.5), ("Kai", -14.5, -4.5), ("Cousin", -10, -5))):
        yaw = math.degrees(math.atan2((-16.5) - x, -((-11.2) - y)))
        c = S.char(nm, (cx + x, cy + y), yaw, "laugh")
        c.point(1 + i * 2, "R", up=-10)
        c.talk(2 + i * 3, F, base="laugh")
    S.cam(V((cx - 14, cy - 8, 2.8)), dist=15, yaw=30, height=5.5, lens=28, fstop=None)
    return S


def tease(name, expr):
    def shot(k, F):
        S = rblx.Stage(PACK, "day")
        cx, cy = canteen(S)
        c = S.char(name, (cx - 12, cy - 6.5), -135, expr)
        c.point(1, "R", up=-10)
        c.talk(3, F, base=expr)
        S.cam(c.head_pt() - V((0, 0, 1.0)), dist=7, yaw=-135, height=c.head_pt().z - 0.3, lens=36)
        return S
    return shot


def b_kai(k, F):  # Kai said, "With Rio's gift, you'd actually be somebody."
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x - 1.3, PG.y), 90, "worried")
    kai = S.char("Kai", (PG.x + 1.5, PG.y + 0.2), -95, "smirk")
    kai.lean(1, 12)
    kai.arm("L", 1, 85, 10)
    kai.talk(3, F, base="smirk")
    n.look(1, 0, -10)
    S.cam_at(V((PG.x - 4.0, PG.y - 5.5, 5.4)), kai.head_pt() - V((0, 0, 1.2)), lens=30)
    return S


def rio_says(expr, talk=True):
    def shot(k, F):
        S = street("sunset")
        r = sit_bench(S, RIO, 1.2, expr, yaw=45)
        if talk:
            r.talk(3, F, base=expr)
        S.cam(r.head_pt() - V((0, 0, 0.7)), dist=6, yaw=45, height=r.head_pt().z, lens=40)
        return S
    return shot


def b_give(k, F):  # Then he gave it to me anyway.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "smile", yaw=40)
    n = sit_bench(S, "Narrator", -1.2, "shocked", yaw=140)
    orb = glow_orb(tuple(r.world((1.5, 1.4, 2.6))), 150)
    attach(orb, r.arms["R"])
    r.arm("R", 1, 40)
    r.arm("R", kf(12), 85, -20)
    bench_cam(S, dist=9, yaw=90, h=4.0)
    return S


# ---------------------------------------------------------------- v7 beats (strength + danger sense)
def c_fly(k, F):  # Some can fly a little.
    S = street("morning")
    c = S.char("Crowd1", (11, -3500, 0.0), 0, "laugh")
    p = c.pos
    kit.key(c.root, 1, loc=(p.x, p.y, p.z))
    for j, f in enumerate(range(kf(6), F + 2, 10)):
        kit.key(c.root, f, loc=(p.x, p.y, p.z + (1.4 if j % 2 else 1.1)))
    c.arm("L", 1, 0, 70)
    c.arm("R", 1, 0, 70)
    kit.sparkle_particles(tuple(c.world((0, 0, 0.5))), n=14, radius=0.9, frames=F + 10, color=(0.7, 0.85, 1))
    S.cam(V((11, -3500, 3.2)), dist=10, yaw=-10, height=3.6, lens=32)
    return S


def lift_can(S, n, F, drop=True):
    can = kit.cyl(1.0, 2.4, tuple(n.world((0, 1.2, 1.2))), kit.mat("tcan", (0.25, 0.45, 0.3)), verts=16)
    up = kf(F * 0.25)
    p0 = V(can.location)
    kit.key(can, 1, loc=tuple(p0))
    kit.key(can, up, loc=tuple(p0 + V((0, -0.6, 4.6))))
    if drop:
        kit.key(can, up + 8, loc=tuple(p0 + V((0, -0.6, 4.6))))
        kit.key(can, up + 14, loc=tuple(p0 + V((0.6, 0.4, 0))), rot=(0, 20, 0))
    else:
        kit.key(can, F, loc=tuple(p0 + V((0, -0.6, 4.6))))
    n.arm("L", up, 175, 5)
    n.arm("R", up, 175, 5)
    if drop:
        n.arm("L", up + 10, 20, 30)
        n.arm("R", up + 10, 20, 30)
    return can


def c_strong(k, F):  # Mine? I'm super strong, for one second.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 180, "determined")
    lift_can(S, n, F, drop=False)
    n.faces([(1, "determined"), (kf(F * 0.3), "laugh")])
    S.cam(V((PG.x, PG.y, 3.6)), dist=12, yaw=180, height=4.2, lens=30)
    return S


def c_gone(k, F):  # Then it's gone.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 180, "laugh")
    can = kit.cyl(1.0, 2.4, tuple(n.world((0, 0.2, 7.2))), kit.mat("tcan", (0.25, 0.45, 0.3)), verts=16)
    kit.key(can, 1, loc=tuple(can.location))
    kit.key(can, kf(8), loc=tuple(can.location))
    kit.key(can, kf(14), loc=tuple(n.world((0.4, 0.4, 5.6))), rot=(0, 25, 0))
    n.arm("L", 1, 175)
    n.arm("R", 1, 175)
    n.arm("L", kf(12), 120, 50)
    n.arm("R", kf(12), 120, 50)
    n.faces([(1, "laugh"), (kf(10), "shocked")])
    S.cam(V((PG.x, PG.y, 4.0)), dist=11, yaw=180, height=4.8, lens=30)
    return S


def c_noclap(k, F):  # Nobody claps for that.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 180, "sad")
    kit.cyl(1.0, 2.4, tuple(n.world((1.8, 0.8, 1.2))), kit.mat("tcan", (0.25, 0.45, 0.3)), verts=16)
    for nm, x in (("Prey1", -6), ("Crowd2", -8)):
        c = S.char(nm, (PG.x + x, PG.y + 2.5), 90, "neutral")
        c.walk(1, F, (PG.x + x + 9, PG.y + 2.5))
    S.cam(V((PG.x, PG.y + 1, 3)), dist=13, yaw=180, height=4.5, lens=30)
    return S


def c_orb(k, F):  # You can give your gift away, but only once.
    S = street("sunset")
    a = S.char("Prey2", (10.2, -3500), 60, "smile")
    b = S.char("Prey1", (12.4, -3500.4), -60, "smile")
    orb = glow_orb((11.3, -3501.2, 2.8), 200)
    kit.key(orb, 1, loc=(10.9, -3501.2, 2.6))
    kit.key(orb, F, loc=(11.8, -3501.2, 2.8))
    a.arm("R", 1, 80, -20)
    b.arm("L", 1, 80, -20)
    S.cam(V((11.3, -3500.5, 2.8)), dist=7, yaw=0, height=3.6, lens=36)
    return S


def c_deathbed(k, F):  # Most people only do it at the very end, to their kids.  (gentle: a glow over a bed)
    from stories.nothing_happens import night_house
    S, h = night_house()
    hx, hy = HOUSE
    orb = glow_orb((hx + 4.6, hy + 2.0, 3.6), 300)
    kit.key(orb, 1, loc=(hx + 4.6, hy + 2.6, 3.4), scale=(1, 1, 1))
    kit.key(orb, F, loc=(hx + 4.6, hy - 1.0, 3.8), scale=(0.6, 0.6, 0.6))
    S.cam_at(V((hx + 0.5, hy - 5.5, 6.5)), V((hx + 4.6, hy + 1.5, 2.8)), lens=28, fstop=None)
    return S


def c_rio_danger(k, F):  # He could sense danger.
    S = street("sunset")
    r = S.char(RIO, (11, -3500), -10, "worried")
    r.faces([(1, "neutral"), (kf(6), "worried")])
    eye_glow(r, kf(6), 14)
    S.cam(r.head_pt() - V((0, 0, 0.9)), dist=6.5, yaw=-10, height=r.head_pt().z - 0.3, lens=40)
    return S


def c_cant_stop(k, F):  # That's it. He couldn't stop it. He just felt it coming.
    S = rblx.Stage(PACK, "day")
    r = S.char(RIO, (PG.x - 2, PG.y), 150, "scared")
    o = S.char("Prey1", (PG.x + 2.5, PG.y + 1), 200, "smile")
    ball = kit.sphere(0.6, (PG.x + 9, PG.y + 3, 5), kit.mat("ball", (0.95, 0.3, 0.2)), seg=16)
    kit.key(ball, 1, loc=(PG.x + 12, PG.y + 3, 6))
    kit.key(ball, kf(F * 0.55), loc=tuple(o.head_pt()))
    kit.key(ball, kf(F * 0.8), loc=(PG.x + 1.5, PG.y - 1, 0.6))
    r.arm("L", 1, 120, 30)
    r.arm("R", 1, 120, 30)
    o.faces([(1, "smile"), (kf(F * 0.55), "shocked")])
    S.cam(V((PG.x, PG.y + 0.5, 3)), dist=13, yaw=180, height=4.5, lens=30)
    return S


def c_scaredy(k, F):  # Kids called him a scaredy cat.
    S = rblx.Stage(PACK, "day")
    r = S.char(RIO, (PG.x, PG.y), 180, "sad")
    r.look(1, 0, -15)
    for i, (nm, dx) in enumerate((("Crowd1", -3), ("Crowd2", 3), ("Kai", 0.4))):
        c = S.char(nm, (PG.x + dx, PG.y + 3.6), dx * 8, "laugh")
        c.point(1 + i * 2, "R", up=-10)
        c.talk(2 + i * 3, F, base="laugh")
    S.cam(V((PG.x, PG.y + 1.8, 3)), dist=14, yaw=60, height=5, lens=30)
    return S


def c_halls(k, F):  # They laughed in the halls. They laughed at lunch.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x - 0.8, PG.y), 180, "sad")
    r = S.char(RIO, (PG.x + 0.8, PG.y), 180, "sad")
    for i, nm in enumerate(("Crowd1", "Crowd2", "Crowd4", "Cousin", "Prey3")):
        a = 2.2 + i * 0.5
        x, y = PG.x + math.cos(a) * 5, PG.y + math.sin(a) * 5 + 1
        yaw = math.degrees(math.atan2(PG.x - x, -(PG.y - y)))
        c = S.char(nm, (x, y), yaw, "laugh")
        c.point(1 + i * 3, "R", up=-10)
    S.cam(V((PG.x, PG.y + 1, 3)), dist=15, yaw=180, height=7, lens=28, fstop=None)
    return S


def c_enough(k, F):  # One day, I'd had enough.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 180, "angry")
    n.arm("L", 1, 30, -10)
    n.arm("R", 1, 30, -10)
    S.cam(n.head_pt() - V((0, 0, 0.8)), dist=6, yaw=180, height=n.head_pt().z, lens=40)
    return S


def c_promise(k, F):  # "I'll keep you safe," I said. "Every minute. I promise."
    S = street("sunset")
    n = sit_bench(S, "Narrator", -1.2, "determined", yaw=135)
    n.talk(3, F, base="determined")
    n.arm("R", 1, 60, -20)
    S.cam(n.head_pt() - V((0, 0, 0.7)), dist=6, yaw=135, height=n.head_pt().z, lens=40)
    return S


def c_strong_win(k, F):  # Together, I always knew the exact second to be strong.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 180, "smirk")
    eye_glow(n, kf(4), 12)
    lift_can(S, n, F, drop=False)
    S.cam(V((PG.x, PG.y, 3.6)), dist=12, yaw=180, height=4.2, lens=30)
    return S


def c_race(k, F):  # I won every game. Every race.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x - 6, PG.y), 90, "laugh")
    n.run(1, F, (PG.x + 4, PG.y))
    for i, nm in enumerate(("Crowd2", "Prey1")):
        c = S.char(nm, (PG.x - 9.5 - i * 1.5, PG.y + 1.2 + i), 90, "tired")
        c.run(1, F, (PG.x - 1 - i * 1.5, PG.y + 1.2 + i))
    S.cam(V((PG.x - 1, PG.y, 2.8)), dist=13, yaw=170, height=4, lens=30)
    return S


def c_kai_lose(k, F):  # Even Kai couldn't touch me.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x - 1.5, PG.y), 90, "smirk")
    kai = S.char("Kai", (PG.x + 1.6, PG.y), -90, "angry")
    eye_glow(n, 1, 10)
    kai.arm("R", 1, 40)
    kai.arm("R", kf(8), 100)
    kai.lean(kf(8), 20)
    n.key_root(kf(6), (PG.x - 1.5, PG.y))
    n.key_root(kf(10), (PG.x - 1.6, PG.y - 1.6))
    kai.key_root(kf(14), (PG.x + 0.4, PG.y), tilt=0)
    kai.key_root(kf(22), (PG.x - 0.6, PG.y), tilt=-80)
    kai.faces([(1, "angry"), (kf(14), "shocked")])
    S.cam(V((PG.x, PG.y, 2.8)), dist=12, yaw=180, height=4.2, lens=30)
    return S


def c_popular(k, F):  # Everyone wanted to sit with me now.
    S = rblx.Stage(PACK, "day")
    cx, cy = canteen(S)
    n = S.char("Narrator", (cx - 8, cy + 2.4, 0.25), 180, "laugh")
    n.sit(1)
    for i, (nm, dx, dy, yaw) in enumerate((("Prey1", -11, 2.4, 180), ("Crowd1", -5, 2.4, 180), ("Crowd2", -8, -2.4, 0),
                                            ("Kai", -6, -2.4, 0), ("Cousin", -10.5, -2.4, 0))):
        c = S.char(nm, (cx + dx, cy + dy, 0.25), yaw, "laugh")
        c.sit(1)
        c.talk(1 + i * 3, F, base="laugh")
    S.cam(V((cx - 8, cy, 3.0)), dist=14, yaw=-15, height=6, lens=30, fstop=None)
    return S


def c_regular(k, F):  # Without his gift, Rio was just a regular kid.
    S = street("day")
    r = S.char(RIO, (11, -3500), -10, "neutral")
    r.walk(1, F, (11, -3503), swing=22)
    S.cam(r.chest_pt() + V((0, 0, 0.6)), dist=10, yaw=-10, lens=34)
    return S


def c_rain(k, F):  # He got caught in the rain.
    S = street("rain")
    r = S.char(RIO, (11, -3500), -10, "shocked")
    r.arm("L", 1, 160, 20)
    r.arm("R", 1, 160, 20)
    S.rain(F, (11, -3500, 0), radius=7, n=450)
    S.cam(r.chest_pt() + V((0, 0, 0.6)), dist=9, yaw=-10, lens=34)
    return S


def c_trip(k, F):  # He tripped on the stairs.
    S = rblx.Stage(PACK, "day")
    r = S.char(RIO, (PG.x, PG.y), 90, "smile")
    r.walk(1, kf(F * 0.4), (PG.x + 1.5, PG.y))
    r.key_root(kf(F * 0.4), tilt=0)
    r.key_root(kf(F * 0.65), (PG.x + 2.4, PG.y), tilt=-80)
    r.faces([(1, "smile"), (kf(F * 0.45), "shocked")])
    r.arm("L", kf(F * 0.55), 150)
    r.arm("R", kf(F * 0.55), 150)
    for k2 in range(3):
        kit.box((3.0, 1.2, 0.5 * (k2 + 1)), (PG.x + 1.6 + k2 * 0.0, PG.y + 3.0 - k2 * 1.2, 0.25 * (k2 + 1)),
                kit.mat("steps", (0.7, 0.7, 0.72)), 0.02)
    S.cam(V((PG.x + 1.5, PG.y, 2.5)), dist=11, yaw=180, height=4, lens=30)
    return S


def c_ball(k, F):  # He never saw the ball coming.
    S = rblx.Stage(PACK, "day")
    r = S.char(RIO, (PG.x, PG.y), 180, "smile")
    ball = kit.sphere(0.6, (PG.x + 9, PG.y + 3, 5), kit.mat("ball", (0.95, 0.3, 0.2)), seg=16)
    hit = kf(F * 0.45)
    kit.key(ball, 1, loc=(PG.x + 10, PG.y + 4, 6))
    kit.key(ball, hit, loc=tuple(r.head_pt() + V((0.5, 0.3, 0.4))))
    kit.key(ball, kf(F * 0.8), loc=(PG.x - 3, PG.y + 2, 0.6))
    r.faces([(1, "smile"), (hit, "shocked")])
    r.lean(hit + 2, -15, 10)
    S.cam(V((PG.x, PG.y, 3.2)), dist=10, yaw=180, height=4.2, lens=32)
    return S


def c_laughoff(k, F):  # He just laughed it off.
    S = rblx.Stage(PACK, "day")
    r = S.char(RIO, (PG.x, PG.y), 180, "laugh")
    r.arm("R", 1, 150, 30)  # rubbing his head
    S.cam(r.head_pt() - V((0, 0, 0.9)), dist=6, yaw=180, height=r.head_pt().z - 0.2, lens=40)
    return S


def c_wait_night(k, F):  # He waited after school. He waited until the streetlights came on.
    from stories.nothing_happens import lamps_on
    S = street("night")
    lamps_on(S, kf(F * 0.4), gap=2, near=(BENCH.x, BENCH.y, 0))
    r = sit_bench(S, RIO, 1.2, "sad")
    r.look(1, 40, 0)
    r.look(kf(F * 0.5), -30, 0)
    S.cam(V((BENCH.x + 0.5, BENCH.y + 1, 3.0)), dist=17, yaw=75, height=5, lens=30, fstop=None)
    return S


def c_felt(k, F):  # Then, one afternoon, I felt danger. It came from our bench.
    S = rblx.Stage(PACK, "dusk")
    n = S.char("Narrator", (PG.x, PG.y), 180, "smile")
    n.faces([(1, "smile"), (kf(6), "scared")])
    eye_glow(n, kf(6), 18)
    S.flash_light(tuple(n.head_pt() + V((0, 2, 0))), kf(6), kf(6) + 6, (1, 0.5, 0.4), 2500)
    n.look(kf(12), 60, 0)
    S.cam(n.head_pt() - V((0, 0, 0.8)), dist=6, yaw=180, height=n.head_pt().z, lens=40)
    return S


ORDER = [s01, s02, s03, c_fly, c_strong, c_gone, c_noclap, c_orb, c_deathbed,
         s07, c_rio_danger, c_cant_stop, c_scaredy,
         b_together, b_lunch, b_bench, b_pickle_give,
         b_laughing, tease("Crowd1", "laugh"), tease("Crowd2", "smirk"), c_halls, b_kai,
         c_enough, s15, c_promise, s16, rio_says("sad"), rio_says("smile"), b_give,
         s19, c_strong_win, c_race, c_kai_lose, c_popular,
         c_regular, c_rain, c_trip, c_ball, c_laughoff,
         s23, c_wait_night, s24, s25,
         c_felt, s30,
         s32, s33, s34, s35]
SHOTS = {i + 1: f for i, f in enumerate(ORDER)}
