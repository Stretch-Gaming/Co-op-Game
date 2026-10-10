"""Shared parts for the HC-A2 puzzle props: cut-stone blocks with chipped corners, carved
grooves, rope wraps, materials and UVs. Each make_*.py script imports this next to itself and
Tools/blender/asset_kit.py for the rest.

Blocks are convex hulls of their corners, so a chip is just a corner pulled in along its three
edges. Bottom corners never move, which keeps footprints exact for parts that must line up with
a Blueprint (plates, gate posts).
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(os.path.join(REPO, "Tools", "blender"))
import asset_kit as kit  # noqa: E402

# Cut stone uses the cave's light rock, carvings the mid rock so symbols read at half size.
# Rope, wood and iron aren't reserved palette colors; they match the timber in frame 02.
COLORS = {
    "M_Stone": (kit.PALETTE["rock_light"], 0.85, 0.0),
    "M_StoneCarving": (kit.PALETTE["rock_mid"], 0.9, 0.0),
    "M_Rope": ("#C9A66B", 0.9, 0.0),
    "M_Wood": ("#7A5134", 0.85, 0.0),
    "M_Iron": ("#3C3E46", 0.45, 0.7),
}


def out_dir():
    """The output folder after `--` on the Blender command line, /tmp/HC-A2 by default."""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    path = argv[0] if argv else "/tmp/HC-A2"
    os.makedirs(path, exist_ok=True)
    return path


def mat(name):
    hex_color, rough, metal = COLORS[name]
    return kit.palette_material(name, hex_color, roughness=rough, metallic=metal)


def _mesh_from_bm(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    return obj


def stone_block(name, lo, hi, seed=0, top_wobble=0.0, xy_wobble=0.0, chips=(), chip=0.06,
                bevel=0.035, segments=3, material="M_Stone"):
    """A cut-stone block filling the box lo..hi (world meters), with soft wide bevels.

    top_wobble: random Z shift of the top corners (style rule 1: no perfectly straight lines).
    xy_wobble:  random inward shift of the top corners only, so the footprint stays exact.
    chips:      indices of top corners to chip, 0..3 counter-clockwise from (-x, -y).
    """
    rng = random.Random(seed)
    lo, hi = Vector(lo), Vector(hi)
    pts = []
    bottom = [(lo.x, lo.y), (hi.x, lo.y), (hi.x, hi.y), (lo.x, hi.y)]
    for x, y in bottom:
        pts.append(Vector((x, y, lo.z)))
    for i, (x, y) in enumerate(bottom):
        sx = 1 if x == lo.x else -1  # direction toward the block's center
        sy = 1 if y == lo.y else -1
        c = Vector((x + sx * rng.uniform(0, xy_wobble), y + sy * rng.uniform(0, xy_wobble),
                    hi.z + rng.uniform(-top_wobble, top_wobble)))
        if i in chips:
            d = chip * rng.uniform(0.8, 1.3)
            pts += [c + Vector((sx * d, 0, 0)), c + Vector((0, sy * d, 0)), c + Vector((0, 0, -d))]
        else:
            pts.append(c)
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1.0), verts=bm.verts, edges=bm.edges)
    obj = _mesh_from_bm(bm, name)
    if bevel:
        kit.chunky_bevel(obj, width=bevel, segments=segments, angle_deg=30, smooth_deg=40)
    obj.data.materials.append(mat(material))
    return obj


def ring_cutter(name, outline, width, depth, z_top=0.05):
    """A closed band that follows a convex outline (XY, centered on the origin), `width` wide,
    from z_top - depth down... used as a boolean cutter to carve a symbol's groove."""
    n = len(outline)
    cen = sum((Vector(p) for p in outline), Vector((0.0, 0.0))) / n
    inner = []
    for i, p in enumerate(outline):
        # Offset each corner inward along its bisector so the band has an even width.
        p = Vector(p)
        a = (Vector(outline[i - 1]) - p).normalized()
        b = (Vector(outline[(i + 1) % n]) - p).normalized()
        bis = (a + b)
        if bis.length < 1e-6:
            bis = (cen - p).normalized()
        bis.normalize()
        half = math.acos(max(-1.0, min(1.0, a.dot(b)))) / 2
        inner.append(p + bis * (width / max(math.sin(half), 0.2)))
    bm = bmesh.new()
    z0, z1 = z_top - depth, z_top + 0.2
    ob = [bm.verts.new((p[0], p[1], z0)) for p in outline]
    ot = [bm.verts.new((p[0], p[1], z1)) for p in outline]
    ib = [bm.verts.new((p.x, p.y, z0)) for p in inner]
    it = [bm.verts.new((p.x, p.y, z1)) for p in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))      # outer wall
        bm.faces.new((ib[j], ib[i], it[i], it[j]))      # inner wall
        bm.faces.new((ot[i], ot[j], it[j], it[i]))      # top
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))      # bottom
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _mesh_from_bm(bm, name)
    obj.data.materials.append(mat("M_StoneCarving"))
    return obj


def solid_cutter(name, outline, depth, z_top=0.05):
    """A prism from a convex outline, for a filled carving (a cross arm, a socket)."""
    bm = bmesh.new()
    bot = [bm.verts.new((p[0], p[1], z_top - depth)) for p in outline]
    top = [bm.verts.new((p[0], p[1], z_top + 0.2)) for p in outline]
    bm.faces.new(bot[::-1])
    bm.faces.new(top)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _mesh_from_bm(bm, name)
    obj.data.materials.append(mat("M_StoneCarving"))
    return obj


def polygon(n, radius, rot=0.0, scale=(1.0, 1.0)):
    return [(math.cos(rot + 2 * math.pi * i / n) * radius * scale[0],
             math.sin(rot + 2 * math.pi * i / n) * radius * scale[1]) for i in range(n)]


def place(obj, matrix):
    obj.matrix_world = matrix @ obj.matrix_world
    bpy.context.view_layer.update()
    return obj


def carve(target, cutters):
    """Boolean the cutters out of the target. Faces the cut leaves on the cutter's surface get
    the cutter's material (M_StoneCarving), so the groove has its own slot and can be tinted in
    Unreal. (The Boolean's own material transfer drops it, so the faces are found by distance.)"""
    for c in cutters:
        cm = c.data.materials[0]
        names = [m.name for m in target.data.materials]
        if cm.name not in names:
            target.data.materials.append(cm)
            names.append(cm.name)
        slot = names.index(cm.name)
        mod = target.modifiers.new("Carve", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = c
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=mod.name)
        to_cutter = c.matrix_world.inverted() @ target.matrix_world
        for p in target.data.polygons:
            ok, hit, _n, _i = c.closest_point_on_mesh(to_cutter @ p.center)
            if ok and (hit - to_cutter @ p.center).length < 1e-4:
                p.material_index = slot
        bpy.data.objects.remove(c, do_unlink=True)
    return target


def rope_loop(name, path_pts, radius=0.035, closed=True, coil_turns=0, seed=0):
    """A chunky rope along a path (world points), as a beveled curve converted to mesh.
    Rope is slightly lumpy: the radius swells and shrinks a little along it."""
    rng = random.Random(seed)
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    cu.resolution_u = 4
    sp = cu.splines.new("POLY" if not closed else "NURBS")
    sp.points.add(len(path_pts) - 1)
    for p, pt in zip(sp.points, path_pts):
        p.co = (pt[0], pt[1], pt[2], 1.0)
        p.radius = rng.uniform(0.85, 1.15)
    sp.use_cyclic_u = closed
    if closed:
        sp.order_u = 3
    obj = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    obj.data.materials.clear()
    obj.data.materials.append(mat("M_Rope"))
    bpy.ops.object.shade_smooth()
    return obj


def rounded_rect_path(cx, cy, z, half_x, half_y, corner=0.08, per_side=3):
    """Points around a rectangle with cut corners, for a rope wrapped around a block."""
    pts = []
    corners = [(half_x, half_y), (-half_x, half_y), (-half_x, -half_y), (half_x, -half_y)]
    for (x0, y0), (x1, y1) in zip(corners, corners[1:] + corners[:1]):
        a = Vector((x0, y0))
        b = Vector((x1, y1))
        d = (b - a).normalized()
        start, end = a + d * corner, b - d * corner
        for k in range(per_side):
            p = start.lerp(end, k / max(per_side - 1, 1))
            pts.append((cx + p.x, cy + p.y, z))
    return pts


def unwrap(obj):
    """Smart UV Project, so textures and masks can be added later."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def finish(parts, name):
    """Join the parts, drop unused or duplicate material slots, unwrap, and report."""
    obj = kit.join(parts, name) if len(parts) > 1 else parts[0]
    obj.name = obj.data.name = name
    # Merge duplicate slots (join keeps one slot per part).
    seen = {}
    remap = []
    for i, m in enumerate(obj.data.materials):
        remap.append(seen.setdefault(m.name, len(seen)))
    order = sorted(seen, key=seen.get)
    # Clearing the slots resets every face to slot 0, so remap after rebuilding them.
    new_index = [remap[p.material_index] for p in obj.data.polygons]
    obj.data.materials.clear()
    for n in order:
        obj.data.materials.append(bpy.data.materials[n])
    for p, i in zip(obj.data.polygons, new_index):
        p.material_index = i
    unwrap(obj)
    bpy.context.view_layer.update()
    lo, hi = kit._bounds([obj])
    size = hi - lo
    print(f"BUILT {name}: {kit.triangles([obj])} tris, "
          f"{size.x * 100:.1f} x {size.y * 100:.1f} x {size.z * 100:.1f} cm, "
          f"slots {[m.name for m in obj.data.materials]}, min z {lo.z * 100:.2f} cm")
    return obj


def lumpy(name, size, seed, facets=40, bevel=0.025, material="M_Stone"):
    """A carved, faceted lump (asset_kit's rock shape) with its base center at the origin."""
    obj = kit.faceted_rock(name, size=size, seed=seed, facets=facets, bevel=bevel, material=mat(material))
    return obj


def move(obj, loc=(0, 0, 0), rot=(0, 0, 0)):
    obj.matrix_world = (Matrix.Translation(Vector(loc)) @
                        Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @
                        Matrix.Rotation(rot[0], 4, "X")) @ obj.matrix_world
    bpy.context.view_layer.update()
    return obj


def chip_cutter(name, x0, x1, edge_y, edge_z, depth):
    """A wedge that knocks a sloped chip off a top edge running along X at (edge_y, edge_z),
    with the outside toward +Y. `depth` is how far the chip bites into the top and the side."""
    bm = bmesh.new()
    tri = [(edge_y - depth, edge_z + 0.05), (edge_y + 0.05, edge_z + 0.05),
           (edge_y + 0.05, edge_z - depth - 0.05)]
    a = [bm.verts.new((x0, y, z)) for y, z in tri]
    b = [bm.verts.new((x1, y, z)) for y, z in tri]
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _mesh_from_bm(bm, name)
    obj.data.materials.append(mat("M_Stone"))
    return obj


def soften(obj, width=0.012, segments=2, angle_deg=60):
    """Bevel only the sharp edges left by carving, so grooves and chips stay soft."""
    kit.chunky_bevel(obj, width=width, segments=segments, angle_deg=angle_deg, smooth_deg=40)


def big_preview_extras(scale, figure_at=None):
    """asset_kit's preview lights are placed and sized for props about 2 m across, and it skips
    the scale figure above 3 m. For the gate, add the same rig scaled up around the asset and a
    1.8 m figure, before calling kit.preview_sheet. Returns the objects to delete afterwards."""
    made = []
    rig = [("Big_Key_Warm", "#FFD7A3", 260, (2.5, -2.0, 3.0), 3.0),
           ("Big_Fill_Teal", kit.PALETTE["crystal_teal"], 90, (-2.5, -1.5, 1.5), 3.0),
           ("Big_Top", "#E6E9F2", 150, (0.0, 0.0, 4.0), 4.0),
           ("Big_Rim", "#FFFFFF", 200, (-1.0, 3.0, 2.5), 2.0)]
    for name, color, energy, loc, size in rig:
        data = bpy.data.lights.new(name, "AREA")
        data.color = kit.hex_rgba(color)[:3]
        # Same irradiance at scaled distances: energy grows with the square of the scale.
        data.energy = energy * scale * scale * 0.8
        data.size = size * scale
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = Vector(loc) * scale
        obj.rotation_euler = (Vector((0, 0, 0.5 * scale)) - obj.location).to_track_quat("-Z", "Y").to_euler()
        made.append(obj)
    if figure_at is not None:
        fig = kit._scale_figure()
        fig.location = Vector(figure_at)
        made.append(fig)
    return made


def remove(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
