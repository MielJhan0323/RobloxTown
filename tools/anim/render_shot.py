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
story.SHOTS[int(n)](kit, int(frames))
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
    kit.render(out, int(frames), (int(w), int(h)), int(samples))
