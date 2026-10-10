"""HZ-A5: SM_EgyptPillar. A sandstone column like frame 06, about 6 m tall: a stepped square base,
a shaft of stacked blocks with two raised carved bands, a band of carved chevrons, a flared
capital and a slab on top. Blocks sit a little off true and some corners are chipped. One slot,
M_Sandstone; the sandstone material and hieroglyph decals are separate texture work.

    Blender -b --factory-startup --python SourceArt/HZ/HZ-A5/make_pillar.py -- /tmp/HZ-A5
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path += [os.path.join(HERE, "../../../Tools/blender"), os.path.join(HERE, "../HZ-A2")]

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import asset_kit as kit  # noqa: E402
import hz_shapes as hz  # noqa: E402

OUT = hz.out_dir("/tmp/HZ-A5")
SEED = 601
rng = random.Random(SEED)

kit.reset()
stone = kit.palette_material("M_Sandstone", kit.PALETTE["sandstone"], roughness=0.85)


def block(name, w, h, z, bevel=0.05, wobble=0.02, top_w=None, chips=0, tilt=0.012):
    """One cut-stone block, w wide and h tall, with its base at height z. `top_w` flares or tapers
    the top. `chips` knocks that many corners off."""
    # kit.chunky_block bevels straight away; we need to chip and flare first, so build the box here.
    bpy.ops.mesh.primitive_cube_add(size=1)
    b = bpy.context.active_object
    b.name = name
    b.scale = (w, w, h)
    hz.apply_transforms(b)
    for v in b.data.vertices:
        v.co.z += h / 2  # base on the floor
        v.co.x += rng.uniform(-wobble, wobble)
        v.co.y += rng.uniform(-wobble, wobble)
        if v.co.z > h / 2:
            v.co.z += rng.uniform(-wobble, wobble) * 0.5
    if top_w:
        k = top_w / w
        for v in b.data.vertices:
            if v.co.z > h / 2:
                v.co.x *= k
                v.co.y *= k
    for _ in range(chips):
        sx, sy = rng.choice((-1, 1)), rng.choice((-1, 1))
        sz = rng.choice((0, 1))
        wz = (top_w or w) if sz else w
        corner = Vector((sx * wz / 2, sy * wz / 2, sz * h))
        n = Vector((sx, sy, 1.4 if sz else -0.3)).normalized()
        hz.chip(b, corner - n * rng.uniform(0.07, 0.12), n)
    hz.bevel(b, width=bevel, segments=2, angle_deg=35, smooth_deg=35)
    b.matrix_world = (Matrix.Translation((rng.uniform(-0.015, 0.015), rng.uniform(-0.015, 0.015), z))
                      @ Matrix.Rotation(rng.uniform(-tilt, tilt), 4, "Z"))
    hz.apply_transforms(b)
    return b


def chevron_cutter(w, z, depth=0.08, size=0.46, stroke=0.11):
    """V-shaped carving cutters on all four faces of a block w wide, centered at height z."""
    bm = bmesh.new()
    half = size / 2
    outline = [(-half, half * 0.9), (0, -half * 0.9), (half, half * 0.9),
               (half - stroke * 1.2, half * 0.9), (0, -half * 0.9 + stroke * 1.9), (-half + stroke * 1.2, half * 0.9)]
    for k in range(4):
        rot = Matrix.Rotation(k * math.pi / 2, 3, "Z")
        front = [bm.verts.new(rot @ Vector((x, -w / 2 - 0.05, z + y))) for x, y in outline]
        back = [bm.verts.new(rot @ Vector((x, -w / 2 + depth, z + y))) for x, y in outline]
        bm.faces.new(front)
        bm.faces.new(list(reversed(back)))
        n = len(outline)
        for i in range(n):
            bm.faces.new((front[(i + 1) % n], front[i], back[i], back[(i + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("Chevrons")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Chevrons", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def carve(target, cutter):
    mod = target.modifiers.new("Carve", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    hz.activate(target)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


# Heights from the floor up: big shapes first, then the bands and carvings.
parts = []
z = 0.0
for name, w, h, extra in [
    ("Base", 1.75, 0.55, dict(bevel=0.07, chips=2)),
    ("Step", 1.45, 0.3, dict(bevel=0.05, chips=1)),
    ("Shaft1", 1.12, 1.12, dict(chips=1)),
    ("Band1", 1.26, 0.17, dict(bevel=0.035)),
    ("Shaft2", 1.12, 1.12, dict(chips=1)),
    ("Band2", 1.26, 0.17, dict(bevel=0.035)),
    ("Shaft3", 1.12, 1.12, dict()),
    ("Chevrons", 1.2, 0.6, dict()),
    ("Capital", 1.16, 0.53, dict(top_w=1.62, bevel=0.05)),
    ("Abacus", 1.78, 0.37, dict(bevel=0.07, chips=2)),
]:
    b = block(name, w, h, z, **extra)
    if name == "Chevrons":
        carve(b, chevron_cutter(w, z + h / 2))
        hz.smooth(b, 35)
    parts.append(b)
    z += h

for b in parts:
    b.data.materials.clear()  # the boolean can leave an empty slot behind
    b.data.materials.append(stone)
pillar = kit.join(parts, "SM_EgyptPillar")
kit.sit_on_floor(pillar)
hz.apply_transforms(pillar)

# The kit's preview lights sit below 4 m, which leaves a 6 m pillar's top unlit. Add a neutral top
# light above it, like the kit's own, for the preview only.
top = bpy.data.objects.new("Top_Tall", bpy.data.lights.new("Top_Tall", "AREA"))
top.data.energy, top.data.size = 250, 4.0
top.location = (0, 0, 8.5)
bpy.context.scene.collection.objects.link(top)
kit.preview_sheet([pillar], os.path.join(HERE, "SM_EgyptPillar_preview.png"), title="SM_EgyptPillar")
hz.export(pillar, OUT)
