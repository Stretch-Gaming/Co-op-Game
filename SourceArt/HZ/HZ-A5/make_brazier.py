"""HZ-A5: SM_Brazier and SM_Brazier_Flame. A bronze bowl of coals on a short, tapered sandstone
stand with a carved triangle on each side, like frame 06, about 1.1 m tall; and a separate chunky
flame in torch amber that sits on the coals.

    Blender -b --factory-startup --python SourceArt/HZ/HZ-A5/make_brazier.py -- /tmp/HZ-A5
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
SEED = 613
rng = random.Random(SEED)

kit.reset()
stone = kit.palette_material("M_Sandstone", kit.PALETTE["sandstone"], roughness=0.85)
bronze = kit.palette_material("M_Bronze", hz.BRONZE, roughness=0.45, metallic=0.8)
coals = kit.palette_material("M_Coals", hz.COALS, roughness=0.95)
flame_mat = hz.flame_material()

# --- Stand: a foot slab and a tapered block with a carved triangle on each side ---
foot = kit.chunky_block("Foot", size=(0.66, 0.66, 0.1), bevel=0.025, wobble=0.012, seed=SEED)
bpy.ops.mesh.primitive_cube_add(size=1)
stand = bpy.context.active_object
stand.name = "Stand"
stand.scale = (0.54, 0.54, 0.6)
hz.apply_transforms(stand)
for v in stand.data.vertices:
    top = v.co.z > 0
    v.co.z += 0.3 + 0.1  # sit on the foot
    v.co.x *= 0.8 if top else 1.0  # taper toward the bowl
    v.co.y *= 0.8 if top else 1.0
    v.co.x += rng.uniform(-0.012, 0.012)
    v.co.y += rng.uniform(-0.012, 0.012)
hz.chip(stand, (0.25, -0.25, 0.44), (1, -1, -0.4))  # a knocked corner at the bottom
hz.bevel(stand, width=0.03, segments=2, angle_deg=35, smooth_deg=35)

# Triangle carvings, cut about 3 cm into each sloping face.
bm = bmesh.new()
TRIANGLE = [(-0.11, 0.33), (0.11, 0.33), (0.0, 0.55)]
face_y = -(0.27 - (0.42 - 0.1) / 0.6 * 0.054)  # the face's depth at the triangle's middle height
for k in range(4):
    rot = Matrix.Rotation(k * math.pi / 2, 3, "Z")
    front = [bm.verts.new(rot @ Vector((x, face_y - 0.06, z))) for x, z in TRIANGLE]
    back = [bm.verts.new(rot @ Vector((x, face_y + 0.028, z))) for x, z in TRIANGLE]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(3):
        bm.faces.new((front[(i + 1) % 3], front[i], back[i], back[(i + 1) % 3]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
cut_mesh = bpy.data.meshes.new("Triangles")
bm.to_mesh(cut_mesh)
bm.free()
cutter = bpy.data.objects.new("Triangles", cut_mesh)
bpy.context.collection.objects.link(cutter)
mod = stand.modifiers.new("Carve", "BOOLEAN")
mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", cutter
hz.activate(stand)
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cutter, do_unlink=True)
for o in (foot, stand):
    o.data.materials.clear()
    o.data.materials.append(stone)

# --- Bronze bowl: a short neck, a wide bowl with a thick rolled rim, two ring handles ---
BOWL_Z = 0.7
profile = [(0.0, BOWL_Z - 0.01), (0.12, BOWL_Z - 0.01), (0.1, BOWL_Z + 0.07), (0.16, BOWL_Z + 0.1),
           (0.3, BOWL_Z + 0.2), (0.37, BOWL_Z + 0.31), (0.42, BOWL_Z + 0.36), (0.42, BOWL_Z + 0.4),
           (0.36, BOWL_Z + 0.4), (0.32, BOWL_Z + 0.35), (0.22, BOWL_Z + 0.22), (0.0, BOWL_Z + 0.18)]
bowl = hz.lathe("Bowl", profile, sides=16, material=bronze)
for v in bowl.data.vertices:  # hammered, not turned: nudge the rim out of round
    v.co.x += rng.uniform(-0.008, 0.008)
    v.co.y += rng.uniform(-0.008, 0.008)
hz.smooth(bowl, 50)
handles = []
for side in (-1, 1):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.016, major_segments=10, minor_segments=5,
                                     location=(side * 0.41, 0, BOWL_Z + 0.26), rotation=(math.pi / 2, 0, 0))
    h = bpy.context.active_object
    h.data.materials.append(bronze)
    hz.smooth(h, 60)
    handles.append(h)

# --- Coals: a heap of faceted lumps filling the bowl ---
lumps = []
for i in range(9):
    a = 2 * math.pi * i / 8 + rng.uniform(-0.3, 0.3)
    d = 0.0 if i == 8 else rng.uniform(0.12, 0.2)
    s = rng.uniform(0.1, 0.15)
    lump = kit.faceted_rock(f"Coal{i}", size=(s, s * 0.9, s * 0.7), seed=SEED + i, facets=14, bevel=0.06,
                            material=coals)
    lump.location = (math.cos(a) * d, math.sin(a) * d, BOWL_Z + 0.22 + (0.03 if i == 8 else 0))
    lump.rotation_euler = (rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(0, 6.28))
    hz.apply_transforms(lump)
    lumps.append(lump)

fire = hz.flame("SM_Brazier_Flame", height=0.58, radius=0.16, seed=SEED, lobes=6, material=flame_mat)
fire.location = (0, 0, BOWL_Z + 0.25)
hz.apply_transforms(fire)

parts = [foot, stand, bowl] + handles + lumps
for o in parts:
    hz.apply_transforms(o)
brazier = kit.join(parts, "SM_Brazier")
bc = hz.base_center(brazier)
for o in (brazier, fire):
    o.location -= bc
    hz.apply_transforms(o)
fb = hz.base_center(fire)
print(f"FLAME_OFFSET from the brazier pivot: {fb.z * 100:.1f} cm up, ({fb.x * 100:.1f}, {fb.y * 100:.1f}) cm across")

kit.preview_sheet([brazier, fire], os.path.join(HERE, "SM_Brazier_preview.png"), title="SM_Brazier + Flame")
for o in (brazier, fire):
    hz.export(o, OUT)
