"""HC-A2: SM_Altar, the cut-stone altar from frame 03.

A two-stone foot, a body of three big stones with a carved double diamond on the front, and a
0.9 x 0.9 m capstone whose top is 1.0 m up, with a round socket 40 cm across and 3 cm deep for
the key relic. The front faces +X, the actor's forward in Unreal.

    Blender -b --factory-startup --python make_altar.py -- /tmp/HC-A2
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import hc_a2_parts as P  # noqa: E402

kit = P.kit

TOP_Z = 1.0        # top of the capstone
CAP = 0.90         # capstone footprint
CAP_T = 0.24
BODY = 0.80
FOOT = 1.20
FOOT_T = 0.14
SOCKET_R = 0.20
SOCKET_D = 0.03


def front_carving():
    """A diamond groove with a recessed diamond inside it, on the face stone at +X."""
    cz = FOOT_T + (TOP_Z - CAP_T - FOOT_T) / 2
    face_x = BODY / 2
    ring = P.ring_cutter("diamond_ring", P.polygon(4, 0.27, scale=(1.0, 1.0)), 0.065, 0.045, z_top=0.0)
    core = P.solid_cutter("diamond_core", P.polygon(4, 0.11), 0.035, z_top=0.0)
    for c in (ring, core):
        P.move(c, loc=(face_x, 0, cz), rot=(0, math.pi / 2, 0))
    return [ring, core]


def build():
    parts = []
    h = FOOT_T
    f = FOOT / 2
    # Foot: two long stones, split off-center.
    parts.append(P.stone_block("foot_a", (-f, -f, 0), (0.12, f, h), seed=1, top_wobble=0.02,
                               chips=(0, 3), chip=0.07, bevel=0.035))
    parts.append(P.stone_block("foot_b", (0.12, -f, 0), (f, f, h), seed=2, top_wobble=0.02,
                               chips=(1,), chip=0.07, bevel=0.035))
    # Body: the face stone at the front, and two stacked stones behind it.
    b = BODY / 2
    top = TOP_Z - CAP_T
    face = P.stone_block("face", (0.0, -b, h), (b, b, top), seed=3, top_wobble=0.015, xy_wobble=0.02,
                         chips=(2,), chip=0.06, bevel=0.035)
    P.carve(face, front_carving())
    P.soften(face, width=0.012)
    parts.append(face)
    mid = h + (top - h) * 0.55
    parts.append(P.stone_block("back_low", (-b, -b, h), (0.0, b, mid), seed=4, top_wobble=0.018,
                               xy_wobble=0.018, chips=(0,), chip=0.05, bevel=0.035))
    parts.append(P.stone_block("back_high", (-b + 0.01, -b + 0.01, mid), (0.0, b - 0.01, top), seed=5,
                               top_wobble=0.008, xy_wobble=0.01, chips=(3,), chip=0.05, bevel=0.035))
    # Capstone, overhanging the body, with the relic socket.
    c = CAP / 2
    cap = P.stone_block("cap", (-c, -c, top), (c, c, TOP_Z), seed=6, top_wobble=0.006,
                        xy_wobble=0.01, chips=(0, 2), chip=0.08, bevel=0.04)
    socket = P.solid_cutter("socket", P.polygon(32, SOCKET_R), SOCKET_D, z_top=TOP_Z)
    P.carve(cap, [socket])
    P.soften(cap, width=0.012)
    parts.append(cap)
    altar = P.finish(parts, "SM_Altar")
    kit.sit_on_floor(altar)
    return altar


def main():
    out = P.out_dir()
    kit.reset()
    altar = build()
    kit.preview_sheet([altar], f"{out}/SM_Altar_preview.png", title="SM_Altar")
    kit.export_glb([altar], f"{out}/SM_Altar.glb")


main()
