# HC-A2 puzzle props

Stretch's HC lane delivery for [#19](https://github.com/Stretch-Gaming/Co-op-Game/issues/19), from the existing team-authored sources in merged PR #66. The original FBX files and validation metadata are unchanged.

## Delivered

- Ten imported meshes and three uniquely named M_Stylized instances under `/Game/Puzzles/Art/HCA2_Props/`.
- Five Blueprint art assemblies in `HCA2_Props/Assemblies/`: diamond/circle/triangle/cross plates and the chamber gate.
- `/Game/Puzzles/Test/L_HCA2_Props`, created through the editor's level-template API from L_StyleTest. Its copied lighting/reference assets and HC-owned test fixtures support comparison without modifying the shared map.
- Eleven art-only placements in `L_Site01_HC`: four symbol plates, three 1.8 m statues in the documented alcoves, the altar, and G1/G2/G3. The starting main branch had no HC puzzle greyboxes or gameplay actors to replace.
- Both statue variants remain available. Alcove placement uses #19's 1.8 m specification; the 1.1 m version appears beside it in the test map. No carry variant is silently selected.

These are art assemblies, with cosmetic `SetPressedVisual` and `SetOpenVisual` functions. Gameplay authority, carrying, puzzle counts and round completion belong to HC-4/5/6. The future gameplay owner must drive the cosmetic functions from server-owned replicated state. There are no new input, HUD, GameMode or round-state changes in this delivery.

## Importer and repeat runs

`manifest.json` records source paths, raw SHA-256/sizes, validation JSON snapshots/hashes, direct FBX metadata, material slots, destinations, collision plans and assembly contracts. Binary hashes use raw bytes; text hashes normalize UTF-8/LF to follow the repository's Windows/Mac policy.

From the checkout containing this tool:

```powershell
python -B Tools/unreal/hc_a2_import/import_hc_a2.py
python -B Tools/unreal/hc_a2_import/validate_offline.py
```

Both default to read-only operation. A repeat dry run reports occupied destinations and `execution_ready: false`. It never changes existing assets. `validate_offline.py --write-evidence` explicitly refreshes reports inside this tooling directory.

Actual asset creation requires the same checkout open in Unreal **5.8.3** and an explicit call:

```python
import sys
from pathlib import Path
import unreal
project_file = Path(unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.get_project_file_path())).resolve()
sys.path.insert(0, str(project_file.parent / "Tools/unreal/hc_a2_import"))
import import_hc_a2
import_hc_a2.run([])
import_hc_a2.run(["--execute", "--project-file", str(project_file)])
```

Execution verifies the exact project, engine patch version, Blueprint-only association, source/parent hashes, opaque M_Stylized/Tint and destination isolation. All thirteen destinations must be unoccupied before creation. There is no force, overwrite, skip-existing or reimport flag. A second execution refuses the whole batch. Partial failures are not atomic; inspect and repair through editor APIs, never .uasset/.umap bytes on disk.

The `editor_*.py` files are bounded authoring/verification scripts for a full editor. Running an authoring script is an explicit write action; scripts refuse unexpected existing assets or collision. The importer is the safe default entry point. Do not use editor-only StaticMeshEditorSubsystem authoring through a Python commandlet; live testing confirmed that subsystem is unavailable there.

## Validated settings

The legacy FbxFactory keeps the explicit FbxImportUI settings effective without changing project/Interchange settings. Import scale is **1.0**, translation/rotation zero, scene/unit conversion enabled, `force_front_x_axis=False`, `transform_vertex_to_absolute=True` and `bake_pivot_in_vertex=False`. The FBX stores meter-sized numeric vertices under its supplied 100x node scale while declaring cm; bake that node transform once and do not add another 100x scale.

Material/texture/animation/LOD imports and automatic collision are disabled. The exported normals are preserved; Unreal recomputes tangents with MikkTSpace, resolving the nearly-zero imported-tangent issue. No source shading or geometry is regenerated.

M_Stylized is read-only. Its Tint override is verified by reading the actual value and override flag because UE 5.8.3's vector setter returns false even after setting successfully. Gradient, roughness, edge, mask and world-aligned values inherit the master.

| Imported slot | Instance in HCA2_Props/Materials | sRGB tint |
| --- | --- | --- |
| M_Stone | MI_HCA2_Stone | #7A6E68 |
| M_StoneCarving | MI_HCA2_StoneCarving | #4A4652 |
| M_Rope | MI_HCA2_Rope | #C9A66B |

Tint is converted from sRGB to linear. No prop textures were supplied; the procedural painted material is used. Later large-prop textures must follow the documented 2K, sRGB base-color, DirectX Normalmap and linear packed R=AO/G=roughness/B=metallic rules.

Nanite is enabled for the opaque altar, both statues, frame and leaf (source triangles above 2,000), and disabled for all plate parts. Fallback uses **100% triangles and zero relative error**: automatic simplification expanded the narrow frame's bounds, so the full authored geometry is retained for fit and non-Nanite systems. FBX import first keeps Nanite disabled so fit checks use authored geometry; the final build enables the planned five meshes with the explicit full-fidelity fallback. Source bounds are rechecked after that build.

PG-A0's preset section in docs/assets.md is still unfilled. These explicit settings have now been exercised in the Windows 5.8.3 editor; this does not claim that a Mac preset or Mac appearance check passed.

## Assemblies

Use actor/component scale (1,1,1), base-centered pivots and component-relative transforms.

| Assembly | Preserved contract |
| --- | --- |
| Each plate | Base at origin; top raised **Z +9 cm**, pressed **Z +2 cm**, travel **7 cm down**. |
| Gate | Frame at origin; leaf closed **Z 0**, open **Z +400 cm**, travel **400 cm up**. |
| Altar | Front +X; relic base **(0,0,97 cm)** in the 40 cm diameter, 3 cm deep socket. |
| Statues | 1.8 m and 1.1 m variants retained, fronts +X. |

The gate's **400 cm Y opening × 400 cm height** is its passage. Full frame bounds are **156 × 708.8224 × 511.2001 cm**, including rubble; the leaf is **30.4 × 430 × 450 cm**. Passage is along X; the centered X slot is 34 cm wide. Open leaf top is **Z 850 cm**. Never resize/recenter the art or shorten travel to force a fit.

Symbol placement is explicit: diamond (32,-8 m), circle (32,+8 m), triangle (48,-8 m), cross (48,+8 m). Gates remain at the documented 25/55/115 m X positions and the altar at X108 m. All new main-map actors belong to L_Site01_HC, with no cross-sublevel actor references.

## Simple collision

All ten meshes now have simple collision, with simple-and-complex query behavior, never complex-as-simple:

- Plate base, each top and leaf: one fitted box.
- Each statue: separately scaled plinth and owl boxes.
- Altar: pedestal and capstone boxes; capstone collision stops at Z97 so the socket base remains accessible.
- Frame: eight split post/core/lintel boxes. The 4×4 m passage and 34 cm X slot stay clear; the cores start at Y ±218 cm, beyond the leaf ends at ±215 cm.

Live checks verified all four 7 cm surface-height changes, closed-gate blocking/open-gate clearance with a pawn-size sweep, and the altar contact surface at Z97. The precise box ranges are in `evidence/compound_collision.json`.

## Remaining completion requirements

Read `VALIDATION.md` and the current captured evidence. Do not treat historical offline results as live gameplay proof.

- Gate concealment needs the HZ owner's enclosing-rock review/work up to Z850. The current cave probes found no rock across the sampled upper-leaf space. This delivery preserves the leaf and travel and does not edit HZ's cave or hide it to conceal the problem.
- Other-platform appearance/fallback checks remain necessary under docs/assets.md. A Windows run cannot establish a Mac result.
- Carry/view choice and the eventual pressure-plate/statue/altar/gate gameplay hookup remain the consuming HC phases. There were no existing HC gameplay greyboxes to swap.

Only tick or close #19 when the applicable art acceptance gates have actually passed. Do not claim missing gameplay or external-platform checks passed. Shared materials, shared maps, core assets, source art, project settings and the original dirty checkout are preserved.

Upstream HC-1 integration: the final rebase retained its three test interactables in L_Site01_HC, then added the eleven HC-A2 actors through the editor. See evidence/upstream_integration.json. No older binary map replaced the upstream map.
