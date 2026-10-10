"""Shared parts for the HC-A1 relic scripts: beveled carved blocks, balls, rings and rope tubes,
plus the relic materials and the finish step (join, UVs, preview sheets, GLB).

Builds on Tools/blender/asset_kit.py. Each make_*.py script imports this module and runs on its
own in a fresh headless Blender:

    blender -b --factory-startup --python SourceArt/HC/HC-A1/make_<asset>.py -- /tmp/HC-A1
"""
import math
import os
import random
import sys

import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.append(os.path.join(REPO, "Tools", "blender"))
import asset_kit as kit  # noqa: E402

# A warm tan for rope. Rope isn't one of the palette's meaning colors, so it stays clear of
# torch amber and relic gold.
ROPE_TAN = "#A88457"


def out_dir(default="/tmp/HC-A1"):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    path = argv[0] if argv else default
    os.makedirs(path, exist_ok=True)
    return path


def relic_materials():
    """Shiny relic surfaces, so small relics catch a headlamp: gold is metallic at roughness 0.3,
    jade is a polished stone at 0.25."""
    gold = kit.palette_material("M_Gold", kit.PALETTE["relic_gold"], roughness=0.3, metallic=1.0)
    jade = kit.palette_material("M_Jade", kit.PALETTE["relic_jade"], roughness=0.25)
    return gold, jade


def _active():
    return bpy.context.view_layer.objects.active


def _place(obj, loc, rot):
    obj.location = Vector(loc)
    obj.rotation_euler = Euler([math.radians(a) for a in rot])
    return obj


def _smooth(obj, deg=40):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(deg))


def block(name, size, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.28, segments=3, taper=(1.0, 1.0),
          wobble=0.06, seed=0, mat=None, angle=35):
    """A carved block with a wide soft bevel. `bevel` is a fraction of the smallest side, `taper`
    scales the top face (x, y), and `wobble` nudges corners by a fraction of the smallest side so
    no edge is perfectly straight."""
    rng = random.Random(seed)
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = _active()
    obj.name = obj.data.name = name
    small = min(size)
    for v in obj.data.vertices:
        if v.co.z > 0:
            v.co.x *= taper[0]
            v.co.y *= taper[1]
        v.co.x = v.co.x * size[0] + rng.uniform(-wobble, wobble) * small
        v.co.y = v.co.y * size[1] + rng.uniform(-wobble, wobble) * small
        v.co.z = v.co.z * size[2] + rng.uniform(-wobble, wobble) * small
    kit.chunky_bevel(obj, width=bevel * small, segments=segments, angle_deg=angle, smooth_deg=40)
    if mat:
        obj.data.materials.append(mat)
    return _place(obj, loc, rot)


def ball(name, radius, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), segments=16, rings=10, mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segments, ring_count=rings)
    obj = _active()
    obj.name = obj.data.name = name
    for v in obj.data.vertices:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    _smooth(obj, 60)
    if mat:
        obj.data.materials.append(mat)
    return _place(obj, loc, rot)


def cylinder(name, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), vertices=16, bevel=0.3, segments=3,
             scale=(1, 1), mat=None):
    """A beveled disc or post along local Z. `bevel` is a fraction of the smaller of radius and
    depth."""
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=vertices)
    obj = _active()
    obj.name = obj.data.name = name
    for v in obj.data.vertices:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
    kit.chunky_bevel(obj, width=bevel * min(radius, depth), segments=segments, angle_deg=50, smooth_deg=50)
    if mat:
        obj.data.materials.append(mat)
    return _place(obj, loc, rot)


def ring(name, major, minor, loc=(0, 0, 0), rot=(0, 0, 0), major_segments=24, minor_segments=8,
         scale=(1, 1, 1), mat=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=major_segments, minor_segments=minor_segments)
    obj = _active()
    obj.name = obj.data.name = name
    for v in obj.data.vertices:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    _smooth(obj, 60)
    if mat:
        obj.data.materials.append(mat)
    return _place(obj, loc, rot)


def tube(name, points, radius, cyclic=False, mat=None, resolution=2, sides_res=2):
    """A round tube through `points` (world space), for rope and trim. Converted to a mesh."""
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = sides_res
    curve.use_fill_caps = True
    spline = curve.splines.new("NURBS")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (co[0], co[1], co[2], 1.0)
    spline.use_cyclic_u = cyclic
    spline.use_endpoint_u = not cyclic
    spline.order_u = 3
    spline.resolution_u = resolution
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = _active()
    obj.name = obj.data.name = name
    _smooth(obj, 60)
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    return obj


def mirror_x(obj, name):
    """A copy of `obj` mirrored across X = 0."""
    dup = obj.copy()
    dup.data = obj.data.copy()
    dup.name = dup.data.name = name
    bpy.context.collection.objects.link(dup)
    dup.location.x = -obj.location.x
    dup.rotation_euler = Euler((obj.rotation_euler.x, -obj.rotation_euler.y, -obj.rotation_euler.z))
    dup.scale.x = -obj.scale.x
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    dup.select_set(True)
    bpy.context.view_layer.objects.active = dup
    # Applying the negative scale keeps the normals pointing out.
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return dup


def pair(obj):
    """`obj` plus its mirror across X = 0."""
    return [obj, mirror_x(obj, obj.name + "_R")]


def finish(parts, name, height=None, length=None):
    """Join the parts, turn them to face +X (Unreal's forward; the scripts model them facing -Y),
    scale to `height` or front-to-back `length` in meters if given, freeze transforms, unwrap UVs and put the base center at
    the origin."""
    obj = kit.join(parts, name)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.rotation_euler = (0, 0, math.radians(90))
    if height:
        zs = [v.co.z for v in obj.data.vertices]
        obj.scale = [height / (max(zs) - min(zs))] * 3
    elif length:
        ys = [v.co.y for v in obj.data.vertices]
        obj.scale = [length / (max(ys) - min(ys))] * 3
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")
    kit.sit_on_floor(obj)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return obj


def deliver(obj, name, folder):
    """The kit's preview sheet with the 1.8 m figure, a close-up sheet without it, and the GLB."""
    kit.preview_sheet([obj], os.path.join(folder, f"{name}_preview.png"), title=name)
    kit.preview_sheet([obj], os.path.join(folder, f"{name}_preview_closeup.png"), title=name,
                      with_figure=False)
    kit.export_glb([obj], os.path.join(folder, f"{name}.glb"))
    slots = [m.name for m in obj.data.materials]
    print(f"SUMMARY {name} | {kit.triangles([obj])} triangles | slots {slots}")
