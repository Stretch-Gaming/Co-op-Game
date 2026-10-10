"""Shared helpers for scripted Blender assets: palette materials, a few chunky shapes, and a
four-angle preview sheet under cave-style lighting. Blender 5.x, run headless:

    blender -b --factory-startup --python SourceArt/HZ/HZ-A2/make_torch.py -- <output folder>

In a generator script:

    import sys; sys.path.append("<repo>/Tools/blender")
    import asset_kit as kit
    kit.reset()
    mat = kit.palette_material("Rock", "#4A4652")
    rock = kit.faceted_rock("SM_Rock_A", size=(1.0, 0.9, 0.75), seed=3, material=mat)
    kit.preview_sheet([rock], "<output folder>/SM_Rock_A_preview.png", title="SM_Rock_A")
    kit.export_glb([rock], "<output folder>/SM_Rock_A.glb")

Next to the 1.8 m figure, a prop under about 50 cm is only a few pixels tall, so also render
`<name>_preview_closeup.png` with `with_figure=False`.

Then clean up the GLB into the FBX you commit:

    blender -b --factory-startup --python Tools/blender/cleanup_export.py -- SM_Rock_A.glb SM_Rock_A.fbx --name SM_Rock_A
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

# The palette from docs/art/style.md. Each color has one job.
PALETTE = {
    "torch_amber": "#FFB347",
    "crystal_teal": "#3FD0C9",
    "relic_gold": "#E8B33A",
    "relic_jade": "#3FA672",
    "ghost_white": "#D6F0FF",
    "trap_red": "#FF4A2A",
    "shadow": "#1E2433",
    "rock_mid": "#4A4652",
    "rock_light": "#7A6E68",
    "sandstone": "#D9A86C",
}

# The preview sheet's fill light: crystal teal mixed with 70% white. At full strength, teal
# turns metallic gold green.
FILL_TEAL = "#C5F1EF"


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (alpha,)


def reset():
    """Start from an empty scene, with meters as the unit."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = "METRIC"
    s.unit_settings.scale_length = 1.0


def palette_material(name, hex_color, roughness=0.75, metallic=0.0, emission=None, emission_strength=0.0):
    """A plain Principled material in a palette color. Unreal re-materials everything with
    M_Stylized instances, so this is only for previews and for telling parts apart on import."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgba(hex_color)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = hex_rgba(emission)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def _select_only(obj):
    """Select just this object and make it active, so operators don't touch anything else."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _apply_modifiers(obj):
    _select_only(obj)
    for m in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def _smooth_shading(obj, smooth_deg, bevel_deg=None):
    """Shade every face smooth and mark edges sharper than `smooth_deg` as sharp, except edges
    sharper than `bevel_deg`: the bevel rounds those off, so they stay smooth."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for f in bm.faces:
        f.smooth = True
    sharp = math.radians(smooth_deg)
    beveled = math.radians(bevel_deg) if bevel_deg is not None else math.inf
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        angle = e.calc_face_angle(0.0)
        if angle > beveled:
            e.smooth = True
        elif angle > sharp:
            e.smooth = False
    bm.to_mesh(obj.data)
    bm.free()


def chunky_bevel(obj, width=0.03, segments=2, angle_deg=35, smooth=True, smooth_deg=35):
    """Wide, soft bevels that catch light. `angle_deg` is the sharpest edge that still gets
    beveled: 35 suits blocks, about 12 suits faceted rock. With `smooth`, the bevels shade soft
    and hardened normals keep the big flat faces flat, so large faces and boolean n-gons don't
    shade in streaks; edges the bevel skips stay sharp if they're sharper than `smooth_deg`.
    Only `obj` changes, whatever else is selected. A width of 0 skips the bevel."""
    _select_only(obj)
    if smooth:
        # Shading goes on before the bevel: hardened normals are worked out from it, and
        # changing sharp edges afterwards would scramble them.
        _smooth_shading(obj, smooth_deg, angle_deg if width > 0 else None)
    if width > 0:
        bev = obj.modifiers.new("ChunkyBevel", "BEVEL")
        bev.width = width
        bev.segments = segments
        bev.limit_method = "ANGLE"
        bev.angle_limit = math.radians(angle_deg)
        bev.harden_normals = smooth
        bev.use_clamp_overlap = True
        _apply_modifiers(obj)


def faceted_rock(name, size=(1.0, 1.0, 0.8), seed=0, facets=44, flat_base=True, bevel=0.03, material=None):
    """A chunky, faceted rock like the style frames: the convex hull of jittered points, so the
    facets are big and clean and there are no holes. Base center at the origin."""
    rng = random.Random(seed)
    pts = []
    for _ in range(facets):
        theta = rng.uniform(0, 2 * math.pi)
        z = rng.uniform(-1, 1)
        r = math.sqrt(1 - z * z)
        jitter = rng.uniform(0.82, 1.08)
        pts.append(Vector((r * math.cos(theta), r * math.sin(theta), z)) * jitter)
    bm = bmesh.new()
    for p in pts:
        bm.verts.new((p.x * size[0] / 2, p.y * size[1] / 2, p.z * size[2] / 2))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    if flat_base:
        # Flatten the lowest part so the rock sits on the floor.
        floor = -size[2] / 2 + size[2] * 0.12
        for v in bm.verts:
            v.co.z = max(v.co.z, floor)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.001)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    if bevel:
        chunky_bevel(obj, width=bevel * max(size), angle_deg=12, smooth_deg=30)
    sit_on_floor(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def chunky_block(name, size=(1.0, 1.0, 0.3), bevel=0.04, wobble=0.015, seed=0, material=None):
    """A cut-stone block with soft, slightly uneven bevels: plates, altars, pedestals, lintels.
    `wobble` nudges the corners so no edge is perfectly straight (style rule 1). Keep it at 0 for
    parts whose footprint must match a Blueprint exactly. A bevel of 0 leaves the block sharp, for
    blocks you cut or reshape first and then pass to chunky_bevel."""
    rng = random.Random(seed)
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if wobble:
        for v in obj.data.vertices:
            v.co.x += rng.uniform(-wobble, wobble)
            v.co.y += rng.uniform(-wobble, wobble)
            if v.co.z > 0:
                v.co.z += rng.uniform(-wobble, wobble)
    if bevel:
        chunky_bevel(obj, width=bevel)
    sit_on_floor(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def sit_on_floor(obj):
    """Move the object so its lowest point is at Z 0 and its footprint is centered, which
    matches the pivot rule in docs/assets.md (base center)."""
    bpy.context.view_layer.update()
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    obj.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bpy.context.view_layer.update()


def join(objects, name):
    """Join parts into one object, keeping each part's material."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name
    return obj


def boolean(obj, cutter, operation="DIFFERENCE", keep_cutter=False):
    """An exact boolean, applied: cut grooves and glyphs before chunky_bevel, so the cut edges
    get soft bevels too. The cut faces take the object's own material. Removes the cutter
    unless `keep_cutter`."""
    mod = obj.modifiers.new("Boolean", "BOOLEAN")
    mod.operation = operation
    mod.solver = "EXACT"
    mod.object = cutter
    _select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if not obj.data.polygons:
        raise RuntimeError(f"Boolean with {cutter.name} left {obj.name} empty")
    clean_material_slots(obj)
    if not keep_cutter:
        bpy.data.objects.remove(cutter, do_unlink=True)
    return obj


def clean_material_slots(obj):
    """Drop empty material slots and give their faces the object's first material. An exact
    boolean adds the cutter's empty slot, and faces on it would export with no material.
    Returns how many faces moved."""
    me = obj.data
    mats = list(me.materials)
    keep = [i for i, m in enumerate(mats) if m is not None]
    if not keep or len(keep) == len(mats):
        return 0
    new_index = {old: new for new, old in enumerate(keep)}
    old = [0] * len(me.polygons)
    me.polygons.foreach_get("material_index", old)
    # Removing a slot shifts the faces above it down by one, so set every face afterwards.
    for i in reversed(range(len(mats))):
        if mats[i] is None:
            me.materials.pop(index=i)
    me.polygons.foreach_set("material_index", [new_index.get(i, 0) for i in old])
    me.update()
    return sum(1 for i in old if i not in new_index)


def triangles(objects):
    return sum(len(p.vertices) - 2 for o in objects if o.type == "MESH" for p in o.data.polygons)


def _bounds(objects):
    bpy.context.view_layer.update()  # pick up any moves made since the last update
    pts = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    return (Vector([min(p[i] for p in pts) for i in range(3)]),
            Vector([max(p[i] for p in pts) for i in range(3)]))


def _setup_lighting():
    s = bpy.context.scene
    world = bpy.data.worlds.new("CavePreview")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex_rgba(PALETTE["shadow"])
    bg.inputs["Strength"].default_value = 1.2
    s.world = world
    # A warm key that leans toward torchlight without turning grey stone orange, a soft teal fill,
    # a neutral top light and a white rim, so the asset's own colors still read.
    lights = [
        ("Key_Warm", "AREA", "#FFD7A3", 260, (2.5, -2.0, 3.0), 3.0),
        ("Fill_CrystalTeal", "AREA", FILL_TEAL, 90, (-2.5, -1.5, 1.5), 3.0),
        ("Top_Neutral", "AREA", "#E6E9F2", 150, (0.0, 0.0, 4.0), 4.0),
        ("Rim_White", "AREA", "#FFFFFF", 200, (-1.0, 3.0, 2.5), 2.0),
    ]
    made = []
    for name, kind, color, energy, loc, size in lights:
        data = bpy.data.lights.new(name, kind)
        data.color = hex_rgba(color)[:3]
        data.energy = energy
        data.size = size
        obj = bpy.data.objects.new(name, data)
        s.collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector((0, 0, 0.5)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        made.append(obj)
    return made


def _fit_lights(lights, lo, hi):
    """The rig suits props up to about 2.5 m. For bigger assets, move the lights out and grow
    them with the asset, and raise their energy with the square of the distance, so a 6 m pillar
    gets the same light as a 1 m prop. They aim at the asset's middle, or 0.5 m up if that's
    higher."""
    size = hi - lo
    scale = max(1.0, max(size) / 2.5)
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    aim = base + Vector((0, 0, max(0.5 * scale, size.z / 2)))
    for light in lights:
        light.location = base + light.location * scale
        light.data.size *= scale
        light.data.energy *= scale * scale
        light.rotation_euler = (aim - light.location).to_track_quat("-Z", "Y").to_euler()


def _scale_figure(height=1.8):
    """A 1.8 m capsule standing in for the player, so scale is easy to judge."""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=height - 0.44, location=(0, 0, height / 2))
    body = bpy.context.active_object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, height - 0.22))
    head = bpy.context.active_object
    fig = join([body, head], "ScaleFigure_1_8m")
    fig.data.materials.append(palette_material("ScaleFigure", "#9AA3B5", roughness=0.9))
    return fig


def preview_sheet(objects, path, title="", resolution=512, with_figure=True):
    """Render four angles (front three-quarter, back three-quarter, side, top-down three-quarter)
    under amber key, teal fill and blue-violet ambient light, and save them as one 2x2 PNG.
    A 1.8 m scale figure stands to the left unless `with_figure` is False. The lights grow with
    the asset, so tall and wide assets are lit like small props."""
    s = bpy.context.scene
    lo, hi = _bounds(objects)
    size = hi - lo
    extra = []
    if with_figure:
        fig = _scale_figure()
        fig.location.x = lo.x - 0.6
        extra.append(fig)
    lights = _setup_lighting()
    _fit_lights(lights, lo, hi)
    extra += lights
    all_lo, all_hi = _bounds([o for o in objects + extra if o.type == "MESH"])
    radius = max((all_hi - all_lo).length / 2, 0.2)
    look = (all_lo + all_hi) / 2
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    s.collection.objects.link(cam)
    s.camera = cam
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x = s.render.resolution_y = resolution
    s.render.film_transparent = False
    s.view_settings.view_transform = "AgX"
    dist = radius / math.tan(cam_data.angle / 2) * 1.02
    views = [(-35, 20), (145, 20), (90, 8), (-35, 55)]
    tiles = []
    for i, (az, el) in enumerate(views):
        a, e = math.radians(az), math.radians(el)
        cam.location = look + Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * dist
        cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
        tile_path = f"{path[:-4]}_view{i}.png"
        s.render.filepath = tile_path
        bpy.ops.render.render(write_still=True)
        tiles.append(tile_path)
    _combine(tiles, path, resolution)
    import os
    for t in tiles:
        os.remove(t)
    print(f"PREVIEW {path} | {title} | {triangles(objects)} triangles | "
          f"{size.x * 100:.0f} x {size.y * 100:.0f} x {size.z * 100:.0f} cm")
    for o in extra:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)


def _combine(tile_paths, out_path, res):
    import numpy as np
    sheet = np.zeros((res * 2, res * 2, 4), dtype=np.float32)
    for i, p in enumerate(tile_paths):
        img = bpy.data.images.load(p)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(res, res, 4)
        row, col = divmod(i, 2)
        # Blender image rows start at the bottom: tile 0 goes top left.
        sheet[(1 - row) * res:(2 - row) * res, col * res:(col + 1) * res] = px
        bpy.data.images.remove(img)
    out = bpy.data.images.new("PreviewSheet", res * 2, res * 2, alpha=True)
    out.pixels = sheet.ravel()
    out.filepath_raw = out_path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)


def export_glb(objects, path):
    """Export only these objects as a GLB, ready for cleanup_export.py. Empty material slots are
    dropped first, and an object with no material at all stops the export."""
    for o in objects:
        if o.type != "MESH":
            continue
        moved = clean_material_slots(o)
        if moved:
            print(f"WARNING {o.name}: {moved} faces were on an empty material slot; "
                  f"gave them {o.data.materials[0].name}")
        if not any(o.data.materials):
            raise RuntimeError(f"{o.name} has no material; give it a palette_material")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format="GLB",
                              export_apply=True, export_yup=True)
    print(f"EXPORTED {path}")
