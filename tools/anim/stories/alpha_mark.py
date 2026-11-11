"""alpha-mark ("The Third Mark") - shots built from the user's exported Roblox Studio models.

Sets (Studio coordinates, studs): A street x -14..14, y -3580..-3420 | B school playground: school wall
faces +Y at y -3526, blacktop x -265..-235, y -3517..-3493 | C mountain trail x 245..259 descending
toward +Y, cliff edge at x ~260 (drop on +X side), bus at x 235, y -3470.
Characters face -Y at yaw 0; kit.camera yaw 0 sits at -Y, yaw 180 at +Y.
"""
import math
import random

import bpy
from mathutils import Vector

import rblx
from rblx import attach, kf

R = math.radians
V = Vector

PREY = ["Prey1", "Prey2", "Prey3", "Smallkid"]
PRED = ["Kai", "Cousin", "Crowd1", "Crowd2", "Crowd3", "Crowd4"]


def mark_for(c):
    if c.name == "Narrator":
        return c.mark("leaf")
    return c.mark("leaf" if c.name in PREY else "claw")


def wrist_cam(S, c, side=-3.6, fwd=5.6, h=4.4, lens=34, mix=0.5):
    """Three-quarter view of a raised left wrist that keeps the face in frame."""
    tgt = c.wrist_pt("L").lerp(c.head_pt(), mix) + c.world((0, 0.6, 0)) - c.pos
    return S.cam_at(c.world((side, fwd, h)), tgt, lens=lens)


def place(S, specs, marks=True):
    """specs: [(name, (x, y), yaw, expr)] -> dict of chars"""
    out = {}
    for name, xy, yaw, expr in specs:
        c = S.char(name, xy, yaw, expr)
        if marks:
            mark_for(c)
        out[name] = c
    return out


def outcast(c, f=1, expr="sad"):
    """Prey kids read as outcasts: head down, shoulders in, sad face."""
    c.face(f, expr)
    c.look(f, 0, -18)
    c.arm("L", f, 8, -6)
    c.arm("R", f, 8, -6)
    c.lean(f, 6)


def hold_end(frames):
    return frames + 15


# ---------------------------------------------------------------- set C dressing
def mountains(S):
    import kit
    rnd = random.Random(2)
    m1 = kit.mat("mtn", (0.36, 0.45, 0.32), rough=0.9)
    m2 = kit.mat("mtn2", (0.45, 0.5, 0.55), rough=0.9)
    snow = kit.mat("snow", (0.95, 0.96, 1.0), rough=0.9)
    for i in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(160, 260)
        x, y = 250 + math.cos(a) * d, -3500 + math.sin(a) * d
        h = rnd.uniform(60, 120)
        r = rnd.uniform(50, 90)
        kit.cyl(r, h, (x, y, -40 + h / 2), m1 if i % 2 else m2, verts=6, r2=0.0, rot=(0, 0, rnd.uniform(0, 1)))
        kit.cyl(r * 0.22, h * 0.22, (x, y, -40 + h * 0.89), snow, verts=6, r2=0.0)
    trunk = kit.mat("trunk", (0.35, 0.22, 0.12))
    leaves = kit.mat("leaves", (0.18, 0.5, 0.2))
    for i in range(18):
        x = rnd.uniform(205, 242)
        y = rnd.uniform(-3545, -3455)
        z = S.ground(x, y)
        if abs(x - 235) < 7 and -3485 < y < -3450:
            continue
        kit.box((0.8, 0.8, 4), (x, y, z + 2), trunk)
        kit.box((4, 4, 4), (x, y, z + 5.5), leaves)


def trail_pt(S, y, x=252.0):
    return V((x, y, S.ground(x, y)))


# ---------------------------------------------------------------- shots
def s01(k, F):  # kids walking to school (street, morning, wide)
    S = rblx.Stage("alpha-mark", "morning")
    cs = place(S, [("Narrator", (11, -3478), 0, "smile"), ("Crowd2", (12.4, -3480.5), 0, "laugh"),
                   ("Crowd1", (9.6, -3481), 0, "smile"), ("Prey1", (13.0, -3472), 0, "sad"),
                   ("Prey3", (9.4, -3469.5), 0, "sad")])
    for i, c in enumerate(cs.values()):
        p = c.pos
        c.walk(1, F, (p.x, p.y - 5), swing=30 if c.name not in PREY else 18)
    for nm in ("Prey1", "Prey3"):
        outcast(cs[nm])
    S.cam(V((11.0, -3478, 3.0)), dist=15, yaw=-28, height=5.0, lens=38, fstop=None)
    return S


def wrist_show(S, name, kind, F, xy=(10.5, -3480), yaw=0, expr="smile", light="morning"):
    c = S.char(name, xy, yaw, expr)
    p = c.mark(kind)
    c.arm("L", 1, 15)
    c.arm("L", kf(15), 42)
    c.look(1, 0, -10)
    wrist_cam(S, c)
    return c, p


def s02(k, F):  # a kid raises wrist (leaf)
    S = rblx.Stage("alpha-mark", "morning")
    wrist_show(S, "Crowd1", "leaf", F)
    return S


def s03(k, F):  # shy kid shows leaf
    S = rblx.Stage("alpha-mark", "morning")
    c, p = wrist_show(S, "Prey2", "leaf", F, xy=(-10.5, -3480))
    c.look(1, 15, -15)
    wrist_cam(S, c, side=-3.2, h=3.8)
    return S


def s04(k, F):  # tough kid shows claw
    S = rblx.Stage("alpha-mark", "morning")
    c, p = wrist_show(S, "Crowd3", "claw", F, xy=(10.5, -3500), expr="smirk")
    c.arm("R", 1, 0, 12)
    c.lean(1, -4)
    wrist_cam(S, c, side=-3.0, h=3.4)
    return S


LINE_X = -250.0


def s05(k, F):  # predators cut the lunch line
    S = rblx.Stage("alpha-mark", "day")
    prey = place(S, [("Prey1", (LINE_X, -3519), 0, "sad"), ("Prey2", (LINE_X, -3516.5), 0, "worried"),
                     ("Prey3", (LINE_X, -3514), 0, "sad"), ("Smallkid", (LINE_X, -3511.5), 0, "worried")])
    pred = place(S, [("Kai", (LINE_X + 3, -3514), 0, "smirk"), ("Cousin", (LINE_X + 3.2, -3510), 0, "smirk")])
    pred["Kai"].walk(1, F, (LINE_X + 0.4, -3521.5))
    pred["Cousin"].walk(1, F, (LINE_X + 2.6, -3517))
    for c in prey.values():
        outcast(c, 1, c.cur)
        c.look(kf(15), -35, -12)
    S.cam(V((LINE_X + 1, -3516, 3)), dist=15, yaw=50, height=5.5, lens=32)
    return S


def s06(k, F):  # prey eat by the trash cans
    S = rblx.Stage("alpha-mark", "day")
    cs = place(S, [("Prey1", (-229.5, -3520.5), 160, "sad"), ("Prey2", (-226, -3520), 200, "sad"),
                   ("Smallkid", (-231.3, -3519), 130, "sad")])
    import kit
    tray = kit.mat("tray", (0.85, 0.6, 0.2))
    for c in cs.values():
        c.sit(1)
        c.key_root(1, (c.pos.x, c.pos.y, S.ground(c.pos.x, c.pos.y) - 1.5))
        c.arm("L", 1, 55)
        c.arm("R", 1, 55)
        c.look(1, 0, -22)
        c.lean(1, 8)
        t = c.world((0, 1.5, 2.1))
        kit.box((1.3, 1.0, 0.12), tuple(t), tray)
    cs["Prey2"].arm("R", kf(16), 80)
    S.cam(V((-228.5, -3520.5, 1.8)), dist=11, yaw=180 + 10, height=3.5, lens=38)
    return S


def s07(k, F):  # cousin flexes claw
    S = rblx.Stage("alpha-mark", "day")
    c = S.char("Cousin", (-245, -3505), 180 + 15, "smirk")
    c.mark("claw")
    c.arm("L", 1, 30, 20)
    c.arm("L", kf(16), 80, 15)
    c.arm("R", 1, 0, 25)
    c.look(1, -10, 8)
    S.cam(c.chest_pt() + V((0, 0, 0.6)), dist=9, yaw=180 + 15, lens=40)
    return S


def s08(k, F):  # prey kid carries two backpacks behind cousin
    S = rblx.Stage("alpha-mark", "day")
    import kit
    co = S.char("Cousin", (-247, -3500), 90, "smirk")
    pk = S.char("Prey3", (-251, -3500), 90, "tired")
    bag1 = kit.mat("bag1", (0.2, 0.35, 0.8))
    bag2 = kit.mat("bag2", (0.85, 0.25, 0.25))
    attach(kit.box((1.6, 1.0, 1.8), tuple(pk.world((0, -1.0, 2.8))), bag1), pk.body)
    attach(kit.box((1.6, 1.0, 1.5), tuple(pk.world((0, 1.0, 2.6))), bag2), pk.body)
    pk.arm("L", 1, 60)
    pk.arm("R", 1, 60)
    co.walk(1, F, (-241, -3500))
    pk.walk(1, F, (-245, -3500), swing=15, arms=False)
    pk.lean(1, 12)
    pk.look(1, 0, -15)
    co.arm("L", 1, 0, 10)
    S.cam(V((-246, -3500, 2.8)), dist=17, yaw=180, height=4, lens=35)
    return S


def s09(k, F):  # crown mural, slow push
    S = rblx.Stage("alpha-mark", "day")
    S.cam_at(V((-236, -3513, 4.2)), V((-236, -3525.7, 3.9)), lens=35, fstop=None)
    return S


def s10(k, F):  # crown mural close
    S = rblx.Stage("alpha-mark", "day")
    S.flash_light((-236, -3523.5, 4.0), 2, None, (1, 0.85, 0.4), 400)
    S.cam_at(V((-236, -3519.5, 4.0)), V((-236, -3525.7, 4.0)), lens=40, fstop=None)
    return S


def narrator_marker(S, xy, yaw, expr, drawn=True):
    n = S.char("Narrator", xy, yaw, expr)
    leaf = n.mark("leaf")
    marker = n.mark("marker", lift=0.05, hidden=not drawn)
    return n, leaf, marker


def s11(k, F):  # Narrator shows "claw"
    S = rblx.Stage("alpha-mark", "day")
    n, leaf, mk = narrator_marker(S, (-246, -3503), 180 + 10, "smirk")
    S.show(leaf, 1, False)
    n.arm("L", 1, 45)
    n.arm("R", 1, 0, 8)
    n.lean(1, -5)
    S.cam(n.chest_pt() + V((0, 0, 0.3)), dist=10, yaw=180 + 5, lens=40)
    return S


def s12(k, F):  # hides marker behind back
    S = rblx.Stage("alpha-mark", "day")
    import kit
    n, leaf, mk = narrator_marker(S, (-246, -3503), 180 + 10, "smirk")
    S.show(leaf, 1, False)
    attach(kit.cyl(0.13, 1.1, tuple(n.world((1.5, 0.1, n.meta["shoulder"] - 2.1))), kit.mat("pen", (0.05, 0.05, 0.06)),
                   verts=8), n.arms["R"])
    n.arm("R", 1, 50)
    n.arm("R", kf(24), -45)
    n.faces([(1, "smirk"), (kf(24), "worried")])
    n.look(kf(24), 25, 0)
    S.cam(n.head_pt() - V((0, 0, 0.9)), dist=7, yaw=180 + 25, lens=45)
    return S


def s13(k, F):  # draws claw on wrist every morning
    S = rblx.Stage("alpha-mark", "morning")
    import kit
    n, leaf, mk = narrator_marker(S, (-221.5, -3509.5), 180, "neutral", drawn=True)
    S.show(mk, 1, False)
    S.show(mk, kf(F * 0.55), True)
    n.arm("L", 1, 42)
    n.arm("R", 1, 50, -28)
    n.arm("R", kf(16), 46, -22)
    n.look(1, 0, -25)
    attach(kit.cyl(0.13, 1.1, tuple(n.world((1.5, 0.1, n.meta["shoulder"] - 2.1))), kit.mat("pen", (0.05, 0.05, 0.06)),
                   verts=8), n.arms["R"])
    wrist_cam(S, n, side=-3.4, h=5.0, mix=0.35)
    return S


def s14(k, F):  # scrubs wrist at the fountain (dusk)
    S = rblx.Stage("alpha-mark", "dusk")
    n = S.char("Narrator", (-269, -3522), 0, "sad")
    n.mark("leaf")
    f = 1
    i = 0
    while f <= F:
        n.arm("L", f, 55)
        n.arm("R", f, 60, -25 if i % 2 else -10)
        f += 15
        i += 1
    n.look(1, 0, -20)
    S.cam(V((-269, -3522.5, 3.2)), dist=9, yaw=-70, height=4.5, lens=40)
    return S


def s15(k, F):  # stares at the leaf
    S = rblx.Stage("alpha-mark", "dusk")
    n = S.char("Narrator", (-262, -3515), 180, "sad")
    leaf = n.mark("leaf")
    n.arm("L", 1, 45)
    n.look(1, -10, -25)
    wrist_cam(S, n, side=-3.0, h=4.8, fwd=5.0)
    return S


def rain_stage(light="rain"):
    S = rblx.Stage("alpha-mark", light)
    return S


def s16(k, F):  # rain at recess: kids run for cover
    S = rain_stage()
    cs = place(S, [("Prey1", (-255, -3500), 180 + 160, "shocked"), ("Crowd2", (-248, -3497), 180 + 200, "shocked"),
                   ("Smallkid", (-252, -3503), 180 + 150, "shocked"), ("Crowd1", (-244, -3502), 180 + 190, "shocked"),
                   ("Narrator", (-249, -3507), 180, "worried")], marks=False)
    for nm, c in cs.items():
        if nm == "Narrator":
            c.arm("L", 1, 170); c.arm("R", 1, 170)
            continue
        p = c.pos
        c.run(1, F, (p.x + random.Random(nm).uniform(-3, 3), p.y - 8))
        c.arm("L", kf(1), 160); c.arm("R", kf(1), 160)
    S.rain(F, (-249, -3505, 0), radius=14, n=700, height=14)
    S.cam(V((-249, -3505, 3)), dist=22, yaw=180, height=8, lens=30)
    return S


def s17(k, F):  # Kai, arms crossed
    S = rain_stage()
    kai = S.char("Kai", (-249, -3509), 180 + 10, "smirk")
    kai.mark("claw")
    kai.arm("L", 1, 75, -40)
    kai.arm("R", 1, 70, -45)
    kai.look(1, -5, 6)
    S.rain(F, (-249, -3506, 0), radius=8, n=400)
    S.cam(kai.head_pt() - V((0, 0, 1.6)), dist=10, yaw=180 + 10, height=kai.head_pt().z - 1.0, lens=38)
    return S


def grab_pair(S, F, n_expr="neutral", k_expr="angry"):
    n = S.char("Narrator", (-249.5, -3505.5), 69, n_expr)
    kai = S.char("Kai", (-246.6, -3506.6), -111, k_expr)
    leaf = n.mark("leaf")
    mk = n.mark("marker", lift=0.05)
    kai.mark("claw")
    n.arm("L", 1, 38)
    kai.arm("R", 1, 72, -6)
    return n, kai, leaf, mk


def s18(k, F):  # Kai grabs Narrator's wrist
    S = rain_stage()
    n, kai, leaf, mk = grab_pair(S, F)
    kai.arm("R", 1, 30)
    kai.arm("R", kf(12), 72, -6)
    n.faces([(1, "neutral"), (kf(12), "shocked")])
    S.rain(F, (-248, -3506, 0), radius=8, n=400)
    S.cam(V((-248, -3506, 3.6)), dist=11, yaw=180 + 10, height=4.6, lens=38)
    return S


def s19(k, F):  # the claw runs in black streaks
    S = rain_stage()
    n, kai, leaf, mk = grab_pair(S, F, "shocked")
    st = n.mark("streaks", lift=0.06, size=1.0, dz=0.45, hidden=True)
    bpy.data.collections["CH_Kai"].hide_render = True
    S.show(mk, kf(F * 0.45), False)
    S.show(st, kf(F * 0.45), True)
    S.rain(F, (-249, -3505, 0), radius=6, n=350)
    S.plate_view(leaf, dist=4.2, up=0.9, side=0.9, lens=34, frame=1)
    return S


def s20(k, F):  # "He's prey," Kai said.
    S = rain_stage()
    n, kai, leaf, mk = grab_pair(S, F, "shocked", "shocked")
    kai.key_root(1, yaw=-60)
    kai.arm("R", 1, 72, 30)
    kai.faces([(1, "shocked"), (kf(F * 0.6), "smirk")])
    kai.talk(kf(F * 0.6), F, base="smirk")
    kai.look(kf(F * 0.6), 10, 5)
    S.rain(F, (-247, -3506, 0), radius=6, n=350)
    S.cam(kai.head_pt() - V((0, 0, 1.4)), dist=9, yaw=-40, height=kai.head_pt().z - 0.6, lens=38)
    return S


def s21(k, F):  # "He's been faking it." to the crowd
    S = rain_stage()
    n, kai, leaf, mk = grab_pair(S, F, "worried", "smirk")
    kai.key_root(1, yaw=-30)
    kai.arm("R", 1, 72, 45)
    kai.talk(1, F, base="smirk")
    kai.arm("L", 1, 0, 50)
    kai.look(1, 10, 5)
    place(S, [("Crowd1", (-252, -3500), 180 + 180, "shocked"), ("Crowd3", (-247, -3499), 180 + 160, "shocked")], marks=False)
    S.rain(F, (-249, -3504, 0), radius=10, n=450)
    S.cam(V((-248.5, -3503.5, 3.2)), dist=15, yaw=0, height=4.5, lens=32)
    return S


def circle(S, center, names, r=5.5, expr="angry"):
    out = {}
    for i, nm in enumerate(names):
        a = 2 * math.pi * i / len(names) + 0.4
        x, y = center[0] + math.cos(a) * r, center[1] + math.sin(a) * r
        # face the centre: forward = (sin yaw, -cos yaw) -> yaw = atan2(dx, -dy)
        yaw = math.degrees(math.atan2(center[0] - x, -(center[1] - y)))
        c = S.char(nm, (x, y), yaw, expr)
        out[nm] = c
    return out


CIRCLE = ["Kai", "Cousin", "Crowd1", "Crowd2", "Crowd3", "Crowd4", "Prey1", "Prey3"]


def s22(k, F):  # everyone circles
    S = rain_stage()
    n = S.char("Narrator", (-250, -3505), 180, "worried")
    n.mark("leaf")
    cs = circle(S, (-250, -3505), CIRCLE, r=8)
    for nm, c in cs.items():
        p = c.pos
        tgt = V((-250, -3505, 0)) + (p - V((-250, -3505, p.z))) * 0.7
        c.walk(1, F, (tgt.x, tgt.y))
    n.look(kf(16), 30, 0)
    S.rain(F, (-250, -3505, 0), radius=14, n=700, height=16)
    S.cam(V((-250, -3505, 1)), dist=16, yaw=180 + 20, height=16, lens=32)
    return S


def s23(k, F):  # "Show us," they said - kids point
    S = rain_stage()
    n = S.char("Narrator", (-250, -3505), 180, "worried")
    cs = circle(S, (-250, -3505), CIRCLE, r=5.6)
    for nm in ("Crowd1", "Crowd3", "Cousin"):
        cs[nm].point(1, "R")
        cs[nm].talk(1, F, base="angry")
    S.rain(F, (-250, -3505, 0), radius=10, n=500)
    c = cs["Crowd3"]
    tgt = c.head_pt() - V((0, 0, 1.2))
    back = (n.pos - tgt)
    back.z = 0
    back.normalize()
    S.cam_at(n.pos + back * 4.5 + V((0, 0, 7.8)), tgt, lens=32)
    return S


def s24(k, F):  # one crowd kid shouts
    S = rain_stage()
    cs = circle(S, (-250, -3505), CIRCLE, r=5.6)
    c = cs["Crowd2"]
    c.faces([(1, "angry")])
    c.talk(kf(10), F, base="angry")
    c.point(1, "R")
    c.lean(1, 8)
    S.rain(F, tuple(c.pos), radius=6, n=350)
    S.cam_at(c.world((0.8, 6.0, 4.4)), c.head_pt() - V((0, 0, 0.4)), lens=45)
    return S


def s25(k, F):  # Narrator holds wrist, it burns
    S = rain_stage()
    n = S.char("Narrator", (-250, -3505), 180, "worried")
    leaf = n.mark("leaf", glow=0.5)
    st = n.mark("streaks", lift=0.06, size=1.0, dz=0.45)
    S.glow(leaf, 1, 0.5)
    S.glow(leaf, F, 3.0)
    n.arm("L", 1, 42)
    n.arm("R", 1, 45, -22)
    n.look(1, 0, -20)
    n.faces([(1, "worried"), (kf(F * 0.5), "scared")])
    S.rain(F, (-250, -3505, 0), radius=6, n=350)
    S.cam(n.chest_pt() + V((0, 0, 0.2)), dist=9, yaw=180 + 20, height=n.chest_pt().z + 0.8, lens=38)
    return S


def leaf_insert(S, F, light_power=0, crown=False):
    n = S.char("Narrator", (-250, -3505), 180, "shocked")
    leaf = n.mark("leaf", glow=2)
    cr = n.mark("crown", glow=4, hidden=not crown, lift=0.05)
    n.arm("L", 1, 42)
    return n, leaf, cr


def s26(k, F):  # the leaf glows
    S = rain_stage()
    n, leaf, cr = leaf_insert(S, F)
    S.glow(leaf, 1, 2)
    S.glow(leaf, F, 9)
    w = n.wrist_pt("L")
    S.flash_light(tuple(n.world((-1.5, 2.0, 2.8))), 2, None, (0.5, 1, 0.5), 60)
    S.rain(F, tuple(w), radius=5, n=250)
    wrist_cam(S, n, side=-3.0, fwd=4.4, h=4.4, lens=36, mix=0.3)
    return S


def s27(k, F):  # cracks open like an egg -> crown
    S = rain_stage()
    n, leaf, cr = leaf_insert(S, F)
    fo = kf(F * 0.5)
    S.glow(leaf, 1, 6)
    S.show(leaf, fo, False)
    S.show(cr, fo, True)
    S.flash_light(tuple(n.world((-1.5, 2.2, 2.8))), fo, None, (1, 0.85, 0.4), 500)
    S.rain(F, tuple(n.wrist_pt("L")), radius=5, n=250)
    wrist_cam(S, n, side=-3.0, fwd=4.4, h=4.4, lens=36, mix=0.3)
    return S


def s28(k, F):  # a crown, glowing (rain easing, warmer)
    S = rain_stage("day")
    n, leaf, cr = leaf_insert(S, F, crown=True)
    S.show(leaf, 1, False)
    S.glow(cr, 1, 3)
    S.glow(cr, F, 6)
    S.flash_light(tuple(n.world((-1.5, 2.2, 2.8))), 1, None, (1, 0.85, 0.4), 300)
    wrist_cam(S, n, side=-3.2, fwd=4.8, h=4.6, lens=36, mix=0.4)
    return S


def s29(k, F):  # Kai lets go and steps back
    S = rblx.Stage("alpha-mark", "day")
    n, kai, leaf, mk = grab_pair(S, F, "shocked", "shocked")
    S.show(leaf, 1, False)
    S.show(mk, 1, False)
    n.mark("crown", glow=4, lift=0.05)
    kai.arm("R", kf(10), 20, 10)
    p = kai.pos
    kai.key_root(kf(10), (p.x, p.y))
    kai.key_root(kf(25), (p.x + 1.8, p.y - 0.8))
    kai.lean(kf(25), -10)
    S.cam(V((-248, -3506, 3.6)), dist=12, yaw=180 + 10, height=4.6, lens=36)
    return S


def s30(k, F):  # everyone steps back
    S = rblx.Stage("alpha-mark", "day")
    n = S.char("Narrator", (-250, -3505), 180, "shocked")
    n.mark("crown", glow=4)
    n.arm("L", 1, 42)
    cs = circle(S, (-250, -3505), CIRCLE, r=5.6, expr="shocked")
    for c in cs.values():
        p = c.pos
        out = (p - V((-250, -3505, p.z))).normalized() * 2.5
        c.key_root(1, (p.x, p.y))
        c.key_root(kf(16), (p.x + out.x, p.y + out.y))
        c.lean(kf(16), -12)
        c.arm("L", kf(16), 30, 20)
        c.arm("R", kf(16), 30, 20)
    S.cam(V((-250, -3505, 1)), dist=18, yaw=180 + 15, height=13, lens=32)
    return S


def s31(k, F):  # small kid whispers "Alpha"
    S = rblx.Stage("alpha-mark", "day")
    c = S.char("Smallkid", (-246, -3500), 180 - 30, "shocked")
    c.faces([(1, "shocked")])
    c.talk(kf(F * 0.4), F, base="shocked")
    c.arm("R", 1, 120, -20)
    c.look(1, 0, 15)
    S.cam(c.head_pt() - V((0, 0, 0.5)), dist=5.5, yaw=180 - 30, height=c.head_pt().z + 0.4, lens=45)
    return S


def s32(k, F):  # kids bow/cheer around the new king
    S = rblx.Stage("alpha-mark", "day")
    n = S.char("Narrator", (-250, -3510), 180, "embarrassed")
    n.mark("crown", glow=2)
    n.arm("R", 1, 0, 0, 0)
    n.look(1, 0, -5)
    cs = circle(S, (-250, -3510), ["Prey1", "Prey2", "Prey3", "Smallkid", "Crowd1", "Crowd2", "Crowd4"], r=5, expr="laugh")
    for i, (nm, c) in enumerate(cs.items()):
        f = 1
        k2 = 0
        while f <= F:
            if i % 2:
                c.lean(f, 35 if k2 % 2 == 0 else 15)
            else:
                up = 170 if k2 % 2 == 0 else 140
                c.arm("L", f, up, 10)
                c.arm("R", f, up, 10)
            f += 15
            k2 += 1
    S.cam(V((-250, -3510, 3)), dist=14, yaw=180, height=6.5, lens=32)
    return S


def mountain_stage(light="day"):
    S = rblx.Stage("alpha-mark", light)
    mountains(S)
    return S


def s33(k, F):  # class hikes up, bus parked
    S = mountain_stage("day")
    group = [("Kai", 251, -3490), ("Cousin", 253.2, -3489), ("Crowd2", 252, -3487), ("Narrator", 251.2, -3484.5),
             ("Prey1", 253.6, -3479.5), ("Smallkid", 251.4, -3477.5)]
    for nm, x, y in group:
        c = S.char(nm, (x, y), 45, "smile" if nm not in PREY else "sad")
        c.walk(1, F, (x, y - 4), swing=30 if nm not in PREY else 18)
        if nm in PREY:
            c.look(1, 0, -18)
    S.cam(V((248, -3480, 10)), dist=34, yaw=120, height=22, lens=30, fstop=None)
    return S


TRAIL = dict(Narrator=(252, -3512), Kai=(256.3, -3516), Cousin=(250, -3509), Prey1=(254, -3509),
             Crowd2=(251, -3515), Smallkid=(253.5, -3506))


def s34(k, F):  # ground starts to shake
    S = mountain_stage("dusty")
    cs = {nm: S.char(nm, xy, 180 + 70, "smile") for nm, xy in TRAIL.items()}
    for nm, c in cs.items():
        c.faces([(1, "smile"), (kf(F * 0.4), "shocked")])
        c.look(kf(F * 0.4), 30, 10)
        c.arm("L", kf(F * 0.4), 20, 25)
        c.arm("R", kf(F * 0.4), 20, 25)
    S.cam(V((253, -3511, S.ground(253, -3511) + 3)), dist=16, yaw=180 + 75, height=S.ground(253, -3511) + 6, lens=32)
    S.shake(kf(F * 0.4), F, 0.3)
    return S


def s35(k, F):  # boulders tumble down the slope
    S = mountain_stage("dusty")
    rnd = random.Random(4)
    for i, o in enumerate(o for o in bpy.data.objects if o.name.startswith("Boulder")):
        p0 = o.matrix_world.translation.copy()
        o.keyframe_insert("location", frame=1)
        o.keyframe_insert("rotation_euler", frame=1)
        dy = 14 + rnd.uniform(0, 10)
        o.location = o.location + V((rnd.uniform(-1, 1), dy, 0))
        o.location.z += S.ground(p0.x, p0.y + dy) - S.ground(p0.x, p0.y)
        o.rotation_euler = (R(rnd.uniform(200, 400)), R(rnd.uniform(-90, 90)), 0)
        o.keyframe_insert("location", frame=F)
        o.keyframe_insert("rotation_euler", frame=F)
    S.dust(F, (252, -3505, S.ground(252, -3505)), radius=7, n=22, color=(0.6, 0.48, 0.35))
    S.cam(V((252, -3518, S.ground(252, -3518))), dist=32, yaw=180 + 40, height=S.ground(252, -3500) + 16, lens=30, fstop=None)
    S.shake(1, F, 0.4)
    return S


def s36(k, F):  # everyone runs, except Kai
    S = mountain_stage("dusty")
    cs = {nm: S.char(nm, xy, 180, "shocked") for nm, xy in TRAIL.items()}
    for nm, c in cs.items():
        if nm == "Kai":
            c.face(1, "scared")
            c.key_root(1, yaw=180 + 160)
            c.arm("L", 1, 30, 20)
            c.arm("R", 1, 30, 20)
            continue
        p = c.pos
        c.key_root(1, yaw=180)
        c.run(1, F, (p.x - 1, p.y + 10))
    S.dust(F, (254, -3530, S.ground(254, -3530)), radius=6, n=14, color=(0.6, 0.48, 0.35))
    S.cam(V((254, -3509, S.ground(254, -3509) + 3)), dist=18, yaw=180 + 15, height=S.ground(254, -3509) + 6, lens=32)
    S.shake(1, F, 0.2)
    return S


def s37(k, F):  # Kai slips over the edge
    S = mountain_stage("dusty")
    kai = S.char("Kai", (258.2, -3519.5), 90 + 180, "shocked")  # facing -X (back to the drop)
    kai.mark("claw")
    g = S.ground(258.2, -3519.5)
    kai.key_root(1, (258.2, -3519.5, g))
    kai.key_root(kf(14), (260.8, -3519.5, g - 0.8), tilt=25)
    kai.key_root(kf(30), (263.0, -3519.5, g - 5), tilt=10)
    kai.arm("L", 1, 40, 30); kai.arm("R", 1, 40, 30)
    kai.arm("L", kf(14), 160, 20); kai.arm("R", kf(14), 160, 20)
    kai.faces([(1, "shocked"), (kf(14), "scared")])
    S.cam_at(V((272, -3512, g + 1.0)), V((260.5, -3519.5, g - 0.5)), lens=32)
    return S


def hang_kai(S, F, expr="scared"):
    g = S.ground(256.5, -3519.5)
    kai = S.char("Kai", (263.2, -3519.4, g - 7.2), 90, expr)
    kai.mark("claw")
    kai.arm("L", 1, 180, 4)
    kai.arm("R", 1, 180, 4)
    kai.look(1, 0, 10)
    return kai, g


def s38(k, F):  # grabs a root
    S = mountain_stage("dusty")
    kai, g = hang_kai(S, F)
    S.cam_at(V((271, -3517, g - 2.0)), V((262.8, -3519.4, g - 2.2)), lens=35)
    return S


def lie_narrator(S, g, expr="determined", crown_glow=6):
    n = S.char("Narrator", (258.8, -3519.6, g + 0.55), 90, expr)
    cr = n.mark("crown", glow=crown_glow)
    n.lie(1, face_down=True)
    n.arm("L", 1, 90)
    n.arm("R", 1, 90)
    n.look(1, 0, 40)
    return n, cr


def s39(k, F):  # crown burns brighter than ever
    S = mountain_stage("dusty")
    n = S.char("Narrator", (254.5, -3513.5), -90, "determined")
    cr = n.mark("crown", glow=4)
    S.glow(cr, 1, 4)
    S.glow(cr, F, 14)
    n.arm("L", 1, 30)
    n.arm("L", kf(12), 42)
    S.flash_light(tuple(n.world((-1.5, 2.0, 2.8))), 1, None, (1, 0.85, 0.4), 500)
    wrist_cam(S, n, side=-3.4, fwd=5.0, h=4.0, lens=34)
    return S


def s40(k, F):  # flat on the ground, grabs Kai's wrist
    S = mountain_stage("dusty")
    kai, g = hang_kai(S, F, "crying")
    n, cr = lie_narrator(S, g)
    S.flash_light((261, -3519.5, g + 1), 1, None, (1, 0.85, 0.4), 200)
    S.cam_at(V((272, -3516.5, g - 1.0)), V((262, -3519.5, g - 1.8)), lens=32)
    return S


def s41(k, F):  # and I pulled
    S = mountain_stage("dusty")
    kai, g = hang_kai(S, F, "crying")
    n, cr = lie_narrator(S, g)
    p = kai.pos
    kai.key_root(1, tuple(p))
    kai.key_root(kf(18), (p.x - 0.3, p.y, p.z + 3.2))
    n.key_root(kf(18), (257.6, -3519.6, g + 0.55))
    n.faces([(1, "determined"), (kf(10), "angry")])
    S.cam_at(V((271, -3514.5, g + 0.5)), V((261, -3519.5, g - 1.0)), lens=32)
    return S


def kai_sitting(S, expr="crying"):
    p = (254.5, -3517.5)
    g = S.ground(*p)
    kai = S.char("Kai", (p[0], p[1], g - 1.5), 180 + 95, expr)
    kai.sit(1)
    kai.arm("L", 1, 40, -10)
    kai.arm("R", 1, 40, -10)
    return kai, g


def s42(k, F):  # Kai sits safe, shaking
    S = mountain_stage("sunset")
    S.hide("Boulder")
    kai, g = kai_sitting(S)
    f, i = 1, 0
    while f <= F:
        kai.lean(f, 10 + (3 if i % 2 else -3), 2 if i % 2 else -2)
        f += 15
        i += 1
    S.cam(kai.head_pt() - V((0, 0, 1.0)), dist=7.5, yaw=180 + 95 + 20, height=kai.head_pt().z - 0.2, lens=40)
    return S


def s43(k, F):  # Kai looks up: "Why'd you save me?"
    S = mountain_stage("sunset")
    S.hide("Boulder")
    kai, g = kai_sitting(S, "sad")
    kai.look(1, 0, 25)
    kai.talk(kf(F * 0.4), F, base="sad")
    S.cam(kai.head_pt(), dist=6, yaw=180 + 95, height=kai.head_pt().z + 1.6, lens=45)
    return S


def s44(k, F):  # Narrator offers a hand
    S = mountain_stage("sunset")
    S.hide("Boulder")
    kai, g = kai_sitting(S, "sad")
    n = S.char("Narrator", (250.5, -3517.6), 180 - 85, "smile")
    n.mark("crown", glow=2)
    n.arm("L", 1, 10)
    n.arm("L", kf(12), 70, 5)
    n.look(1, 0, -20)
    n.talk(kf(12), F, base="smile")
    S.cam(V((252.5, -3517.5, g + 2.6)), dist=11, yaw=180, height=g + 4.2, lens=34)
    return S


def s45(k, F):  # helps Kai up, class gathers, sunset
    S = mountain_stage("sunset")
    S.hide("Boulder")
    g = S.ground(254.5, -3517.5)
    kai = S.char("Kai", (254.6, -3517.5), 180 + 95, "smile")
    n = S.char("Narrator", (252.0, -3517.6), 180 - 85, "laugh")
    n.mark("crown", glow=2)
    kai.mark("claw")
    n.arm("L", 1, 70)
    kai.arm("R", 1, 70)
    for i, nm in enumerate(["Cousin", "Prey1", "Crowd2", "Smallkid"]):
        x, y = 249 + i * 1.8, -3510.5 + (i % 2) * 1.2
        c = S.char(nm, (x, y), 180 + 10, "laugh" if i % 2 else "smile")
        c.walk(1, kf(30), (x + 0.5, y - 2.5))
        c.key_root(kf(30), yaw=180 + 20)
    S.cam(V((253.3, -3516, g + 2.5)), dist=16, yaw=10, height=g + 5, lens=32)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 46)}
