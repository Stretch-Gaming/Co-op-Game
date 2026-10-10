"""HZ-A3: SM_SpikePlate_Base and SM_SpikePlate_Spikes.

An exact 2.0 x 2.0 m cut-stone floor plate with a 4 x 4 grid of holes and two small trap-red
runes, and a separate set of 16 chunky iron spikes on a hidden iron grid that rises through the
holes. Both meshes are centered on the same XY, so with their pivots lined up in XY every spike
sits in its hole.

    blender -b --factory-startup --python SourceArt/HZ/HZ-A3/make_spike_plate.py -- /tmp/HZ-A3
"""
import math
import sys
from pathlib import Path

import bpy

sys.path.append(str(Path(__file__).resolve().parent))
import hz_parts as hz  # noqa: E402

kit = hz.kit

PLATE = 2.0          # exact footprint, so it lines up with BP_Trap_Spikes
THICK = 0.25         # the top is this far above the pivot; sink the pivot by this much
GRID = 4
PITCH = 0.36
HOLE_R = 0.11
HOLE_DEPTH = 0.18
SPIKE_H = 0.46
SPIKE_R = 0.08
BAR_H = 0.05
FIELD = 0.72         # half-width of the holed field; a border of cut stone runs outside it
SEAM = 0.014         # gap between stone blocks
BACKING = 0.05       # a hidden slab under the blocks, so the seams have a bottom


def grid_positions():
    off = (GRID - 1) / 2
    return [((i - off) * PITCH, (j - off) * PITCH) for i in range(GRID) for j in range(GRID)]


def build_base():
    stone, trap = hz.mat_stone(), hz.mat_trap()
    h, g, f = PLATE / 2, SEAM / 2, FIELD
    lo_z, hi_z = BACKING - 0.01, THICK
    boxes = [
        # Long border blocks along X, then short ones along Y at the approach edges.
        ((-h, f + g, lo_z), (h, h, hi_z)),
        ((-h, -h, lo_z), (h, -f - g, hi_z)),
        ((f + g, -f + g, lo_z), (h, f - g, hi_z)),
        ((-h, -f + g, lo_z), (-f - g, f - g, hi_z)),
        # The four slabs of the holed field.
        ((g, g, lo_z), (f - g, f - g, hi_z)),
        ((-f + g, g, lo_z), (-g, f - g, hi_z)),
        ((g, -f + g, lo_z), (f - g, -g, hi_z)),
        ((-f + g, -f + g, lo_z), (-g, -g, hi_z)),
    ]
    blocks = [hz.stone_block(f"block{k}", lo, hi, seed=20 + k, material=stone)
              for k, (lo, hi) in enumerate(boxes)]
    backing = hz.box("backing", (PLATE, PLATE, BACKING), location=(0, 0, BACKING / 2))
    backing.data.materials.append(stone)
    # Soft bevels first: cutting first would let the bevel's overlap clamp shrink every edge.
    for k, b in enumerate(blocks):
        hz.soft_bevel(b, width=0.04 + 0.008 * (k % 3), segments=3)

    # Holes, each with a chamfered rim from a short cone cutter at the top.
    for k, (x, y) in enumerate(grid_positions()):
        slab = blocks[4 + (0 if x > 0 and y > 0 else 1 if y > 0 else 2 if x > 0 else 3)]
        c = hz.cylinder(f"hole{k}", HOLE_R, HOLE_DEPTH + 0.1, sides=8,
                        location=(x, y, THICK - HOLE_DEPTH + (HOLE_DEPTH + 0.1) / 2),
                        rotation=(0, 0, math.pi / 8))
        hz.boolean(slab, c)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=HOLE_R, radius2=HOLE_R + 0.03, depth=0.03,
                                        location=(x, y, THICK - 0.015 + 0.004),
                                        rotation=(0, 0, math.pi / 8))
        hz.boolean(slab, bpy.context.active_object)
    # Chipped corners: lived in, without touching the outer footprint's base.
    for k, (blk, x, y, rz) in enumerate([(0, h, h, 0.6), (1, -h, -h, 2.2), (4, f, f, 0.9),
                                          (7, -f, -f, 2.6)]):
        chip = hz.box(f"chip{k}", (0.16, 0.12, 0.09), location=(x, y, THICK), rotation=(0.5, 0.35, rz))
        hz.boolean(blocks[blk], chip)
    # A warning triangle at each approach edge (the corridor runs along X), pointing at the holes.
    runes = []
    for k, side in enumerate((1, -1)):
        x = side * (f + h) / 2
        rot = (0, 0, math.pi if side > 0 else 0.0)
        recess = hz.prism(f"recess{k}", hz.polygon(3, 0.14), 0.04, location=(x, 0, THICK),
                          rotation=rot)
        hz.boolean(blocks[2 + k], recess)
        # The inlay's top sits just above the stone, so it reads and can glow.
        runes.append(hz.frame(f"rune{k}", hz.polygon(3, 0.125), hz.polygon(3, 0.055), 0.03,
                              location=(x, 0, THICK - 0.011), rotation=rot, material=trap))
    for r in runes:
        kit.chunky_bevel(r, width=0.006, segments=1, angle_deg=50, smooth_deg=40)
    base = kit.join(blocks + [backing] + runes, "SM_SpikePlate_Base")
    hz.finish(base, normals=False)
    return base


def build_spikes():
    iron = hz.mat_iron()
    parts = []
    for k, (x, y) in enumerate(grid_positions()):
        s = hz.spike(f"spike{k}", height=SPIKE_H, radius=SPIKE_R, sides=6, seed=100 + k, material=iron)
        s.location = (x, y, BAR_H)
        hz.apply_transform(s)
        parts.append(s)
    # A hidden iron grid ties the spikes together, so the set moves as one piece.
    span = (GRID - 1) * PITCH + 0.2  # past the spikes, so the bounds are square
    off = (GRID - 1) / 2
    for i in range(GRID):
        c = (i - off) * PITCH
        parts.append(kit.chunky_block(f"barx{i}", size=(span, 0.07, BAR_H), bevel=0.012, wobble=0.0,
                                      material=iron))
        parts[-1].location = (0, c, 0)
        parts.append(kit.chunky_block(f"bary{i}", size=(0.07, span, BAR_H * 0.98), bevel=0.012,
                                      wobble=0.0, material=iron))
        parts[-1].location = (c, 0, 0.0005)
    for p in parts:
        hz.apply_transform(p)
    spikes = kit.join(parts, "SM_SpikePlate_Spikes")
    hz.finish(spikes)
    return spikes


def main():
    out = hz.out_dir()
    kit.reset()
    base = build_base()
    spikes = build_spikes()
    raised_offset = THICK - BAR_H - SPIKE_H * 0.09  # collar top at the plate top
    print(f"SPIKES raised pivot Z, relative to the plate pivot: {raised_offset * 100:.1f} cm")
    lowered_offset = THICK - BAR_H - SPIKE_H - 0.03  # tips 3 cm under the plate top
    print(f"SPIKES lowered pivot Z, relative to the plate pivot: {lowered_offset * 100:.1f} cm")

    spikes.hide_render = True
    kit.preview_sheet([base], str(out / "SM_SpikePlate_Base_preview.png"), title="SM_SpikePlate_Base")
    spikes.hide_render = False
    base.hide_render = True
    kit.preview_sheet([spikes], str(out / "SM_SpikePlate_Spikes_preview.png"), title="SM_SpikePlate_Spikes")
    base.hide_render = False
    kit.export_glb([spikes], str(out / "SM_SpikePlate_Spikes.glb"))
    kit.export_glb([base], str(out / "SM_SpikePlate_Base.glb"))

    # Assembled, with the spikes raised, for review only.
    spikes.location.z = raised_offset
    kit.preview_sheet([base, spikes], str(out / "SM_SpikePlate_Raised_preview.png"),
                      title="SM_SpikePlate raised")


main()
