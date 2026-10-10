"""HC-A2: SM_Statue (1.8 m) and SM_Statue_Small (1.1 m), a carved stone owl on a plinth.

The owl from frame 05: an upright faceted body and head, ear tufts, big round eyes with dark
pupils, folded wings and blocky feet. It sits on a two-stone plinth with a carved diamond on the
front, like the plinths in the frame's alcoves, and a rope sling lashed around the plinth so it
reads as something the team hauls around. The front faces +X. The small one is the same statue
scaled to 1.1 m.

An owl rather than the frame's lion or wolf, so it can't be mistaken for the gold lion idol.

    Blender -b --factory-startup --python make_statue.py -- /tmp/HC-A2
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import hc_a2_parts as P  # noqa: E402

kit = P.kit
bpy = P.bpy

HEIGHT = 1.8
SMALL = 1.1
PLINTH_T = 0.56
FOOT_T = 0.12


def lump(name, size, loc, rot=(0, 0, 0), seed=0, facets=48, flat_base=False, bevel=0.03,
         material="M_Stone"):
    obj = kit.faceted_rock(name, size=size, seed=seed, facets=facets, flat_base=flat_base,
                           bevel=bevel, material=P.mat(material))
    return P.move(obj, loc, rot)


def disc(name, radius, depth, loc, material, verts=16, bevel=0.015):
    """A short cylinder along X (eyes and pupils)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=loc, rotation=(0, math.pi / 2, 0))
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    kit.chunky_bevel(obj, width=bevel, segments=2, angle_deg=40, smooth_deg=50)
    obj.data.materials.append(P.mat(material))
    return obj


def beak(loc):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.075, radius2=0.0, depth=0.17,
                                    location=loc, rotation=(0, math.radians(150), math.pi / 4))
    obj = bpy.context.active_object
    obj.name = "beak"
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    kit.chunky_bevel(obj, width=0.012, segments=2, angle_deg=30)
    obj.data.materials.append(P.mat("M_Stone"))
    return obj


def plinth():
    parts = []
    parts.append(P.stone_block("plinth_foot", (-0.5, -0.5, 0), (0.5, 0.5, FOOT_T), seed=1,
                               top_wobble=0.015, chips=(0, 2), chip=0.07, bevel=0.03))
    block = P.stone_block("plinth_block", (-0.43, -0.43, FOOT_T), (0.43, 0.43, PLINTH_T), seed=2,
                          top_wobble=0.012, xy_wobble=0.015, chips=(1,), chip=0.06, bevel=0.035)
    # The diamond sits above the rope sling, so the rope never hides it.
    ring = P.ring_cutter("diamond", P.polygon(4, 0.125), 0.045, 0.035, z_top=0.0)
    P.move(ring, loc=(0.43, 0, PLINTH_T - 0.135), rot=(0, math.pi / 2, 0))
    P.carve(block, [ring])
    P.soften(block, width=0.01)
    parts.append(block)
    return parts


def sling():
    """Two turns of rope around the plinth block, a knot at the front corner and a loose end."""
    z0 = FOOT_T + 0.05
    ropes = []
    for i, dz in enumerate((0.0, 0.085)):
        pts = P.rounded_rect_path(0, 0, z0 + dz, 0.46, 0.46, corner=0.1, per_side=4)
        ropes.append(P.rope_loop(f"rope_{i}", pts, radius=0.04, seed=10 + i))
    ropes.append(lump("knot", (0.17, 0.17, 0.16), (0.40, 0.40, z0 - 0.03), seed=12, facets=30,
                      bevel=0.03, material="M_Rope"))
    end = [(0.43, 0.45, z0), (0.50, 0.50, z0 - 0.06), (0.55, 0.53, z0 - 0.11)]
    ropes.append(P.rope_loop("rope_end", end, radius=0.035, closed=False, seed=13))
    return ropes


def owl():
    b = PLINTH_T
    parts = [
        lump("body", (0.70, 0.78, 0.92), (0.0, 0, b), seed=21, facets=64, flat_base=True, bevel=0.035),
        lump("head", (0.58, 0.76, 0.50), (0.02, 0, b + 0.76), seed=22, facets=56, bevel=0.035),
        lump("tuft_l", (0.16, 0.14, 0.22), (-0.02, 0.27, b + 1.10), rot=(math.radians(-22), 0, 0),
             seed=23, facets=24, bevel=0.02),
        lump("tuft_r", (0.16, 0.14, 0.22), (-0.02, -0.27, b + 1.10), rot=(math.radians(22), 0, 0),
             seed=24, facets=24, bevel=0.02),
        lump("wing_l", (0.52, 0.2, 0.78), (-0.06, 0.37, b + 0.06), rot=(math.radians(10), 0, 0),
             seed=25, facets=36, bevel=0.03),
        lump("wing_r", (0.52, 0.2, 0.78), (-0.06, -0.37, b + 0.06), rot=(math.radians(-10), 0, 0),
             seed=26, facets=36, bevel=0.03),
        lump("tail", (0.26, 0.34, 0.18), (-0.33, 0, b), seed=27, facets=24, flat_base=True, bevel=0.02),
    ]
    # The face: eye rims, dark pupils and a beak, all big enough to read across the hall.
    ez = b + 0.98
    for side, y in (("l", 0.15), ("r", -0.15)):
        parts.append(disc(f"eye_{side}", 0.14, 0.12, (0.27, y, ez), "M_Stone"))
        parts.append(disc(f"pupil_{side}", 0.065, 0.06, (0.335, y, ez), "M_StoneCarving", verts=12,
                          bevel=0.01))
    parts.append(beak((0.35, 0, ez - 0.13)))
    # Blocky feet: three rounded toes each, gripping the plinth's front edge.
    for side, y in (("l", 0.15), ("r", -0.15)):
        for k, dy in enumerate((-0.07, 0.0, 0.07)):
            toe = P.stone_block(f"toe_{side}{k}", (-0.1, -0.04, 0), (0.1, 0.04, 0.085),
                                seed=30 + k, top_wobble=0.01, xy_wobble=0.01, bevel=0.03, segments=2)
            parts.append(P.move(toe, (0.33, y + dy, b - 0.01), (0, 0, dy * 2.5)))
    return parts


def build(name, height):
    parts = plinth() + sling() + owl()
    statue = P.finish(parts, name)
    kit.sit_on_floor(statue)
    lo, hi = kit._bounds([statue])
    s = height / (hi.z - lo.z)
    statue.scale = (s, s, s)
    bpy.context.view_layer.objects.active = statue
    statue.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    kit.sit_on_floor(statue)
    print(f"SCALED {name} by {s:.3f}")
    return statue


def main():
    out = P.out_dir()
    for name, height in (("SM_Statue", HEIGHT), ("SM_Statue_Small", SMALL)):
        kit.reset()
        statue = build(name, height)
        kit.preview_sheet([statue], f"{out}/{name}_preview.png", title=name)
        kit.export_glb([statue], f"{out}/{name}.glb")


main()
