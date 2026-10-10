# HC-A3 offline HUD layout preparation

Bounded follow-up to [PR #68](https://github.com/Stretch-Gaming/Co-op-Game/pull/68) for [issue #20](https://github.com/Stretch-Gaming/Co-op-Game/issues/20). Base: `codex/hc-a3-hud-art` at `6f7e713f47f7d3ac8b9d96738639d3ea4bda4618`. This delivery reuses all three source textures unchanged.

## Review

- [1280 x 720 overview](review-board-1280x720.png)
- [1920 x 1080 overview](review-board-1920x1080.png)
- [Native smallest horizontal split, timed interaction](previews/1280x720_split-horizontal_timed.png)
- [Native smallest vertical split, cleared](previews/1280x720_split-vertical_cleared.png)
- [Dimensions and margins](dimensions.md)
- [Concrete UMG handoff](UMG-handoff.md)

There are 24 native-resolution previews: two resolutions, full screen / horizontal split / vertical split, and playing / timed / cleared / failed states. The two split layouts each contain two independently positioned local-player HUDs. Shared relic/round values agree between players; timed-progress samples differ to demonstrate local presentation. Both clear and failed banners retain the round number.

Text and progress bars are independent drawing layers. The three textures remain square and are never stretched. Background polygons are neutral offline context, not new game assets. Overview boards reduce images for scanning; use the individual PNGs for native-size review.

## Reproduce and validate

Use Python 3.10+ and Pillow 10.1+. Hydrate the existing three HUD PNGs from LFS before running:

```text
python -B SourceArt/HC/HC-A3/layout/render_layouts.py
python -B SourceArt/HC/HC-A3/layout/verify_layouts.py
python -B Tools/unreal/hc_a3_import/test_import_hud.py
python -B Tools/unreal/hc_a3_import/import_hud.py
```

Renderer writes only here. The importer default prints a proposed plan and performs no repository/editor writes. It needs only Python's standard library, including full PNG alpha decoding. No generation service, Unreal launch or editor control is involved.

Evidence: `geometry-and-validation.json` gives every player's viewport, scale, square brush rect, visible bounds, text bounds and preview hashes; `independent-checks.json` cross-checks native PNGs, source hashes, margins, states and alpha decoding against Pillow; the importer folder has its 15-test guard report.

The offline gate passed in PR #72, targeting `codex/hc-a3-hud-art` while #68 was unmerged. The completed engine delivery and actual runtime layout are recorded in [../integration/README.md](../integration/README.md). Offline geometry remains a handoff reference; the engine implementation uses its own per-player geometry and DPI calculation.
