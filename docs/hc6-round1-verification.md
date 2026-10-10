# HC-6 Round 1 actor delivery

Stretch's bounded slice of [#12](https://github.com/Stretch-Gaming/Co-op-Game/issues/12), tracked separately in [#77](https://github.com/Stretch-Gaming/Co-op-Game/issues/77) under HC epic #1. The start pad and chamber gate cover part of #11. Full #11/#12 acceptance remains open. No altar, revive, other rounds or global recovery implementation is included.

The worktree was created from `origin/main` at `dcecbab75999f1cc976d847a24912f4246ddbc8e`, on `codex/hc6-round1`. Every editor script checks this checkout's project path and Unreal 5.8.3 before asset changes. The dedicated editor uses MCP port **8016**; the repository's `.mcp.json` and other editor sessions were not changed. Git author is StretchGaming.

## Actor behavior

- `BP_PressurePlate`: a server-only overlap snapshot counts each overlapping Actor once. A Pawn or an Actor with the server tag `HC_PlateWeight` qualifies. Polling also notices tag removal while an object remains inside the volume. Clients never count occupancy. `Enabled` and `Pressed` use RepNotify; the top moves from relative Z **9** to **2 cm**, changes material slot 0, and is hidden when disabled.
- `BP_PuzzleSetup`: reads the **row name** through `BP_CoopGameState.GetScalingRow()`, then reads the existing `DT_RoundScaling`. Rows remain unchanged: **2 players → 3 plates/2 statues; 3 → 3/1; 4 → 4/1**. The enabled slots must be unique and complete. Missing slots, duplicate slots, insufficient transforms or an unset statue class leave the setup unready. It spawns only on the server, owns the spawned instances and destroys/respawns them on a new attempt. Every enabled plate must be pressed simultaneously before it calls the existing GameMode `ClearRound()`.
- `BP_StartPad`: compares unique overlapping Pawn PlayerStates against every entry in the shared GameState PlayerArray, including two local players. Everyone must be present continuously for **3 server seconds**, with 2–4 connected PlayerStates. Departure or a roster change cancels the hold. In Lobby it calls only the existing GameMode `StartRound(1)`.
- `BP_ChamberGate`: the server derives `Open` from round state; RepNotify applies the leaf's relative Z **0/+400 cm**. `RoundIndex=0` is the entrance gate, opening once Round 1 starts. `RoundIndex=1` opens when Round 1 clears or a later round has begun. It closes again for a failed/restarted Round 1.

Setup, pad and gate find GameState at runtime, bind `OnRoundStateChanged` once, and immediately apply its current state. Tick retries a missing initial binding. Setup also polls occupancy on the server, avoiding overlap-event ordering and stale destroyed-actor entries. There are no saved references to placed actors in another sublevel.

All four actors implement `BPI_RoundReset.ResetForRound(Index, Attempt)`, reject client calls and ignore unrelated round indices. The reset clears plate state, setup instances/readiness, the start hold and the matching gate. Configuration follows the authoritative RoundState attempt. The fixture explicitly dispatches this interface and calls GameMode `StartRound`; it does **not** prove everyone-down recovery, checkpoints, reconnect recovery or the unfinished global reset dispatcher.

## Fixture results

`/Game/Puzzles/Test/HC6/L_HC6_Round1` uses only its own temporary geometry, two test materials and `BP_HC6TestWeight`. That weight is a tagged test Actor, with no carrying/statue gameplay. The fixture GameMode supplies the appropriate scaling-row name in Lobby while preserving phase; production Core and the table are untouched.

| Run | Total players | Host local players | Result |
| --- | ---: | ---: | --- |
| Play As Client | 2 | — | 25 checks passed |
| Play As Client | 3 | — | 25 checks passed |
| Play As Client | 4 | — | 25 checks passed |
| Host split-screen | 2 | 2 | 25 checks passed |
| Host split-screen + remote client | 3 | 2 | 25 checks passed |
| Host split-screen + two remote clients | 4 | 2 | 25 checks passed |

The driver injects `IA_Move` into each owning Enhanced Input subsystem. Server teleports establish approach positions; the actual crossings and departures use player movement and normal Character movement replication. The driver waits for the server to observe movement and for PlayerState identity to initialize before advancing. This is an in-process network test, not a physical controller or separate-machine test. The original six-case run used the rendering editor; the complete post-rebase run used an unattended NullRHI editor after GUI/audio initialization stalled on restart. Both runs passed. The native rendered screenshot confirms the host's two views.

Checks cover ownership/binding, all-player start hold and departure, fixture PlayerState addition/removal, stationary tag removal/restoration, two Pawns sharing a plate, one/last departure, simultaneous presses, scaling, replicated sink/material/gate state, actor reset into Attempt 2 and rejected client/wrong-index resets. The extra roster PlayerState is a fixture participant, not a claimed real reconnect test. A focused test also confirms replicated test-weight spawns and fail-closed behavior when `StatueClass` is unset, followed by successful respawn after restoring it.

Evidence is in `Tools/unreal/hc6_round1/`: the six named result JSONs, `configuration-verification.json`, `core-comparison.json`, `delivery-validation.json`, the Blueprint audit and `split-screen.png`. The screenshot shows both host views; its geometry is intentionally temporary. Earlier harness/authoring attempts are recorded separately and are not passing acceptance evidence.

## Integration status

Actual cave placement remains exclusively with the cave chat. No persistent map or `L_Site01_HC` was changed, and no integrated Round 1 success is claimed. PR #71, PR #74 and HC-4 carrying merged while this slice was being built. The branch was rebased onto `91a5195ec6d31060d4e28d02f2e068ac595cd0b1`, preserving those deliveries. Actor defaults now reference the prepared plate/gate meshes, two existing material tints and the delivered `BP_Statue` class. Those art, HUD, carrying and Core files remain untouched by this PR.

`L_Site01` passed a fresh-disk **Play As Client, 2-player** baseline smoke in the unattended editor: both owning controllers possessed Pawns and all worlds loaded GameState. The four HC6 actor counts were explicitly zero in every world, so this result does not claim an integrated plate puzzle. No Blueprint Runtime Error or Accessed None was found in the post-rebase runtime log. Saved actor status, reset interfaces and RepNotify settings also passed a read-only fresh-editor audit with no dirty packages.

This slice consumes the existing scaling contract; the fixture supplies the row only for verification. Production integration must confirm rows `2`, `3`, `4` are selected before starting Round 1. The global recovery system remains outside this slice.

The final saved-file audit uses a fresh editor. Core packages became dirty in memory during dependency processing, but their graphs matched the original readback and they were never saved. The dedicated editor was closed to discard that state. Raw Core, HUD, scaling-table and map hashes are checked against `origin/main`.

## Exact placement handoff

All coordinates below are **Unreal centimeters**, yaw/pitch/roll **0**, scale **(1,1,1)**. Place only in the cave chat's approved HC sublevel, never in the persistent map. The following are instructions for later placement, not saved placements in this PR.

| Actor | Location XYZ | Settings/tags |
| --- | --- | --- |
| Plate diamond | (3200, −800, 0) | `PlateSlot=0`, `RoundIndex=1`, Actor tag `HC_Round1` |
| Plate circle | (3200, 800, 0) | `PlateSlot=1`, `RoundIndex=1`, Actor tag `HC_Round1` |
| Plate triangle | (4800, −800, 0) | `PlateSlot=2`, `RoundIndex=1`, Actor tag `HC_Round1` |
| Plate cross | (4800, 800, 0) | `PlateSlot=3`, `RoundIndex=1`, Actor tag `HC_Round1` |
| Puzzle setup | (4000, 0, 0) | Exactly one; `RoundIndex=1`, `PuzzleTag=HC_Round1` |
| Start pad | (800, 0, 0) | `RoundIndex=1`, `HoldSeconds=3`; optional debug tag `HC_StartPad` |
| G1 | (2500, 0, 0) | `RoundIndex=0`, `OpenHeight=400`; optional debug tag `HC_G1` |
| G2 | (5500, 0, 0) | `RoundIndex=1`, `OpenHeight=400`; optional debug tag `HC_G2` |

Pressure-volume half extent is **(70,70,60)** at relative **(0,0,60)**. Start-volume half extent is **(250,250,100)** at relative **(0,0,100)**. Both generate overlaps with `OverlapAllDynamic`. The plate top uses `NoCollision`; the gate leaf uses `BlockAll`. All actors replicate and are always relevant, with net update frequency 20.

Set setup `StatueTransforms` to world transforms **(3500,1300,0)** and **(4000,1300,0)**, zero rotation, unit scale, in that order. These match PR #71's first two alcoves. The third alcove at (4500,1300,0) is unused by this slice. `StatueClass` now defaults to the delivered `/Game/Puzzles/BP_Statue.BP_Statue_C`, and remains configurable. That class must replicate and apply `HC_PlateWeight` on the server while heavy/free/placed, removing it while carried. This delivery does not modify its tag/carry logic or create a competing class. An unset class deliberately leaves setup unready. Fixtures continue to override the class with their own tagged test weight.

Set `PlateMesh` per slot to `/Game/Puzzles/Art/HCA2_Props/SM_PressurePlate_Top`, `_Circle`, `_Triangle`, `_Cross`. The default is the diamond top. Keep the prepared base mesh `SM_PressurePlate_Base` at the same world transform as a static base, without a plate-weight tag. `ReleasedMaterial` and `PressedMaterial` default to the existing `MI_HCA2_Stone` and `MI_HCA2_StoneCarving` tints; slot 0 is switched, with no imported-material edits. `GateMesh` defaults to `SM_ChamberGate_Leaf`; keep `SM_ChamberGate_Frame` at the same world transform as static art. Preserve the 4 m opening and upper-leaf pocket already described by #71. Remove the old art-only moving tops/leaves when replacing their placements, so there is only one moving surface. Static decorative statues must not duplicate the setup's spawned gameplay weights.

No placed actor references need to be assigned: only the plate tags/slots, mesh/material class references, gate round indices and setup's world-transform array. Validate the complete cave at 2/3/4 players and split-screen after the cave, carrying and Core prerequisites land; keep #11/#12 open until their complete acceptance passes.
