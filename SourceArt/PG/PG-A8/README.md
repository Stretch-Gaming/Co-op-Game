# PG-A8: hand flare and hiss — chosen source

Source delivery for [#111](https://github.com/Stretch-Gaming/Co-op-Game/issues/111), consumed by [#107](https://github.com/Stretch-Gaming/Co-op-Game/issues/107). Candidate A is the wrapped grip with a bent amber burning tip. B's straight collar and narrow tip lost useful detail at 64 pixels; only its comparison render is retained. Both candidates were generated outside the repository. The visual reference was the existing [style frame](../PG-A0/style-frames/style-reference.png), interpreted in original scripted geometry; no image generation or third-party mesh was used.

| Deliverable | Source specification |
| --- | --- |
| `PG-A8_HandFlare.blend` | Editable cleaned chosen mesh and wireframe collision; Blender 5.2.2 LTS |
| `SM_HandFlare.fbx` | 736 visible triangles, 384 vertices; 6 × 6 × 22 cm; +Z up, FBX centimeter metadata, unit scale; base-center pivot, bounds −3/−3/0 to +3/+3/22 cm |
| `UCX_SM_HandFlare_00` (inside FBX) | One closed convex 12-sided prism; 44 collision triangles; encloses the visible mesh |
| `SFX_Flare_Hiss_Loop.wav` | Mono PCM16, 48,000 Hz, 192,000 frames / 4 seconds; −8.40 dBFS peak, −21.60 dBFS RMS |
| `previews/` | Studio and dark source renders, candidate comparison, native 64-pixel readability board; illustrative Blender previews, not Unreal acceptance |
| `validation.json`, `SM_HandFlare.validation.json`, `audio-build.json` | Fresh FBX reimport and blend reopen checks, exporter metrics, deterministic synthesis parameters |

No textures are required or supplied. Four stable material slots, in this exact index order:

1. `M_FlareMetal`: blue-violet dark metal; use an opaque `M_Stylized` instance, roughness 0.48 / metallic 0.45.
2. `M_FlareGrip`: matte brown wrap; opaque `M_Stylized` instance, roughness 0.85.
3. `M_FlareBody`: ochre paper/cloth; opaque `M_Stylized` instance, roughness 0.80.
4. `M_FlareAmber`: ember and sculpted flame; opaque PG emissive material, torch amber **#FFB347** (linear RGB 1 / 0.4508 / 0.063). This slot can share the existing burn fade; it must not stay lit after expiry.

Use the shared material's gradient for darker bases / lighter tops. Broad bevel profiles and flat facets provide the edge shape; no curvature texture is baked. Source-preview materials demonstrate colors only; replace them with project material instances at import.

## Rebuild and check

Tools: [Blender](https://www.blender.org/) 5.2.2 LTS, its bundled Python and NumPy 2.3.4; system Python 3.14 and Pillow 12.1.1 for the optional labeled preview boards. No paid service, add-on, live Blender connection, Unreal editor, or external asset dependency. All modeling, synthesis and preview lighting code is in this folder. Start from the repository root; choose a **new external** staging directory:

```sh
python3 SourceArt/PG/PG-A8/rebuild.py /tmp/pg-a8-rebuild --compare
python3 SourceArt/PG/PG-A8/preview_boards.py /tmp/pg-a8-rebuild
```

On Windows use an external directory and pass `--blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"` if Blender is not on PATH. The wrapper refuses a nonempty staging directory or a directory within the repository. Every headless process uses factory startup and `--python-exit-code 1`, and runs sequentially; Cycles source renders use two CPU threads, 16 samples at 512 pixels. Copy only `delivery/` over this asset folder after review; keep unselected geometry outside the repository. These commands do not remove existing files or touch editor sessions.

The chosen visual goes through the established `Tools/blender/cleanup_export.py` with a 1,999-triangle limit. No decimation was needed. `validate_flare.py --finalize` then adds the separately named UCX collision and saves the editable clean blend. A subsequent fresh process reimports the final FBX, checks its budget/bounds/pivot/slots/finite UVs, closed manifold edges, positive volume and absence of degenerate faces, verifies convex collision containment, and reopens the saved blend to compare metrics. This is Blender reimport evidence; Unreal reimport remains pending.

Audio is original PCG64 noise (seed 111), synthesized with periodic FFT bins, shaped above 650 Hz / below 6.5 kHz, and modulated by whole-cycle 1.25 Hz and 3 Hz envelopes. A 96-sample smooth envelope at each end and four zero samples at each endpoint make the PCM value and adjacent slopes agree exactly across the loop. The measured seam 10 ms RMS / next 10 ms RMS ratio is 0.838, with zero clipped samples and negligible DC. No sampled recording, speech, music or library sound is used. Audio format and continuity passed; in-game audition is pending.

## Import handoff to PG tools

Import the FBX into `Content/Player/Art/Flares/` as `SM_HandFlare`, scale **1**, convert scene units, static mesh only, **Nanite off** (under 2k triangles), **Import Materials/Textures off**, **Generate Collision off**, **One Convex Hull per UCX on**, and preserve the supplied normals. Verify exactly one visible mesh and one imported simple collision hull, then assign the four slots above. Reimport from this committed source path.

The existing authoring source (`Tools/unreal/six_round/player/stage0.py`) uses an Engine cylinder at relative scale **0.06 / 0.06 / 0.22**, nominally 6 × 6 × 22 cm, with a **centered** actor origin. This source asset already has those dimensions and a **base** origin. Do not retain the old nonuniform scale when swapping meshes. For a centered runtime fixture, a normalized visual needs **Z = −11 cm** relative to its centered collision root. If attached below the old scaled root, inherited scale/location must be compensated or made absolute; a plain −11 cm child offset there is insufficient. The tools owner should select the adapter while preserving the existing swept root, flight, owner-ignore and light behavior. Recheck throw origin/landing/bounce and light alignment after integration. The amber tip center is around Z = 19 cm from the source base (Z = +8 cm from a centered adapter). No Blueprint/system replacement is provided here.

Import the WAV as `SFX_Flare_Hiss_Loop`. Enable looping on the owning audio component or cue; spatialize and attenuate as **3D mono** sound with a candidate audible range of 400 cm, then tune by ear. Match component playback/start/stop and volume fade to the existing replicated burn lifetime; do not create a second burn lifecycle. Stop audio on expiry, actor cleanup and round cleanup. Ensure late joining clients do not play a hiss after burnout. A waveform seam check does not establish in-game attenuation or fade quality.

Import and placement, `L_StyleTest` review (requires shared-level lock), client and host split-screen visual/audio checks, and Mac/Windows review are pending under #111 / #107. They require the serialized private editor slot after tools/view handoff and a saved integrated candidate. No Unreal editor was opened or attached by this source worker. Package checks were not attempted on the roughly 8 GiB free disk volume; they require the established 30 GiB gate. These source checks make no network, device, roster or packaged-game claim.

## Prompt, provenance and redistribution

Exact modeling brief:

> A hand flare matching a 6 x 6 x 22 cm greybox, broad faceted metal heel, wrapped grip, ivory paper canister, chunky amber burning tip; stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures

Original work for PK / `peterkimpk1`, made with free local Blender/Python scripting and synthesis. All authored assets, renders and scripts in this folder are offered under **[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)**: public repository redistribution and commercial use allowed, **no attribution required**. No Fab/marketplace/library asset or paid plan was used. The reference image belongs to the existing project and is not copied into this delivery. No `CREDITS.md` addition is required. Tool licenses apply to the tools themselves, not these original assets.
