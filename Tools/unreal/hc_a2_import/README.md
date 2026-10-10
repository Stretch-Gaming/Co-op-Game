# HC-A2 puzzle-prop import tooling

Offline delivery for Stretch's HC lane, [issue #19](https://github.com/Stretch-Gaming/Co-op-Game/issues/19), using the existing sources from [merged PR #66](https://github.com/Stretch-Gaming/Co-op-Game/pull/66). No source regeneration, Unreal imports, actor placement or in-game checks were performed.

## Files and authority

- `manifest.json`: ten FBX paths, raw-byte SHA-256 hashes/sizes, complete validation JSON snapshots and hashes, direct FBX inspection, material slots, Nanite choices, collision plans and assembly contracts.
- `import_hc_a2.py`: read-only by default; asset creation requires `--execute` and an exact absolute `--project-file`.
- `source_audit.py`: standard-library binary FBX reader and fail-closed manifest checks.
- `validate_offline.py`, `test_safety.py`: offline acceptance gate and refusal tests.
- `evidence/`: recorded default dry run, test results and source/LFS/syntax/isolation evidence.

All proposed writes are the ten meshes directly under `/Game/Puzzles/Art/HCA2_Props/` and three uniquely named material instances in its `Materials/` child. The shared parent `/Game/Shared/Style/M_Stylized` is read-only. The tool does not create actors, Blueprints, maps, textures, plugins or project settings.

Read `AGENTS.md`, `docs/assets.md`, `docs/art/style.md` and `docs/mcp.md` before the later editor pass. PG-A0's import presets are still an unfilled section in `docs/assets.md`. These are explicit settings derived from the supplied files and PR #66; they still need editor verification.

## Offline use

From the checkout containing this tooling, with Python 3.11+:

```powershell
python -B Tools/unreal/hc_a2_import/import_hc_a2.py
python -B Tools/unreal/hc_a2_import/validate_offline.py
```

Both commands default to no writes. To refresh reports **inside this tooling folder only**, run:

```powershell
python -B Tools/unreal/hc_a2_import/validate_offline.py --write-evidence
```

The tools require hydrated FBX files and the read-only parent material. Existing LFS objects may be hydrated with Git LFS in the chosen checkout; this does not regenerate them. The gate compares all ten binary file hashes and sizes against their committed LFS pointers, checks metadata, parses triangulated geometry, slot assignments, finite UVs/normals, base-centered bounds and the FBX scene/node settings. JSON/text hashes use UTF-8 with LF newlines to follow Git's Mac/Windows normalization; FBX and material hashes use raw bytes.

The default dry run reports offline editor checks as **not run**. It cannot inspect the live asset registry or evaluate shaders, collision, lighting or replication.

## Later opt-in editor use

This is a separate HC editor pass, outside this offline delivery. Save unrelated work first, stop PIE, and open **the same checkout's** `CoopGame.uproject` in Unreal **5.8.3**. Do not run this copy against a different open checkout. PythonScriptPlugin is already enabled in the inspected project; this tooling never changes plugin settings. Hydrate any existing shared style dependencies before loading the parent.

In the editor's Python console:

```python
import sys
from pathlib import Path
import unreal
project_file = Path(unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.get_project_file_path())).resolve()
sys.path.insert(0, str(project_file.parent / "Tools/unreal/hc_a2_import"))
import import_hc_a2
import_hc_a2.run([])  # read-only: project/version, parent/Tint and destination registry checks
```

Review the printed plan and empty conflicts. Explicit asset creation is a separate call:

```python
import_hc_a2.run(["--execute", "--project-file", str(project_file)])
```

Execution verifies the exact project path, Blueprint-only project association, engine patch version, pinned source and parent hashes, opaque parent material, Tint parameter and required editor APIs. It prepares import options before any creation and refuses any planned package already on disk or registered in the editor. It rechecks each destination immediately before creation. A junction/symlink resolving outside the target folder is rejected.

There is **no overwrite, skip-existing, force or reimport flag**. A repeat execution after a successful run refuses the entire batch before creation; it does not retint, reset collision or replace a reviewed asset. An editor dry run also reports/refuses occupied destinations. Later intentional reimports must be performed through editor APIs in a separately reviewed HC pass, preserving materials, assemblies and reviewed collision.

Execution is **not atomic**. A failed import/check/save can leave partial unsaved assets in memory or saved packages. It reports failure without deleting or rolling back assets. Inspect the log and only the named HCA2_Props packages before deciding whether to finish or clean up through editor APIs. No automatic retries. Never edit, remove or fabricate .uasset/.umap bytes on disk.

## Import and material settings

Use the legacy `FbxFactory` explicitly, with `AssetImportTask`, to keep `FbxImportUI` settings effective without changing Interchange or project settings. Import static meshes only, combine the single render geometry, disable material/texture/animation/LOD imports, disable automatic collision and generated lightmap UVs, and import the exported normals/tangents to preserve PR #66's flat-face shading fix.

Import scale is **1.0**, translation/rotation zero, scene and scene-unit conversion enabled, `force_front_x_axis=False`, `transform_vertex_to_absolute=True`, `bake_pivot_in_vertex=False`. The supplied FBX declares centimeters/Z-up but stores meter-sized vertex coordinates under a 100x node scale and approximately 180-degree Z rotation. Bake that node transform once; never multiply import scale by 100. The importer checks imported bounds/pivot to 0.5 cm and the one source UV channel before saving. Facing still needs a visual +X check.

Read-only binary inspection of M_Stylized found `BLEND_Opaque`, `Tint`, gradient, edge, roughness and world-aligned/mask parameter names. The importer confirms the parent and Tint through editor APIs before execution. Proposed instances:

| Imported slot | Instance inside HCA2_Props/Materials | sRGB tint |
| --- | --- | --- |
| M_Stone | MI_HCA2_Stone | #7A6E68 |
| M_StoneCarving | MI_HCA2_StoneCarving | #4A4652 |
| M_Rope | MI_HCA2_Rope | #C9A66B |

Tint values are converted from sRGB to linear for Unreal LinearColor. Gradient, edge, roughness, mask and world-aligned settings inherit the shared master's defaults. Slot assignment uses the imported slot names/order and aborts if these differ. No material is substituted for M_Stylized and the parent is never modified or saved.

No textures were supplied for these props; use the procedural painted material. Any later large-prop textures follow the documented **2K**, sRGB base color, DirectX Normalmap and packed linear R=AO/G=roughness/B=metallic rules. The shared curvature bake remains a PG-A0 follow-up.

Nanite is enabled only for the opaque **altar, both statues, gate frame and gate leaf**, each above 2,000 source triangles. It remains disabled on the plate base and all four tops. Settings are applied through StaticMeshEditorSubsystem, including the build/apply step. If a later material becomes translucent, disable Nanite and revalidate; do not reuse this opaque plan unchanged. Check fallback appearance on the other platform, including older Macs where available.

## Assembly instructions for the later HC pass

Use component-relative offsets with actor/component scale **(1,1,1)** and base-centered pivots. Do not resize or recenter the supplied art to force a fit.

| Assembly | Required placement |
| --- | --- |
| Plate | Base at actor origin. One selected symbol top at **(0,0,+9 cm)** raised, **(0,0,+2 cm)** pressed. Travel **7 cm down**. All four symbol tops remain available; mapping is an owner decision. |
| Gate | Frame at actor origin. Leaf **(0,0,0)** closed, **(0,0,+400 cm)** open. Travel **400 cm up**; retain the full travel. |
| Altar | Front faces +X. Relic base at **(0,0,97 cm)** in the 40 cm diameter, 3 cm deep socket. |
| Statues | Preserve both 1.8 m SM_Statue and 1.1 m SM_Statue_Small. Front faces +X. Selection, carry attachment and camera clearance remain owner decisions. |

The gate's **400 cm Y opening × 400 cm height is its passage, not its full mesh bounds**. The actual frame is **156 × 708.8224 × 511.2001 cm**, including rubble; the leaf is **30.4 × 430 × 450 cm**. Passage runs along X; the leaf slot is centered at X=0 and 34 cm wide. The leaf top reaches **850 cm** when open. HZ must provide enough enclosing rock above the lintel; flag inadequate cave clearance for coordination. Do not shorten travel, redesign the gate or silently hide the leaf in this tooling.

Later assembly/greybox replacement belongs in HC-owned Blueprints/test map and `L_Site01_HC`, with that sublevel current. Check both travel extremes and intermediate positions. Never place these into a persistent map during this pass. Do not create saved actor references across lanes.

## Collision and later acceptance

The importer adds **one fitted simple box** to the plate base, each top and the gate leaf. These six boxes still require visual/physics verification. It sets simple-and-complex query behavior, never complex-as-simple; use simple collision for gameplay/physics.

The four compound props are intentionally imported with **zero simple shapes**, marked pending, because automatic whole-mesh hulls would lose the spaces that must stay clear. They are **not ready for gameplay placement** until this editor work is complete:

| Prop | Manual simple collision plan |
| --- | --- |
| Each statue | Plinth box plus owl capsule or box, fitted independently at the supplied size. Check rope, carrying and seating on the 1.8 m top. |
| Altar | Two boxes for pedestal and capstone. Check socket/relic interaction at Z=97; fit the capstone collision so it does not obstruct the intended interaction. |
| Gate frame | Separate post/lintel boxes with the 4×4 m passage clear. Preserve the 34 cm slot; split front/back hulls where the moving leaf needs that slot clear. No whole-frame box or convex hull across the opening. |

Author these shapes in the Static Mesh Editor/editor APIs; never modify the FBX, regenerate art or add C++ to solve collision. Inspect simple-collision overlays, test a pawn through the open gate along X, and verify the closed leaf blocks correctly. Check plate standing/stepping and both top heights, statue seating/carry clearance and the altar socket. Movement and puzzle state remain server-owned gameplay work, outside this folder.

Remaining checks, all **pending**:

- Inspect materials/shaders and flat faces, scale against the 1.8 m character, +X facing, UVs, each slot and Nanite/fallbacks.
- In `L_StyleTest`, lock the shared map before adding anything and coordinate its owner; save only authorized packages. Compare against example props under the cave lights. Use HC's test map for HC-only assembly work.
- Under warm torch pools, cold crystal fill and blue-violet shadows, check all four symbols at half-screen resolution, matte painted stone, rope visibility and reserved colors. Do not tint decorative props relic gold/jade, ghost white or trap red.
- Check both statue variants in first/third person and split-screen before the owner selects a carry variant. Verify the gate's rock envelope up to Z=850 cm with HZ.
- Finish HC test-map checks, then replace greyboxes in the HC sublevel. Compile affected Blueprints; check Output Log and Accessed None. Run Play As Client with 2, 3 and 4 players and a second local split-screen player for relevant view/input work.
- Save only HC-owned/locked assets; verify Git/LFS scope before the later asset push. Leave issue #19's import and placement steps unchecked until those gates actually pass.

The sources are team-authored scripted Blender work, with public redistribution/no-credit status recorded on #19 and PR #66. No new third-party assets or credits are introduced.
