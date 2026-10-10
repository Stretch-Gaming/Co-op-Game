"""HZ-A4: SM_RopeHanging.

About 2 m of old rope hanging from an iron ring. The ring hangs, parallel to the wall, from a
staple on a small iron wall plate; the rope is knotted around the ring, with a short tail, and frays at the bottom.
The wall plate's back is the wall line, facing -Y in Blender.

    blender -b --factory-startup --python SourceArt/HZ/HZ-A4/make_rope_hanging.py -- /tmp/HZ-A4
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.append(str(Path(__file__).resolve().parents[1] / "HZ-A3"))
import hz_parts as hz  # noqa: E402

kit = hz.kit

ROPE_R = 0.034
RING_R = 0.085       # ring centerline radius
RING_WIRE = 0.02
DROP = 2.0           # rope length below the knot
WALL_Y = 0.0         # back of the wall plate
PLATE_T = 0.025


def build():
    iron, rope = hz.mat_iron(), hz.mat_rope()
    top = DROP + 0.32
    # Wall plate and staple.
    plate = hz.box("plate", (0.16, PLATE_T, 0.2), location=(0, WALL_Y - PLATE_T / 2, top))
    plate.data.materials.append(iron)
    hz.soft_bevel(plate, width=0.008, segments=2)
    for dz in (-0.065, 0.065):  # two chunky rivets
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=0.018,
                                             location=(0, WALL_Y - PLATE_T, top + dz))
        rivet = bpy.context.active_object
        rivet.scale = (1, 0.6, 1)
        rivet.data.materials.append(iron)
        hz.apply_transform(rivet)
        plate = kit.join([plate, rivet], "plate")
    staple_y = WALL_Y - PLATE_T - 0.065
    face = WALL_Y - PLATE_T + 0.005
    staple = hz.sweep("staple", [(0, face, top + 0.045), (0, staple_y, top + 0.045),
                                 (0, staple_y - 0.022, top), (0, staple_y, top - 0.045),
                                 (0, face, top - 0.045)],
                      lambda i, s, th: 0.014, sides=8, material=iron)
    hz.shade_smooth(staple, 50)
    # The ring hangs through the staple, parallel to the wall, like a door knocker.
    ring_c = Vector((0, (face + staple_y) / 2, top - RING_R))
    bpy.ops.mesh.primitive_torus_add(major_segments=16, minor_segments=7, major_radius=RING_R,
                                     minor_radius=RING_WIRE, location=ring_c, rotation=(math.pi / 2, 0, 0))
    ring = bpy.context.active_object
    ring.data.materials.append(iron)
    hz.shade_smooth(ring, 50)

    # The knot: a few tight turns around the bottom of the ring.
    knot_c = ring_c - Vector((0, 0, RING_R))
    wrap_r = RING_WIRE + ROPE_R * 0.9
    turns = []
    for i in range(43):
        t = i / 42
        th = 2 * math.pi * 2.3 * t
        turns.append(knot_c + Vector((-0.045 + 0.09 * t, math.cos(th) * wrap_r, math.sin(th) * wrap_r)))
    knot = hz.rope("knot", turns, radius=ROPE_R * 0.95, twist_per_m=30, sides=9, material=rope)

    # The main rope: from under the knot down 2 m, with a gentle sway and a frayed end.
    start = knot_c - Vector((0, 0, wrap_r))
    path = []
    for i in range(41):
        t = i / 40
        sway = 0.05 * math.sin(t * math.pi) + 0.015 * math.sin(t * 7.0)
        path.append(start + Vector((sway, -0.02 * t, -DROP * t)))
    main = hz.rope("main", path, radius=ROPE_R, twist_per_m=24, sides=12, material=rope, fray=0.08)
    tuft = hz.frayed_tuft("tuft", path[-1], Vector((0, 0, -1)), ROPE_R, seed=4, length=0.09, material=rope)
    # A short tail from the knot, lying along the main rope.
    tail_path = [knot_c + Vector((0.05, 0, -wrap_r * 0.5))]
    for i in range(1, 9):
        t = i / 8
        tail_path.append(start + Vector((0.06 + 0.05 * t * t, -0.025, -0.22 * t)))
    tail = hz.rope("tail", tail_path, radius=ROPE_R * 0.9, twist_per_m=24, sides=10, material=rope, fray=0.04)
    tail_tuft = hz.frayed_tuft("tail_tuft", tail_path[-1], tail_path[-1] - tail_path[-2], ROPE_R * 0.9,
                               seed=5, length=0.05, material=rope)

    obj = kit.join([plate, staple, ring, knot, main, tuft, tail, tail_tuft], "SM_RopeHanging")
    hz.finish(obj, normals=False)
    return obj, ring_c, top


def main():
    out = hz.out_dir()
    kit.reset()
    obj, ring_c, top = build()
    lo, hi = kit._bounds([obj])
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    ring = ring_c - base
    print(f"ROPE pivot (bottom of the rope) to the ring center: X {ring.x * 100:.1f}, Y {ring.y * 100:.1f}, "
          f"Z {ring.z * 100:.1f} cm; wall line (plate back) at Y {(WALL_Y - base.y) * 100:.1f} cm, "
          f"plate center at Z {(top - base.z) * 100:.1f} cm (Blender axes)")
    kit.preview_sheet([obj], str(out / "SM_RopeHanging_preview.png"), title="SM_RopeHanging")
    kit.export_glb([obj], str(out / "SM_RopeHanging.glb"))


main()
