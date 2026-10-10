# HZ-A5: Map 2 kit

Source art for Map 2's sandstone antechamber ([#56](https://github.com/StretchGaming/Co-op-Game/issues/56)), matched to style frame 06 ([`frame-06-egyptian-antechamber.png`](../../PG/PG-A0/style-frames/frame-06-egyptian-antechamber.png)).

- **Meshes** (from #64): `SM_EgyptPillar`, `SM_Brazier` and `SM_Brazier_Flame`, built by `make_pillar.py` and `make_brazier.py` in Blender. Each FBX has a `.validation.json` and a preview sheet.
- **Sandstone wall and floor:** 2048 × 2048 painted tileables for world-aligned `M_Stylized` instances, built by `make_sandstone.py`.
- **Hieroglyph decals:** five carved-glyph decals for deferred decal material instances, built by `make_hieroglyphs.py`.

`hz_tex.py` holds what the two texture scripts share: periodic noise, distance fields that wrap around the tile, DirectX normals from height, the preview lighting, the seam check and PNG writing.

## Sandstone wall and floor

| Set | Tile | Picked candidate | Rejected candidate |
| --- | --- | --- | --- |
| `T_Sandstone_Wall_*` | 300 × 300 cm: five courses of 54–66 cm blocks, 80–140 cm long | **A, coursed ashlar**: even courses of large blocks in running bond, wide soft bevels, a few chips and cracks | B, rough uneven courses: courses from 38 to 88 cm, lumpier faces, more chips and cracks |
| `T_Sandstone_Floor_*` | 400 × 400 cm: 3 rows about 1.3 m deep, nine slabs 80–190 cm long, two of them split into two stacked slabs (11 in all) | **A, random-ashlar flagstones**: big rectangular slabs of mixed sizes | B, squarish Voronoi flagstones: Chebyshev Voronoi cells with stepped, zigzag outlines |

Why these: wall A has the stacked, even courses of frame 06's walls and pillar, and reads as cut stone at half-screen size. Wall B's lumpy faces and extra cracks add surface noise that the style rules say to avoid (rule 1), and its narrow courses look like rubble rather than a built temple. Floor A has frame 06's big rectangular slabs in mixed sizes. Floor B's zigzag outlines look like crazy paving, not cut slabs, and they repeat more visibly. Both candidates of each material are tiled 3 × 3 side by side in `T_Sandstone_*_candidates.png`. Only those small previews are committed; the rejected maps stay out of the repo.

Maps in each set:

| Suffix | Content | sRGB | Unreal compression |
| --- | --- | --- | --- |
| `_BC` | Base color. Painted: per-block color shifts around `#D9A86C`, soft brush patches, a lighter top on each wall block, lit top-left bevel edges, violet-brown joints (`#7A6062`, never black) | On | Default (BC1) |
| `_N` | Normal, **DirectX convention (green down, Y−)**, which is Unreal's own: leave Flip Green Channel off | Off | Normalmap (BC5) |
| `_ARM` | `M_Stylized`'s packed mask: R = cavity/edge (0.5 on flat faces, above 0.6 on convex edges, below 0.4 in joints), G = roughness, B = metallic (0) | Off | Masks |
| `_R` | Roughness on its own (the same as `_ARM`'s G): 0.80–0.98, matte like the pillar's `M_Sandstone` (0.85) | Off | Masks or Grayscale |
| `_AO` | Ambient occlusion on its own, 1 = open | Off | Masks or Grayscale |
| `_H` | Height, 16-bit, 0 = deepest joint, 1 = highest face; for height blending or parallax if wanted | Off | Grayscale (keep 16-bit) |

The face color averages `#D8A76F` on the wall and `#D9AA70` on the floor, against the palette's `#D9A86C`, so these sit beside the pillar and brazier, whose sandstone is the palette color. Previews: `T_Sandstone_Wall_preview.png` and `T_Sandstone_Floor_preview.png` show the base color and a lit version, each tiled 3 × 3, over every map of a single tile. The lighting is a rough stand-in, not Unreal's.

### Checks

`T_Sandstone_Wall.validation.json` and `T_Sandstone_Floor.validation.json` record the seed, the layout, each file's SHA-256, the face color and an edge-wrap check of every map as written. The check measures the mean step across each wrap seam (last column to first, last row to first) and ranks it against the step across every interior column or row boundary of the same map. Every seam ranks between the 5th and 77th percentile of the interior lines, so it is no more visible than any other line of pixels. As a control, the same check on the base color cropped by 37 px, which can't tile, must fail, and it does. The scripts also self-test the normal convention on a dome: its upper slope must store green below 0.5.

All the noise is built by filtering white noise in the frequency domain, and every distance field is measured across the wrap, so the maps tile by construction.

## Hieroglyph decals

| Decal | Design | Pixels | Placed size |
| --- | --- | --- | --- |
| `T_Hieroglyph_01` | A rayed sun over a bar, like the motif on frame 06's door | 1024 × 1024 | 100 × 100 cm |
| `T_Hieroglyph_02` | Two peaks under a small sun, over three rows of water | 1024 × 1024 | 100 × 100 cm |
| `T_Hieroglyph_03` | A framed column of five glyphs (reed, beetle, snake, bird, loop-cross) | 512 × 2048 | 50 × 200 cm |
| `T_Hieroglyph_04` | A frieze band of chevrons and glyphs. It tiles left to right, so it can run along a wall | 2048 × 512 | 200 × 50 cm per repeat |
| `T_Hieroglyph_05` | A cartouche: a rounded ring with a foot bar, holding a sun, a feather and a beetle | 512 × 1024 | 50 × 100 cm |

Each has `_BC` (sRGB on), `_Mask` (opacity, sRGB off) and `_N` (DirectX normal, sRGB off). They're sunk relief: the groove's floor is shaded blue-violet, the groove walls that face the top-left are lit and the others are dark, so they read even before the normal does anything. The glyphs are our own simple designs, drawn from code with Pillow's line and polygon tools, with a small hand-cut wobble. They're inspired by Egyptian carving in general, and don't copy any existing artwork or font.

`T_Hieroglyph_contact_sheet.png` shows each decal on the picked wall at its placed size, lit, beside its base color over its mask on a checker. `T_Hieroglyph.validation.json` records each file's SHA-256, the mask's coverage, that the mask is 0 on every border (so no decal shows a box edge), and the frieze's left-right wrap check.

## Rebuilding

From the repo root, with Python 3 and numpy, scipy and Pillow (tested with numpy 2.0.2, scipy 1.13.1 and Pillow 11.3.0):

```sh
python3 -I SourceArt/HZ/HZ-A5/make_sandstone.py     # both materials, about 40 s
python3 -I SourceArt/HZ/HZ-A5/make_hieroglyphs.py   # needs the wall maps for its contact sheet
```

Both write into this folder by default; pass another folder as the first argument to write elsewhere. `make_sandstone.py --candidates /tmp/HZ-A5-candidates` also writes the full maps of every candidate, rejected ones included, to a folder outside the repo. The seeds are fixed (5601 wall, 5602 floor, 5603 decals), and the output was byte-identical across runs on the same library versions. Other versions of numpy's FFT can change the last bit of a few pixels.

The meshes rebuild with `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python SourceArt/HZ/HZ-A5/make_<asset>.py -- /tmp/HZ-A5`, then `Tools/blender/cleanup_export.py`, as in [docs/assets.md](../../../docs/assets.md).

## Importing

- **Wall and floor:** import into `Content/Hazards/Art/` and make `MI_Sandstone_Wall` and `MI_Sandstone_Floor` from `M_Stylized`. Set `BaseColorTexture` to `_BC` and `MaskTexture` to `_ARM`, turn on `UseWorldAligned`, and set `WorldTileSize` to 300 for the wall and 400 for the floor. Set `Tint` to white, since the color is in the texture, and `RoughnessMultiplier` to 1.0, since `_ARM`'s G is already the final roughness. Texture group World. `_N` is ready, but `M_Stylized` has no normal input yet (see below).
- **Decals:** a decal parent material in the lane folder, such as `M_Decal_Hieroglyph`, with Material Domain **Deferred Decal** and Blend Mode **Translucent**, and texture parameters for `_BC`, `_Mask` (into Opacity) and `_N`. Roughness can be a constant, about 0.9. One `MI_Hieroglyph_0N` per decal. The project runs Substrate (`r.Substrate=True` in `Config/DefaultEngine.ini`), so check the decal in the editor: the legacy inputs are converted for you, or use a Substrate slab with the mask as coverage. Set the decal textures' address mode to Clamp, except `_04`, which needs Wrap on X to repeat along a wall.

## License

Generated by the team's own scripts with numpy, scipy and Pillow, from fixed seeds. No photos, textures, fonts or other inputs were downloaded or sampled, and no image generator was used. It's our own work: it can be published in this repo, and no credit is needed.
