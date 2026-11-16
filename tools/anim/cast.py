"""Recurring cast (scripts/CAST.md): story names -> character models, plus their standard looks.

    from cast import C, place
    milo = place(S, "Milo", (x, y), yaw, "smile")
"""
import rblx

C = {"Milo": "Narrator", "Rio": "Crowd3", "Kai": "Kai", "Pip": "Smallkid", "Juno": "Prey1", "Dev": "Prey2",
     "Wren": "Prey3", "Odessa": "Crowd2", "Mom": "Crowd1", "Dad": "Cousin", "Parker": "Crowd4"}
ADULT_SCALE = {"Mom": 1.18, "Dad": 1.18, "Parker": 1.18, "Odessa": 1.18}
rblx.HAIR_OVERRIDE["Kai"] = dict(style="spiky", color=(0.03, 0.03, 0.045), shine=(0.12, 0.12, 0.16))


def place(S, name, xy, yaw=0, expr="smile"):
    c = S.char(C[name], xy, yaw, expr)
    s = ADULT_SCALE.get(name)
    if s:
        c.root.scale = (s, s, s)
    if name == "Dad":
        S.hide("Sunglass")
    return c
