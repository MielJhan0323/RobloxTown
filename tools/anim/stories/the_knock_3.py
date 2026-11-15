"""the-knock-3 ("The Knock", Part 3 - Final). Viewers' write-in pick: the streetlights are back on, so run outside.
Twist: the figure in his window waves like him... and Dad, home from the restaurant, says "Hey, kiddo."

Sets: hallway + porch (the_knock), staircase (the_knock_2), and the Parkers' house across the street (built here:
facade with door + a front window, a small living room behind it so the camera can look out at our house).
"""
import math

import bpy
from mathutils import Vector

import kit
import rblx
from rblx import attach, kf
from stories.five_seconds import car
from stories.nothing_happens import lamps_on, text
from stories.the_knock import HALL, P, hall, knocker, narrator_in_hall, parents, porch, rattle, stage
from stories.the_knock_2 import ST, phone_insert, staircase

R = math.radians
V = Vector
PACK = "alpha-mark"
PK = V((P.x, P.y - 36.0, 0))      # Parkers' house, facade at y = PK.y - 4.5... faces +Y (toward our house)
UPWIN = V((P.x + 8.0, P.y + 3.6, 12.5))   # our upstairs bedroom window


# ---------------------------------------------------------------- sets
def morning():
    S = rblx.Stage(PACK, "morning")
    return S


def our_house(S, figure=False, curtain_open=0.0, wave=None):
    """Porch facade + an upstairs bedroom window (curtain, optional hoodie figure)."""
    porch(S, lit=False)
    x, y, z = UPWIN
    kit.box((4.6, 0.4, 4.1), (x, y + 0.35, z), kit.mat("ptrim", (0.95, 0.95, 0.95)), 0.02)
    kit.box((4.0, 0.1, 3.5), (x, y + 0.22, z), kit.mat("roominside", (0.05, 0.05, 0.07)), 0)
    if figure:
        hood = kit.mat("hoodie", (0.45, 0.47, 0.5), rough=0.8)
        dark = kit.mat("figface", (0.02, 0.02, 0.03))
        root = kit.empty((x + 0.3, y + 0.15, z - 1.75), name="figure")
        parts = [kit.box((1.8, 0.12, 2.2), (x + 0.3, y + 0.15, z - 0.9), hood, 0.1),
                 kit.box((1.3, 0.12, 1.3), (x + 0.3, y + 0.13, z + 0.85), hood, 0.15),
                 kit.box((0.9, 0.08, 0.9), (x + 0.3, y + 0.08, z + 0.8), dark, 0.05)]
        for sx in (-0.18, 0.18):
            parts.append(kit.sphere(0.07, (x + 0.3 + sx, y + 0.02, z + 0.88), kit.mat("knockeye", (1, 1, 0.95), emit=20,
                                                                                       emit_color=(1, 1, 0.9)), seg=8))
        for o in parts:
            attach(o, root)
        arm_piv = kit.empty((x + 1.25, y + 0.14, z + 0.1), name="figarm")
        arm = kit.box((0.4, 0.1, 1.5), (x + 1.25, y + 0.14, z - 0.5), hood, 0.08)
        attach(arm, arm_piv)
        if wave:
            f0, f1 = wave
            kit.key(arm_piv, 1, rot=(0, 0, 0))
            kit.key(arm_piv, f0, rot=(0, -160, 0))
            for j, f in enumerate(range(f0, f1 + 1, 10)):
                kit.key(arm_piv, f, rot=(0, -160 + (20 if j % 2 else -20), 0))
    cur = kit.mat("bedcurtain", (0.35, 0.45, 0.75), rough=0.9)
    for side in (-1, 1):
        c = kit.box((2.0, 0.1, 3.5), (x + side * 1.0, y + 0.05, z), cur, 0.03)
        if curtain_open:
            f0, f1 = curtain_open
            kit.key(c, 1, loc=(x + side * 1.0, y + 0.05, z))
            kit.key(c, f0, loc=(x + side * 1.0, y + 0.05, z))
            kit.key(c, f1, loc=(x + side * 1.0 + (1.3 if side > 0 else 0.0), y + 0.05, z), scale=(0.35 if side > 0 else 1, 1, 1))
        elif figure:
            c.location.x += 1.3 if side > 0 else 0.0
            c.scale = (0.35 if side > 0 else 1, 1, 1)
    # street + far sidewalk
    kit.box((90, 14, 0.15), (P.x, P.y - 22, 0.0), kit.mat("asphalt", (0.12, 0.12, 0.13), rough=0.9), 0)
    for k2 in range(8):
        kit.box((3, 0.4, 0.05), (P.x - 35 + k2 * 10, P.y - 22, 0.1), kit.mat("roadline", (0.95, 0.85, 0.3)), 0)


def parkers(S, inside=False):
    """Parkers' house across the street: facade faces +Y at y = PK.y + 4, door + front window, living room behind."""
    x, y = PK.x, PK.y + 4.0
    wall = kit.mat("pkwall", (0.95, 0.78, 0.45), rough=0.9)
    trim = kit.mat("pktrim", (0.98, 0.98, 0.98))
    # facade with a window hole (x+4..x+10, z 3..8) and a door at x-4
    for bx, bw in ((x - 8.5, 13), (x + 12.5, 5)):
        kit.box((bw, 0.8, 14), (bx, y, 7), wall, 0)
    kit.box((6, 0.8, 3), (x + 7, y, 1.5), wall, 0)
    kit.box((6, 0.8, 6), (x + 7, y, 11), wall, 0)
    kit.box((6.4, 0.9, 0.3), (x + 7, y, 3.0), trim, 0)
    kit.box((4.2, 0.9, 7.6), (x - 4, y, 3.8), kit.mat("pkdoor", (0.25, 0.45, 0.35)), 0.04)
    kit.box((14, 6, 0.4), (x - 2, y + 3, 0.2), kit.mat("pkwalk", (0.7, 0.68, 0.65)), 0.02)
    kit.box((40, 14, 0.4), (x, y + 10, -0.2), kit.mat("pklawn", (0.25, 0.55, 0.22), rough=0.9), 0)
    # the rest of the house: sides, back and a roof
    for sx in (-15.2, 15.2):
        kit.box((0.8, 14, 14), (x + sx, y - 7, 7), wall, 0)
    kit.box((31, 0.8, 14), (x, y - 14, 7), wall, 0)
    roof = kit.mat("pkroof", (0.35, 0.25, 0.22), rough=0.8)
    for sy in (-1, 1):
        r = kit.box((32, 9.5, 0.6), (x, y - 7 + sy * 3.6, 16.6), roof, 0.03)
        r.rotation_euler = (R(sy * 30), 0, 0)
    for wx in (-12, 12.5):
        kit.box((3.5, 0.9, 3), (x + wx, y + 0.05, 9), kit.mat("pkwin2", (0.5, 0.65, 0.85)), 0.02)
    if inside:   # living room behind the window (the camera stands in here)
        kit.box((20, 12, 0.3), (x + 3, y - 6, -0.15), kit.mat("pkfloor", (0.5, 0.35, 0.22)), 0)
        kit.box((20, 0.5, 14), (x + 3, y - 12, 7), wall, 0)
        kit.box((0.5, 12, 14), (x + 13, y - 6, 7), wall, 0)
        kit.box((0.5, 12, 14), (x - 7, y - 6, 7), wall, 0)
        kit.box((20, 12, 0.4), (x + 3, y - 6, 14), trim, 0)
        kit.point((x + 3, y - 6, 10), (1, 0.92, 0.8), 150, 3.0)


# ---------------------------------------------------------------- shots
def s01(k, F):  # You picked the option I didn't even think of.
    S = stage("dusk")
    hall(S, clock_time="6:01")
    n = narrator_in_hall(S, (0, 1.0), 0, "worried")
    n.look(1, 30, 0)
    n.look(kf(F * 0.5), -30, 0)
    S.cam(V((HALL.x, HALL.y + 2, 3.5)), dist=11, yaw=0, height=6, lens=28)
    return S


def s02(k, F):  # The streetlights were back on.
    S = rblx.Stage(PACK, "dusk")
    lamps_on(S)
    S.cam_at(V((0, -3585, 4.5)), V((0, -3520, 5)), lens=26, fstop=None)
    return S


def s03(k, F):  # Knockers only come in the dark.
    S = stage("night")
    staircase(S, eyes=True)
    S.drone([(1, (ST.x + 2.4, ST.y - 4, 3.0), (ST.x + 0.6, ST.y + 15.5, 17)), (F, (ST.x + 2.2, ST.y - 1.5, 2.6), (ST.x + 0.6, ST.y + 15.5, 17.5))],
            lens=24, allow_close=True)
    return S


def s04(k, F):  # So I ran.
    S = stage("dusk")
    hall(S, clock_time="6:01")
    n = narrator_in_hall(S, (0, 6), 0, "determined")
    n.run(1, F, (HALL.x, HALL.y - 4))
    S.cam(V((HALL.x, HALL.y, 3.5)), dist=11, yaw=0, height=5, lens=28)
    return S


def s05(k, F):  # Down the hall.  (drone chases him)
    S = stage("dusk")
    hall(S, clock_time="6:01")
    n = narrator_in_hall(S, (0, 6), 0, "scared")
    n.run(1, F, (HALL.x - 2, HALL.y - 6))
    S.drone([(1, (HALL.x + 1, HALL.y + 10, 6), (HALL.x, HALL.y + 4, 3.5)), (F, (HALL.x - 0.5, HALL.y - 1, 6), (HALL.x - 2, HALL.y - 6, 3.5))],
            lens=26, allow_close=True)
    return S


def s06(k, F):  # Past the stairs. I didn't look up.
    S = stage("night")
    staircase(S, eyes=True)
    n = S.char("Narrator", (ST.x - 3.0, ST.y - 2.0), 90, "scared")
    n.run(1, F, (ST.x + 3.0, ST.y - 2.0))
    n.look(1, 0, -20)
    S.cam(V((ST.x, ST.y - 2, 3.5)), dist=10, yaw=0, height=5, lens=26)
    return S


def s07(k, F):  # I threw open the front door, and the morning hit my face.
    S = stage("dusk")
    fd, bd = hall(S, clock_time="6:02")
    n = narrator_in_hall(S, (-3.6, 4.0), -90, "determined")
    n.arm("R", 1, 85)
    op = kf(F * 0.35)
    kit.key(fd, 1, rot=(0, 0, 0))
    kit.key(fd, op, rot=(0, 0, 0))
    kit.key(fd, op + 6, rot=(0, 0, 100))
    L = kit.point((HALL.x - 8.5, HALL.y + 4, 5), (1, 0.85, 0.55), 0, 3.0)
    L.data.keyframe_insert("energy", frame=op)
    L.data.energy = 9000
    L.data.keyframe_insert("energy", frame=op + 6)
    n.faces([(1, "determined"), (op + 6, "shocked")])
    S.cam_at(V((HALL.x + 2.0, HALL.y - 1.5, 5.4)), V((HALL.x - 5.5, HALL.y + 4.0, 4.2)), lens=28)
    return S


def s08(k, F):  # (morning hit my face - outside: he bursts out onto the porch)
    S = morning()
    our_house(S)
    n = S.char("Narrator", (P.x, P.y + 2.6), 0, "shocked")
    n.run(1, F, (P.x - 1, P.y - 8))
    S.cam_at(V((P.x + 6, P.y - 16, 4.5)), V((P.x, P.y, 3.5)), lens=28)
    return S


def mrs_parker(S, xy, yaw, expr="neutral"):
    c = S.char("Crowd4", xy, yaw, expr)
    c.root.scale = (1.18, 1.18, 1.18)
    return c


def s09(k, F):  # Mrs. Parker was getting her newspaper.
    S = morning()
    parkers(S)
    mp = mrs_parker(S, (PK.x - 4, PK.y + 8), 0, "smile")
    paper = kit.box((1.2, 0.3, 0.8), tuple(mp.world((1.5, 0.6, 1.9))), kit.mat("newspaper", (0.92, 0.92, 0.88)), 0.05)
    attach(paper, mp.arms["R"])
    mp.arm("R", 1, 40)
    mp.lean(1, 20)
    mp.lean(kf(F * 0.6), 0)
    S.cam_at(V((PK.x + 4, PK.y + 26, 5)), V((PK.x - 3, PK.y + 6, 3.5)), lens=24)
    return S


def s10(k, F):  # She saw my face and didn't ask a single question.
    S = morning()
    parkers(S)
    mp = mrs_parker(S, (PK.x - 4, PK.y + 8), 180, "shocked")
    S.cam(mp.head_pt() - V((0, 0, 1.6)), dist=8, yaw=180, height=mp.head_pt().z - 0.6, lens=32)
    return S


def s11(k, F):  # She just pulled me inside.
    S = morning()
    parkers(S)
    mp = mrs_parker(S, (PK.x - 4, PK.y + 6.5), 180, "worried")
    n = S.char("Narrator", (PK.x - 1.5, PK.y + 9), 160, "scared")
    mp.arm("R", 1, 80, -20)
    for c in (mp, n):
        p = c.pos
        c.walk(kf(F * 0.3), F, (PK.x - 4, PK.y + 4.6))
    S.allow_close = {("Crowd4", "Narrator"), ("Narrator", "Crowd4")}
    S.cam_at(V((PK.x + 6, PK.y + 26, 5)), V((PK.x - 3, PK.y + 6, 3.5)), lens=24)
    return S


def s12(k, F):  # Mom was still on the phone.
    S = morning()
    parkers(S, inside=True)
    loc = (PK.x + 3, PK.y + 1.0, 4.6)
    phone_insert(S, [(1, "MOM", (0.5, 1, 0.6))], loc, sub="CALL  9:31:07")
    S.cam_at(V((loc[0], loc[1] - 7.0, loc[2])), V(loc), lens=34, fstop=2.0, allow_close=True)
    return S


def s13(k, F):  # "Stay there, bug. We're five minutes away."  (car speeding down the street)
    S = rblx.Stage(PACK, "morning")
    cr = car((-4, -3540, 0), color=(0.85, 0.85, 0.88), yaw=0)
    kit.key(cr, 1, loc=(-4, -3560, 0))
    kit.key(cr, F, loc=(-4, -3520, 0))
    S.drone([(1, V((1, -3576, 4.5)), V((-4, -3556, 1.4))),
             (F, V((0, -3542, 5.5)), V((-4, -3518, 1.4)))], lens=30, fstop=None)   # chase drone behind the car
    return S


def window_view(S, **kw):
    our_house(S, **kw)
    parkers(S, inside=True)


def s14(k, F):  # From the Parkers' window, I could see my house.
    S = morning()
    window_view(S)
    n = S.char("Narrator", (PK.x + 7, PK.y + 2.5), 180, "worried")
    S.cam_at(V((PK.x + 6, PK.y - 4, 6)), V((P.x + 2, P.y, 8)), lens=26)
    return S


def s15(k, F):  # My bedroom curtain moved.
    S = morning()
    window_view(S, curtain_open=(kf(F * 0.3), kf(F * 0.8)))
    S.cam_at(V((PK.x + 7, PK.y + 3, 6)), V(UPWIN), lens=70, fstop=None)
    return S


def s16(k, F):  # Something was standing in my window.
    S = morning()
    window_view(S, figure=True)
    S.cam_at(V((PK.x + 7, PK.y + 3, 6)), V(UPWIN), lens=80, fstop=None)
    return S


def s17(k, F):  # Wearing my hoodie.
    S = morning()
    window_view(S, figure=True)
    S.drone([(1, (PK.x + 7, PK.y + 3, 6), V(UPWIN)), (F, (PK.x + 7.4, PK.y + 6, 6.5), V(UPWIN) + V((0.3, 0, 0.4)))], lens=85)
    return S


def s18(k, F):  # It lifted its hand and waved. Slowly.
    S = morning()
    window_view(S, figure=True, wave=(kf(F * 0.2), F))
    S.cam_at(V((PK.x + 7, PK.y + 3, 6)), V(UPWIN), lens=90, fstop=None)
    return S


def s19(k, F):  # The same way I wave.
    S = morning()
    parkers(S, inside=True)
    n = S.char("Narrator", (PK.x + 7, PK.y + 2.5), 180, "scared")
    n.arm("R", 1, 0)
    n.arm("R", kf(F * 0.4), 160, -10)
    S.cam_at(V((PK.x + 7.5, PK.y + 6.8, 5.5)), n.head_pt() - V((0, 0, 1.2)), lens=30, allow_close=True)
    return S


def s20(k, F):  # Then Mom and Dad's car pulled into the driveway.
    S = morning()
    our_house(S)
    cr = car((P.x - 14, P.y - 30, 0), color=(0.85, 0.85, 0.88), yaw=0)
    kit.key(cr, 1, loc=(P.x - 14, P.y - 34, 0))
    kit.key(cr, kf(F * 0.8), loc=(P.x - 14, P.y - 12, 0))
    S.cam_at(V((P.x + 8, P.y - 26, 5)), V((P.x - 6, P.y - 10, 2.5)), lens=26, fstop=None)
    return S


def s21(k, F):  # I ran across the street faster than I've ever run.
    S = morning()
    our_house(S)
    n = S.char("Narrator", (P.x - 2, P.y - 30), 180, "determined")
    n.run(1, F, (P.x - 6, P.y - 12))
    S.drone([(1, (P.x + 6, P.y - 34, 4), (P.x - 2, P.y - 28, 3)), (F, (P.x + 4, P.y - 20, 4), (P.x - 6, P.y - 12, 3))], lens=28)
    return S


def family(S, expr_m="laugh", expr_d="smile", lifted=False):
    car((P.x - 14, P.y - 12, 0), color=(0.85, 0.85, 0.88), yaw=0)
    mom, dad = parents(S, (P.x - 7.5, P.y - 9), (P.x - 3.0, P.y - 9.5), -20, 20, expr_m)
    S.hide("Sunglass")   # Dad's sunglasses would cover his eyes
    dad.face(1, expr_d)
    n = S.char("Narrator", (P.x - 5.5, P.y - 11.5), 0, "smile")
    S.allow_close = {("Crowd1", "Narrator"), ("Narrator", "Crowd1"), ("Cousin", "Narrator"), ("Narrator", "Cousin")}
    return mom, dad, n


def s22(k, F):  # Mom hugged me so hard my feet left the ground.
    S = morning()
    our_house(S)
    mom, dad, n = family(S)
    n.key_root(1, (P.x - 6.6, P.y - 10.4))
    n.key_root(kf(F * 0.4), (P.x - 6.6, P.y - 10.4, 1.4))
    for c in (mom, n):
        c.arm("L", 1, 80, 25)
        c.arm("R", 1, 80, 25)
    n.face(1, "laugh")
    S.cam_at(V((P.x - 2, P.y - 20, 4.5)), V((P.x - 6.5, P.y - 9.5, 4)), lens=30)
    return S


def s23(k, F):  # "Bug, you're okay. You're okay."
    S = morning()
    our_house(S)
    mom, dad, n = family(S, "crying")
    mom.talk(3, F, base="crying")
    S.cam(mom.head_pt() - V((0, 0, 1.4)), dist=8, yaw=-20, height=mom.head_pt().z - 0.5, lens=32)
    return S


def s24(k, F):  # Dad knelt down and messed up my hair. He smiled at me.
    S = morning()
    our_house(S)
    mom, dad, n = family(S)
    p = dad.pos
    dad.key_root(1, (p.x, p.y, p.z))
    dad.key_root(kf(F * 0.3), (p.x - 0.6, p.y - 1.0, p.z - 1.6))
    dad.lean(kf(F * 0.3), 20)
    dad.arm("R", kf(F * 0.45), 150, 30)
    for j, f in enumerate(range(kf(F * 0.45), F + 2, 5)):
        dad.arm("R", f, 150, 30 + (10 if j % 2 else -10))
    S.cam_at(V((P.x + 0.5, P.y - 18, 4.5)), V((P.x - 4.5, P.y - 10.5, 3.2)), lens=30)
    return S


def kneeling_dad(S, expr="smile"):
    our_house(S)
    mom, dad, n = family(S, "smile", expr)
    p = dad.pos
    dad.key_root(1, (p.x - 0.6, p.y - 1.0, p.z - 1.6))
    dad.lean(1, 20)
    return mom, dad, n


def s25(k, F):  # "Hey, kiddo."
    S = morning()
    mom, dad, n = kneeling_dad(S)
    dad.talk(kf(F * 0.2), kf(F * 0.7), base="smile")
    S.cam(dad.head_pt() - V((0, 0, 1.2)), dist=6.5, yaw=10, height=dad.head_pt().z - 0.3, lens=36)
    return S


def s26(k, F):  # I looked at Mom. She didn't notice.
    S = morning()
    mom, dad, n = kneeling_dad(S)
    n.look(1, 0, 0)
    n.look(kf(F * 0.3), -45, 5)
    n.face(kf(F * 0.3), "worried")
    S.cam_at(V((P.x - 4, P.y - 18, 4.5)), V((P.x - 6, P.y - 10.5, 3.6)), lens=30)
    return S


def s27(k, F):  # Last night, something knocked on our back door and said, "Something followed us."
    S = stage("night")
    fd, bd = hall(S, clock_time="9:02")
    from stories.the_knock import knocks
    knocks(bd, [kf(4), kf(4) + 8], amp=0.6)
    S.drone([(1, (HALL.x + 1.0, HALL.y + 1.0, 4), (HALL.x + 6, HALL.y + 4, 3.5)), (F, (HALL.x + 3.0, HALL.y + 2.8, 3.8), (HALL.x + 6, HALL.y + 4, 3.5))],
            lens=32, allow_close=True)
    return S


def dad_eyes(S, dad, f_on):
    """Tiny glowing glints on Dad's pupils - the Knocker is inside him. Placed on the head's front face."""
    h = dad.head
    bb = [V(c) for c in h.bound_box]
    lo = V((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = V((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    w, ht = hi.x - lo.x, hi.y - lo.y          # OBJ import: local x = width, y = height, z = depth (face at z min)
    out = []
    for sx in (-0.105, 0.105):
        local = V(((lo.x + hi.x) / 2 + sx * w, hi.y - 0.32 * ht, lo.z - 0.03))
        e = kit.sphere(0.05, (0, 0, 0), kit.mat("dadglint", (1, 0.95, 0.8), emit=14, emit_color=(1, 0.9, 0.7)), seg=8)
        e.parent = h
        e.location = local
        S.show(e, 1, False)
        S.show(e, f_on, True)
        out.append(e)
    return out


def s28(k, F):  # It wasn't lying.
    S = morning()
    mom, dad, n = kneeling_dad(S)
    dad_eyes(S, dad, kf(F * 0.5))
    S.drone([(1, dad.head_pt() + dad.world((0, 7, -0.6)) - dad.pos, dad.head_pt() - V((0, 0, 0.8))),
             (F, dad.head_pt() + dad.world((0, 5.2, -0.4)) - dad.pos, dad.head_pt() - V((0, 0, 0.6)))], lens=34)
    return S


def s29(k, F):  # Dad never calls me kiddo.
    S = morning()
    mom, dad, n = kneeling_dad(S)
    dad_eyes(S, dad, 1)
    dad.look(1, 0, 0)
    S.drone([(1, dad.head_pt() + dad.world((0, 5.2, -0.4)) - dad.pos, dad.head_pt() - V((0, 0, 0.6))),
             (F, dad.head_pt() + dad.world((0, 4.0, -0.2)) - dad.pos, dad.head_pt() - V((0, 0, 0.4)))], lens=34, allow_close=True)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 30)}
