# Sprint plan: from an empty repo to the cave demo

Ten sprints take the team from an empty repo to **Demo 1**: an underground cave with three puzzle rounds, then a short trip to Map 2, played by 2–4 players online, with split-screen on the host. Sprints are 45 minutes, or 60 minutes when they end on a playable checkpoint. The plan fits three evenings, and each evening ends with a build everyone can join and play.

The first sprints build a small cave you can walk around in and keep improving with textures, items and traps. The rounds are built inside it after that. The direction behind this plan is in [design/direction-2026-10-09.md](design/direction-2026-10-09.md).

Each machine has its own lane and epic, and each epic phase is one sprint. For example, PG-4 is Mac 1's work in Sprint 4. Each epic also has numbered **asset** tasks, such as HZ-A1, which run alongside the build.

| Machine | Person | Lane | Epic |
| --- | --- | --- | --- |
| Windows (integrator + host) | Stretch | HC | [Core, puzzles and rounds](epics/epic-core-rounds.md) |
| Mac 1 | PK | PG | [Player view and ghosts](epics/epic-player-ghosts.md) |
| Mac 2 | Ak47 | HZ | [Cave, traps and atmosphere](epics/epic-cave-traps.md) |

All three lanes build against one map layout: [map/site01-layout.md](map/site01-layout.md). How assets are generated and imported: [assets.md](assets.md). Editor agent setup: [mcp.md](mcp.md).

## The demo

1. Up to four players spawn in a dim cavern lit by a shaft of daylight, torches and glowing crystals. Two of them can share the Windows screen.
2. Everyone plays in first person and can switch to third person at any time. Headlamps light the dark passages.
3. Relics are scattered through the cave. Small ones go straight into the team's count; there are more of them with more players.
4. **Round 1, the plate hall:** pressure plates open the gate. Statues stand in for missing players, so the puzzle works with 2, 3 or 4.
5. **Round 2, the altar:** carry the heavy key relic out of a trapped side passage, down the trap corridor, and onto the altar.
6. **Round 3, the haunted gauntlet:** one or two players hold levers to keep a gate open while the others cross a dark hall of traps and ghosts, then open it from the far side.
7. Traps and ghosts knock players down, and a teammate holds Interact to revive them. If everyone is down at once, the round restarts from its entrance.
8. Players zipline out of the cave into Map 2, a small Egyptian antechamber, where the results show the relics collected.

## Sprints

| Sprint | Min | Windows · Stretch · HC | Mac 1 · PK · PG | Mac 2 · Ak47 · HZ | Ends with |
| --- | --- | --- | --- | --- | --- |
| 0. Setup | 60 | Create the project, plugins, settings, map and sublevels; push by minute 15. Stub the core contracts. | Open the project while shaders compile. Connect MCP and run the smoke test. | Open the project while shaders compile. Connect MCP. | **Playable 1** |
| 1. The cave | 45 | Interaction: trace, prompt, hold. Input contexts. Debug keys. | First person with the switch to third person. Headlamp. | Cave blockout. First light shading. `AC_Health` stub. | Smoke join |
| 2. Relics | 45 | Relics and the team count. Carry and drop. PG's view on the real character. | Split-screen on the host. | `AC_Health` working. Spike trap. Cave textures. | Smoke join |
| 3. Cave demo | 60 | Revive. The heavy key relic. | First ghost. | Dart trap. Second light pass, with props. | **Playable 2** |
| 4. Rounds | 45 | Round framework, chamber gates and the start pad. | Ghosts spawn each round, scaled. | Swinging trap. Dress chambers 1–3. | Smoke join |
| 5. Round 1 | 45 | Round 1: plates and statues. Restart when everyone is down. | Ghosts back off from light. | Round 2's trap corridor and key relic nook. | Smoke join |
| 6. Three rounds | 60 | Round 2: the altar. Round HUD. | Round 3: the haunted gauntlet. | Round 3's hall and traps. Fog, dust, drips. | **Playable 3** |
| 7. Map 2 | 45 | Travel to Map 2 with the run's relics. Results and restart. | Zipline out of the cave. | Map 2: the Egyptian antechamber. | Smoke join |
| 8. Full run | 60 | Run every path; fix and tune. | Tune ghosts, the views and split-screen. | Sound pass. Tune traps. | **Playable 4** |
| 9. Demo | 60 | Fixes, performance with split-screen on Windows, tag `demo-1`. | Fixes and feel. | Fixes, effects, Mac performance. | **Demo 1** |

That's 8 hours 45 minutes of sprints. With 10-minute breaks it fits three evenings, each ending on a checkpoint:

| Evening | Sprints | Time with breaks | Ends with |
| --- | --- | --- | --- |
| 1 | 0–3 | About 4 hours | Playable 2, the cave demo |
| 2 | 4–6 | About 2 hours 50 minutes | Playable 3, three rounds |
| 3 | 7–9 | About 3 hours 5 minutes | Demo 1 |

A phase that runs over moves into the next sprint. Don't stretch a sprint to finish it; use the [cut list](#cut-list) instead. If Playable 4 slips, add one 45-minute buffer sprint before the demo.

After Demo 1: more maps (Map 2 beyond its antechamber, with camels in Egypt), split-screen on joining machines, tool slots and the Scout, and Epic Online Services sessions.

## Asset generation

Every lane generates or sources its own art, sound and UI, as separate tasks from its build work. Assets come a sprint before they're needed, and gameplay never waits on them: greybox stays in place until an asset passes review. The pipeline, specs and review steps are in [assets.md](assets.md).

| Sprint | HC (Windows) | PG (Mac 1) | HZ (Mac 2) |
| --- | --- | --- | --- |
| 1 | HC-A1: relic set | PG-A0: pick the generator and prove the pipeline | HZ-A1: cave surfaces and a rock kit |
| 2 | — | PG-A1: player color variants | HZ-A2: cave props and light sources |
| 3 | HC-A2: puzzle props | PG-A2: ghost model and material | HZ-A3: spike and dart trap meshes |
| 4 | — | — | HZ-A4: swinging log and chamber dressing |
| 5 | HC-A3: HUD art | PG-A3: ghost sounds | — |
| 6 | — | PG-A4: zipline cable and handle | HZ-A5: Map 2 kit |
| 7 | — | — | HZ-A6: cave and trap sounds |

## Playable checkpoints

Each checkpoint is a build anyone on the team can join and play. The times are sprint time from the start of Sprint 0, not counting breaks. A checkpoint only counts if it works for **clients**, not just the host. Test once with 2 players and once with 4; from Playable 2 on, the 4-player test includes a split-screen pair on the Windows machine. How to host and join: [README](../README.md#playtesting).

### Playable 1: Everyone's in (end of Sprint 0, about 1:00)

- Both Macs and a second Windows client join the Windows host, so the session holds 4 players.
- Everyone runs and jumps around the level's floor and sees the others move smoothly.

### Playable 2: The cave demo (end of Sprint 3, about 3:30)

- Walk the spawn cavern and the first chambers in first person. The cave has its first textures and props, lit by the daylight shaft, torches and crystals.
- Switch to third person and back. Turn your headlamp on and off; everyone sees it.
- A second player joins split-screen on the Windows machine with a gamepad while both Macs are online.
- Pick up relics and watch the team count go up. Carry the key relic; it slows you down.
- The spike and dart traps knock you down, and a teammate holds Interact to revive you.
- A ghost drifts through the walls after you.

### Playable 3: Three rounds (end of Sprint 6, about 6:00)

- Everyone steps on the start pad, and the gate to Round 1 opens. The HUD shows the round and the relics.
- Round 1: the plates open the gate with 2 players using statues, and with 4 players facing more plates.
- Round 2: carry the key relic past the traps to the altar.
- Round 3: hold the levers while the others cross the haunted gauntlet, then open the gate from the far side.
- More ghosts come with 4 players, and headlamps drive them back.
- When everyone is down at once, the round restarts from its entrance.

### Playable 4: Full run (end of Sprint 8, about 7:45)

- One run from the start pad through all three rounds, out of the cave, and into Map 2, where the results show the relics collected. No debug keys. Once with 2 players and once with 4, including a split-screen pair.
- The host restarts the run from the results screen, and every client reconnects.
- Every path was checked during Sprint 8: each round's restart, the zipline or the walkway, travel to Map 2, and the results.

### Demo 1 (end of Sprint 9, about 8:45)

- The run is fun at 2, 3 and 4 players, textured, lit and with sound.
- The demo commit is tagged `demo-1`.

## Sprint rhythm

**45-minute sprint**

| Time | What happens |
| --- | --- |
| 0:00 | Kickoff, 3 minutes. Confirm your phase and asset task, name any locks you need, and log it in [SPRINT_LOG.md](../SPRINT_LOG.md). Start any asset generation now, since it runs while you build. |
| 0:03 | Build, 30 minutes. Commit small. Windows stops at 0:30 to get ready to merge. |
| 0:33 | The Macs push and release their locks. |
| 0:33 | Windows pulls, opens the editor, runs Play As Client with 2 players, pushes the merged commit and starts hosting. |
| 0:40 | Smoke join, 3 minutes. Everyone pulls and joins, and checks their own feature as a client. |
| 0:43 | Note what broke. Those fixes come first next sprint. |

**60-minute sprint, ending on a checkpoint**

| Time | What happens |
| --- | --- |
| 0:00 | Kickoff, 3 minutes. |
| 0:03 | Build, 35 minutes. Windows stops at 0:35. |
| 0:38 | The Macs push. Windows merges, checks and starts hosting. |
| 0:45 | Playtest, 10 minutes. Run the checkpoint list above once with 2 players and once with 4. Look at the new assets in place. |
| 0:55 | Retro, 5 minutes. Keep, cut or change. Use the cut list if a lane is behind. |

## Shared contracts

Lanes depend on each other only through these. **Stub by** is the sprint when the asset exists with its final names and inputs. **Works by** is when other lanes can rely on its behavior. Changing a contract after its stub needs a heads-up at kickoff.

Don't save hard references between placed actors in different sublevels; Unreal can't keep them. Find another lane's actors at runtime, through these contracts, the GameState or actor tags, and check that the reference is valid before you use it.

| Contract | Owner | Stub by | Works by | What it is |
| --- | --- | --- | --- | --- |
| `Content/Core/BPI_Interactable` | HC | 0 | 1 | `GetInteractInfo(Instigator)` returns a prompt and a hold time in seconds (0 means instant). `CanInteract(Instigator)` returns a bool. `Interact(Instigator)` runs on the server only, after the server rechecks distance and `CanInteract`. |
| `Content/Core/BP_CoopCharacter` | HC | 0 | 1–3 | The player character, a child of the template character. The interact trace works in Sprint 1. Carrying, `GetCarried()` and `ReleaseCarried()` work in Sprint 2, along with PG's `AC_PlayerView` and the view and headlamp keys. `AC_Health` and revive work in Sprint 3. |
| `Content/Core/BP_CoopGameMode` | HC | 0 | See each function | A child of GameMode, not GameModeBase, and the only place the round phase changes. All server-only. `SetRoundPhase(Phase)` works from Sprint 0. `StartRound(Index)` and `ClearRound()` from Sprint 1. `AddRelics(Count)` from Sprint 2. `FailRound()` from Sprint 5. `CompleteMap()` from Sprint 7. |
| `Content/Core/BP_CoopGameState` | HC | 0 | 0 | A child of GameState. `GetPlayerCount()` counts PlayerStates, including split-screen players. `GetScalingRow()` returns the row name `2`, `3` or `4`; a solo test uses `2`. `RoundIndex`. `RoundPhase` (RepNotify) fires `OnRoundPhaseChanged(NewPhase)` on the server and every client. `PhaseEndsAt` in server time (0 means no countdown). `RelicsCollected`. |
| `Content/Core/E_RoundPhase` | HC | 0 | 0 | `Lobby`, `Playing`, `Cleared`, `Failed`, `MapComplete`. Ghosts and round-specific hazards run only while the phase is `Playing`. |
| Debug and host keys in `BP_CoopPlayerController` | HC | — | 1, and F5–F6 in 2 | Debug, host only: F1 starts Round 1, F2 clears the round, F3 fails it, F4 completes the map. Host keys, not debug: F5 adds a split-screen player and F6 removes one, through PG's `BPFL_SplitScreen`. |
| Input contexts | HC for the character and controller, PG for the view keys | — | 1 | Each pawn adds its own mapping context in Receive Controller Changed when a local player takes it, and removes only that context when the player leaves. Nobody calls Clear All Mappings. Controller-wide keys live in separate contexts that `BP_CoopPlayerController` adds once. |
| Round actors | HC | 4 | 4 | `BP_RoundStart` at each chamber entrance calls `StartRound(N)`. `BP_ChamberGate` opens when its round is cleared. `BP_RespawnPoint` marks where a failed round restarts. Puzzle actors reset when their round starts again. |
| `Content/Puzzles/BP_Relic` and `BP_Carryable` | HC | 2 | 2 | A relic adds its value to `RelicsCollected` when picked up. Each relic has `MinPlayers`, so bonus relics only appear with more players. Carryables are picked up, carried and dropped; `bHeavy` halves the carrier's speed and holds a pressure plate. |
| `Content/Player/AC_PlayerView` | PG | 1 | 1 on PG's test character, 2 on the real one | First person by default. `ToggleView()` glides to third person and back, changing the field of view. `ToggleHeadlamp()`. The view mode and headlamp replicate, so every machine shows them the same way. |
| `Content/Player/BPFL_SplitScreen` | PG | 2 | 2 | `AddLocalPlayer()` and `RemoveLocalPlayer()`, for the host machine. |
| `Content/Player/Ghosts/BP_Ghost` | PG | 3 | 3 | Damages players through `Apply Damage`. From Sprint 4, ghosts spawn when a round starts, scaled by `DT_GhostScaling`, and leave when it ends. |
| `Content/Hazards/AC_Health` | HZ | 1 | 2 | Player health only. `Health`, `MaxHealth`, `bDowned` (RepNotify). `IsDowned()`, `CanBeRevived()`, and server-only `Revive(Reviver)` and `ForceDown(bAllowRevive)`. `OnDowned` and `OnRevived` fire on the server. Damage arrives through `Apply Damage` on the owner. |
| Scaling tables | Each lane, in its own folder | HC 0, PG and HZ 1 | When first used | `DT_RoundScaling` (HC), `DT_GhostScaling` (PG) and `DT_HazardScaling` (HZ), each with rows `2`, `3` and `4`, looked up with `GetScalingRow()`. Read them when a round starts, never at BeginPlay, when the host may still be alone. |
| Maps and sublevels | HC for persistent levels, each lane for its sublevel | 0, and Map 2 in 7 | 0 | `/Game/Maps/L_Site01`, the cave, with always-loaded `L_Site01_HC`, `L_Site01_PG` and `L_Site01_HZ`. `/Game/Maps/L_Site02`, Map 2, with `L_Site02_HZ`. Persistent levels hold only player starts, the map exit and world settings, placed by HC under a lock. |

## Cut list

If a lane falls behind, cut in this order rather than move a checkpoint. Each cut says what comes off the checkpoint lists with it.

1. Any asset that isn't ready. The greybox stays, and nothing comes off a checkpoint.
2. The zipline. Players take the walkway down instead.
3. Ghosts backing off from light. Ghosts still chase; "headlamps drive them back" comes off Playable 3.
4. The second lever at 4 players. Round 3 uses one lever at every player count.
5. Sound beyond ambience and trap sounds.

Never cut joining at 2–4 players with a split-screen pair on the host, first person with the switch to third person, interact and carry, relics, knockdown and revive, the three rounds and their restarts, at least one ghost, or travel to Map 2.

## Risks

| Risk | What we do |
| --- | --- |
| The Macs' first open of the project takes a long time while shaders compile. | Sprint 0 is setup only for the Macs. Windows pushes the bare project by minute 15. |
| Mac clients can't join the Windows host. | Playable 1 tests it first. Check the same engine version and commit, the Windows firewall, and UDP port 7777. See the [README](../README.md#playtesting). |
| Split-screen and Lumen together are too slow on the Windows host. | PG tests split-screen in Sprint 2, and HC-9 tunes scalability for split-screen. The cave's darkness helps: fewer lights in view. |
| The view mode looks different on each machine. | `AC_PlayerView` replicates the mode and applies the character's rotation settings everywhere. PG tests it as a client. |
| Generated assets are slow, off-style or unlicensed. | Assets are a parallel track that gameplay never waits on, PG-A0 picks one pipeline in Sprint 1, and every asset records its source and license. |
| Epic's MCP tools can't wire Blueprint graphs. | The Sprint 0 smoke test records what they can do in [mcp.md](mcp.md). Agents scaffold assets, place actors and set properties; people wire the graphs. |
| The org runs out of Git LFS storage or bandwidth. | Generated assets add up fast. Check the org's LFS usage on GitHub after the first evening. |
