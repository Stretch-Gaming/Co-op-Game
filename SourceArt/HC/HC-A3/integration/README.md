# HC-A3 completed engine delivery (#20)

The three source textures from PR #68 are now imported in Unreal 5.8.3 and used by the owning player's HUD. This integration branch includes the source and offline preparation from PRs #68 and #72 plus the runtime work. Neither earlier PR was merged. The original checkout was left alone.

## Delivered assets

| Path | Purpose |
| --- | --- |
| `Content/Puzzles/Art/HCA3_UI/T_HUD_*.uasset` | Three 512px UI textures with alpha |
| `Content/Puzzles/Art/HCA3_UI/DA_HCA3_*Brush.uasset` | Square, alpha-aware Slate brushes |
| `Content/Puzzles/UI/HCA3/WBP_HCA3RoundHUD.uasset` | Relic totals, round number, Ready/Cleared/Failed display |
| `Content/Puzzles/UI/HCA3/AC_HCA3HUD.uasset` | Local owning-pawn HUD creation, controller changes, cleanup and prompt reflow |
| `Content/Puzzles/UI/WBP_InteractPrompt.uasset` | Art-backed interaction prompt with separate text and timed progress |
| `Content/Core/BP_CoopCharacter.uasset` | Locked integration: component attachment and prompt sizing |

All binary changes were made through the editor. No maps, shared materials, project settings or other-lane assets were edited. The Core lock was acquired after the HC-1 chat released its character. The existing server interaction logic, RPCs, Enhanced Input setup and `UpdatePrompt(Text, Percent, Visible, Timed)` contract remain intact.

The three original PNGs and their SHA-256 hashes are unchanged. Texture import/readback uses UserInterface2D RGBA, UI group, no mipmaps, sRGB, retained alpha, clamp XY, bilinear filtering and no streaming/virtual texture. Scale is handled by square UMG brushes; collision and Nanite are not applicable to textures. PG-A0 had no established UI-specific preset; this concrete UI preset was verified in engine.

## Runtime layout and bindings

Round HUD fills the owning player's screen using `Add to Player Screen`. It reads `BP_CoopGameState.RelicsCollected/RelicsAvailable` and `S_RoundState` without changing gameplay state. It shows the Demo 1 three-round display (this is not a player-count constant). Actual relic state in the current test maps is 0 / 0; relic collection gameplay remains HC-2's responsibility.

Let d be viewport DPI, w/h the local widget size, and s = clamp(min(w*d/1280, h*d/720), 0.85, 1.25) / d. The icon is 64*s square at (24*s,24*s); counter text starts at (96*s,40*s), font 22*s. The round frame is 340*s square centered at the top, offset -94*s to account for its transparent padding. Its normal label uses 22*s; the cleared/failed state keeps the round number below it.

The prompt is anchored at (0.5,0.82) and centered in its owning screen. Desired size is (330/d,170/d), with a 300/d square frame and separate action/key text. Long action labels over 19 characters render as the first 16 plus an ellipsis; the supplied localized Text value and gameplay contract are preserved. The timed bar uses the existing server-confirmed Percent. The component refreshes presentation every 0.2 seconds and recalculates prompt placement after a second local player joins. No global viewport add or indexed-player getter is used.

The actual runtime geometry above supersedes the proposed offline geometry for engine use. No nine-slice stretching is used. The font is Unreal's existing Roboto; no external font was added.

## Acceptance evidence

- `texture-import.json`: actual engine/project identity, source hashes and property readbacks.
- `final-engine-audit.json`: all four modified/new Blueprints compile successfully, final graph snapshots, three 512px imported textures retaining alpha, no indexed player getters or global viewport add.
- `client-interaction-2.json`, `-3.json`, `-4.json`: Play As Client in L_HC_Test. Distinct owned HUDs, input/prompt ownership, instant RPC replication, short/full timed hold, continuous begin/end, range and permission cancellation, round reset replication, and pawn end-play cleanup.
- The final two-client regression runs after prompt reflow. Three/four-client interaction tests ran before that presentation-only addition; their gameplay graphs were preserved. An interrupted final rerun is retained as `interrupted-regression-2.json`; it stopped when PIE ended before completion and is not acceptance evidence.
- `main-map-clients.json`: L_Site01, Play As Client, two correctly owned and distinct HUD/prompt instances.
- `split-screen.json`: L_Site01, two local players and independent interactions. `final-split-screen.json`: final owning-player reflow check at 1280×720.
- `runtime-log-check.json`: no Accessed None or Blueprint Runtime Error in the isolated integration editor's full log. Authoring Python diagnostics are not counted as runtime Blueprint errors.
- `save-audit.json`: no dirty map packages; only the four owned/locked Blueprints saved.
- `delivery-validation.json`: final file hashes, source alpha/dimensions, scope and Git LFS coverage.

The retained screenshots are raw Slate captures, including window chrome: 1289×780 around a 1280×720 client area and 1929×1140 around a 1920×1080 client area. Their HUD text is rendered by UMG, never baked into the images.

![Final 1280×720 two-player layout](cave-split-1280-playing.png)
![Final 1920×1080 two-player layout](cave-split-1920-playing.png)
![Cleared state](cave-split-1280-cleared.png)
![Failed state](cave-split-1280-failed.png)
![Style-test map](style-test-1920.png)

`cave-full-1920-playing.png` records full-screen review. The style-test image uses a transient owning-player prompt set to 65% to expose the bar during art review; it is not a network-timing test. The separate client reports test actual server timing. No style-test map changes were saved.

Windows UE 5.8.3 is the tested platform. Physical gamepad input, Mac execution and broader HC-8 results/restart gameplay are separate playable-checkpoint work, not claims made by this art delivery. No merge was performed.

## Reproduction and review

Open this branch's CoopGame.uproject in UE 5.8.3. Inspect the delivered assets directly; imports already exist and the opt-in importer refuses replacement. In L_HC_Test use Play As Client, Run Under One Process and 2/3/4 clients. For automated interaction checks set `Saved/HCA3/clients.txt` to the client count and explicitly execute `Tools/unreal/hc_a3_import/check_interaction_hud.py`. Wait for the matching report's `ok: true` before ending PIE.

For local split-screen use L_Site01 with two local players in the same world. Confirm both widgets use their owning controllers, focus separate HC1Main fixtures, and inspect Round 2, Cleared and Failed after the GameMode changes phase. Do not place actors or save these transient test state changes. Compare against the screenshots at 1280×720 and 1920×1080.

The default `import_hud.py` remains a source validation and proposed-import printout with no Unreal import or writes. The authoring scripts in that folder are explicit engine tools with checkout/version guards, and are not needed for ordinary review. Source provenance and public redistribution rights remain in [../README.md](../README.md) and [../prompts.md](../prompts.md); no attribution is required by those output terms.
