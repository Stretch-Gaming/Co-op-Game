"""HZ-A4: SM_RopeCoil.

A loose coil of old rope about 50 cm across, lying on the floor: three slightly uneven turns
stacked on each other, with the free end trailing out over the floor and fraying.

    blender -b --factory-startup --python SourceArt/HZ/HZ-A4/make_rope_coil.py -- /tmp/HZ-A4
"""
import math
import random
import sys
from pathlib import Path

from mathutils import Vector

sys.path.append(str(Path(__file__).resolve().parents[1] / "HZ-A3"))
import hz_parts as hz  # noqa: E402

kit = hz.kit

ROPE_R = 0.032       # chunky: about 20% thicker than a real 5 cm rope
COIL_R = 0.21        # centerline radius, so the coil is about 50 cm across


def coil_points(seed):
    rng = random.Random(seed)
    wobble = [(rng.uniform(0, 2 * math.pi), rng.uniform(0.01, 0.022)) for _ in range(3)]
    turns, per_turn = 3.0, 40
    pts = []
    n = int(turns * per_turn)
    for i in range(n + 1):
        t = i / per_turn
        th = 2 * math.pi * t
        r = COIL_R + sum(a * math.sin(th * (k + 2) + p) for k, (p, a) in enumerate(wobble))
        r -= 0.012 * t  # each layer sits a little inside the one below
        z = ROPE_R + 1.75 * ROPE_R * t * 0.62  # layers settle into each other
        pts.append(Vector((math.cos(th) * r, math.sin(th) * r, z)))
    return pts


def build():
    rope = hz.mat_rope()
    pts = coil_points(seed=3)
    # The free end: off the top of the coil, down over its side, and out across the floor.
    last = pts[-1]
    out_dir = Vector((last.x, last.y, 0)).normalized()
    side = Vector((-out_dir.y, out_dir.x, 0))
    tail = []
    for i in range(1, 11):
        f = i / 10
        p = last + out_dir * (0.17 * f) + side * (0.13 * math.sin(f * 2.4))
        p.z = ROPE_R + (last.z - ROPE_R) * max(0.0, 1 - f * 2.2) ** 2
        tail.append(p)
    path = pts + tail
    body = hz.rope("coil", path, radius=ROPE_R, twist_per_m=24, sides=12, material=rope, fray=0.07)
    tip_dir = (path[-1] - path[-2]).normalized()
    tuft = hz.frayed_tuft("tuft", path[-1], tip_dir, ROPE_R, seed=8, length=0.07, material=rope)
    # The start end, tucked under the first turn, frays too.
    start_dir = (path[0] - path[1]).normalized()
    tuft0 = hz.frayed_tuft("tuft0", path[0], start_dir, ROPE_R, seed=9, length=0.05, material=rope)
    obj = kit.join([body, tuft, tuft0], "SM_RopeCoil")
    kit.sit_on_floor(obj)
    hz.apply_transform(obj)
    hz.finish(obj, normals=False)
    return obj


def main():
    out = hz.out_dir()
    kit.reset()
    obj = build()
    # At 50 cm the 1.8 m figure would shrink the coil to a speck, so this sheet leaves it out.
    kit.preview_sheet([obj], str(out / "SM_RopeCoil_preview.png"), title="SM_RopeCoil", with_figure=False)
    kit.export_glb([obj], str(out / "SM_RopeCoil.glb"))


main()
