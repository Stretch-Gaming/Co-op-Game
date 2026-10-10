# HC-0 verification — Windows, 2026-10-09

Verified against the revised cave plan at `f1011f9`, using Unreal **5.8.3**, changelist 58210709. Blueprint-only; no `Source/` folder. First-time engine/shader setup and two plan revisions exceeded the planned setup cycle. HC-1 has not started.

## Saved project

- Third Person Blueprint template, no Starter Content. All 238 original template content files match their creation hashes.
- Unreal MCP, All Toolsets and Python Editor Script plugins enabled. `.mcp.json` points to the editor's localhost port 8000. Chaos Vehicles remains enabled for the unused Vehicle template reference pack imported under the earlier plan.
- Editor/game default map: `/Game/Maps/L_Site01`. GameMode and GameInstance defaults use the Coop classes. Maximum players: 4.
- Split-screen and gamepad offset enabled. Maintain Y-FOV is configured in `DefaultEngine.ini`. F5/F6 and PG's split-screen helper are future sprint work.
- After a fresh editor launch, Site 1 and MCP loaded without startup errors. The toolsets' required GameFeatureData scan rule is configured.
- Site 1's Always Loaded sublevels: `/Game/Puzzles/L_Site01_HC`, `/Game/Player/L_Site01_PG`, `/Game/Hazards/L_Site01_HZ`.
- Map 2 has `/Game/Hazards/L_Site02_HZ` Always Loaded. Its early floor/environment bootstrap makes the bare map usable for later travel tests; HZ owns its later art.
- Both persistent levels contain four player starts only. Temporary floors/environment are in HZ. Saved floors measure 30 × 30 m and 20 × 20 m, with surfaces at Z=0. Old lane map redirectors were removed with Unreal's Update Redirector References command.

## Contracts

All eight core Blueprints and `BP_HC0ContractProbe` compile without errors. GameMode/GameState inherit the non-Base engine classes; character/controller inherit the original template classes.

- `E_RoundPhase`: Lobby, Playing, Cleared, Failed, MapComplete.
- `S_RoundState`: Index, Phase, Attempt, PhaseEndsAt, ScalingRow. `RoundState` is RepNotify; its handler calls `OnRoundStateChanged(State)`.
- GameState's RelicsCollected/RelicsAvailable and PlayerState's ColorSlot replicate. GameInstance has the two run relic totals for future travel logic.
- `SetRoundPhase` checks authority, suppresses same-phase updates and preserves every other struct field. StartRound(Index), ClearRound(), FailRound(), CompleteMap() and AddRelics(Count) are printing stubs.
- `GetPlayerCount` counts PlayerStates. `GetScalingRow` returns the stored struct row. Default state is Index 0, Lobby, Attempt 0, no timer, row `2`, with zero relic totals. Automatic lobby row updates and round snapshots remain scheduled work.
- `E_InteractMode`: Instant, Timed, Continuous. `BPI_Interactable` has GetInteractInfo(Instigator) → Prompt, HoldSeconds, Mode; CanInteract(Instigator) → Result; Interact, InteractBegin and InteractEnd, each with Instigator.
- `BPI_RoundReset`: ResetForRound(Index, Attempt). Carrying functions remain empty contracts for their later sprint.
- `S_RoundScaling`/`DT_RoundScaling`: only PlateCount and StatueCount. Rows `2` = (3,2), `3` = (3,1), `4` = (4,1).

## Local runtime checks

PIE used **Play As Client**, with a dedicated server and separate client worlds in one editor process.

| Check | 2 clients | 3 clients | 4 clients |
| --- | --- | --- | --- |
| Player count agrees everywhere | 2 | 3 | 4 |
| Coop GameInstance/character classes loaded | Passed | Passed | Passed |
| All five phase values replicate | Passed | Passed | Passed |
| Non-default index, attempt, timer and row survive phase changes | Passed | Passed | Passed |
| Relic totals agree everywhere | Passed | Passed | Passed |
| Dispatcher fires once per update on server and every client | Passed | Passed | Passed |
| Same phase and five stub functions leave state/callback count unchanged | Passed | Passed | Passed |
| Owning-client running and jumping replicate | Passed | Passed | Passed |
| Errors or Accessed None in successful test interval | 0 | 0 | 0 |

The probe set a server-only fixture (Index 7, Attempt 2, timer 123.5, row matching client count, relic totals 11/19). Each world bound its own Blueprint listener. It observed five updates, and no additional update for the same phase. The test actor was placed temporarily in HC's sublevel, never saved there, and discarded before the final saved-map audit. Its reusable Blueprint asset lives under `Content/Puzzles/Test/` and is absent from gameplay levels.

Map 2 separately passed a four-client spawn test: every pawn stood on the corrected floor, with normal capsule clearance. A standalone split-screen test created two local players, verified both Coop controllers and locally controlled pawns, and visually confirmed two rendered horizontal views. Both test intervals had zero errors or Accessed None.

Template input remains per owning local player and its HUD logic uses AddToPlayerScreen. HC-1 will move pawn input contexts to possession changes. Physical gamepad routing was not tested.

## Method and team checkpoint

The built-in Unreal MCP server handled discovery, editor UI operations, asset editors, and PIE controls. Editor Python also used Unreal's Blueprint, asset and data-table toolset APIs. Enum/struct edits used the editor UI. Binary assets were never edited directly on disk. Final audit found no dirty packages or temporary test actors in the saved maps.

Playable 1 requires both Macs and a second Windows client to join the Windows host at the same engine patch and commit, then run and jump while seeing each other move. Stretch confirmed both Macs are ready; cross-machine verification is pending. Local PIE and split-screen checks do not establish Mac joining or packaging. Map travel behavior begins in HC-2.
