# HZ-A1: cave surfaces

One material family for the Site 01 cave ([issue #52](https://github.com/StretchGaming/Co-op-Game/issues/52)): a painted rock for the walls (the ceiling reuses it) and a cave floor of damp slabs and grit, as 2K tileable textures for world-aligned instances of `M_Stylized`. Also a color-grading LUT and the settings for the atmosphere preset.

Everything here is made by the scripts in this folder, from fixed seeds, with Python (numpy, scipy, Pillow). Nothing was downloaded and no image generator was used, so there's no prompt. It's our own work: public redistribution is allowed and no credit is needed.

![Rock, tiled 3x3](previews/T_CaveRock_tiled3x3_preview.png)
![Floor, tiled 3x3](previews/T_CaveFloor_tiled3x3_preview.png)

## Files

| File | What it is | Import as |
| --- | --- | --- |
| `T_CaveRock_BC.png`, `T_CaveFloor_BC.png` | Base color, 2048², 8-bit RGB | sRGB on, `TC_Default` (BC1) |
| `T_CaveRock_ORM.png`, `T_CaveFloor_ORM.png` | Packed mask for `M_Stylized`'s `MaskTexture`: R AO and edges, G roughness, B metallic (0) | sRGB off, `TC_Masks` |
| `T_CaveRock_N.png`, `T_CaveFloor_N.png` | Normal map, **DirectX (green-down)**, Unreal's convention | `TC_Normalmap` (BC5), sRGB off, Flip Green Channel **off** |
| `T_CaveRock_R.png`, `T_CaveFloor_R.png` | Roughness on its own (same as the ORM's green) | sRGB off, `TC_Grayscale` |
| `T_CaveRock_AO.png`, `T_CaveFloor_AO.png` | Plain ambient occlusion (1 = open), floored at 0.3 | sRGB off, `TC_Grayscale` |
| `T_CaveRock_H.png`, `T_CaveFloor_H.png` | Height, 16-bit gray, 0–1 over the range in the validation JSON | Only if you need it; `M_Stylized` has no height input |
| `T_CaveGrade_LUT.png` | Color-grading LUT, 256 × 16 Unreal strip | Texture Group `ColorLookupTable` |
| `T_Cave*.validation.json` | Checks: tiling, sizes, hashes, normal convention, palette and noise numbers | — |
| `T_Cave*.generation.json` | Seed and every parameter of the chosen candidate, plus the height range | — |
| `candidates.json` | Scores for all six candidates | — |
| `previews/` | 3x3 tiled previews of the chosen surfaces, the candidate contact sheets, and the LUT applied to a style frame | Not for import |
| `hz_tileables.py` | Shared helpers: periodic noise, periodic Voronoi, normals, AO | — |
| `make_cave_surfaces.py` | Builds the candidates and the chosen textures | — |
| `validate_tileables.py` | Checks the textures and writes the previews and JSON | — |
| `make_grade_lut.py` | Builds the LUT, its check and its preview | — |

The `_BC` and `_ORM` pair is what `M_Stylized` actually takes. The others are there for whoever extends the material, and for checking.

## How they're made

Both surfaces are height fields on a torus, so every map tiles exactly: the noise is made in the frequency domain, the Voronoi cells come from a periodic KD-tree, and every blur and derivative wraps around.

- **Rock (walls and ceiling):** a dozen rounded chunks per tile, cut into flat facets with a periodic Delaunay mesh, like the low-poly planes on the style frames' rocks and the [cave rock concept](../../PG/PG-A0/style-frames/concepts/cave-rock-1m.png). Then softened into wide bevels.
- **Floor:** thirteen broad, nearly flat slabs per tile with rounded edges, like the floors in style frames 01, 02 and 05. The cracks are packed with grit and small pebbles, and the low ground holds dark, glossy damp patches.
- **Painting:** each chunk and facet gets its own value between the palette's rock mid `#4A4652` and rock light `#7A6E68`, with a slow warm-to-cool drift across the tile and a few broad, soft brush strokes. Steeper facets read darker. Creases go blue-violet toward the shadow color `#1E2433`, never black (the darkest pixel is about 20% luma), and outer edges go lighter and slightly warm.
- **No light direction is baked in.** The shading depends on how steep a facet is, not which way it faces. `M_Stylized`'s world-aligned mode maps the same texture onto walls, the ceiling and the floor, and mirrors it on opposite faces, so a baked key light would be wrong on half of them. The material's own gradient and edge highlight add the top-lit look.
- **Fine noise is kept out** (style.md rules 1 and 2): under 3% of the rock's base-color detail is at wavelengths below 8 cm, and nothing of the reserved relic, ghost, trap or crystal colors is in either texture (see `style.reserved_colors` in the validation JSON).

## Candidates and the pick

Three candidates per surface were made at 1024 px outside the repo. Only their scores (`candidates.json`) and contact sheets are kept here.

![Rock candidates](previews/T_CaveRock_candidates_preview.png)
![Floor candidates](previews/T_CaveFloor_candidates_preview.png)

| Candidate | Fine noise under 8 cm | Shapes over 25 cm | Split-screen contrast | Verdict |
| --- | ---: | ---: | ---: | --- |
| **Rock A, faceted chunks** | 0.026 | 0.76 | 0.035 | **Chosen.** Closest to the style frames' rock: big chunks, a few flat painted planes each, soft bevels. |
| Rock B, strata | 0.045 | 0.68 | 0.035 | Layered ledges read well on walls, but they turn into stripes on the ceiling's projection, and the seed left a hard ridge that reads as a cut. |
| Rock C, pillows | 0.015 | 0.79 | 0.040 | Calmest and most readable, but the round pillows look like cobbles, too close to a floor, and lose the chunky planes. |
| **Floor A, slabs and grit** | 0.159 | 0.48 | 0.032 | **Chosen.** Matches the slab floors in the frames; the grit stays in the cracks, so the slabs read as big calm shapes. |
| Floor B, cobbles | 0.202 | 0.41 | 0.032 | Busier: more than three times the cells, so it reads as a street, not a cave. |
| Floor C, bedrock | 0.309 | 0.59 | 0.029 | Grit spreads across the open floor and turns into the fine noise rule 1 warns about; the lowest contrast at split-screen size. |

"Fine noise" is the share of the base color's lightness variance at wavelengths under 8 cm; "shapes over 25 cm" is the share above 25 cm; "split-screen contrast" is the standard deviation of lightness after blurring away everything under 25 cm, roughly what survives at half-screen distance. The floor has more fine detail than the rock by design, since grit is in its brief, so it's compared within its own set.

## Checks

`validate_tileables.py` writes `T_CaveRock.validation.json` and `T_CaveFloor.validation.json`. For every map it records the size (all 2048 × 2048), PNG mode, byte size, SHA-256, channel ranges, and a tiling check:

- **Tiling:** the mean jump across the wrap (last column to first, last row to first) divided by the mean of the ordinary pixel steps right beside it. 1.0 is perfect; the limit is 1.25. Every map scores between 0.91 and 1.05 on both axes. The same check on a crop of each texture, which doesn't wrap, scores between 11 and 198, which shows the check can fail.
- **Normal convention:** the normal map's red and green correlate +0.92 or better with the slopes of the height map in the DirectX sense (green = surface facing down the image), so it's DirectX, Unreal's convention. Don't flip the green channel on import.
- **Reproducible:** rerunning `make_cave_surfaces.py` gives byte-identical PNGs.

## Using them in Unreal

Import into `Content/Hazards/Art/` (for example `Content/Hazards/Art/Cave/`), with the settings in the files table, then make two instances of `/Game/Shared/Style/M_Stylized`. Suggested starting values:

| Parameter | `MI_CaveRock` (walls and ceiling) | `MI_CaveFloor` |
| --- | --- | --- |
| `UseWorldAligned` | on | on |
| `BaseColorTexture` | `T_CaveRock_BC` | `T_CaveFloor_BC` |
| `MaskTexture` | `T_CaveRock_ORM` | `T_CaveFloor_ORM` |
| `WorldTileSize` | 400 (one tile per 4 m, 512 px/m) | 300 (one tile per 3 m, 683 px/m) |
| `WorldBlendSharpness` | 6 | 8 |
| `Tint` | white | white |
| `GradientStrength` | 0.3 | 0.2 |
| `EdgeStrength` / `CavityStrength` | 0.2 / 0.5 | 0.15 / 0.4 |
| `RoughnessMultiplier` | 1.0 | 1.0 |
| `MetallicMultiplier` / `MetallicOffset` | 0 / 0 | 0 / 0 |

- **The ORM's red channel is tuned to `M_Stylized`'s thresholds**, not plain AO: flat faces sit near 0.5, between `CavityThreshold` (0.4) and `EdgeThreshold` (0.6), creases fall below 0.4 and outer edges rise above 0.6. A plain AO map (flat = 1.0) would put the amber edge color over every flat face. The plain AO is in `_AO` if someone needs it.
- **`M_Stylized` has no normal-map input**, so the `_N` maps don't do anything yet. The base color carries the facet shading on its own. See "Open questions" below.
- **Orientation:** world-aligned UVs run with world +Z, so on walls the top of the image ends up at the bottom. Nothing in these textures has an up, so it doesn't matter.
- **Repetition:** the rock repeats every 4 m and the floor every 3 m. Break up long walls with a second instance at a different `WorldTileSize` (350–450) or `Tint`, or with props.

## Atmosphere preset (to build in `L_Site01_HZ`)

Starting values, to tune in `L_StyleTest` against the style frames. Windows makes the final call on lighting.

**Exponential Height Fog**

| Setting | Value |
| --- | --- |
| Fog Inscattering Color (`fog_inscattering_luminance`) | `#1E2433` in the color picker's sRGB hex field (linear 0.0130, 0.0176, 0.0331) |
| Fog Density | 0.08 to start; range 0.05–0.15. Aim for the far end of a 30 m corridor to be about half fogged. |
| Fog Height Falloff | 0.25, with the actor at the cave floor's height, so the fog pools low |
| Fog Max Opacity | 0.85, so torches and crystals still punch through at distance |
| Start Distance | 300 cm, so nearby players and the HUD area stay clean in split-screen |
| Directional Inscattering | off (black); the cave has no sun except the daylight shaft |
| Volumetric Fog | off to start, for the Macs (HZ-10). If it's on: Scattering Distribution 0.2, Albedo white, Extinction Scale 1, View Distance 3000 cm, and the torch lights' Volumetric Scattering Intensity 1–2 for halos |

**Post Process Volume** (Infinite Extent, Priority 1)

| Setting | Value |
| --- | --- |
| Color Grading → Misc → Color Grading LUT | `T_CaveGrade_LUT`, intensity 1.0 (0.6–1.0) |
| Color grading wheels (Global, Shadows, Midtones, Highlights) | neutral; the LUT does the grade, so they don't double it |
| Exposure | keep `L_StyleTest`'s fixed EV100 1.3 (min = max), so the look doesn't drift as players move between lit and dark rooms |
| Bloom | Standard, Intensity 0.5, Threshold −1, so torches and crystals glow without haloing the walls |
| Vignette | 0.3 |
| Film (tonemapper) | defaults |
| Local Exposure → Shadow Contrast Scale | 0.85, if the dark rooms read too dark at half-screen (style.md rule 6) |

**The LUT** (`make_grade_lut.py`) is gentle, in display space, which is where Unreal applies it: shadows are lifted toward `#1E2433` (black maps to `#0D0F15`, blue-violet rather than black, rule 3), highlights lean slightly toward torch amber, a soft S-curve adds contrast and the mids get 10% more saturation. Grey stays in order (checked), and the reserved colors keep their meaning: the validation JSON lists each palette color before and after. The preview shows it on style frame 02:

![LUT on style frame 02](previews/T_CaveGrade_LUT_preview.png)

Set the LUT's Texture Group to `ColorLookupTable` on import, which turns off mips and compression. If the grade looks stronger or weaker in the editor than in the preview, check its sRGB setting against that preview.

## Reproduce

From the repo root, with Python 3.9+ and numpy, scipy and Pillow:

```sh
# The chosen textures, 2048 px, into this folder (about 30 s)
python3 -I SourceArt/HZ/HZ-A1/make_cave_surfaces.py
# Checks, validation JSON and 3x3 previews
python3 -I SourceArt/HZ/HZ-A1/validate_tileables.py
# The LUT, its check and its preview
python3 -I SourceArt/HZ/HZ-A1/make_grade_lut.py

# All six candidates, outside the repo, then their scores and contact sheets
python3 -I SourceArt/HZ/HZ-A1/make_cave_surfaces.py --candidates /tmp/HZ-A1 --size 1024
python3 -I SourceArt/HZ/HZ-A1/validate_tileables.py --candidates /tmp/HZ-A1
```

To try another candidate, change `chosen` in `SURFACES` in `make_cave_surfaces.py`. Seeds and parameters are in the `ROCK` and `FLOOR` tables there.

## Open questions

- **Normal maps.** `M_Stylized` has no normal input. Either PG adds a `NormalTexture` parameter to its world-aligned branch (a triplanar normal needs each projection's tangent swizzled to world space), or the cave goes without and the painted base color does the work, which is how the style frames read anyway.
- **The mask's red channel.** It's tuned to `M_Stylized`'s cavity and edge thresholds (flat = 0.5). PG-6 and PG-A4 used plain AO there (flat = 1.0). If PG wants one meaning for that channel, say which, and the scripts can switch.

## Known limits

- Not checked in Unreal yet: the import, the instances, the triplanar blend on the cave meshes and the fog are for the owner (steps 5–8 of #52).
- The previews' lighting is a stand-in (a warm key from the top left and a blue-violet ambient, using the normal map), not `M_Stylized`.
- Base color sits between 19% and 55% per channel, to match the palette's rock colors. If the walls read too dark under the cave lights, raise `Tint` above white or the lighting, rather than the texture.
