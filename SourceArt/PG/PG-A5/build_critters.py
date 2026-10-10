"""PG-A5: cave bats and rats, ambient life for Site 1.

Four static meshes, each built from chunky overlapping primitives with one palette material
per part, so the Unreal import gets a material slot per color:

- SM_Bat_Body: a flying bat's body and head, facing +X, with no wings.
- SM_Bat_Wing: one wing, spreading toward +Y from its root at Y 0. The flying Blueprint
  flaps two copies around the shoulder hinge, the left one mirrored with a scale of Y -1.
- SM_Bat_Hanging: a bat asleep upside down, wrapped in its wings, feet up.
- SM_Rat: a black, scary cave rat facing +X: hunched, scruffy, teeth bared, tail trailing.

Run it headless to rebuild the previews, the committed FBXs, PG-A5_Critters.blend and the
lineup render:

    blender -b --factory-startup --python SourceArt/PG/PG-A5/build_critters.py -- SourceArt/PG/PG-A5

Or, in a live Blender (through Blender MCP), exec the file with `PG_A5_LIVE = True` set, then
call `build("SM_Rat")` and so on to look at one mesh at a time.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

REPO = Path(__file__).resolve().parents[3] if "__file__" in globals() else Path.cwd()
sys.path.append(str(REPO / "Tools" / "blender"))
import asset_kit as kit  # noqa: E402

# Creature colors. None of them is in docs/art/style.md's palette, because each palette color
# has one job, and the creatures must stay clear of the relic, ghost and trap colors. The bats are
# muted, dark browns and greys that read against the blue-violet rock without glowing.
FUR_BAT = "#5C4B58"
MEMBRANE = "#3B3142"
SKIN = "#C98F8C"     # the bat's nose and legs: a dusty pink, well away from trap red
EYE = "#17121A"
FANG = "#E8DCC6"     # warm off-white, not the ghost's cold #D6F0FF
# The rat is near-black with a cold violet cast, so the stylized edge light still finds its
# shape. Its eyes are a deep, dark blood red with only a faint glint: far darker than trap red
# (#FF4A2A), so they read as a creature's eyes, not a trap warning.
FUR_RAT = "#1C1920"
BELLY_RAT = "#302B33"
SKIN_RAT = "#5A4346"   # ears, nose, feet and tail: grey-pink, scaly and dirty
EYE_RAT = "#7A1214"
TEETH_RAT = "#CDBB8C"  # yellowed incisors, duller than relic gold


def mats():
    return {
        "bat_fur": kit.palette_material("Bat_Fur", FUR_BAT, roughness=0.85),
        "membrane": kit.palette_material("Bat_Membrane", MEMBRANE, roughness=0.7),
        "rat_fur": kit.palette_material("Rat_Fur", FUR_RAT, roughness=0.9),
        "rat_belly": kit.palette_material("Rat_Belly", BELLY_RAT, roughness=0.9),
        "rat_skin": kit.palette_material("Rat_Skin", SKIN_RAT, roughness=0.55),
        "rat_eye": kit.palette_material("Rat_Eye", EYE_RAT, roughness=0.1, emission=EYE_RAT, emission_strength=0.6),
        "rat_teeth": kit.palette_material("Rat_Teeth", TEETH_RAT, roughness=0.35),
        "skin": kit.palette_material("Critter_Skin", SKIN, roughness=0.6),
        "eye": kit.palette_material("Critter_Eye", EYE, roughness=0.15),
        "fang": kit.palette_material("Critter_Fang", FANG, roughness=0.4),
    }


# ---------------------------------------------------------------- primitives

def _finish_part(obj, name, material, smooth=True):
    obj.name = name
    obj.data.materials.clear()
    obj.data.materials.append(material)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def blob(name, radius, location, material, scale=(1, 1, 1), rotation=(0, 0, 0), segments=14, rings=9):
    """A scaled UV sphere: the body, head and most soft parts."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius,
                                         location=location, rotation=rotation, scale=scale)
    obj = bpy.context.active_object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return _finish_part(obj, name, material)


def cone(name, r1, r2, depth, location, rotation, material, sides=8):
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=r1, radius2=r2, depth=depth,
                                    location=location, rotation=rotation)
    obj = bpy.context.active_object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return _finish_part(obj, name, material)


def disc(name, radius, depth, location, rotation, material, scale=(1, 1, 1), sides=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=depth,
                                        location=location, rotation=rotation, scale=scale)
    obj = bpy.context.active_object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    kit.chunky_bevel(obj, width=min(depth * 0.45, radius * 0.3), segments=2, angle_deg=30)
    return _finish_part(obj, name, material)


def tube(name, points, r0, r1, material, sides=8):
    """A tapering tube along a polyline, from radius r0 to r1: tails, finger bones and toes."""
    pts = [Vector(p) for p in points]
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = t.cross(Vector((0, 0, 1)))
        if n.length < 1e-4:
            n = t.cross(Vector((0, 1, 0)))
        n.normalize()
        b = t.cross(n)
        r = r0 + (r1 - r0) * i / (len(pts) - 1)
        rings.append([bm.verts.new(p + (n * math.cos(a) + b * math.sin(a)) * r)
                      for a in (2 * math.pi * j / sides for j in range(sides))])
    for a, c in zip(rings, rings[1:]):
        for j in range(sides):
            k = (j + 1) % sides
            bm.faces.new((a[j], a[k], c[k], c[j]))
    bm.faces.new(list(reversed(rings[0])))
    tip = bm.verts.new(pts[-1] + (pts[-1] - pts[-2]).normalized() * r1)
    for j in range(sides):
        bm.faces.new((rings[-1][j], rings[-1][(j + 1) % sides], tip))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return _finish_part(obj, name, material)


def slab(name, outline, thickness, material, z=0.0, bevel=0.003):
    """Extrude a closed XY outline into a thin slab, centred on `z`: the wing membrane."""
    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, z - thickness / 2)) for x, y in outline]
    top = [bm.verts.new((x, y, z + thickness / 2)) for x, y in outline]
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    kit.chunky_bevel(obj, width=bevel, segments=1, angle_deg=40)
    return _finish_part(obj, name, material, smooth=False)


def bend(obj, fn):
    """Move every vertex through fn(Vector) -> Vector, for the wing's camber."""
    for v in obj.data.vertices:
        v.co = fn(v.co.copy())
    obj.data.update()


# ---------------------------------------------------------------- bat

def bat_head(m, at, down=False):
    """Head, ears, snout, eyes and fangs. Facing +X; with `down`, upside down (ears toward -Z)."""
    s = -1 if down else 1
    x, y, z = at
    parts = [blob("head", 0.046, (x, y, z), m["bat_fur"], scale=(1.0, 1.05, 0.95))]
    for side in (-1, 1):
        # Big, pointed ears: half the bat's charm, and its silhouette at a distance.
        parts.append(cone(f"ear{side}", 0.022, 0.003, 0.06,
                          (x - 0.004, y + side * 0.026, z + s * 0.05),
                          (s * side * math.radians(-24), math.radians(-12) if not down else math.radians(192), 0),
                          m["bat_fur"], sides=7))
        parts.append(blob(f"eye{side}", 0.0105, (x + 0.036, y + side * 0.019, z + s * 0.012), m["eye"], segments=10, rings=6))
        parts.append(cone(f"fang{side}", 0.0045, 0.0005, 0.016,
                          (x + 0.05, y + side * 0.009, z - s * 0.024),
                          (0, 0, 0) if down else (math.pi, 0, 0), m["fang"], sides=5))
    parts.append(blob("snout", 0.022, (x + 0.04, y, z - s * 0.008), m["bat_fur"], scale=(1.0, 1.15, 0.85)))
    parts.append(blob("nose", 0.009, (x + 0.06, y, z - s * 0.002), m["skin"], scale=(0.8, 1.4, 0.8), segments=10, rings=6))
    return parts


def build_bat_body(m):
    parts = [blob("body", 0.06, (0, 0, 0), m["bat_fur"], scale=(1.25, 0.9, 0.85))]
    parts += bat_head(m, (0.08, 0, 0.012))
    for side in (-1, 1):
        parts.append(tube(f"leg{side}", [(-0.05, side * 0.022, -0.02), (-0.085, side * 0.03, -0.03),
                                         (-0.105, side * 0.034, -0.026)], 0.008, 0.004, m["skin"], sides=6))
    body = kit.join(parts, "SM_Bat_Body")
    return body


# The wing's outline, seen from above: root along Y 0 from X 0.035 (front) to X -0.045, the
# leading edge out to the wrist, then three finger tips with scalloped membrane between them.
WING_OUTLINE = [
    (0.035, 0.0), (0.05, 0.07), (0.045, 0.15),           # arm, out to the wrist
    (0.012, 0.215), (0.004, 0.29),                       # first finger tip
    (-0.025, 0.235), (-0.07, 0.255),                     # scallop, second tip
    (-0.072, 0.195), (-0.112, 0.17),                     # scallop, third tip
    (-0.088, 0.12), (-0.09, 0.06), (-0.045, 0.0),        # trailing edge back to the body
]
WING_BONES = [  # wrist outward to each finger tip
    [(0.035, 0.0), (0.05, 0.07), (0.045, 0.15)],
    [(0.045, 0.15), (0.03, 0.22), (0.004, 0.29)],
    [(0.045, 0.15), (-0.01, 0.2), (-0.07, 0.255)],
    [(0.045, 0.15), (-0.04, 0.16), (-0.112, 0.17)],
]
# The shoulder hinge, before cleanup_export moves the pivot: the root's leading corner.
WING_HINGE = (0.0, 0.0, 0.0)


def wing_camber(co):
    # A gentle arch along the span and a droop at the trailing edge, so it isn't a flat card.
    co.z += 0.03 * math.sin(min(co.y / 0.29, 1.0) * math.pi * 0.8) - 0.12 * max(0.0, -co.x - 0.02) * (co.y / 0.29)
    return co


def build_bat_wing(m):
    membrane = slab("membrane", WING_OUTLINE, 0.007, m["membrane"])
    parts = [membrane]
    for k, bone in enumerate(WING_BONES):
        r0 = 0.009 if k == 0 else 0.006
        parts.append(tube(f"bone{k}", [(x, y, 0.004) for x, y in bone], r0, 0.0035, m["bat_fur"], sides=6))
    parts.append(cone("thumb", 0.006, 0.001, 0.025, (0.055, 0.155, 0.006), (0, math.radians(70), 0), m["bat_fur"], sides=5))
    wing = kit.join(parts, "SM_Bat_Wing")
    bend(wing, wing_camber)
    return wing


def build_bat_hanging(m):
    """Upside down, facing +X. The feet grip the ceiling at the top; the head hangs at the
    bottom. Folded wings wrap the body like a cloak, open at the front over the fur."""
    parts = [
        blob("cloak", 0.06, (0, 0, 0.0), m["membrane"], scale=(0.95, 1.0, 1.55), segments=16, rings=11),
        blob("chest", 0.046, (0.03, 0, -0.012), m["bat_fur"], scale=(0.85, 0.85, 1.6), segments=16, rings=11),
    ]
    for side in (-1, 1):
        # The folded forearms down the front edges of the cloak, ending in the thumbs.
        parts.append(tube(f"arm{side}", [(0.034, side * 0.047, 0.06), (0.052, side * 0.042, 0.0),
                                         (0.042, side * 0.031, -0.06)], 0.0065, 0.005, m["membrane"], sides=6))
        parts.append(cone(f"thumb{side}", 0.006, 0.001, 0.02, (0.045, side * 0.03, -0.07),
                          (0, math.radians(200), 0), m["bat_fur"], sides=5))
        # Short hooked toes gripping the ceiling, dark so they don't read as antennae.
        parts.append(tube(f"foot{side}", [(-0.006, side * 0.016, 0.082), (-0.004, side * 0.018, 0.1),
                                          (0.008, side * 0.018, 0.107)], 0.0065, 0.004, m["eye"], sides=6))
    parts += bat_head(m, (0.012, 0, -0.11), down=True)
    return kit.join(parts, "SM_Bat_Hanging")


# ---------------------------------------------------------------- rat

def build_rat(m):
    """Hunched and scruffy: a high, arched back with a ridge of ragged tufts, a long head that
    drops to a pointed snout, narrow eyes under heavy brows, bared incisors, small torn ears and a
    long, thick tail dragging behind."""
    f, b, s, e, t = m["rat_fur"], m["rat_belly"], m["rat_skin"], m["rat_eye"], m["rat_teeth"]
    parts = [
        blob("rump", 0.075, (-0.045, 0, 0.078), f, scale=(1.4, 1.0, 1.0)),
        blob("shoulders", 0.06, (0.05, 0, 0.07), f, scale=(1.15, 0.95, 0.9)),
        blob("belly", 0.06, (-0.01, 0, 0.042), b, scale=(1.6, 0.8, 0.55)),
        blob("head", 0.045, (0.125, 0, 0.058), f, scale=(1.35, 0.88, 0.82), rotation=(0, math.radians(14), 0)),
        cone("snout", 0.031, 0.007, 0.085, (0.19, 0, 0.044), (0, math.radians(102), 0), f, sides=10),
        blob("nose", 0.0095, (0.233, 0, 0.039), s, segments=10, rings=6),
    ]
    for side in (-1, 1):
        # Narrow, slanted eyes under a heavy brow: the angry look comes from the brow, not size.
        parts.append(blob(f"eye{side}", 0.0105, (0.158, side * 0.029, 0.07), e, scale=(1.3, 0.8, 0.62),
                          rotation=(side * math.radians(-18), 0, 0), segments=10, rings=6))
        parts.append(blob(f"brow{side}", 0.012, (0.153, side * 0.028, 0.08), f, scale=(1.6, 0.75, 0.42),
                          rotation=(side * math.radians(-22), math.radians(-12), 0), segments=10, rings=6))
        # Small ears laid back, the left one with a torn notch.
        ear = disc(f"ear{side}", 0.022, 0.006, (0.105, side * 0.036, 0.098),
                   (math.radians(90 - 35 * side), math.radians(-25), math.radians(-30 * side)), s)
        if side < 0:
            bpy.ops.mesh.primitive_cube_add(size=0.016, location=(0.1, -0.05, 0.115), rotation=(0.6, 0.3, 0.5))
            kit.boolean(ear, bpy.context.active_object)
        parts.append(ear)
        # Long yellowed incisors under the snout tip, and splayed clawed feet.
        parts.append(cone(f"tooth{side}", 0.0055, 0.0018, 0.024, (0.222, side * 0.0055, 0.022),
                          (math.pi, 0, 0), t, sides=5))
        for k, x in enumerate((0.07, -0.08)):
            parts.append(blob(f"foot{side}{k}", 0.016, (x, side * 0.042, 0.008), s, scale=(1.6, 0.9, 0.5), segments=10, rings=6))
            for c in (-1, 0, 1):
                parts.append(cone(f"claw{side}{k}{c}", 0.003, 0.0005, 0.016,
                                  (x + 0.026, side * 0.042 + c * 0.008, 0.004), (0, math.radians(95), 0), t, sides=4))
    # A ragged ridge of tufts down the arched spine, leaning back. Each sits on the top of the
    # rump or shoulders (whichever is higher there), sunk in a little.
    def back_top(x):
        top = 0.0
        for cx, cz, rx, rz in ((-0.045, 0.078, 0.105, 0.075), (0.05, 0.07, 0.069, 0.054)):
            u = (x - cx) / rx
            if abs(u) < 1:
                top = max(top, cz + rz * math.sqrt(1 - u * u))
        return top
    for k in range(9):
        x = 0.075 - k * 0.022
        parts.append(cone(f"tuft{k}", 0.011 + 0.003 * (k % 2), 0.001, 0.034 + 0.01 * (k % 3),
                          (x, (k % 3 - 1) * 0.007, back_top(x) + 0.004),
                          (0, math.radians(-48 - 8 * (k % 2)), 0), f, sides=5))
    # The tail: thick at the root, dragging on the floor and curling at the tip.
    tail = [(-0.14, 0.0, 0.07), (-0.19, 0.008, 0.035), (-0.25, 0.025, 0.012), (-0.32, 0.05, 0.008),
            (-0.38, 0.09, 0.01), (-0.41, 0.14, 0.016)]
    parts.append(tube("tail", tail, 0.013, 0.003, s, sides=7))
    return kit.join(parts, "SM_Rat")


# ---------------------------------------------------------------- output

# Each mesh is modelled at a convenient size, then scaled to its final size here: a rat about
# 50 cm from nose to tail tip, a bat about 55 cm across the wings. That's larger than life, so
# they read in a split view, but still small next to the 1.8 m player.
SCALE = {"SM_Bat_Body": 0.8, "SM_Bat_Wing": 0.8, "SM_Bat_Hanging": 0.8, "SM_Rat": 0.75}

BUILDERS = {
    "SM_Bat_Body": build_bat_body,
    "SM_Bat_Wing": build_bat_wing,
    "SM_Bat_Hanging": build_bat_hanging,
    "SM_Rat": build_rat,
}


def reset():
    """An empty scene. A live Blender only clears its data, because kit.reset() loads factory
    settings, which would unload the MCP add-on that's driving it."""
    if not globals().get("PG_A5_LIVE"):
        kit.reset()
        return
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(coll):
            coll.remove(block)


def build(name):
    """Build one mesh in a fresh scene and return it."""
    reset()
    obj = BUILDERS[name](mats())
    obj.data.name = name
    obj.scale = (SCALE[name],) * 3
    kit._select_only(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    kit.clean_material_slots(obj)
    return obj


def bounds_cm(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def save_blend_and_lineup(out):
    """Save the editable source, PG-A5_Critters.blend, with one collection per mesh, then render
    PG-A5_lineup.png: every critter side by side, with a flying bat put
    together the way BP_CaveBat holds it (wings at the shoulders, raised a little)."""
    reset()
    scene = bpy.context.scene
    shown = []
    for k, name in enumerate(BUILDERS):
        obj = BUILDERS[name](mats())
        obj.data.name = name
        obj.scale = (SCALE[name],) * 3
        kit._select_only(obj)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        coll = bpy.data.collections.new(name)
        scene.collection.children.link(coll)
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        coll.objects.link(obj)
        obj.location.y = 0.35 * k
        shown.append(obj)
    body, wing = bpy.data.objects["SM_Bat_Body"], bpy.data.objects["SM_Bat_Wing"]
    # The body's origin is the bat's center; in Blender's axes the wing spreads toward +Y from
    # its root at Y 0, so the far wing is a mirrored copy.
    body.location = (0.0, -0.45, 0.35)
    wing.location = (0.0, -0.45 + 0.028, 0.35 + 0.012)
    wing.rotation_euler = (math.radians(15), 0, 0)
    other = wing.copy()
    other.name = "SM_Bat_Wing_Mirrored"
    wing.users_collection[0].objects.link(other)
    other.location.y = -0.45 - 0.028
    other.scale.y = -1
    other.rotation_euler = (math.radians(-15), 0, 0)
    hanging = bpy.data.objects["SM_Bat_Hanging"]
    hanging.location = (0.0, 0.05, 0.6)
    rat = bpy.data.objects["SM_Rat"]
    rat.location = (0.05, 0.55, 0.0)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "PG-A5_Critters.blend"), copy=True, compress=True)
    kit.preview_sheet(shown + [other], str(out / "PG-A5_lineup.png"), title="PG-A5 lineup", resolution=640,
                      with_figure=False)


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    metrics = {}
    for name in BUILDERS:
        obj = build(name)
        lo, hi = bounds_cm(obj)
        base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        info = {"triangles": kit.triangles([obj]),
                "size_cm": [round((hi[i] - lo[i]) * 100, 1) for i in range(3)],
                "materials": [mt.name for mt in obj.data.materials]}
        if name == "SM_Bat_Wing":
            # Where the shoulder hinge ends up once cleanup_export puts the pivot at base center.
            info["hinge_from_pivot_cm"] = [round((WING_HINGE[i] * SCALE[name] - base[i]) * 100, 2) for i in range(3)]
        metrics[name] = info
        kit.preview_sheet([obj], str(out / f"{name}_preview.png"), title=name, with_figure=False)
        glb = out / f"{name}.glb"
        kit.export_glb([obj], str(glb))
        subprocess.run([bpy.app.binary_path, "-b", "--factory-startup", "--python",
                        str(REPO / "Tools" / "blender" / "cleanup_export.py"), "--",
                        str(glb), str(out / f"{name}.fbx"), "--name", name, "--overwrite"], check=True)
        glb.unlink()
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    save_blend_and_lineup(out)
    print(json.dumps(metrics, indent=2))


if not globals().get("PG_A5_LIVE") and "--" in sys.argv:
    main(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
