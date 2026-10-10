"""SM_Relic_GoldIdol: the squat, seated gold lion idol from concepts/gold-idol-25cm.png, 25 cm tall,
with a big jade cabochon in a raised bezel on its chest.

Soft carved forms rather than boxes: the body is blocked out from scaled spheres and rounded
cubes, fused with a voxel remesh and smoothed a little. Then crisp grooves are cut with
booleans before a final decimate: the mane's segments and its edge round the face, carved panel
outlines on the chest, shoulders and haunches, the angry eye slits under the brow, the
mouth line, nostril dents, cupped ears, and toe grooves on the paws. Square teeth, the bezel and
the gem are added as their own parts. Faces -Y while it's built; the finish step turns it to face
+X.

Also renders SM_Relic_GoldIdol_compare.png: the concept on the left and a matching three-quarter
front view on the right.

    blender -b --factory-startup --python SourceArt/HC/HC-A1/make_SM_Relic_GoldIdol.py -- /tmp/HC-A1
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import relic_parts as rp  # noqa: E402
from relic_parts import kit, tube  # noqa: E402

NAME = "SM_Relic_GoldIdol"
CONCEPT = os.path.join(rp.REPO, "SourceArt", "PG", "PG-A0", "style-frames", "concepts", "gold-idol-25cm.png")
VOXEL = 0.0035  # remesh voxel size in meters
BODY_TRIANGLES = 8000  # decimate target for the fused, grooved body

kit.reset()
gold = kit.palette_material("M_Gold", kit.PALETTE["relic_gold"], roughness=0.3, metallic=1.0)
# A little glow, so the gem still reads in the dark cave.
jade = kit.palette_material("M_Jade", kit.PALETTE["relic_jade"], roughness=0.25,
                            emission=kit.PALETTE["relic_jade"], emission_strength=0.6)


def blob(name, center, radii, roundness=1.0, rot=(0, 0, 0), segments=32, rings=16):
    """A sphere scaled to `radii`. `roundness` below 1 squares it off toward a rounded cube."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=segments, ring_count=rings)
    obj = bpy.context.active_object
    obj.name = obj.data.name = name
    for v in obj.data.vertices:
        v.co = Vector([math.copysign(abs(c) ** roundness, c) * r for c, r in zip(v.co, radii)])
    obj.location = center
    obj.rotation_euler = [math.radians(a) for a in rot]
    return obj


def apply_modifier(obj, kind, **settings):
    mod = obj.modifiers.new(kind, kind)
    for key, value in settings.items():
        setattr(mod, key, value)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def mirrored(fn):
    """Call fn(side) for the right side (+1) and the left side (-1)."""
    return [fn(side) for side in (1, -1)]


# Block-out, mostly in rounded cubes so the forms read as carved. Body: a pear that's widest at
# the haunches beside it, a broad chest that bulges forward for the gem, round shoulders, front
# legs set wide apart, big front paws and back paws peeking out.
shapes = [
    blob("Torso", (0, 0.0, 0.08), (0.072, 0.058, 0.08), 0.8),
    blob("Chest", (0, -0.034, 0.088), (0.06, 0.04, 0.066), 0.7),
    blob("Belly", (0, -0.005, 0.04), (0.07, 0.054, 0.04), 0.8),
]
shapes += mirrored(lambda s: blob("Haunch", (s * 0.07, 0.014, 0.05), (0.04, 0.05, 0.05), 0.7))
shapes += mirrored(lambda s: blob("Shoulder", (s * 0.07, -0.022, 0.104), (0.032, 0.038, 0.04), 0.7))
shapes += mirrored(lambda s: blob("FrontLeg", (s * 0.066, -0.054, 0.055), (0.025, 0.027, 0.045), 0.65))
shapes += mirrored(lambda s: blob("FrontPaw", (s * 0.066, -0.084, 0.02), (0.034, 0.036, 0.021), 0.6))
shapes += mirrored(lambda s: blob("BackPaw", (s * 0.1, -0.028, 0.014), (0.022, 0.03, 0.015), 0.6))
shapes.append(blob("Tail", (0.072, 0.062, 0.018), (0.03, 0.014, 0.013), 0.8, rot=(0, 0, 40)))

# Head, about 45% of the height, sitting forward on the chest. It's laid out at the size below,
# then scaled up round HEAD_PIVOT, so the head reads big like the concept's.
HEAD_PIVOT = Vector((0, -0.04, 0.15))
HEAD_SCALE = 1.15


def head(p):
    """A point laid out on the head, moved to where it is after the head is scaled up."""
    return HEAD_PIVOT + (Vector(p) - HEAD_PIVOT) * HEAD_SCALE


def head_blob(name, center, radii, roundness=1.0, rot=(0, 0, 0)):
    return blob(name, head(center), [r * HEAD_SCALE for r in radii], roundness, rot)


# A rounded skull, a mane shell over the top and back, a heavy angry brow, narrowed eyes, cheeks,
# a wide muzzle block with a nose pad, a jaw slab, and ears.
shapes += [
    head_blob("Skull", (0, -0.04, 0.19), (0.056, 0.05, 0.05), 0.7),
    head_blob("Mane", (0, -0.015, 0.2), (0.064, 0.058, 0.056), 0.75),
    head_blob("Muzzle", (0, -0.1, 0.176), (0.05, 0.03, 0.024), 0.55),
    head_blob("NosePad", (0, -0.124, 0.189), (0.024, 0.014, 0.014), 0.65),
    head_blob("Jaw", (0, -0.098, 0.145), (0.046, 0.032, 0.016), 0.5),
]
shapes += mirrored(lambda s: head_blob("Brow", (s * 0.026, -0.08, 0.215), (0.03, 0.016, 0.017), 0.65,
                                       rot=(0, -20 * s, 0)))
shapes += mirrored(lambda s: head_blob("Eye", (s * 0.027, -0.086, 0.198), (0.02, 0.013, 0.011), 0.8))
shapes += mirrored(lambda s: head_blob("Cheek", (s * 0.045, -0.09, 0.172), (0.02, 0.022, 0.02), 0.8))
shapes += mirrored(lambda s: head_blob("Ear", (s * 0.056, -0.018, 0.238), (0.018, 0.013, 0.018), 0.85))

# Fuse everything into one soft carved form.
body = kit.join(shapes, "Body")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
apply_modifier(body, "REMESH", mode="VOXEL", voxel_size=VOXEL, adaptivity=0.0)
apply_modifier(body, "SMOOTH", factor=0.5, iterations=4)
body.data.materials.append(gold)


def hit(origin, target):
    """Where a ray from `origin` toward `target` first meets the surface."""
    origin = Vector(origin)
    direction = (Vector(target) - origin).normalized()
    ok, loc, normal, _ = body.ray_cast(origin, direction)
    assert ok, (origin, target)
    return loc, normal, direction


def sink(name, hits, radius, depth, cyclic):
    pts = [loc + direction * radius * depth for loc, _, direction in hits]
    kit.boolean(body, tube(name, pts, radius, cyclic=cyclic, resolution=3, sides_res=1))


def groove_out(name, origin, targets, radius=0.004, depth=0.4, cyclic=False):
    """A crisp round groove traced over the surface by rays cast out of `origin`, inside the body."""
    hits = []
    for t in targets:
        loc, normal, direction = hit(origin, t)
        hits.append((loc, normal, -direction))
    sink(name, hits, radius, depth, cyclic)


def groove_in(name, points, direction, radius=0.004, depth=0.4, cyclic=False):
    """A crisp round groove traced over the surface by parallel rays along `direction`, aimed at
    `points` from outside the body."""
    d = Vector(direction).normalized()
    sink(name, [hit(Vector(p) - d * 0.3, Vector(p)) for p in points], radius, depth, cyclic)


def arc(fn, a, b, steps):
    return [fn(a + (b - a) * i / (steps - 1)) for i in range(steps)]


def ellipse(center, radii, plane, steps=18):
    """Points on an ellipse round `center` in `plane` ("xz" or "yz")."""
    pts = []
    for i in range(steps):
        t = i / steps * 2 * math.pi
        p = list(center)
        p[0 if plane == "xz" else 1] += radii[0] * math.cos(t)
        p[2] += radii[1] * math.sin(t)
        pts.append(p)
    return pts


# Mane: an edge groove framing the face, and two grooves front to back splitting the shell into
# three broad segments.
MANE = head((0, -0.015, 0.2))
groove_out("ManeEdge", MANE, arc(lambda p: MANE + Vector((math.sin(math.radians(p)) * 0.2, -0.13,
                                                          math.cos(math.radians(p)) * 0.19)), -100, 100, 15))
for s in (1, -1):
    groove_out(f"ManeSplit{s}", MANE,
               arc(lambda t: MANE + Vector((s * 0.04, -math.cos(math.radians(t)) * 0.1,
                                            math.sin(math.radians(t)) * 0.1)), 60, 205, 12))

# Carved panels: an oval round the chest, a disc on each shoulder and an oval on each haunch.
groove_in("ChestPanel", ellipse((0, 0, 0.09), (0.05, 0.058), "xz"), (0, 1, 0), cyclic=True)
for s in (1, -1):
    groove_in(f"ShoulderDisc{s}", ellipse((0, -0.022, 0.106), (0.024, 0.024), "yz"), (-s, 0, 0), cyclic=True)
    groove_in(f"HaunchPanel{s}", ellipse((0, 0.016, 0.05), (0.034, 0.03), "yz"), (-s, 0, 0), cyclic=True)

# Angry, narrowed eye slits under the brow, slanting down toward the nose.
for s in (1, -1):
    groove_in(f"EyeSlit{s}", [head((s * x, 0, z)) for x, z in ((0.012, 0.205), (0.026, 0.208), (0.04, 0.212),
                                                                 (0.048, 0.215))], (0, 1, 0), 0.0035)
# The mouth line between muzzle and jaw.
MOUTH_Z = head((0, 0, 0.156)).z
groove_in("Mouth", [(x, 0, MOUTH_Z) for x in (-0.048, -0.024, 0.0, 0.024, 0.048)], (0, 1, 0), 0.0045)
# Two nostril dents in the nose pad.
for s in (1, -1):
    loc, _, direction = hit(head((s * 0.011, -0.3, 0.19)), head((s * 0.011, 0, 0.188)))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, segments=12, ring_count=8, location=loc + direction * 0.0015)
    kit.boolean(body, bpy.context.active_object)
# Cupped ears, open to the front.
for s in (1, -1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, segments=16, ring_count=8,
                                         location=head((s * 0.056, -0.032, 0.24)))
    kit.boolean(body, bpy.context.active_object)
# Three toes on each front paw and each back paw.
for s in (1, -1):
    for paw, spread, r in (((s * 0.066, -0.084, 0.02), 0.3, 0.0038), ((s * 0.1, -0.028, 0.014), 0.28, 0.003)):
        for o in (-spread, spread):
            groove_out(f"Toe{s}{o}", paw, arc(lambda t: (paw[0] + o * 0.1, paw[1] - math.cos(math.radians(t)) * 0.1,
                                                         paw[2] + math.sin(math.radians(t)) * 0.1), -20, 60, 6), r)
# A flat base, so it sits steady on the altar.
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.5 + 0.004))
kit.boolean(body, bpy.context.active_object)
# Decimate last, so the triangle budget holds however many grooves there are.
apply_modifier(body, "DECIMATE", ratio=BODY_TRIANGLES / kit.triangles([body]), use_collapse_triangulate=True)

bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
parts = [body]

# Square teeth on the jaw slab: big ones at the corners, smaller ones between.
for x, size in ((-0.034, 0.014), (-0.012, 0.011), (0.012, 0.011), (0.034, 0.014)):
    loc, _, _ = hit((x, -0.3, MOUTH_Z), (x, 0, MOUTH_Z))
    parts.append(rp.block(f"Tooth{x}", (size, size * 0.8, size * 1.1), (loc.x, loc.y + 0.002, loc.z - 0.001),
                          bevel=0.25, segments=2, wobble=0.04, seed=int(abs(x) * 1000), mat=gold))

# The gem: a big jade cabochon, about 40% of the chest's width, in a raised gold bezel.
loc, normal, _ = hit((0, -0.3, 0.09), (0, 0, 0.09))
facing = normal.to_track_quat("Z", "Y").to_euler()
bezel = rp.ring("Bezel", 0.031, 0.0072, loc + normal * 0.004, major_segments=28, minor_segments=8, mat=gold)
bezel.rotation_euler = facing
gem = rp.ball("Gem", 0.0285, loc + normal * 0.006, scale=(1, 1, 0.62), segments=24, rings=12, mat=jade)
gem.rotation_euler = facing
parts += [bezel, gem]

idol = rp.finish(parts, NAME, height=0.25)
out = rp.out_dir()
rp.deliver(idol, NAME, out)


def compare_sheet(objects, path, res=768):
    """The concept on the left, and a three-quarter front render from about the same angle on the
    right, on a light grey studio background like the concept's."""
    s = bpy.context.scene
    world = bpy.data.worlds.new("Studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = kit.hex_rgba("#BDBDBD")
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    s.world = world
    lo, hi = kit._bounds(objects)
    look = (lo + hi) / 2
    radius = (hi - lo).length / 2
    made = []
    for name, color, energy, direction in (("Key", "#FFF4E6", 18, (1.0, 0.9, 1.3)),
                                           ("Fill", "#E8ECF5", 6, (0.6, -1.2, 0.4)),
                                           ("Top", "#FFFFFF", 6, (0.0, 0.0, 1.0)),
                                           ("Rim", "#FFFFFF", 9, (-1.2, 0.3, 0.8))):
        data = bpy.data.lights.new(name, "AREA")
        data.color = kit.hex_rgba(color)[:3]
        data.energy = energy
        data.size = 0.6
        light = bpy.data.objects.new(name, data)
        s.collection.objects.link(light)
        light.location = look + Vector(direction).normalized() * 0.9
        light.rotation_euler = (look - light.location).to_track_quat("-Z", "Y").to_euler()
        made.append(light)
    cam_data = bpy.data.cameras.new("CompareCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("CompareCam", cam_data)
    s.collection.objects.link(cam)
    s.camera = cam
    az, el = math.radians(32), math.radians(12)
    dist = radius / math.tan(cam_data.angle / 2) * 1.08
    cam.location = look + Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * dist
    cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    s.render.resolution_x = s.render.resolution_y = res
    s.render.filepath = path[:-4] + "_render.png"
    # AgX washes out saturated gold; Standard is closer to how the painted concept shows color.
    s.view_settings.view_transform = "Standard"
    bpy.ops.render.render(write_still=True)
    s.view_settings.view_transform = "AgX"

    import numpy as np
    sheet = np.ones((res, res * 2, 4), dtype=np.float32)
    for col, src in enumerate((CONCEPT, s.render.filepath)):
        img = bpy.data.images.load(src)
        img.scale(res, res)
        sheet[:, col * res:(col + 1) * res] = np.array(img.pixels[:], dtype=np.float32).reshape(res, res, 4)
        bpy.data.images.remove(img)
    os.remove(s.render.filepath)
    img = bpy.data.images.new("Compare", res * 2, res, alpha=True)
    img.pixels = sheet.ravel()
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    for o in made + [cam]:
        bpy.data.objects.remove(o, do_unlink=True)
    print(f"COMPARE {path}")


compare_sheet([idol], os.path.join(out, f"{NAME}_compare.png"))
