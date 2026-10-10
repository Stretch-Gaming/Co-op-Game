# HC-A1 relic import and validation (#18)

All four supplied relics are imported in UE 5.8.3 under `/Game/Puzzles/Art/HCA1_Relics/`, with five uniquely named instances of the existing read-only `M_Stylized`, Nanite, source normals and simple collision. `Content/Puzzles/Test/L_HCA1_AssetTest.umap` provides an HC inspection scene with a 1.8 m template-character reference. Sources were not regenerated, resized or redesigned.

**Still pending:** gameplay placement/replacement, pickup/carry acceptance, rendered split-screen review and Mac/fallback review. Current main has neither `BP_Relic` (#8) nor `BP_KeyRelic` (#10), and `L_Site01_HC` is empty. This delivery creates no stand-in gameplay logic and does not claim #18's in-place gate. PR #70 remains unmerged.

## Delivered evidence

- `manifest.json`: exact source paths, byte sizes and SHA-256/LFS fingerprints; complete source validation reports; independent binary FBX topology, transforms, UVs, normals, materials and nominal/source dimension distinction.
- `material_bindings.reviewed.json`, `engine_preflight.json`, `placement_preflight.json`: actual UE 5.8.3 parent parameters, graph response and source-mask inspection. The original example remains deliberately unverified.
- `engine_import.json`: successful creation of four meshes and five instances. Its heart-collision-pending flag describes that initial stage; `engine_asset_validation.json` records the finished collision and saved asset checks.
- `engine_asset_validation.json`: source dimensions, ordered slots, material values, UVs, original Nanite triangle counts, reduced render-fallback counts and simple collision.
- `engine_render_validation.json`, `renders/`: Windows renders in a transient `L_StyleTest` session, with only the owned HC test level saved. Shared map/material bytes are unchanged. The primary agent visually reviewed all five final images.
- `engine_smoke_validation.json`: stone/handle collision probes and 2-, 3- and 4-client asset-loading checks in `L_Site01`, with the HC inspection level mounted only in memory. This proves asset loading, not collection/carrying behavior.
- `evidence.json`, `dry_run.txt`: reproducible offline safety checks and fingerprints. `delivery_state.json` identifies completed and pending gates.

Source and license were recorded on [#18](https://github.com/Stretch-Gaming/Co-op-Game/issues/18) and [merged #65](https://github.com/Stretch-Gaming/Co-op-Game/pull/65): team-authored scripted Blender outputs, own work, no attribution required. No new third-party assets were downloaded. Existing project template assets are referenced only.

## Source dimensions and preserved choices

| Mesh | Reported X x Y x Z (cm) | Original/Nanite triangles | Ordered material slots |
| --- | --- | --- | --- |
| `SM_Relic_GoldIdol` | 22.1418 x 22.7571 x 25 | 9,406 | Gold, idol jade glow |
| `SM_Relic_JadeMask` | 9.8168 x 17.7345 x 22 | 8,224 | Jade, gold |
| `SM_Relic_GemScarab` | 18 x 16.3004 x 7.0937 | 8,148 | Gold, jade |
| `SM_KeyRelic_StoneHeart` | 39.2349 x 74.0457 x 62 | 9,866 | Stone, gold, jade, tan rope |

The nominal brief is 20-30 cm for small relics and about 60 cm for the key relic. These source-reported dimensions are separately recorded from PR #65's rounded design dimensions. Keep the 18 cm scarab, 62 cm heart, mask plinth, heart wraps/loops, tan rope and idol gem emission. The 74.0457 cm heart width includes its loops; the actual stone-only vertex bounds measured by this tooling differ from PR #65's approximate 55 cm stone-width note.

FBX raw vertices are meter-sized, with model scale 100 and `UnitScaleFactor=1` (cm). Scene conversion and `transform_vertex_to_absolute=True` apply that supplied transform. Import scale remains 1.0, with no added rotation, decimation, generated UVs or pivot bake. Engine checks confirmed +X-facing geometry and base-center pivots; Nanite triangle counts exactly match the sources. Render-fallback meshes are simplified and require Mac review.

## Materials and collision

All instances live in the flat relic folder: `MI_HCA1_RelicGold`, `MI_HCA1_RelicJade`, `MI_HCA1_IdolJadeGlow`, `MI_HCA1_HeartStone`, `MI_HCA1_HeartRopeTan`. Gold uses metallic 1/roughness 0.3; jade uses 0/0.25, stone 0/0.85, rope 0/0.9. Palette tints are converted from sRGB to linear. The shared mask is non-sRGB RGBA `(128,255,0,255)`, so its green channel is 1 and the roughness multiplier directly produces the intended roughness.

The master has no `EmissiveColor` parameter. Its existing emission path is `Fresnel(RimExponent) * RimColor * RimStrength`. Setting exponent 0 yields constant Fresnel 1 per the installed engine implementation; idol jade uses jade `RimColor` and `RimStrength=0.6`. Thus its source glow is preserved without a new or modified parent. UE 5.8.3's scalar/vector setters return false even when applying changes; the importer verifies actual parameter readback instead.

Small relics each have one box. The heart has a stone-fitted box centered at `(0,0,31)` cm, approximately `34.5264 x 60.5488 x 62.4` cm, with a 0.2 cm margin. Symmetric XY bounds accommodate FBX axis reflections while excluding outer handles. Simple-as-complex queries use that same box. Persisted-asset collision probes hit the stone center and miss both outer handles at Y +/-35 cm. Source render geometry stays intact.

No texture images were supplied or generated. The Smart UV layer and constant PBR intent are preserved. Any future textures must follow the existing 1K budget, sRGB base color, DirectX/Normalmap normals and non-sRGB ORM conventions. `docs/assets.md` still marks PG-A0's import presets as unfinished; this tooling uses explicit source-derived settings verified in 5.8.3.

## Safe offline use

From this checkout in PowerShell:

```powershell
$hcPython = 'C:\Users\Stretch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $hcPython -B Tools/unreal/hc_a1_import/import_relics.py
& $hcPython -B Tools/unreal/hc_a1_import/validate_offline.py
```

The default importer is read-only and never loads Unreal, creates directories or saves assets. It verifies the project, sources, fingerprints, metadata and isolated destinations. Bytecode caching is disabled. `--write-evidence` on the offline validator explicitly refreshes its evidence files. Git LFS source hashes and sizes are compared to committed pointer OIDs, and all four FBXs must be hydrated.

## Exact future execution steps

The assets already exist in this branch: **do not rerun creation here**. Execution/preflight deliberately refuses any existing asset, redirector or disk content in HCA1_Relics. There is no overwrite, reuse, reimport or force option, so manual collision/material work is preserved.

For a fresh, separately authorized checkout, hydrate existing content/sources with Git LFS, verify UE 5.8.3 and PythonScriptPlugin, and open that exact checkout's `CoopGame.uproject`. Do not change plugins/settings. Stop PIE and keep other chats' editors separate. Replace the path below with that checkout's absolute path; the tooling and active editor must be in the same checkout.

```python
py import sys; from pathlib import Path; hc_root=Path(r'C:/Users/Stretch/.codex/worktrees/hc-a1-import-tools/Co op Game'); sys.dont_write_bytecode=True; sys.path.insert(0,str(hc_root/'Tools/unreal/hc_a1_import')); import import_relics; import_relics.main(['--project-root',str(hc_root),'--editor-check','--material-bindings',str(hc_root/'Tools/unreal/hc_a1_import/material_bindings.reviewed.json')])
```

Only after preflight succeeds, explicitly execute in the full editor:

```python
py import_relics.main(['--project-root',str(hc_root),'--execute','--material-bindings',str(hc_root/'Tools/unreal/hc_a1_import/material_bindings.reviewed.json')])
```

The script uses `AssetImportTask`, a pinned `FbxFactory/FbxImportUI`, material APIs and `StaticMeshEditorSubsystem`; it saves only newly created isolated assets. A PythonScript commandlet lacks that subsystem and is refused before creation. Full-editor automation is also available through `-ExecutePythonScript="<forward/slash/path>/run_editor.py" -HCA1Execute`; absent `-HCA1Execute`, that wrapper performs only editor preflight. Use forward slashes because Unreal's script parser interprets backslash escapes.

Creation leaves the heart collision unfinished. For newly imported, untouched assets only, run `finish_assets.py` with a full-editor `-ExecutePythonScript` session and explicit `-HCA1FinishAssets`; it refuses an existing heart collider. It builds the source-fitted box, saves only the heart and verifies all assets. Check the success JSON/marker and Output Log, not just process exit code: full-editor Python can report script errors while returning process exit 0.

`build_preview.py -HCA1BuildPreview` creates only the dedicated HC test map and captures renders. `-HCA1RepairPreview` explicitly rebuilds this script's tagged fixtures in that map, preserving untagged actors. `editor_smoke.py -HCA1Smoke` and `smoke_rpc.py` coordinate isolated client-load checks on localhost port 8002 and restore Play settings. The RPC helper verifies the live editor's project marker before changing any Play settings. Follow repository locks/coordination before mounting levels in shared/persistent test worlds; never save those worlds as part of asset inspection.

An execution failure can leave partial or unsaved isolated assets. There is no automatic rollback/deletion. Inspect the editor and Output Log before a retry; cleanup must use editor APIs/UI and check references. Never edit or remove `.uasset` files on disk. No script places gameplay actors or edits other chats' files.

## Remaining integration gate

Assign the three small meshes to HC-2's `BP_Relic` variants after #8 supplies that system. Assign the heart to HC-4's physics-root `BP_KeyRelic` after #10 supplies carrying. Preserve MinPlayers/scaling, server authority and owning-player input/HUD; keep placements in `L_Site01_HC`. This branch does not implement those separate epics or modify Core, persistent maps or the empty gameplay sublevel.

Then run actual client collection/carry/drop, late join, reset and 2/3/4-player checks, plus host split-screen visibility/input and Mac/fallback/style review. Check source reimport paths, compile any changed Blueprints and scan Output Log. Only then replace greybox and tick #18's in-place acceptance. The current client smoke checks establish static-art loading only. No pickup, carrying, rendered split-screen or Mac checks are claimed.
