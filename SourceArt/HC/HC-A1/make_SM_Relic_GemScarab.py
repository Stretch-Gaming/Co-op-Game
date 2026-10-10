"""SM_Relic_GemScarab: a gold scarab beetle with a polished jade shell, about 18 cm long. A domed
jade shell split by a gold seam, a gold pronotum, a wide toothed head fan with jade eyes, a gold
underbody and six short, chunky gold legs. Faces -Y while it's built; the finish step turns it to
face +X.

    blender -b --factory-startup --python SourceArt/HC/HC-A1/make_SM_Relic_GemScarab.py -- /tmp/HC-A1
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import relic_parts as rp  # noqa: E402
from relic_parts import ball, block, kit, pair, tube  # noqa: E402

NAME = "SM_Relic_GemScarab"

kit.reset()
gold, jade = rp.relic_materials()
parts = []


def dome(name, radii, loc, rot=(0, 0, 0), cut=0.0, mat=None, segments=20, rings=12):
    """A ball squashed to `radii`, with its bottom sliced flat `cut` below its center."""
    obj = ball(name, 1.0, loc, scale=radii, rot=rot, segments=segments, rings=rings, mat=mat)
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, -cut)
    return obj


def segment(name, a, b, width, height, mat, seed):
    """A chunky leg segment: a carved block from point a to point b."""
    d = [b[i] - a[i] for i in range(3)]
    length = math.sqrt(sum(c * c for c in d))
    yaw = math.degrees(math.atan2(d[1], d[0]))
    pitch = -math.degrees(math.asin(d[2] / length))
    mid = [(a[i] + b[i]) / 2 for i in range(3)]
    return block(name, (length + width * 0.6, width, height), mid, rot=(0, pitch, yaw), bevel=0.38, seed=seed, mat=mat)


# Gold underbody, flat on the floor, showing as a rim under the shell.
parts.append(dome("Underbody", (0.052, 0.086, 0.022), (0, 0.0, 0.016), cut=0.016, mat=gold))

# The jade shell: one polished dome, split down the middle by a gold seam.
SH_Y, SH_Z = 0.028, 0.022
SH_R = (0.058, 0.062, 0.048)
parts.append(dome("Shell", SH_R, (0, SH_Y, SH_Z), cut=0.012, mat=jade, segments=28, rings=16))
seam = []
for i in range(9):
    y = SH_Y - SH_R[1] * 0.9 + i / 8 * SH_R[1] * 1.72
    k = 1 - ((y - SH_Y) / SH_R[1]) ** 2
    seam.append((0, y, SH_Z + SH_R[2] * math.sqrt(max(k, 0.0)) - 0.002))
parts.append(tube("Seam", seam, 0.0065, mat=gold))
# A gold rim round the bottom of the shell, like a jeweler's setting.
rim_k = math.sqrt(1 - (0.009 / SH_R[2]) ** 2) + 0.03
rim = [(SH_R[0] * rim_k * math.cos(t), SH_Y + SH_R[1] * rim_k * math.sin(t), SH_Z - 0.009)
       for t in (i / 32 * 2 * math.pi for i in range(32))]
parts.append(tube("ShellRim", rim, 0.0055, cyclic=True, mat=gold))

# Gold pronotum, then a wide head fan with four blunt teeth, and jade eyes.
parts.append(dome("Pronotum", (0.05, 0.032, 0.036), (0, -0.036, 0.018), cut=0.018, mat=gold))
parts.append(dome("HeadFan", (0.036, 0.03, 0.02), (0, -0.068, 0.014), cut=0.014, mat=gold))
for i, (dx, yaw) in enumerate(((-0.021, 30), (-0.008, 8), (0.008, -8), (0.021, -30))):
    parts.append(block(f"FanTooth{i}", (0.013, 0.016, 0.012), (dx, -0.094 + 0.006 * abs(dx) / 0.021, 0.008),
                       rot=(0, 0, yaw), taper=(0.7, 0.7), bevel=0.4, seed=10 + i, mat=gold))
parts += pair(ball("Eye", 0.0075, (0.027, -0.062, 0.02), mat=jade))

# Six short, chunky gold legs tucked under the shell: hip, knee, foot.
legs = [
    ((0.03, -0.045, 0.015), (0.054, -0.062, 0.026), (0.062, -0.086, 0.004)),
    ((0.042, -0.004, 0.015), (0.068, 0.0, 0.026), (0.077, 0.014, 0.004)),
    ((0.04, 0.03, 0.015), (0.062, 0.05, 0.026), (0.066, 0.076, 0.004)),
]
for n, (hip, knee, foot) in enumerate(legs):
    parts += pair(segment(f"Femur{n}", hip, knee, 0.02, 0.016, gold, 20 + n))
    parts += pair(segment(f"Tibia{n}", knee, foot, 0.017, 0.014, gold, 30 + n))
    parts += pair(block(f"Foot{n}", (0.022, 0.022, 0.011), (foot[0], foot[1], 0.0055), bevel=0.4, seed=40 + n,
                        mat=gold))

scarab = rp.finish(parts, NAME, length=0.18)
rp.deliver(scarab, NAME, rp.out_dir())
