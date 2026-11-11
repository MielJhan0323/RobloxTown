"""Shot helpers for stories animated with the user's exported Roblox Studio models (inside Blender).

Assets come from tools/anim/rblx_build.py (output/models/<slug>/assets.blend + assets.json + faces/).
Characters are R6 rigs: root (feet) > body > torso / neck > head / arms / legs. Units are studs
(a kid is ~5 studs tall). yaw 0 = facing -Y (toward a camera placed at -Y, kit.camera's default).

    import rblx
    S = rblx.Stage("alpha-mark", light="day")
    n = S.char("Narrator", (x, y), yaw=0, expr="smile")
    n.arm("L", f, fwd=80)          # raise left arm forward (degrees)
    n.face(f, "shocked")           # face decal swap at frame f
    n.talk(f0, f1)                 # mouth flaps (talk / base face)
    S.cam((x, y, z), dist=8, yaw=0, height=None, lens=50)
    S.render(out, frames)
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

import kit

R = math.radians
ROOT = Path(__file__).resolve().parents[2]
STEP = 15  # spacing of key poses (the render fills the in-betweens when ITT_STEP=2)
WIDEN = 0.7  # every camera lens is multiplied by this: wider, reference-style medium framing


def attach(obj, parent):
    """Parent keeping the current world transform."""
    bpy.context.view_layer.update()
    mw = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = mw
    return obj


def kf(f):
    """Snap a frame to the start of the held pose that shows it."""
    return 1 + max(0, round((f - 1) / STEP)) * STEP


class Char:
    def __init__(self, stage, name, loc, yaw=0, expr="smile"):
        self.S, self.name = stage, name
        g = lambda k: bpy.data.objects[f"{name}_{k}"]  # noqa: E731
        self.root, self.body, self.neck = g("root"), g("body"), g("neck")
        self.arms = {"L": g("armL"), "R": g("armR")}
        self.legs = {"L": g("legL"), "R": g("legR")}
        self.meta = stage.meta[name]
        self.head = [o for o in self.neck.children if o.data and len(o.data.vertices) == 517][0]
        self.heads = {}
        self.cur = None
        self.place(loc, yaw)
        self.face(1, expr)

    # -------------------------------------------------------------- placement
    def place(self, loc, yaw=0, f=None, z=None):
        x, y = loc[0], loc[1]
        if z is None:
            z = loc[2] if len(loc) > 2 else self.S.ground(x, y)
        self.root.location = (x, y, z)
        self.root.rotation_euler = (0, 0, math.pi + R(yaw))
        if f is not None:
            self.root.keyframe_insert("location", frame=f)
            self.root.keyframe_insert("rotation_euler", frame=f)
        return self

    def key_root(self, f, loc=None, yaw=None, tilt=None):
        if loc is not None:
            z = loc[2] if len(loc) > 2 else self.S.ground(loc[0], loc[1])
            self.root.location = (loc[0], loc[1], z)
            self.root.keyframe_insert("location", frame=f)
        if yaw is not None or tilt is not None:
            r = self.root.rotation_euler
            if yaw is not None:
                r.z = math.pi + R(yaw)
            if tilt is not None:
                r.x = R(tilt)
            self.root.keyframe_insert("rotation_euler", frame=f)

    @property
    def pos(self):
        return Vector(self.root.location)

    def world(self, local):
        """Point in the character's frame (x right, y forward, z up, studs from feet) -> world."""
        yaw = self.root.rotation_euler.z - math.pi
        lx, ly, lz = local
        # forward is -Y at yaw 0
        fx, fy = math.sin(yaw), -math.cos(yaw)
        rx, ry = -math.cos(yaw), -math.sin(yaw)  # character's right
        p = self.pos
        return Vector((p.x + rx * lx + fx * ly, p.y + ry * lx + fy * ly, p.z + lz))

    def head_pt(self):
        return self.world((0, 0, self.meta["shoulder"] + 0.6))

    def chest_pt(self):
        return self.world((0, 0, self.meta["shoulder"] - 0.9))

    def wrist_pt(self, side="L"):
        x = -1.5 if side == "L" else 1.5
        return self.world((x, 0, self.meta["shoulder"] - self.meta["arm_len"] + 0.35))

    # -------------------------------------------------------------- pose
    def arm(self, side, f, fwd=0.0, out=0.0, twist=0.0):
        o = self.arms[side]
        o.rotation_euler = (R(fwd), R(-out if side == "R" else out), R(twist))
        o.keyframe_insert("rotation_euler", frame=f)

    def leg(self, side, f, fwd=0.0, out=0.0):
        o = self.legs[side]
        o.rotation_euler = (R(fwd), R(-out if side == "R" else out), 0)
        o.keyframe_insert("rotation_euler", frame=f)

    def look(self, f, yaw=0.0, pitch=0.0, roll=0.0):
        """yaw>0 turns the head to the character's left; pitch>0 looks up."""
        self.neck.rotation_euler = (R(pitch), R(roll), R(yaw))
        self.neck.keyframe_insert("rotation_euler", frame=f)

    def lean(self, f, fwd=0.0, side=0.0):
        self.body.rotation_euler = (R(-fwd), R(side), 0)
        self.body.keyframe_insert("rotation_euler", frame=f)

    def rest(self, f):
        for s in "LR":
            self.arm(s, f)
            self.leg(s, f)
        self.look(f)
        self.lean(f)

    def idle(self, f0, f1, amt=1.0, seed=None):
        rnd = random.Random(seed if seed is not None else hash(self.name) % 999)
        f = f0
        while f <= f1:
            self.look(f, rnd.uniform(-8, 8) * amt, rnd.uniform(-4, 4) * amt)
            for s in "LR":
                self.arm(s, f, rnd.uniform(-4, 6) * amt, rnd.uniform(0, 5) * amt)
            f += STEP * 2

    def walk(self, f0, f1, to, swing=30, arms=True):
        start = self.pos.copy()
        self.key_root(f0, start)
        self.key_root(f1, to)
        for fc in self.root.animation_data.action.fcurves:
            if fc.data_path == "location":
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        k, f = 0, f0
        while f <= f1:
            a = swing if k % 2 else -swing
            self.leg("L", f, a)
            self.leg("R", f, -a)
            if arms:
                self.arm("L", f, -a * 0.8)
                self.arm("R", f, a * 0.8)
            f += STEP
            k += 1
        self.leg("L", f1 + 1, 0)
        self.leg("R", f1 + 1, 0)

    def run(self, f0, f1, to):
        self.walk(f0, f1, to, swing=55)
        f = f0
        while f <= f1:
            self.lean(f, 12)
            f += STEP

    def point(self, f, side="R", up=0):
        self.arm(side, f, 90 + up)

    def sit(self, f, seat_z=None):
        for s in "LR":
            self.leg(s, f, 90)
        if seat_z is not None:
            p = self.pos
            self.key_root(f, (p.x, p.y, seat_z - 0.05))

    def lie(self, f, face_down=True):
        """Flat on the ground (pivot at feet): tilt the whole rig 90 deg."""
        self.key_root(f, tilt=-90 if face_down else 90)

    # -------------------------------------------------------------- face
    def _head_for(self, expr):
        if expr in self.heads:
            return self.heads[expr]
        path = self.S.faces / self.name / f"{expr}.png"
        if not path.exists():
            path = self.S.faces / self.name / "smile.png"
        if not self.heads:
            h = self.head
        else:
            h = self.head.copy()
            bpy.context.scene.collection.objects.link(h)
            h.parent = self.head.parent
            h.matrix_parent_inverse = self.head.matrix_parent_inverse.copy()
            h.matrix_basis = self.head.matrix_basis.copy()
        m = self.head.active_material.copy()
        m.node_tree.nodes["FACE"].image = bpy.data.images.load(str(path), check_existing=True)
        h.material_slots[0].link = "OBJECT"
        h.material_slots[0].material = m
        self.heads[expr] = h
        return h

    def face(self, f, expr):
        h = self._head_for(expr)
        for e, o in self.heads.items():
            o.hide_render = o is not h
            o.keyframe_insert("hide_render", frame=f)
        self.cur = expr

    def faces(self, seq):
        """seq = [(frame, expr), ...]"""
        for f, e in seq:
            self.face(f, e)

    def talk(self, f0, f1, base=None):
        base = base or self.cur or "neutral"
        self._head_for("talk")
        self._head_for(base)
        f, k = f0, 0
        while f <= f1:
            self.face(f, "talk" if k % 2 == 0 else base)
            f += STEP
            k += 1
        self.face(f1 + 1, base)

    # -------------------------------------------------------------- props
    def mark(self, kind, side="L", glow=0.0, lift=0.006, size=0.7, dz=0.4, hidden=False):
        """Wrist mark on the front of the forearm. kind: leaf|claw|crown|marker|streaks."""
        p = self.S.decal(kind, self.arms[side], self, side, glow, size=size, lift=lift, dz=dz)
        if hidden:
            self.S.show(p, 1, False)
        return p


class Stage:
    def __init__(self, slug, light="day", sets=("SETS",)):
        self.slug = slug
        self.dir = ROOT / "output" / "models" / slug
        self.meta = json.loads((self.dir / "assets.json").read_text())
        self.faces = self.dir / "faces"
        kit.reset()
        sc = bpy.context.scene
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"
        sc.view_settings.exposure = 0.0
        sc.eevee.bloom_intensity = 0.04
        with bpy.data.libraries.load(str(self.dir / "assets.blend"), link=False) as (src, dst):
            dst.collections = [c for c in src.collections]
        for c in dst.collections:
            if c.name == "SETS" or c.name.startswith("CH_"):
                if c.name == "SETS" and "SETS" not in sets:
                    continue
                sc.collection.children.link(c)
        missing = set()
        for img in bpy.data.images:
            f = self.dir / Path(img.filepath.replace("//", "")).name
            if f.exists():
                img.filepath = str(f)
                img.reload()
            else:
                missing.add(img.name)
        for m in bpy.data.materials:  # drop texture nodes whose file is missing (they'd render pink)
            if m.use_nodes:
                for nd in list(m.node_tree.nodes):
                    if nd.type == "TEX_IMAGE" and nd.image and nd.image.name in missing:
                        m.node_tree.nodes.remove(nd)
                for nd in list(m.node_tree.nodes):
                    if nd.type == "NORMAL_MAP" and not nd.inputs["Color"].is_linked:
                        m.node_tree.nodes.remove(nd)
        self._tint_sets()
        self.chars = {}
        self.light(light)
        self._decal_imgs = {}

    def _tint_sets(self):
        """Studio exports set textures as grey material maps; Roblox tints them with the part colour (Kd)."""
        kd, cur = {}, None
        mtl = next(self.dir.glob("*.mtl"), None)
        if mtl:
            for line in mtl.read_text(errors="ignore").splitlines():
                t = line.split()
                if t[:1] == ["newmtl"]:
                    cur = t[1]
                elif t[:1] == ["Kd"] and cur:
                    kd[cur] = tuple(float(v) for v in t[1:4])
        mats = {s.material for o in bpy.data.collections["SETS"].all_objects for s in o.material_slots if s.material}
        for m in mats:
            if not m.use_nodes:
                continue
            nt = m.node_tree
            b = next((nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED"), None)
            if not b:
                continue
            b.inputs["Roughness"].default_value = 0.8
            col = kd.get(m.name) or kd.get(m.name.split(".")[0])
            if col is None:
                continue
            link = next((l for l in nt.links if l.to_socket == b.inputs["Base Color"]), None)
            if not link:
                b.inputs["Base Color"].default_value = (*col, 1)
                continue
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs[0].default_value = 1.0
            # soften the material map (Roblox textures are subtle): tex' = 0.55 + 0.45 * tex
            soft = nt.nodes.new("ShaderNodeMix")
            soft.data_type = "RGBA"
            soft.inputs[0].default_value = 0.6
            soft.inputs[6].default_value = (1, 1, 1, 1)
            nt.links.new(link.from_socket, soft.inputs[7])
            nt.links.new(soft.outputs[2], mix.inputs[6])
            mix.inputs[7].default_value = (*[min(1.0, c * 1.15) for c in col], 1)
            nt.links.remove(link)
            nt.links.new(mix.outputs[2], b.inputs["Base Color"])

    # -------------------------------------------------------------- world
    def light(self, kind):
        L = {
            "day": dict(sky=(0.48, 0.68, 0.98), sky_e=1.0, sun=(55, 0, 30), sun_c=(1, 0.97, 0.9), sun_e=3.4),
            "morning": dict(sky=(0.62, 0.75, 0.95), sky_e=0.95, sun=(62, 0, 120), sun_c=(1, 0.88, 0.7), sun_e=3.2),
            "dusk": dict(sky=(0.55, 0.42, 0.55), sky_e=0.55, sun=(80, 0, -60), sun_c=(1, 0.55, 0.35), sun_e=2.2),
            "rain": dict(sky=(0.46, 0.5, 0.58), sky_e=0.75, sun=(40, 0, 20), sun_c=(0.8, 0.85, 0.95), sun_e=1.1),
            "sunset": dict(sky=(0.95, 0.62, 0.45), sky_e=0.8, sun=(75, 0, -50), sun_c=(1, 0.62, 0.35), sun_e=3.6),
            "dusty": dict(sky=(0.72, 0.66, 0.58), sky_e=0.8, sun=(50, 0, 40), sun_c=(1, 0.9, 0.75), sun_e=2.2),
        }[kind]
        w = bpy.data.worlds.new("w")
        bpy.context.scene.world = w
        w.use_nodes = True
        nt = w.node_tree
        bg = nt.nodes["Background"]
        bg.inputs[1].default_value = L["sky_e"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], ramp.inputs[0])
        sky = L["sky"]
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (*[min(1, c * 1.25 + 0.12) for c in sky], 1)
        ramp.color_ramp.elements[1].position = 0.6
        ramp.color_ramp.elements[1].color = (*[c * 0.75 for c in sky], 1)
        nt.links.new(ramp.outputs[0], bg.inputs[0])
        kit.sun(L["sun"], L["sun_c"], L["sun_e"], angle=4)
        self.kind = kind

    def ground(self, x, y, z0=200.0):
        dg = bpy.context.evaluated_depsgraph_get()
        origin = Vector((x, y, z0))
        for _ in range(12):
            hit, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(dg, origin, Vector((0, 0, -1)))
            if not hit:
                return 0.0
            ok = ob and any(c.name == "SETS" for c in ob.users_collection) and not ob.name.startswith(
                ("Lamp", "Awning", "Bus", "Boulder", "Root", "Swing", "Slide", "Lunch", "Tray", "Bench", "Trash",
                 "Seat", "Fountain", "Crown", "Mural"))
            if ok:
                return loc.z
            origin = loc - Vector((0, 0, 0.01))
        return 0.0

    def char(self, name, loc, yaw=0, expr="smile"):
        c = Char(self, name, loc, yaw, expr)
        self.chars[name] = c
        return c

    def hide_unused(self):
        """Hide characters that were not placed in this shot."""
        for n in self.meta:
            if n not in self.chars:
                bpy.data.collections["CH_" + n].hide_render = True

    def hide(self, *prefixes):
        for o in bpy.data.objects:
            if o.name.startswith(prefixes):
                o.hide_render = True

    # -------------------------------------------------------------- camera
    def cam(self, target, dist=8, yaw=0, height=None, lens=50, fstop=4.0, focus=None, roll=0):
        c = kit.camera(tuple(target), dist=dist, yaw=yaw, height=height, lens=lens * WIDEN, fstop=fstop, focus=focus)
        c.data.clip_start = 0.05
        c.data.clip_end = 2000
        self.camera = c
        return c

    def cam_at(self, loc, target, lens=50, fstop=4.0, focus=None):
        tgt = kit.empty(tuple(target), name="cam_target")
        d = bpy.data.cameras.new("cam")
        d.lens = lens * WIDEN
        d.sensor_fit = "VERTICAL"
        d.sensor_height = 24
        d.clip_start = 0.05
        d.clip_end = 2000
        c = bpy.data.objects.new("cam", d)
        bpy.context.collection.objects.link(c)
        c.location = loc
        con = c.constraints.new("TRACK_TO")
        con.target = tgt
        con.track_axis = "TRACK_NEGATIVE_Z"
        con.up_axis = "UP_Y"
        if fstop:
            d.dof.use_dof = True
            d.dof.aperture_fstop = fstop
            d.dof.focus_object = kit.empty(tuple(focus), name="focus") if focus is not None else tgt
        bpy.context.scene.camera = c
        self.camera = c
        return c

    def plate_view(self, plate, dist=2.5, up=0.4, side=0.0, lens=50, fstop=2.8, frame=1):
        """Camera looking straight at a wrist mark (evaluated at `frame`)."""
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        mw = plate.matrix_world
        n = (mw.to_3x3() @ Vector((0, 0, 1))).normalized()
        c = mw.translation
        sidev = n.cross(Vector((0, 0, 1)))
        sidev = sidev.normalized() if sidev.length > 1e-4 else Vector((1, 0, 0))
        loc = c + n * dist + Vector((0, 0, up)) + sidev * side
        return self.cam_at(loc, c, lens=lens, fstop=fstop)

    def shake(self, f0, f1, amp=0.25):
        c = self.camera
        base = Vector(c.location)
        rnd = random.Random(7)
        f = f0
        while f <= f1:
            c.location = base + Vector((rnd.uniform(-amp, amp), 0, rnd.uniform(-amp, amp)))
            c.keyframe_insert("location", frame=f)
            f += STEP
        c.location = base
        c.keyframe_insert("location", frame=f1 + 1)

    # -------------------------------------------------------------- effects
    def decal_img(self, kind):
        if kind not in self._decal_imgs:
            self._decal_imgs[kind] = bpy.data.images.load(str(self.dir / "decals" / f"{kind}.png"), check_existing=True)
        return self._decal_imgs[kind]

    def decal(self, kind, parent, char, side, glow=0.0, size=0.7, lift=0.006, dz=0.4):
        """A square image plate glued on the outer front of the forearm."""
        bpy.ops.mesh.primitive_plane_add(size=size)
        p = bpy.context.active_object
        p.name = f"mark_{char.name}_{kind}"
        m = bpy.data.materials.new(p.name)
        m.use_nodes = True
        m.blend_method = "HASHED"
        m.shadow_method = "NONE"
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = self.decal_img(kind)
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color" if "Emission Color" in b.inputs else "Emission"])
        b.inputs["Emission Strength"].default_value = glow
        p.data.materials.append(m)
        # place in the rig frame (char faces +Y in the rig's local space): front face of the arm, near the wrist
        arm = parent
        bpy.context.view_layer.update()
        meshes = [o for o in arm.children if o.type == "MESH" and len(o.data.vertices) == 42] or list(arm.children)
        mesh = meshes[0]
        lo = Vector([min((mesh.matrix_world @ Vector(c))[i] for c in mesh.bound_box) for i in range(3)])
        hi = Vector([max((mesh.matrix_world @ Vector(c))[i] for c in mesh.bound_box) for i in range(3)])
        # world front direction of the character
        yaw = char.root.rotation_euler.z - math.pi
        fwd = Vector((math.sin(yaw), -math.cos(yaw), 0))
        ctr = (lo + hi) / 2
        depth = mesh.dimensions.y / 2  # export is unrotated: local Y = arm depth
        p.location = Vector((ctr.x, ctr.y, lo.z + dz)) + fwd * (depth + lift)
        p.rotation_euler = (R(90), 0, yaw)
        bpy.context.view_layer.update()
        mw = p.matrix_world.copy()
        p.parent = arm
        p.matrix_parent_inverse = arm.matrix_world.inverted()
        p.matrix_world = mw
        p["glow"] = glow
        return p

    def glow(self, plate, f, strength):
        b = plate.active_material.node_tree.nodes["Principled BSDF"]
        b.inputs["Emission Strength"].default_value = strength
        b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)

    def show(self, obj, f, on=True):
        obj.hide_render = not on
        obj.keyframe_insert("hide_render", frame=f)

    def rain(self, frames, center, radius=10, n=500, height=12):
        """Falling streaks around center (re-randomised every held pose)."""
        m = kit.mat("rain", (0.8, 0.85, 0.95), emit=0.3, alpha=0.35)
        rnd = random.Random(3)
        drops = []
        for i in range(n):
            o = kit.box((0.03, 0.03, 0.9), (0, 0, 0), m, bevel=0)
            drops.append(o)
        import os
        rstep = int(os.environ.get("ITT_STEP", "0")) or STEP
        f = 1
        while f <= frames + STEP:
            for o in drops:
                o.location = (center[0] + rnd.uniform(-radius, radius), center[1] + rnd.uniform(-radius, radius),
                              center[2] + rnd.uniform(0, height))
                o.keyframe_insert("location", frame=f)
            f += rstep
        for o in drops:
            for fc in o.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
        return drops

    def dust(self, frames, center, radius=6, n=60, color=(0.75, 0.65, 0.5)):
        m = kit.mat("dust", color, alpha=0.55)
        rnd = random.Random(5)
        out = []
        for i in range(n):
            s = rnd.uniform(0.4, 1.4)
            o = kit.sphere(s, (center[0] + rnd.uniform(-radius, radius), center[1] + rnd.uniform(-radius, radius),
                               center[2] + rnd.uniform(0, 3)), m, seg=8)
            kit.key(o, 1, scale=(0.6, 0.6, 0.6))
            kit.key(o, frames, scale=(1.4, 1.4, 1.4), loc=tuple(Vector(o.location) + Vector((0, 0, rnd.uniform(0.5, 2)))))
            out.append(o)
        return out

    def flash_light(self, loc, f_on, f_off, color=(1, 0.9, 0.5), power=800):
        L = kit.point(loc, color, 0, radius=0.5)
        L.data.energy = 0
        L.data.keyframe_insert("energy", frame=max(1, f_on - 1))
        L.data.energy = power
        L.data.keyframe_insert("energy", frame=f_on)
        if f_off:
            L.data.energy = 0
            L.data.keyframe_insert("energy", frame=f_off)
        return L

    # -------------------------------------------------------------- output
    def render(self, out, frames, res=(540, 960), samples=8):
        self.hide_unused()
        kit.render(out, frames, res, samples, step=STEP)
