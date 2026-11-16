"""cast-lineup: every character model side by side, for the cast sheet (scripts/CAST.md)."""
from mathutils import Vector

import rblx

NAMES = ["Narrator", "Crowd3", "Kai", "Smallkid", "Prey1", "Prey2", "Prey3", "Crowd2", "Crowd1", "Cousin", "Crowd4"]
rblx.HAIR_OVERRIDE["Kai"] = dict(style="spiky", color=(0.03, 0.03, 0.045), shine=(0.12, 0.12, 0.16))


def s01(k, F):
    S = rblx.Stage("alpha-mark", "day")
    for i, n in enumerate(NAMES):
        S.char(n, (-1300 + (i - 5) * 4.6, -3600), 0, "smile")
    S.cam_at(Vector((-1300, -3632, 4.0)), Vector((-1300, -3600, 3.2)), lens=50, fstop=None)
    return S


SHOTS = {1: s01}
