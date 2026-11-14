"""the-knock ("The Knock", Part 1) - kid-safe horror cliffhanger: when the streetlights go out, never open the door.

Sets: A = exported town street at night (lamps switch off); P = front porch built here (facade, door, porch light,
bushes); HALL = dark entry hallway built here (front door on the left wall, back door on the right wall, window +
clock on the far wall). The Knocker: a tall shadow figure with two glowing eyes - never shown up close.
Parents: Crowd1 (mom) and Cousin (dad), scaled up a little.
"""
import math
import random

import bpy
from mathutils import Vector

import kit
import rblx
from rblx import attach, kf
from stories.nothing_happens import text

R = math.radians
V = Vector
PACK = "alpha-mark"
P = V((-1300.0, -3505.0, 0))      # porch: house facade along y = P.y + 4, door at x = P.x
HALL = V((-1200.0, -3505.0, 0))   # hallway centre; front door on x = HALL.x - 6, back door on x = HALL.x + 6


# ---------------------------------------------------------------- props
def door(loc, normal_x, color=(0.45, 0.28, 0.18), name="door", light_leak=None):
    """Door in a wall at x = loc.x facing normal_x (+1/-1). Returns the hinge empty (rotate z to open/rattle)."""
    x, y = loc[0], loc[1]
    wood = kit.mat(name + "_w", color, rough=0.6)
    frame = kit.mat("dframe", (0.92, 0.92, 0.9))
    kit.box((0.35, 4.6, 0.4), (x, y, 8.2), frame, 0.03)
    for dy in (-2.15, 2.15):
        kit.box((0.35, 0.3, 8.2), (x, y + dy, 4.1), frame, 0.03)
    hinge = kit.empty((x, y - 2.0, 4.0), name=name + "_hinge")
    d = kit.box((0.25, 4.0, 7.9), (x, y, 3.95), wood, 0.04)
    for dz in (2.2, 5.6):
        kit.box((0.06, 3.0, 2.6), (x + normal_x * 0.14, y, dz), kit.mat(name + "_p", tuple(c * 0.8 for c in color)), 0.03)
    knob = kit.sphere(0.17, (x + normal_x * 0.25, y + 1.5, 3.8), kit.mat("knob", (0.85, 0.7, 0.3), metal=0.8), seg=10)
    chain = kit.box((0.05, 1.1, 0.06), (x + normal_x * 0.2, y + 1.3, 5.6), kit.mat("chain", (0.7, 0.7, 0.72), metal=0.8), 0)
    for o in (d, knob, chain):
        attach(o, hinge)
    if light_leak:
        kit.box((0.08, 3.6, 0.08), (x + normal_x * 0.05, y, 0.05), kit.mat(name + "_leak", light_leak, emit=6,
                                                                          emit_color=light_leak), 0)
    return hinge


def rattle(hinge, f0, f1, amp=2.5, every=2):
    for j, f in enumerate(range(f0, f1 + 1, every)):
        hinge.rotation_euler = (0, 0, R(amp if j % 2 else -amp * 0.4))
        hinge.keyframe_insert("rotation_euler", frame=f)
    hinge.rotation_euler = (0, 0, 0)
    hinge.keyframe_insert("rotation_euler", frame=f1 + every)


def knocks(hinge, frames_at, amp=1.2):
    for f in frames_at:
        for dt, a in ((0, 0), (1, amp), (3, 0)):
            hinge.rotation_euler = (0, 0, R(a))
            hinge.keyframe_insert("rotation_euler", frame=f + dt)


def knocker(loc, yaw=0, height=9.0, name="knocker"):
    """Tall shadow figure: dark stretched body, long arms, two glowing eyes. Returns (root, eyes)."""
    root = kit.empty(loc, name=name)
    black = kit.mat("shadowbody", (0.01, 0.01, 0.015), rough=1.0)
    x, y, z = loc
    h = height
    parts = [kit.box((1.4, 0.9, h * 0.55), (x, y, z + h * 0.45), black, 0.3),
             kit.sphere(0.8, (x, y, z + h * 0.82), black, scale=(1, 1, 1.25), seg=14)]
    for sx in (-1, 1):
        a = kit.box((0.35, 0.35, h * 0.55), (x + sx * 0.95, y, z + h * 0.42), black, 0.15)
        a.rotation_euler = (0, R(sx * 6), 0)
        parts.append(a)
        parts.append(kit.box((0.4, 0.4, h * 0.4), (x + sx * 0.4, y, z + h * 0.15), black, 0.1))
    eyes = []
    for sx in (-0.28, 0.28):
        e = kit.sphere(0.13, (x + sx, y - 0.72, z + h * 0.84), kit.mat("knockeye", (1, 1, 0.95), emit=25,
                                                                         emit_color=(1, 1, 0.9)), seg=10)
        parts.append(e)
        eyes.append(e)
    for o in parts:
        attach(o, root)
    root.rotation_euler = (0, 0, R(yaw))
    return root, eyes


def phone(c, pct="2%"):
    loc = c.world((1.5, 0.6, c.meta["shoulder"] - c.meta["arm_len"] + 0.1))
    body = kit.box((0.75, 0.12, 1.35), tuple(loc), kit.mat("phone", (0.08, 0.08, 0.1)), 0.06)
    scr = kit.box((0.62, 0.02, 1.15), tuple(loc + c.world((0, 0.08, 0)) - c.pos), kit.mat("screen", (0.15, 0.2, 0.3),
                                                                                           emit=1.5, emit_color=(0.3, 0.45, 0.7)), 0)
    for o in (body, scr):
        o.rotation_euler = (0, 0, c.root.rotation_euler.z - math.pi)
        attach(o, c.arms["R"])
    return body


def lamps_off(S, f0, gap=0):
    """Every street lamp bulb lit, then switching off one by one from f0 (with a flicker)."""
    bulbs = sorted((o for o in bpy.data.objects if o.name.startswith("Lampbulb")), key=lambda o: o.matrix_world.translation.y)
    for k2, o in enumerate(bulbs):
        m = kit.mat("bulboff%d" % k2, (1, 0.9, 0.6), emit=0.0001, emit_color=(1, 0.85, 0.5))
        o.data.materials.clear()
        o.data.materials.append(m)
        sock = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        off = f0 + k2 * gap
        for f, v in ((1, 12), (off, 12), (off + 2, 1), (off + 3, 12), (off + 5, 0)):
            sock.default_value = v
            sock.keyframe_insert("default_value", frame=f)
        L = kit.point(tuple(o.matrix_world.translation - V((0, 0, 0.6))), (1, 0.85, 0.55), 600, 1.0)
        for f, v in ((1, 600), (off + 4, 600), (off + 5, 0)):
            L.data.energy = v
            L.data.keyframe_insert("energy", frame=f)


def lamps_dark():
    for o in bpy.data.objects:
        if o.name.startswith("Lampbulb"):
            o.data.materials.clear()
            o.data.materials.append(kit.mat("bulbdead", (0.2, 0.2, 0.22)))


# ---------------------------------------------------------------- sets
def stage(light="night"):
    S = rblx.Stage(PACK, light)
    if light == "night":
        bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    return S


def porch(S, lit=True, dusk=False):
    x, y = P.x, P.y
    wall = kit.mat("facade", (0.62, 0.7, 0.85), rough=0.9)
    trim = kit.mat("ptrim", (0.95, 0.95, 0.95))
    kit.box((90, 60, 0.4), (x, y - 10, -0.2), kit.mat("lawn", (0.2, 0.45, 0.2), rough=0.9), 0)
    kit.box((26, 1.0, 16), (x, y + 4.5, 8), wall, 0)                        # house front
    for wx in (-8, 8):
        kit.box((4, 0.3, 3.5), (x + wx, y + 3.9, 6), kit.mat("pwin", (1, 0.85, 0.5) if lit else (0.1, 0.12, 0.2),
                                                              emit=2 if lit else 0, emit_color=(1, 0.85, 0.5)), 0)
        kit.box((4.6, 0.4, 4.1), (x + wx, y + 4.0, 6), trim, 0.02)
    kit.box((4.6, 0.4, 8.4), (x, y + 3.95, 4.2), trim, 0.03)                 # front door (facing -Y)
    kit.box((4.0, 0.3, 7.9), (x, y + 3.85, 3.95), kit.mat("pdoor", (0.45, 0.28, 0.18)), 0.04)
    kit.sphere(0.17, (x + 1.5, y + 3.6, 3.8), kit.mat("knob", (0.85, 0.7, 0.3), metal=0.8), seg=10)
    kit.box((14, 6, 0.5), (x, y + 1.2, 0.25), kit.mat("porchfloor", (0.6, 0.42, 0.28)), 0.03)
    for k2 in range(3):
        kit.box((5, 1.2, 0.25), (x, y - 2.4 - k2 * 1.2, 0.25 - k2 * 0.08), kit.mat("step", (0.7, 0.68, 0.65)), 0.02)
    for px in (-6.5, 6.5):
        kit.box((0.5, 0.5, 9), (x + px, y - 1.5, 4.5), trim, 0.03)
    kit.box((14.5, 6.4, 0.5), (x, y + 1.1, 9.2), kit.mat("roofp", (0.4, 0.22, 0.18)), 0.03)
    lamp = kit.sphere(0.4, (x + 3.2, y + 3.7, 7.0), kit.mat("plamp", (1, 0.9, 0.6), emit=8 if lit else 0.5,
                                                             emit_color=(1, 0.85, 0.5)), seg=10)
    if lit:
        kit.point((x + 3.2, y + 2.8, 7.0), (1, 0.8, 0.5), 500, 1.0)
    bush = kit.mat("bush", (0.12, 0.35, 0.15), rough=0.9)
    for bx in (-10.5, -8.5, 9.0, 11.0):
        kit.sphere(1.6, (x + bx, y + 2.5, 1.2), bush, scale=(1, 1, 0.8), seg=12)
    return lamp


def hall(S, clock_time="9:01", window_glow=False):
    """Dark entry hallway. Front door on the left wall (x - 6), back door on the right wall (x + 6)."""
    x, y = HALL.x, HALL.y
    wall = kit.mat("hallwall", (0.42, 0.45, 0.55), rough=0.9)
    kit.box((14, 26, 0.3), (x, y, -0.15), kit.mat("hallfloor", (0.35, 0.24, 0.16), rough=0.7), 0)
    kit.box((0.6, 26, 12), (x - 6.3, y, 6), wall, 0)
    kit.box((0.6, 26, 12), (x + 6.3, y, 6), wall, 0)
    kit.box((13.2, 0.6, 12), (x, y + 12.3, 6), wall, 0)
    kit.box((13.2, 0.6, 12), (x, y - 12.3, 6), wall, 0)
    kit.box((13.2, 26, 0.4), (x, y, 12.2), kit.mat("hallceil", (0.6, 0.6, 0.62)), 0)
    kit.box((4.5, 9, 0.04), (x, y, 0.02), kit.mat("runner", (0.45, 0.12, 0.15), rough=0.95), 0)   # rug
    fd = door((x - 6.0, y + 4.0), 1, name="front", light_leak=(0.55, 0.65, 1.0))
    bd = door((x + 6.0, y + 4.0), -1, color=(0.3, 0.32, 0.36), name="back", light_leak=(0.3, 0.35, 0.5))
    text("FRONT", (x - 5.8, y + 4.0, 9.0), rot=(90, 0, 90), size=0.45, color=(0.9, 0.9, 0.9))
    text("BACK", (x + 5.8, y + 4.0, 9.0), rot=(90, 0, -90), size=0.45, color=(0.9, 0.9, 0.9))
    # far wall: window (moonlight) + clock
    kit.box((4, 0.3, 4), (x, y + 12.0, 6.5), kit.mat("hwin", (0.2, 0.3, 0.6), emit=1.2, emit_color=(0.35, 0.45, 0.9)), 0)
    kit.box((0.2, 0.32, 4), (x, y + 11.95, 6.5), kit.mat("hwinf", (0.9, 0.9, 0.9)), 0)
    kit.box((3.6, 0.3, 1.5), (x + 4.0, y + 12.0, 9.5), kit.mat("clockb", (0.08, 0.08, 0.1)), 0.06)
    text(clock_time, (x + 4.0, y + 11.8, 9.05), size=0.95, color=(1, 0.25, 0.2), emit=6)
    kit.spot((x, y + 20, 10), (x, y, 0), (0.45, 0.55, 1.0), 4000, 35, 0.6, 0.4)          # moonlight through window
    kit.point((x, y - 4, 10), (0.5, 0.55, 0.9), 70, 3.0)                                   # cold fill
    kit.point((x, y - 5, 5.5), (0.6, 0.65, 1.0), 160, 2.0)                                # face fill (still spooky blue)
    return fd, bd


def narrator_in_hall(S, xy=(0, 0), yaw=180, expr="scared"):
    return S.char("Narrator", (HALL.x + xy[0], HALL.y + xy[1]), yaw, expr)


# ---------------------------------------------------------------- shots
def s01(k, F):  # In this town, when the streetlights go out,
    S = stage("night")
    lamps_off(S, kf(F * 0.3), gap=3)
    S.drone([(1, (0, -3585, 14), (0, -3520, 4)), (F, (0, -3560, 9), (0, -3500, 4))], lens=26)
    return S


def s02(k, F):  # you never open the door.
    S = stage("night")
    fd, bd = hall(S)
    n = narrator_in_hall(S, (-3.6, 4.0), -90, "worried")
    n.arm("R", 1, 20)
    n.arm("R", kf(10), 85)
    S.cam_at(V((HALL.x - 1.0, HALL.y - 2.5, 5.2)), V((HALL.x - 5.5, HALL.y + 4.0, 4.0)), lens=30)
    return S


def s03(k, F):  # That's when the Knockers come.
    S = stage("night")
    lamps_dark()
    kn, eyes = knocker((2.5, -3470, 0), yaw=0, height=10)
    kit.key(kn, 1, loc=(2.5, -3470, 0))
    kit.key(kn, F, loc=(2.5, -3474, 0))
    S.cam_at(V((10, -3525, 3)), V((2.5, -3470, 6)), lens=34, fstop=None)
    return S


def s04(k, F):  # They sound like people you love.
    S = stage("night")
    fd, bd = hall(S)
    knocks(fd, [kf(4), kf(4) + 6, kf(4) + 12])
    S.cam_at(V((HALL.x - 1.5, HALL.y - 1.0, 5.0)), V((HALL.x - 6, HALL.y + 4, 4)), lens=32)
    return S


def s05(k, F):  # Last year, one knocked on the Parkers' door using their grandma's voice.
    S = stage("night")
    porch(S, lit=False)
    kn, eyes = knocker((P.x + 0.6, P.y + 2.0, 0.5), yaw=180, height=8.5)
    S.cam_at(V((P.x + 6, P.y - 16, 4.5)), V((P.x, P.y + 2, 4.5)), lens=32, fstop=None)
    return S


def s06(k, F):  # Their grandma lives in Florida.
    S = stage("day")
    c = S.char("Prey1", (11, -3500), 0, "neutral")
    c.arm("L", kf(6), 30, 35)
    c.arm("R", kf(6), 30, 35)
    c.look(kf(6), 0, -5)
    sign = kit.box((0.2, 3.6, 2.2), (14.6, -3500, 5.5), kit.mat("postcard", (0.4, 0.75, 0.95)), 0.05)
    text("FLORIDA", (14.45, -3500, 5.2), rot=(90, 0, -90), size=0.6, color=(1, 0.95, 0.4), emit=0.5)
    S.cam(c.chest_pt() + V((0, 0, 0.6)), dist=10, yaw=-15, lens=34)
    return S


def s07(k, F):  # The rules are simple. Lock everything.
    S = stage("night")
    fd, bd = hall(S)
    n = narrator_in_hall(S, (-3.6, 4.0), -90, "determined")
    for j, f in enumerate(range(1, F + 2, 6)):
        n.arm("R", f, 85 if j % 2 else 70, 10 if j % 2 else -5)
    S.cam_at(V((HALL.x + 1.5, HALL.y - 0.5, 5.4)), n.head_pt() - V((0, 0, 1.0)), lens=30)
    return S


def s08(k, F):  # Don't answer.
    S = stage("night")
    fd, bd = hall(S)
    n = narrator_in_hall(S, (-1.5, 2.0), 180 + 60, "scared")
    n.lean(1, -8)
    n.arm("L", 1, 20, 30)
    n.arm("R", 1, 20, 30)
    S.drone([(1, (HALL.x + 2, HALL.y - 6, 5), n.head_pt() - V((0, 0, 1.2))),
             (F, (HALL.x + 0.5, HALL.y - 3.5, 4.8), n.head_pt() - V((0, 0, 1.0)))], lens=30)
    return S


def s09(k, F):  # Knockers can copy any voice, but only words they heard today.
    S = stage("night")
    porch(S, lit=False)
    kn, eyes = knocker((P.x - 9.8, P.y + 1.0, 0), yaw=180, height=9)
    for e in eyes:   # eyes blink as it "listens"
        m = e.active_material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        for j, f in enumerate(range(1, F + 2, 12)):
            m.default_value = 25 if j % 3 else 0.5
            m.keyframe_insert("default_value", frame=f)
    S.drone([(1, (P.x - 2, P.y - 14, 4), (P.x - 9.8, P.y + 1, 6)), (F, (P.x - 6, P.y - 9, 5.5), (P.x - 9.8, P.y + 1, 7))], lens=30)
    return S


def parents(S, mom_xy, dad_xy, yaw_m=0, yaw_d=0, expr="smile"):
    mom = S.char("Crowd1", mom_xy, yaw_m, expr)
    dad = S.char("Cousin", dad_xy, yaw_d, expr)
    for c in (mom, dad):
        c.root.scale = (1.18, 1.18, 1.18)
    return mom, dad


def s10(k, F):  # Tonight, Mom and Dad went out for dinner.
    S = stage("dusk")
    porch(S, lit=True)
    mom, dad = parents(S, (P.x - 2.2, P.y + 0.5), (P.x + 2.2, P.y + 0.5), 0, 0)
    for c in (mom, dad):
        p = c.pos
        c.walk(kf(F * 0.3), F, (p.x, p.y - 5))
    n = S.char("Narrator", (P.x, P.y + 2.4), 0, "smile")
    n.arm("R", 1, 0, 120)
    S.cam_at(V((P.x + 6, P.y - 15, 5)), V((P.x, P.y + 1, 3.6)), lens=30)
    return S


def s11(k, F):  # "Back before the lights go out," Mom said.
    S = stage("dusk")
    porch(S, lit=True)
    mom, dad = parents(S, (P.x - 1.8, P.y), (P.x + 3.0, P.y - 1.0), 160, 0)
    n = S.char("Narrator", (P.x - 1.6, P.y + 2.6), 0, "smile")
    mom.talk(3, F, base="smile")
    mom.point(kf(6), "R", up=40)
    S.cam(mom.head_pt() - V((0, 0, 1.4)), dist=9, yaw=-20, height=mom.head_pt().z - 0.6, lens=34)
    return S


def s12(k, F):  # She kissed my head and called me "bug," like she does every night.
    S = stage("dusk")
    porch(S, lit=True)
    mom = S.char("Crowd1", (P.x - 1.6, P.y), 180, "laugh")
    mom.root.scale = (1.18, 1.18, 1.18)
    n = S.char("Narrator", (P.x - 1.6, P.y + 2.4), 0, "embarrassed")
    mom.lean(kf(5), 22)
    mom.lean(kf(F * 0.7), 0)
    mom.talk(kf(F * 0.55), F, base="laugh")
    S.allow_close = {("Crowd1", "Narrator")}
    S.cam_at(V((P.x + 5.5, P.y - 3, 5.5)), V((P.x - 1.6, P.y + 1.2, 5)), lens=30)
    return S


def s13(k, F):  # We were on the front porch.  (the clue: eyes in the bushes)
    S = stage("dusk")
    porch(S, lit=True)
    mom, dad = parents(S, (P.x - 2.4, P.y + 0.4), (P.x + 2.4, P.y + 0.4), 180, 180)
    n = S.char("Narrator", (P.x, P.y + 2.4), 0, "smile")
    for sx in (-0.25, 0.25):
        kit.sphere(0.1, (P.x - 9.5 + sx, P.y + 0.9, 1.6), kit.mat("bushEye", (1, 1, 0.9), emit=25, emit_color=(1, 1, 0.9)), seg=8)
    S.drone([(1, (P.x + 2, P.y - 13, 5), (P.x, P.y + 1, 3.5)), (F, (P.x - 4, P.y - 10, 3), (P.x - 6.5, P.y + 1, 2.4))], lens=30)
    return S


def s14(k, F):  # At nine, the streetlights went out.
    S = stage("night")
    lamps_off(S, 4, gap=2)
    S.cam_at(V((-10, -3540, 3)), V((4, -3500, 6)), lens=26, fstop=None)
    return S


def s15(k, F):  # They weren't home.
    S = stage("night")
    porch(S, lit=False)
    S.cam_at(V((P.x, P.y - 22, 6)), V((P.x, P.y, 4)), lens=26, fstop=None)
    return S


def s16(k, F):  # At nine-oh-one, someone knocked on the front door.
    S = stage("night")
    fd, bd = hall(S, "9:01")
    n = narrator_in_hall(S, (0.5, -2.0), 180 + 40, "shocked")
    knocks(fd, [kf(5), kf(5) + 6, kf(5) + 12])
    n.faces([(1, "neutral"), (kf(5) + 2, "shocked")])
    n.look(kf(6), 40, 0)
    S.cam_at(V((HALL.x + 4.5, HALL.y - 9.5, 6)), V((HALL.x - 3, HALL.y + 3, 4)), lens=26)
    return S


def s17(k, F):  # "Bug? It's Mom. I lost my keys. Open up, it's freezing."
    S = stage("night")
    fd, bd = hall(S)
    knocks(fd, [3, 9, kf(F * 0.6)])
    L = kit.point((HALL.x - 6.6, HALL.y + 4, 0.4), (0.55, 0.65, 1.0), 80, 0.3)    # light under the door
    shadow = kit.box((0.05, 1.6, 0.2), (HALL.x - 5.92, HALL.y + 4.4, 0.06), kit.mat("feet", (0, 0, 0)), 0)  # feet shadow
    kit.key(shadow, 1, loc=(HALL.x - 5.92, HALL.y + 4.6, 0.06))
    kit.key(shadow, F, loc=(HALL.x - 5.92, HALL.y + 3.8, 0.06))
    S.cam_at(V((HALL.x - 2.5, HALL.y + 1.5, 3.2)), V((HALL.x - 6, HALL.y + 4, 2.8)), lens=30)
    return S


def s18(k, F):  # Then, a knock on the back door. Softer.
    S = stage("night")
    fd, bd = hall(S)
    n = narrator_in_hall(S, (0.5, -2.0), 180 - 40, "scared")
    knocks(bd, [kf(4), kf(4) + 8], amp=0.6)
    n.look(kf(5), -45, 0)
    S.cam_at(V((HALL.x - 4.5, HALL.y - 9.5, 6)), V((HALL.x + 3, HALL.y + 3, 4)), lens=26)
    return S


def s19(k, F):  # "Hey, kiddo. It's Dad. Mom's with me. Don't open the front. Something followed us."
    S = stage("night")
    fd, bd = hall(S)
    S.drone([(1, (HALL.x + 1.0, HALL.y + 1.0, 4), (HALL.x + 6, HALL.y + 4, 3.5)),
             (F, (HALL.x + 3.0, HALL.y + 2.8, 3.8), (HALL.x + 6, HALL.y + 4, 3.5))], lens=32, allow_close=True)
    return S


def s20(k, F):  # Dad never calls me kiddo.
    S = stage("night")
    fd, bd = hall(S)
    n = narrator_in_hall(S, (0.5, -2.0), 0, "worried")
    n.look(1, 30, 0)
    n.look(kf(F * 0.5), -15, 0)
    S.cam(n.head_pt() - V((0, 0, 1.5)), dist=9, yaw=0, height=n.head_pt().z - 0.7, lens=32)
    return S


def s21(k, F):  # But Mom said "bug" on the porch, where anything could have heard it.  (flashback: eyes in the bush)
    S = stage("dusk")
    porch(S, lit=True)
    mom = S.char("Crowd1", (P.x - 1.6, P.y), 180, "laugh")
    mom.root.scale = (1.18, 1.18, 1.18)
    S.char("Narrator", (P.x - 1.6, P.y + 2.4), 0, "embarrassed")
    S.allow_close = {("Crowd1", "Narrator")}
    for sx in (-0.25, 0.25):
        kit.sphere(0.1, (P.x - 9.5 + sx, P.y + 0.9, 1.6), kit.mat("bushEye", (1, 1, 0.9), emit=25, emit_color=(1, 1, 0.9)), seg=8)
    S.drone([(1, (P.x - 1.6, P.y - 8, 5), (P.x - 1.6, P.y + 1, 4.5)), (F, (P.x - 9.5, P.y - 5.5, 2.2), (P.x - 9.5, P.y + 1, 1.6))],
            lens=30, allow_close=True)
    return S


def s22(k, F):  # The front door rattled.
    S = stage("night")
    fd, bd = hall(S)
    rattle(fd, 1, F, amp=3.5)
    S.cam_at(V((HALL.x - 1.5, HALL.y - 1.0, 5.0)), V((HALL.x - 6, HALL.y + 4, 4)), lens=30)
    S.shake(1, F, 0.08)
    return S


def s23(k, F):  # The back door went quiet. Too quiet.
    S = stage("night")
    fd, bd = hall(S)
    S.drone([(1, (HALL.x - 2.0, HALL.y - 4, 5)), (F, (HALL.x + 2.0, HALL.y + 1.5, 4.4))][0:0] or
            [(1, (HALL.x - 2.0, HALL.y - 4, 5), (HALL.x + 6, HALL.y + 4, 4)),
             (F, (HALL.x + 2.0, HALL.y + 1.5, 4.4), (HALL.x + 6, HALL.y + 4, 4))], lens=30, allow_close=True)
    return S


def s24(k, F):  # My phone has two percent battery.
    S = stage("night")
    fd, bd = hall(S)
    n = narrator_in_hall(S, (0, 0), 0, "scared")
    n.arm("R", 1, 75, -10)
    ph = phone(n)
    t = text("2%", tuple(ph.matrix_world.translation + V((0, -0.2, 0.2))), size=0.35, color=(1, 0.2, 0.2), emit=6)
    attach(t, n.arms["R"])
    S.cam_at(n.world((0.5, 3.2, 3.5)), n.world((0.9, 1.0, 2.6)), lens=34, allow_close=True)
    return S


def s25(k, F):  # I can reach one door before it dies.
    S = stage("night")
    fd, bd = hall(S)
    n = narrator_in_hall(S, (0, 1.0), 0, "scared")
    n.look(1, 50, 0)
    n.look(kf(F * 0.35), -50, 0)
    n.look(kf(F * 0.7), 50, 0)
    S.cam(V((HALL.x, HALL.y + 2, 3.5)), dist=11, yaw=0, height=6.0, lens=28)
    return S


def s26(k, F):  # Front door, or back door?  (drone rises over him, both doors in frame, cut to black)
    S = stage("night")
    fd, bd = hall(S)
    n = narrator_in_hall(S, (0, 1.0), 0, "scared")
    rattle(fd, 1, F, amp=2.0, every=3)
    S.drone([(1, (HALL.x, HALL.y - 9, 4.5), (HALL.x, HALL.y + 2, 3.8)), (F, (HALL.x, HALL.y - 7, 10.5), (HALL.x, HALL.y + 3, 2))],
            lens=24)
    return S


SHOTS = {i: globals()[f"s{i:02d}"] for i in range(1, 27)}
