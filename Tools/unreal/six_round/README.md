# Six-round adventure integration (#93)

Primary-owned integration checkout: `C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game`, branch `codex/six-round-adventure`, Unreal 5.8.3 editor port 8061. Three explicitly authorized Sol 6.1 medium workers authored separate Core/player/world scripts. The primary reviews, repairs and executes them sequentially through the editor. Binary assets are never authored on disk.

This is ongoing work. Script syntax, editor compilation, geometric clearance, client input tests and a complete human-played mission are separate gates. None of the offline reports establishes gameplay completion. Worker staging reports predate primary repairs; final source/asset hashes and editor receipts are authoritative when recorded.

## Ownership and current boundaries

- This task owns Core/adventure behavior, player systems and isolated test fixtures, under exact LFS reservations where required.
- “Pull all changes down” owns `L_ConnectedRoomMaze`, its HC maze copy and standalone environment door. Its verified delivery is the environment basis for later adventure integration. Do not add a duplicate door or edit its active checkout/editor.
- PK holds the production HZ maps, original maze capture and original AdventureTrap while rebuilding them. Those files remain untouched here.
- World staging therefore uses new `Hazards/Traps/SixRound/` actors and `Hazards/Test/SixRound/L_WorldRoute_Test`. The composite disables standalone cave proxies and streams one copied cave plus one derivative maze. These are isolated test assets, not production acceptance.

The graphics editor suffered a D3D device reset on October 10. Authoring recovered in NullRHI, then resumed in a rendered D3D11 editor. Graphics-free results and synthetic owning-input checks must not be described as physical-device, Mac or presentation acceptance.

## Native authoring order

The primary must hold the editor lease and exact asset locks. `request.py` queues one relative script and a JSON argument object; `run_stages.py` accepts an ordered JSON list of `[script, args]` pairs and stops on failure. Compile/save must pass before the next dependent stage. Do not rerun a green stage unless its inputs changed.

1. Declare primary/player/Core contracts (`00_primary_contracts.py`, `player/stage0.py`, `core/00_contracts.py`); install the declared interfaces through the primary UI workflow before graph implementation. Do not rerun declarations over implemented assets: they reset defaults.
2. Build player traversal/tools/cage/taking/chase/spectator graphs, then `core/10_health.py`, `core/20_rounds.py` and `core/resource_recovery.py`. Apply `core/fix_retry_restock.py` after rounds: it captures retry state before the round setter and refills after the new scaling row is active. Initial Round2 entry must not grant an extra refill.
3. Build `core/30_puzzles.py`, `core/40_relic.py` and the parent run/results graphs in `core/60_run.py`; run `escape_key_recovery.py`, then `core/fix_relic_home.py`. The latter requires the recovery functions and the carryable's initialized `InitialTransform`; it restores the authored pedestal pose. Reapplying base round/recovery scripts requires reapplying their narrow fixes.
4. Complete primary Character/input hooks (`integration_inputs.py`, UI server-event/Forward parameter setup, `finish_inputs.py`, `movement_input.py`, `tune_movement.py`, `core/90_character_hooks.py`) and world reset hooks. Preserve owning Enhanced Input, reliable server requests and per-local screens. Missing UI-created pins/interfaces stop the dependent stage.
5. Author world meshes/actors from the current reviewed manifest (`world/bake_preserved.py`, `world/place_preserved.py`, world behavior builders, `world/place_route.py` with `include_test_cave_proxies=false`) and `player/place_test.py`. Use the latest primary-reviewed repair plan and targeted refresh. Do not regenerate `world/positions.json` or replace repaired meshes with an older bake.
6. Build `core/puzzle_door_adapter.py` and `core/test_map_game_mode.py` before `core/test_map_build.py`; apply `finish_test_mode.py` and `core/50_place.py` against the isolated test packages. The latter includes `core/place_small_relics.py`; the narrow writer checks and saves only the tagged pickups. The primary's `copy_chasm_portal.py` edits only the owned cave copy. `update_perch_locks.py` moves only the two HC locks onto the authored decks. Then run test-map audit/validation and geometric clearance gates.
7. Apply HUD and presentation hooks after their dependencies exist. Reuse canonical repository Art/Audio adopted in PR125, including `/Game/Player/Art/Taker/SM_Taker` and `SM_TakerArm`. Do not run duplicate imports or copy assets from another checkout. `player/presentation_hooks.py` and `wire_presentation.py` bind delivered assets. Confirm legacy duplicate audio cleanup through the editor before publication.

The two narrow fixes take `{}` arguments. Their queue paths are `core/fix_retry_restock.py` and `core/fix_relic_home.py`, relative to `Tools/unreal/six_round/`. Each script's prerequisites and native receipts govern execution; this list does not establish a successful rebuild.

## Isolated map composition

`/Game/Puzzles/Test/SixRound/L_SixRound_Test` uses the test GameMode and streams only `L_CaveEnvironment_Test`, `L_SixRound_HC_Test`, `/Game/Hazards/Test/SixRound/L_WorldRoute_Test` and `/Game/Player/Test/SixRound/L_SixRound_PG_Test`. The cave is a saved copy of the read-only HZ source; inherited gameplay is removed only from that copy. WorldRoute contains the full connection-derived maze with reviewed gaps, separate HallB paths and doorway cuts. Do not also stream `L_ConnectedMaze`, whose floors would fill those gaps; do not add EnvironmentPreview.

One puzzle-controlled connection-door adapter stands at `(325,1400,200)` and opens to Z650. It uses the delivered mesh; manual interaction cannot bypass Round1. Protected source maps and the standalone environment door remain unchanged. Current repair2 `world/positions.json` is authoritative for approaches, arrivals, upper walk nodes, solo challenges and checkpoints. Production entry into this route remains a primary integration gate.

## Evidence

The native queue records source hashes and returned diagnostics under ignored `Saved/SixRound/receipts/`. Final reviewed evidence belongs under this folder's `evidence/`, with explicit passed, failed and unrun gates and asset hashes. Keep failed diagnostics that explain a repaired defect without presenting them as the current gate.

`Saved/SixRound/native-qa-pg/summary.json` records passed owning controls and initial door checks for 2/3/4 joining clients, four-player host split controls, F5 second-local creation and five shared-keyboard bridge checks, at base `9dc0fab`. These are synthetic owning-input tests with disclosed initial approaches, including a shared-keyboard climb placement. Cleanup records empty PIE worlds, restored preferences and editor handback to primary. Read the per-case reports and hashes before extending claims to later inputs.

`INTEGRATION_STATUS.md` records native compile/save and composition results; it is an integration snapshot, not acceptance. The QA summary leaves whole-route movement, cage/heavy/death/taking/chase, a full six-round mission, rendered visual/audio, physical keyboard/controller devices, Mac and packet emulation unrun. Geometric traces cannot replace actual walking/jumping/climbing or the heavy return/zipline test. Failed API inspection attempts remain diagnostic evidence.

The fonts are unmodified Averia Serif Libre Regular/Bold from Google Fonts under SIL OFL 1.1, with source fonts and the license in `SourceArt/HC/SixRoundUI/Fonts/` and attribution in `CREDITS.md`. Their raw Git blob hashes were independently compared with the upstream files.

## Required final gates

Six-round transitions and no early completion; immediate death without teammate revive; owning spectator input; regroup and three-second wipe/impossible-puzzle restart; released mechanisms and dropped relic; escape retry with the cage open and relic restored; light locks/flares; heavy-carry and unrelated zipline movement; server-scheduled taking/traps/chase; actual 2/3/4-client and host split-screen mission runs; results travel and two successive runs; complete route walking, log/compile review, visuals and separately recorded Mac/device checks.

Unpassed gates keep #93 and the related phase issues open.
