"""Blocky-toy 3D scene kit for animated stand-in shots (runs inside Blender).

Original characters/sets built from bevelled boxes: posable rigs with
expressive faces (blink, talk, smile/frown, brows), simple sets (town,
lighthouse, sea, houses, rooms, fair), cinematic lighting presets and
keyframed motions. Used by tools/animate.py; real Roblox Studio recordings
in raw/<slug>/ always replace these clips.
"""
from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

FPS = 30
R = math.radians

# ------------------------------------------------------------------ scene

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    ee = sc.eevee
    ee.taa_render_samples = 24
    ee.use_gtao = True
    ee.gtao_distance = 1.5
    ee.use_bloom = True
    ee.bloom_intensity = 0.06
    ee.bloom_threshold = 0.9
    ee.use_soft_shadows = True
    ee.shadow_cube_size = "1024"
    ee.shadow_cascade_size = "2048"
    ee.use_ssr = False
    sc.render.fps = FPS
    sc.view_settings.view_transform = "Filmic"
    sc.view_settings.look = "High Contrast"
    sc.view_settings.exposure = -0.35
    sc.render.film_transparent = False
    return sc


_mats: dict = {}


def mat(name, color, rough=0.55, emit=0.0, emit_color=None, metal=0.0, alpha=1.0):
    key = (name, tuple(color), rough, emit, alpha)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
        m.shadow_method = "NONE"
        m.show_transparent_back = False
    _mats[key] = m
    return m


def glow_mat(name, color, strength=4.0, alpha=1.0):
    """Pure emission, optionally see-through (light beams)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    if alpha < 1:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        # soft edges: strongest where the surface faces the camera, fading to 0 at silhouettes
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.5
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(lw.outputs["Facing"], inv.inputs[1])
        pw = nt.nodes.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = 3.0
        nt.links.new(inv.outputs[0], pw.inputs[0])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = alpha
        nt.links.new(pw.outputs[0], mul.inputs[0])
        nt.links.new(mul.outputs[0], mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
        m.blend_method = "BLEND"
        m.shadow_method = "NONE"
    else:
        nt.links.new(em.outputs[0], out.inputs[0])
    return m


def _finish(o, material, bevel, parent):
    if material:
        o.data.materials.append(material)
    if bevel:
        mod = o.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = "NONE"
    if parent:
        o.parent = parent
    for p in o.data.polygons:
        p.use_smooth = bool(bevel) or len(o.data.polygons) > 40
    return o


def box(size, loc=(0, 0, 0), material=None, bevel=0.06, parent=None, rot=(0, 0, 0), name="box"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(o, material, bevel, parent)


def cyl(r, h, loc=(0, 0, 0), material=None, verts=24, parent=None, rot=(0, 0, 0), r2=None, bevel=0.0, name="cyl", caps=True):
    fill = "NGON" if caps else "NOTHING"
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc, rotation=[R(a) for a in rot], end_fill_type=fill)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=h, vertices=verts, location=loc, rotation=[R(a) for a in rot], end_fill_type=fill)
    o = bpy.context.object
    o.name = name
    return _finish(o, material, bevel, parent)


def sphere(r, loc=(0, 0, 0), material=None, parent=None, scale=(1, 1, 1), seg=16, name="sph"):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    _finish(o, material, 0, parent)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def torus(R_, r, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0), name="tor"):
    bpy.ops.mesh.primitive_torus_add(major_radius=R_, minor_radius=r, location=loc, rotation=[R(a) for a in rot],
                                     major_segments=32, minor_segments=8)
    o = bpy.context.object
    o.name = name
    _finish(o, material, 0, parent)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def empty(loc=(0, 0, 0), parent=None, name="pivot"):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = loc
    if parent:
        o.parent = parent
    return o


def key(obj, frame, **kw):
    """key(obj, f, rot=(x,y,z) deg | loc=(..) | scale=(..))"""
    if "rot" in kw:
        obj.rotation_euler = [R(a) for a in kw["rot"]]
        obj.keyframe_insert("rotation_euler", frame=frame)
    if "loc" in kw:
        obj.location = kw["loc"]
        obj.keyframe_insert("location", frame=frame)
    if "scale" in kw:
        obj.scale = kw["scale"]
        obj.keyframe_insert("scale", frame=frame)


def smooth_all():
    for a in bpy.data.actions:
        for fc in a.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.easing = "AUTO"


# ------------------------------------------------------------------ world + light

SKIES = {
    "sunset": [(0.0, (0.98, 0.55, 0.25)), (0.18, (0.95, 0.42, 0.35)), (0.45, (0.42, 0.30, 0.55)), (1.0, (0.10, 0.12, 0.32))],
    "golden": [(0.0, (1.0, 0.75, 0.40)), (0.3, (0.95, 0.70, 0.55)), (1.0, (0.35, 0.55, 0.85))],
    "day": [(0.0, (0.85, 0.92, 1.0)), (1.0, (0.30, 0.55, 0.95))],
    "morning": [(0.0, (1.0, 0.88, 0.70)), (0.4, (0.70, 0.82, 0.98)), (1.0, (0.35, 0.58, 0.92))],
    "dusk": [(0.0, (0.85, 0.50, 0.40)), (0.3, (0.40, 0.32, 0.50)), (1.0, (0.10, 0.10, 0.25))],
    "night": [(0.0, (0.10, 0.14, 0.30)), (1.0, (0.01, 0.02, 0.07))],
}


SKY = {  # Nishita physical sky: sun elevation (deg), rotation, strength, tint
    "sunset": (2.0, 200, 0.35, (1.0, 0.85, 0.8)),
    "golden": (8.0, 200, 0.3, (1.0, 0.92, 0.85)),
    "morning": (18.0, 140, 0.22, (1.0, 0.98, 0.95)),
    "day": (45.0, 160, 0.18, (1, 1, 1)),
    "dusk": (-1.5, 200, 0.6, (0.8, 0.75, 1.0)),
    "night": (-6.0, 200, 0.0, (1, 1, 1)),
}


def world(sky="sunset", strength=1.0, fog=0.0, fog_color=(0.8, 0.85, 1.0)):
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    elev, rot, st, tint = SKY[sky]
    if sky == "night":
        # deep blue gradient by view height + faint stars
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(tc.outputs["Window"], sep.inputs[0])
        nt.links.new(sep.outputs["Y"], ramp.inputs[0])
        ramp.color_ramp.elements[0].color = (0.05, 0.08, 0.2, 1)
        ramp.color_ramp.elements[1].color = (0.005, 0.01, 0.04, 1)
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 260
        vec = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(vec.outputs["Window"], vor.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs[1].default_value = 0.0
        mr.inputs[2].default_value = 0.04
        mr.inputs[3].default_value = 1.2
        mr.inputs[4].default_value = 0.0
        nt.links.new(vor.outputs["Distance"], mr.inputs[0])
        add = nt.nodes.new("ShaderNodeMix")
        add.data_type = "RGBA"
        add.blend_type = "ADD"
        add.inputs[0].default_value = 1.0
        nt.links.new(ramp.outputs[0], add.inputs[6])
        nt.links.new(mr.outputs[0], add.inputs[7])
        nt.links.new(add.outputs[2], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = 1.0 * strength
    else:
        sk = nt.nodes.new("ShaderNodeTexSky")
        sk.sky_type = "NISHITA"
        sk.sun_elevation = R(max(elev, -2))
        sk.sun_rotation = R(rot)
        sk.sun_disc = elev > 0
        sk.air_density = 1.4
        sk.dust_density = 2.5 if sky in ("sunset", "golden", "dusk") else 1.0
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(sk.outputs[0], mix.inputs[6])
        nt.links.new(mix.outputs[2], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = st * strength
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    if fog:
        vol = nt.nodes.new("ShaderNodeVolumeScatter")
        vol.inputs["Density"].default_value = fog
        vol.inputs["Color"].default_value = (*fog_color, 1)
        nt.links.new(vol.outputs[0], out.inputs["Volume"])
        ee = bpy.context.scene.eevee
        ee.use_volumetric_lights = True
        ee.volumetric_tile_size = "16"
        ee.volumetric_samples = 32
        ee.volumetric_end = 150
    return w


def sun(rot=(60, 0, 40), color=(1, 0.8, 0.6), strength=3.0, angle=3.0):
    d = bpy.data.lights.new("sun", "SUN")
    d.energy = strength
    d.color = color
    d.angle = R(angle)
    o = bpy.data.objects.new("sun", d)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = [R(a) for a in rot]
    return o


def point(loc, color=(1, 0.75, 0.45), power=300, radius=0.3):
    d = bpy.data.lights.new("pt", "POINT")
    d.energy = power
    d.color = color
    d.shadow_soft_size = radius
    o = bpy.data.objects.new("pt", d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    return o


def spot(loc, target, color=(1, 0.95, 0.8), power=3000, size=25, blend=0.4, radius=0.2):
    d = bpy.data.lights.new("spot", "SPOT")
    d.energy = power
    d.color = color
    d.spot_size = R(size)
    d.spot_blend = blend
    d.shadow_soft_size = radius
    o = bpy.data.objects.new("spot", d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    aim(o, target)
    return o


def aim(o, target):
    d = Vector(target) - Vector(o.location)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


LIGHTING = {
    "sunset": dict(sky="sunset", sun_rot=(76, 0, -50), sun_col=(1.0, 0.6, 0.32), sun_e=4.6, world_e=1.0),
    "golden": dict(sky="golden", sun_rot=(70, 0, -40), sun_col=(1.0, 0.78, 0.5), sun_e=3.5, world_e=1.0),
    "morning": dict(sky="morning", sun_rot=(55, 0, 35), sun_col=(1.0, 0.9, 0.75), sun_e=3.0, world_e=0.9),
    "day": dict(sky="day", sun_rot=(45, 0, 30), sun_col=(1, 0.97, 0.92), sun_e=2.6, world_e=0.8),
    "dusk": dict(sky="dusk", sun_rot=(84, 0, -60), sun_col=(0.9, 0.5, 0.4), sun_e=1.6, world_e=0.6),
    "night": dict(sky="night", sun_rot=(50, 0, 140), sun_col=(0.55, 0.65, 1.0), sun_e=0.55, world_e=0.9),
}


def lighting(kind="sunset", fog=0.0):
    L = LIGHTING[kind]
    world(L["sky"], L["world_e"], fog=fog, fog_color=(0.75, 0.8, 1.0) if kind == "night" else (1, 0.9, 0.8))
    sun(L["sun_rot"], L["sun_col"], L["sun_e"])
    if kind == "night":
        sun((40, 0, 200), (0.45, 0.55, 0.95), 0.8, 10)  # soft moon fill


# ------------------------------------------------------------------ camera

def camera(target, dist=8, height=None, yaw=0, lens=50, fstop=2.8, dolly=0.06, frames=60, focus=None, pitch_off=0.0):
    """Camera looking at target from yaw (0 = from -Y). dolly: fraction moved closer over the shot."""
    tgt = empty(target, name="cam_target")
    tgt.location.z += pitch_off
    d = bpy.data.cameras.new("cam")
    d.lens = lens
    d.sensor_fit = "VERTICAL"
    d.sensor_height = 24
    d.clip_end = 600
    cam = bpy.data.objects.new("cam", d)
    bpy.context.collection.objects.link(cam)
    h = target[2] if height is None else height
    a = R(yaw)
    p0 = Vector((target[0] + dist * math.sin(a), target[1] - dist * math.cos(a), h))
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    cam.location = p0
    if dolly:
        key(cam, 1, loc=p0)
        p1 = p0.lerp(Vector(tgt.location), dolly)
        key(cam, frames, loc=p1)
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    d.dof.use_dof = fstop is not None
    if fstop:
        d.dof.aperture_fstop = fstop
        if focus is not None:
            d.dof.focus_object = empty(focus, name="focus")
        else:
            d.dof.focus_object = tgt
    bpy.context.scene.camera = cam
    return cam


# ------------------------------------------------------------------ characters

SKIN = [(0.98, 0.80, 0.62), (0.80, 0.58, 0.40), (0.55, 0.37, 0.25), (1.0, 0.86, 0.72)]
BLACK = (0.02, 0.02, 0.025)

PEOPLE = {
    "narrator": dict(skin=0, shirt=(0.20, 0.45, 0.85), pants=(0.15, 0.17, 0.25), hair=(0.30, 0.18, 0.10), hair_style="short", scale=0.86),
    "june": dict(skin=0, shirt=(1.0, 0.80, 0.25), pants=(0.95, 0.55, 0.65), hair=(0.55, 0.32, 0.15), hair_style="pigtails", scale=0.68),
    "mom": dict(skin=0, shirt=(0.35, 0.70, 0.55), pants=(0.25, 0.25, 0.40), hair=(0.40, 0.22, 0.12), hair_style="long", scale=1.0),
    "dad": dict(skin=0, shirt=(0.75, 0.22, 0.20), pants=(0.25, 0.30, 0.45), hair=(0.25, 0.15, 0.08), hair_style="short", scale=1.05, beard=False),
    "tommy": dict(skin=1, shirt=(0.95, 0.45, 0.20), pants=(0.25, 0.35, 0.65), hair=(0.08, 0.06, 0.05), hair_style="short", scale=0.66),
    "alder": dict(skin=3, shirt=(0.58, 0.40, 0.70), pants=(0.40, 0.30, 0.50), hair=(0.80, 0.80, 0.82), hair_style="bun", scale=0.95, glasses=True),
    "pell": dict(skin=0, shirt=(0.12, 0.18, 0.35), pants=(0.12, 0.14, 0.22), hair=(0.92, 0.92, 0.92), hair_style="short", scale=1.02, beard=True, hat="captain"),
    "towny": dict(skin=2, shirt=(0.30, 0.65, 0.35), pants=(0.30, 0.25, 0.20), hair=(0.05, 0.04, 0.03), hair_style="short", scale=1.0, hat="cap"),
}


class Char:
    """Posable blocky character. Root at feet, faces -Y (towards a camera at yaw 0)."""

    def __init__(self, who, loc=(0, 0, 0), yaw=0, expr="neutral", **over):
        spec = {**PEOPLE[who], **over}
        self.who = who
        s = spec["scale"]
        skin = mat("skin" + str(spec["skin"]), SKIN[spec["skin"]], 0.5)
        shirt = mat(who + "_shirt", spec["shirt"], 0.7)
        pants = mat(who + "_pants", spec["pants"], 0.75)
        hairm = mat(who + "_hair", spec["hair"], 0.6)
        shoe = mat("shoe", (0.12, 0.10, 0.09), 0.6)
        black = mat("black", BLACK, 0.3)
        white = mat("white", (1, 1, 1), 0.2, emit=0.6)
        self.root = empty(loc, name=who)
        self.root.rotation_euler = (0, 0, R(yaw))
        self.root.scale = (s, s, s)
        self.base_loc = Vector(loc)
        self.yaw = yaw
        rt = self.root
        # legs
        self.legL = empty((-0.5, 0, 2.0), rt, "legL")
        self.legR = empty((0.5, 0, 2.0), rt, "legR")
        for lg in (self.legL, self.legR):
            box((0.96, 0.96, 1.75), (0, 0, -0.9), pants, 0.08, lg)
            box((0.98, 1.1, 0.3), (0, -0.06, -1.86), shoe, 0.08, lg)
        # torso (pivot at hips so it can lean)
        self.hip = empty((0, 0, 2.0), rt, "hip")
        self.body = empty((0, 0, 0), self.hip, "body")  # idle layer (breathing sway)
        box((2.0, 1.0, 2.0), (0, 0, 1.0), shirt, 0.12, self.body)
        # arms
        self.armL = empty((-1.5, 0, 1.85), self.body, "armL")
        self.armR = empty((1.5, 0, 1.85), self.body, "armR")
        for side, arm in ((-1, self.armL), (1, self.armR)):
            box((0.92, 0.95, 0.95), (side * -0.02, 0, -0.42), shirt, 0.1, arm)
            box((0.86, 0.88, 1.05), (side * -0.02, 0, -1.35), skin, 0.12, arm)
        self.handL = empty((0, -0.1, -1.85), self.armL, "handL")
        self.handR = empty((0, -0.1, -1.85), self.armR, "handR")
        # head
        self.neck = empty((0, 0, 2.0), self.body, "neck")
        self.hd = empty((0, 0, 0), self.neck, "headbob")  # idle layer for the head
        hd = self.hd
        self.head = box((1.3, 1.2, 1.25), (0, 0, 0.68), skin, 0.28, hd, name="head")
        # eyes
        self.eyes = []
        for x in (-0.27, 0.27):
            e = sphere(0.1, (x, -0.6, 0.78), black, hd, scale=(0.95, 0.4, 1.45))
            sphere(0.035, (x - 0.035, -0.63, 0.84), white, hd)
            self.eyes.append(e)
        # brows
        bm = mat(who + "_brow", tuple(c * 0.6 for c in spec["hair"]), 0.6)
        self.browL = box((0.26, 0.06, 0.06), (-0.27, -0.6, 1.06), bm, 0.02, hd)
        self.browR = box((0.26, 0.06, 0.06), (0.27, -0.6, 1.06), bm, 0.02, hd)
        # mouth: smile curve + open mouth
        self.mouth = self._mouth_curve(hd, black, expr)
        self.mouth_open = sphere(0.12, (0, -0.6, 0.42), mat("mouthin", (0.25, 0.05, 0.06), 0.4), hd, scale=(1.2, 0.35, 0.05))
        # cheeks (blush, cute)
        blush = mat("blush", (1.0, 0.55, 0.55), 0.6, alpha=0.55)
        for x in (-0.45, 0.45):
            sphere(0.09, (x, -0.59, 0.55), blush, hd, scale=(1.3, 0.2, 0.8))
        self._hair(hd, hairm, spec)
        if spec.get("glasses"):
            gm = mat("glassframe", (0.15, 0.1, 0.08), 0.3)
            self.glasses = empty((0, 0, 0), hd, "glasses")
            for x in (-0.27, 0.27):
                torus(0.17, 0.025, (x, -0.66, 0.78), gm, self.glasses, rot=(90, 0, 0))
            box((0.2, 0.03, 0.03), (0, -0.66, 0.8), gm, 0, self.glasses)
        if spec.get("beard"):
            box((1.2, 0.3, 0.5), (0, -0.52, 0.22), hairm, 0.12, hd)
            box((0.7, 0.12, 0.14), (0, -0.66, 0.5), hairm, 0.05, hd)  # moustache
        if spec.get("hat") == "captain":
            cyl(0.75, 0.35, (0, 0, 1.48), mat("hatwhite", (0.95, 0.95, 0.92), 0.5), parent=hd, r2=0.68)
            cyl(0.72, 0.12, (0, 0, 1.3), mat("hatband", (0.05, 0.06, 0.12), 0.4), parent=hd)
            box((0.9, 0.5, 0.06), (0, -0.62, 1.27), mat("visor", (0.03, 0.03, 0.04), 0.2), 0.02, hd, rot=(-15, 0, 0))
            sphere(0.08, (0, -0.72, 1.45), mat("gold", (1, 0.75, 0.2), 0.3, metal=1.0), hd)
        elif spec.get("hat") == "cap":
            cyl(0.7, 0.35, (0, 0, 1.38), shirt, parent=hd)
            box((0.9, 0.6, 0.06), (0, -0.7, 1.25), shirt, 0.02, hd)
        self.expr = expr
        self.expression(expr)
        self.blink_seed = random.Random(hash(who) & 0xffff)

    # --- face
    def _mouth_curve(self, parent, material, expr):
        cu = bpy.data.curves.new("mouth", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.035
        cu.bevel_resolution = 3
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        o = bpy.data.objects.new("mouth", cu)
        bpy.context.collection.objects.link(o)
        o.parent = parent
        o.data.materials.append(material)
        return o

    def expression(self, expr):
        curve = {"happy": 0.1, "smile": 0.06, "small_smile": 0.035, "neutral": 0.0, "blank": 0.0, "sad": -0.07,
                 "surprised": 0.0, "sleepy": 0.02, "worried": -0.04, "embarrassed": 0.05, "wise": 0.05, "confused": -0.02}.get(expr, 0)
        w = 0.2 if expr != "blank" else 0.14
        pts = self.mouth.data.splines[0].bezier_points
        for p, (x, z) in zip(pts, [(-w, 0.42 + curve), (0, 0.42 - curve * 0.6), (w, 0.42 + curve)]):
            p.co = (x, -0.63, z)
            p.handle_left_type = p.handle_right_type = "AUTO"
        self.mouth.hide_render = expr == "surprised"
        self.mouth_open.scale = (1.2, 0.35, 0.9 if expr == "surprised" else 0.05)
        tilt = {"sad": 14, "worried": 18, "surprised": 0, "confused": -10}.get(expr, 0)
        lift = {"surprised": 0.12, "sad": 0.02, "worried": 0.04, "happy": 0.05}.get(expr, 0.0)
        self.browL.rotation_euler = (0, R(-tilt), 0)
        self.browR.rotation_euler = (0, R(tilt), 0)
        if expr == "confused":
            self.browR.rotation_euler = (0, R(-12), 0)
        self.browL.location.z = 1.06 + lift
        self.browR.location.z = 1.06 + lift
        eye_z = 0.25 if expr == "sleepy" else (1.0 if expr != "happy" else 0.6)
        for e in self.eyes:
            e.scale = (0.95, 0.4, 1.45 * eye_z)
        self.expr = expr

    def _hair(self, hd, hm, spec):
        st = spec["hair_style"]
        if spec.get("hat") == "captain":
            box((1.36, 1.26, 0.5), (0, 0.06, 1.0), hm, 0.15, hd)
            return
        box((1.42, 1.3, 0.42), (0, 0.04, 1.27), hm, 0.18, hd)            # top
        box((1.42, 0.5, 0.95), (0, 0.42, 0.85), hm, 0.15, hd)            # back
        box((0.18, 1.0, 0.55), (-0.66, 0.1, 1.0), hm, 0.08, hd)          # sides
        box((0.18, 1.0, 0.55), (0.66, 0.1, 1.0), hm, 0.08, hd)
        box((1.1, 0.25, 0.22), (0.1, -0.55, 1.2), hm, 0.08, hd)          # fringe
        if st == "long":
            box((1.5, 0.55, 1.9), (0, 0.42, 0.25), hm, 0.18, hd)
        elif st == "pigtails":
            for x in (-0.85, 0.85):
                sphere(0.32, (x, 0.2, 0.75), hm, hd, scale=(0.9, 0.9, 1.3))
                sphere(0.1, (x * 0.85, 0.15, 1.05), mat("bow", (1, 0.35, 0.5), 0.5), hd)
        elif st == "bun":
            sphere(0.42, (0, 0.35, 1.55), hm, hd)

    # --- helpers
    def head_world(self):
        return self.root.matrix_world @ Vector((0, 0, 4.7)) if False else Vector(self.base_loc) + Vector((0, 0, 4.7 * self.root.scale[2]))

    def chest(self):
        return Vector(self.base_loc) + Vector((0, 0, 3.0 * self.root.scale[2]))

    def eye_level(self):
        return Vector(self.base_loc) + Vector((0, 0, 4.75 * self.root.scale[2]))

    # --- motion primitives (frames are 1-based, inclusive)
    def idle(self, f0, f1, sway=1.0):
        rnd = self.blink_seed
        for f in range(f0, f1 + 1, 20):
            ph = f / 20.0
            key(self.body, f, rot=(sway * 1.2 * math.sin(ph * 1.3), 0, sway * 1.5 * math.sin(ph * 0.7)))
            key(self.hd, f, rot=(sway * 2.5 * math.sin(ph * 0.9 + 1), sway * 2 * math.sin(ph * 0.6), sway * 4 * math.sin(ph * 0.5)))
        # blinks
        f = f0 + rnd.randint(10, 40)
        while f < f1 - 6:
            for e in self.eyes:
                z = e.scale[2]
                key(e, f - 1, scale=(e.scale[0], e.scale[1], z))
                key(e, f + 1, scale=(e.scale[0], e.scale[1], 0.08))
                key(e, f + 4, scale=(e.scale[0], e.scale[1], z))
            f += rnd.randint(55, 110)

    def talk(self, f0, f1):
        o = self.mouth_open
        rnd = random.Random(f0)
        f = f0
        while f < f1:
            key(o, f, scale=(1.2, 0.35, rnd.choice([0.35, 0.6, 0.85, 0.5])))
            key(o, f + 3, scale=(1.2, 0.35, 0.05))
            f += rnd.randint(5, 8)

    def arm(self, side, f, rot):
        key(self.armL if side == "L" else self.armR, f, rot=rot)

    def arms(self, f, l=(0, 0, 0), r=(0, 0, 0)):
        self.arm("L", f, l)
        self.arm("R", f, r)

    def legs(self, f, l=(0, 0, 0), r=(0, 0, 0)):
        key(self.legL, f, rot=l)
        key(self.legR, f, rot=r)

    def sit_at(self, x, y, surface_z, f=1):
        """Sit with hips resting on a surface at height surface_z (legs forward)."""
        s = self.root.scale[2]
        self.base_loc = Vector((x, y, surface_z - 1.52 * s))
        self.root.location = self.base_loc
        key(self.root, f, loc=tuple(self.base_loc))
        self.legs(f, (-90, 0, 0), (-90, 0, 0))

    def lie_at(self, x, y, surface_z, f=1):
        """Lie face-up on a surface, feet at (x, y), head towards +Y."""
        s = self.root.scale[2]
        self.root.location = (x, y, surface_z + 0.5 * s)
        self.root.rotation_euler = (R(-90), 0, 0)
        key(self.root, f, loc=tuple(self.root.location), rot=(-90, 0, 0))

    def walk(self, f0, f1, to, step=14, swing=28, arms=True):
        """Walk from current location to `to` (world xy)."""
        key(self.root, f0, loc=tuple(self.base_loc))
        key(self.root, f1, loc=(to[0], to[1], self.base_loc.z))
        for fc in self.root.animation_data.action.fcurves:
            if fc.data_path == "location":
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        for f in range(f0, f1 + 1, step // 2):
            s = 1 if ((f - f0) // (step // 2)) % 2 == 0 else -1
            self.legs(f, (s * swing, 0, 0), (-s * swing, 0, 0))
            if arms:
                self.arms(f, (-s * swing * 0.8, 0, 0), (s * swing * 0.8, 0, 0))
            key(self.hip, f, loc=(0, 0, 2.0 + (0.08 if s > 0 else 0.0)))
        self.base_loc = Vector((to[0], to[1], self.base_loc.z))

    def tiptoe(self, f0, f1, to):
        self.walk(f0, f1, to, step=22, swing=16)
        for f in range(f0, f1 + 1, 11):
            self.arms(f, (-40, 0, 25), (-40, 0, -25))

    def wave(self, f0, f1, side="R"):
        sgn = 1 if side == "R" else -1
        for i, f in enumerate(range(f0, f1, 7)):
            self.arm(side, f, (0, sgn * (150 + (15 if i % 2 else -15)), 0))

    def nod(self, f, n=2):
        for i in range(n):
            key(self.neck, f + i * 10, rot=(0, 0, 0))
            key(self.neck, f + i * 10 + 5, rot=(-14, 0, 0))
        key(self.neck, f + n * 10, rot=(0, 0, 0))

    def look(self, f, yaw=0, pitch=0, roll=0):
        key(self.neck, f, rot=(pitch, roll, yaw))

    def look_around(self, f0, f1, amp=35):
        f, s = f0, 1
        while f < f1:
            self.look(f, s * amp, 5)
            f += 18
            s = -s

    def hold_forward(self, f, side="both", angle=-75):
        if side in ("both", "L"):
            self.arm("L", f, (angle, 0, 8))
        if side in ("both", "R"):
            self.arm("R", f, (angle, 0, -8))

    def raise_up(self, f, side="R", angle=-160):
        self.arm(side, f, (angle, 0, 0))

    def sit(self, f=1, seat_h=None):
        """Sitting pose: legs forward, root lowered so the hips rest on a seat."""
        self.legs(f, (-90, 0, 0), (-90, 0, 0))
        self.root.location.z = self.base_loc.z + (seat_h if seat_h is not None else 0) - 2.0 * self.root.scale[2] * 0.0
        key(self.root, f, loc=tuple(self.root.location))

    def lie(self, f=1, face_up=True):
        self.root.rotation_euler = (R(-90 if face_up else 90), 0, R(self.yaw))
        key(self.root, f, rot=(-90 if face_up else 90, 0, self.yaw))

    def head_in_hands(self, f0, f1):
        key(self.hip, f0, rot=(18, 0, 0))
        self.arms(f0, (-125, 0, 28), (-125, 0, -28))
        key(self.neck, f0, rot=(22, 0, 0))
        for f in range(f0 + 20, f1, 30):
            key(self.neck, f, rot=(26, 0, 3 * math.sin(f)))

    def shrug_goofy(self, f0, f1):
        f, s = f0, 1
        while f < f1:
            self.arms(f, (0, -150 if s > 0 else -60, 0), (0, 60 if s > 0 else 150, 0))
            key(self.hip, f, rot=(0, s * 10, 0))
            key(self.neck, f, rot=(0, -s * 14, 0))
            f += 9
            s = -s

    def knock(self, f0, f1, side="R"):
        for i, f in enumerate(range(f0, f1, 6)):
            self.arm(side, f, (-95 + (25 if i % 2 else 0), 0, 0))


# ------------------------------------------------------------------ props

def jar(loc, parent=None, glow=True):
    root = empty(loc, parent, "jar")
    glass = mat("glass", (0.85, 0.95, 1.0), 0.05, alpha=0.3)
    cyl(0.35, 0.8, (0, 0, 0.4), glass, parent=root)
    cyl(0.37, 0.12, (0, 0, 0.86), mat("lid", (0.7, 0.55, 0.3), 0.4, metal=0.6), parent=root)
    cols = [(0.2, 0.6, 1.0), (0.3, 0.9, 0.6), (0.6, 0.85, 1.0), (0.2, 0.8, 0.8), (1.0, 0.85, 0.5)]
    rnd = random.Random(3)
    for i in range(12):
        c = cols[i % len(cols)]
        box((0.16, 0.16, 0.12), (rnd.uniform(-0.18, 0.18), rnd.uniform(-0.18, 0.18), 0.12 + i * 0.045),
            mat(f"seaglass{i % 5}", c, 0.15, emit=1.5 if glow else 0.2, alpha=0.85), 0.04, root,
            rot=(rnd.uniform(0, 40), rnd.uniform(0, 40), rnd.uniform(0, 90)))
    if glow:
        p = point((0, 0, 0.45), (0.5, 0.85, 1.0), 25, 0.2)
        p.parent = root
    return root


def bunny(loc, parent=None, rot=(0, 0, 0)):
    root = empty(loc, parent, "bunny")
    root.rotation_euler = [R(a) for a in rot]
    m = mat("bunny", (0.95, 0.9, 0.95), 0.9)
    sphere(0.32, (0, 0, 0), m, root, scale=(1, 0.9, 1.1))
    sphere(0.25, (0, -0.05, 0.42), m, root)
    for x in (-0.1, 0.1):
        box((0.1, 0.06, 0.4), (x, 0, 0.75), m, 0.04, root)
        sphere(0.03, (x, -0.24, 0.47), mat("black", BLACK, 0.3), root)
    return root


def bike(loc, yaw=0):
    root = empty(loc, name="bike")
    root.rotation_euler = (0, 0, R(yaw))
    red = mat("bikered", (0.85, 0.12, 0.12), 0.35, metal=0.4)
    tire = mat("tire", (0.04, 0.04, 0.04), 0.8)
    for x in (-1.1, 1.1):
        torus(0.6, 0.08, (x, 0, 0.65), tire, root, rot=(90, 0, 0))
    cyl(0.06, 2.0, (0, 0, 1.15), red, parent=root, rot=(0, 90, 0))
    cyl(0.06, 1.1, (-0.55, 0, 0.9), red, parent=root, rot=(0, 50, 0))
    cyl(0.06, 1.1, (0.6, 0, 0.9), red, parent=root, rot=(0, -45, 0))
    box((0.5, 0.25, 0.1), (-0.5, 0, 1.45), mat("seat", (0.1, 0.1, 0.1), 0.6), 0.04, root)
    cyl(0.05, 1.0, (1.05, 0, 1.45), mat("bar", (0.6, 0.6, 0.65), 0.3, metal=1), parent=root, rot=(90, 0, 0))
    return root


def boxes_pile(loc, n=4, seed=1):
    rnd = random.Random(seed)
    m = mat("cardboard", (0.72, 0.52, 0.32), 0.85)
    tape = mat("tape", (0.85, 0.75, 0.55), 0.4)
    for i in range(n):
        x, y = loc[0] + rnd.uniform(-1.4, 1.4), loc[1] + rnd.uniform(-0.8, 0.8)
        s = rnd.uniform(0.9, 1.3)
        z = loc[2] + (s / 2 if i < 3 else 1.6)
        box((s * 1.2, s, s), (x, y, z), m, 0.03, rot=(0, 0, rnd.uniform(-20, 20)))
        box((0.15, s + 0.02, 0.02), (x, y, z + s / 2), tape, 0, rot=(0, 0, rnd.uniform(-20, 20)))


def pancakes(loc):
    for i in range(4):
        cyl(0.45, 0.12, (loc[0], loc[1], loc[2] + 0.07 + i * 0.12), mat("pancake", (0.85, 0.6, 0.3), 0.6), bevel=0.03)
    cyl(0.6, 0.05, (loc[0], loc[1], loc[2]), mat("plate", (0.95, 0.95, 0.95), 0.3))
    for x in (-0.15, 0.15):
        sphere(0.05, (loc[0] + x, loc[1] - 0.1, loc[2] + 0.56), mat("berry", (0.5, 0.1, 0.4), 0.3))


def newspaper(parent_hand, f=1):
    o = box((1.6, 0.04, 1.1), (0, -0.4, -0.2), mat("paper", (0.9, 0.88, 0.8), 0.9), 0.0, parent_hand)
    for i in range(5):
        box((1.2, 0.05, 0.05), (0, -0.43, 0.1 - i * 0.15), mat("ink", (0.3, 0.3, 0.3), 0.9), 0.0, parent_hand)
    return o


# ------------------------------------------------------------------ sets

def ground(size=200, color=(0.35, 0.55, 0.28), loc=(0, 0, 0)):
    return box((size, size, 0.2), (loc[0], loc[1], loc[2] - 0.1), mat("ground" + str(color), color, 0.9), 0)


def ocean(loc=(0, 60, -0.3), size=(400, 200), color=(0.08, 0.28, 0.45), frames=60):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=60, size=1, location=loc)
    o = bpy.context.object
    o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat("sea", color, 0.15, metal=0.0))
    for p in o.data.polygons:
        p.use_smooth = True
    w = o.modifiers.new("wave", "WAVE")
    w.height = 0.25
    w.width = 6
    w.speed = 0.15
    w.narrowness = 1.2
    return o


def house(loc, yaw=0, wall=(0.35, 0.55, 0.85), roof=(0.55, 0.25, 0.2), w=11, d=9, h=8, lit=False, porch=True, door_open=False):
    root = empty(loc, name="house")
    root.rotation_euler = (0, 0, R(yaw))
    wm = mat("wall" + str(wall), wall, 0.8)
    trim = mat("trim", (0.95, 0.93, 0.88), 0.6)
    box((w, d, h), (0, 0, h / 2), wm, 0.05, root)
    # gable roof: a real prism mesh with overhang
    rm = mat("roof" + str(roof), roof, 0.7)
    rh = w * 0.38
    ov = 0.6
    hw, hd = w / 2 + ov, d / 2 + ov
    verts = [(-hw, -hd, h), (hw, -hd, h), (0, -hd, h + rh), (-hw, hd, h), (hw, hd, h), (0, hd, h + rh)]
    faces = [(0, 1, 2), (5, 4, 3), (0, 2, 5, 3), (1, 4, 5, 2), (0, 3, 4, 1)]
    me = bpy.data.meshes.new("roof")
    me.from_pydata(verts, [], faces)
    ro = bpy.data.objects.new("roof", me)
    bpy.context.collection.objects.link(ro)
    ro.parent = root
    ro.data.materials.append(rm)
    sol = ro.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.3
    gv = [(-w / 2, -d / 2, h), (w / 2, -d / 2, h), (0, -d / 2, h + rh - 0.4), (-w / 2, d / 2, h), (w / 2, d / 2, h), (0, d / 2, h + rh - 0.4)]
    gme = bpy.data.meshes.new("gable")
    gme.from_pydata(gv, [], [(0, 1, 2), (5, 4, 3)])
    go = bpy.data.objects.new("gable", gme)
    bpy.context.collection.objects.link(go)
    go.parent = root
    go.data.materials.append(wm)
    go.modifiers.new("sol", "SOLIDIFY").thickness = 0.2
    # door + windows on the front (-Y)
    door_c = (0.45, 0.25, 0.15)
    door = box((2.2, 0.2, 4.2), (0, -d / 2 - 0.05, 2.5), mat("door", door_c, 0.6), 0.04, root)
    win = mat("winlit", (1.0, 0.75, 0.4), 0.3, emit=4.0) if lit else mat("win", (0.55, 0.7, 0.85), 0.1)
    wins = []
    wx = w * 0.32
    for x in (-wx, wx):
        box((2.6, 0.25, 2.3), (x, -d / 2 - 0.05, 4.6), trim, 0.03, root)
        wins.append(box((2.2, 0.3, 1.9), (x, -d / 2 - 0.06, 4.6), win, 0.0, root))
    if porch:
        box((w + 1, 3.2, 0.4), (0, -d / 2 - 1.6, 0.2), mat("porchwood", (0.55, 0.4, 0.28), 0.8), 0.03, root)
        for x in (-w / 2, w / 2):
            box((0.35, 0.35, 6.6), (x, -d / 2 - 3.0, 3.5), trim, 0.03, root)
        box((w + 1.2, 3.4, 0.3), (0, -d / 2 - 1.6, 7.0), rm, 0.03, root)
    if lit:
        p = point((0, -d / 2 - 1.8, 6.2), (1, 0.7, 0.4), 350, 0.4)
        p.parent = root
    return root, wins


def lighthouse(loc, beam_frames=None, beam_yaw=None, beam_alpha=0.14, scale=1.0, target=None, frames=60):
    """Striped lighthouse. beam_frames: (yaw0, yaw1) sweep over the shot; beam_yaw: fixed yaw; target: aim beam at point."""
    root = empty(loc, name="lighthouse")
    root.scale = (scale,) * 3
    red = mat("lhred", (0.85, 0.15, 0.12), 0.6)
    white = mat("lhwhite", (0.95, 0.95, 0.93), 0.6)
    for i in range(5):
        cyl(2.6 - i * 0.22, 3.0, (0, 0, 1.5 + i * 3.0), red if i % 2 == 0 else white, 32, root, r2=2.6 - (i + 1) * 0.22)
    top = 15.0
    cyl(2.0, 0.4, (0, 0, top + 0.2), mat("lhdark", (0.15, 0.15, 0.18), 0.5), 32, root)
    cyl(1.5, 2.2, (0, 0, top + 1.5), glow_mat("lamp", (1.0, 0.9, 0.6), 18), 24, root)
    cyl(1.9, 1.0, (0, 0, top + 3.0), red, 32, root, r2=0.2)
    lamp = point((0, 0, top + 1.5), (1, 0.85, 0.55), 4000, 1.0)
    lamp.parent = root
    pivot = empty((0, 0, top + 1.5), root, "beam_pivot")
    beam = cyl(1.2, 90, (0, -45, 0), glow_mat("beam", (1.0, 0.9, 0.65), 5.0, beam_alpha), 64, pivot, rot=(90, 0, 0), r2=7.0, caps=False)
    beam.location = (0, -45.6, 0)
    beam_light = spot((0, -1, 0), (0, -50, -8), (1, 0.92, 0.75), 60000, 14, 0.5, 1.0)
    beam_light.parent = pivot
    beam_light.location = (0, 0, 0)
    beam_light.rotation_euler = (R(84), 0, 0)
    if target is not None:
        d = Vector(target) - (Vector(loc) + Vector((0, 0, (top + 1.5) * scale)))
        yaw = math.degrees(math.atan2(d.x, -d.y))
        pitch = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
        pivot.rotation_euler = (R(pitch), 0, R(yaw))
        beam_light.rotation_euler = (R(90), 0, 0)
    elif beam_frames:
        key(pivot, 1, rot=(-3, 0, beam_frames[0]))
        key(pivot, frames, rot=(-3, 0, beam_frames[1]))
        for fc in pivot.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    elif beam_yaw is not None:
        pivot.rotation_euler = (R(-3), 0, R(beam_yaw))
    return root, pivot


def beam_on(target, from_dir=(0.6, 1.0, 0.9), length=60, color=(1, 0.92, 0.72), alpha=0.18, power=9000, radius=1.6, shaft=True):
    """A visible shaft of lighthouse light landing on a spot (+ the light itself)."""
    t = Vector(target)
    d = Vector(from_dir).normalized()
    src = t + d * length
    mid = (t + src) / 2
    o = None
    if shaft:  # faint glowing shaft: narrow at the light, wider where it lands
        o = cyl(radius, length, mid, glow_mat("shaft", color, 4.0, min(alpha, 0.12)), 64, r2=radius * 0.35, caps=False)
        o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    s = spot(t + d * 25, t, color, power, 18, 0.45, 0.6)
    return o, s


def tree(loc, s=1.0):
    cyl(0.35 * s, 3 * s, (loc[0], loc[1], 1.5 * s), mat("trunk", (0.4, 0.27, 0.15), 0.9))
    sphere(1.8 * s, (loc[0], loc[1], 4.0 * s), mat("leaves", (0.25, 0.5, 0.22), 0.9), scale=(1, 1, 0.9), seg=10)


def fence(x0, x1, y, h=1.0):
    m = mat("fence", (0.95, 0.95, 0.92), 0.7)
    x = x0
    while x <= x1:
        box((0.2, 0.2, h), (x, y, h / 2), m, 0.02)
        x += 1.0
    box((x1 - x0, 0.12, 0.15), ((x0 + x1) / 2, y, h * 0.7), m, 0)


def room(w=14, d=10, h=8, wall=(0.92, 0.85, 0.72), floor=(0.62, 0.45, 0.3), window=None, window_lit=False, night=False):
    """Three-walled room open towards -Y. window: x position on the back wall (or ('L', y) for side wall)."""
    box((w, d, 0.3), (0, 0, -0.15), mat("floor" + str(floor), floor, 0.7), 0)
    wm = mat("rwall" + str(wall), wall, 0.9)
    box((w, 0.4, h), (0, d / 2, h / 2), wm, 0)
    box((0.4, d, h), (-w / 2, 0, h / 2), wm, 0)
    box((0.4, d, h), (w / 2, 0, h / 2), wm, 0)
    box((w, 0.3, 0.3), (0, d / 2 - 0.3, 0.15), mat("skirting", (0.95, 0.95, 0.95), 0.6), 0)
    if window is not None:
        x = window
        frame = mat("winframe", (0.95, 0.95, 0.95), 0.5)
        glass = mat("roomglass", (0.08, 0.12, 0.3) if night else (0.75, 0.88, 1.0), 0.1,
                    emit=(0.6 if night else 2.0), emit_color=((0.15, 0.2, 0.45) if night else (0.9, 0.95, 1.0)))
        box((3.4, 0.6, 3.4), (x, d / 2 - 0.05, 4.6), frame, 0.02)
        box((3.0, 0.65, 3.0), (x, d / 2 - 0.05, 4.6), glass, 0)
        box((0.15, 0.7, 3.0), (x, d / 2 - 0.1, 4.6), frame, 0)
        box((3.0, 0.7, 0.15), (x, d / 2 - 0.1, 4.6), frame, 0)
    if night:
        point((0, -d / 2 + 2, h - 1.5), (0.55, 0.62, 1.0), 120, 1.5)  # cool fill
    else:
        point((0, -d / 2 + 1, h - 1.0), (1.0, 0.85, 0.7), 450, 2.0)
    return wm


def bed(loc, yaw=0, blanket=(0.45, 0.55, 0.9)):
    root = empty(loc, name="bed")
    root.rotation_euler = (0, 0, R(yaw))
    wood = mat("bedwood", (0.6, 0.42, 0.28), 0.7)
    box((3.6, 6.2, 1.2), (0, 0, 0.6), wood, 0.05, root)
    box((3.6, 0.4, 2.6), (0, 3.0, 1.3), wood, 0.08, root)
    box((3.4, 5.8, 0.6), (0, 0, 1.45), mat("mattress", (0.95, 0.95, 0.95), 0.8), 0.15, root)
    box((3.5, 3.8, 0.35), (0, -0.9, 1.85), mat("blanket" + str(blanket), blanket, 0.9), 0.15, root)
    box((2.2, 1.0, 0.45), (0, 2.2, 1.95), mat("pillow", (1, 1, 1), 0.9), 0.2, root)
    return root


def table(loc, w=4, d=2.6, h=2.6, color=(0.62, 0.42, 0.26)):
    m = mat("table" + str(color), color, 0.6)
    box((w, d, 0.25), (loc[0], loc[1], h), m, 0.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box((0.25, 0.25, h), (loc[0] + sx * (w / 2 - 0.3), loc[1] + sy * (d / 2 - 0.3), h / 2), m, 0.02)


def couch(loc, yaw=0, color=(0.75, 0.45, 0.35)):
    root = empty(loc, name="couch")
    root.rotation_euler = (0, 0, R(yaw))
    m = mat("couch" + str(color), color, 0.95)
    box((6, 2.6, 1.4), (0, 0, 0.7), m, 0.2, root)
    box((6, 0.9, 2.2), (0, 1.0, 1.9), m, 0.3, root)
    for x in (-2.8, 2.8):
        box((0.8, 2.6, 2.0), (x, 0, 1.2), m, 0.3, root)
    for x in (-1.3, 1.3):
        box((2.4, 2.0, 0.5), (x, -0.1, 1.55), m, 0.25, root)
    return root


def fairground(frames=60):
    ground(200, (0.4, 0.6, 0.3))
    # ferris wheel
    wheel = empty((0, 30, 12), name="wheel")
    steel = mat("steel", (0.9, 0.9, 0.95), 0.3, metal=0.5)
    torus(10, 0.25, (0, 0, 0), steel, wheel, rot=(90, 0, 0))
    torus(6, 0.15, (0, 0, 0), steel, wheel, rot=(90, 0, 0))
    cols = [(1, 0.3, 0.3), (0.3, 0.7, 1), (1, 0.85, 0.2), (0.4, 0.9, 0.4), (0.9, 0.4, 0.9), (1, 0.6, 0.2)]
    for i in range(12):
        a = i * math.pi / 6
        cyl(0.1, 10, (5 * math.sin(a), 0, 5 * math.cos(a)), steel, 8, wheel, rot=(0, math.degrees(a), 0))
        box((1.6, 1.6, 1.4), (10 * math.sin(a), 0, 10 * math.cos(a) - 0.9), mat(f"cab{i % 6}", cols[i % 6], 0.5), 0.15, wheel)
        sphere(0.25, (10 * math.sin(a), -0.3, 10 * math.cos(a)), glow_mat("bulb", (1, 0.85, 0.5), 6), wheel)
    key(wheel, 1, rot=(0, 0, 0))
    key(wheel, frames, rot=(0, 12, 0))
    for x in (-5, 5):
        cyl(0.3, 14, (x * 0.8, 30, 6), steel, 8, rot=(0, -x * 3.5, 0))
    # stalls
    for i, x in enumerate((-16, -8, 9, 17)):
        stall((x, 14 + (i % 2) * 3), cols[i])
    # bunting
    for i in range(30):
        box((0.5, 0.05, 0.6), (-20 + i * 1.4, 6, 7 + 0.4 * math.sin(i * 0.5)), mat(f"flag{i % 6}", cols[i % 6], 0.6), 0, rot=(0, 0, 0))
    for i in range(14):
        sphere(0.2, (-18 + i * 2.8, 6, 6.8), glow_mat("bulb2", (1, 0.8, 0.45), 5))
    return wheel


def stall(loc, color, w=5):
    m = mat("stallwood", (0.9, 0.85, 0.75), 0.7)
    box((w, 3, 2.4), (loc[0], loc[1], 1.2), m, 0.05)
    for i in range(5):
        box((w / 5, 3.4, 0.3), (loc[0] - w / 2 + w / 10 + i * w / 5, loc[1] - 0.2, 5.0),
            mat("awn" + str(i % 2) + str(color), color if i % 2 == 0 else (1, 1, 1), 0.6), 0.02)
    for x in (-w / 2, w / 2):
        box((0.2, 0.2, 5), (loc[0] + x, loc[1] - 1.4, 2.5), m, 0.02)


def cotton_candy(parent, loc=(0, -0.2, 0.2)):
    root = empty(loc, parent, "cc")
    cyl(0.04, 1.0, (0, 0, -0.3), mat("stick", (0.95, 0.9, 0.8), 0.5), parent=root)
    sphere(0.45, (0, 0, 0.35), mat("candy", (1, 0.6, 0.8), 0.95, emit=0.3), root, scale=(1, 1, 1.2), seg=12)
    return root


def balloons(loc, n=5):
    cols = [(1, 0.25, 0.3), (0.3, 0.6, 1), (1, 0.85, 0.2), (0.4, 0.85, 0.4), (0.9, 0.45, 0.9)]
    for i in range(n):
        x, z = loc[0] + (i - n / 2) * 0.7, loc[2] + 6 + (i % 2) * 0.8
        sphere(0.5, (x, loc[1], z), mat(f"bal{i}", cols[i % 5], 0.25), scale=(1, 1, 1.2))
        cyl(0.02, 4, (x * 0.9 + loc[0] * 0.1, loc[1], z - 2.5), mat("string", (0.9, 0.9, 0.9), 0.5), 6)


def town(lit=False, frames=60, n=10, seed=4, extent=40, y0=10):
    rnd = random.Random(seed)
    walls = [(0.35, 0.55, 0.85), (0.95, 0.85, 0.55), (0.85, 0.5, 0.45), (0.6, 0.8, 0.6), (0.95, 0.95, 0.9), (0.7, 0.6, 0.85)]
    roofs = [(0.55, 0.25, 0.2), (0.3, 0.3, 0.38), (0.45, 0.3, 0.25), (0.2, 0.35, 0.5)]
    for i in range(n):
        x = -extent + i * (2 * extent / max(1, n - 1)) + rnd.uniform(-2, 2)
        y = y0 + rnd.uniform(0, 14)
        house((x, y, 0), rnd.uniform(-15, 15), rnd.choice(walls), rnd.choice(roofs), w=rnd.uniform(6, 9), h=rnd.uniform(4, 6.5),
              lit=lit and rnd.random() < 0.8, porch=False)
    for i in range(6):
        tree((rnd.uniform(-extent, extent), y0 + rnd.uniform(-4, 18)), rnd.uniform(0.8, 1.3))


def dock(loc, length=16):
    m = mat("dockwood", (0.5, 0.36, 0.24), 0.85)
    for i in range(int(length)):
        box((3.5, 0.9, 0.25), (loc[0], loc[1] + i * 1.0, loc[2]), m, 0.02)
    for i in range(0, int(length), 4):
        for x in (-1.8, 1.8):
            cyl(0.22, 4, (loc[0] + x, loc[1] + i, loc[2] - 1.2), m, 10)


def boat(loc, yaw=0, frames=60):
    root = empty(loc, name="boat")
    root.rotation_euler = (0, 0, R(yaw))
    box((7, 2.6, 1.4), (0, 0, 0.5), mat("hull", (0.9, 0.9, 0.92), 0.5), 0.3, root)
    box((7.2, 2.7, 0.3), (0, 0, 0.0), mat("hullred", (0.75, 0.12, 0.1), 0.5), 0.1, root)
    box((2.5, 2.0, 1.8), (-1, 0, 2.0), mat("cabin", (0.25, 0.45, 0.7), 0.5), 0.1, root)
    cyl(0.1, 5, (1.5, 0, 3.5), mat("mast", (0.4, 0.3, 0.2), 0.7), 8, root)
    key(root, 1, rot=(0, 0, yaw))
    key(root, max(2, frames // 2), rot=(3, 2, yaw))
    key(root, frames, rot=(-2, -2, yaw))
    return root


def truck(loc, yaw=0):
    root = empty(loc, name="truck")
    root.rotation_euler = (0, 0, R(yaw))
    box((9, 4, 5), (-1.5, 0, 3.2), mat("truckbox", (0.95, 0.95, 0.95), 0.6), 0.1, root)
    box((3.5, 4, 3.6), (4.8, 0, 2.5), mat("truckcab", (0.85, 0.35, 0.15), 0.4), 0.3, root)
    box((0.2, 3.2, 1.6), (6.6, 0, 3.2), mat("windshield", (0.3, 0.45, 0.6), 0.05, metal=0.3), 0.05, root)
    for x in (-4.5, -1.5, 4.5):
        for y in (-2, 2):
            cyl(0.9, 0.7, (x, y, 0.9), mat("tire", (0.04, 0.04, 0.04), 0.8), 20, root, rot=(90, 0, 0))
    return root


def sparkle_particles(center, n=40, radius=3.0, frames=60, color=(1, 0.95, 0.7)):
    rnd = random.Random(9)
    m = glow_mat("spark", color, 12)
    for i in range(n):
        o = sphere(0.06, (center[0] + rnd.uniform(-radius, radius), center[1] + rnd.uniform(-radius, radius) * 0.4,
                          center[2] + rnd.uniform(-radius, radius)), m, seg=6)
        z0 = o.location.z
        key(o, 1, loc=tuple(o.location), scale=(0, 0, 0))
        f = rnd.randint(1, max(2, frames - 10))
        key(o, f, loc=(o.location.x, o.location.y, z0), scale=(0, 0, 0))
        key(o, f + 6, loc=(o.location.x, o.location.y, z0 + 0.3), scale=(1.4, 1.4, 1.4))
        key(o, min(frames, f + 18), loc=(o.location.x, o.location.y, z0 + 0.8), scale=(0, 0, 0))


# ------------------------------------------------------------------ render

def render(out_path, frames, res=(540, 960), samples=8, step=2):
    """step=2: animate on twos (15 fps output, same timing) - halves render time."""
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = frames
    sc.frame_step = step
    sc.render.fps = FPS // step
    sc.eevee.use_soft_shadows = False
    sc.eevee.shadow_cube_size = "512"
    sc.eevee.shadow_cascade_size = "1024"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.eevee.taa_render_samples = samples
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    sc.render.filepath = out_path
    smooth_all()
    bpy.ops.render.render(animation=True)
