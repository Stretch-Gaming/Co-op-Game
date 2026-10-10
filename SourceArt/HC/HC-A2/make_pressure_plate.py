"""HC-A2: SM_PressurePlate_Base and SM_PressurePlate_Top (frame 05).

The base is a curb of eight cut stones with an exact 2.0 x 2.0 m footprint, about 10 cm proud
of the floor, around a 1.84 m well with a 2 cm stone bed. The top is a 1.80 m slab, 14 cm thick,
with a carved symbol. Placed on the base's pivot, its underside rests 9 cm up and sinks 7 cm to
2 cm when pressed, onto the bed: its face goes from 13 cm above the curb to 6 cm above it.

One top per symbol: SM_PressurePlate_Top (diamond), and _Circle, _Triangle and _Cross.

    Blender -b --factory-startup --python make_pressure_plate.py -- /tmp/HC-A2
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import hc_a2_parts as P  # noqa: E402

kit = P.kit

FOOT = 2.0        # exact outer footprint
WELL = 1.84       # opening inside the curb
CURB_H = 0.10     # curb height above the floor
TOP = 1.80        # slab size
TOP_T = 0.14      # slab thickness
REST_Z = 0.09     # slab underside when up
PRESSED_Z = 0.02  # slab underside when pressed (sits on the bed)


def build_base():
    parts = []
    f, wl = FOOT / 2, WELL / 2
    # Long stones on the -y/+y sides, short ones between them, split off-center so the seams
    # don't line up, and a few chipped top corners.
    s, n, w, e = 0.3, -0.4, 0.25, -0.2
    stones = [
        ((-f, -f, 0), (s, -wl, CURB_H)), ((s, -f, 0), (f, -wl, CURB_H)),
        ((-f, wl, 0), (n, f, CURB_H)), ((n, wl, 0), (f, f, CURB_H)),
        ((-f, -wl, 0), (-wl, w, CURB_H)), ((-f, w, 0), (-wl, wl, CURB_H)),
        ((wl, -wl, 0), (f, e, CURB_H)), ((wl, e, 0), (f, wl, CURB_H)),
    ]
    chips = [(0,), (2,), (1,), (), (3,), (0, 2), (), (1,)]
    for i, (lo, hi) in enumerate(stones):
        parts.append(P.stone_block(f"curb_{i}", lo, hi, seed=10 + i, top_wobble=0.012, chips=chips[i], chip=0.045,
                                   bevel=0.028, segments=3))
    # The bed inside the well, so the sunk slab sits on stone rather than the cave floor.
    parts.append(P.stone_block("bed", (-wl, -wl, 0), (wl, wl, PRESSED_Z), seed=40, bevel=0.0,
                               material="M_StoneCarving"))
    base = P.finish(parts, "SM_PressurePlate_Base")
    kit.sit_on_floor(base)
    return base


def symbol_cutters(symbol):
    z = TOP_T + 0.03   # the slab's top face sits a little above TOP_T once wobbled
    depth = 0.075      # groove floor about 4.5 cm below the face
    w = 0.12           # groove width, wide enough to read at half-screen size
    if symbol == "diamond":
        return [P.ring_cutter("cut", P.polygon(4, 0.55, scale=(1.0, 0.72)), w, depth, z_top=z)]
    if symbol == "circle":
        return [P.ring_cutter("cut", P.polygon(32, 0.47), w, depth, z_top=z)]
    if symbol == "triangle":
        tri = [(x, y - 0.09) for x, y in P.polygon(3, 0.58, rot=math.pi / 2)]
        return [P.ring_cutter("cut", tri, w, depth, z_top=z)]
    if symbol == "cross":
        a, b = 0.45, 0.085
        return [P.solid_cutter("cut_h", [(-a, -b), (a, -b), (a, b), (-a, b)], depth, z_top=z),
                P.solid_cutter("cut_v", [(-b, -a), (b, -a), (b, a), (-b, a)], depth, z_top=z)]
    raise ValueError(symbol)


def edge_chips(seed):
    """Sloped chips knocked off the slab's top edges (style rule 5)."""
    import random
    rng = random.Random(seed)
    cuts = []
    for side in range(4):
        for _ in range(rng.choice((1, 2))):
            t = rng.uniform(-0.6, 0.6)
            ln = rng.uniform(0.25, 0.45)
            c = P.chip_cutter(f"chip_{side}", t - ln / 2, t + ln / 2, TOP / 2, TOP_T,
                              rng.uniform(0.07, 0.1))
            c.rotation_euler.z = side * math.pi / 2
            P.bpy.context.view_layer.update()
            cuts.append(c)
    return cuts


def build_top(symbol, name, seed):
    s = TOP / 2
    slab = P.stone_block(name, (-s, -s, 0), (s, s, TOP_T), seed=seed, top_wobble=0.015,
                         xy_wobble=0.015, chips=(1, 3), chip=0.07, bevel=0.04, segments=3)
    P.carve(slab, edge_chips(seed))
    P.carve(slab, symbol_cutters(symbol))
    P.soften(slab, width=0.02)
    top = P.finish([slab], name)
    kit.sit_on_floor(top)
    return top


VARIANTS = [("diamond", "SM_PressurePlate_Top", 51), ("circle", "SM_PressurePlate_Top_Circle", 52),
            ("triangle", "SM_PressurePlate_Top_Triangle", 53), ("cross", "SM_PressurePlate_Top_Cross", 54)]


def main():
    out = P.out_dir()
    kit.reset()
    base = build_base()
    kit.preview_sheet([base], f"{out}/SM_PressurePlate_Base_preview.png", title="SM_PressurePlate_Base")
    kit.export_glb([base], f"{out}/SM_PressurePlate_Base.glb")
    for symbol, name, seed in VARIANTS:
        kit.reset()
        top = build_top(symbol, name, seed)
        kit.preview_sheet([top], f"{out}/{name}_preview.png", title=name)
        kit.export_glb([top], f"{out}/{name}.glb")
    # The assembly, slab up, for review only (not exported).
    kit.reset()
    base = build_base()
    top = build_top("diamond", "SM_PressurePlate_Top", 51)
    top.location.z += REST_Z
    kit.preview_sheet([base, top], f"{out}/SM_PressurePlate_Assembled_preview.png",
                      title="SM_PressurePlate assembled, slab up")


main()
