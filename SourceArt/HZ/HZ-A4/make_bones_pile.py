"""HZ-A4: SM_BonesPile.

A small pile of chunky, cartoon bones about 60 cm across: five long bones with knobbly ends,
a few curved ribs, and a big friendly skull on top. Readable rather than gruesome: round
shapes, soft bevels, no cracks or gore.

    blender -b --factory-startup --python SourceArt/HZ/HZ-A4/make_bones_pile.py -- /tmp/HZ-A4
"""
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector

sys.path.append(str(Path(__file__).resolve().parents[1] / "HZ-A3"))
import hz_parts as hz  # noqa: E402

kit = hz.kit


def knob(name, at, r):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=7, radius=r, location=at)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def bone(name, length, shaft_r, knob_r, seed, material):
    """A long bone along X, centered at the origin: a waisted, slightly bent shaft with two
    knobs at each end."""
    rng = random.Random(seed)
    half = length / 2 - knob_r * 0.9
    n = 7
    pts = [(-half + 2 * half * i / (n - 1), 0, 0.012 * math.sin(math.pi * i / (n - 1))) for i in range(n)]

    def radius(i, s, th):
        u = abs(i / (n - 1) - 0.5) * 2  # 0 in the middle, 1 at the ends
        return shaft_r * (0.85 + 0.45 * u * u)

    shaft = hz.sweep(f"{name}_shaft", pts, radius, sides=8)
    parts = [shaft]
    for side in (-1, 1):
        for k, off in enumerate((-1, 1)):
            r = knob_r * rng.uniform(0.85, 1.05)
            parts.append(knob(f"{name}_knob{side}{k}", (side * (half + knob_r * 0.25), off * knob_r * 0.55, 0), r))
    obj = kit.join(parts, name)
    obj.data.materials.clear()
    obj.data.materials.append(material)
    hz.shade_smooth(obj, 60)
    return obj


def rib(name, radius, sweep_deg, thick, material):
    """A curved rib: an arc in the XY plane, tapering at one end."""
    n = 9
    pts = [(math.cos(math.radians(sweep_deg) * i / (n - 1)) * radius,
            math.sin(math.radians(sweep_deg) * i / (n - 1)) * radius, 0) for i in range(n)]
    obj = hz.sweep(name, pts, lambda i, s, th: thick * (1.0 - 0.45 * i / (n - 1)), sides=7, material=material)
    hz.shade_smooth(obj, 60)
    return obj


def skull(material):
    """A big, round cartoon skull facing -Y: cranium, a blocky face and jaw, deep round eye
    sockets, a nose notch and a row of chunky teeth."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=10, radius=0.11, location=(0, 0.01, 0.13))
    cranium = bpy.context.active_object
    cranium.scale = (1.0, 1.08, 0.95)
    hz.apply_transform(cranium)
    cranium.data.materials.append(material)
    face = hz.box("face", (0.17, 0.12, 0.1), location=(0, -0.045, 0.06))
    face.data.materials.append(material)
    hz.soft_bevel(face, width=0.03, segments=3)
    hz.boolean(cranium, face, operation="UNION")
    for side in (-1, 1):
        eye = knob("eye", (side * 0.047, -0.11, 0.112), 0.04)
        eye.scale = (1.0, 1.0, 1.12)
        hz.boolean(cranium, eye)
    nose = hz.prism("nose", hz.polygon(3, 0.022, rot=math.pi / 2), 0.08, location=(0, -0.11, 0.07),
                    rotation=(math.pi / 2, 0, 0))
    hz.boolean(cranium, nose)
    # Teeth: grooves between four chunky teeth, and a mouth line under them.
    mouth = hz.box("mouth", (0.13, 0.04, 0.012), location=(0, -0.105, 0.025))
    hz.boolean(cranium, mouth)
    for x in (-0.03, 0.0, 0.03):
        gap = hz.box("gap", (0.01, 0.04, 0.035), location=(x, -0.105, 0.04))
        hz.boolean(cranium, gap)
    hz.shade_smooth(cranium, 45)
    cranium.name = "skull"
    return cranium


def place(obj, loc, rot_deg):
    obj.matrix_world = Matrix.Translation(loc) @ Euler([math.radians(a) for a in rot_deg]).to_matrix().to_4x4()
    hz.apply_transform(obj)
    return obj


def build():
    mat = hz.mat_bone()
    parts = []
    # (length, shaft radius, knob radius, location, rotation in degrees)
    long_bones = [
        (0.42, 0.026, 0.042, (0.0, 0.06, 0.042), (0, 0, 18)),
        (0.38, 0.024, 0.04, (0.02, -0.07, 0.07), (0, -6, -32)),     # lying across the first
        (0.34, 0.022, 0.036, (-0.17, 0.08, 0.036), (0, 0, 82)),
        (0.3, 0.021, 0.034, (0.19, 0.07, 0.034), (0, 0, 118)),
        (0.28, 0.02, 0.033, (-0.08, -0.19, 0.033), (0, 0, 166)),
    ]
    for k, (ln, sr, kr, loc, rot) in enumerate(long_bones):
        parts.append(place(bone(f"bone{k}", ln, sr, kr, seed=k, material=mat), Vector(loc), rot))
    for k, (loc, rot) in enumerate((((0.1, -0.2, 0.018), (0, 0, 15)), ((0.16, -0.15, 0.018), (0, 0, 25)),
                                    ((0.21, -0.1, 0.03), (12, 0, 38)))):
        parts.append(place(rib(f"rib{k}", 0.13, 95, 0.018, mat), Vector(loc), rot))
    parts.append(place(skull(mat), Vector((-0.06, -0.01, 0.045)), (-14, 4, 50)))
    pile = kit.join(parts, "SM_BonesPile")
    kit.sit_on_floor(pile)
    hz.apply_transform(pile)
    hz.finish(pile, normals=False)
    return pile


def main():
    out = hz.out_dir()
    kit.reset()
    pile = build()
    # At 60 cm the 1.8 m figure would shrink the pile to a speck, so this sheet leaves it out.
    kit.preview_sheet([pile], str(out / "SM_BonesPile_preview.png"), title="SM_BonesPile", with_figure=False)
    kit.export_glb([pile], str(out / "SM_BonesPile.glb"))


main()
