# PG-A5: bats and mice

| File | Triangles | Size, X × Y × Z (cm) | Imported as |
| --- | ---: | --- | --- |
| `SM_Bat_Body.fbx` | 1,120 | 20 × 9 × 11 | `SM_Bat_Body`, the flying bat without wings |
| `SM_Bat_Wing.fbx` | 276 | 15 × 24 × 4 | `SM_Bat_Wing`, one wing; `BP_CaveBat` mirrors it for the other side |
| `SM_Bat_Hanging.fbx` | 1,636 | 11 × 10 × 24 | `SM_Bat_Hanging`, a bat asleep upside down |
| `SM_Mouse.fbx` | 2,410 | 22 × 11 × 8 | `SM_Mouse`, nose to tail tip |

All four face +X, with the pivot at the base center, as `cleanup_export.py` sets it. None has collision or Nanite: nothing touches them, and they're small. Each color is its own material slot (`Bat_Fur`, `Bat_Membrane`, `Mouse_Fur`, `Mouse_Belly`, `Critter_Skin`, `Critter_Eye`, `Critter_Fang`), which the import fills with the matching `MI_` instance of `/Game/Shared/Style/M_Stylized`. There are no textures; each instance sets `Tint`.

They're larger than life so they read in a split view: a bat is about 55 cm across the wings, and a mouse is 22 cm from nose to tail tip. The colors are muted browns and greys, away from the reserved relic, ghost and trap colors in [docs/art/style.md](../../../docs/art/style.md#palette). The fangs are a warm off-white, not the ghost's cold white.

- **Wing hinge:** in `SM_Bat_Wing`'s mesh space in Unreal, the shoulder hinge is at (1.94, 11.66, 0.32) cm, and the wing spreads toward −Y from it. `metrics.json` gives the same point in Blender's axes, where Y is flipped. `BP_CaveBat` puts each wing under a hinge component, offset by that amount, at (0, ±2.8, 1.2) cm on the bat.
- **Body:** the body's Blender origin is 1.52 cm forward of and 4.08 cm below the mesh pivot. `BP_CaveBat` offsets the `Body` component by that, so the bat's center is on its orbit.
- **Hanging bat:** the pivot is under the ears. Place it 23.85 cm below the rock or beam, less a centimeter or two so the toes sink in.

`build_critters.py` rebuilds everything here:

    blender -b --factory-startup --python SourceArt/PG/PG-A5/build_critters.py -- SourceArt/PG/PG-A5

It writes a preview sheet for each mesh, `metrics.json`, and the FBXs through [Tools/blender/cleanup_export.py](../../../Tools/blender/cleanup_export.py). The meshes were modelled and checked in a live Blender through Blender MCP with the same script: exec it with `PG_A5_LIVE = True` set, so it clears the scene instead of loading factory settings, which would unload the MCP add-on.

Made in Blender 5.2.2 LTS with original Python modelling. It's our own work: no third-party content or generators, public redistribution allowed, and no credit needed.

The import, the Blueprints and the placement in `L_Site01_PG` are in [Tools/unreal/pg_a5_critters](../../../Tools/unreal/pg_a5_critters/README.md).
