"""HZ-A4: SM_CarvedPillar.

A 4 m cave pillar of stacked, chunky cut-stone blocks, each a little off true, with a wider
plinth and capital, chipped corners, and one wider band block carved with a double diamond on
each face, like the altar and statue plinths in the style frames.

    blender -b --factory-startup --python SourceArt/HZ/HZ-A4/make_carved_pillar.py -- /tmp/HZ-A4
"""
import math
import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "HZ-A3"))
import hz_parts as hz  # noqa: E402

kit = hz.kit

# (width, height, twist in degrees, x/y offset) from the floor up. Heights add up to 4.0 m.
STACK = [
    (1.15, 0.34, 0.0, (0.0, 0.0)),     # plinth
    (0.86, 0.78, 3.0, (0.01, -0.01)),
    (0.82, 0.62, -2.5, (-0.015, 0.01)),
    (0.92, 0.56, 1.0, (0.0, 0.0)),     # the carved band
    (0.80, 0.80, 4.0, (0.015, 0.01)),
    (0.84, 0.56, -3.0, (-0.01, -0.015)),
    (1.10, 0.34, 1.5, (0.0, 0.0)),     # capital
]
CARVED = 3
SEAM = 0.012


def diamond(r):
    return hz.polygon(4, r, rot=math.pi / 2)


def carve(block, width, z, height, twist, offset):
    """A double diamond on each face of the band block."""
    for k in range(4):
        a = k * math.pi / 2 + twist
        rot = (math.pi / 2, 0, a)
        nx, ny = math.sin(a), -math.cos(a)  # outward normal of face k
        cx, cy = offset[0] + nx * width / 2, offset[1] + ny * width / 2
        outer = hz.frame(f"dia{k}", diamond(0.24), diamond(0.16), 0.09,
                         location=(cx, cy, z + height / 2), rotation=rot)
        hz.boolean(block, outer)
        inner = hz.prism(f"dot{k}", diamond(0.07), 0.09, location=(cx, cy, z + height / 2), rotation=rot)
        hz.boolean(block, inner)


def build():
    stone = hz.mat_stone()
    rng = random.Random(5)
    blocks = []
    z = 0.0
    for i, (w, h, twist, (ox, oy)) in enumerate(STACK):
        top_gap = SEAM if i < len(STACK) - 1 else 0.0
        bh = h - top_gap
        b = hz.box(f"block{i}", (w, w * rng.uniform(0.97, 1.02), bh), location=(0, 0, bh / 2))
        wob = 0.01 if i == CARVED else 0.025
        for v in b.data.vertices:  # no edge perfectly straight; the bottom stays flat
            v.co.x += rng.uniform(-wob, wob)
            v.co.y += rng.uniform(-wob, wob)
            if v.co.z > 0:
                v.co.z += rng.uniform(-0.01, 0.01)
        b.data.materials.append(stone)
        b.location = (ox, oy, z)
        b.rotation_euler = (0, 0, math.radians(twist))
        hz.apply_transform(b)
        # Bevel before cutting: the bevel's overlap clamp would shrink every edge to the size
        # of the smallest chip edge.
        hz.soft_bevel(b, width=rng.uniform(0.1, 0.13), segments=3)
        if i == CARVED:
            carve(b, w, z, bh, math.radians(twist), (ox, oy))
        # A chipped corner or two, rotated to a random corner.
        for c in range(1 if i in (0, len(STACK) - 1) else 2):
            corner = rng.randrange(4) * math.pi / 2 + math.pi / 4 + math.radians(twist)
            r = w / 2 * math.sqrt(2) - 0.06  # the bevel has already rounded the corner off
            cz = z + (h - top_gap if rng.random() < 0.6 else 0.0)
            chip = hz.box(f"chip{i}{c}", (0.24, 0.2, 0.16),
                          location=(ox + math.cos(corner) * r, oy + math.sin(corner) * r, cz),
                          rotation=(rng.uniform(0.3, 0.8), rng.uniform(0.3, 0.8), corner))
            hz.boolean(b, chip)
        blocks.append(b)
        z += h
    pillar = kit.join(blocks, "SM_CarvedPillar")
    hz.finish(pillar, normals=False)
    return pillar


def main():
    out = hz.out_dir()
    kit.reset()
    pillar = build()
    hz.preview([pillar], str(out / "SM_CarvedPillar_preview.png"), title="SM_CarvedPillar")
    kit.export_glb([pillar], str(out / "SM_CarvedPillar.glb"))


main()
