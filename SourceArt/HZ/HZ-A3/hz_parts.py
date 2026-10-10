"""HZ lane parts shared by the HZ-A3 trap scripts and the HZ-A4 dressing scripts: materials,
UV unwrapping, booleans, rope, chain links, logs and spikes. Builds on Tools/blender/asset_kit.py.

    import sys; from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[1] / "HZ-A3"))
    import hz_parts as hz
    kit = hz.kit
"""
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

REPO = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO / "Tools" / "blender"))
import asset_kit as kit  # noqa: E402

# Surface colors outside the palette's reserved meanings. Wood and rope match the timber and
# rope wraps in frame-02; iron is the dark torch-bracket iron; stone is the light cave rock.
WOOD = "#6E5440"
WOOD_DARK = "#5C3E27"
IRON = "#555A66"
ROPE = "#B8925A"
BONE = "#D9C7A3"  # warm ivory, kept well away from ghost white


def out_dir():
    """The output folder passed after `--`, created if needed."""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    path = Path(argv[0] if argv else "/tmp/HZ")
    path.mkdir(parents=True, exist_ok=True)
    return path


def mat_stone():
    return kit.palette_material("M_Stone", kit.PALETTE["rock_light"], roughness=0.85)


def mat_wood():
    return kit.palette_material("M_Wood", WOOD, roughness=0.8)


def mat_iron():
    return kit.palette_material("M_Iron", IRON, roughness=0.5, metallic=0.5)


def mat_rope():
    return kit.palette_material("M_Rope", ROPE, roughness=0.9)


def mat_bone():
    return kit.palette_material("M_Bone", BONE, roughness=0.7)


def mat_trap():
    """Trap red, only for trap warnings. A little emission in the preview stands in for the glow
    Unreal adds when the trap arms."""
    red = kit.PALETTE["trap_red"]
    return kit.palette_material("M_TrapWarning", red, roughness=0.5, emission=red, emission_strength=1.5)


def new_object(name, bm, material=None):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def set_material(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def shade_smooth(obj, angle_deg=40):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))


def apply_transform(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def boolean(obj, cutter, operation="DIFFERENCE", keep_cutter=False):
    """Exact boolean, applied. Use before chunky_bevel so the cut edges get soft bevels too."""
    mod = obj.modifiers.new("Bool", "BOOLEAN")
    mod.operation = operation
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if not obj.data.polygons:
        raise RuntimeError(f"Boolean with {cutter.name} left {obj.name} empty")
    drop_empty_slots(obj)
    if not keep_cutter:
        bpy.data.objects.remove(cutter, do_unlink=True)


def stone_block(name, lo, hi, seed, tilt=0.006, material=None):
    """A cut-stone block filling the box from `lo` to `hi`, with its top tilted a few
    millimeters so neighbors don't line up perfectly. The footprint stays exact. Not beveled
    yet, so booleans can cut it first."""
    rng = random.Random(seed)
    size = [h - l for l, h in zip(lo, hi)]
    obj = box(name, size, location=[(l + h) / 2 for l, h in zip(lo, hi)])
    ax, ay = rng.uniform(-tilt, tilt), rng.uniform(-tilt, tilt)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    for v in obj.data.vertices:
        if v.co.z > (lo[2] + hi[2]) / 2:
            v.co.z += ax * (v.co.x - cx) / (size[0] / 2) + ay * (v.co.y - cy) / (size[1] / 2)
    if material:
        obj.data.materials.append(material)
    return obj


def drop_empty_slots(obj):
    """Booleans add the cutter's empty material slot. Give the new faces (the cut walls) the
    object's own first material, and remove the empty slots."""
    mats = list(obj.data.materials)
    keep = [i for i, m in enumerate(mats) if m is not None]
    if len(keep) == len(mats) or not keep:
        return
    remap = {old: new for new, old in enumerate(keep)}
    for f in obj.data.polygons:
        f.material_index = remap.get(f.material_index, 0)
    for i in reversed(range(len(mats))):
        if mats[i] is None:
            obj.data.materials.pop(index=i)


def cylinder(name, radius, depth, sides=8, location=(0, 0, 0), rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def box(name, size, location=(0, 0, 0), rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    apply_transform(obj)
    return obj


def prism(name, outline, depth, location=(0, 0, 0), rotation=(0, 0, 0), material=None):
    """Extrude a 2D outline (XY points, counter-clockwise) by `depth` along Z, centered on Z 0.
    Good for carved glyphs and inlays."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, -depth / 2)) for x, y in outline]
    hi = [bm.verts.new((x, y, depth / 2)) for x, y in outline]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_object(name, bm, material)
    obj.location = location
    obj.rotation_euler = rotation
    apply_transform(obj)
    return obj


def frame(name, outer, inner, depth, location=(0, 0, 0), rotation=(0, 0, 0), material=None):
    """Extrude the band between two matching polygons (same point count), e.g. a triangle ring."""
    bm = bmesh.new()
    n = len(outer)
    ol = [bm.verts.new((x, y, -depth / 2)) for x, y in outer]
    oh = [bm.verts.new((x, y, depth / 2)) for x, y in outer]
    il = [bm.verts.new((x, y, -depth / 2)) for x, y in inner]
    ih = [bm.verts.new((x, y, depth / 2)) for x, y in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ol[i], ol[j], oh[j], oh[i]))  # outer wall
        bm.faces.new((ih[i], ih[j], il[j], il[i]))  # inner wall
        bm.faces.new((oh[i], oh[j], ih[j], ih[i]))  # top
        bm.faces.new((il[i], il[j], ol[j], ol[i]))  # bottom
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_object(name, bm, material)
    obj.location = location
    obj.rotation_euler = rotation
    apply_transform(obj)
    return obj


def polygon(n, radius, rot=0.0, scale=(1.0, 1.0)):
    return [(math.cos(rot + 2 * math.pi * i / n) * radius * scale[0],
             math.sin(rot + 2 * math.pi * i / n) * radius * scale[1]) for i in range(n)]


def smart_uv(obj, angle_deg=66, margin=0.02):
    """Smart UV Project, so textures and masks can be added later."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle_deg), island_margin=margin)
    bpy.ops.object.mode_set(mode="OBJECT")


def jitter(obj, amount, seed, only_up=False, keep_footprint=False):
    """Nudge every vertex a little so nothing is perfectly straight (style rule 1)."""
    rng = random.Random(seed)
    for v in obj.data.vertices:
        if only_up and v.co.z <= 1e-4:
            continue
        dx, dy, dz = (rng.uniform(-amount, amount) for _ in range(3))
        if keep_footprint:
            dx = dy = 0.0
        v.co += Vector((dx, dy, dz))


def _frames(points):
    """Parallel-transport frames along a polyline: (tangent, normal, binormal) per point."""
    tangents = []
    for i in range(len(points)):
        a = points[max(i - 1, 0)]
        b = points[min(i + 1, len(points) - 1)]
        tangents.append((b - a).normalized())
    t0 = tangents[0]
    ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    n = t0.cross(ref).normalized()
    out = []
    for t in tangents:
        n = (n - t * n.dot(t)).normalized()
        out.append((t, n, t.cross(n).normalized()))
    return out


def sweep(name, points, radius_fn, sides=10, cap=True, material=None):
    """Sweep a ring of `sides` vertices along a polyline. `radius_fn(i, s, theta)` gives the
    radius at point i, arc length s and ring angle theta, so callers can twist or taper it."""
    pts = [Vector(p) for p in points]
    frames = _frames(pts)
    bm = bmesh.new()
    rings = []
    s = 0.0
    for i, (p, (t, n, b)) in enumerate(zip(pts, frames)):
        if i:
            s += (p - pts[i - 1]).length
        ring = []
        for j in range(sides):
            th = 2 * math.pi * j / sides
            r = radius_fn(i, s, th)
            ring.append(bm.verts.new(p + (n * math.cos(th) + b * math.sin(th)) * r))
        rings.append(ring)
    for a, c in zip(rings, rings[1:]):
        for j in range(sides):
            k = (j + 1) % sides
            bm.faces.new((a[j], a[k], c[k], c[j]))
    if cap:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return new_object(name, bm, material)


def rope(name, points, radius=0.03, twist_per_m=9.0, sides=12, material=None, fray=0.0):
    """Stylized three-strand rope: a lobed tube whose lobes twist along its length, so it reads as
    rope without modeling strands. `fray` swells the last bit at each end."""
    total = sum((Vector(points[i]) - Vector(points[i - 1])).length for i in range(1, len(points)))

    def r(i, s, th):
        lobes = 0.74 + 0.26 * abs(math.cos(1.5 * (th - s * twist_per_m)))
        end = 1.0
        if fray:
            d = min(s, total - s)
            if d < fray:
                end = 1.0 + 0.35 * (1 - d / fray)
        return radius * lobes * end

    obj = sweep(name, points, r, sides=sides, material=material)
    shade_smooth(obj, 60)
    return obj


def frayed_tuft(name, at, direction, radius, seed, strands=8, length=0.08, material=None):
    """A frayed rope end: short, tapering strands splayed out from the tip."""
    rng = random.Random(seed)
    d = Vector(direction).normalized()
    parts = []
    for k in range(strands):
        ang = 2 * math.pi * k / strands + rng.uniform(-0.3, 0.3)
        side = d.orthogonal().normalized()
        side.rotate(Matrix.Rotation(ang, 3, d))
        tip_dir = (d + side * rng.uniform(0.3, 0.6)).normalized()
        base = Vector(at) + side * radius * 0.5 - d * radius * 0.3
        ln = length * rng.uniform(0.6, 1.1)
        bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=radius * 0.36, radius2=radius * 0.1,
                                        depth=ln, location=base + tip_dir * ln / 2)
        c = bpy.context.active_object
        c.rotation_euler = tip_dir.to_track_quat("Z", "Y").to_euler()
        apply_transform(c)
        parts.append(c)
    obj = kit.join(parts, name)
    if material:
        set_material(obj, material)
    shade_smooth(obj, 50)
    return obj


def chain_link(name, center, axis, roll, length=0.2, width=0.12, wire=0.025, material=None):
    """One oval chain link along `axis`, rolled by `roll` radians around it."""
    bpy.ops.mesh.primitive_torus_add(major_segments=10, minor_segments=6,
                                     major_radius=(width - wire * 2) / 2 + wire / 2,
                                     minor_radius=wire)
    link = bpy.context.active_object
    link.name = name
    # Stretch the ring into an oval along local X.
    stretch = (length - wire * 2) / (width - wire * 2)
    link.scale = (stretch, 1, 1)
    apply_transform(link)
    # Torus lies in XY; stand it up so its long axis is X and its plane is XZ.
    link.rotation_euler = (math.pi / 2, 0, 0)
    apply_transform(link)
    rot = Vector((1, 0, 0)).rotation_difference(Vector(axis).normalized()).to_matrix().to_4x4()
    link.matrix_world = Matrix.Translation(center) @ rot @ Matrix.Rotation(roll, 4, "X")
    apply_transform(link)
    if material:
        link.data.materials.append(material)
    return link


def chain(name, start, end, link_length=0.2, width=0.12, wire=0.025, material=None, seed=0):
    """A straight chain of alternating links whose first link starts at `start` and whose last
    link ends at `end`. The pitch stretches a little so the links fill the span exactly."""
    a, b = Vector(start), Vector(end)
    axis = (b - a).normalized()
    span = (b - a).length
    ideal = link_length - wire * 2.2
    count = max(1, round((span - link_length) / ideal) + 1)
    pitch = (span - link_length) / (count - 1) if count > 1 else 0.0
    rng = random.Random(seed)
    links = []
    for k in range(count):
        c = a + axis * (link_length / 2 + k * pitch)
        roll = (math.pi / 2 if k % 2 else 0.0) + rng.uniform(-0.12, 0.12)
        links.append(chain_link(f"{name}_{k}", c, axis, roll, link_length, width, wire, material))
    obj = kit.join(links, name)
    shade_smooth(obj, 50)
    return obj


class LogShape:
    """A chunky, slightly bent, slightly lumpy log along X, centered at the origin. Bands and
    wraps use `radius(x, theta)` and `center_z(x)` so they hug the same lumps."""

    def __init__(self, length=3.0, radius=0.3, sides=10, seed=0, bend=0.05, taper=0.0):
        rng = random.Random(seed)
        self.length, self.r, self.sides, self.bend, self.taper = length, radius, sides, bend, taper
        self.amp = [rng.uniform(-0.08, 0.08) for _ in range(sides)]
        self.phase = [rng.uniform(0, 2 * math.pi) for _ in range(sides)]

    def center_z(self, x):
        u = x / (self.length / 2)
        return self.bend * (1 - u * u)

    def radius(self, x, j):
        u = x / (self.length / 2)
        return self.r * (1 + self.amp[j] + 0.05 * math.sin(self.phase[j] + u * 3.1) - self.taper * u)

    def point(self, x, j, scale=1.0):
        th = 2 * math.pi * j / self.sides
        r = self.radius(x, j) * scale
        return Vector((x, math.cos(th) * r, math.sin(th) * r + self.center_z(x)))

    def _loft(self, name, layout, cap_ends):
        """Loft rings at (x, scale) stations; returns the object and its two cap faces."""
        bm = bmesh.new()
        loops = [[bm.verts.new(self.point(x, j, sc)) for j in range(self.sides)] for x, sc in layout]
        for a, c in zip(loops, loops[1:]):
            for j in range(self.sides):
                k = (j + 1) % self.sides
                bm.faces.new((a[j], c[j], c[k], a[k]))
        caps = []
        if cap_ends:
            caps = [bm.faces.new(loops[0]), bm.faces.new(list(reversed(loops[-1])))]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.faces.index_update()
        cap_ids = [f.index for f in caps]
        return new_object(name, bm), cap_ids

    def log(self, name, rings=14, material=None, end_material=None):
        """The log itself, with chamfered ends; `end_material` paints the end grain."""
        h, cham = self.length / 2, self.r * 0.22
        xs = [-h + self.length * i / (rings - 1) for i in range(1, rings - 1)]
        layout = [(-h, 0.78), (-h + cham, 1.0)] + [(x, 1.0) for x in xs] + [(h - cham, 1.0), (h, 0.78)]
        obj, caps = self._loft(name, layout, True)
        obj.data.materials.append(material)
        if end_material:
            obj.data.materials.append(end_material)
            for i in caps:
                obj.data.polygons[i].material_index = 1
        shade_smooth(obj, 50)
        return obj

    def band(self, name, x, width=0.1, thick=0.025, material=None):
        """An iron band hugging the log at `x`: a short tube just outside the bark."""
        lift = 1 + thick / self.r
        obj, _ = self._loft(name, [(x - width / 2, 0.98), (x - width / 2, lift), (x + width / 2, lift),
                                   (x + width / 2, 0.98)], False)
        obj.data.materials.append(material)
        kit.chunky_bevel(obj, width=0.006, segments=1, angle_deg=50, smooth_deg=50)
        return obj


def spike(name, height=0.46, radius=0.06, sides=6, seed=0, material=None):
    """A chunky iron spike: a short collar, then a faceted cone with a slightly blunt, slightly
    leaning tip. Base at Z 0."""
    rng = random.Random(seed)
    lean = Vector((rng.uniform(-0.012, 0.012), rng.uniform(-0.012, 0.012), 0))
    bm = bmesh.new()
    profile = [(0.0, 1.0), (0.08, 1.0), (0.11, 0.84), (0.5, 0.58), (0.84, 0.26), (1.0, 0.08)]
    rings = []
    for f, rs in profile:
        z = f * height
        ring = []
        for j in range(sides):
            th = 2 * math.pi * j / sides + 0.3
            p = Vector((math.cos(th) * radius * rs, math.sin(th) * radius * rs, z)) + lean * (f ** 2)
            ring.append(bm.verts.new(p))
        rings.append(ring)
    for a, c in zip(rings, rings[1:]):
        for j in range(sides):
            k = (j + 1) % sides
            bm.faces.new((a[j], a[k], c[k], c[j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    obj = new_object(name, bm, material)
    shade_smooth(obj, 35)
    return obj


def soft_bevel(obj, width=0.04, segments=3, angle_deg=40):
    """Like kit.chunky_bevel, but with hardened normals: big flat faces (including boolean
    n-gons) shade flat, and the bevels between them shade soft. kit.chunky_bevel leaves
    harden_normals off, which streaks large n-gons; weighted normals fix that but make the
    bevels look hard."""
    bev = obj.modifiers.new("SoftBevel", "BEVEL")
    bev.width = width
    bev.segments = segments
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(angle_deg)
    bev.harden_normals = True
    bev.use_clamp_overlap = True
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_apply(modifier=bev.name)


def weighted_normals(obj):
    """Keep big flat faces flat next to soft bevels, so boolean n-gons don't shade in streaks."""
    mod = obj.modifiers.new("WeightedNormals", "WEIGHTED_NORMAL")
    mod.keep_sharp = True
    mod.weight = 50
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def preview(objects, path, title, with_figure=True):
    """kit.preview_sheet, but for assets taller or wider than about 2.5 m the light rig is scaled
    up to the asset's size. The kit's lights sit at fixed spots sized for 1-2 m props, so a 4 m
    pillar pokes up past the top light (its top renders black) and its middle is overexposed.
    Scaling positions, sizes and energies together keeps the same look at any size."""
    lo, hi = kit._bounds(objects)
    scale = max(1.0, max(hi - lo) / 2.5)
    original = kit._setup_lighting

    def scaled():
        lights = original()
        for light in lights:
            light.location = light.location * scale
            light.data.size *= scale
            light.data.energy *= scale * scale
        return lights

    kit._setup_lighting = scaled
    try:
        kit.preview_sheet(objects, path, title=title, with_figure=with_figure)
    finally:
        kit._setup_lighting = original


def finish(obj, normals=True):
    """Final pass on an asset: face-weighted normals, then UVs."""
    empty = [i for i, m in enumerate(obj.data.materials) if m is None]
    if empty or not obj.data.materials:
        raise RuntimeError(f"{obj.name} has a face with no material (slots {empty})")
    if normals:
        weighted_normals(obj)
    smart_uv(obj)
    return obj
