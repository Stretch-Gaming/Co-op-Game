"""HZ-A2: SM_CrystalCluster. Seven teal hexagonal crystals with pointed tips, at varied angles,
growing from a small faceted rock base, about 85 cm tall. Crystal and rock are separate material
slots (M_Crystal, M_Rock) so the glow can be tuned in Unreal.

    Blender -b --factory-startup --python SourceArt/HZ/HZ-A2/make_crystal_cluster.py -- /tmp/HZ-A2
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path += [os.path.join(HERE, "../../../Tools/blender"), HERE]

from mathutils import Matrix, Vector  # noqa: E402

import asset_kit as kit  # noqa: E402
import hz_shapes as hz  # noqa: E402

OUT = hz.out_dir("/tmp/HZ-A2")
SEED = 311
rng = random.Random(SEED)

kit.reset()
rock = kit.palette_material("M_Rock", kit.PALETTE["rock_mid"], roughness=0.9)
crystal = kit.palette_material("M_Crystal", kit.PALETTE["crystal_teal"], roughness=0.25,
                               emission=kit.PALETTE["crystal_teal"], emission_strength=0.8)

base = kit.faceted_rock("Base", size=(0.66, 0.54, 0.28), seed=SEED, facets=26, bevel=0.035, material=rock)

# (length, radius, tilt from vertical, direction of tilt, root offset on the rock), all in meters
# and degrees. Big shapes first: one tall crystal, two medium, and small ones leaning out.
CRYSTALS = [
    (0.70, 0.115, 5, 30, (0.0, 0.02)),
    (0.50, 0.092, 24, 205, (-0.09, -0.03)),
    (0.44, 0.085, 30, 325, (0.10, -0.05)),
    (0.34, 0.072, 38, 105, (0.03, 0.11)),
    (0.28, 0.062, 46, 250, (-0.15, 0.06)),
    (0.24, 0.056, 50, 15, (0.17, 0.04)),
    (0.19, 0.05, 52, 150, (-0.04, -0.15)),
]
parts = []
for i, (length, r, tilt, azim, (ox, oy)) in enumerate(CRYSTALS):
    twist = rng.uniform(0, math.pi)
    tip_off = Vector((rng.uniform(-0.15, 0.15) * r, rng.uniform(-0.15, 0.15) * r, 0))
    rings = [
        # Buried in the rock, shallower for the leaning ones so they don't poke out underneath.
        hz.ring((0, 0, -0.12 * math.cos(math.radians(tilt)) ** 2), r * 0.95, sides=6, rot=twist),
        hz.ring((0, 0, 0.0), r, sides=6, rot=twist),
        hz.ring((0, 0, length * 0.7), r * 0.88, sides=6, rot=twist),
        [Vector((0, 0, length)) + tip_off],
    ]
    c = hz.loft(f"Crystal{i}", rings, crystal)
    hz.bevel(c, width=r * 0.16, segments=2, angle_deg=30, smooth_deg=30)
    aim = Matrix.Rotation(math.radians(azim), 4, "Z") @ Matrix.Rotation(math.radians(tilt), 4, "Y")
    c.matrix_world = Matrix.Translation((ox, oy, 0.13)) @ aim
    hz.apply_transforms(c)
    parts.append(c)

cluster = kit.join([base] + parts, "SM_CrystalCluster")
kit.sit_on_floor(cluster)
hz.apply_transforms(cluster)

kit.preview_sheet([cluster], os.path.join(HERE, "SM_CrystalCluster_preview.png"), title="SM_CrystalCluster",
                  with_figure=False)
kit.preview_sheet([cluster], os.path.join(HERE, "SM_CrystalCluster_scale_preview.png"), title="SM_CrystalCluster")
hz.export(cluster, OUT)
