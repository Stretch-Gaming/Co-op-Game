"""PG-A7 the taker. Original Blender Python modeling (taker_shapes.py): a long-limbed shadow
creature and the separate reaching arm for the wall taking. Bakes each mesh's 1K base color
(sRGB) and packed mask (red AO floored at .32, green roughness, blue metallic) with Cycles,
exports one FBX per mesh with its sockets, renders preview sheets, the 15 m dark read test,
the lunge strip and the arm coming out of a wall, and saves the editable .blend:

    blender -b --factory-startup --python SourceArt/PG/PG-A7/build_taker.py -- SourceArt/PG/PG-A7

Blender +Z is up and both meshes face +X. Units are metres; the FBX is in centimetres.

- SM_Taker: origin on the floor under the middle of the feet, which is also the lunge pivot.
  Material slot 0 is the body, slot 1 the eyes (ghost white, the only white on it).
- SM_TakerArm: origin where the arm leaves the wall. The wall faces +X; the root is buried
  behind it (X < 0) and the hand opens toward the victim at about X 1.9 m.

The bake and export helpers are adapted from SourceArt/PG/PG-6/build_lever_gate.py.
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.append(str(REPO / "Tools" / "blender"))
sys.path.append(str(HERE))
import asset_kit as kit  # noqa: E402
import taker_look as look  # noqa: E402
import taker_shapes as shapes  # noqa: E402

OUT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
for folder in ("textures", "previews"):
    (OUT / folder).mkdir(parents=True, exist_ok=True)

kit.reset()
scene = bpy.context.scene
lin = look.lin

# ---------------------------------------------------------------------------
# Bake sources: emission shaders with a dark-to-light ramp on the object's generated Z and a
# broad painted mottle, baked to the base color. Roughness and metallic sit on the material.
# The body is the shadow family (blue-violet, never black); ghost white is only on the eyes.
PALETTE = {
    'shadow': (look.BODY_LO, look.BODY_HI, .86, 0),
    'eyes': (look.GHOST_WHITE, look.GHOST_WHITE, .30, 0),
}


sources = {}


def source_mat(kind):
    if kind in sources:
        return sources[kind]
    lo, hi, rough, metal = PALETTE[kind]
    m = bpy.data.materials.new('SRC_' + kind)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    links = m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial')
    emit = n.new('ShaderNodeEmission')
    links.new(emit.outputs[0], out.inputs['Surface'])
    tex = n.new('ShaderNodeTexCoord')
    sep = n.new('ShaderNodeSeparateXYZ')
    links.new(tex.outputs['Generated'], sep.inputs[0])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*lin(lo), 1)
    ramp.color_ramp.elements[1].color = (*lin(hi), 1)
    links.new(sep.outputs['Z'], ramp.inputs[0])
    if kind == 'shadow':
        # Big soft patches, a few per metre: painted, not photographed.
        noise = n.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 1.6
        noise.inputs['Detail'].default_value = 1.0
        links.new(tex.outputs['Object'], noise.inputs['Vector'])
        mix = n.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = .22
        links.new(ramp.outputs[0], mix.inputs[1])
        links.new(noise.outputs['Color'], mix.inputs[2])
        links.new(mix.outputs[0], emit.inputs['Color'])
    else:
        links.new(ramp.outputs[0], emit.inputs['Color'])
    m['roughness'] = rough
    m['metallic'] = metal
    m['kind'] = kind
    sources[kind] = m
    return m


# ---------------------------------------------------------------------------
assets, metrics = {}, {}
BUDGET = {'SM_Taker': 15000, 'SM_TakerArm': 6000}
PIVOTS = {
    'SM_Taker': ('On the floor under the middle of the feet; also the lunge pivot. Faces +X. '
                 'Lunge: pitch forward about it (negative pitch in Unreal) while moving forward.'),
    'SM_TakerArm': ('Where the arm leaves the wall. The wall faces +X; the root is buried behind it '
                    '(X < 0); the open hand reaches toward the victim along +X.'),
}


def bounds(o):
    co = [o.matrix_world @ v.co for v in o.data.vertices]
    return [[min(c[a] for c in co), max(c[a] for c in co)] for a in range(3)]


def active(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def unwrap(o):
    active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.012, area_weight=.5)
    bpy.ops.object.mode_set(mode='OBJECT')


def finish(name, o, extra_slots=()):
    o.name = name
    o.data.name = name
    o.data.materials.clear()
    o.data.materials.append(source_mat('shadow'))
    for m in extra_slots:
        o.data.materials.append(m)
    unwrap(o)
    o.data.calc_loop_triangles()
    b = bounds(o)
    metrics[name] = {
        'triangles': len(o.data.loop_triangles),
        'dimensions_cm': [round((hi - lo) * 100, 1) for lo, hi in b],
        'bounds_cm': [[round(lo * 100, 1), round(hi * 100, 1)] for lo, hi in b],
        'pivot': PIVOTS[name],
        'uv': 'UV0: one packed smart-project atlas' + (', shared by both slots' if extra_slots else ''),
        'health': shapes.health(o),
    }
    assert metrics[name]['triangles'] <= BUDGET[name], (name, metrics[name]['triangles'])
    assets[name] = o
    print('MODEL', name, metrics[name], flush=True)
    return o


def build_taker():
    body, eyes, _ = shapes.build_body('SM_Taker', shapes.stalker, collection=scene.collection)
    eye_src = source_mat('eyes')
    for e in eyes:
        e.data.materials.append(eye_src)
    body.data.materials.append(source_mat('shadow'))
    bpy.ops.object.select_all(action='DESELECT')
    for x in [body] + eyes:
        x.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    o = bpy.context.object
    # Slot 0 body, slot 1 eyes, whatever order the join left them in.
    eye_faces = [p.index for p in o.data.polygons if o.data.materials[p.material_index].get('kind') == 'eyes']
    o.data.materials.clear()
    finish('SM_Taker', o, extra_slots=[eye_src])
    for p in o.data.polygons:
        p.material_index = 0
    for i in eye_faces:
        o.data.polygons[i].material_index = 1
    metrics['SM_Taker']['material_slots'] = ['0 Body (shadow family)', '1 Eyes (ghost white)']
    metrics['SM_Taker']['eye_triangles'] = sum(len(o.data.polygons[i].vertices) - 2 for i in eye_faces)
    assert metrics['SM_Taker']['eye_triangles'] > 0
    return o


def build_arm():
    arm, _ = shapes.build_arm('SM_TakerArm', collection=scene.collection)
    finish('SM_TakerArm', arm)
    metrics['SM_TakerArm']['material_slots'] = ['0 Body (shadow family)']
    return arm


# ---------------------------------------------------------------------------
# Sockets: Unreal's FBX importer turns empties named SOCKET_<name> under the mesh into static
# mesh sockets. Their positions are also in metrics.json, in case an import drops them.
sockets = {}


def socket(mesh_name, sock, loc, note):
    o = bpy.data.objects.new(f'SOCKET_{sock}', None)
    scene.collection.objects.link(o)
    o.empty_display_size = .1
    o.location = loc
    o.parent = assets[mesh_name]
    sockets.setdefault(mesh_name, []).append(o)
    ue = [round(loc[0] * 100, 1), round(-loc[1] * 100, 1), round(loc[2] * 100, 1)]
    metrics[mesh_name].setdefault('sockets_unreal_cm', {})[sock] = {'location': ue, 'use': note}


def eye_centre(o):
    pts = [o.data.vertices[v].co for p in o.data.polygons if p.material_index == 1 for v in p.vertices]
    return sum(pts, Vector()) / len(pts)


def palm_centre(o, near, radius=.12):
    pts = [v.co for v in o.data.vertices if (v.co - Vector(near)).length < radius]
    return sum(pts, Vector()) / len(pts)


# ---------------------------------------------------------------------------
# Bake (from PG-6): base color from the emission sources, AO, then roughness/metallic as a flat
# emission; pack AO (floored at .32), roughness and metallic into one ORM mask.
def image_new(name, colorspace):
    im = bpy.data.images.new(name, width=1024, height=1024, alpha=False)
    im.colorspace_settings.name = colorspace
    return im


def target(mat, im):
    n = mat.node_tree.nodes
    for node in n:
        node.select = False
    node = n.new('ShaderNodeTexImage')
    node.image = im
    node.select = True
    n.active = node
    return node


def write_png(im, path):
    im.filepath_raw = str(path)
    im.file_format = 'PNG'
    im.save()


def bake_asset(name, o):
    print('BAKE START', name, flush=True)
    for other in bpy.data.objects:
        other.hide_render = other is not o
    active(o)
    mats = list(o.data.materials)
    color = image_new('T_' + name[3:] + '_BaseColor', 'sRGB')
    nodes = [target(m, color) for m in mats]
    bpy.ops.object.bake(type='EMIT')
    write_png(color, OUT / 'textures' / f'{color.name}.png')
    for m, n in zip(mats, nodes):
        m.node_tree.nodes.remove(n)
    ao = image_new(name + '_AO_temp', 'Non-Color')
    nodes = [target(m, ao) for m in mats]
    bpy.ops.object.bake(type='AO')
    for m, n in zip(mats, nodes):
        m.node_tree.nodes.remove(n)
    rm = image_new(name + '_RM_temp', 'Non-Color')
    nodes = [target(m, rm) for m in mats]
    original = []
    for m in mats:
        em = next(v for v in m.node_tree.nodes if v.type == 'EMISSION')
        socket_in = em.inputs['Color']
        original.append((m, socket_in.links[0].from_socket))
        for link in list(socket_in.links):
            m.node_tree.links.remove(link)
        socket_in.default_value = (1, m['roughness'], m['metallic'], 1)
    bpy.ops.object.bake(type='EMIT')
    for m, from_socket in original:
        em = next(v for v in m.node_tree.nodes if v.type == 'EMISSION')
        m.node_tree.links.new(from_socket, em.inputs['Color'])
    for m, n in zip(mats, nodes):
        m.node_tree.nodes.remove(n)
    a = np.empty(1024 * 1024 * 4, dtype=np.float32)
    r = np.empty_like(a)
    ao.pixels.foreach_get(a)
    rm.pixels.foreach_get(r)
    a = a.reshape((1024, 1024, 4))
    r = r.reshape((1024, 1024, 4))
    r[:, :, 0] = np.maximum(.32, a[:, :, 0])
    r[:, :, 3] = 1
    packed = image_new('T_' + name[3:] + '_ORM', 'Non-Color')
    packed.pixels.foreach_set(r.ravel())
    packed.update()
    write_png(packed, OUT / 'textures' / f'{packed.name}.png')
    bpy.data.images.remove(ao)
    bpy.data.images.remove(rm)
    # Preview materials: roughly what M_Stylized does with the two textures, plus a glowing
    # eye slot standing in for the suggested emissive eye material.
    previews = []
    for m in mats:
        kind = m['kind']
        # Named after the suggested Unreal instances, so the imported slots carry these names.
        pm = bpy.data.materials.new(f'MI_{name[3:]}_{"Eyes" if kind == "eyes" else "Body"}')
        pm.use_nodes = True
        n = pm.node_tree.nodes
        links = pm.node_tree.links
        bs = next(v for v in n if v.type == 'BSDF_PRINCIPLED')
        col = n.new('ShaderNodeTexImage')
        col.image = color
        col.label = 'sRGB base color'
        orm = n.new('ShaderNodeTexImage')
        orm.image = packed
        orm.label = 'Linear R AO / G Roughness / B Metallic'
        sep = n.new('ShaderNodeSeparateColor')
        links.new(orm.outputs['Color'], sep.inputs[0])
        mix = n.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = .35
        links.new(col.outputs['Color'], mix.inputs[1])
        links.new(sep.outputs['Red'], mix.inputs[2])
        links.new(mix.outputs[0], bs.inputs['Base Color'])
        links.new(sep.outputs['Green'], bs.inputs['Roughness'])
        links.new(sep.outputs['Blue'], bs.inputs['Metallic'])
        if kind == 'eyes':
            links.new(col.outputs['Color'], bs.inputs['Emission Color'])
            bs.inputs['Emission Strength'].default_value = 8.0
        pm['kind'] = kind
        previews.append(pm)
    # Swap in place: clearing the slots would reset every face to slot 0.
    for i, pm in enumerate(previews):
        o.data.materials[i] = pm
    for sm in mats:
        sm.use_fake_user = True  # keep the bake sources in the .blend
    tri = o.modifiers.new('Export triangulation', 'TRIANGULATE')
    active(o)
    bpy.ops.object.modifier_apply(modifier=tri.name)
    color.pack()
    packed.pack()
    print('BAKE DONE', name, flush=True)


def export_fbx(name):
    o = assets[name]
    bpy.ops.object.select_all(action='DESELECT')
    for x in [o] + sockets.get(name, []):
        x.hide_set(False)
        x.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(
        filepath=str(OUT / f'{name}.fbx'), use_selection=True, object_types={'MESH', 'EMPTY'},
        global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Y', axis_up='Z', use_mesh_modifiers=True, mesh_smooth_type='FACE',
        use_tspace=False, path_mode='RELATIVE', embed_textures=False, add_leaf_bones=False,
        bake_anim=False)
    print('EXPORTED', name, flush=True)


# ---------------------------------------------------------------------------
# Previews.
def only_render(objects):
    keep = set(objects)
    for other in bpy.data.objects:
        other.hide_render = other not in keep and other.type != 'LIGHT'


def combine_row(paths, out_path, w, h):
    sheet = np.zeros((h, w * len(paths), 4), dtype=np.float32)
    for i, p in enumerate(paths):
        img = bpy.data.images.load(str(p))
        sheet[:, i * w:(i + 1) * w] = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        bpy.data.images.remove(img)
        Path(p).unlink()
    out = bpy.data.images.new('Row', w * len(paths), h, alpha=True)
    out.pixels = sheet.ravel()
    out.filepath_raw = str(out_path)
    out.file_format = 'PNG'
    out.save()
    bpy.data.images.remove(out)


def dark_read_sheet(o):
    tiles = []
    for yaw in (0, 55, 120):
        o.rotation_euler.z = math.radians(yaw)
        only_render([o])
        p = OUT / 'previews' / f'_read_{yaw}.png'
        look.dark_read(scene, p)
        tiles.append(p)
    o.rotation_euler.z = 0
    combine_row(tiles, OUT / 'previews' / 'SM_Taker_read_15m.png', 640, 360)


def studio(objects, cam_loc, aim, path, res=(640, 640), lens=35, wall=None):
    """One render under the kit's cave lights, from a chosen camera."""
    col = bpy.data.collections.new('Studio')
    scene.collection.children.link(col)
    lights = kit._setup_lighting()
    lo, hi = kit._bounds([x for x in objects if x.type == 'MESH'])
    kit._fit_lights(lights, lo, hi)
    extra = list(lights)
    if wall:
        extra.append(look._plane('Studio_Wall', wall[0], wall[1], wall[2],
                                 look.plain('M_Studio_Rock', '#4A4652'), col))
    cam_d = bpy.data.cameras.new('StudioCam')
    cam_d.lens = lens
    cam = bpy.data.objects.new('StudioCam', cam_d)
    col.objects.link(cam)
    cam.location = cam_loc
    cam.rotation_euler = (Vector(aim) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    only_render(list(objects) + extra)
    scene.camera = cam
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    for x in extra + [cam]:
        bpy.data.objects.remove(x, do_unlink=True)
    bpy.data.collections.remove(col)


def lunge_strip(o):
    """Rest, half and full lunge, seen side on: pitch about the floor pivot plus a step forward."""
    tiles = []
    for i, (deg, step) in enumerate(((0, 0), (12, .45), (24, .95))):
        o.rotation_euler = (0, math.radians(deg), 0)
        o.location = (step, 0, 0)
        bpy.context.view_layer.update()
        p = OUT / 'previews' / f'_lunge_{i}.png'
        studio([o], (1.0, -6.2, 1.5), (1.0, 0, 1.3), p, res=(512, 640), lens=35)
        tiles.append(p)
    o.rotation_euler = (0, 0, 0)
    o.location = (0, 0, 0)
    combine_row(tiles, OUT / 'previews' / 'SM_Taker_lunge.png', 512, 640)


def arm_in_wall(arm):
    """The arm out of a wall at chest height: from the side, and from the victim's eyes."""
    arm.location = (0, 0, 1.3)
    bpy.context.view_layer.update()
    wall = ((4, 6), (0, 0, 1.8), (0, math.radians(90), 0))
    tiles = []
    p = OUT / 'previews' / '_arm_side.png'
    studio([arm], (2.4, -3.4, 2.0), (1.0, 0, 1.3), p, res=(640, 640), lens=30, wall=wall)
    tiles.append(p)
    p = OUT / 'previews' / '_arm_victim.png'
    studio([arm], (3.5, .3, 1.65), (1.2, 0, 1.45), p, res=(640, 640), lens=26, wall=wall)
    tiles.append(p)
    arm.location = (0, 0, 0)
    combine_row(tiles, OUT / 'previews' / 'SM_TakerArm_in_wall.png', 640, 640)


# ---------------------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.render.bake.margin = 12
scene.render.bake.use_clear = True

taker = build_taker()
arm = build_arm()

for name, o in list(assets.items()):
    bake_asset(name, o)

socket('SM_Taker', 'Eyes', tuple(eye_centre(taker)), 'Between the eyes: an eye glow light or the look-at point.')
socket('SM_Taker', 'ReachHand', tuple(palm_centre(taker, (1.09, -.47, 1.63))),
       'Palm of the forward-reaching hand: where a lunge grabs.')
socket('SM_TakerArm', 'Palm', tuple(palm_centre(arm, (1.87, 0, .13))),
       'Palm of the open hand: attach or aim the victim here.')
for name in assets:
    metrics[name]['triangles_exported'] = len(assets[name].data.polygons)

for name in assets:
    export_fbx(name)

for name, o in assets.items():
    only_render([o])
    kit.preview_sheet([o], str(OUT / 'previews' / f'{name}_preview.png'), title=name)
dark_read_sheet(taker)
lunge_strip(taker)
arm_in_wall(arm)

with open(OUT / 'metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

# Editable source: one collection per mesh, with its sockets.
for name, o in assets.items():
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    for x in [o] + sockets.get(name, []):
        for c in list(x.users_collection):
            c.objects.unlink(x)
        col.objects.link(x)
    o['triangles'] = metrics[name]['triangles_exported']
    o['dimensions_cm'] = metrics[name]['dimensions_cm']
    o['pivot'] = PIVOTS[name]
for o in bpy.data.objects:
    o.hide_render = False
scene['PGA7_notes'] = ('Original Blender Python models, built by build_taker.py from taker_shapes.py. '
                       'Textures packed. SM_Taker origin on the floor under the feet (lunge pivot); '
                       'SM_TakerArm origin where it leaves the wall. Both face +X.')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'PG-A7_Taker.blend'))
print('ALL COMPLETE', json.dumps({k: v['triangles_exported'] for k, v in metrics.items()}), flush=True)
