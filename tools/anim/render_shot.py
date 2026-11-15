"""Inside Blender: build + render one animated shot.
blender -b --factory-startup -P tools/anim/render_shot.py -- <slug> <n> <frames> <out.mp4> <w> <h> <samples> [still_frame]
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
slug, n, frames, out, w, h, samples = argv[:7]
still = int(argv[7]) if len(argv) > 7 else 0
story = importlib.import_module(f"stories.{slug.replace('-', '_')}")
kit.reset()
stage = story.SHOTS[int(n)](kit, int(frames))
if hasattr(stage, "hide_unused"):
    stage.hide_unused()
import os as _os
if _os.environ.get("ITT_MATTE") == "1":
    # character matte for compositing 2D text BEHIND the characters in the edit
    import bpy
    sc = bpy.context.scene
    chars = set()
    for c in bpy.data.collections:
        if c.name.startswith("CH_") and not c.hide_render:
            chars.update(c.all_objects)

    def is_char(o):
        if o.name.startswith("MATTE_"):
            return True
        while o is not None:
            if o in chars:
                return True
            o = o.parent
        return False
    white = bpy.data.materials.new("MATTE_W"); white.use_nodes = True
    black = bpy.data.materials.new("MATTE_B"); black.use_nodes = True
    for m, col in ((white, (1, 1, 1, 1)), (black, (0, 0, 0, 1))):
        nt = m.node_tree; nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = col; em.inputs[1].default_value = 1.0
        outn = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], outn.inputs[0])
    for o in bpy.data.objects:
        if o.type in ("MESH", "CURVE", "FONT", "SURFACE", "META") and o.material_slots:
            m = white if is_char(o) else black
            for sl in o.material_slots:
                sl.link = "OBJECT"
                sl.material = m
        elif o.type in ("MESH", "CURVE", "FONT") and not o.material_slots:
            o.data.materials.append(white if is_char(o) else black)
    w_ = sc.world.node_tree.nodes.get("Background")
    if w_:
        w_.inputs[0].default_value = (0, 0, 0, 1); w_.inputs[1].default_value = 0
    for nd in list(sc.world.node_tree.nodes):
        if nd.name not in ("Background", "World Output"):
            sc.world.node_tree.nodes.remove(nd)
    sc.world.node_tree.links.new(w_.outputs[0], sc.world.node_tree.nodes["World Output"].inputs[0])
    sc.use_nodes = False
    sc.eevee.use_bloom = False
    sc.eevee.use_gtao = False
    sc.view_settings.view_transform = "Standard"
    for ps in [o for o in bpy.data.objects if o.type == "MESH" and o.particle_systems]:
        ps.hide_render = True
if still:
    import bpy
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = int(w), int(h)
    sc.eevee.taa_render_samples = int(samples)
    sc.render.image_settings.file_format = "PNG"
    kit.smooth_all()
    sc.frame_set(still)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
else:
    import os
    step = int(os.environ.get("ITT_STEP", "0")) or None  # frames per rendered image (2 = smooth 15 fps)
    kit.render(out, int(frames), (int(w), int(h)), int(samples), step=step)
