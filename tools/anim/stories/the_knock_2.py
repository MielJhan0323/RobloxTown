"""the-knock-2 ("The Knock", Part 2) - viewers chose: don't open any door, charge the phone, call Mom.
Both doors were Knockers; Mom keeps him company on the phone all night; ends on handprints on the inside.

Reuses the_knock's hallway + porch; adds a kitchen (outlet, window) and a dark restaurant (candle) built here.
"""
import math

import bpy
from mathutils import Vector

import kit
import rblx
from rblx import attach, kf
from stories.nothing_happens import lamps_on, text
from stories.the_knock import HALL, P, door, hall, knocker, knocks, narrator_in_hall, parents, phone, porch, rattle, stage
from stories.five_seconds import car

R = math.radians
V = Vector
PACK = "alpha-mark"
KIT = V((-1100.0, -3505.0, 0))      # kitchen centre; window on the far wall (y + 8), outlet low on the left wall
REST = V((-1000.0, -3505.0, 0))     # restaurant


# ---------------------------------------------------------------- sets
def kitchen(S, clock_time="9:14", morning=False, prints=False):
    x, y = KIT.x, KIT.y
    wall = kit.mat("kwall", (0.75, 0.8, 0.88) if morning else (0.4, 0.44, 0.55), rough=0.9)
    kit.box((16, 18, 0.3), (x, y, -0.15), kit.mat("ktile", (0.8, 0.8, 0.78), rough=0.5), 0)
    for wx in (-8.3, 8.3):
        kit.box((0.6, 18, 12), (x + wx, y, 6), wall, 0)
    for bx, bw in ((x - 5.4, 5.8), (x + 5.4, 5.8)):                 # far wall around a window hole (x-2.5..x+2.5)
        kit.box((bw, 0.6, 12), (bx, y + 8.3, 6), wall, 0)
    kit.box((5.0, 0.6, 4.8), (x, y + 8.3, 2.4), wall, 0)
    kit.box((5.0, 0.6, 3.2), (x, y + 8.3, 10.4), wall, 0)
    kit.box((16.6, 0.6, 12), (x, y - 9.3, 6), wall, 0)
    kit.box((16.6, 18, 0.4), (x, y, 12.2), kit.mat("kceil", (0.85, 0.85, 0.85)), 0)
    # counters + cabinets along the far wall, with a window above the sink
    kit.box((16, 2.6, 3.4), (x, y + 6.8, 1.7), kit.mat("kcab", (0.92, 0.92, 0.9)), 0.04)
    kit.box((16.2, 2.8, 0.3), (x, y + 6.8, 3.5), kit.mat("ktop", (0.3, 0.3, 0.34)), 0.02)
    sky = (0.85, 0.75, 0.55) if morning else (0.1, 0.13, 0.28)
    kit.box((40, 0.2, 30), (x, y + 18, 8), kit.mat("kwin", sky, emit=0.35 if morning else 0.6, emit_color=sky), 0)
    kit.box((40, 12, 0.3), (x, y + 12, -0.15), kit.mat("kyard", (0.2, 0.4, 0.2) if morning else (0.05, 0.1, 0.08)), 0)
    kit.box((5.4, 0.4, 0.3), (x, y + 7.9, 4.8), kit.mat("ksill", (0.95, 0.95, 0.95)), 0)
    kit.box((0.2, 0.42, 4), (x, y + 7.9, 6.8), kit.mat("ksill", (0.95, 0.95, 0.95)), 0)
    glass = kit.box((5, 0.08, 4), (x, y + 7.7, 6.8), kit.mat("kglass", (0.7, 0.8, 1.0), rough=0.05, alpha=0.15), 0)
    if prints:   # handprints on the INSIDE of the glass
        img = bpy.data.images.load(str(rblx.ROOT / "output" / "models" / PACK / "decals" / "handprints.png"), check_existing=True)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y + 7.6, 6.8), rotation=(R(90), 0, 0))
        hp = bpy.context.active_object
        hp.scale = (4.2, 3.4, 1)
        m = bpy.data.materials.new("prints")
        m.use_nodes = True
        m.blend_method = "HASHED"
        nt = m.node_tree
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = img
        b = nt.nodes["Principled BSDF"]
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
        hp.data.materials.append(m)
    kit.box((3.2, 2.6, 7.6), (x + 6, y + 6.6, 3.8), kit.mat("kfridge", (0.92, 0.94, 0.96), rough=0.3), 0.08)
    # outlet low on the left wall
    kit.box((0.1, 0.7, 1.0), (x - 7.95, y + 2.0, 1.2), kit.mat("outlet", (0.95, 0.95, 0.92)), 0.02)
    kit.box((3.6, 0.3, 1.5), (x - 4.5, y + 8.0, 9.6), kit.mat("clockb", (0.08, 0.08, 0.1)), 0.06)
    text(clock_time, (x - 4.5, y + 7.8, 9.15), size=0.95, color=(1, 0.25, 0.2), emit=6)
    if morning:
        kit.spot((x, y + 20, 9), (x, y, 0), (1, 0.85, 0.6), 3500, 40, 0.6, 0.6)
        kit.point((x, y - 3, 9), (1, 0.92, 0.8), 150, 3)
    else:
        kit.spot((x, y + 20, 10), (x, y, 0), (0.45, 0.55, 1.0), 3500, 35, 0.6, 0.4)
        kit.point((x, y - 5, 6), (0.6, 0.65, 1.0), 170, 2.0)
    return glass


def kid_at_outlet(S, expr="scared", yaw=90):
    n = S.char("Narrator", (KIT.x - 6.4, KIT.y + 2.0, -1.4), yaw, expr)
    n.sit(1)
    return n


def cable(n):
    a = n.world((1.5, 0.6, 1.3))
    b = V((KIT.x - 7.9, KIT.y + 2.0, 1.2))
    L = (b - a)
    c = kit.cyl(0.05, L.length, tuple(a + L / 2), kit.mat("cable", (0.95, 0.95, 0.95)), verts=6)
    c.rotation_euler = L.to_track_quat("Z", "Y").to_euler()


def phone_text(c, label, color=(1, 0.2, 0.2)):
    ph = phone(c)
    t = text(label, tuple(ph.matrix_world.translation + V((0, -0.2, 0.25))), size=0.3, color=color, emit=6)
    attach(t, c.arms["R"])
    return ph, t


def restaurant(S):
    x, y = REST.x, REST.y
    kit.box((30, 30, 0.3), (x, y, -0.15), kit.mat("rfloor", (0.25, 0.15, 0.1)), 0)
    kit.box((30, 0.6, 12), (x, y + 8, 6), kit.mat("rwall", (0.35, 0.18, 0.15), rough=0.9), 0)
    kit.box((6, 4, 0.3), (x, y + 1.5, 2.8), kit.mat("rtable", (0.95, 0.95, 0.92)), 0.03)
    for dx in (-2.5, 2.5):
        kit.box((0.3, 0.3, 2.8), (x + dx, y + 1.5, 1.4), kit.mat("rleg", (0.2, 0.2, 0.22)), 0)
    kit.cyl(0.25, 0.9, (x, y + 1.5, 3.4), kit.mat("candle", (1, 0.97, 0.9)), verts=10)
    kit.sphere(0.15, (x, y + 1.5, 4.0), kit.mat("flame", (1, 0.7, 0.2), emit=25, emit_color=(1, 0.7, 0.2)), seg=8)
    kit.point((x, y + 1.5, 4.3), (1, 0.65, 0.3), 250, 0.2)
    for k2 in range(3):
        kit.box((1.6, 0.1, 2.4), (x - 9 + k2 * 9, y + 7.6, 7), kit.mat("rframe", (0.7, 0.55, 0.3)), 0.03)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.3


def mom_dad_table(S, talking=True):
    mom = S.char("Crowd1", (REST.x - 1.6, REST.y - 1.0, -0.6), 0, "worried")
    dad = S.char("Cousin", (REST.x + 1.8, REST.y - 1.0, -0.6), 0, "worried")
    for c in (mom, dad):
        c.root.scale = (1.18, 1.18, 1.18)
        c.sit(1)
    ph = phone(mom)
    mom.arm("R", 1, 150, -30)   # phone to her ear
    if talking:
        mom.talk(3, 400, base="worried")
    return mom, dad


# ---------------------------------------------------------------- shots
def s01(k, F):  # You told me not to open either door.
    S = stage("night")
    hall(S)
    n = narrator_in_hall(S, (0, 1.0), 0, "worried")
    n.key_root(1, (HALL.x, HALL.y + 1.0))
    n.key_root(F, (HALL.x, HALL.y - 2.5))
    S.cam(V((HALL.x, HALL.y, 3.5)), dist=11, yaw=0, height=6, lens=28)
    return S


def s02(k, F):  # So I didn't.
    S = stage("night")
    hall(S)
    n = narrator_in_hall(S, (0, -2.5), 0, "determined")
    for j, f in enumerate(range(1, F + 2, 5)):
        n.look(f, 18 if j % 2 else -18, 0)
    S.cam(n.head_pt() - V((0, 0, 1.4)), dist=8, yaw=0, height=n.head_pt().z - 0.5, lens=32)
    return S


def s03(k, F):  # I crawled to the kitchen and plugged in my phone.
    S = stage("night")
    kitchen(S)
    n = S.char("Narrator", (KIT.x + 2, KIT.y - 4, -1.4), -50, "scared")
    n.lean(1, 50)
    n.key_root(1, (KIT.x + 2, KIT.y - 4, -1.4))
    n.key_root(kf(F * 0.7), (KIT.x - 5.6, KIT.y + 1.5, -1.4), yaw=90)
    for j, f in enumerate(range(1, kf(F * 0.7), 6)):
        n.arm("L", f, 60 if j % 2 else 100)
        n.arm("R", f, 100 if j % 2 else 60)
    S.cam_at(V((KIT.x + 6, KIT.y - 7.5, 6)), V((KIT.x - 2, KIT.y, 1.5)), lens=26)
    return S


def s04(k, F):  # Three percent. Four.
    S = stage("night")
    kitchen(S)
    n = kid_at_outlet(S)
    n.arm("R", 1, 75, -10)
    cable(n)
    ph, t3 = phone_text(n, "3%")
    t4 = text("4%", tuple(t3.location), size=0.3, color=(1, 0.5, 0.2), emit=6)
    t4.rotation_euler = t3.rotation_euler
    t4.parent, t4.matrix_parent_inverse = t3.parent, t3.matrix_parent_inverse.copy()
    S.show(t3, kf(F * 0.5), False)
    S.show(t4, 1, False)
    S.show(t4, kf(F * 0.5), True)
    S.cam_at(n.world((0.5, 3.2, 3.0)), n.world((0.9, 1.0, 2.0)), lens=34, allow_close=True)
    return S


def s05(k, F):  # The knocking got louder. Both doors at once.
    S = stage("night")
    fd, bd = hall(S)
    rattle(fd, 1, F, amp=3.5)
    rattle(bd, 2, F, amp=3.0, every=3)
    S.cam(V((HALL.x, HALL.y + 3, 4)), dist=10, yaw=0, height=6, lens=24)
    S.shake(1, F, 0.08)
    return S


def s06(k, F):  # Five percent. I called Mom.
    S = stage("night")
    kitchen(S)
    n = kid_at_outlet(S, "determined")
    n.arm("R", 1, 75, -10)
    cable(n)
    ph, t = phone_text(n, "5%  CALLING MOM", color=(0.5, 1, 0.6))
    S.cam_at(n.world((0.5, 3.2, 3.0)), n.world((0.9, 1.0, 2.0)), lens=34, allow_close=True)
    return S


def s07(k, F):  # It rang. And rang.
    S = stage("night")
    kitchen(S)
    n = kid_at_outlet(S, "scared")
    phone(n)
    n.arm("R", 1, 150, -30)
    cable(n)
    S.cam_at(V((KIT.x + 1.5, KIT.y - 2.5, 4.4)), n.head_pt() - V((0, 0, 1.2)), lens=30)
    return S


def s08(k, F):  # "Bug? Honey, the lights went out at the restaurant."
    S = stage("night")
    restaurant(S)
    mom, dad = mom_dad_table(S)
    S.cam(V((REST.x, REST.y - 1, 4.2)), dist=11, yaw=0, height=5.2, lens=30)
    return S


def s09(k, F):  # "Dad and I are stuck here till morning. Are you inside? Is the door locked?"
    S = stage("night")
    restaurant(S)
    mom, dad = mom_dad_table(S)
    S.cam(mom.head_pt() - V((0, 0, 1.6)), dist=8, yaw=-20, height=mom.head_pt().z - 0.6, lens=32)
    return S


def s10(k, F):  # I looked at the front door.
    S = stage("night")
    hall(S)
    S.drone([(1, (HALL.x - 1, HALL.y - 3, 5), (HALL.x - 6, HALL.y + 4, 4)), (F, (HALL.x - 2.5, HALL.y + 0.5, 4.5), (HALL.x - 6, HALL.y + 4, 4))],
            lens=30, allow_close=True)
    return S


def s11(k, F):  # Then the back door.
    S = stage("night")
    hall(S)
    S.drone([(1, (HALL.x + 1, HALL.y - 3, 5), (HALL.x + 6, HALL.y + 4, 4)), (F, (HALL.x + 2.5, HALL.y + 0.5, 4.5), (HALL.x + 6, HALL.y + 4, 4))],
            lens=30, allow_close=True)
    return S


def s12(k, F):  # If Mom and Dad were at the restaurant...
    S = stage("night")
    kitchen(S)
    n = kid_at_outlet(S, "worried", yaw=60)
    phone(n)
    n.arm("R", 1, 150, -30)
    n.faces([(1, "worried"), (kf(F * 0.6), "shocked")])
    S.cam_at(V((KIT.x + 1.0, KIT.y - 1.5, 4.4)), n.head_pt() - V((0, 0, 1.0)), lens=32)
    return S


def s13(k, F):  # then who was outside?  (two Knockers, one at each door of the house)
    S = stage("night")
    porch(S, lit=False)
    knocker((P.x + 0.4, P.y + 2.4, 0.5), yaw=180, height=8.5, name="kfront")
    knocker((P.x + 11.5, P.y + 6.5, 0), yaw=-90, height=8.5, name="kback")
    S.drone([(1, (P.x - 4, P.y - 22, 6), (P.x + 3, P.y + 3, 4)), (F, (P.x - 12, P.y - 14, 14), (P.x + 4, P.y + 3, 3))], lens=26)
    return S


def s14(k, F):  # Both doors went silent.
    S = stage("night")
    hall(S)
    S.drone([(1, (HALL.x, HALL.y - 8, 5)), (F, (HALL.x, HALL.y - 3, 5))][0:0] or
            [(1, (HALL.x, HALL.y - 8, 5), (HALL.x, HALL.y + 4, 4)), (F, (HALL.x, HALL.y - 3, 5), (HALL.x, HALL.y + 4, 4))], lens=26)
    return S


def window_knocker(S, F, eyes_on=1):
    kn, eyes = knocker((KIT.x + 0.3, KIT.y + 10.0, -2.0), yaw=0, height=10, name="kwin")
    kit.spot((KIT.x, KIT.y + 18, 9), (KIT.x, KIT.y + 9, 6), (0.45, 0.55, 1.0), 2500, 30, 0.6, 0.3)
    return kn


def s15(k, F):  # Then something knocked on the kitchen window.
    S = stage("night")
    glass = kitchen(S)
    window_knocker(S, F)
    for f in (kf(4), kf(4) + 5, kf(4) + 10):
        kit.key(glass, f, loc=tuple(glass.location))
        kit.key(glass, f + 1, loc=tuple(glass.location + V((0, -0.06, 0))))
        kit.key(glass, f + 3, loc=tuple(glass.location))
    S.cam_at(V((KIT.x - 2, KIT.y - 2, 5.2)), V((KIT.x, KIT.y + 8, 6.8)), lens=30)
    return S


def s16(k, F):  # Right next to me.
    S = stage("night")
    kitchen(S)
    window_knocker(S, F)
    n = S.char("Narrator", (KIT.x - 1.5, KIT.y + 4.6, -1.4), 180 + 20, "shocked")
    n.sit(1)
    S.cam(V((KIT.x - 1, KIT.y + 5, 3.5)), dist=8, yaw=20, height=4.2, lens=28)
    return S


def s17(k, F):  # "Bug," it said, in Mom's voice. "Who are you talking to?"
    S = stage("night")
    kitchen(S)
    kn = window_knocker(S, F)
    kit.key(kn, 1, loc=tuple(kn.location))
    kit.key(kn, F, loc=tuple(kn.location - V((0, 0.8, 0))))
    S.cam_at(V((KIT.x, KIT.y + 3.5, 6.4)), V((KIT.x + 0.3, KIT.y + 9.3, 6.6)), lens=34, allow_close=True)
    return S


def s18(k, F):  # I didn't answer. I didn't breathe.
    S = stage("night")
    kitchen(S)
    n = S.char("Narrator", (KIT.x - 1.5, KIT.y + 4.6, -1.4), 180 + 20, "scared")
    n.sit(1)
    n.arm("L", 1, 150, -40)       # hand over mouth
    S.cam(n.head_pt() - V((0, 0, 1.0)), dist=6.5, yaw=20, height=n.head_pt().z, lens=36)
    return S


def s19(k, F):  # I held the phone against my chest.
    S = stage("night")
    kitchen(S)
    n = S.char("Narrator", (KIT.x - 1.5, KIT.y + 4.6, -1.4), 180 + 20, "sad")
    n.sit(1)
    ph = phone(n)
    n.arm("R", 1, 120, -60)
    n.arm("L", 1, 110, -60)
    kit.point(tuple(n.chest_pt() + n.world((0, 1.0, 0)) - n.pos), (0.5, 0.7, 1.0), 25, 0.2)
    S.cam(n.chest_pt(), dist=7, yaw=20, height=n.chest_pt().z + 0.8, lens=34)
    return S


def s20(k, F):  # Mom stayed on the line all night.
    S = stage("night")
    kitchen(S, clock_time="2:13")
    n = S.char("Narrator", (KIT.x - 1.5, KIT.y + 4.6, -1.4), 180 + 20, "tired")
    n.sit(1)
    phone(n)
    n.arm("R", 1, 150, -30)
    S.cam(V((KIT.x - 2, KIT.y + 4, 4)), dist=12, yaw=10, height=6.5, lens=28)
    return S


def s21(k, F):  # She told me stories. She hummed.
    S = stage("night")
    kitchen(S, clock_time="3:40")
    n = S.char("Narrator", (KIT.x - 1.5, KIT.y + 4.6, -1.4), 180 + 20, "smile_blink")
    n.sit(1)
    phone(n)
    n.arm("R", 1, 150, -30)
    from stories.closet_monster import notes
    notes(tuple(n.head_pt() + n.world((0.8, 0.4, 0)) - n.pos), F)
    S.cam(n.head_pt() - V((0, 0, 1.0)), dist=7, yaw=20, height=n.head_pt().z, lens=34)
    return S


def s22(k, F):  # Every time something knocked, she said, "Don't answer, bug. I'm right here."
    S = stage("night")
    glass = kitchen(S, clock_time="4:52")
    window_knocker(S, F)
    n = S.char("Narrator", (KIT.x - 1.5, KIT.y + 4.6, -1.4), 180 + 20, "neutral")
    n.sit(1)
    phone(n)
    n.arm("R", 1, 150, -30)
    for f in (kf(3), kf(3) + 6):
        kit.key(glass, f, loc=tuple(glass.location))
        kit.key(glass, f + 1, loc=tuple(glass.location + V((0, -0.05, 0))))
        kit.key(glass, f + 3, loc=tuple(glass.location))
    S.cam(V((KIT.x - 1, KIT.y + 5, 4)), dist=10, yaw=25, height=5.5, lens=28)
    return S


def s23(k, F):  # At six a.m., the streetlights flickered back on.
    S = rblx.Stage(PACK, "dusk")
    lamps_on(S, 3, gap=max(2, F // 9), near=(0, -3580, 0))
    S.cam_at(V((0, -3585, 4.5)), V((0, -3520, 5)), lens=26, fstop=None)
    return S


def s24(k, F):  # The knocking stopped.
    S = rblx.Stage(PACK, "morning")
    hall(S)
    kit.spot((HALL.x, HALL.y + 20, 9), (HALL.x, HALL.y, 0), (1, 0.85, 0.6), 9000, 40, 0.6, 0.6)
    S.drone([(1, (HALL.x, HALL.y - 9, 5), (HALL.x, HALL.y + 4, 4)), (F, (HALL.x, HALL.y - 5, 5), (HALL.x, HALL.y + 4, 4))], lens=26)
    return S


def s25(k, F):  # At seven, Mom and Dad pulled into the driveway.
    S = rblx.Stage(PACK, "morning")
    porch(S, lit=False)
    cr = car((P.x - 14, P.y - 30, 0), color=(0.85, 0.85, 0.88), yaw=0)
    kit.key(cr, 1, loc=(P.x - 14, P.y - 34, 0))
    kit.key(cr, kf(F * 0.8), loc=(P.x - 14, P.y - 12, 0))
    S.cam_at(V((P.x + 8, P.y - 26, 5)), V((P.x - 6, P.y - 10, 2.5)), lens=26, fstop=None)
    return S


def s26(k, F):  # Before I opened the door, I made Mom say one thing a Knocker couldn't have heard today.
    S = rblx.Stage(PACK, "morning")
    hall(S)
    kit.spot((HALL.x, HALL.y + 20, 9), (HALL.x, HALL.y, 0), (1, 0.85, 0.6), 9000, 40, 0.6, 0.6)
    n = narrator_in_hall(S, (-3.4, 4.0), -90, "determined")
    n.arm("R", 1, 85)
    n.talk(kf(6), F, base="determined")
    S.cam_at(V((HALL.x + 1.5, HALL.y - 1, 5.4)), n.head_pt() - V((0, 0, 1.0)), lens=30)
    return S


def s27(k, F):  # She smiled. "I love you more than the whole sky."
    S = rblx.Stage(PACK, "morning")
    porch(S, lit=False)
    mom, dad = parents(S, (P.x - 1.6, P.y - 0.6), (P.x + 2.4, P.y - 0.9), 0, 0, "smile")
    mom.talk(kf(F * 0.3), F, base="smile")
    S.cam(mom.head_pt() - V((0, 0, 1.6)), dist=9, yaw=-15, height=mom.head_pt().z - 0.6, lens=32)
    return S


def s28(k, F):  # She says it every morning. Never at night.
    S = rblx.Stage(PACK, "morning")
    hall(S)
    kit.spot((HALL.x, HALL.y + 20, 9), (HALL.x, HALL.y, 0), (1, 0.85, 0.6), 9000, 40, 0.6, 0.6)
    n = narrator_in_hall(S, (-3.4, 4.0), -90, "smile")
    S.cam_at(V((HALL.x + 1.5, HALL.y - 1, 5.4)), n.head_pt() - V((0, 0, 1.0)), lens=30)
    return S


def s29(k, F):  # I opened the door.  (outside view: door opens, he runs into a hug)
    S = rblx.Stage(PACK, "morning")
    porch(S, lit=False)
    mom, dad = parents(S, (P.x - 1.2, P.y - 1.2), (P.x + 2.8, P.y - 1.4), 0, -10, "laugh")
    n = S.char("Narrator", (P.x, P.y + 3.0), 0, "laugh")
    n.walk(kf(F * 0.3), kf(F * 0.7), (P.x - 0.2, P.y + 0.3))
    for c in (mom, n):
        c.arm("L", kf(F * 0.7), 80, 25)
        c.arm("R", kf(F * 0.7), 80, 25)
    S.allow_close = {("Crowd1", "Narrator"), ("Narrator", "Crowd1")}
    S.cam_at(V((P.x + 4, P.y - 12, 4.5)), V((P.x, P.y + 1, 3.6)), lens=30)
    return S


def s30(k, F):  # But the kitchen window still has handprints.
    S = rblx.Stage(PACK, "morning")
    kitchen(S, clock_time="7:12", morning=True, prints=True)
    S.cam_at(V((KIT.x - 2.5, KIT.y - 1, 5.2)), V((KIT.x, KIT.y + 8, 6.8)), lens=30)
    return S


def s31(k, F):  # On the inside.  (push in until the prints fill the frame, cut)
    S = rblx.Stage(PACK, "morning")
    kitchen(S, clock_time="7:12", morning=True, prints=True)
    S.drone([(1, (KIT.x, KIT.y + 3, 6.6), (KIT.x, KIT.y + 8, 6.8)), (F, (KIT.x, KIT.y + 5.6, 6.8), (KIT.x, KIT.y + 8, 6.8))],
            lens=32, allow_close=True)
    return S


# ---------------------------------------------------------------- Part 2 v2 (4-part series): cliffhanger ending
ST = V((-900.0, -3505.0, 0))   # staircase set: steps climb toward +Y into a dark landing


def staircase(S, eyes=False):
    x, y = ST.x, ST.y
    wall = kit.mat("stwall", (0.5, 0.52, 0.6), rough=0.9)
    kit.box((12, 40, 0.3), (x, y + 4, -0.15), kit.mat("stfloor", (0.35, 0.24, 0.16)), 0)
    for wx in (-3.6, 3.6):
        kit.box((0.5, 40, 22), (x + wx, y + 4, 11), wall, 0)
    kit.box((8, 0.5, 22), (x, y + 19, 11), wall, 0)
    kit.box((8, 40, 0.4), (x, y + 4, 21.5), kit.mat("stceil", (0.5, 0.5, 0.55)), 0)
    step = kit.mat("ststep", (0.55, 0.38, 0.24), rough=0.7)
    for k2 in range(14):
        kit.box((6.6, 1.2, 0.8), (x, y + 1 + k2 * 1.0, 0.4 + k2 * 0.8), step, 0.02)
        kit.box((6.6, 0.95 * (14 - k2), 0.8), (x, y + 1 + k2 * 1.0 + 0.95 * (14 - k2) / 2, 0.4 + k2 * 0.8), step, 0)
    kit.box((6.6, 4, 0.4), (x, y + 15.5, 11.5), step, 0)                                     # landing
    rail = kit.mat("strail", (0.92, 0.92, 0.9))
    L = V((0, 14, 11.2))
    r = kit.cyl(0.12, L.length, (x - 3.0, y + 1 + 7, 3.0 + 5.6), rail, verts=8)
    r.rotation_euler = L.to_track_quat("Z", "Y").to_euler()
    kit.box((1.6, 0.3, 1.0), (x + 2.0, y + 18.6, 15.5), kit.mat("stframe", (0.7, 0.55, 0.3)), 0.03)    # picture up top
    kit.spot((x, y - 6, 8), (x, y + 6, 4), (0.75, 0.75, 0.85), 2500, 45, 0.6, 0.6)           # gray dawn from below
    kit.point((x, y + 15, 14), (0.25, 0.28, 0.4), 15, 1.0)                                     # landing stays dark
    if eyes:
        for sx in (-0.3, 0.3):
            kit.sphere(0.13, (x + 0.6 + sx, y + 15.5, 18.2), kit.mat("knockeye", (1, 1, 0.95), emit=25,
                                                                      emit_color=(1, 1, 0.9)), seg=10)


def v2_whisper(k, F):  # Mom whispered, "Don't answer, bug. I'm right here."
    S = stage("night")
    restaurant(S)
    mom, dad = mom_dad_table(S)
    mom.lean(1, 12)
    S.cam(mom.head_pt() - V((0, 0, 1.4)), dist=8, yaw=30, height=mom.head_pt().z - 0.4, lens=34)
    return S


def v2_allnight(k, F):  # She stayed on the line all night.
    S = stage("night")
    kitchen(S, clock_time="2:13")
    n = S.char("Narrator", (KIT.x - 1.5, KIT.y + 4.6, -1.4), 180 + 20, "tired")
    n.sit(1)
    phone(n)
    n.arm("R", 1, 150, -30)
    from stories.closet_monster import notes
    notes(tuple(n.head_pt() + n.world((0.8, 0.4, 0)) - n.pos), F)
    S.cam(V((KIT.x - 2, KIT.y + 4, 4)), dist=12, yaw=10, height=6.5, lens=28)
    return S


def v2_quiet(k, F):  # The knocking stopped. The house was quiet. Too quiet.
    S = stage("dusk")
    hall(S, clock_time="6:00")
    S.drone([(1, (HALL.x, HALL.y - 9, 5), (HALL.x, HALL.y + 4, 4)), (F, (HALL.x, HALL.y - 4, 5), (HALL.x, HALL.y + 4, 4))], lens=26)
    return S


def v2_prints(k, F):  # On the kitchen window, there were handprints. Three of them.
    S = stage("dusk")
    kitchen(S, clock_time="6:04", morning=True, prints=True)
    S.cam_at(V((KIT.x - 2.5, KIT.y - 1, 5.2)), V((KIT.x, KIT.y + 8, 6.8)), lens=30)
    return S


def v2_touch(k, F):  # I touched the glass. They didn't smear.
    S = stage("dusk")
    kitchen(S, clock_time="6:04", morning=True, prints=True)
    n = S.char("Narrator", (KIT.x - 0.4, KIT.y + 5.3), 180, "worried")
    n.arm("R", 1, 40)
    n.arm("R", kf(F * 0.4), 105, -10)
    S.cam_at(V((KIT.x + 3.0, KIT.y + 2.0, 6.2)), V((KIT.x, KIT.y + 7.6, 6.6)), lens=30)
    return S


def v2_inside(k, F):  # They were on the inside.
    S = stage("dusk")
    kitchen(S, clock_time="6:04", morning=True, prints=True)
    S.drone([(1, (KIT.x, KIT.y + 3, 6.6), (KIT.x, KIT.y + 8, 6.8)), (F, (KIT.x, KIT.y + 5.6, 6.8), (KIT.x, KIT.y + 8, 6.8))],
            lens=32, allow_close=True)
    return S


def v2_upstairs(k, F):  # Then, from upstairs, in Mom's voice:
    S = stage("dusk")
    staircase(S)
    n = S.char("Narrator", (ST.x, ST.y - 2.5), 180, "scared")
    n.look(1, 0, 0)
    n.look(kf(F * 0.4), 0, 35)
    S.cam(V((ST.x, ST.y - 2.5, 3.5)), dist=9, yaw=0, height=4.5, lens=30)
    return S


def v2_comeup(k, F):  # "Bug? Come up here. I want to show you something."
    S = stage("dusk")
    staircase(S, eyes=True)
    S.char("Narrator", (ST.x, ST.y - 2.5), 180, "scared")
    S.drone([(1, (ST.x + 2.6, ST.y - 6, 4.0), (ST.x, ST.y + 14, 15)), (F, (ST.x + 2.2, ST.y - 1.5, 2.4), (ST.x + 0.6, ST.y + 15.5, 17.0))],
            lens=24, allow_close=True)
    return S


def v2_stillon(k, F):  # Mom was still on the phone.
    S = stage("dusk")
    staircase(S)
    n = S.char("Narrator", (ST.x, ST.y - 2.5), 0, "shocked")
    n.arm("R", 1, 75, -10)
    ph = phone(n)
    t = text("MOM  9:14:52", tuple(ph.matrix_world.translation + V((0, -0.2, 0.25))), size=0.22, color=(0.5, 1, 0.6), emit=6)
    attach(t, n.arms["R"])
    S.drone([(1, n.world((0.5, 3.2, 3.5)), n.world((0.9, 1.0, 2.6))), (F, n.world((0.3, 5.5, 4.6)), n.head_pt() - V((0, 0, 1.0)))],
            lens=34, allow_close=True)
    return S


ORDER = [
    (s01, "You told me not to open either door."), (s02, "So I didn't."),
    (s03, "I crawled to the kitchen and plugged in my phone."), (s04, "Three percent. Four."),
    (s05, "The knocking got louder. Both doors at once."), (s06, "Five percent. I called Mom."), (s07, "It rang. And rang."),
    (s08, "\"Bug? Honey, the lights went out at the restaurant."), (s09, "Dad and I are stuck here till morning. Are you inside? Is the door locked?\""),
    (s10, "I looked at the front door."), (s11, "Then the back door."), (s12, "If Mom and Dad were at the restaurant..."),
    (s13, "then who was outside?"), (s14, "Both doors went silent."), (s15, "Then something knocked on the kitchen window."),
    (s16, "Right next to me."), (s17, "\"Bug,\" it said, in Mom's voice. \"Who are you talking to?\""),
    (s18, "I didn't answer."), (s19, "I held the phone against my chest."), (v2_whisper, "Mom whispered, \"Don't answer, bug. I'm right here.\""),
    (v2_allnight, "She stayed on the line all night."), (s23, "At six, the streetlights flickered back on."),
    (v2_quiet, "The knocking stopped. The house was quiet. Too quiet."), (v2_prints, "On the kitchen window, there were handprints. Three of them."),
    (v2_touch, "I touched the glass. They didn't smear."), (v2_inside, "They were on the inside."),
    (v2_upstairs, "Then, from upstairs, in Mom's voice:"), (v2_comeup, "\"Bug? Come up here. I want to show you something.\""),
    (v2_stillon, "Mom was still on the phone."),
]
SHOTS = {i + 1: f for i, (f, _) in enumerate(ORDER)}
LINES = [t for _, t in ORDER]
