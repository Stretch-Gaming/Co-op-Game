"""HZ-A4: SM_SwingLog.

A heavy 3 m log with iron bands and a rope wrap, hanging from two chains that loop over an
iron axle. All one mesh. The log lies along X and swings around the axle, which also runs
along X, 3 m above the bottom of the log. The cleanup script puts the pivot at the base, so
BP_Trap_Swing needs the hinge offset this script prints (and the pull request records).

    blender -b --factory-startup --python SourceArt/HZ/HZ-A4/make_swing_log.py -- /tmp/HZ-A4
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.append(str(Path(__file__).resolve().parents[1] / "HZ-A3"))
import hz_parts as hz  # noqa: E402

kit = hz.kit

LENGTH = 3.0
RADIUS = 0.36
SIDES = 12
TOP = 3                # the ring index pointing straight up (+Z) with 12 sides
HINGE_ABOVE_BASE = 3.0  # axle center above the lowest point of the log
CHAIN_X = 0.95
AXLE_R = 0.07


def build():
    wood, iron, rope = hz.mat_wood(), hz.mat_iron(), hz.mat_rope()
    end = kit.palette_material("M_WoodEnd", "#B09070", roughness=0.85)
    shape = hz.LogShape(LENGTH, RADIUS, sides=SIDES, seed=7, bend=0.07, taper=0.05)
    log = shape.log("log", rings=16, material=wood, end_material=end)
    parts = [log]
    for x, w in ((-CHAIN_X, 0.15), (CHAIN_X, 0.15), (-1.3, 0.08), (1.3, 0.08)):
        parts.append(shape.band(f"band{x}", x, width=w, thick=0.032, material=iron))

    # A rope wrap between the chain bands: lived in.
    rope_r = 0.03
    pts = []
    turns, x0, x1 = 3.2, -0.35, -0.05
    n = 70
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        th = 2 * math.pi * turns * t
        f = th / (2 * math.pi / SIDES)
        j = int(math.floor(f)) % SIDES
        k = (j + 1) % SIDES
        w = f - math.floor(f)
        r = (shape.radius(x, j) * (1 - w) + shape.radius(x, k) * w) * 0.965 + rope_r * 0.85
        pts.append((x, math.cos(th) * r, math.sin(th) * r + shape.center_z(x)))
    parts.append(hz.rope("wrap", pts, radius=rope_r, twist_per_m=40, sides=8, material=rope))

    # Two short branch stubs on top for a less perfect silhouette.
    for k, (x, tilt) in enumerate(((0.45, 0.35), (-0.62, -0.5))):
        top = shape.point(x, TOP)
        stub = hz.cylinder(f"stub{k}", 0.1, 0.26, sides=7,
                           location=top + Vector((math.sin(tilt) * 0.08, 0, 0.02)),
                           rotation=(0, tilt, 0))
        for v in stub.data.vertices:  # taper toward the broken end
            if v.co.z > 0:
                v.co.x *= 0.75
                v.co.y *= 0.75
        hz.apply_transform(stub)
        stub.data.materials.append(wood)
        kit.chunky_bevel(stub, width=0.01, segments=1, angle_deg=40, smooth_deg=50)
        parts.append(stub)

    # Eyelets on the chain bands, chains up to the axle, and the axle with its collars.
    log_bottom = min((log.matrix_world @ v.co).z for v in log.data.vertices)
    hinge_z = log_bottom + HINGE_ABOVE_BASE
    for side in (-1, 1):
        x = side * CHAIN_X
        band_top = shape.point(x, TOP, 1 + 0.032 / RADIUS).z
        eye_c = Vector((x, 0, band_top + 0.045))
        bpy.ops.mesh.primitive_torus_add(major_segments=10, minor_segments=6, major_radius=0.07,
                                         minor_radius=0.03, location=eye_c,
                                         rotation=(0, math.pi / 2, 0))
        eye = bpy.context.active_object
        eye.data.materials.append(iron)
        hz.shade_smooth(eye, 50)
        parts.append(eye)
        parts.append(hz.chain(f"chain{side}", eye_c + Vector((0, 0, 0.045)),
                              Vector((x, 0, hinge_z + AXLE_R + 0.035)), link_length=0.3,
                              width=0.18, wire=0.034, material=iron, seed=40 + side))
        for dx in (-0.13, 0.13):
            collar = hz.cylinder(f"collar{side}{dx}", AXLE_R + 0.03, 0.06, sides=10,
                                 location=(x + dx, 0, hinge_z), rotation=(0, math.pi / 2, 0))
            collar.data.materials.append(iron)
            kit.chunky_bevel(collar, width=0.008, segments=1, angle_deg=40, smooth_deg=40)
            parts.append(collar)
    axle = hz.cylinder("axle", AXLE_R, 2.3, sides=10, location=(0, 0, hinge_z),
                       rotation=(0, math.pi / 2, 0))
    axle.data.materials.append(iron)
    kit.chunky_bevel(axle, width=0.01, segments=1, angle_deg=40, smooth_deg=40)
    parts.append(axle)

    obj = kit.join(parts, "SM_SwingLog")
    hz.finish(obj)
    return obj, hinge_z


def main():
    out = hz.out_dir()
    kit.reset()
    obj, hinge_z = build()
    lo, hi = kit._bounds([obj])
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    off = Vector((0, 0, hinge_z)) - base
    print(f"HINGE (axle center) from the pivot: X {off.x * 100:.1f} cm, Y {off.y * 100:.1f} cm, "
          f"Z {off.z * 100:.1f} cm; the axle runs along X")
    hz.preview([obj], str(out / "SM_SwingLog_preview.png"), title="SM_SwingLog")
    kit.export_glb([obj], str(out / "SM_SwingLog.glb"))


main()
