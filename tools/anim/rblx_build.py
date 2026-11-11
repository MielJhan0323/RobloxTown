"""Inside Blender: turn a Roblox Studio OBJ export into a posable asset .blend.

blender -b --factory-startup -P tools/anim/rblx_build.py -- <export.obj> <out.blend> <faces_dir>

- Characters are found by name: <Name><1..6> R6 parts (legs, arms, torso, head = the 517-vert mesh).
  Their parts are sorted by geometry, so the export's numbering does not matter.
- Every other object near a character (hair "Handle", glasses, pockets, freckles...) is parented to
  the nearest body part.
- Rig per character (collection "CH_<Name>"): root (feet) > body (hips) > torso, neck > head,
  shoulders > arms, hips > legs. Root faces -Y after build (yaw 0 = facing a camera at -Y).
- The head's UVs are remapped to the face square of the atlas and the head gets its own material
  that reads faces_dir/<Name>/<expr>.png (made by tools/anim/rblx_faces.py).
- Everything else stays where Studio put it (the sets), in collection "SETS".
"""
import json
import math
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OBJ, OUT, FACES = argv[0], argv[1], Path(argv[2])
CHAR_RE = re.compile(r"^(Narrator|Kai|Cousin|Prey\d|Crowd\d|Smallkid)(\d)$")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=OBJ, use_split_groups=True)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]


def bbox(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector([min(v[i] for v in ws) for i in range(3)]), Vector([max(v[i] for v in ws) for i in range(3)]))


# plastic look + nearest-neighbour textures (crisp like Roblox)
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    for n in m.node_tree.nodes:
        if n.type == "TEX_IMAGE":
            n.interpolation = "Closest"
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Roughness"].default_value = 0.55
            n.inputs["Specular IOR Level" if "Specular IOR Level" in n.inputs else "Specular"].default_value = 0.25
    m.blend_method = "HASHED" if any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes) else "OPAQUE"
    m.shadow_method = "HASHED"

groups = {}
for o in objs:
    mm = CHAR_RE.match(o.name)
    if mm:
        groups.setdefault(mm.group(1), []).append(o)
chars = {k: v for k, v in groups.items() if len(v) == 6}
used = {o for v in chars.values() for o in v}

coll_sets = bpy.data.collections.new("SETS")
bpy.context.scene.collection.children.link(coll_sets)
meta = {}


CUR = {}


def empty(name, loc, parent=None):
    e = bpy.data.objects.new(name, None)
    CUR["coll"].objects.link(e)
    e.empty_display_size = 0.4
    e.location = loc
    bpy.context.view_layer.update()
    if parent:
        e.parent = parent
        e.matrix_parent_inverse = parent.matrix_world.inverted()
    bpy.context.view_layer.update()
    return e


def parent_keep(o, p):
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy()
    o.parent = p
    o.matrix_parent_inverse = p.matrix_world.inverted()
    o.matrix_world = mw


for name, parts in chars.items():
    head = max(parts, key=lambda o: len(o.data.vertices))
    rest = [o for o in parts if o is not head]
    torso = max(rest, key=lambda o: bbox(o)[1].x - bbox(o)[0].x)
    rest.remove(torso)
    tlo, thi = bbox(torso)
    cx, cy = (tlo.x + thi.x) / 2, (tlo.y + thi.y) / 2
    legs = sorted(rest, key=lambda o: bbox(o)[0].z)[:2]
    arms = [o for o in rest if o not in legs]
    feet = min(bbox(o)[0].z for o in legs)
    coll = bpy.data.collections.new("CH_" + name)
    bpy.context.scene.collection.children.link(coll)
    CUR["coll"] = coll
    root = empty(f"{name}_root", (cx, cy, feet))
    body = empty(f"{name}_body", (cx, cy, tlo.z), root)
    neck = empty(f"{name}_neck", (cx, cy, thi.z), body)
    piv = {"torso": torso, "head": head}
    rigs = {"root": root, "body": body, "neck": neck}
    for o in arms:
        lo, hi = bbox(o)
        side = "R" if (lo.x + hi.x) / 2 > cx else "L"  # character faces +Y here: +X is its right
        sh = empty(f"{name}_arm{side}", ((lo.x + hi.x) / 2, cy, hi.z - 0.5), body)
        parent_keep(o, sh)
        rigs["arm" + side] = sh
        piv["arm" + side] = o
    for o in legs:
        lo, hi = bbox(o)
        side = "R" if (lo.x + hi.x) / 2 > cx else "L"
        hp = empty(f"{name}_leg{side}", ((lo.x + hi.x) / 2, cy, hi.z), body)
        parent_keep(o, hp)
        rigs["leg" + side] = hp
        piv["leg" + side] = o
    parent_keep(torso, body)
    parent_keep(head, neck)
    # accessories: anything within this character's footprint in the lineup row
    for o in objs:
        if o in used or o.parent:
            continue
        lo, hi = bbox(o)
        c = (lo + hi) / 2
        if not (tlo.x - 1.6 <= c.x <= thi.x + 1.6 and abs(c.y - cy) < 2.5 and feet - 0.5 <= c.z <= thi.z + 4):
            continue

        def dist(p):
            a, b = bbox(p)
            q = Vector([min(max(c[i], a[i]), b[i]) for i in range(3)])
            return (q - c).length

        target = head if c.z > thi.z - 0.1 else min(piv.values(), key=dist)
        parent_keep(o, target)
        used.add(o)
        coll.objects.link(o)
    for o in parts:
        used.add(o)
        coll.objects.link(o)
    # head: remap UVs to the face square, own material with an image per expression
    uv = head.data.uv_layers.active.data
    us = [d.uv.x for d in uv]
    vs = [d.uv.y for d in uv]
    u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
    img_path = None
    for n in head.active_material.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            img_path = bpy.path.abspath(n.image.filepath)
    for d in uv:
        d.uv.x = (d.uv.x - u0) / max(1e-6, u1 - u0)
        d.uv.y = (d.uv.y - v0) / max(1e-6, v1 - v0)
    hm = bpy.data.materials.new(f"{name}_face")
    hm.use_nodes = True
    nt = hm.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.5
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.name = "FACE"
    tex.interpolation = "Linear"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    head.data.materials.clear()
    head.data.materials.append(hm)
    # turn the whole character to face -Y
    root.rotation_euler.z = math.pi
    meta[name] = {"home": [cx, cy, feet], "height": thi.z - feet + (thi.z - tlo.z) * 0 + 1.2,
                  "head_top": max(bbox(head)[1].z, thi.z) - feet, "shoulder": thi.z - feet,
                  "atlas": img_path, "face_uv": [u0, u1, v0, v1], "arm_len": bbox(piv["armL"])[1].z - bbox(piv["armL"])[0].z}

for o in objs:
    if o not in used:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll_sets.objects.link(o)
for o in list(bpy.context.scene.collection.objects):
    bpy.context.scene.collection.objects.unlink(o)

Path(OUT).with_suffix(".json").write_text(json.dumps(meta, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILT", list(meta))
