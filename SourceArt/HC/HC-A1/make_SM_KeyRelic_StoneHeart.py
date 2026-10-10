"""SM_KeyRelic_StoneHeart: the key relic, a heavy carved stone heart about 62 cm tall, carried with
both hands. Two faceted cave-rock lobes on a thick, blunt body with a few chips knocked out of
it, gold and jade runes inlaid front and back (the altar's diamond motif round a jade stone), and
a rope wrapped three times round its waist with a big rope loop on each side to carry it by.
Faces -Y while it's built; the finish step turns it to face +X.

    blender -b --factory-startup --python SourceArt/HC/HC-A1/make_SM_KeyRelic_StoneHeart.py -- /tmp/HC-A1
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import relic_parts as rp  # noqa: E402
from relic_parts import ball, kit, tube  # noqa: E402

NAME = "SM_KeyRelic_StoneHeart"

kit.reset()
gold, jade = rp.relic_materials()
stone = kit.palette_material("M_Stone", kit.PALETTE["rock_light"], roughness=0.85)
rope = kit.palette_material("M_Rope", rp.ROPE_TAN, roughness=0.9)
parts = []


def hull(name, points):
    """The convex hull of `points`: big clean facets, no holes."""
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def lump(name, center, size, seed, facets=36):
    """A faceted lump: jittered points on an ellipsoid, hulled."""
    rng = random.Random(seed)
    pts = []
    for _ in range(facets):
        theta = rng.uniform(0, 2 * math.pi)
        z = rng.uniform(-1, 1)
        r = math.sqrt(1 - z * z)
        j = rng.uniform(0.86, 1.06)
        pts.append((center[0] + r * math.cos(theta) * size[0] / 2 * j,
                    center[1] + r * math.sin(theta) * size[1] / 2 * j,
                    center[2] + z * size[2] / 2 * j))
    return hull(name, pts)


# The body: a thick, blunt, tapering block of rock, hulled from jittered rings.
rng = random.Random(7)
rings = [  # height, half width, half depth
    (0.0, 0.1, 0.11),
    (0.05, 0.15, 0.15),
    (0.16, 0.21, 0.165),
    (0.28, 0.255, 0.17),
    (0.4, 0.265, 0.16),
]
body_pts = []
for z, rx, ry in rings:
    for i in range(9):
        t = (i + rng.uniform(-0.25, 0.25)) / 9 * 2 * math.pi
        j = rng.uniform(0.92, 1.04)
        body_pts.append((math.cos(t) * rx * j, math.sin(t) * ry * j, z + rng.uniform(-0.012, 0.012) * (z > 0)))
heart = hull("Heart", body_pts)
heart.data.materials.append(stone)

# Two lobes on top, leaving a cleft between them.
for side, seed in ((1, 11), (-1, 12)):
    kit.boolean(heart, lump(f"Lobe{side}", (side * 0.135, 0.0, 0.44), (0.31, 0.32, 0.3), seed), "UNION")

# A few chips knocked out of the edges: lived in.
for i, (direction, height, size) in enumerate((((-1, -0.6), 0.47, 0.09), ((1, 0.5), 0.3, 0.08), ((0.7, -0.7), 0.1, 0.07))):
    d = Vector((direction[0], direction[1], 0)).normalized()
    hit, loc, _, _ = heart.ray_cast(Vector((0, 0, height)) + d * 2, -d)
    if hit:
        kit.boolean(heart, lump(f"Chip{i}", loc + d * size * 0.18, (size, size, size * 0.8), 30 + i, facets=14),
                "DIFFERENCE")

kit.chunky_bevel(heart, width=0.024, segments=3, angle_deg=12, smooth_deg=30)
parts.append(heart)


def on_surface(x, z, front=True, out=0.0):
    """Where a ray along Y hits the heart's front (or back) at (x, z), and the surface normal there."""
    sign = -1 if front else 1
    hit, loc, normal, _ = heart.ray_cast(Vector((x, sign * 2, z)), Vector((0, -sign, 0)))
    assert hit, (x, z)
    return loc + normal * out, normal


def inlay_ring(name, center, radius, tube_radius, front, mat, corners=4, rot=45):
    """A closed inlay (a diamond with `corners` 4, a circle with many) traced over the surface."""
    pts = []
    n = corners * 3 if corners < 8 else corners
    for i in range(n):
        t = math.radians(rot) + i / n * 2 * math.pi
        if corners < 8:
            # Straight sides with rounded corners: walk the polygon's edges.
            k = i / 3
            a = math.radians(rot) + math.floor(k) / corners * 2 * math.pi
            b = a + 2 * math.pi / corners
            f = k - math.floor(k)
            px = (1 - f) * math.cos(a) + f * math.cos(b)
            pz = (1 - f) * math.sin(a) + f * math.sin(b)
        else:
            px, pz = math.cos(t), math.sin(t)
        loc, _ = on_surface(center[0] + px * radius, center[1] + pz * radius, front, out=tube_radius * 0.35)
        pts.append(loc)
    return tube(name, pts, tube_radius, cyclic=True, mat=mat, resolution=3)


def stud(name, x, z, radius, front, mat, flat=0.45):
    """A domed stone or stud set into the surface, facing out along the normal."""
    loc, normal = on_surface(x, z, front)
    obj = ball(name, radius, tuple(loc), scale=(1, 1, flat), segments=18, rings=10, mat=mat)
    obj.rotation_euler = normal.to_track_quat("Z", "Y").to_euler()
    return obj


# Front runes: the altar's diamond in gold round a jade stone, a jade bar running down from it
# below the rope, and different marks on each lobe (gold slashes, a small jade diamond), kept
# uneven so the runes never read as a face.
parts.append(inlay_ring("FrontDiamond", (0, 0.39), 0.095, 0.014, True, gold, rot=0))
parts.append(stud("FrontStone", 0, 0.39, 0.042, True, jade))
parts.append(tube("FrontBar", [on_surface(0, z, True, 0.004)[0] for z in (0.165, 0.13, 0.095, 0.06)], 0.012, mat=jade))
for i, dx in enumerate((-0.03, 0.01)):
    parts.append(tube(f"LobeSlash{i}", [on_surface(-0.15 + dx + ddx, z, True, 0.004)[0]
                                        for ddx, z in ((-0.018, 0.43), (0.0, 0.47), (0.018, 0.51))],
                      0.011, mat=gold))
parts.append(inlay_ring("LobeDiamond", (0.15, 0.47), 0.035, 0.0105, True, jade, rot=0))

# Back runes: a jade diamond round a gold stud, so it reads from behind too.
parts.append(inlay_ring("BackDiamond", (0, 0.39), 0.08, 0.012, False, jade, rot=0))
parts.append(stud("BackStud", 0, 0.39, 0.028, False, gold, flat=0.6))

# Rope wrapped three times round the waist.
ROPE_R = 0.017
for n, z in enumerate((0.2, 0.235, 0.27)):
    loop = []
    for i in range(20):
        t = i / 20 * 2 * math.pi
        d = Vector((math.cos(t), math.sin(t), 0))
        hit, loc, normal, _ = heart.ray_cast(Vector((0, 0, z)) + d * 2, -d)
        loop.append(loc + d * ROPE_R * 0.75 + Vector((0, 0, 0.003 * math.sin(3 * t + n))))
    parts.append(tube(f"RopeWrap{n}", loop, ROPE_R, cyclic=True, mat=rope, resolution=2, sides_res=1))

# A big rope loop on each side to carry it by, 15-20% larger than real so it reads in first
# person, with a knot where it's tied on.
for side in (1, -1):
    hit, loc, _, _ = heart.ray_cast(Vector((side * 2, 0, 0.235)), Vector((-side, 0, 0)))
    sx = loc.x
    handle = [(sx - side * 0.01, -0.065, 0.24), (sx + side * 0.05, -0.075, 0.21), (sx + side * 0.1, -0.05, 0.18),
              (sx + side * 0.115, 0.0, 0.17), (sx + side * 0.1, 0.05, 0.18), (sx + side * 0.05, 0.075, 0.21),
              (sx - side * 0.01, 0.065, 0.24)]
    parts.append(tube(f"RopeHandle{side}", handle, 0.02, mat=rope, resolution=3, sides_res=1))
    for y in (-0.06, 0.06):
        knot = ball(f"Knot{side}{y}", 0.03, (sx + side * 0.012, y, 0.235), scale=(0.9, 1.0, 1.2), segments=10, rings=6,
                    mat=rope)
        parts.append(knot)

stone_heart = rp.finish(parts, NAME, height=0.62)
rp.deliver(stone_heart, NAME, rp.out_dir())
