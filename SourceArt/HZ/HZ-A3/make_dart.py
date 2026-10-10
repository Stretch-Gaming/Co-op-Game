"""HZ-A3: SM_Dart.

One dart, 30 cm long and oversized so it reads in flight: a chunky iron tip, a wooden shaft,
and three feathers bound with a cord wrap. The tip points along +X.

    blender -b --factory-startup --python SourceArt/HZ/HZ-A3/make_dart.py -- /tmp/HZ-A3
"""
import math
import sys
from pathlib import Path

import bmesh

sys.path.append(str(Path(__file__).resolve().parent))
import hz_parts as hz  # noqa: E402

kit = hz.kit

LENGTH = 0.30
SHAFT_R = 0.018


def revolve(name, profile, sides, material):
    """Revolve (x, radius) pairs around the X axis."""
    bm = bmesh.new()
    rings = []
    for x, r in profile:
        rings.append([bm.verts.new((x, math.cos(2 * math.pi * j / sides + 0.4) * r,
                                    math.sin(2 * math.pi * j / sides + 0.4) * r)) for j in range(sides)])
    for a, c in zip(rings, rings[1:]):
        for j in range(sides):
            k = (j + 1) % sides
            bm.faces.new((a[j], a[k], c[k], c[j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = hz.new_object(name, bm, material)
    hz.shade_smooth(obj, 40)
    return obj


def feather(name, angle, material):
    """A flat, slightly cupped feather vane on the shaft, rotated `angle` around X."""
    x0, x1 = -0.15, -0.055
    outline = [(x0, SHAFT_R * 0.6), (x0 + 0.012, SHAFT_R + 0.03), (x0 + 0.05, SHAFT_R + 0.03),
               (x1, SHAFT_R * 0.8)]
    obj = hz.prism(name, outline, 0.007, material=material)
    for v in obj.data.vertices:  # cup the vane a little
        v.co.z += 0.004 * math.sin((v.co.x - x0) / (x1 - x0) * math.pi)
    obj.rotation_euler = (math.pi / 2 + angle, 0, 0)
    hz.apply_transform(obj)
    kit.chunky_bevel(obj, width=0.002, segments=1, angle_deg=40, smooth_deg=40)
    return obj


def build():
    iron, wood = hz.mat_iron(), hz.mat_wood()
    feathers = kit.palette_material("M_Feather", "#BBAE98", roughness=0.9)
    rope = hz.mat_rope()
    tip = revolve("tip", [(0.06, 0.022), (0.075, 0.027), (0.09, 0.027), (0.13, 0.016),
                          (LENGTH / 2, 0.003)], 4, iron)
    collar = revolve("collar", [(0.05, 0.0215), (0.068, 0.0215)], 8, iron)
    shaft = revolve("shaft", [(-0.15, SHAFT_R * 0.9), (-0.1, SHAFT_R), (0.0, SHAFT_R * 1.05),
                              (0.065, SHAFT_R)], 6, wood)
    wrap = revolve("wrap", [(-0.06, 0.02), (-0.045, 0.022), (-0.03, 0.02)], 8, rope)
    vanes = [feather(f"feather{k}", 2 * math.pi * k / 3, feathers) for k in range(3)]
    dart = kit.join([tip, collar, shaft, wrap] + vanes, "SM_Dart")
    hz.finish(dart)
    return dart


def main():
    out = hz.out_dir()
    kit.reset()
    dart = build()
    lo, hi = kit._bounds([dart])
    print(f"DART axis is {-lo.z * 100:.1f} cm above the pivot; the pivot is at the middle of its "
          f"length, {hi.x * 100:.1f} cm behind the tip")
    # At 30 cm the 1.8 m figure would fill the frame, so this sheet leaves it out.
    kit.preview_sheet([dart], str(out / "SM_Dart_preview.png"), title="SM_Dart", with_figure=False)
    kit.export_glb([dart], str(out / "SM_Dart.glb"))


main()
