"""HZ-A3: SM_DartLauncher.

A carved stone wall panel, 1.5 m wide and 1.2 m high, that sits flush in the trap corridor's
wall: a plinth, two side posts, a lintel with a trap-red warning triangle, and a carved band
with a channel holding five dart holes, edged with trap-red strips. The carved face points
toward -Y in Blender.

    blender -b --factory-startup --python SourceArt/HZ/HZ-A3/make_dart_launcher.py -- /tmp/HZ-A3
"""
import math
import random
import sys
from pathlib import Path

import bpy

sys.path.append(str(Path(__file__).resolve().parent))
import hz_parts as hz  # noqa: E402

kit = hz.kit

W, H = 1.5, 1.2
FRONT, BACK = -0.15, 0.15   # the wall surface is the front face
BAND_LO, BAND_HI = 0.44, 0.76
BAND_PROUD = 0.03           # the carved band stands this far out of the wall
HOLES = 5
HOLE_PITCH = 0.19
HOLE_R = 0.055
HOLE_Z = (BAND_LO + BAND_HI) / 2


def block(name, x0, x1, z0, z1, seed, front=FRONT, wobble=0.01):
    b = hz.stone_block(name, (x0, front, z0), (x1, BACK, z1), seed=seed, tilt=0.0, material=hz.mat_stone())
    # Nudge the front corners in and out a little: nothing perfectly straight.
    rng = random.Random(seed)
    for v in b.data.vertices:
        if v.co.y < 0:
            v.co.y += rng.uniform(-wobble, wobble * 0.3)
            v.co.z += rng.uniform(-wobble, wobble) if 0.01 < v.co.z < H - 0.01 else 0
    return b


def build():
    trap = hz.mat_trap()
    g = 0.007  # half the seam between blocks
    post = 0.26
    blocks = [
        block("plinth", -W / 2, W / 2, 0.0, 0.24 - g, 1, front=FRONT - 0.03, wobble=0.006),
        block("postL", -W / 2, -W / 2 + post - g, 0.24 + g, 0.88 - g, 2),
        block("postR", W / 2 - post + g, W / 2, 0.24 + g, 0.88 - g, 3),
        block("under", -W / 2 + post + g, W / 2 - post - g, 0.24 + g, BAND_LO - g, 4,
              front=FRONT + 0.015),
        block("band", -W / 2 + post + g, W / 2 - post - g, BAND_LO + g, BAND_HI - g, 5,
              front=FRONT - BAND_PROUD, wobble=0.006),
        block("over", -W / 2 + post + g, W / 2 - post - g, BAND_HI + g, 0.88 - g, 6,
              front=FRONT + 0.015),
        block("lintel", -W / 2, W / 2, 0.88 + g, H, 7, front=FRONT - 0.045),
    ]
    # Soft bevels first: cutting first would let the bevel's overlap clamp shrink every edge.
    for k, b in enumerate(blocks):
        hz.soft_bevel(b, width=0.035 + 0.01 * (k % 3), segments=3)
    band = blocks[4]
    face = FRONT - BAND_PROUD
    # The carved channel the darts fire from.
    ch_w = HOLE_PITCH * HOLES + 0.04
    channel = hz.box("channel", (ch_w, 0.08, 0.16), location=(0, face, HOLE_Z))
    hz.boolean(band, channel)
    for k in range(HOLES):
        x = (k - (HOLES - 1) / 2) * HOLE_PITCH
        bore = hz.cylinder(f"bore{k}", HOLE_R, 0.36, sides=8, location=(x, face, HOLE_Z),
                           rotation=(math.pi / 2, 0, math.pi / 8))
        hz.boolean(band, bore)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=HOLE_R + 0.025, radius2=HOLE_R, depth=0.025,
                                        location=(x, face + 0.04 + 0.0125 - 0.002, HOLE_Z),
                                        rotation=(math.pi / 2, 0, math.pi / 8))
        hz.boolean(band, bpy.context.active_object)
    # Chips on the lintel and the plinth.
    for k, (blk, x, z, r) in enumerate([(6, W / 2, H, (0.4, 0.6, 0.3)), (0, -W / 2, 0.24, (0.7, 0.2, 0.5)),
                                         (6, -0.35, H, (0.2, 0.9, 0.1))]):
        chip = hz.box(f"chip{k}", (0.16, 0.12, 0.1), location=(x, FRONT - 0.04, z), rotation=r)
        hz.boolean(blocks[blk], chip)

    # Trap-red warning: strips above and below the channel, and a triangle on the lintel
    # pointing down at the holes. Each sits in a shallow recess, just proud of the stone.
    warn = []
    for k, z in enumerate((HOLE_Z + 0.11, HOLE_Z - 0.11)):
        recess = hz.box(f"strip_recess{k}", (ch_w, 0.03, 0.04), location=(0, face, z))
        hz.boolean(band, recess)
        warn.append(kit.chunky_block(f"strip{k}", size=(ch_w - 0.02, 0.026, 0.03), bevel=0.006,
                                     wobble=0.0, material=trap))
        warn[-1].location = (0, face + 0.009, z - 0.015)
        hz.apply_transform(warn[-1])
    lintel_mid = (0.88 + H) / 2
    lintel_face = FRONT - 0.045
    recess = hz.prism("tri_recess", hz.polygon(3, 0.165, rot=-math.pi / 2), 0.04,
                      location=(0, lintel_face, lintel_mid), rotation=(math.pi / 2, 0, 0))
    hz.boolean(blocks[6], recess)
    warn.append(hz.frame("tri", hz.polygon(3, 0.15, rot=-math.pi / 2), hz.polygon(3, 0.065, rot=-math.pi / 2),
                         0.03, location=(0, lintel_face + 0.011, lintel_mid), rotation=(math.pi / 2, 0, 0),
                         material=trap))

    for w in warn:
        kit.chunky_bevel(w, width=0.005, segments=1, angle_deg=50, smooth_deg=40)
    panel = kit.join(blocks + warn, "SM_DartLauncher")
    hz.finish(panel, normals=False)
    return panel


def main():
    out = hz.out_dir()
    kit.reset()
    panel = build()
    lo, hi = kit._bounds([panel])
    pivot_y = (lo.y + hi.y) / 2
    print(f"DARTS hole centers: Z {HOLE_Z * 100:.1f} cm above the pivot, X "
          + ", ".join(f"{(k - (HOLES - 1) / 2) * HOLE_PITCH * 100:.0f}" for k in range(HOLES))
          + f" cm; band face at Y {(FRONT - BAND_PROUD - pivot_y) * 100:.1f} cm, "
          f"post faces (the wall line) at Y {(FRONT - pivot_y) * 100:.1f} cm, back at Y "
          f"{(BACK - pivot_y) * 100:.1f} cm from the pivot (Blender axes)")
    kit.preview_sheet([panel], str(out / "SM_DartLauncher_preview.png"), title="SM_DartLauncher")
    kit.export_glb([panel], str(out / "SM_DartLauncher.glb"))


main()
