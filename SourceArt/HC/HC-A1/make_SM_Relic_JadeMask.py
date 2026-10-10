"""SM_Relic_JadeMask: a carved jade mask with gold trim, about 22 cm tall, standing on a low gold
plinth so it sits upright on an altar. Chunky carved features: a heavy brow, stern eye slots and
a mouth slot cut right through, a big nose and cheekbones, all in jade, with a thick gold
border, gold lips, ear spools, a forehead diamond and a three-lobed gold crest.
Faces -Y while it's built; the finish step turns it to face +X.

    blender -b --factory-startup --python SourceArt/HC/HC-A1/make_SM_Relic_JadeMask.py -- /tmp/HC-A1
"""
import math
import os
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import relic_parts as rp  # noqa: E402
from relic_parts import block, cylinder, kit, pair, tube  # noqa: E402

NAME = "SM_Relic_JadeMask"
W, D, H = 0.16, 0.055, 0.19  # face plate width, depth and height
Z0 = 0.106  # height of the plate's center above the floor


def outline(nx, nz):
    """Map the square [-1, 1]^2 to the mask's rounded shield shape, narrower at the chin."""
    dx = nx * math.sqrt(max(0.0, 1 - nz * nz / 2))
    dz = nz * math.sqrt(max(0.0, 1 - nx * nx / 2))
    x = 0.35 * nx + 0.65 * dx
    z = 0.35 * nz + 0.65 * dz
    return x * (0.74 + 0.26 * min(1.0, (z + 1) / 1.3)), z


def surface(nx, nz, depth=0.0, back=0.0):
    """A point on the plate's curved front face at square coordinates (nx, nz), pushed out by
    `depth`, or into the plate by `back`."""
    x, z = outline(nx, nz)
    y = -D / 2 + 0.022 * x * x + 0.01 * z * z - depth + back
    return (x * W / 2, y, Z0 + z * H / 2)


kit.reset()
gold, jade = rp.relic_materials()
parts = []

# The face plate: a block cut into a grid, rounded into a shield and curved back at the sides.
bpy.ops.mesh.primitive_cube_add(size=1)
plate = bpy.context.active_object
plate.name = plate.data.name = "FacePlate"
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.subdivide(number_cuts=7)
bpy.ops.object.mode_set(mode="OBJECT")
for v in plate.data.vertices:
    nx, ny, nz = v.co.x * 2, v.co.y * 2, v.co.z * 2
    v.co = surface(nx, nz, back=(ny + 1) / 2 * D)

# Stern eye slots and a mouth slot, cut right through so the mask reads at a glance.
cutters = [
    block("EyeCut", (0.048, 0.2, 0.021), (0.036, 0, Z0 + 0.007), rot=(0, -10, 0), taper=(0.75, 1.0), bevel=0.3,
          wobble=0),
    block("MouthCut", (0.058, 0.2, 0.016), (0, 0, Z0 - 0.054), taper=(1.2, 1.0), bevel=0.3, wobble=0),
]
cutters.append(rp.mirror_x(cutters[0], "EyeCut_R"))
plate.data.materials.append(jade)
for c in cutters:
    kit.boolean(plate, c)
kit.chunky_bevel(plate, width=0.012, segments=3, angle_deg=35, smooth_deg=40)
parts.append(plate)

# Carved jade features: a heavy brow over each eye, cheekbones and a big wedge nose.
parts += pair(block("Brow", (0.062, 0.026, 0.024), surface(0.42, 0.37, 0.002), rot=(0, -10, -8), bevel=0.4, seed=1,
                    mat=jade))
parts += pair(block("Cheek", (0.04, 0.028, 0.032), surface(0.54, -0.22, 0.004), rot=(0, 12, -14), bevel=0.45, seed=2,
                    mat=jade))
parts.append(block("Nose", (0.036, 0.04, 0.074), surface(0, -0.1, 0.009), rot=(-10, 0, 0), taper=(0.5, 0.45),
                   bevel=0.32, seed=3, mat=jade))

# Gold trim: a thick border round the face, lips round the mouth slot and a forehead diamond.
border = []
for i in range(48):
    t = i / 48 * 2 * math.pi
    c, s = math.cos(t), math.sin(t)
    m = max(abs(c), abs(s))
    x, y, z = surface(c / m, s / m, back=D / 2 - 0.004)
    r = math.hypot(x, z - Z0)
    k = (r + 0.004) / r
    border.append((x * k, y, Z0 + (z - Z0) * k))
parts.append(tube("Border", border, 0.012, cyclic=True, mat=gold, resolution=3))
lips = [surface(nx, nz, 0.003) for nx, nz in
        [(-0.42, -0.57), (-0.2, -0.6), (0.2, -0.6), (0.42, -0.57), (0.42, -0.79), (0.2, -0.82), (-0.2, -0.82),
         (-0.42, -0.79)]]
parts.append(tube("Lips", lips, 0.0065, cyclic=True, mat=gold, resolution=3))
parts.append(block("BrowDiamond", (0.03, 0.016, 0.03), surface(0, 0.62, 0.004), rot=(0, 45, 0), bevel=0.35, wobble=0,
                   mat=gold))

# Gold ear spools and a three-lobed crest.
ear_x, _, _ = surface(1, 0.05)
parts += pair(cylinder("EarSpool", 0.024, 0.022, (ear_x + 0.012, 0.004, Z0 + 0.006), rot=(0, 90, 0), bevel=0.4,
                       mat=gold))
top = Z0 + H / 2
parts.append(block("CrestBand", (0.12, 0.04, 0.024), (0, 0.006, top - 0.01), bevel=0.4, seed=4, mat=gold))
parts.append(block("CrestMid", (0.044, 0.032, 0.052), (0, 0.008, top + 0.014), taper=(0.5, 0.7), bevel=0.4, seed=5,
                   mat=gold))
parts += pair(block("CrestSide", (0.036, 0.03, 0.04), (0.046, 0.01, top + 0.004), rot=(0, 24, 0), taper=(0.5, 0.7),
                    bevel=0.4, seed=6, mat=gold))

# A low gold plinth, so the mask stands upright on an altar.
parts.append(block("Plinth", (0.13, 0.085, 0.024), (0, 0.004, 0.012), taper=(0.9, 0.88), bevel=0.35, seed=7, mat=gold))

mask = rp.finish(parts, NAME, height=0.22)
rp.deliver(mask, NAME, rp.out_dir())
