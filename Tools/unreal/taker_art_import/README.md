# PG-A7 taker art import

Prepared for the primary agent. Only the primary operates Unreal. These tools import the exact PR121 art; they do not place actors or change the taking, chase, interaction, puzzles, HUD or sounds.

Source: PR121, commit `60ae5e0250e790f943064f54e400574e8285463c`, issue #110. The 17 hydrated files in `SourceArt/PG/PG-A7/` total about 9.2 MB. `source-manifest.json` records every SHA256, binary FBX measurements, textures, sockets and original author metrics. Run `audit_source.py` with Python to reproduce it.

The body is 13,199 triangles, about177×130×266cm; the arm is5,500 triangles, about285×163×122cm. Both carry UV0/normals and socket empties. Body pivot is at the feet; arm pivot is the wall plane. Their static art has no collision; future actors own collision and behavior. Native import checks dimensions, facing/pivot bounds, Nanite triangle count, ordered material slots and socket positions before saving.

**Known delivery discrepancy:** source README/metrics claim both exports are closed/manifold. Binary FBX face incidence finds2 boundary edges and one edge shared by3 triangles near the body's top of head (aboutZ264cm, X−5cm). Arm is clean. Exact edge coordinates are in the manifest. The primary explicitly accepted recording this as a warning for visual/no-collision art; source geometry remains unchanged. Native rendering still needs inspection.

## Ten canonical assets

All under `/Game/Player/Art/Taker/`:

- `SM_Taker`, `SM_TakerArm`
- `T_Taker_BaseColor`, `T_Taker_ORM`, `T_TakerArm_BaseColor`, `T_TakerArm_ORM`
- `MI_Taker_Body`, `MI_TakerArm_Body`, `M_TakerEyes`, `MI_Taker_Eyes`

Bodies inherit read-only `/Game/Shared/Style/M_Stylized`, UV mode, baked gradient, white tint, no amber edge/rim term, cavity0.4, roughness1 and metallic0. BaseColor is sRGB/default compression; packed ORM is linear/TC_Masks (R AO, G roughness, B metallic). The eyes are opaque/unlit ghost white#D6F0FF with emission8. Opaque meshes enable Nanite, leaving its fallback for Mac review. No shared material or source FBX is saved or edited.

## Primary execution

Use existing `Tools/unreal/playable_game/run_priorities.py`, injecting `ROOT`, `ARGS`, `OUTPUT` as usual:

1. `folder=taker_art_import`, `script=import_taker.py`, `mode=preflight`.
2. Review evidence; then same script with `mode=execute`.
3. If import stopped after creating the ten packages, do not rerun execute. Run `script=finalize_import.py`, `mode=verify-only`, review, then `mode=finalize` to verify first and save only the existing ten assets. It checks the preflight shared-parent hash and records final asset hashes. Reopen and run `script=verify_import.py`, `mode=verify`.
4. Render under the cave's lighting at a split-screen size; inspect sockets, eye bloom, silhouette and Mac fallback before swapping the greybox.

Preflight requires this exact checkout, UE5.8.3, stopped PIE, unchanged source hashes, compatible shared material parameters and inherited UV switch false. It refuses any existing asset or unregistered content in the destination, even a previous partial import. It constructs FBX options before mutations. Import disables automatic materials/textures, imports source normals and units, retains degenerate geometry, verifies package names, and saves only these ten packages. No Save All.

On an import/verification failure, newly created editor assets remain for primary inspection; no rollback, asset deletion or automatic overwrite runs. Fixing or clearing a partial import is a separate primary action. Source count is verified against FBX, Nanite keeps that full count; fallback triangle count is recorded separately and may be simplified.

## Source and license evidence

Original team work, Blender5.2.2 modeling/scripts/Cycles bakes. No library assets or generators. PR121 body and `SourceArt/PG/PG-A7/README.md` explicitly state public redistribution allowed and no credit required. This is the team's original-art permission, not an invented CC0 declaration. No CREDITS row is required. The source files retain their delivery hashes. Primary owns the issue/source-license note and scoped locks; this worker creates no external comments or commits.

## PR123 sound consolidation

Coordinator selected `/Game/Player/Art/Audio/` as canonical. PR123 commit `534973a06c6702a82b0b4959b0b98427c1ea6722` supplies9 sound waves and2 attenuation assets there. Primary merged these packages; this worker did not import, alter or delete any audio. `audio-delivery.json` checks all11 package hashes against the PR's LFS objects and the9 source WAVs as mono48kHz24-bit integer PCM (including extensible WAV headers).

Run `verify_audio.py` through the same wrapper for read-only native duration/channel/loop/volume/attenuation/hash checks. Native compressed platform sample rate is not exposed/checked; source48kHz is verified. Canonical attenuation is Sphere/Natural Sound: Taking300cm inner/3000cm falloff, Taker150/1500. Three loops use Restart virtualization. Build layer volume0.5; others1.0. `_2D` waves have no attenuation.

Coordinator owns repointing future taking/chase hooks from the earlier `/Game/Player/Audio/` duplicates, and removing unpublished duplicates after reference checks. Do not run either sound importer again. The coordinator must keep victim-only sting playback, per-local-player chase playback, synchronized chase layers, and stop/fade lifecycle. Listening, relative levels and split-screen audibility remain acceptance checks; PR123 did not wire gameplay or perform a listening check.
