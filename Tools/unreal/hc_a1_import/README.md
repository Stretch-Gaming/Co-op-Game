# HC-A1 relic import tooling (#18)

This delivery prepares Stretch's HC lane for a later Unreal 5.8.3 editor import. It does not import assets, launch/control Unreal, replace greybox, or pass in-place acceptance. The only authored files are in `Tools/unreal/hc_a1_import/`.

Context read: `AGENTS.md`, `docs/assets.md`, `docs/art/style.md`, `docs/mcp.md`, [issue #18 and all three comments](https://github.com/Stretch-Gaming/Co-op-Game/issues/18), and [merged PR #65](https://github.com/Stretch-Gaming/Co-op-Game/pull/65). PR #65 merged at `f2d0800b0c552b9da8819d60f4fc2a35fb3a1afb`. The checkout started at fetched `origin/main` `b9ed193fb35458f1c35588362d7a629949313362`. Source license/provenance is already recorded on #18: team-authored Blender outputs, own work, no attribution required. No source was regenerated or redesigned. LFS hydration restores the existing four FBX objects without changing their tracked contents.

## Files

- `manifest.json`: exact repository-relative source paths, byte sizes and SHA-256 hashes for FBXs, validation reports and generating scripts; shared HC-A1 helper fingerprint; full source reports and independent binary FBX inspection; nominal dimensions, slots, preserved choices, materials, collision plans and destinations.
- `import_relics.py`: default read-only dry run; opt-in editor preflight and execution.
- `fbx_inspect.py`: standard-library binary FBX inspection (one reviewed mesh per file; not a general FBX SDK).
- `material_bindings.example.json`: **unverified proposal**, deliberately disabled for execution. Five uniquely named material instances inside the relic folder.
- `validate_offline.py`, `evidence.json`, `dry_run.txt`: reproducible offline checks and captured results. Evidence hashes exclude the evidence file and dry-run capture themselves.

## Source dimensions and geometry

| Mesh | Source report X x Y x Z (cm) | Triangles | Ordered source slots |
| --- | --- | --- | --- |
| `SM_Relic_GoldIdol` | 22.1418 x 22.7571 x 25 | 9,406 | `M_Gold`, `M_Jade` |
| `SM_Relic_JadeMask` | 9.8168 x 17.7345 x 22 | 8,224 | `M_Jade`, `M_Gold` |
| `SM_Relic_GemScarab` | 18 x 16.3004 x 7.0937 | 8,148 | `M_Gold`, `M_Jade` |
| `SM_KeyRelic_StoneHeart` | 39.2349 x 74.0457 x 62 | 9,866 | `M_Stone`, `M_Gold`, `M_Jade`, `M_Rope` |

These are the cleanup export's **reported dimensions**, independently checked against FBX raw vertex extents and model scale. The nominal issue brief is 20-30 cm for small relics and about 60 cm for the key relic. PR #65's rounded dimensions are separately recorded. Keep the scarab at 18 cm and the heart at 62 cm. The heart's 74.0457 cm width includes rope loops; PR #65 describes the stone alone as approximately 55 cm wide. That is a design note, not independently measured collision bounds.

The FBXs have `UnitScaleFactor=1` (centimeters) but meter-sized raw vertex coordinates with model `Lcl Scaling=[100,100,100]` and a roughly 180-degree Z rotation. Import scene/unit conversion and `transform_vertex_to_absolute=True` apply the supplied model transform. Additional import scale is **1.0**, with no corrective rotation. Source metadata says export forward axis `-Y`; PR #65 says the default Unreal import faces `+X`. Preserve both statements and verify actual facing/pivot in the editor. If bounds differ by more than 0.1 cm, execution stops without automatic rescaling.

Keep the seated lion and its jade chest gem, mask plinth and through-cut openings, scarab gold rim/seam and jade shell, heart runes, all three tan rope wraps and both carry loops. Preserve supplied normals with Import Normals (Unreal generates tangents). No decimation, generated UV layer, pivot bake, degenerate removal or nominal-size normalization is requested. Nanite is enabled for all four opaque meshes. Check source LOD geometry and Nanite/fallback behavior independently in the editor; offline inspection cannot confirm import fidelity.

## Materials and collision

The only parent is existing `/Game/Shared/Style/M_Stylized`, loaded read-only. The script never saves or edits the parent or existing shared instances. FBX material/texture creation is disabled. It proposes and, after verified bindings, creates only:

| Profile | Destination name (all in `/Game/Puzzles/Art/HCA1_Relics/`) | Source intent |
| --- | --- | --- |
| gold | `MI_HCA1_RelicGold` | #E8B33A, metallic 1, roughness 0.3 |
| jade | `MI_HCA1_RelicJade` | #3FA672, metallic 0, roughness 0.25 |
| idol_jade | `MI_HCA1_IdolJadeGlow` | Jade plus source emission strength 0.6 |
| stone | `MI_HCA1_HeartStone` | #7A6E68, metallic 0, roughness 0.85 |
| rope | `MI_HCA1_HeartRopeTan` | #A88457, metallic 0, roughness 0.9 |

The example converts sRGB palette colors to linear `Tint`. It proposes `RoughnessMultiplier`, `MetallicMultiplier`, `MetallicOffset` and idol `EmissiveColor`. These names and multiplier responses are **not verified material bindings**. `EmissiveColor` appearing in an asset's name table does not prove it is an exposed parameter. The editor preflight lists actual scalar/vector names and refuses unknown bindings. Review the master graph and default mask response read-only, then adjust the proposed bindings to reproduce source roughness, metallic and emission. A multiplier is not necessarily an absolute roughness value. If the master has no suitable emission parameter, stop material execution and resolve that with the owner; do not silently remove the glow or edit the shared master in this pass. Marking the review flag true is a human assertion, not automatic shader/visual validation.

The small relics receive one simple box each. Inspect the fit, including the mask plinth and scarab legs. The heart is imported with **no automatic collision**: a whole-mesh box would include its rope loops. Before use, add and fit a box around the stone only in Static Mesh Editor, excluding the loops. Approximately 39 cm depth, 55 cm stone width and 62 cm height are starting guides, not final collision dimensions. Keep simple collision for physics; do not substitute complex-as-simple. Collision and visual fit remain acceptance gates.

No texture images are supplied or created. Preserve the Smart UV layer and constant material intent. Future texture work must use 1K textures, sRGB base color, DirectX normals/Normalmap compression, and non-sRGB ORM (R=AO, G=roughness, B=metallic). Full PBR texture and curvature-bake requirements remain an owner review item; this tooling does not claim a complete textured delivery.

## Offline use now

From the isolated worktree in PowerShell (use a real installed Python 3.10+; the Windows Store alias is not a runtime):

```powershell
Set-Location -LiteralPath 'C:\Users\Stretch\.codex\worktrees\hc-a1-import-tools\Co op Game'
$hcPython = 'C:\Users\Stretch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $hcPython -B Tools/unreal/hc_a1_import/import_relics.py
& $hcPython -B Tools/unreal/hc_a1_import/validate_offline.py
```

No execution flag means no Unreal import, asset load, folder creation or save. The importer disables bytecode caching before loading its helper. `validate_offline.py --write-evidence` explicitly refreshes the two evidence files inside this folder. Validation checks hydrated FBX hashes against Git's committed LFS pointer OIDs and sizes; `git lfs ls-files -l` must show `*` for all four.

If sources are pointers in a future checkout, hydrate **only the existing FBXs**, without regeneration:

```powershell
git lfs pull --include='SourceArt/HC/HC-A1/*.fbx' --exclude=''
```

## Exact later editor steps (not run in this delivery)

1. After review/merge or in a separately authorized import checkout, hydrate its existing shared style kit and any project assets needed by the editor. Open **that checkout's** `CoopGame.uproject` in UE **5.8.3**. PythonScriptPlugin is already enabled in the descriptor; do not change project settings. Stop PIE. Save your unrelated work yourself first. Coordinate the import with the HC owner and other chats before changing content.
2. Confirm `Content/Puzzles/Art/HCA1_Relics/` and its Asset Registry namespace are empty. The importer refuses any existing assets, redirectors or disk content there. Inspect `/Game/Shared/Style/M_Stylized` read-only. Do not lock/change the master for this workflow.
3. In Unreal's bottom command console, run the following **single line**. This is read-only. It verifies the active project path and engine, lists material parameters, and constructs transient import options to check API/property availability. If using a post-merge checkout, replace `hc_root` with its exact absolute path; the script itself must live in that same checkout.

```python
py import sys; from pathlib import Path; hc_root=Path(r'C:/Users/Stretch/.codex/worktrees/hc-a1-import-tools/Co op Game'); sys.dont_write_bytecode=True; sys.path.insert(0,str(hc_root/'Tools/unreal/hc_a1_import')); import import_relics; import_relics.main(['--project-root',str(hc_root),'--editor-check'])
```

4. Copy the example into the owned tooling directory as `material_bindings.reviewed.json`. Review all five profiles against actual exposed parameters and master response. Preserve idol emission, tan rope, shiny gold and jade. Adjust names/values as needed; only after that review set `verified_in_ue_5_8_3` to `true`. No new parent materials, textures or static-switch changes are made by this importer. Keep the file for the later import's evidence.
5. Run read-only preflight with the reviewed bindings. Any refusal must be resolved before execution; a missing emissive control is a real outstanding material constraint.

```python
py import_relics.main(['--project-root',str(hc_root),'--editor-check','--material-bindings',str(hc_root/'Tools/unreal/hc_a1_import/material_bindings.reviewed.json')])
```

6. When the separate import work is authorized and preflight passes, explicitly execute:

```python
py import_relics.main(['--project-root',str(hc_root),'--execute','--material-bindings',str(hc_root/'Tools/unreal/hc_a1_import/material_bindings.reviewed.json')])
```

Execution uses `AssetTools`, `AssetImportTask`, a pinned `FbxFactory`/`FbxImportUI`, material-instance APIs and `StaticMeshEditorSubsystem`. It does not write `.uasset` bytes directly. It creates five instances and four static meshes only inside the flat isolated folder, assigns by checked imported slot names, checks imported bounds, builds Nanite and saves only assets created in that call. It never places actors, changes levels, modifies gameplay or calls Save All. The supplied source data stays unchanged.

## Repeat runs and failures

Offline dry runs are repeatable and read-only. Editor preflight is also read-only, apart from transient options and loading the parent into memory. There is no overwrite, reuse, reimport or force flag. A successful execute makes the destination nonempty, so every later execute/preflight refuses that destination. This preserves manual collision/material tuning. Changing even one source byte or metadata value fails fingerprints before engine access.

Execution is not an atomic editor transaction. An import, material binding, collision, Nanite or save error can leave partial/unsaved assets, or some already saved packages in the isolated folder. The script stops and never deletes or rolls back automatically. Inspect assets and Output Log in the editor. If a retry is needed, coordinate an explicit cleanup of only newly created HCA1_Relics assets through editor APIs/UI and check for references; do not delete `.uasset` files on disk. If extra assets appear unexpectedly, stop and inspect. Verify the destination and existing package checks again before rerunning.

## Engine acceptance still required

- Validate actual UE 5.8.3 Python API execution, FBX factory routing, intended source transforms, approximately +X facing, base-center pivot and centimeter size next to the 1.8 m character. Compare source geometry, normals/bevel shading, UVs, slots and triangle counts; the Nanite fallback count may differ from source geometry.
- Verify Nanite build, opaque materials, Windows render and supported Mac fallback; no shader/import errors in Output Log. Check material instance parameter values and cave-light response, particularly the idol's glow, gold/jade headlamp highlights, stone and tan rope.
- Fit the heart's stone-only collision in Static Mesh Editor and test it; review the three box colliders. Save only the owned relic assets. Reopen assets and verify persistence, import source paths and dependencies; all new assets must resolve inside HCA1_Relics except the read-only M_Stylized parent/dependencies.
- Check in `L_StyleTest` only under its required lock and coordination, then HC's own test map/sublevel. No map is changed by this delivery. Swap greybox only after visual/collision acceptance.
- For the later integration push, compile any changed gameplay Blueprints, run Play As Client with at least two players, check 2/3/4-player scaling, second local split-screen readability/input where relevant, and inspect errors/Accessed None. This delivery ran no imports, editor, PIE, gameplay, split-screen or platform tests.
- Check Git status and LFS tracking before the later asset commit. Keep #18's import and in-place checkboxes unchecked until those actual gates pass.

API evidence uses the installed 5.8.3 headers (see `evidence.json`). Public reference pages: [FBX options](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/FbxStaticMeshImportData?application_version=5.0), [StaticMeshEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/StaticMeshEditorSubsystem?application_version=5.7), and [MaterialEditingLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialEditingLibrary?application_version=5.7). Those older-version public pages are API context; they do not establish a tested 5.8.3 import.
