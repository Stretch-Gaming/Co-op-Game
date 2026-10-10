"""HZ-A2: SM_Stalagmite_A (about 1.2 m) and SM_Stalagmite_B (about 2.2 m). Floor stalagmites,
chunky and faceted like the cave-rock concept, slightly bent, with blunt tips. One slot, M_Rock.

    Blender -b --factory-startup --python SourceArt/HZ/HZ-A2/make_stalagmites.py -- /tmp/HZ-A2
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path += [os.path.join(HERE, "../../../Tools/blender"), HERE]

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import asset_kit as kit  # noqa: E402
import hz_shapes as hz  # noqa: E402

OUT = hz.out_dir("/tmp/HZ-A2")

# Radius along the height, as fractions of the base radius: a wide foot, a long taper and a blunt,
# rounded tip, not a needle.
PROFILE = [(0.0, 1.0), (0.05, 0.97), (0.15, 0.87), (0.36, 0.71), (0.6, 0.53), (0.8, 0.37), (0.93, 0.24)]


def radius_at(t):
    for (t0, r0), (t1, r1) in zip(PROFILE, PROFILE[1:]):
        if t <= t1:
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return PROFILE[-1][1]


def spire(name, height, base_r, seed, bend=0.1, sides=6, cuts=5, material=None):
    """One stalagmite: jittered, twisted rings along a spine that bends to one side, with a low blunt
    cap, skinned with flat facets. Then a few big plane cuts across the rings give it the broad
    hewn facets of the cave-rock concept, and a wide bevel at a low angle softens their edges."""
    rng = random.Random(seed)
    lean = rng.uniform(0, 2 * math.pi)

    def center(t):
        k = bend * height * t * t
        wob = 0.025 * height * math.sin(t * 5 + seed)
        return Vector((math.cos(lean) * k + wob * 0.3, math.sin(lean) * k - wob * 0.2, t * height))

    rings = []
    rot = rng.uniform(0, 6.28)
    for t, rf in PROFILE:
        r = base_r * rf
        if t > 0.05:  # the foot's two rings line up, so it stands straight on the floor
            rot += math.pi / sides + rng.uniform(-0.15, 0.15)  # offset rings make big triangular facets
        rings.append(hz.convex_ring(center(t), r * rng.uniform(0.96, 1.06), r * rng.uniform(0.84, 0.96),
                                    sides, rot, 0.12, rng))
    # A small, slightly tilted cap instead of a point: a blunt, rounded tip after beveling.
    rings.append(hz.convex_ring(center(1.0), base_r * 0.12, base_r * 0.09, 3, rot, 0.0, rng))
    obj = hz.faceted_loft(name, rings, material)
    slope = base_r * 0.8 / height  # how much the surface faces upward
    for k in range(cuts):
        t = 0.2 + 0.65 * (k + rng.uniform(0.1, 0.9)) / cuts  # keep the foot wide
        a = rng.uniform(0, 2 * math.pi)
        d = base_r * radius_at(t) * rng.uniform(0.86, 0.93)
        normal = Vector((math.cos(a), math.sin(a), slope + rng.uniform(-0.1, 0.1)))
        before = obj.data.copy()
        top = max(v.co.z for v in obj.data.vertices)
        hz.chip(obj, center(t) + Vector((math.cos(a), math.sin(a), 0)) * d, normal)
        if max(v.co.z for v in obj.data.vertices) < top - 0.01 * height:
            obj.data = before  # this cut took the tip off: skip it
        else:
            bpy.data.meshes.remove(before)
    hz.bevel(obj, width=base_r * 0.07, segments=2, angle_deg=10, smooth_deg=13)
    return obj


def rubble(name, size, seed, at, material):
    r = kit.faceted_rock(name, size=size, seed=seed, facets=20, bevel=0.04, material=material)
    r.location = at
    hz.apply_transforms(r)
    return r


def build_a():
    kit.reset()
    rock = kit.palette_material("M_Rock", kit.PALETTE["rock_mid"], roughness=0.9)
    main = spire("Spire", 1.2, 0.34, seed=11, bend=0.12, cuts=4, material=rock)
    pebble = rubble("Rubble", (0.3, 0.26, 0.16), 12, (0.3, 0.06, 0), rock)
    obj = kit.join([main, pebble], "SM_Stalagmite_A")
    kit.sit_on_floor(obj)
    hz.apply_transforms(obj)
    return obj


def build_b():
    kit.reset()
    rock = kit.palette_material("M_Rock", kit.PALETTE["rock_mid"], roughness=0.9)
    main = spire("Spire", 2.2, 0.48, seed=23, bend=0.09, cuts=6, material=rock)
    # A young stalagmite fused to the foot, and a couple of fallen chunks, for a better silhouette.
    side = spire("Side", 0.62, 0.2, seed=29, bend=0.2, cuts=2, material=rock)
    side.location = (0.42, 0.16, 0)
    hz.apply_transforms(side)
    rocks = [rubble("Rubble1", (0.34, 0.28, 0.18), 31, (-0.36, -0.28, 0), rock),
             rubble("Rubble2", (0.22, 0.2, 0.13), 37, (0.18, -0.46, 0), rock)]
    obj = kit.join([main, side] + rocks, "SM_Stalagmite_B")
    kit.sit_on_floor(obj)
    hz.apply_transforms(obj)
    return obj


for build in (build_a, build_b):
    obj = build()
    kit.preview_sheet([obj], os.path.join(HERE, f"{obj.name}_preview.png"), title=obj.name)
    hz.export(obj, OUT)
