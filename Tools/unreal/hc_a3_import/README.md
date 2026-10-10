# HC-A3 opt-in texture import preparation

Depends on [PR #68](https://github.com/Stretch-Gaming/Co-op-Game/pull/68) at `6f7e713f47f7d3ac8b9d96738639d3ea4bda4618`. The three source PNGs are reused unchanged. `manifest.json` supplies repository-relative paths, SHA-256 hashes, dimensions, exact object destinations and the fixed texture preset.

## Default: validate and print

```text
python -B Tools/unreal/hc_a3_import/import_hud.py
python -B Tools/unreal/hc_a3_import/test_import_hud.py
```

The default command uses only Python's standard library. It checks all three exact source paths and PR #68 hashes, PNG chunk CRCs, 512 x 512 RGBA format, real transparent/opaque pixels, transparent edges and visibly open frame centers, then prints the proposed imports. It does not import the unreal module, write files or change assets. Hydrate LFS pointers first.

## Future opt-in apply

Do not run apply during this preparation delivery. In a later separately authorized pass, open the **same checkout's CoopGame.uproject in Unreal 5.8.3**. The project path and engine patch must match. Run through the editor's Python console, using the absolute path to this script:

```python
import runpy
api = runpy.run_path(r"<checkout>/Tools/unreal/hc_a3_import/import_hud.py", run_name="hc_a3_import")
api["main"]([])          # default dry-run, even inside the editor
api["main"](["--apply"]) # explicit opt-in after reviewing the printed plan
```

Apply accepts exactly three new Texture2D assets under `/Game/Puzzles/Art/HCA3_UI/`. It refuses any existing destination, any source/hash/destination change, an incorrect project, or a different engine version. There is no overwrite or reimport mode.

AssetImportTask uses automated synchronous import with a TextureFactory, material creation disabled, replacement disabled and save disabled. After verifying each returned object path/type and applying/readback-checking settings, it saves only the three new textures. It never edits Core, widgets, maps, shared materials or project settings and never calls Save All. No Source folder or runtime C++ is added.

This is not a transaction spanning engine import failures: a failed apply can leave new unsaved HC-A3 textures in memory. Stop and inspect that folder rather than retrying or saving unrelated dirty assets. The script does not delete assets or roll back unrelated state. Actual engine import was subsequently executed and verified in the integration delivery linked below.

## Fixed UI texture preset

| Property | Value | Intent |
| --- | --- | --- |
| compression_settings | TC_EDITOR_ICON (UserInterface2D RGBA) | Preserve painted UI color/alpha |
| lod_group | TEXTUREGROUP_UI | UI texture group |
| mip_gen_settings | TMGS_NO_MIPMAPS | Fixed HUD texture without mip chain |
| srgb | true | Source color is sRGB |
| compression_no_alpha | false | Preserve alpha |
| never_stream | true | Keep small HUD textures resident |
| virtual_texture_streaming | false | Ordinary UMG texture |
| address_x / address_y | TA_CLAMP | Avoid wrapping at transparent canvas edges |
| filter | TF_BILINEAR | Smooth display scaling |

This is a concrete proposal for the missing UI import preset, not an assertion that PG-A0 already approved it. The three 512px RGBA textures use about 3 MiB uncompressed texel storage before overhead; engine verification is recorded in the integration delivery.

API review: [TextureFactory 5.8 documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextureFactory) confirms material/alpha/preset fields. Installed UE 5.8.3 headers reviewed: AssetImportTask.h, TextureFactory.h, Texture.h, Texture2D.h and TextureDefines.h. API property/enum names are also guarded during apply. The mocked tests demonstrate script logic, not actual Unreal compatibility.

## Evidence and boundaries

`test-results.json` records 15 passing offline tests, covering default no-writes/no-Unreal-import behavior, wrong engine/project, existing targets, out-of-scope destinations, source escape/hash changes, altered alpha settings, corrupt/RGB PNGs and fake-API import/save boundaries. `dry-run.json` records the validated portable plan.

The preparation gate passed in PR #72, targeting `codex/hc-a3-hud-art` while #68 remained unmerged. [Engine delivery](../../../SourceArt/HC/HC-A3/integration/README.md) records subsequent actual imports, Blueprint integration, client checks and split-screen acceptance.

## Engine authoring tools

These are explicit editor scripts, separate from the default dry-run importer. Execute only in this checkout's Unreal 5.8.3 editor, with the existing AllToolsets plugin available. The three Blueprint authoring scripts reject another checkout or engine before edits. No new plugins are enabled.

- `execute_import.py`: execute the guarded importer and record property readbacks; rejects existing targets. Do not rerun now that the textures exist.
- `build_hud.py`: author the three square Slate brushes and the existing HC-A3 RoundHUD Blueprint. The widget must already exist (the delivered asset is supplied). Reads GameState; does not write gameplay state.
- `build_component.py`: author HC-A3's owning-pawn HUD component, including cleanup and prompt reflow.
- `integrate_hud.py`: attach that component and author only prompt painting/layout. Requires the Core character LFS lock and a handoff before use. Preserves gameplay graphs and `UpdatePrompt` contract.
- `check_interaction_hud.py`: opt-in PIE test for the existing HC-1 lane fixtures in L_HC_Test. Set Saved/HCA3/clients.txt to 2, 3 or 4, configure Play As Client and start PIE before executing. It uses native timers for RPC execution and stops its callback on completion/error. Observe the matching client-interaction-N.json result before ending PIE. It changes transient PIE fixtures only.

Authoring scripts save only their named assets; they do not call Save All. Normal development should edit the delivered Blueprints through Unreal. Do not execute these scripts merely to inspect assets.
