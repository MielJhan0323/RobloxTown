"""five-seconds ("Five Seconds") - everyone gets one gift; Rio gives his (future sight) away.

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
from stories.nothing_happens import text

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


def s05(k, F):  # My gift? I could whistle really loud.
    S = street("morning")
    n = S.char("Narrator", (11, -3500), 0, "smirk")
    n.faces([(1, "smirk"), (kf(8), "shocked")])   # the round mouth = whistle
    for nm, x, y in (("Prey1", 8.8, -3497.5), ("Crowd1", 13.3, -3497.8)):
        c = S.char(nm, (x, y), 0, "angry")
        for side in "LR":
            c.arm(side, kf(10), 150, 35)
        c.lean(kf(10), -10)
    S.cam(V((11, -3499, 3.4)), dist=12, yaw=-8, height=4.4, lens=34)
    return S


def s06(k, F):  # Rio's gift was the best one.
    S = street("sunset")
    r = S.char(RIO, (11, -3500), -10, "smile")
    kit.sparkle_particles(tuple(r.head_pt()), n=24, radius=2.0, frames=F + 10, color=(1, 0.85, 0.4))
    S.cam(r.chest_pt() + V((0, 0, 0.7)), dist=9, yaw=-10, lens=36)
    return S


def s07(k, F):  # He could see five seconds into the future.
    S = street("sunset")
    r = S.char(RIO, (11, -3500), -10, "determined")
    eye_glow(r, kf(6), 18)
    S.cam(r.head_pt() - V((0, 0, 0.9)), dist=6.5, yaw=-10, height=r.head_pt().z - 0.3, lens=40)
    return S


def s08(k, F):  # He never dropped a plate.
    S = rblx.Stage(PACK, "day")
    cx, cy = canteen(S)
    r = S.char(RIO, (cx - 4, cy - 4), 0, "smile")
    other = S.char("Prey2", (cx - 6.5, cy - 4.5), 30, "shocked")
    tray = kit.box((1.6, 1.2, 0.12), (cx - 5.4, cy - 5.2, 3.0), kit.mat("ftray", (0.95, 0.65, 0.2)), 0.02)
    kit.key(tray, 1, loc=(cx - 5.4, cy - 5.2, 3.0), rot=(0, 0, 0))
    kit.key(tray, kf(10), loc=(cx - 4.6, cy - 5.4, 2.0), rot=(40, 10, 0))
    kit.key(tray, kf(16), loc=tuple(r.world((0, 1.6, 2.6))), rot=(0, 0, 0))
    kit.key(tray, F, loc=tuple(r.world((0, 1.6, 2.6))), rot=(0, 0, 0))
    r.arm("L", kf(12), 85, -10)
    r.arm("R", kf(12), 85, -10)
    r.faces([(1, "smile"), (kf(16), "smirk")])
    S.cam(V((cx - 5, cy - 4.5, 3.0)), dist=12, yaw=-15, height=4.6, lens=32)
    return S


def s09(k, F):  # He never lost at tag.
    S = rblx.Stage(PACK, "day")
    r = S.char(RIO, (PG.x, PG.y), 180, "laugh")
    r.key_root(1, (PG.x, PG.y))
    r.key_root(kf(12), (PG.x + 2.5, PG.y + 0.5))
    r.lean(kf(12), 0, 20)
    for nm, x, y in (("Crowd2", PG.x - 3, PG.y + 3), ("Prey1", PG.x + 3, PG.y + 3.5)):
        c = S.char(nm, (x, y), 180 + (30 if x < PG.x else -30), "shocked")
        c.run(1, kf(12), (PG.x + (0.4 if x < PG.x else 1.6), PG.y + 0.8))
        c.arm("R", kf(12), 90)
    S.cam(V((PG.x + 0.5, PG.y + 1.5, 2.8)), dist=16, yaw=180, height=6, lens=30)
    return S


def s10(k, F):  # He always knew when I was about to laugh.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "laugh", yaw=60)
    n = sit_bench(S, "Narrator", -1.2, "smile", yaw=120)
    n.faces([(1, "smile"), (kf(F * 0.4), "laugh")])
    r.point(kf(4), "R", up=-30)
    bench_cam(S, dist=10, yaw=90, h=4.0)
    return S


def s11(k, F):  # I think I liked him before I knew what that meant.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "laugh", yaw=70)
    n = sit_bench(S, "Narrator", -1.2, "embarrassed", yaw=130)
    n.look(1, 10, 5)
    S.cam(n.head_pt() - V((0, 0, 0.6)), dist=6, yaw=130, height=n.head_pt().z, lens=40)
    return S


def s12(k, F):  # Every afternoon, we sat on the bench by the burger stand.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "smile")
    n = sit_bench(S, "Narrator", -1.2, "smile")
    S.cam(V((BENCH.x + 0.5, BENCH.y + 4.5, 3.2)), dist=20, yaw=70, height=6, lens=30, fstop=None)
    return S


def hand_burger(c, side="R"):
    b = burger(tuple(c.world((1.5 if side == "R" else -1.5, 0.3, c.meta["shoulder"] - c.meta["arm_len"] - 0.2))), 0.9)
    attach(b, c.arms[side])
    return b


def s13(k, F):  # He always got a double cheeseburger, extra pickles.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "laugh", yaw=80)
    hand_burger(r, "R")
    for j, f in enumerate(range(1, F + 2, 10)):
        r.arm("R", f, 120 if j % 2 else 100, -10)
    S.cam(r.head_pt() - V((0, 0, 1.0)), dist=6.5, yaw=80, height=r.head_pt().z - 0.2, lens=38)
    return S


def s14(k, F):  # Then, on my birthday, Rio gave me his gift.
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "smile", yaw=40)
    n = sit_bench(S, "Narrator", -1.2, "shocked", yaw=140)
    orb = glow_orb(tuple(r.world((1.5, 1.4, 2.6))), 150)
    attach(orb, r.arms["R"])
    r.arm("R", 1, 40)
    r.arm("R", kf(12), 85, -20)
    bench_cam(S, dist=9, yaw=90, h=4.0)
    return S


def s15(k, F):  # "Just promise you'll spend every minute with me,"
    S = street("sunset")
    r = sit_bench(S, RIO, 1.2, "smile", yaw=40)
    r.talk(3, F, base="smile")
    S.cam(r.head_pt() - V((0, 0, 0.7)), dist=6, yaw=40, height=r.head_pt().z, lens=40)
    return S


def s16(k, F):  # he said. I promised.
    S = street("sunset")
    n = sit_bench(S, "Narrator", -1.2, "smile", yaw=140)
    orb = glow_orb(tuple(n.world((0, 1.6, 2.4))), 250)
    kit.key(orb, 1, loc=tuple(orb.location), scale=(1, 1, 1))
    kit.key(orb, F, loc=tuple(orb.location), scale=(0.1, 0.1, 0.1))
    n.arm("L", 1, 70, -20)
    n.arm("R", 1, 70, -20)
    eye_glow(n, kf(F * 0.6), 15)
    S.cam(n.head_pt() - V((0, 0, 1.1)), dist=6.5, yaw=140, height=n.head_pt().z - 0.2, lens=38)
    return S


def s17(k, F):  # With his gift, I won every game.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 180, "laugh")
    n.arm("L", 1, 170, 15)
    n.arm("R", 1, 170, 15)
    for i, nm in enumerate(("Prey1", "Crowd2", "Crowd1", "Smallkid")):
        a = 2.4 + i * 0.5
        c = S.char(nm, (PG.x + math.cos(a) * 5, PG.y + math.sin(a) * 5), 180 + (i - 1.5) * 25, "laugh")
        for j, f in enumerate(range(1, F + 2, 8)):
            c.arm("L", f, 160 if j % 2 else 130, 10)
            c.arm("R", f, 160 if j % 2 else 130, 10)
    S.cam(V((PG.x, PG.y + 2, 3)), dist=14, yaw=180, height=5.5, lens=30)
    return S


def s18(k, F):  # Every race.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x - 6, PG.y), 90, "laugh")
    n.run(1, F, (PG.x + 4, PG.y))
    for i, nm in enumerate(("Crowd2", "Prey1")):
        c = S.char(nm, (PG.x - 9.5 - i * 1.5, PG.y + 1.2 + i), 90, "tired")
        c.run(1, F, (PG.x - 1 - i * 1.5, PG.y + 1.2 + i))
    S.cam(V((PG.x - 1, PG.y, 2.8)), dist=13, yaw=170, height=4, lens=30)
    return S


def s19(k, F):  # Everyone wanted to be my friend.
    S = rblx.Stage(PACK, "day")
    n = S.char("Narrator", (PG.x, PG.y), 180, "laugh")
    for i, nm in enumerate(("Prey1", "Crowd2", "Crowd1", "Smallkid", "Prey2", "Crowd4")):
        a = i / 6 * 2 * math.pi + 0.5
        x, y = PG.x + math.cos(a) * 3.2, PG.y + math.sin(a) * 3.2
        yaw = math.degrees(math.atan2(PG.x - x, -(PG.y - y)))
        c = S.char(nm, (x, y), yaw, "laugh")
        c.talk(1 + i * 2, F, base="laugh")
    S.cam(V((PG.x, PG.y, 2)), dist=13, yaw=180, height=8, lens=30)
    return S


def s20(k, F):  # The bench got lonely.
    S = street("dusk")
    r = sit_bench(S, RIO, 1.2, "sad")
    burger((BENCH.x + 0.1, BENCH.y - 0.8, 1.95), 0.8)
    burger((BENCH.x + 0.1, BENCH.y - 1.8, 1.95), 0.8)
    S.cam(V((BENCH.x + 0.5, BENCH.y + 1, 3.0)), dist=17, yaw=75, height=5, lens=30, fstop=None)
    return S


def s21(k, F):  # Rio kept saving me a seat.
    S = street("dusk")
    r = sit_bench(S, RIO, 1.2, "sad", yaw=110)
    r.arm("R", 1, 40, -10)
    for j, f in enumerate(range(1, F + 2, 8)):
        r.arm("R", f, 55 if j % 2 else 45, 30)
    r.look(1, 30, -15)
    bench_cam(S, dist=8, yaw=90, h=3.8)
    return S


def s22(k, F):  # I kept saying, "Tomorrow."
    S = rblx.Stage(PACK, "dusk")
    n = S.char("Narrator", (PG.x, PG.y), 180, "smile")
    n.talk(4, F, base="smile")
    for j, f in enumerate(range(1, F + 2, 6)):
        n.arm("R", f, 10, 120 if j % 2 else 90)
    for nm, dx in (("Crowd2", -2.2), ("Prey1", 2.3)):
        S.char(nm, (PG.x + dx, PG.y - 0.8), 180 + (-20 if dx < 0 else 20), "laugh")
    S.cam(n.head_pt() - V((0, 0, 1.6)), dist=9, yaw=180, height=n.head_pt().z - 0.6, lens=34)
    return S


def s23(k, F):  # Then, one afternoon, Rio crossed the street to buy our burgers.
    S = street("dusk")
    r = S.char(RIO, (-9.5, -3510), 90, "smile")
    r.walk(1, F, (-4.5, -3510), swing=24)
    S.cam(V((-6, -3509, 3)), dist=16, yaw=30, height=5, lens=30, fstop=None)
    return S


def s24(k, F):  # I saw it five seconds before it happened.
    S = rblx.Stage(PACK, "dusk")
    n = S.char("Narrator", (PG.x, PG.y), 180, "smile")
    n.faces([(1, "smile"), (kf(6), "shocked")])
    eye_glow(n, kf(6), 22)
    flash = S.flash_light(tuple(n.head_pt() + V((0, 2, 0))), kf(6), kf(6) + 6, (1, 0.9, 0.6), 2500)
    S.cam(n.head_pt() - V((0, 0, 0.8)), dist=6, yaw=180, height=n.head_pt().z, lens=40)
    return S


def s25(k, F):  # But I was all the way across town.
    S = rblx.Stage(PACK, "dusk")
    n = S.char("Narrator", (PG.x - 8, PG.y + 2), 90, "scared")
    n.run(1, F, (PG.x + 4, PG.y + 2))
    S.cam(V((PG.x - 2, PG.y + 2, 2.8)), dist=20, yaw=165, height=6, lens=28, fstop=None)
    return S


def s26(k, F):  # And Rio couldn't see it at all.  (headlights only - nothing is shown)
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


def s27(k, F):  # He gave away the one thing that could have saved him.
    S = street("rain")
    burger((BENCH.x + 0.1, BENCH.y + 1.0, 1.95), 0.8)
    S.rain(F, tuple(BENCH + V((2, 0, 0))), radius=9, n=500)
    S.cam(V((BENCH.x + 0.5, BENCH.y, 2.5)), dist=15, yaw=75, height=4.5, lens=30, fstop=None)
    return S


def s28(k, F):  # Now, every afternoon, I sit on our bench with two burgers.
    S = street("sunset")
    n = sit_bench(S, "Narrator", -1.2, "sad")
    burger((BENCH.x + 0.1, BENCH.y + 0.6, 1.95), 0.8)
    burger((BENCH.x + 0.1, BENCH.y + 1.6, 1.95), 0.8)
    bench_cam(S, dist=11, yaw=95, h=4.2)
    return S


def s29(k, F):  # Extra pickles.
    S = street("sunset")
    b = burger((BENCH.x + 0.1, BENCH.y + 1.0, 1.95), 1.0)
    S.cam_at(V((BENCH.x + 2.4, BENCH.y + 1.5, 3.0)), V((BENCH.x + 0.1, BENCH.y + 1.0, 2.2)), lens=40, fstop=2.0)
    return S


def s30(k, F):  # And I keep my promise.
    S = street("sunset")
    n = sit_bench(S, "Narrator", -1.2, "crying", yaw=105)
    n.look(1, 20, -10)
    S.cam(n.head_pt() - V((0, 0, 0.8)), dist=6.2, yaw=105, height=n.head_pt().z, lens=40)
    return S


def s31(k, F):  # Every minute.
    S = street("sunset")
    n = sit_bench(S, "Narrator", -1.2, "sad", yaw=90)
    n.look(1, 35, -5)
    burger((BENCH.x + 0.1, BENCH.y + 1.2, 1.95), 0.8)
    S.cam(V((BENCH.x + 0.5, BENCH.y, 3.0)), dist=22, yaw=90, height=6.5, lens=30, fstop=None)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 32)}
