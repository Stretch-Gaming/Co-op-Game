"""PG-6 floor lever and gauntlet gate. Original Blender Python modeling, in the PG-A4 zipline
style: worn desaturated timber, dark iron, flax rope wraps. Builds four meshes, bakes each one's
1K base color (sRGB) and packed mask (red AO floored at .32, green roughness, blue metallic) with
Cycles, exports one FBX per mesh with its UCX_ collision boxes, renders preview sheets and saves
the editable .blend:

    blender -b --factory-startup --python SourceArt/PG/PG-6/build_lever_gate.py -- SourceArt/PG/PG-6

Blender +Z is up, the passage runs along X and widths span Y. Units are metres.

- SM_Lever_Base: pivot at base centre on the floor. The hinge axle runs along Y at (0, 0, 0.45).
- SM_Lever_Handle: origin exactly on the hinge axis; upright along +Z at rest.
- SM_GauntletGate: pivot at bottom centre; 4.3 m (Y) x 4.0 m (Z) x 0.28 m (X).
- SM_GauntletGate_Frame: pivot at bottom centre; clear opening Y -2.0..+2.0, lintel underside 4.6 m.

The material, bake and export helpers are adapted from SourceArt/PG/PG-A4/build_tall_anchors.py.
"""
import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

REPO = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO / "Tools" / "blender"))
import asset_kit as kit  # noqa: E402

OUT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
for folder in ("textures", "previews"):
    (OUT / folder).mkdir(parents=True, exist_ok=True)

# Mating dimensions. These are what the Blueprints rely on; keep them exact.
HINGE_Z = 0.45            # lever axle height above the floor (Y axis through (0, 0, HINGE_Z))
SLOT_HALF = 0.08          # lever slot is 0.16 m wide in Y
GATE_HALF_Y = 2.15        # gate spans 4.3 m in Y
GATE_HALF_X = 0.14        # gate is 0.28 m thick in X
GATE_H = 4.0
OPEN_HALF = 2.0           # frame clear opening 4.0 m in Y
LINTEL_UNDER = 4.6
LINTEL_TOP = 5.2
GROOVE_HALF_X = 0.16      # groove/slot in posts and lintel: X -0.16..+0.16
GROOVE_DEPTH_Y = 2.19     # groove back wall, 4 cm past the gate's edge

kit.reset()
scene = bpy.context.scene
random.seed(6)


# ---------------------------------------------------------------------------
# Source materials (from PG-A4): emission shaders with a dark-to-light ramp on the object's
# generated Z, baked to the base color. Roughness and metallic are stored on the material.
def lin(hexcode):
    c = [int(hexcode[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x < .04045 else ((x + .055) / 1.055) ** 2.4 for x in c)


# Desaturated timber, iron, flax and rock. None of them claims a reserved gameplay color.
PALETTE = {
    'wood': ('#493D40', '#938078', .84, 0),
    'wood_edge': ('#665550', '#B09A88', .79, 0),
    'iron': ('#38404F', '#7A6E68', .58, .72),
    'iron_edge': ('#4A4652', '#A4A5AD', .50, .80),
    'rope': ('#625B60', '#BBB3A0', .91, 0),
    'rope_edge': ('#77707A', '#CDC3B3', .88, 0),
    'rock': ('#4A4652', '#7A6E68', .95, 0),
    'rock_edge': ('#5C5664', '#95857A', .92, 0),
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
    ramp.color_ramp.elements[0].position = 0
    ramp.color_ramp.elements[0].color = (*lin(lo), 1)
    ramp.color_ramp.elements[1].position = 1
    ramp.color_ramp.elements[1].color = (*lin(hi), 1)
    links.new(sep.outputs['Z'], ramp.inputs[0])
    if 'wood' in kind:
        # Three broad painted grain bands, not scanned grain or high frequency noise.
        wave = n.new('ShaderNodeTexWave')
        wave.wave_type = 'BANDS'
        wave.bands_direction = 'Z'
        wave.inputs['Scale'].default_value = 2.1
        wave.inputs['Distortion'].default_value = .6
        links.new(tex.outputs['Generated'], wave.inputs['Vector'])
        mix = n.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = .16
        links.new(ramp.outputs[0], mix.inputs[1])
        links.new(wave.outputs['Color'], mix.inputs[2])
        links.new(mix.outputs[0], emit.inputs['Color'])
    else:
        links.new(ramp.outputs[0], emit.inputs['Color'])
    m['roughness'] = rough
    m['metallic'] = metal
    m['kind'] = kind
    sources[kind] = m
    return m


# ---------------------------------------------------------------------------
# Part helpers (from PG-A4, with a few additions: bow control, prisms and rope bands).
parts = []


def active(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def register(o, name, kind, smooth=False):
    o.name = name
    o.data.materials.append(source_mat(kind))
    for p in o.data.polygons:
        p.use_smooth = smooth
    parts.append(o)
    return o


def bevel(o, width, kind):
    """Wide worn bevel; the bevel faces take the lighter edge material."""
    o.data.materials.append(source_mat(kind + '_edge' if kind + '_edge' in PALETTE else kind))
    mod = o.modifiers.new('Wide worn bevel', 'BEVEL')
    mod.width = width
    mod.segments = 1
    mod.material = 1
    mod.use_clamp_overlap = True
    active(o)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return o


def box(name, center, size, kind='iron', edge=.015, uneven=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.object
    o.dimensions = size
    active(o)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    register(o, name, kind)
    bevel(o, edge, kind)
    if uneven:
        # Coarse 2 mm edge drift; mating faces are clamped back to exact afterwards.
        for v in o.data.vertices:
            v.co.y += .002 * math.sin(v.co.z * 9 + v.co.x * 14)
            v.co.x += .002 * math.sin(v.co.z * 11 + v.co.y * 8)
    return o


def span(name, lo, hi, kind='wood', edge=.03, uneven=True):
    """A box given by its min and max corners."""
    lo, hi = Vector(lo), Vector(hi)
    return box(name, (lo + hi) / 2, hi - lo, kind, edge, uneven)


def beam(name, a, b, width, depth, kind='wood', edge=.02, bow=None, bow_side=.55):
    """A gently bowed, chamfered timber between two end centres. For a vertical beam `width` runs
    along X and `depth` along Y; for a beam along Y, `width` runs along X and `depth` along Z."""
    a, b = Vector(a), Vector(b)
    length = (b - a).length
    c = min(edge, width * .24, depth * .24)
    bow = min(.013, length * .018) if bow is None else bow
    profile = [(-width / 2 + c, -depth / 2), (width / 2 - c, -depth / 2), (width / 2, -depth / 2 + c),
               (width / 2, depth / 2 - c), (width / 2 - c, depth / 2), (-width / 2 + c, depth / 2),
               (-width / 2, depth / 2 - c), (-width / 2, -depth / 2 + c)]
    ts = [0, .025, .33, .66, .975, 1]
    vs, fs = [], []
    for t in ts:
        taper = .93 if t in (0, 1) else 1 + .025 * math.sin(t * 5)
        bend = math.sin(math.pi * t) * bow
        for x, y in profile:
            vs.append((x * taper + bend, y * taper - bend * bow_side, length * (t - .5)))
    for i in range(5):
        for j in range(8):
            fs.append((i * 8 + j, i * 8 + (j + 1) % 8, (i + 1) * 8 + (j + 1) % 8, (i + 1) * 8 + j))
    fs += [tuple(range(7, -1, -1)), tuple(range(40, 48))]
    me = bpy.data.meshes.new('Bent chamfered timber')
    me.from_pydata(vs, [], fs)
    me.update()
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.location = (a + b) * .5
    register(o, name, kind)
    me.materials.append(source_mat(kind + '_edge'))
    for i, p in enumerate(me.polygons):
        if i < 40 and (i % 8 % 2 == 1 or i // 8 in (0, 4)):
            p.material_index = 1
    o.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler()
    return o


def cylinder(name, center, radius, depth, kind='iron', axis='Y', vertices=10):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=center)
    o = bpy.context.object
    register(o, name, kind)
    # Smooth round sides, flat caps.
    for p in o.data.polygons:
        p.use_smooth = abs(p.normal.z) < .5
    if axis == 'Y':
        o.rotation_euler[0] = math.pi / 2
    elif axis == 'X':
        o.rotation_euler[1] = math.pi / 2
    return o


def ring(name, center, major, minor, kind='rope', axis='Z', n=12, k=4):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=n,
                                     minor_segments=k, location=center)
    o = bpy.context.object
    register(o, name, kind, True)
    if axis == 'Y':
        o.rotation_euler[0] = math.pi / 2
    elif axis == 'X':
        o.rotation_euler[1] = math.pi / 2
    return o


def bolt(name, center, axis='Y', radius=.025):
    return cylinder(name, center, radius, .014, 'iron_edge', axis, 6)


AXES = {'X': (1, 2, 0), 'Y': (0, 2, 1), 'Z': (0, 1, 2)}  # (u, v, w) world indices per loop axis


def rope_band(name, center, hu, hv, axis, minor=.014, corner=.05, sides=5, kind='rope'):
    """A flax rope pulled tight around a rectangular timber: a tube swept along a rounded
    rectangle with half sizes (hu, hv) to the rope's centreline, in the plane across `axis`."""
    iu, iv, iw = AXES[axis]
    corner = min(corner, hu * .9, hv * .9)
    path = []
    for cu, cv, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cu * (hu - corner), cv * (hv - corner)
        for k in range(4):
            a = math.radians(a0 + k * 30)
            path.append((ox + corner * math.cos(a), oy + corner * math.sin(a), math.cos(a), math.sin(a)))
    vs, fs = [], []
    n = len(path)
    for pu, pv, nu, nv in path:
        for s in range(sides):
            a = 2 * math.pi * s / sides
            r_out, r_w = minor * math.cos(a), minor * math.sin(a)
            p = [0.0, 0.0, 0.0]
            p[iu] = center[iu] + pu + nu * r_out
            p[iv] = center[iv] + pv + nv * r_out
            p[iw] = center[iw] + r_w
            vs.append(p)
    for i in range(n):
        for s in range(sides):
            a, b = i * sides + s, i * sides + (s + 1) % sides
            c, d = ((i + 1) % n) * sides + (s + 1) % sides, ((i + 1) % n) * sides + s
            fs.append((a, b, c, d))
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    return register(o, name, kind, True)


def prism_y(name, profile_xz, y0, y1, kind='iron', edge=.008):
    """A plate cut to a profile in the XZ plane, extruded from y0 to y1."""
    n = len(profile_xz)
    vs = [(x, y0, z) for x, z in profile_xz] + [(x, y1, z) for x, z in profile_xz]
    fs = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    fs += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    register(o, name, kind)
    active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bevel(o, edge, kind)
    return o


# ---------------------------------------------------------------------------
# SM_Lever_Base: stone plinth, timber housing, two timber cheeks lined with iron quadrant
# plates either side of a 0.16 m slot, and an iron axle along Y at (0, 0, 0.45).
def lever_base():
    span('Stone plinth', (-.375, -.30, 0), (.375, .30, .16), 'rock', .045)
    span('Timber housing block', (-.32, -.26, .16), (.32, .26, .32), 'wood', .035)
    # Flax rope pulled twice around the housing block.
    for z in (.215, .25):
        rope_band('Housing rope wrap', (0, 0, z), .334, .274, 'Z', .013, .04)
    # Iron corner angles on the housing block.
    for sx in (-1, 1):
        for sy in (-1, 1):
            box('Housing corner iron', (sx * .305, sy * .245, .245), (.07, .07, .17), 'iron', .012)
    for sy in (-1, 1):
        # Timber cheek outside the iron plate.
        span('Timber cheek', (-.26, sy * .105 if sy > 0 else -.25, .32),
             (.26, .25 if sy > 0 else -.105, .55), 'wood', .03)
        # Iron quadrant plate: a tombstone sector round the hinge, inner face on the slot.
        prof = [(.2, .30)] + [(.2 * math.cos(math.radians(a)), HINGE_Z + .2 * math.sin(math.radians(a)))
                              for a in range(0, 181, 20)] + [(-.2, .30)]
        y0, y1 = (SLOT_HALF, .105) if sy > 0 else (-.105, -SLOT_HALF)
        prism_y('Iron quadrant plate', prof, y0, y1, 'iron', .008)
        # Hex nut and washer on each axle end, outside the cheeks.
        cylinder('Axle washer', (0, sy * .257, HINGE_Z), .075, .014, 'iron', 'Y', 12)
        cylinder('Axle nut', (0, sy * .277, HINGE_Z), .056, .03, 'iron_edge', 'Y', 6)
        for x in (-.19, .19):
            for z in (.385, .495):
                bolt('Cheek rivet', (x, sy * .253, z), 'Y', .022)
        # Rivets through the quadrant plates' exposed tops.
        for a in (35, 90, 145):
            bolt('Quadrant rivet', (.165 * math.cos(math.radians(a)), sy * .108,
                                    HINGE_Z + .165 * math.sin(math.radians(a))), 'Y', .016)
    cylinder('Iron axle', (0, 0, HINGE_Z), .035, .53, 'iron', 'Y', 10)
    # Worn timber stop pads at the slot ends, kept low so the handle swings past 45 degrees.
    for sx in (-1, 1):
        span('Slot stop pad', (sx * .30 - .045, -.075, .32), (sx * .30 + .045, .075, .385), 'wood', .02)
        box('Stop pad iron cap', (sx * .30, 0, .39), (.10, .16, .02), 'iron', .006)


# ---------------------------------------------------------------------------
# SM_Lever_Handle: built with the hinge at the origin, upright along +Z.
def lever_handle():
    cylinder('Iron hub', (0, 0, 0), .078, .13, 'iron', 'Y', 12)
    for sy in (-1, 1):
        cylinder('Hub washer', (0, sy * .069, 0), .046, .012, 'iron_edge', 'Y', 8)
    # Bent timber shaft, 0.12 m (X) x 0.11 m (Y), bowed in X only so it stays in the slot.
    beam('Bent timber shaft', (0, 0, .03), (0, 0, .665), .12, .11, 'wood', .022, bow=.024, bow_side=0)
    box('Lower ferrule', (0, 0, .125), (.142, .128, .05), 'iron', .01)
    box('Upper ferrule', (0, 0, .595), (.146, .13, .055), 'iron', .01)
    for sx in (-1, 1):
        bolt('Ferrule rivet', (sx * .074, 0, .125), 'X', .014)
    # Oversized T grip: timber crossbar along Y, iron socket and end caps, flax rope wraps.
    box('Grip socket', (0, 0, .69), (.14, .15, .15), 'iron', .016)
    cylinder('Timber grip bar', (0, 0, .70), .056, .44, 'wood', 'Y', 10)
    for sy in (-1, 1):
        cylinder('Grip end cap', (0, sy * .23, .70), .073, .04, 'iron', 'Y', 10)
        bolt('Grip end boss', (0, sy * .254, .70), 'Y', .03)
        for i, y in enumerate((.098, .122, .146, .170, .194)):
            ring('Grip rope wrap', (0, sy * y, .70 + .002 * (i % 2)), .058, .0115, 'rope', 'Y', 12, 4)


# ---------------------------------------------------------------------------
# SM_GauntletGate: seven bent timber verticals with see-through gaps, three iron cross straps
# on both faces, a timber top rail and blunt iron shoes. Bottom flat at z = 0.
GATE_COLS = [-1.95, -1.30, -.65, 0, .65, 1.30, 1.95]
STRAP_Z = (.62, 2.0, 3.32)


def gauntlet_gate():
    for i, y in enumerate(GATE_COLS):
        top = 3.80 + random.uniform(-.02, .02)
        beam('Gate vertical', (0, y, .10), (0, y, top), .18, .40, 'wood', .035,
             bow=.010 + .006 * random.random())
        shoe = span('Iron shoe', (-.115, y - .215, 0), (.115, y + .215, .15), 'iron', .022, False)
        # Blunt tooth: draw the shoe's lower edge in a little.
        for v in shoe.data.vertices:
            if v.co.z < -.05:
                v.co.x *= .86
                v.co.y = (v.co.y) * .93
    span('Timber top rail', (-.12, -GATE_HALF_Y, 3.70), (.12, GATE_HALF_Y, GATE_H), 'wood', .04)
    # Horizontal timber rails through the core behind each strap, so the gaps read as a grid.
    for z in STRAP_Z:
        beam('Gate cross rail', (0, -GATE_HALF_Y, z), (0, GATE_HALF_Y, z), .17, .26, 'wood', .03, bow=.008)
    for sx in (-1, 1):
        for z in STRAP_Z:
            span('Iron cross strap', (sx * .11 - .02, -GATE_HALF_Y, z - .12), (sx * .11 + .02, GATE_HALF_Y, z + .12),
                 'iron', .014)
            for y in GATE_COLS:
                for dy, dz in ((-.10, .055), (.10, -.055)):
                    bolt('Strap rivet', (sx * .133, y + dy, z + dz), 'X', .024)
        # Top rail iron band.
        span('Top rail band', (sx * .12 - .015, -GATE_HALF_Y + .02, 3.80), (sx * .12 + .015, GATE_HALF_Y - .02, 3.90),
             'iron', .008, False)
    # Lived in: two patch planks nailed over split verticals.
    for y, z0, z1, sx in ((-.65, 1.0, 1.55, 1), (1.30, 2.55, 2.95, -1)):
        span('Patch plank', (sx * .09 - .016, y - .17, z0), (sx * .09 + .016, y + .17, z1), 'wood', .012)
        for dz in (.08, z1 - z0 - .08):
            bolt('Patch nail', (sx * .108, y, z0 + dz), 'X', .016)


# ---------------------------------------------------------------------------
# SM_GauntletGate_Frame: stone footings and timber posts with a groove facing the opening,
# a split timber lintel with a slot the gate rises through, iron brackets and rope lashings.
def gate_frame():
    G, D = GROOVE_HALF_X, GROOVE_DEPTH_Y
    FOOT = .62  # stone footing height
    for sy in (-1, 1):
        def Y(a, b):
            return (sy * a, sy * b) if sy > 0 else (sy * b, sy * a)

        y0, y1 = Y(OPEN_HALF, 2.85)
        yr0, yr1 = Y(D, 2.85)
        # Stone footing in three blocks around the groove.
        span('Stone footing front', (G, y0, 0), (.56, y1, FOOT), 'rock', .06)
        span('Stone footing back', (-.56, y0, 0), (-G, y1, FOOT), 'rock', .06)
        span('Stone footing rear', (-G, yr0, 0), (G, yr1, FOOT - .04), 'rock', .06)
        # Timber post: front and back uprights either side of the groove, and the groove's back wall.
        yc = sy * 2.30
        for sx in (-1, 1):
            beam('Timber post upright', (sx * .28, yc, FOOT), (sx * .28, yc, LINTEL_UNDER), .24, .60, 'wood', .04,
                 bow=.012)
        yb0, yb1 = Y(D, 2.60)
        span('Groove back timber', (-G, yb0, FOOT - .04), (G, yb1, LINTEL_UNDER), 'wood', .03)
        # Iron U straps round each post at three heights, riveted on the front and back faces.
        for z in (1.45, 2.65, 3.85):
            for sx in (-1, 1):
                yf0, yf1 = Y(OPEN_HALF, 2.62)
                span('Post strap face', (sx * .415 - .017, yf0, z - .07), (sx * .415 + .017, yf1, z + .07),
                     'iron', .01)
                for yy in (2.12, 2.48):
                    bolt('Post strap rivet', (sx * .435, sy * yy, z), 'X', .02)
            ys0, ys1 = Y(2.60, 2.634)
            span('Post strap side', (-.432, ys0, z - .07), (.432, ys1, z + .07), 'iron', .01)
        # Iron brackets tying post and lintel on both faces.
        for sx in (-1, 1):
            bys = Y(2.06, 2.54)
            span('Bracket post plate', (sx * .40 - (.03 if sx < 0 else 0), bys[0], 4.05),
                 (sx * .40 + (.03 if sx > 0 else 0), bys[1], LINTEL_UNDER), 'iron', .01)
            span('Bracket lintel plate', (sx * .45 - (.03 if sx < 0 else 0), bys[0], LINTEL_UNDER),
                 (sx * .45 + (.03 if sx > 0 else 0), bys[1], 5.02), 'iron', .01)
            for z in (4.22, 4.42, 4.78, 4.92):
                xo = .43 if z < LINTEL_UNDER else .48
                for yy in (2.14, 2.46):
                    bolt('Bracket rivet', (sx * xo, sy * yy, z), 'X', .021)
        # Lintel end block closing the slot over the post.
        ye0, ye1 = Y(D, 2.75)
        span('Lintel end block', (-G, ye0, LINTEL_UNDER), (G, ye1, LINTEL_TOP), 'wood', .03)
        # Flax lashings round the lintel ends, outside the opening.
        for yy in (2.27, 2.33, 2.39):
            rope_band('Lintel rope lashing', (0, sy * yy, (LINTEL_UNDER + LINTEL_TOP) / 2), .47, .32, 'Y', .019, .06)
    # Split lintel: front and back timbers either side of the gate slot, iron lips on the slot edges.
    for sx in (-1, 1):
        beam('Lintel timber', (sx * .305, -2.75, 4.9), (sx * .305, 2.75, 4.9), .29, .60, 'wood', .045, bow=.012)
        span('Slot lip iron', (sx * G - (.07 if sx < 0 else 0), -D, LINTEL_TOP - .005),
             (sx * G + (.07 if sx > 0 else 0), D, LINTEL_TOP + .025), 'iron', .008, False)
        for yy in (-1.6, -.8, 0, .8, 1.6):
            bolt('Lip rivet', (sx * (G + .035), yy, LINTEL_TOP + .027), 'Z', .017)


# ---------------------------------------------------------------------------
# Envelope clamps and checks. Bevel drift and bowed timbers must not cross mating faces.
def clamp_gate(o):
    for v in o.data.vertices:
        v.co.x = max(-GATE_HALF_X, min(GATE_HALF_X, v.co.x))
        v.co.y = max(-GATE_HALF_Y, min(GATE_HALF_Y, v.co.y))
        v.co.z = max(0.0, min(GATE_H, v.co.z))


def clamp_frame(o):
    """Keep the opening (|Y| < 2.0, Z < 4.6) and the gate's groove/slot completely clear."""
    for v in o.data.vertices:
        c = v.co
        if abs(c.y) < OPEN_HALF and c.z < LINTEL_UNDER:
            if c.z > 4.55:
                c.z = LINTEL_UNDER
            else:
                c.y = math.copysign(OPEN_HALF, c.y)
        # Groove and lintel slot: X -0.16..0.16, |Y| < 2.19, any height.
        if abs(c.x) < GROOVE_HALF_X - 1e-6 and abs(c.y) < GROOVE_DEPTH_Y - 1e-6:
            dx, dy = GROOVE_HALF_X - abs(c.x), GROOVE_DEPTH_Y - abs(c.y)
            if dx < dy:
                c.x = math.copysign(GROOVE_HALF_X, c.x)
            else:
                c.y = math.copysign(GROOVE_DEPTH_Y, c.y)


def check_base(o):
    for v in o.data.vertices:
        c = v.co
        if abs(c.y) < SLOT_HALF - 1e-5 and c.z > .40 + 1e-5:
            r = math.hypot(c.x, c.z - HINGE_Z)
            assert r < .036, ('slot obstruction', tuple(c))


def check_handle(o):
    for v in o.data.vertices:
        c = v.co
        if math.hypot(c.x, c.z) < .36:
            assert abs(c.y) < SLOT_HALF - .004, ('handle wider than slot', tuple(c))


def check_frame(o):
    for v in o.data.vertices:
        c = v.co
        assert not (abs(c.y) < OPEN_HALF - 1e-5 and c.z < LINTEL_UNDER - 1e-5), ('opening', tuple(c))
        assert not (abs(c.x) < GROOVE_HALF_X - 1e-5 and abs(c.y) < GROOVE_DEPTH_Y - 1e-5), ('slot', tuple(c))


# ---------------------------------------------------------------------------
assets, metrics, collision = {}, {}, {}
BUDGET = {'SM_Lever_Base': 5000, 'SM_Lever_Handle': 5000, 'SM_GauntletGate': 10000,
          'SM_GauntletGate_Frame': 10000}
PIVOTS = {
    'SM_Lever_Base': 'Base centre on the floor. Hinge axle along Y through (0, 0, 45) cm; slot 16 cm wide (Y -8..+8).',
    'SM_Lever_Handle': 'Exactly on the hinge axis. Place at (0, 0, 45) cm on the base and rotate by pitch; upright along +Z at rest, swings +/-45 deg about Y.',
    'SM_GauntletGate': 'Bottom centre, flat bottom at Z 0. Slides up 420 cm in the frame grooves (top then at 820 cm).',
    'SM_GauntletGate_Frame': 'Bottom centre on the floor. Clear opening Y -200..+200 cm, Z 0..460 cm; grooves and lintel slot X -16..+16, Y to +/-219 cm.',
}


def bounds(o):
    co = [o.matrix_world @ v.co for v in o.data.vertices]
    return [[min(c[a] for c in co), max(c[a] for c in co)] for a in range(3)]


def finish(name, builder, post=None, check=None):
    global parts
    parts = []
    builder()
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    o.data.name = name
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-7)
    bm.to_mesh(o.data)
    bm.free()
    if post:
        post(o)
    o.data.update()
    if check:
        check(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(68), island_margin=.014, area_weight=.5)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.data.calc_loop_triangles()
    b = bounds(o)
    metrics[name] = {
        'triangles': len(o.data.loop_triangles),
        'dimensions_cm': [round((hi - lo) * 100, 2) for lo, hi in b],
        'bounds_cm': [[round(lo * 100, 2), round(hi * 100, 2)] for lo, hi in b],
        'pivot': PIVOTS[name],
        'uv': 'unique packed UV atlas',
        'material_slots_after_bake': 1,
    }
    assert metrics[name]['triangles'] < BUDGET[name], (name, metrics[name]['triangles'])
    assets[name] = o
    print('MODEL', name, metrics[name], flush=True)
    return o


def ucx(name, index, lo, hi):
    """An Unreal simple-collision box, named UCX_<MeshName>_NN. No UVs, no material, no bake."""
    lo, hi = Vector(lo), Vector(hi)
    me = bpy.data.meshes.new(f'UCX_{name}_{index:02d}')
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co = Vector([(lo[i] + hi[i]) / 2 + v.co[i] * (hi[i] - lo[i]) for i in range(3)])
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(me.name, me)
    scene.collection.objects.link(o)
    o.display_type = 'WIRE'
    o.hide_render = True
    collision.setdefault(name, []).append(o)
    metrics[name].setdefault('collision_cm', []).append(
        {'name': o.name, 'min': [round(x * 100, 2) for x in lo], 'max': [round(x * 100, 2) for x in hi]})
    return o


# ---------------------------------------------------------------------------
# Bake (from PG-A4): base color from the emission sources, AO, then roughness/metallic as a flat
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
        socket = em.inputs['Color']
        original.append((m, socket.links[0].from_socket))
        for link in list(socket.links):
            m.node_tree.links.remove(link)
        socket.default_value = (1, m['roughness'], m['metallic'], 1)
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
    # Preview material: what M_Stylized does with the two textures, near enough.
    m = bpy.data.materials.new('M_' + name[3:] + '_BakedPreview')
    m.use_nodes = True
    n = m.node_tree.nodes
    links = m.node_tree.links
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
    o.data.materials.clear()
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.material_index = 0
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
    for x in [o] + collision[name]:
        x.hide_set(False)
        x.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(
        filepath=str(OUT / f'{name}.fbx'), use_selection=True, object_types={'MESH'},
        global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Y', axis_up='Z', use_mesh_modifiers=True, mesh_smooth_type='FACE',
        use_tspace=False, path_mode='RELATIVE', embed_textures=False, add_leaf_bones=False,
        bake_anim=False)
    print('EXPORTED', name, flush=True)


def preview(objects, filename, title):
    keep = set(objects)
    for other in bpy.data.objects:
        other.hide_render = other not in keep
    kit.preview_sheet(objects, str(OUT / 'previews' / filename), title=title)


# ---------------------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.render.bake.margin = 12
scene.render.bake.use_clear = True

base = finish('SM_Lever_Base', lever_base, check=check_base)
handle = finish('SM_Lever_Handle', lever_handle, check=check_handle)
gate = finish('SM_GauntletGate', gauntlet_gate, post=clamp_gate)
frame = finish('SM_GauntletGate_Frame', gate_frame, post=clamp_frame, check=check_frame)
tri_pair = metrics['SM_GauntletGate']['triangles'] + metrics['SM_GauntletGate_Frame']['triangles']
assert tri_pair < 15000, tri_pair

for name, o in list(assets.items()):
    bake_asset(name, o)

# Collision boxes (not baked, not counted in the triangle budgets).
ucx('SM_Lever_Base', 0, (-.375, -.30, 0), (.375, .30, .65))
hb = bounds(handle)
ucx('SM_Lever_Handle', 0, (hb[0][0], hb[1][0], hb[2][0]), (hb[0][1], hb[1][1], hb[2][1]))
ucx('SM_GauntletGate', 0, (-GATE_HALF_X, -GATE_HALF_Y, 0), (GATE_HALF_X, GATE_HALF_Y, GATE_H))
fb = bounds(frame)
ucx('SM_GauntletGate_Frame', 0, (fb[0][0], fb[1][0], 0), (fb[0][1], -OPEN_HALF, LINTEL_UNDER))
ucx('SM_GauntletGate_Frame', 1, (fb[0][0], OPEN_HALF, 0), (fb[0][1], fb[1][1], LINTEL_UNDER))
ucx('SM_GauntletGate_Frame', 2, (fb[0][0], fb[1][0], LINTEL_UNDER), (fb[0][1], fb[1][1], fb[2][1]))

for name in assets:
    export_fbx(name)

# Preview sheets, under the kit's cave lighting (EEVEE).
for name, o in assets.items():
    preview([o], f'{name}_preview.png', name)
# Lever assembled, handle pulled 40 degrees toward +X (positive Blender Y rotation).
tilted = handle.copy()
scene.collection.objects.link(tilted)
tilted.location = (0, 0, HINGE_Z)
tilted.rotation_euler = (0, math.radians(40), 0)
bpy.context.view_layer.update()
tilt_x = max((tilted.matrix_world @ v.co).x for v in tilted.data.vertices)
metrics['SM_Lever_Handle']['rotation_note'] = (
    f'Blender +Y rotation tilts the top toward +X (40 deg: top reaches X {tilt_x * 100:.1f} cm).')
preview([base, tilted], 'Lever_Assembled_preview.png', 'Lever, handle at +40 deg about Y')
bpy.data.objects.remove(tilted, do_unlink=True)
preview([gate, frame], 'GauntletGate_InFrame_preview.png', 'Gauntlet gate closed in frame')

with open(OUT / 'metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

# Editable source: one collection per mesh, with its collision boxes.
for name, o in assets.items():
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    for x in [o] + collision[name]:
        for c in list(x.users_collection):
            c.objects.unlink(x)
        col.objects.link(x)
    o['triangles'] = metrics[name]['triangles']
    o['dimensions_cm'] = metrics[name]['dimensions_cm']
    o['pivot'] = PIVOTS[name]
for o in bpy.data.objects:
    o.hide_render = o.name.startswith('UCX_')
scene['PG6_notes'] = ('Original Blender Python models, built by build_lever_gate.py. Textures packed. '
                      'Lever handle origin is on the hinge axis at (0, 0, 0.45) of the base; gate and frame '
                      'share the bottom-centre pivot.')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'PG-6_LeverGate.blend'))
print('ALL COMPLETE', json.dumps({k: v['triangles'] for k, v in metrics.items()}), flush=True)
