"""Animated stand-in shots for scripts/lighthouse.md (one function per shot).

Each shot(k, F) builds a scene with the kit and animates it over frames 1..F.
Camera: yaw 0 = looking from -Y towards +Y. Characters face -Y at yaw 0.
"""
import math

LH = (34, 70, 0)          # lighthouse position (exterior sets)
BLUE = (0.30, 0.52, 0.85)  # June's new blue house
OLD = (0.95, 0.82, 0.50)   # the old yellow house


# ---------------------------------------------------------------- shared sets
def seaside(k, F, light="sunset", fog=0.0, lit=False, beam=(-40, 40), beam_target=None, town_seed=2, lh=LH, lh_scale=1.0):
    k.lighting(light, fog)
    k.ground(400, (0.40, 0.56, 0.30) if light != "night" else (0.18, 0.26, 0.2), loc=(0, -140, 0))
    k.ocean((0, 140, -0.3), (600, 160), (0.07, 0.25, 0.42) if light != "night" else (0.02, 0.06, 0.14), frames=F)
    k.box((60, 30, 6), (lh[0], lh[1], -2.5), k.mat("cliff", (0.45, 0.42, 0.38), 0.95), 2.0)
    k.town(lit=lit, seed=town_seed, y0=18, extent=45)
    return k.lighthouse((lh[0], lh[1], 3), beam_frames=None if beam_target else beam, target=beam_target, frames=F, scale=lh_scale)


def blue_house(k, F, light="sunset", fog=0.0, lit=False, beam_on_house=False, porch_people=False):
    k.lighting(light, fog)
    k.ground(400, (0.40, 0.56, 0.30) if light != "night" else (0.16, 0.24, 0.19), loc=(0, -140, 0))
    k.ocean((0, 120, -0.3), (600, 160), (0.07, 0.25, 0.42) if light != "night" else (0.02, 0.06, 0.14), frames=F)
    h, wins = k.house((0, 10, 0), 0, BLUE, (0.85, 0.85, 0.88), lit=lit)
    k.dock((14, 48, 0.2), 24)
    k.fence(-14, -6, 4)
    k.tree((-12, 16), 1.2)
    k.tree((11, 18), 1.0)
    k.lighthouse((40, 85, 3), beam_frames=None if beam_on_house else (-20, 20), target=(0, 6, 3) if beam_on_house else None, frames=F)
    return h, wins


def bedroom(k, F, night=True, beam=True, lamp=False):
    k.lighting("night" if night else "morning")
    k.room(16, 12, 9, wall=(0.72, 0.80, 0.95) if night else (0.95, 0.88, 0.75), window=3.0, night=night)
    b = k.bed((-2.5, 1.5, 0), 0, (0.95, 0.65, 0.75))
    k.box((2.0, 1.4, 2.4), (4.5, 4.2, 1.2), k.mat("dresser", (0.85, 0.75, 0.6), 0.6), 0.05)
    k.bunny((-1.8, 3.3, 2.4))
    if beam:
        k.beam_on((-2.5, 0.5, 2.2), from_dir=(0.45, 1.0, 0.55), length=30, alpha=0.12, power=5000, radius=1.3)
    if lamp:
        k.point((4.5, 4.0, 3.0), (1, 0.7, 0.4), 150, 0.3)
    return b


def kitchen(k, F, light="day"):
    k.lighting("morning" if light == "day" else "dusk")
    k.room(18, 12, 9, wall=(0.98, 0.92, 0.80), floor=(0.75, 0.70, 0.62), window=-4.0, night=light != "day")
    k.box((7, 2.2, 3.2), (4.5, 4.6, 1.6), k.mat("counter", (0.55, 0.7, 0.75), 0.5), 0.05)
    k.box((7.2, 2.4, 0.25), (4.5, 4.6, 3.3), k.mat("countertop", (0.95, 0.95, 0.95), 0.3), 0.03)
    k.table((-1, 0, 0))
    k.box((1.5, 1.5, 1.5), (-3.8, 0, 0.75), k.mat("chair", (0.65, 0.45, 0.28), 0.6), 0.05)
    k.box((1.5, 1.5, 1.5), (1.8, 0, 0.75), k.mat("chair", (0.65, 0.45, 0.28), 0.6), 0.05)


def living(k, F, night=False):
    k.lighting("night" if night else "golden")
    k.room(18, 12, 9, wall=(0.85, 0.75, 0.62), floor=(0.55, 0.38, 0.26), window=4.5, night=night)
    k.couch((-2, 3.4, 0), 0)
    k.box((4, 3, 0.15), (-2, -0.5, 0.08), k.mat("rug", (0.7, 0.3, 0.3), 0.95), 0.0)
    k.cyl(0.6, 3, (6.5, 3.5, 1.5), k.mat("lampbase", (0.3, 0.3, 0.3), 0.4))
    k.cyl(1.0, 1.0, (6.5, 3.5, 3.4), k.mat("shade", (1, 0.9, 0.7), 0.6, emit=1.5), r2=0.6)


# ---------------------------------------------------------------- shots
def s01(k, F):  # In this town, — seaside town at golden sunset, wide
    seaside(k, F, "sunset", beam=(-30, 10))
    k.camera((5, 40, 6), dist=70, height=18, yaw=-10, lens=32, fstop=None, frames=F, dolly=0.08)


def s02(k, F):  # the lighthouse shines for anyone who's lost.
    seaside(k, F, "sunset", beam=(-70, 30))
    k.camera((LH[0], LH[1], 14), dist=40, height=8, yaw=-25, lens=35, fstop=None, frames=F, dolly=0.1)


def s03(k, F):  # Not just ships. — boat in the beam
    seaside(k, F, "dusk", beam_target=(6, 85, 1.5), lh=(40, 110, 0))
    k.boat((6, 85, 0.2), 20, frames=F)
    k.spot((0, 70, 30), (6, 85, 1), (1, 0.92, 0.75), 30000, 14)
    k.camera((6, 85, 2.5), dist=30, height=7, yaw=-15, lens=40, fstop=None, frames=F, dolly=0.05)


def s04(k, F):  # People. — townsperson surprised in a spotlight (punch-in)
    k.lighting("dusk")
    k.ground(200, (0.5, 0.48, 0.45))
    k.house((-7, 8, 0), 0, (0.95, 0.85, 0.55), lit=True, porch=False)
    k.house((7, 8, 0), 0, (0.85, 0.5, 0.45), lit=True, porch=False)
    t = k.Char("towny", (0, 0, 0), 0, "surprised")
    t.idle(1, F)
    t.look(1, 0, 0)
    t.look(8, 0, -22)
    t.arms(1, (0, 0, 0), (0, 0, 0))
    t.arms(10, (0, -20, 0), (0, 20, 0))
    k.beam_on((0, 0, 3), from_dir=(0.2, 0.7, 1.0), length=40, power=9000, radius=1.2, shaft=False)
    k.sparkle_particles((0, 0, 4), 18, 2.5, F)
    k.camera(tuple(t.eye_level() + k.Vector((0, 0, -0.5))), dist=6.5, height=4.3, lens=50, fstop=2.0, frames=F)


def s05(k, F):  # Tommy lost at the summer fair, looking around, teary
    k.lighting("sunset")
    k.fairground(F)
    k.balloons((-4, 8, 0))
    tm = k.Char("tommy", (0, 0, 0), 0, "sad")
    tm.idle(1, F)
    tm.look_around(1, F, 40)
    for i in range(4):
        towny = k.Char("towny", (-7 + i * 4.5, 7 + (i % 2) * 2, 0), 180 if i % 2 else 160, "smile",
                       shirt=[(0.9, 0.3, 0.3), (0.3, 0.6, 0.9), (0.8, 0.7, 0.2), (0.6, 0.4, 0.8)][i])
        towny.walk(1, F, (-7 + i * 4.5 + (3 if i % 2 else -3), 7 + (i % 2) * 2))
    k.camera(tuple(tm.eye_level() + k.Vector((0, 0, -0.8))), dist=11, height=3.6, yaw=8, lens=45, fstop=2.0, frames=F)


def s06(k, F):  # the beam found him at the cotton candy stand.
    k.lighting("dusk")
    k.fairground(F)
    k.stall((0, 3), (1, 0.55, 0.75), 6)
    tm = k.Char("tommy", (0, -1.5, 0), 0, "happy")
    tm.idle(1, F)
    k.cotton_candy(tm.handR)
    tm.raise_up(1, "R", -80)
    tm.raise_up(F // 2, "R", -110)
    tm.look(1, 0, -10)
    k.beam_on((0, -1.5, 2.5), from_dir=(0.3, 0.8, 1.0), length=45, power=9000, radius=1.2, shaft=False)
    k.sparkle_particles((0, -1.5, 3), 16, 2.0, F)
    k.camera(tuple(tm.chest() + k.Vector((0, 0, 0.6))), dist=8, height=3.4, lens=45, fstop=2.2, frames=F)


def s07(k, F):  # When Mrs. Alder lost her glasses — squinting, patting cushions
    living(k, F)
    a = k.Char("alder", (-2, -0.3, 0), 0, "worried", glasses=False)
    a.idle(1, F)
    key = k.key
    key(a.hip, 1, rot=(25, 0, 0))
    for i, f in enumerate(range(1, F, 9)):
        a.arms(f, (-55 - (15 if i % 2 else 0), 0, 0), (-50 - (0 if i % 2 else 15), 0, 0))
    a.look_around(1, F, 25)
    a.glasses_obj = None
    gl = k.empty((0, 0, 0), a.hd, "g")  # glasses pushed up on her hair (she hasn't noticed)
    gm = k.mat("glassframe", (0.15, 0.1, 0.08), 0.3)
    for x in (-0.27, 0.27):
        k.torus(0.17, 0.025, (x, -0.45, 1.38), gm, gl, rot=(60, 0, 0))
    k.camera(tuple(a.chest() + k.Vector((0, 0, 0.8))), dist=11, height=4.6, yaw=12, lens=45, fstop=2.4, frames=F)


def s08(k, F):  # it lit up her own head. (punch-in)
    living(k, F, night=False)
    a = k.Char("alder", (-2, -0.3, 0), 0, "confused", glasses=False)
    a.idle(1, F)
    gl = k.empty((0, 0, 0), a.hd, "g")
    gm = k.mat("glassframe", (0.15, 0.1, 0.08), 0.3)
    for x in (-0.27, 0.27):
        k.torus(0.17, 0.025, (x, -0.45, 1.38), gm, gl, rot=(60, 0, 0))
    a.look(1, 0, -15)
    k.beam_on(tuple(a.head_world()), from_dir=(0.4, 0.9, 1.2), length=25, power=4000, radius=0.8, shaft=False)
    k.sparkle_particles(tuple(a.head_world() + k.Vector((0, 0, 0.6))), 14, 1.2, F)
    k.camera(tuple(a.eye_level() + k.Vector((0, 0, -0.2))), dist=5.5, height=4.6, lens=50, fstop=2.0, frames=F)


def s09(k, F):  # They were on it. — close on glasses atop her hair, embarrassed smile
    living(k, F)
    a = k.Char("alder", (-2, -0.3, 0), 0, "embarrassed", glasses=False)
    a.idle(1, F, 0.5)
    gl = k.empty((0, 0, 0), a.hd, "g")
    gm = k.mat("glassframe", (0.15, 0.1, 0.08), 0.3)
    for x in (-0.27, 0.27):
        k.torus(0.17, 0.025, (x, -0.45, 1.38), gm, gl, rot=(60, 0, 0))
    a.raise_up(1, "R", -40)
    a.arm("R", 12, (-165, 0, -20))  # hand goes up to touch them
    k.camera(tuple(a.eye_level() + k.Vector((0, 0, 0.15))), dist=4.2, height=5.0, lens=55, fstop=1.8, frames=F)


def s10(k, F):  # And when my dad lost his job — kitchen table at dusk, head in hands
    kitchen(k, F, "dusk")
    k.point((-1, 0, 7), (1, 0.75, 0.45), 260, 0.5)
    k.box((1.6, 1.6, 1.5), (-1, 2.0, 0.75), k.mat("chair", (0.65, 0.45, 0.28), 0.6), 0.05)
    d = k.Char("dad", (-1, 1.9, 0), 0, "sad")
    d.sit_at(-1, 2.0, 1.5)
    d.idle(1, F, 0.3)
    d.head_in_hands(1, F)
    k.box((1.2, 0.05, 0.9), (-0.4, -0.2, 2.75), k.mat("letter", (0.95, 0.95, 0.9), 0.8), 0, rot=(90, 0, 15))
    k.cyl(0.25, 0.5, (-2.4, -0.3, 2.98), k.mat("mug", (0.9, 0.3, 0.25), 0.4))
    k.camera((-1, 1.2, 3.8), dist=9, height=5.2, yaw=10, lens=45, fstop=2.2, frames=F)


def s11(k, F):  # it shone on our porch for a whole week — old house at night, beam on porch
    k.lighting("night")
    k.ground(400, (0.16, 0.24, 0.19))
    h, _ = k.house((0, 8, 0), 0, OLD, (0.45, 0.3, 0.25), lit=True)
    k.tree((-10, 12), 1.2)
    k.tree((10, 14), 1.0)
    k.beam_on((0, 1.5, 1.0), from_dir=(0.8, 0.6, 0.75), length=60, power=30000, radius=2.5)
    k.camera((0, 6, 3), dist=26, height=5, yaw=-10, lens=35, fstop=None, frames=F, dolly=0.08)


def _porch_dad(k, F, expr):
    k.lighting("night")
    k.ground(400, (0.16, 0.24, 0.19))
    k.house((0, 8, 0), 0, OLD, (0.45, 0.3, 0.25), lit=True)
    k.box((2.2, 1.6, 1.4), (1.5, 2.8, 1.1), k.mat("porchchair", (0.85, 0.85, 0.82), 0.6), 0.1)
    d = k.Char("dad", (1.5, 2.6, 0.4), 0, expr)
    d.sit_at(1.5, 2.9, 1.8)
    d.idle(1, F, 0.4)
    d.hold_forward(1, "both", -80)
    k.newspaper(d.handL)
    k.beam_on((1.5, 2.3, 2.0), from_dir=(0.8, -0.6, 0.75), length=50, power=9000, radius=2.0, shaft=False)
    return d


def s12(k, F):  # He pretended not to notice. — reading newspaper
    d = _porch_dad(k, F, "neutral")
    d.look(1, 0, 22)
    k.camera((1.5, 2.6, 4.2), dist=9, height=4.6, yaw=-6, lens=45, fstop=2.2, frames=F)


def s13(k, F):  # He noticed. — peeks over the paper, small smile (punch)
    d = _porch_dad(k, F, "small_smile")
    d.hold_forward(1, "both", -80)
    d.hold_forward(10, "both", -62)
    d.look(1, 0, 18)
    d.look(10, -18, -10)
    k.camera(tuple(d.eye_level() + k.Vector((0, 0.4, -0.3))), dist=5, height=4.8, yaw=-10, lens=50, fstop=1.8, frames=F)


def s14(k, F):  # Then, we moved. — truck, family carrying boxes
    k.lighting("day")
    k.ground(400, (0.40, 0.56, 0.30))
    k.house((-6, 12, 0), 0, OLD, (0.45, 0.3, 0.25))
    k.truck((8, 4, 0), 0)
    for who, x0, x1, y in (("dad", -3, 3, 0), ("mom", -6, -0.5, -2), ("narrator", -9, -4, 1)):
        c = k.Char(who, (x0, y, 0), -90, "neutral")
        c.walk(1, F, (x1, y), arms=False)
        c.hold_forward(1, "both", -80)
        c.hold_forward(F, "both", -80)
        k.box((1.4, 1.2, 1.1), (0, -0.6, -0.4), k.mat("cardboard", (0.72, 0.52, 0.32), 0.85), 0.03, c.handL)
    j = k.Char("june", (-1.5, -4.5, 0), 0, "blank")
    j.idle(1, F)
    k.bunny((0.2, -0.4, 0), j.handL)
    k.camera((0, 0, 3), dist=24, height=6, yaw=0, lens=35, fstop=None, frames=F, dolly=0.06)


def s15(k, F):  # Across town, to a little blue house by the docks.
    blue_house(k, F, "golden")
    k.camera((4, 18, 3), dist=36, height=7, yaw=-18, lens=32, fstop=None, frames=F, dolly=0.1)


def s16(k, F):  # My sister June was six. — on bed hugging bunny
    bedroom(k, F, night=False, beam=False)
    j = k.Char("june", (-2.5, 0.5, 1.9), 0, "blank")
    j.sit_at(-2.5, 0.8, 2.05)
    j.idle(1, F)
    j.hold_forward(1, "both", -45)
    k.bunny((0.5, -0.5, 0.4), j.hip, rot=(0, 0, 0))
    k.camera(tuple(j.chest() + k.Vector((0, 0, 1.6))), dist=8, height=4.6, lens=45, fstop=2.0, frames=F)


def s17(k, F):  # She stopped talking the day we packed up her room. — empty room, boxes
    k.lighting("dusk")
    k.room(16, 12, 9, wall=(0.95, 0.85, 0.7), window=3.0, night=True)
    k.boxes_pile((-3, 3, 0), 5, 2)
    k.boxes_pile((4, 2.5, 0), 3, 5)
    j = k.Char("june", (0, -1, 0), 150, "sad")
    j.idle(1, F)
    j.look_around(1, F, 25)
    k.bunny((0.2, -0.4, 0), j.handL)
    k.point((0, -3, 7), (1, 0.7, 0.45), 160, 1.0)
    k.camera((0, 0, 3.2), dist=12, height=4.5, yaw=10, lens=40, fstop=2.4, frames=F)


def s18(k, F):  # Not sad-quiet. — close on June, blank
    bedroom(k, F, night=False, beam=False)
    j = k.Char("june", (0, -2, 0), 0, "blank")
    j.idle(1, F, 0.4)
    k.camera(tuple(j.eye_level() + k.Vector((0, 0, -0.35))), dist=4.0, height=3.2, lens=50, fstop=1.8, frames=F)


def s19(k, F):  # Just gone-quiet. — June at the window, back to camera
    bedroom(k, F, night=False, beam=False)
    j = k.Char("june", (3, 3.3, 0), 180, "blank")
    j.idle(1, F, 0.5)
    k.box((3, 1.4, 2.4), (3, 4.6, 1.2), k.mat("windowseat", (0.85, 0.75, 0.6), 0.6), 0.05)
    k.camera((3, 3.3, 3.2), dist=8, height=3.6, yaw=-10, lens=45, fstop=2.2, frames=F)


def s20(k, F):  # Mom tried pancakes.
    kitchen(k, F, "day")
    m = k.Char("mom", (1.5, -1.6, 0), 30, "happy")
    m.idle(1, F)
    m.hold_forward(1, "both", -70)
    m.hold_forward(F, "both", -80)
    k.pancakes((-0.6, -0.7, 2.73))
    k.box((1.4, 1.4, 1.5), (-3.0, -1.0, 0.75), k.mat("chair", (0.65, 0.45, 0.28), 0.6), 0.05)
    j = k.Char("june", (-3.0, -1.0, 0), -40, "blank")
    j.sit_at(-3.0, -1.0, 1.5)
    j.idle(1, F, 0.3)
    m.talk(1, F - 10)
    k.camera((-0.5, -1.4, 4.0), dist=13, height=5.0, yaw=0, lens=40, fstop=2.4, frames=F)


def s21(k, F):  # Dad tried knock-knock jokes. — goofy dance, June blank
    living(k, F)
    d = k.Char("dad", (2, -1, 0), -25, "happy")
    d.idle(1, F)
    d.shrug_goofy(1, F)
    d.talk(1, F)
    j = k.Char("june", (-3.0, 3.0, 0), 15, "blank")
    j.sit_at(-3.0, 3.1, 1.8)
    j.idle(1, F, 0.3)
    k.camera((0, 0, 4.0), dist=16, height=5.0, yaw=0, lens=40, fstop=2.4, frames=F)


def s22(k, F):  # I gave her my bike.
    k.lighting("day")
    k.ground(400, (0.5, 0.5, 0.5))
    k.house((0, 12, 0), 0, BLUE, (0.85, 0.85, 0.88))
    n = k.Char("narrator", (-3.2, -0.5, 0), -60, "smile")
    b = k.bike((-0.4, -0.5, 0), 0)
    n.idle(1, F)
    n.hold_forward(1, "both", -60)
    k.key(b, 1, loc=(-1.2, -0.5, 0))
    k.key(b, F, loc=(0.2, -0.5, 0))
    n.walk(1, F, (-1.8, -0.5))
    n.hold_forward(F, "both", -60)
    j = k.Char("june", (3.0, -0.8, 0), 60, "blank")
    j.idle(1, F)
    k.camera((0, -0.5, 2.8), dist=13, height=4, yaw=0, lens=40, fstop=2.6, frames=F)


def s23(k, F):  # Nothing. — close on June, no reaction
    k.lighting("day")
    k.ground(400, (0.5, 0.5, 0.5))
    k.house((0, 12, 0), 0, BLUE, (0.85, 0.85, 0.88))
    j = k.Char("june", (0, 0, 0), 0, "blank")
    j.idle(1, F, 0.2)
    k.camera(tuple(j.eye_level() + k.Vector((0, 0, -0.35))), dist=4.0, height=3.2, lens=50, fstop=1.8, frames=F, dolly=0.0)


def s24(k, F):  # The first foggy night, I couldn't sleep. — narrator awake in bed
    k.lighting("night")
    k.room(16, 12, 9, wall=(0.55, 0.62, 0.85), window=3.5, night=True)
    k.bed((0, 1.5, 0), 0, (0.35, 0.45, 0.85))
    n = k.Char("narrator", (0, -1.0, 0), 0, "neutral")
    n.lie_at(0, -0.6, 1.75)
    n.idle(1, F, 0.4)
    n.look(1, 0, 0)
    n.look(F // 2, 25, 0)
    k.camera((0, 2.4, 2.6), dist=7, height=7.5, yaw=0, lens=40, fstop=2.2, frames=F, focus=(0, 3.3, 2.4))


def s25(k, F):  # I looked out my window, — kneeling, looking out (from outside, through the window)
    k.lighting("night", fog=0.02)
    k.room(16, 12, 9, wall=(0.55, 0.62, 0.85), window=None, night=True)
    n = k.Char("narrator", (0, 2.5, 0), 0, "worried")
    n.sit_at(0, 2.6, 1.6)
    n.idle(1, F)
    n.look(1, 0, 0)
    n.look(F // 2, 10, -12)
    k.point((0, 4, 6), (0.6, 0.7, 1.0), 80, 1.0)
    k.camera(tuple(n.eye_level()), dist=5.5, height=4.6, lens=50, fstop=2.0, frames=F)


def s26(k, F):  # and the beam was sweeping the whole town.
    seaside(k, F, "night", fog=0.015, lit=True, beam=(-80, 30))
    k.camera((5, 40, 6), dist=70, height=20, yaw=-8, lens=30, fstop=None, frames=F, dolly=0.04)


def s27(k, F):  # Then it stopped. — lighthouse, beam frozen
    seaside(k, F, "night", fog=0.015, lit=True, beam=(-10, -10))
    k.camera((LH[0], LH[1], 15), dist=32, height=10, yaw=-30, lens=35, fstop=None, frames=F, dolly=0.0)


def s28(k, F):  # Right on our house. (sparkle, punch)
    blue_house(k, F, "night", fog=0.012, lit=True, beam_on_house=True)
    k.beam_on((0, 5.5, 3.5), from_dir=(0.6, 1.0, 0.45), length=60, alpha=0.16, power=40000, radius=3.0)
    k.sparkle_particles((0, 5, 5), 40, 5, F)
    k.camera((0, 8, 4), dist=30, height=5, yaw=8, lens=35, fstop=None, frames=F, dolly=0.1)


def s29(k, F):  # On June's window. — glowing window close
    _, wins = blue_house(k, F, "night", fog=0.012, lit=True, beam_on_house=True)
    k.beam_on((3.5, 5.4, 4.6), from_dir=(0.6, 1.0, 0.45), length=50, alpha=0.18, power=30000, radius=1.6)
    k.sparkle_particles((3.5, 5.2, 4.8), 14, 1.5, F)
    k.camera((3.5, 5.4, 4.6), dist=16, height=4.0, yaw=-8, lens=45, fstop=None, frames=F)


def s30(k, F):  # I tiptoed into her room. — hallway
    k.lighting("night")
    k.room(10, 16, 9, wall=(0.62, 0.62, 0.8), window=None, night=True)
    k.box((2.2, 0.4, 4.5), (3.5, -2, 2.25), k.mat("door", (0.45, 0.25, 0.15), 0.6), 0.04, rot=(0, 0, 90))
    k.point((3.4, -2, 3.5), (1.0, 0.85, 0.55), 220, 0.4)  # warm glow from June's door
    n = k.Char("narrator", (-3, 2, 0), -70, "worried")
    n.tiptoe(1, F, (1.8, -1.2))
    k.camera((0, 0, 3.2), dist=11, height=4.2, yaw=0, lens=40, fstop=2.4, frames=F)


def _june_bed(k, F, expr, sit=True):
    bedroom(k, F, night=True, beam=True)
    j = k.Char("june", (-2.5, 0.4, 0), 0, expr)
    j.sit_at(-2.5, 0.8, 2.05)
    j.idle(1, F, 0.6)
    return j


def s31(k, F):  # She was sitting up, staring at the light.
    j = _june_bed(k, F, "blank")
    j.look(1, 30, -12)
    k.spot((1, -6, 8), (-2.5, 0.4, 3.5), (1, 0.9, 0.7), 1500, 20)
    k.camera(tuple(j.eye_level() + k.Vector((0, 0, -0.6))), dist=8, height=4.6, yaw=-15, lens=45, fstop=2.0, frames=F)


def s32(k, F):  # "Are you lost?" I whispered. — narrator at bed edge
    j = _june_bed(k, F, "blank")
    n = k.Char("narrator", (-0.9, -0.4, 0), -120, "worried")
    n.sit_at(-1.0, -0.4, 2.05)
    n.idle(1, F, 0.5)
    n.talk(int(F * 0.15), int(F * 0.55))
    n.look(1, 10, 10)
    k.camera(tuple(n.eye_level() + k.Vector((0, 0, -0.3))), dist=6.0, height=4.4, yaw=-115, lens=50, fstop=1.8, frames=F)


def s33(k, F):  # She nodded. — teary
    j = _june_bed(k, F, "sad")
    j.nod(6, 2)
    for x in (-0.27, 0.27):
        k.sphere(0.05, (x, -0.62, 0.6), k.mat("tear", (0.6, 0.85, 1.0), 0.05, emit=1.0), j.hd, scale=(1, 0.5, 1.4))
    k.camera(tuple(j.eye_level() + k.Vector((0, 0, -0.3))), dist=3.6, height=3.6, yaw=-10, lens=50, fstop=1.8, frames=F)


def _both_bed(k, F, n_expr, j_expr):
    j = _june_bed(k, F, j_expr)
    n = k.Char("narrator", (-0.9, 0.2, 0), -30, n_expr)
    n.sit_at(-0.9, 0.4, 2.05)
    n.idle(1, F, 0.5)
    return j, n


def s34(k, F):  # "Me too, a little," I said. — small sad smile
    j, n = _both_bed(k, F, "small_smile", "blank")
    n.talk(1, int(F * 0.6))
    k.camera(tuple(n.eye_level() + k.Vector((0, 0, -0.3))), dist=4.4, height=4.3, yaw=25, lens=50, fstop=1.8, frames=F)


def s35(k, F):  # "New house." — gesturing at the room
    j, n = _both_bed(k, F, "smile", "blank")
    n.talk(1, F - 5)
    n.arm("R", 1, (-30, 0, 0))
    n.arm("R", F // 2, (-70, 0, 40))
    k.camera((-1.5, 0.2, 3.6), dist=9, height=4.6, yaw=10, lens=45, fstop=2.2, frames=F)


def s36(k, F):  # New street. New everything." — June leans on narrator's shoulder
    j, n = _both_bed(k, F, "small_smile", "small_smile")
    n.talk(1, int(F * 0.7))
    z = j.base_loc.z
    k.key(j.root, 1, loc=(-2.5, 0.8, z))
    k.key(j.root, F // 2, loc=(-2.0, 0.7, z))
    k.key(j.hip, 1, rot=(0, 0, 0))
    k.key(j.hip, F // 2 + 10, rot=(0, 16, 0))
    k.camera((-1.4, 0.2, 3.7), dist=6.5, height=4.4, yaw=5, lens=45, fstop=2.0, frames=F)


def s37(k, F):  # The light stayed all night. — house glowing in fog
    blue_house(k, F, "night", fog=0.02, lit=True, beam_on_house=True)
    k.beam_on((3.5, 5.4, 4.6), from_dir=(0.6, 1.0, 0.45), length=50, alpha=0.16, power=30000, radius=1.6)
    k.camera((0, 8, 4), dist=34, height=6, yaw=-14, lens=35, fstop=None, frames=F, dolly=0.06)


def s38(k, F):  # So did I. — both asleep (pull-out)
    bedroom(k, F, night=True, beam=True)
    j = k.Char("june", (-2.5, 0.2, 0), 0, "sleepy")
    j.lie_at(-2.5, 0.2, 1.75)
    n = k.Char("narrator", (-0.2, -1.4, 0), 0, "sleepy")
    n.sit_at(-0.2, -1.4, 0.0)
    k.key(n.neck, 1, rot=(10, -20, 0))
    k.key(n.neck, F, rot=(14, -24, 0))
    k.camera((-1.6, 1.0, 3.0), dist=10, height=6, yaw=10, lens=40, fstop=2.4, frames=F, dolly=-0.06)


def _front_door(k, F):
    k.lighting("morning")
    k.ground(400, (0.40, 0.56, 0.30))
    k.house((0, 8, 0), 0, BLUE, (0.85, 0.85, 0.88))


def s39(k, F):  # The next morning, the lighthouse keeper, — Mr. Pell at the door
    _front_door(k, F)
    p = k.Char("pell", (0, -5.0, 0), 0, "wise")
    p.walk(1, F - 10, (0, -0.6))
    p.idle(1, F)
    k.camera((0, -2.0, 4.2), dist=12, height=4.6, yaw=-20, lens=40, fstop=2.4, frames=F)


def s40(k, F):  # old Mr. Pell, knocked on our door — narrator opening the door, sleepy
    _front_door(k, F)
    n = k.Char("narrator", (0, 3.0, 0.4), 0, "sleepy")
    n.idle(1, F)
    p = k.Char("pell", (2.6, 0.8, 0.4), 160, "smile")
    p.knock(1, F // 2, "R")
    k.camera((0, 3.0, 3.8), dist=8, height=4.6, yaw=-22, lens=45, fstop=2.4, frames=F, focus=(0, 3.0, 4.0))


def s41(k, F):  # with a jar of sea glass. — close insert, glowing jar
    _front_door(k, F)
    p = k.Char("pell", (0, 2.8, 0.4), 0, "smile")
    p.idle(1, F)
    p.hold_forward(1, "both", -80)
    k.jar((0.75, -0.25, -0.3), p.handL)
    k.sparkle_particles((0, 1.6, 4.3), 14, 1.0, F, (0.6, 0.9, 1.0))
    k.camera((0, 1.6, 4.4), dist=4.2, height=4.6, yaw=0, lens=50, fstop=1.6, frames=F)


def s42(k, F):  # "The light doesn't fix lost," he said.
    _front_door(k, F)
    p = k.Char("pell", (0, 2.8, 0.4), 0, "wise")
    p.idle(1, F)
    p.talk(1, int(F * 0.8))
    k.camera(tuple(p.eye_level() + k.Vector((0, 0, -0.35))), dist=4.6, height=5.0, yaw=-12, lens=50, fstop=1.8, frames=F)


def s43(k, F):  # "It just shows someone where to sit." — Pell + narrator
    _front_door(k, F)
    p = k.Char("pell", (1.8, 2.8, 0.4), -60, "wise")
    p.idle(1, F)
    p.talk(1, F - 8)
    p.arm("R", 1, (-40, 0, 0))
    p.arm("R", F // 2, (-60, 0, -20))
    n = k.Char("narrator", (-1.8, 3.0, 0.4), 60, "neutral")
    n.idle(1, F)
    k.camera((0, 2.8, 4.0), dist=11, height=4.6, yaw=0, lens=40, fstop=2.4, frames=F)


def s44(k, F):  # June took the jar. — small hands reach
    _front_door(k, F)
    j = k.Char("june", (0, 2.8, 0.4), 0, "blank")
    j.idle(1, F)
    j.hold_forward(1, "both", -10)
    j.hold_forward(F // 2, "both", -80)
    jar = k.jar((0, 1.6, 2.0))
    k.key(jar, 1, loc=(0, 0.6, 2.4))
    k.key(jar, F // 2, loc=(0, 1.5, 2.0))
    k.key(jar, F, loc=(0, 1.6, 1.95))
    k.camera((0, 1.6, 3.2), dist=5, height=3.0, yaw=-8, lens=50, fstop=1.8, frames=F)


def s45(k, F):  # She held a blue piece up to the sun. (sparkle)
    k.lighting("golden")
    k.ground(400, (0.40, 0.56, 0.30), loc=(0, -140, 0))
    k.ocean((0, 120, -0.3), (600, 160), frames=F)
    j = k.Char("june", (0, 0, 0), 0, "small_smile")
    j.idle(1, F)
    j.raise_up(1, "R", -100)
    j.raise_up(F // 2, "R", -165)
    j.look(1, 0, -10)
    j.look(F // 2, 0, -30)
    g = k.box((0.3, 0.12, 0.3), (0, -0.2, 0.15), k.mat("blueglass", (0.2, 0.55, 1.0), 0.05, emit=6, alpha=0.9), 0.06, j.handR, rot=(0, 0, 30))
    k.point((0, -0.4, 0.15), (0.3, 0.6, 1.0), 25, 0.1).parent = j.handR
    k.sparkle_particles((0.6, -0.5, 4.8), 22, 1.3, F, (0.6, 0.85, 1.0))
    k.camera(tuple(j.eye_level() + k.Vector((0, 0, 0.3))), dist=6, height=2.6, yaw=-10, lens=45, fstop=1.8, frames=F)


def s46(k, F):  # And for the first time in three weeks, — family watching on the porch
    blue_house(k, F, "golden")
    j = k.Char("june", (0, 4.6, 0.4), 0, "blank")
    j.idle(1, F)
    for who, x, yaw in (("mom", -3, 25), ("dad", 3.2, -25), ("narrator", -5.6, 30)):
        c = k.Char(who, (x, 5.6, 0.4), yaw, "worried")
        c.idle(1, F)
        c.look(1, -yaw * 0.5, 15)
    k.camera((0, 5.0, 3.6), dist=16, height=4.6, yaw=0, lens=38, fstop=2.6, frames=F)


def s47(k, F):  # she said one word. — close, lips parting, small smile
    blue_house(k, F, "golden")
    j = k.Char("june", (0, 4.6, 0.4), 0, "small_smile")
    j.idle(1, F, 0.4)
    k.key(j.mouth_open, 1, scale=(1.2, 0.35, 0.05))
    k.key(j.mouth_open, int(F * 0.7), scale=(1.2, 0.35, 0.05))
    k.key(j.mouth_open, int(F * 0.85), scale=(1.2, 0.35, 0.45))
    k.camera(tuple(j.eye_level() + k.Vector((0, 0, -0.35))), dist=3.6, height=3.6, yaw=-6, lens=50, fstop=1.6, frames=F)


def s48(k, F):  # "Home." — house + lighthouse at golden sunset, family on porch (pull-out)
    k.lighting("sunset")
    k.ground(400, (0.40, 0.56, 0.30), loc=(0, -140, 0))
    k.ocean((0, 120, -0.3), (600, 160), frames=F)
    k.house((0, 10, 0), 0, BLUE, (0.85, 0.85, 0.88), lit=True)
    k.dock((14, 48, 0.2), 24)
    k.lighthouse((-26, 70, 3), beam_frames=(-30, 10), frames=F)
    j = k.Char("june", (0, 4.6, 0.4), 0, "happy")
    j.idle(1, F)
    j.wave(int(F * 0.3), F)
    for who, x in (("mom", -2.6), ("dad", 2.6), ("narrator", -5)):
        c = k.Char(who, (x, 5.4, 0.4), 0, "happy")
        c.idle(1, F)
    k.camera((0, 5, 3.5), dist=20, height=4.8, yaw=8, lens=35, fstop=3.5, frames=F, dolly=-0.12)


SHOTS = {int(n[1:]): f for n, f in globals().items() if n.startswith("s") and n[1:].isdigit()}
