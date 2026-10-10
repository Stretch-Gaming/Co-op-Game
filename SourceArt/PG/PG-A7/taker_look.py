"""PG-A7 the taker: look-development helpers. Lit preview materials and the dark read test:
the taker 15 m from a player's camera in a dark cave, rendered at the size of one split-screen
half (640 x 360, 90 degree horizontal field of view), against a torch-lit wall.
"""
import math

import bpy
from mathutils import Vector


def lin(hexcode):
    c = [int(hexcode[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x < .04045 else ((x + .055) / 1.055) ** 2.4 for x in c)


# Shadow family for the body: blue-violet, darkest at the feet, never black.
BODY_LO, BODY_HI = '#161A26', '#4A4562'
GHOST_WHITE = '#D6F0FF'


def body_preview_material(name='M_TakerPreview_Body'):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    links = m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial')
    bs = n.new('ShaderNodeBsdfPrincipled')
    links.new(bs.outputs[0], out.inputs['Surface'])
    tex = n.new('ShaderNodeTexCoord')
    sep = n.new('ShaderNodeSeparateXYZ')
    links.new(tex.outputs['Generated'], sep.inputs[0])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*lin(BODY_LO), 1)
    ramp.color_ramp.elements[1].color = (*lin(BODY_HI), 1)
    links.new(sep.outputs['Z'], ramp.inputs[0])
    links.new(ramp.outputs[0], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = .85
    return m


def eye_material(name='M_TakerPreview_Eyes', strength=8.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    out = n.new('ShaderNodeOutputMaterial')
    em = n.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*lin(GHOST_WHITE), 1)
    em.inputs['Strength'].default_value = strength
    m.node_tree.links.new(em.outputs[0], out.inputs['Surface'])
    return m


def plain(name, hexcode, rough=.95):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bs = next(v for v in m.node_tree.nodes if v.type == 'BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value = (*lin(hexcode), 1)
    bs.inputs['Roughness'].default_value = rough
    return m


def _plane(name, size, loc, rot, mat, col):
    me = bpy.data.meshes.new(name)
    sx, sy = size
    me.from_pydata([(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)],
                   [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    me.materials.append(mat)
    return o


def _light(name, kind, color, energy, loc, col, aim=None, spot=None, size=.1):
    d = bpy.data.lights.new(name, kind)
    d.color = lin(color)
    d.energy = energy
    if kind in ('POINT', 'SPOT'):
        d.shadow_soft_size = size
    if spot:
        d.spot_size = math.radians(spot)
        d.spot_blend = .6
    o = bpy.data.objects.new(name, d)
    col.objects.link(o)
    o.location = loc
    if aim is not None:
        o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def dark_read(scene, path, distance=15.0, res=(640, 360), headlamp=True):
    """Render whatever is visible at the origin from `distance` metres down +X, the way a
    player standing in the maze mouth sees it. The wall 3 m behind the taker gets a warm
    torch pool; the player's headlamp (12 m reach in the game) barely reaches it."""
    col = bpy.data.collections.new('DarkRead')
    scene.collection.children.link(col)
    world = bpy.data.worlds.new('DarkReadWorld')
    world.use_nodes = True
    bg = next(v for v in world.node_tree.nodes if v.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (*lin('#1E2433'), 1)
    bg.inputs['Strength'].default_value = .25
    old_world = scene.world
    scene.world = world
    rock = plain('M_DarkRead_Rock', '#4A4652')
    _plane('DR_Wall', (7, 16), (-3.2, 0, 3.5), (0, math.radians(90), 0), rock, col)
    _plane('DR_Floor', (24, 16), (6, 0, 0), (0, 0, 0), plain('M_DarkRead_Floor', '#3A3742'), col)
    _light('DR_Torch', 'POINT', '#FFB347', 420, (-2.6, 2.4, 2.3), col, size=.15)
    _light('DR_Torch2', 'POINT', '#FFB347', 160, (-2.6, -3.2, 1.8), col, size=.15)
    _light('DR_CrystalFill', 'POINT', '#3FD0C9', 60, (2.0, -4.0, 0.6), col, size=.3)
    if headlamp:
        _light('DR_Headlamp', 'SPOT', '#FFF1DC', 900, (distance, .2, 1.65), col, aim=(0, 0, 1.3), spot=34,
               size=.03)
    cam_d = bpy.data.cameras.new('DR_Cam')
    cam_d.sensor_fit = 'HORIZONTAL'
    cam_d.angle = math.radians(90)
    cam = bpy.data.objects.new('DR_Cam', cam_d)
    col.objects.link(cam)
    cam.location = (distance, 0, 1.65)
    cam.rotation_euler = (Vector((0, 0, 1.4)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    old = (scene.camera, scene.render.resolution_x, scene.render.resolution_y, scene.render.engine,
           scene.render.filepath, scene.render.resolution_percentage)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        pass
    scene.view_settings.view_transform = 'AgX'
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True, scene=scene.name)
    (scene.camera, scene.render.resolution_x, scene.render.resolution_y, scene.render.engine,
     scene.render.filepath, scene.render.resolution_percentage) = old
    scene.world = old_world
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
        elif isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)
    bpy.data.collections.remove(col)
    bpy.data.worlds.remove(world)
