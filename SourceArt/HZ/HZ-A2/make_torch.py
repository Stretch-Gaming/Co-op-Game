"""HZ-A2: SM_WallTorch and SM_WallTorch_Flame. An iron wall bracket holding a wooden torch with a
rope wrap below its iron basket head, and a separate chunky flame in torch amber. About 70 cm
tall overall. The torch points out of the wall along -Y; the wall plate's back is flat at Y 0.

    Blender -b --factory-startup --python SourceArt/HZ/HZ-A2/make_torch.py -- /tmp/HZ-A2
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path += [os.path.join(HERE, "../../../Tools/blender"), HERE]

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import asset_kit as kit  # noqa: E402
import hz_shapes as hz  # noqa: E402

OUT = hz.out_dir("/tmp/HZ-A2")
SEED = 207
rng = random.Random(SEED)

kit.reset()
iron = kit.palette_material("M_Iron", hz.IRON, roughness=0.45, metallic=0.7)
wood = kit.palette_material("M_Wood", hz.WOOD, roughness=0.8)
rope = kit.palette_material("M_Rope", hz.ROPE, roughness=0.9)
flame_mat = hz.flame_material()

STICK_Y = -0.165      # how far the torch's axis stands out from the wall
COLLAR_Z = 0.27       # where the bracket holds the torch
TILT = math.radians(9)  # the torch leans out from the wall

# --- Bracket: wall plate with rivets, an arm, a curled strut and a collar ---
plate = kit.chunky_block("Plate", size=(0.11, 0.03, 0.25), bevel=0.009, wobble=0.004, seed=SEED, material=iron)
plate.location = (0, -0.015, COLLAR_Z - 0.01)
rivets = []
for z in (COLLAR_Z + 0.085, COLLAR_Z - 0.09):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=0.014, location=(0, -0.03, z))
    r = bpy.context.active_object
    r.scale = (1, 0.55, 1)
    r.data.materials.append(iron)
    hz.smooth(r)
    rivets.append(r)
arm = kit.chunky_block("Arm", size=(0.034, 0.13, 0.03), bevel=0.008, wobble=0.003, seed=SEED + 1, material=iron)
arm.location = (0, -0.03 - 0.065 + 0.005, COLLAR_Z - 0.015)
# Diagonal strut from low on the plate up to the collar, with a little curl at the wall end.
strut = kit.chunky_block("Strut", size=(0.026, 0.15, 0.022), bevel=0.007, wobble=0.002, seed=SEED + 2, material=iron)
strut.location = (0, -0.095, COLLAR_Z - 0.10)
strut.rotation_euler = (math.radians(-33), 0, 0)
bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.01, major_segments=10, minor_segments=5,
                                 location=(0, -0.042, COLLAR_Z - 0.155), rotation=(0, math.radians(90), 0))
curl = bpy.context.active_object
curl.data.materials.append(iron)
hz.smooth(curl, 60)
bpy.ops.mesh.primitive_torus_add(major_radius=0.036, minor_radius=0.012, major_segments=12, minor_segments=6,
                                 location=(0, STICK_Y, COLLAR_Z))
collar = bpy.context.active_object
collar.scale = (1, 1, 1.3)
collar.data.materials.append(iron)
hz.smooth(collar, 60)

# --- Torch: a slightly bent wooden stick, thicker at the top, a rope wrap, an iron basket head ---
rings = [[Vector((0.0, STICK_Y, -0.005))]]
for i, z in enumerate((0.01, 0.1, 0.2, 0.3, 0.38, 0.44, 0.48)):
    r = 0.019 + 0.007 * (z / 0.48) + (0.005 if z > 0.43 else 0)
    bend = 0.012 * math.sin(z / 0.48 * math.pi)
    rings.append(hz.ring((bend, STICK_Y, z), r, sides=8, rot=i * 0.4, jitter=0.07, rng=rng))
rings.append(hz.ring((0.004, STICK_Y, 0.5), 0.022, sides=8, rot=3.0, jitter=0.1, rng=rng))
stick = hz.loft("Stick", rings, wood)
hz.bevel(stick, 0.004, segments=1, angle_deg=40, smooth_deg=50)

wrap = hz.rope_wrap("Rope", (0.006, STICK_Y, 0.375), 0.026, turns=3, thickness=0.0095, seed=SEED, material=rope)

basket = []
for z, r in ((0.425, 0.034), (0.555, 0.074)):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.009, major_segments=14, minor_segments=5,
                                     location=(0.004, STICK_Y, z))
    basket.append(bpy.context.active_object)
for i in range(6):
    a = 2 * math.pi * i / 6 + 0.2
    lo = Vector((0.004 + math.cos(a) * 0.034, STICK_Y + math.sin(a) * 0.034, 0.415))
    hi = Vector((0.004 + math.cos(a) * 0.086, STICK_Y + math.sin(a) * 0.086, 0.60 + rng.uniform(-0.01, 0.012)))
    slat = kit.chunky_block(f"Slat{i}", size=(0.017, 0.011, (hi - lo).length), bevel=0.0035, wobble=0, material=iron)
    # Keep its base at the origin, then aim it from lo to hi.
    hz.apply_transforms(slat)
    q = Vector((0, 0, 1)).rotation_difference((hi - lo).normalized())
    slat.matrix_world = Matrix.Translation(lo) @ q.to_matrix().to_4x4() @ Matrix.Rotation(a + math.pi / 2, 4, "Z")
    basket.append(slat)
for b in basket:
    if not b.data.materials:
        b.data.materials.append(iron)
    hz.smooth(b, 50)

fire = hz.flame("SM_WallTorch_Flame", height=0.27, radius=0.058, seed=SEED, lobes=5, material=flame_mat)
fire.location = (0.004, STICK_Y, 0.475)

# Lean the torch, its basket and its flame out from the wall around the collar.
pivot = Vector((0, STICK_Y, COLLAR_Z))
lean = Matrix.Translation(pivot) @ Matrix.Rotation(TILT, 4, "X") @ Matrix.Translation(-pivot)
bpy.context.view_layer.update()
for o in [stick, wrap, collar, fire] + basket:
    o.matrix_world = lean @ o.matrix_world

parts = [plate, arm, strut, curl, collar, stick, wrap] + rivets + basket
for o in parts + [fire]:
    hz.apply_transforms(o)
torch = kit.join(parts, "SM_WallTorch")

# Base center pivot: move the torch and flame together so the flame keeps its place.
bc = hz.base_center(torch)
for o in (torch, fire):
    o.location -= bc
    hz.apply_transforms(o)
fb = hz.base_center(fire)
lo, hi = kit._bounds([torch])
print(f"FLAME_OFFSET from the torch pivot: {fb.z * 100:.1f} cm up, {-fb.y * 100:.1f} cm along -Y, "
      f"{fb.x * 100:.1f} cm along X; wall plate back at {(hi.y) * 100:.1f} cm along +Y")

# One sheet with the 1.8 m figure for scale, and a close-up for detail.
kit.preview_sheet([torch, fire], os.path.join(HERE, "SM_WallTorch_preview.png"), title="SM_WallTorch + Flame")
kit.preview_sheet([torch, fire], os.path.join(HERE, "SM_WallTorch_preview_closeup.png"),
                  title="SM_WallTorch + Flame", with_figure=False)
for o in (torch, fire):
    hz.export(o, OUT)
