HC-A3 layout and import-preparation slice for #20 is complete on `codex/hc-a3-layout-prep`, based on PR #68 head `6f7e713f47f7d3ac8b9d96738639d3ea4bda4618`.

Dependency: PR #68 remains the source-art parent. This follow-up targets `codex/hc-a3-hud-art`; neither PR is merged.

Owned changes:
- `SourceArt/HC/HC-A3/layout/`: 24 native-resolution HUD previews and two review boards, dimensions/margins, UMG handoff, renderer and independent evidence.
- `Tools/unreal/hc_a3_import/`: manifest, read-only-by-default opt-in UE 5.8.3 import script, instructions and 15-test guard evidence.

Coverage: full screen plus horizontal and vertical two-player split-screen at 1280 x 720 and 1920 x 1080, for playing/timed/cleared/failed. All layouts show relic totals and round number; timed progress and phase banners use independent text/drawing layers. The three delivered PNGs and their SHA-256 hashes are unchanged.

Validation: 24 cases / 40 player views passed visible-safe-area, frame-opening, non-overlap and square-aspect checks. The standard-library PNG alpha decoder agrees with Pillow. Source transparency/hashes and full-resolution preview hashes passed. All 15 importer tests passed, including default no-repository-writes/no-unreal-import behavior and wrong project/version, overwrite, path/hash/alpha-setting and destination guards. Apply logic was tested only with a fake editor API.

Proposed import destinations are the three named textures under `/Game/Puzzles/Art/HCA3_UI/`. Default mode only validates and prints the plan. Actual apply requires explicit --apply, a matching checkout and UE 5.8.3, and refuses existing assets. It creates no widgets/materials and saves only the new approved textures.

No artwork regeneration, paid generation service or Unreal launch/control occurred. Actual imports, widget integration, engine DPI/texture verification, client tests and in-game split-screen acceptance remain pending. Leave #20 open and leave its import/in-place checkboxes unchecked.
