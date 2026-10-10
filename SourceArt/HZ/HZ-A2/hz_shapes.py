"""Shapes shared by the HZ-A2 and HZ-A5 prop scripts: lofted rings, convex-hull chunks, rope wraps
and stylized flames, plus UV unwrapping and export. Builds on Tools/blender/asset_kit.py.

    import hz_shapes as hz
    out = hz.out_dir("/tmp/HZ-A2")   # the folder after "--", or the default
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

import asset_kit as kit

HERE = os.path.dirname(os.path.abspath(__file__))

# Colors outside the palette's reserved meanings, for surfaces the palette doesn't cover.
WOOD = "#7A5236"
WOOD_DARK = "#4E3424"
IRON = "#4A4856"
ROPE = "#B79C72"
BRONZE = "#7B5634"
COALS = "#2A2128"


def out_dir(default):
    """The output folder passed after "--" on the Blender command line."""
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    path = args[0] if args else default
    os.makedirs(path, exist_ok=True)
    return path


def deselect():
    bpy.ops.object.select_all(action="DESELECT")


def activate(obj):
    deselect()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def bevel(obj, width, segments=2, angle_deg=35, smooth_deg=35):
    """kit.chunky_bevel, with the arguments these scripts use."""
    kit.chunky_bevel(obj, width=width, segments=segments, angle_deg=angle_deg, smooth_deg=smooth_deg)


def smooth(obj, angle_deg=40):
    activate(obj)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))


def _new_object(name, bm, material):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def loft(name, rings, material=None, cap_bottom=True, cap_top=True):
    """Skin a list of rings (each a list of points, all the same length) into a closed tube. A ring
    with a single point closes that end in a cone."""
    bm = bmesh.new()
    vrings = [[bm.verts.new(p) for p in ring] for ring in rings]
    for a, b in zip(vrings, vrings[1:]):
        if len(a) == 1:
            for i in range(len(b)):
                bm.faces.new((a[0], b[(i + 1) % len(b)], b[i]))
        elif len(b) == 1:
            for i in range(len(a)):
                bm.faces.new((a[i], a[(i + 1) % len(a)], b[0]))
        else:
            n = len(a)
            for i in range(n):
                bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    if cap_bottom and len(vrings[0]) > 2:
        bm.faces.new(list(reversed(vrings[0])))
    if cap_top and len(vrings[-1]) > 2:
        bm.faces.new(vrings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _new_object(name, bm, material)


def ring(center, rx, ry=None, sides=8, rot=0.0, jitter=0.0, rng=None, normal_tilt=None):
    """Points on a horizontal ellipse, each pushed in or out by up to `jitter` (a fraction)."""
    ry = rx if ry is None else ry
    pts = []
    for i in range(sides):
        a = rot + 2 * math.pi * i / sides
        j = 1 + (rng.uniform(-jitter, jitter) if rng and jitter else 0)
        p = Vector((math.cos(a) * rx * j, math.sin(a) * ry * j, 0))
        if normal_tilt is not None:
            p = normal_tilt @ p
        pts.append(Vector(center) + p)
    return pts


def lathe(name, profile, sides=12, material=None, rot=0.0):
    """Revolve a list of (radius, z) points around Z. Radius 0 closes that end."""
    rings = []
    for r, z in profile:
        rings.append([Vector((0, 0, z))] if r == 0 else ring((0, 0, z), r, sides=sides, rot=rot))
    return loft(name, rings, material, cap_bottom=profile[0][0] != 0, cap_top=profile[-1][0] != 0)


def hull(name, points, material=None):
    """The convex hull of some points: big clean facets, no holes, like the cave-rock concept."""
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    res = bmesh.ops.convex_hull(bm, input=bm.verts)
    loose = list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)})
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    return _new_object(name, bm, material)


def convex_ring(center, rx, ry, sides, rot, jitter, rng):
    """A jittered horizontal ring that stays a convex polygon, for faceted_loft."""
    for _ in range(50):
        pts = ring(center, rx, ry, sides=sides, rot=rot, jitter=jitter, rng=rng)
        ok = True
        for i in range(sides):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % sides]
            if (b - a).cross(c - b).z <= 0:
                ok = False
                break
        if ok:
            return pts
        jitter *= 0.8
    return ring(center, rx, ry, sides=sides, rot=rot)


def faceted_loft(name, rings, material=None):
    """Like loft, but each band between two rings is their convex hull, so every face is a flat
    facet, as on the cave-rock concept. Rings must be horizontal convex polygons (convex_ring),
    and the last may be a single point."""
    bm = bmesh.new()
    vrings = [[bm.verts.new(p) for p in r] for r in rings]
    for a, b in zip(vrings, vrings[1:]):
        tmp = bmesh.new()
        src = {}
        for v in a + b:
            src[tmp.verts.new(v.co)] = v
        res = bmesh.ops.convex_hull(tmp, input=tmp.verts)
        ring_a = set(a)
        for f in [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)]:
            vs = [src[v] for v in f.verts]
            if all(v in ring_a for v in vs) or not any(v in ring_a for v in vs):
                continue  # the band's caps, shared with the next band
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
        tmp.free()
    if len(vrings[0]) > 2:
        bm.faces.new(list(reversed(vrings[0])))
    if len(vrings[-1]) > 2:
        bm.faces.new(vrings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _new_object(name, bm, material)


def chip(obj, point, normal):
    """Slice a corner off a mesh with a plane through `point` facing `normal`, and cap the cut:
    chipped stone (style rule 5). Do it before beveling."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Vector(point), plane_no=Vector(normal).normalized(),
                                 clear_outer=True)
    cut = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if cut:
        bmesh.ops.holes_fill(bm, edges=cut)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def rope_wrap(name, center, radius, turns=3, thickness=0.012, pitch=None, seed=0, material=None):
    """A few chunky rope loops around a post, each slightly tilted so it looks hand-tied."""
    rng = random.Random(seed)
    pitch = pitch or thickness * 1.9
    loops = []
    for i in range(turns):
        bpy.ops.mesh.primitive_torus_add(major_radius=radius + thickness * 0.7, minor_radius=thickness,
                                         major_segments=12, minor_segments=6,
                                         location=(center[0], center[1], center[2] + (i - (turns - 1) / 2) * pitch),
                                         rotation=(rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(0, 6.28)))
        loops.append(bpy.context.active_object)
    obj = kit.join(loops, name)
    smooth(obj, 60)
    if material:
        obj.data.materials.clear()
        obj.data.materials.append(material)
    return obj


def flame_lobe(height, radius, lean=(0.0, 0.0), curl=0.12, sides=7, seed=0, base=(0, 0, 0)):
    """One tongue of a stylized flame: a fat teardrop whose tip leans out, then curls back."""
    rng = random.Random(seed)
    # (height fraction, radius fraction): a fat, round body and a soft tapering tip.
    profile = [(0.0, 0.62), (0.12, 0.96), (0.28, 1.0), (0.46, 0.84), (0.62, 0.62), (0.77, 0.4), (0.9, 0.2)]
    side = Vector((-lean[1], lean[0], 0))
    side = side.normalized() if side.length > 1e-6 else Vector((1, 0, 0))

    def spine(t):
        out = Vector((lean[0], lean[1], 0)) * (t * t)
        sway = side * (math.sin(t * math.pi * 1.4 + seed) * curl * t)
        return (out + sway) * height + Vector((0, 0, t * height))

    rings = [[Vector(base) + Vector((0, 0, -0.07 * height))]]
    for t, rf in profile:
        rings.append(ring(Vector(base) + spine(t), radius * rf * 1.06, radius * rf * 0.9,
                          sides=sides, rot=0.7 * t + seed, jitter=0.06, rng=rng))
    rings.append([Vector(base) + spine(1.0)])
    return loft("lobe", rings)


def flame(name, height, radius, seed=0, lobes=5, material=None):
    """A chunky stylized flame like the torches in frame 02: a tall central tongue with a lazy S,
    and a ring of shorter, fatter tongues leaning out and curling. Base center at the origin."""
    rng = random.Random(seed)
    parts = [flame_lobe(height, radius, lean=(rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1)), curl=0.16,
                        sides=8, seed=seed)]
    for i in range(lobes):
        a = 2 * math.pi * i / lobes + rng.uniform(-0.25, 0.25)
        d = radius * 0.5
        h = height * rng.uniform(0.48, 0.74)
        k = rng.uniform(0.3, 0.45)
        parts.append(flame_lobe(h, radius * rng.uniform(0.6, 0.75), lean=(math.cos(a) * k, math.sin(a) * k),
                                curl=0.1, seed=seed + i + 1, base=(math.cos(a) * d, math.sin(a) * d, 0)))
    obj = kit.join(parts, name)
    smooth(obj, 75)
    kit.sit_on_floor(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def flame_material():
    """Torch amber, glowing. No specular, so the preview's lights don't wash it out to white."""
    mat = kit.palette_material("M_Flame", kit.PALETTE["torch_amber"], roughness=1.0,
                               emission=kit.PALETTE["torch_amber"], emission_strength=1.6)
    mat.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.0
    return mat


def apply_transforms(obj):
    activate(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def uv_unwrap(obj, angle_deg=60):
    """Smart UV Project, so textures and masks can be added later."""
    activate(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle_deg), island_margin=0.02, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def material_slots(obj):
    return [m.name for m in obj.data.materials]


def base_center(obj):
    lo, hi = kit._bounds([obj])
    return Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))


def report(obj):
    """Print size, triangles and slots, for the pull request table."""
    lo, hi = kit._bounds([obj])
    size = (hi - lo) * 100
    print(f"ASSET {obj.name}: {size.x:.0f} x {size.y:.0f} x {size.z:.0f} cm, "
          f"{kit.triangles([obj])} triangles, slots {material_slots(obj)}")


def export(obj, out):
    """Unwrap, then export one object as <out>/<name>.glb."""
    uv_unwrap(obj)
    report(obj)
    kit.export_glb([obj], os.path.join(out, f"{obj.name}.glb"))
