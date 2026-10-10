"""HC-A2: SM_ChamberGate_Frame and SM_ChamberGate_Leaf.

Chunky stone posts and a lintel around an exact 4.0 m wide, 4.0 m high opening. The opening
runs along Y and the passage along X, so the gate drops into a wall that crosses the corridor
without rotating. Each post has a 34 cm slot, 18 cm deep, and the lintel is two beams with the
same slot between them, so the leaf slides straight up through it into the rock above.

The leaf is a slab of cut stones, 4.30 m wide (15 cm in each post's slot), 28 cm thick and 4.5 m
tall (the top 50 cm sits inside the lintel when closed), with a carved diamond on both faces,
as in the gate in frame 03's background. Closed, its pivot sits on the frame's pivot; open, it
is 4.0 m higher, with its bottom flush with the lintel's underside.

    Blender -b --factory-startup --python make_chamber_gate.py -- /tmp/HC-A2
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import hc_a2_parts as P  # noqa: E402
from mathutils import Matrix  # noqa: E402

kit = P.kit

OPEN_W = 4.0       # exact opening width
OPEN_H = 4.0       # opening height, to the lintel's underside
POST_W = 1.0       # each post, along Y
DEPTH = 1.2        # posts and lintel, along X
SLOT = 0.34        # slot width, along X
GROOVE = 0.18      # how far the slot cuts into each post
LINTEL_H = 0.85
LEAF_T = 0.28
LEAF_W = OPEN_W + 2 * 0.15
LEAF_H = OPEN_H + 0.5
TRAVEL = OPEN_H    # how far the leaf rises to open


def post(sign, seed):
    """One post: front and back piers either side of the slot, and a core behind the groove,
    each in three courses with staggered seams. `sign` is +1 for the +Y post."""
    parts = []
    y_in, y_out = OPEN_W / 2, OPEN_W / 2 + POST_W
    s, d = SLOT / 2, DEPTH / 2

    def box(name, x0, x1, y0, y1, z0, z1, k, **kw):
        lo = (x0, min(sign * y0, sign * y1), z0)
        hi = (x1, max(sign * y0, sign * y1), z1)
        kw.setdefault("bevel", 0.05)
        kw.setdefault("top_wobble", 0.02)
        parts.append(P.stone_block(name, lo, hi, seed=seed + k, **kw))

    pier_courses = [0.0, 1.45, 2.8, OPEN_H]
    core_courses = [0.0, 2.1, OPEN_H]
    # Each course sticks out a little more or less on the outside faces, like hand-laid stone.
    # The faces toward the opening and the slot stay exact.
    out_y = [0.06, -0.04, 0.03]
    out_x = [0.04, -0.03, 0.05]
    for i in range(3):
        z0, z1 = pier_courses[i], pier_courses[i + 1]
        chips = (i % 4, (i + 2) % 4) if i < 2 else ()
        box(f"pier_f{i}", s, d + out_x[i], y_in, y_out + out_y[i], z0, z1, i, chips=chips, chip=0.12)
        box(f"pier_b{i}", -d - out_x[2 - i], -s, y_in, y_out + out_y[2 - i], z0, z1, 10 + i,
            chips=chips[:1], chip=0.12)
    for i in range(2):
        box(f"core{i}", -s, s, y_in + GROOVE, y_out - 0.02, core_courses[i], core_courses[i + 1], 20 + i)
    # Feet: a wide stone at the base of each pier, flush with the opening so it stays 4.0 m.
    box("foot_f", s, d + 0.18, y_in, y_out + 0.28, 0.0, 0.34, 30, chips=(1, 2), chip=0.12, bevel=0.07)
    box("foot_b", -d - 0.18, -s, y_in, y_out + 0.28, 0.0, 0.34, 31, chips=(0, 3), chip=0.12, bevel=0.07)
    # Rubble against the outside of the post: fallen chips, lived in (style rule 5). The same
    # rocks, mirrored, on both posts, so the bounds (and the pivot) stay centered.
    rubble = [((0.38, 3.32), (0.55, 0.5, 0.4)), ((-0.42, 3.3), (0.45, 0.42, 0.3))]
    for k, ((x, y), size) in enumerate(rubble):
        r = kit.faceted_rock(f"rubble{k}", size=size, seed=140 + k, facets=22,
                             material=P.mat("M_Stone"))
        P.move(r, (x, y, 0))
        if sign < 0:
            r.matrix_world = Matrix.Scale(-1, 4, (0, 1, 0)) @ r.matrix_world
            P.bpy.context.view_layer.objects.active = r
            P.bpy.ops.object.select_all(action="DESELECT")
            r.select_set(True)
            P.bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        parts.append(r)
    return parts


def keystone_carving(x_face, cz, sign):
    ring = P.ring_cutter("ks_ring", P.polygon(4, 0.3), 0.075, 0.05, z_top=0.0)
    core = P.solid_cutter("ks_core", P.polygon(4, 0.1), 0.04, z_top=0.0)
    for c in (ring, core):
        P.move(c, loc=(x_face, 0, cz), rot=(0, sign * math.pi / 2, 0))
    return [ring, core]


def lintel(seed):
    parts = []
    s, d = SLOT / 2, DEPTH / 2 + 0.05
    half = OPEN_W / 2 + POST_W + 0.3
    z0, z1 = OPEN_H, OPEN_H + LINTEL_H
    ks = 0.6  # keystone half width
    for side, x0, x1 in (("f", s, d), ("b", -d, -s)):
        parts.append(P.stone_block(f"lintel_{side}_l", (x0, -half, z0), (x1, -ks, z1), seed=seed,
                                   top_wobble=0.03, chips=(0, 3), chip=0.12, bevel=0.06))
        parts.append(P.stone_block(f"lintel_{side}_r", (x0, ks, z0), (x1, half, z1), seed=seed + 1,
                                   top_wobble=0.03, chips=(1, 2), chip=0.12, bevel=0.06))
        # The keystone stands proud of the beam, front and back, with the gate's diamond.
        sign = 1 if side == "f" else -1
        kx0, kx1 = (x0, x1 + 0.08) if side == "f" else (x0 - 0.08, x1)
        key = P.stone_block(f"keystone_{side}", (kx0, -ks, z0), (kx1, ks, z1 + 0.25), seed=seed + 2,
                            top_wobble=0.02, chips=(0, 2), chip=0.1, bevel=0.06)
        face = kx1 if side == "f" else kx0
        P.carve(key, keystone_carving(face, z0 + (LINTEL_H + 0.25) / 2, sign))
        P.soften(key, width=0.015)
        parts.append(key)
        seed += 5
    return parts


def check_centered(obj):
    """The cleanup script puts the pivot at the bounds' base center. The leaf's offsets assume
    both pivots land on the slot's center line, so the bounds must be centered on X and Y."""
    lo, hi = kit._bounds([obj])
    c = (lo + hi) / 2
    assert abs(c.x) < 0.005 and abs(c.y) < 0.005 and abs(lo.z) < 0.001, (obj.name, c, lo.z)


def build_frame():
    parts = post(+1, 100) + post(-1, 200) + lintel(300)
    frame = P.finish(parts, "SM_ChamberGate_Frame")
    check_centered(frame)
    kit.sit_on_floor(frame)
    return frame


def leaf_carving():
    cz = 2.3
    cuts = []
    for sign in (1, -1):
        ring = P.ring_cutter("leaf_ring", P.polygon(4, 0.6, scale=(1.15, 1.0)), 0.1, 0.06, z_top=0.0)
        core = P.solid_cutter("leaf_core", P.polygon(4, 0.2, scale=(1.15, 1.0)), 0.045, z_top=0.0)
        for c in (ring, core):
            P.move(c, loc=(sign * LEAF_T / 2, 0, cz), rot=(0, sign * math.pi / 2, 0))
        cuts += [ring, core]
    return cuts


def build_leaf():
    t, w = LEAF_T / 2, LEAF_W / 2
    gap = 0.015
    courses = [(0.0, 1.55, [-w, 0.45, w]),
               (1.55, 3.05, [-w, -0.8, 0.8, w]),
               (3.05, LEAF_H, [-w, -0.55, w])]
    # Each stone sits a little proud or shy of the others (still inside the 34 cm slot), and the
    # visible ones have a chipped corner.
    proud = [0.012, -0.01, 0.0, 0.0, -0.012, 0.01, 0.0]
    chips = [(2,), (3,), (2, 3), (), (3,), (), ()]
    parts = []
    n = 0
    for ci, (z0, z1, ys) in enumerate(courses):
        for k in range(len(ys) - 1):
            y0 = ys[k] + (gap if k > 0 else 0)
            y1 = ys[k + 1] - (gap if k < len(ys) - 2 else 0)
            zb = z0 + (gap if ci > 0 else 0)
            x = proud[n]
            stone = P.stone_block(f"leaf_{ci}{k}", (-t + x, y0, zb), (t + x, y1, z1), seed=400 + n,
                                  top_wobble=0.02 if ci < 2 else 0.0, chips=chips[n], chip=0.09,
                                  bevel=0.05)
            if ci == 1 and k == 1:
                P.carve(stone, leaf_carving())
                P.soften(stone, width=0.015)
            parts.append(stone)
            n += 1
    leaf = P.finish(parts, "SM_ChamberGate_Leaf")
    check_centered(leaf)
    kit.sit_on_floor(leaf)
    return leaf


def main():
    out = P.out_dir()
    kit.reset()
    frame = build_frame()
    kit.preview_sheet([frame], f"{out}/SM_ChamberGate_Frame_preview.png", title="SM_ChamberGate_Frame")
    kit.export_glb([frame], f"{out}/SM_ChamberGate_Frame.glb")
    kit.reset()
    leaf = build_leaf()
    kit.preview_sheet([leaf], f"{out}/SM_ChamberGate_Leaf_preview.png", title="SM_ChamberGate_Leaf")
    kit.export_glb([leaf], f"{out}/SM_ChamberGate_Leaf.glb")
    # The assembly, half open, for review only (not exported).
    kit.reset()
    frame = build_frame()
    leaf = build_leaf()
    leaf.location.z += TRAVEL * 0.5
    kit.preview_sheet([frame, leaf], f"{out}/SM_ChamberGate_Assembled_preview.png",
                      title="SM_ChamberGate assembled, half open")


main()
