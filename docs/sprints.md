# Sprint plan: from an empty repo to the cave demo

Fifteen sprints take the team from an empty repo to **Demo 1**: the maze run through an underground cave, then a short trip to Map 2 for the results, played by 2–4 players online, with split-screen on the host. Sprints are 45 minutes, or 60 minutes when they end on a playable checkpoint. The plan fits five evenings, and each evening ends with a build everyone can join and play.

The first sprints build a small cave you can walk around in and keep improving with textures, items and traps. The maze run is built inside and around it after that. The direction behind this plan is in [design/direction-2026-10-10.md](design/direction-2026-10-10.md), which updates [design/direction-2026-10-09.md](design/direction-2026-10-09.md).

Each machine has its own lane and epic, and each epic phase is one sprint. For example, PG-4 is Mac 1's work in Sprint 4. Each epic also has numbered **asset** tasks, such as HZ-A1, which run alongside the build.

Every phase, asset task and checkpoint is also a [GitHub issue](https://github.com/StretchGaming/Co-op-Game/issues), grouped by [sprint milestone](https://github.com/StretchGaming/Co-op-Game/milestones). These docs say what to build; the issues say who's on it and how far along it is.

| Machine | Person | Lane | Epic |
| --- | --- | --- | --- |
| Windows (integrator + host) | Stretch | HC | [Core, puzzles and rounds](epics/epic-core-rounds.md) |
| Mac 1 | PK | PG | [Player view and ghosts](epics/epic-player-ghosts.md) |
| Mac 2 | Ak47 | HZ | [Cave, traps and atmosphere](epics/epic-cave-traps.md) |

All three lanes build against one map layout: [map/site01-layout.md](map/site01-layout.md). How assets are generated and imported: [assets.md](assets.md). Editor agent setup: [mcp.md](mcp.md).

## The demo

1. Up to four players spawn in a dim cavern lit by a shaft of daylight, torches and glowing crystals. Two of them can share the Windows screen. Everyone plays in first person and can switch to third person at any time.
2. **Round 1, the first room:** everyone stands on the start pad, and the mining puzzle starts. The team finds the pickaxe, breaks the boulders, loads their rocks into the mine cart and pushes it to the end of the track, and holds down the plates the boulders hid. That opens the gate into the first hallway.
3. **Round 2, the maze:** the team walks into the maze mouth, and something takes them one at a time, suddenly, until one player is left. Each player then crosses their own path alone: traps, ledges to climb, gaps to jump.
4. **Round 3, the meeting hall:** the paths meet. Together, the players light every lock at once with their headlamps and flares, and one door opens for each of them.
5. **Round 4, the deep maze:** each player takes their own door into a harder path, with stretches to sprint through and scares along the way.
6. **Round 5, the relic:** in the final chamber, players hold levers to raise the relic's cage while one of them lifts the relic.
7. **Round 6, the escape:** the relic's carrier moves slowly. Ghosts and cave beings chase the team down the zipline and back through the cave, and everyone protects the carrier with headlamps and flares. Placing the relic on the drop-off altar in the first room completes the mission.
8. Lethal damage kills players, and there are no revives. The dead watch a teammate and come back when the team regroups. When the whole team dies, the round restarts from its checkpoint.
9. Relics are scattered along the way. Small ones go straight into the team's count, and there are more of them with more players. After the mission, the run travels to Map 2, a small Egyptian antechamber, where the results show the relics collected.

## Sprints

| Sprint | Min | Windows · Stretch · HC | Mac 1 · PK · PG | Mac 2 · Ak47 · HZ | Ends with |
| --- | --- | --- | --- | --- | --- |
| 0. Setup | 60 | Create the project, plugins, settings and maps; push by minute 15. Stub the core contracts. | Open the project while shaders compile. Connect MCP and run the smoke test. | Open the project while shaders compile. Connect MCP. | **Playable 1** |
| 1. Foundations | 45 | Interaction with holds. Input contexts. Round state and debug keys. | First person with the switch to third person. | Cave blockout and the light it needs. `AC_Health` stub. | Smoke join |
| 2. Relics | 45 | Relics and the team count. Player colors and split-screen keys. Put PG's view on the real character. Travel test. | Split-screen on the host. Headlamp. | `AC_Health` working. Spike trap. | Smoke join |
| 3. Cave demo | 60 | Death integration. Team-wipe restart at the spawn checkpoint. | First ghost. | Dart trap. The first cave textures. | **Playable 2** |
| 4. Carrying | 45 | Carrying, the relic and statues. | Ghosts each round. Player colors applied. | Swinging trap. The trap corridor, timed for the relic's carrier. | Smoke join |
| 5. Rounds | 45 | The six rounds: triggers, gates and checkpoints, with a spot at each path start. Restarts, and the dead coming back when a round clears. | Ghosts back off from light. The dead watch a teammate. | The haunted hall on the way home. Fall volume. | Smoke join |
| 6. Into the maze | 60 | The first room: the start pad, Round 1's plates and the maze door. | The taking. | The maze route, built from the prototype maze. | **Playable 3** |
| 7. Paths | 45 | Map 2 and the run. | Climb, jump and sprint. The zipline. | The first paths: traps, climbs and gaps. | Smoke join |
| 8. Tools | 45 | HUD, results and restart, in the new UI kit. | Tools: flares and the headlamp. | The second paths: harder, with a collapsing bridge and a boulder. | Smoke join |
| 9. The relic | 60 | The meeting hall's locks. | The relic chamber. | The relic chamber and the escape route. | **Playable 4** |
| 10. The escape | 45 | The relic and the drop-off. | The chase. | Light, props and dressing. | Smoke join |
| 11. Restarts | 45 | Restarts across the whole run. | Split-screen and view polish. | Map 2. | Smoke join |
| 12. Full mission | 60 | Run every path; fix and tune. | Tune ghosts and the chase under network emulation. | Sound pass. Tune traps. | **Playable 5** |
| 13. Buffer | 45 | Fixes. Performance with split-screen on Windows. | Fixes. | Effects. Mac performance. | Smoke join |
| 14. Demo | 60 | Final fixes, tag `demo-1`. | Final fixes and feel. | Final fixes. | **Demo 1** |

That's 12 hours 45 minutes of sprints. With 10-minute breaks it fits five evenings, each ending on a checkpoint:

| Evening | Sprints | Time with breaks | Ends with |
| --- | --- | --- | --- |
| 1 | 0–3 | About 4 hours | Playable 2, the cave demo |
| 2 | 4–6 | About 2 hours 50 minutes | Playable 3, into the maze |
| 3 | 7–9 | About 2 hours 50 minutes | Playable 4, the relic |
| 4 | 10–12 | About 2 hours 50 minutes | Playable 5, the full mission |
| 5 | 13–14 | About 1 hour 55 minutes | Demo 1 |

A phase that runs over moves into the next sprint. Don't stretch a sprint to finish it; use the [cut list](#cut-list) instead. Sprint 13 is a planned buffer: if earlier phases slipped, it absorbs them; if not, it's for polish and performance.

After Demo 1: more maps (Map 2 beyond its antechamber, with camels in Egypt), split-screen on joining machines, tool slots and the Scout, and Epic Online Services sessions.

## Asset generation

Every lane generates or sources its own art, sound and UI, as separate tasks from its build work. Each asset task has two deliveries: **generated**, with the chosen candidate saved, and **in place**, imported, reviewed and swapped in for the greybox. Gameplay never waits on assets, and greybox stays until an asset passes review. The pipeline, specs, licensing rules and review steps are in [assets.md](assets.md).

PG-A0 sets up the pipeline and the shared style kit in Sprint 1, so other generation starts in Sprint 2. Every asset follows [art/style.md](art/style.md). Generation runs unattended, but choosing, cleaning up and importing take the same person's time, so early deliveries are small.

| Task | Owner | Generated by end of | In place by end of |
| --- | --- | --- | --- |
| PG-A0: pipeline and import presets | PG | Sprint 1 | Sprint 1 |
| HC-A1: relic set | HC | Sprint 2 | Sprint 3 |
| HZ-A1: cave surfaces | HZ | Sprint 2 | Sprint 3 |
| PG-A1: player colors | PG | Sprint 3 | Sprint 4 |
| PG-A2: ghost | PG | Sprint 4 | Sprint 5 |
| HC-A2: puzzle props | HC | Sprint 4 | Sprint 6 |
| HZ-A2: props and light sources | HZ | Sprint 4 | Sprint 6 |
| HZ-A3: trap meshes | HZ | Sprint 5 | Sprint 10 |
| HZ-A4: dressing | HZ | Sprint 6 | Sprint 10 |
| HZ-A7: maze climbing kit | HZ | Sprint 6 | Sprint 8 |
| PG-A3: ghost and taking sounds | PG | Sprint 6 | Sprint 8 |
| PG-A4: zipline | PG | Sprint 6 | Sprint 7 |
| HZ-A5: Map 2 kit | HZ | Sprint 6 | Sprint 11 |
| HC-A3: HUD art | HC | Sprint 7 | Sprint 8 |
| PG-A6: UI kit, type and depth | PG | Sprint 7 | Sprint 8 |
| PG-A7: the taker | PG | Sprint 7 | Sprint 9 |
| PG-A8: flare | PG | Sprint 7 | Sprint 8 |
| HC-A4: maze puzzle props | HC | Sprint 8 | Sprint 9 |
| PG-A5: bats and mice | PG | Sprint 8 | Sprint 8 |
| HZ-A6: cave and trap sounds | HZ | Sprint 8 | Sprint 12 |

**Minimum presentation kit.** These can't be cut, because checkpoints depend on them. If one isn't ready, use a free library asset from Fab that the repo's license rules allow, rather than greybox.

- Playable 2: HZ-A1 (cave surfaces), HC-A1 (relics), and HZ-1's and HZ-3's light.
- Demo 1: everything for Playable 2, plus HZ-A2 (props and light sources), PG-A2 (ghost), PG-A6 (UI kit), PG-A7 (the taker), HC-A2 (puzzle props), HZ-A5 (Map 2 kit) and HZ-A6 (cave and trap sounds).

Every other asset is optional: if it isn't ready, the greybox stays and nothing comes off a checkpoint.

## Playable checkpoints

Each checkpoint is a build anyone on the team can join and play. The times are sprint time from the start of Sprint 0, not counting breaks. A checkpoint only counts if it works for **clients**, not just the host. Test once with 2 players and once with 4; from Playable 2 on, the 4-player test includes a split-screen pair on the Windows machine. How to host and join: [README](../README.md#playtesting).

### Playable 1: Everyone's in (end of Sprint 0, about 1:00)

- Both Macs and a second Windows client join the Windows host, so the session holds 4 players.
- Everyone runs and jumps around the level's floor and sees the others move smoothly.

### Playable 2: The cave demo (end of Sprint 3, about 3:30)

- Walk the spawn cavern and the first chambers in first person. The cave has its first textures, lit by the daylight shaft, torches and crystals.
- Switch to third person and back. Turn your headlamp on and off; everyone sees it pointing where you look.
- A second player joins split-screen on the Windows machine with a gamepad while both Macs are online.
- Pick up relics and watch the team count go up.
- The spike and dart traps warn before they hit. Lethal damage kills you on every screen; you cannot move, interact or be revived, and ghosts ignore you.
- When the whole team dies, everyone restarts in the spawn cavern after 3 seconds, on separate spots. Test death independently for both local split-screen players.
- A ghost drifts through the walls after you.

### Playable 3: Into the maze (end of Sprint 6, about 6:00)

- Everyone stands on the start pad, and Round 1 starts. The mining puzzle opens the gate with 2 players and with 4 players, who face one more boulder and a cart that needs more rocks.
- The team walks into the maze mouth, and the door shuts behind them. Players are taken one at a time, each in a different way, until one is left. Everyone still there sees each person vanish, on every screen, including both halves of a split-screen pair.
- Each taken player comes to alone at the start of their own path. Everyone walks their own greybox path to the meeting hall, and the round clears when every living player is there.
- A player who dies on their path watches a teammate, and comes back in the meeting hall when the round clears. When the whole team dies, each player restarts at the start of their own path.
- More ghosts come with 4 players, and a headlamp drives one back.

### Playable 4: The relic (end of Sprint 9, about 8:30)

- Climb ledges, jump gaps and sprint across the first paths, past their traps.
- In the meeting hall, light every lock at once with headlamps and flares. One door opens for each player, and each player takes their own.
- The second paths are harder: a bridge that collapses behind you, a boulder, falling rocks.
- In the relic chamber, players hold the levers to raise the cage while one lifts the relic. This works with 2 players and with 4.
- The HUD shows the round's name and objective, the team's relics, who's alive, and your flares, in the new UI kit on every screen, including both split views.

### Playable 5: The full mission (end of Sprint 12, about 11:00)

- One run from the start pad to the drop-off, then into Map 2, where the results show the relics collected out of those available. No debug keys. Once with 2 players and once with 4, including a split-screen pair.
- The relic's carrier moves at half speed. Ghosts and cave beings chase the team home, going for the carrier first, and headlamps and flares hold them off. If the carrier dies, a teammate picks the relic up.
- The zipline, or the walkway, takes the team down from the relic chamber.
- The host restarts the run from the results screen, and every client reconnects.
- Every path was checked during Sprint 12: each round's restart, the dead coming back at each regroup, a player leaving mid-run, the escape's restart with the relic back on its pedestal, travel to Map 2, the results and the restart.

### Demo 1 (end of Sprint 14, about 12:45)

- The maze run is fun at 2, 3 and 4 players, with the minimum presentation kit in place: textured, lit and with sound.
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
| 0:45 | Playtest, 10 minutes. Run the checkpoint list above once with 2 players and once with 4. Look at the new assets in place; Stretch makes the [look check](art/style.md#look-check) on the host. |
| 0:55 | Retro, 5 minutes. Keep, cut or change. Use the cut list if a lane is behind. |

## Shared contracts

Lanes depend on each other only through these. **Stub by** is the sprint when the asset exists with its final names and inputs. **Works by** is when other lanes can rely on its behavior. Changing a contract after its stub needs a heads-up at kickoff.

Don't save hard references between placed actors in different sublevels; Unreal can't keep them. Find another lane's actors at runtime, through these contracts, the GameState or actor tags, and check that the reference is valid before you use it.

Two rules hold for every contract that changes state: the server decides, and anything that replicates from a component needs **Component Replicates** turned on.

| Contract | Owner | Stub by | Works by | What it is |
| --- | --- | --- | --- | --- |
| `Content/Core/BPI_Interactable` and `E_InteractMode` | HC | 0 | 1 | `GetInteractInfo(Instigator)` returns a prompt, a mode and a hold time. Modes: `Instant`, `Timed` (hold for the hold time) and `Continuous` (active while held). `CanInteract(Instigator)` returns a bool. On the server, the character calls `Interact(Instigator)` for an instant use or a completed hold, and `InteractBegin(Instigator)` and `InteractEnd(Instigator)` around a continuous one. |
| Interaction handling in `BP_CoopCharacter` | HC | 0 | 1 | The character sends the press and the release to the server. The server tracks the active use: it times holds itself, and ends or cancels a use when the button is released, the player moves out of range (4 m) or dies, the round resets, or the player leaves. |
| `Content/Core/BPI_RoundReset` | HC | 0 | 5 | `ResetForRound(Index, Attempt)`. When a round restarts, the server calls it on every actor that implements it, and each lane resets its own: plates, locks, doors, the relic and its cage, levers, carryables, ghosts and traps. Collected relics stay collected. |
| `Content/Core/BP_CoopCharacter` | HC | 0 | 1–8 | The player character, a child of the template character. Interaction works in Sprint 1, PG's `AC_PlayerView` in Sprint 2, `AC_Health` and death handling in Sprint 3, carrying with its own Drop key in Sprint 4, PG's `AC_Traversal` in Sprint 7 and PG's `AC_Tools` in Sprint 8. |
| `Content/Core/BP_CoopGameMode` | HC | 0 | See each function | The only place the round state changes. All server-only. `SetRoundPhase(Phase)` from Sprint 0. `StartRound(Index)` and `ClearRound()` from Sprint 1. `AddRelics(Count)` from Sprint 2. `CompleteMap()` from Sprint 2 as a plain travel to Map 2, and with the run's state from Sprint 7. Team-wipe checkpoint restart from Sprint 3. `FailRound()` from Sprint 5. From Sprint 5, the six rounds of the maze run: Rounds 3 and 5 start the next round as soon as they clear, a round fails when the living players can no longer finish it, and when a round clears, the players who died in it come back at the checkpoint where the team regroups. |
| `Content/Core/BP_CoopGameState` and `S_RoundState` | HC | 0 | 1 | `GetPlayerCount()` counts PlayerStates, including split-screen players. `RoundState` is one replicated struct: `Index` (1 to 6), `Phase`, `Attempt`, `PhaseEndsAt` (server time, 0 means no countdown) and `ScalingRow` (`2`, `3` or `4`). Its RepNotify fires `OnRoundStateChanged(State)` on the server and every client. Apply the current `RoundState` when you bind as well as when it changes, since a client can miss a short-lived phase. `RelicsCollected` and `RelicsAvailable`. |
| `Content/Core/BP_CoopGameInstance` | HC | 0 | 7 | Holds the run's state on the server across travel: relics collected and available. |
| `Content/Core/BP_CoopPlayerState` | HC | 0 | 2 | `ColorSlot` (0 to 3), replicated. The GameMode gives each player, including a split-screen player, the first free slot when they join. In the maze, a player's `ColorSlot` also picks their path when a round restarts. |
| `Content/Core/E_RoundPhase` | HC | 0 | 0 | `Lobby`, `Playing`, `Cleared`, `Failed`, `MapComplete`. Ghosts run only while the phase is `Playing`. |
| Debug and host keys in `BP_CoopPlayerController` | HC | — | 1, and F4–F6 in 2 | Debug, host only: F1 starts Round 1, F2 clears the round, F3 fails it, F4 completes the map. Host keys, not debug: F5 adds a split-screen player and F6 removes one, through PG's `BPFL_SplitScreen`. |
| Input contexts | HC for the character and controller, PG for the view, movement and tool keys | — | 1, and the new keys in 7 and 8 | Each pawn adds its own mapping context in Receive Controller Changed when a local player takes it, and removes only that context when the player leaves. Nobody calls Clear All Mappings. Controller-wide keys live in separate contexts that `BP_CoopPlayerController` adds once. HC adds `IA_Sprint` (Left Shift, or a left-stick click) in Sprint 7 and `IA_ThrowFlare` (Q, or the right bumper) in Sprint 8 to `IMC_Coop`, and forwards them to PG's components. |
| Round actors | HC | 3 | 5 | `BP_Checkpoint` holds four separate spawn spots; the spawn cavern's works from Sprint 3, and each round has its own from Sprint 5. In Rounds 2 and 4 the four spots are the four path starts, picked by `ColorSlot`. `BP_RoundStart` starts Rounds 1 and 2; Round 2's needs the whole team inside it. `BP_RegroupVolume` clears Rounds 2 and 4 when every living player is inside it. `BP_ChamberGate` opens when its round clears, or, for G1 to G3, when Round 6 starts. `BP_StartPad` starts Round 1. |
| `Content/Puzzles/BP_Relic` | HC | 2 | 2 | Adds its value to `RelicsCollected` when picked up. `MinPlayers` makes bonus relics appear only with more players; each relic that appears counts toward `RelicsAvailable`. |
| `Content/Puzzles/BP_Carryable` | HC | 4 | 4 | Picked up with Interact, put down with Drop. A replicated carry state (carrier, and free, carried or placed) applies the same collision on every machine. `bHeavy` halves the carrier's speed, stops them sprinting, climbing and throwing flares, and holds a pressure plate. `ReleaseCarried()` hands the item to whatever takes it, such as the drop-off altar. |
| `Content/Puzzles/BP_KeyRelic` | HC | 4 | 10 | The relic: a heavy carryable with the actor tag `Relic`, so ghosts can find its carrier. It can be lifted only while PG's cage is raised or latched. Its first lift in Round 5 calls `ClearRound()`, which starts Round 6. Placing it on the drop-off altar completes the mission and calls `CompleteMap()`. |
| `Content/Puzzles/BP_CrystalLock` and `BP_MazeDoor` | HC | 8 | 9 | The meeting hall's locks implement PG's `BPI_Lightable`. A headlamp lock is lit while a living player's headlamp rests on it; a brazier lock is lit while a burning flare is in its bowl. When every enabled lock is lit at once, the enabled doors open and Round 3 clears. A door closes behind the first player through it. Counts come from `DT_RoundScaling`. |
| `Content/Player/AC_PlayerView` | PG | 1 | 1 on PG's test character, 2 on the real one | `ApplyViewState()` sets the view from scratch, and runs at BeginPlay, on possession and on every change. `ToggleView()` switches between first and third person. `ToggleHeadlamp()`. `ApplyColorSlot()` from Sprint 4. From Sprint 5, while its owner is dead, the view follows a living teammate, and Interact switches to the next one. |
| `Content/Player/BPFL_SplitScreen` | PG | 1 | 2 | `AddLocalPlayer()` and `RemoveLocalPlayer()`, for the host machine only, in the `Lobby` and `Cleared` phases, up to 2 local players and 4 in total. |
| `Content/Player/Ghosts/BP_Ghost` | PG | 3 | 3 | Targets living players only (`IsDead()` is false) and damages them through `Apply Damage`. From Sprint 4, ghosts spawn when a round starts, scaled, and leave when it ends. From Sprint 10, ghosts in the escape go for the relic's carrier first. |
| `Content/Player/Taking/BP_TakingDirector` | PG | 5 | 6 | When Round 2 starts, takes every player but one, one at a time, on the server. Each taking replicates its victim and its server start time, so every machine plays the same scare from it. Once the scare covers the victim's screen, the server moves them to their spot at Round 2's checkpoint. Players can't be damaged while they're being taken. |
| `Content/Player/AC_Traversal` | PG | 6 | 7 | Sprinting, climbing up ledges, and climbing marked ropes, vines and handholds, to the measurements in the [layout doc](map/site01-layout.md#moving-through-the-maze). Speed and movement-mode changes go through the server and a RepNotify, the same way as the heavy carry's speed. A heavy carry turns sprinting and climbing off. |
| `Content/Player/Tools/AC_Tools`, `BP_Flare` and `BPI_Lightable` | PG | 7 | 8 | `FlaresLeft`, replicated. `ThrowFlare()` runs on the server and spawns a replicated `BP_Flare` that burns for `FlareSeconds`. Ghosts and cave beings won't enter its glow. Server-only `RestockFlares()` tops a player up to `FlaresPerPlayer`; the GameMode calls it when a round clears. On the server, a lit headlamp calls `BPI_Lightable`'s `LightBegin(Source)` and `LightEnd(Source)` on what its beam rests on, and a burning flare calls them on the brazier it lands in. |
| `Content/Player/RelicChamber/BP_Lever` and `BP_RelicCage` | PG | 6 | 9 | `BP_Lever` is a continuous interaction. The cage rises while every needed lever is held (`LeverCount`), and latches open once the relic leaves it. `IsRaised()` replicates, and HC's relic checks it before it can be lifted. |
| `Content/Player/Ghosts/BP_ChaseDirector` | PG | 9 | 10 | When Round 6 starts, sends waves of ghosts and cave beings along the escape route, scaled. They go for the relic's carrier first, and they leave when the mission completes or the round restarts. |
| `Content/Hazards/AC_Health` | HZ | 1 | 2 | Player health and death only, with Component Replicates on. `Health`, `MaxHealth`, `bDead` (RepNotify). `IsDead()` and server-only `ResetHealth()`. Lethal damage sets `bDead`; `OnDied` fires once on the server, cancels interactions and releases carried items and mechanisms. Dead players cannot move or interact, and damage cannot kill them again. No downed state or revive API. `ResetHealth()` restores full health and clears `bDead` only for a GameMode-controlled restart or regroup. Its RepNotify restores movement on every machine. Damage arrives through `Apply Damage` on the owner. |
| Trap schedules | HZ | 2 | 2–4 | Each trap replicates its schedule (a start time in server time plus its interval or speed) or the moment it was triggered, so every machine shows the warning before the server applies damage. The same goes for the collapsing bridge, the boulder and falling rocks. |
| `Content/Hazards/Maze/BP_MouthSeal` | HZ | 6 | 6 | Server-only `SealAllBut(PathIndex)`: a rockfall seals every path mouth at the maze's fork but one, on a replicated schedule. PG's taking calls it when the last taking ends. It implements `BPI_RoundReset`. |
| `Content/Hazards/FirstRoom/BP_MinePuzzle` | HZ | 6 | 6 | Round 1's mining puzzle. Its boulders sit on HC's `BP_PressurePlate`s (`PuzzleTag` `HZ_MinePlates`) and enable each plate once its rocks are lifted off. Its rocks are `BP_Carryable` children that hold a plate while they lie free. When the cart is at the end of its track and every enabled plate is pressed, while Round 1 is `Playing`, it calls the GameMode's `ClearRound()`, which opens the first room's `BP_ChamberGate`. Boulders in play and rocks needed come from `RoundState.ScalingRow`. Every piece implements `BPI_RoundReset` for Round 1. |
| Climbable volumes | HZ | 7 | 7 | A volume with the actor tag `Climbable` marks a climbing wall, rope or vines. PG's `AC_Traversal` climbs inside it. |
| Scaling tables | Each lane, in its own folder | HC 0, PG and HZ 1 | When first used | `DT_RoundScaling` (HC: `BeamLocks`, `FlareLocks`; `PlateCount` and `StatueCount` are no longer used, because the first room's counts live on HZ's `BP_MinePuzzle`), `DT_GhostScaling` (PG: `GhostCount`, `GhostSpeed`, `GhostDamage`, `LeverCount`, `ChaseWaveSize`, `ChaseWaveSeconds`, `FlaresPerPlayer`, `FlareSeconds`) and `DT_HazardScaling` (HZ: `SpikeDelay`, `DartInterval`, `SwingSpeed`), each with rows `2`, `3` and `4`. Look them up with `RoundState.ScalingRow`. In the `Lobby` phase, the server keeps the row in step with the player count; from Round 1, it changes only when a round starts. If a player leaves mid-round, the round restarts with the new count. Starting values are in [the direction](design/direction-2026-10-10.md#making-it-work-for-2-to-4-players). |
| Maps and sublevels | HC for persistent levels, each lane for its sublevel | 0 | 0 | `/Game/Maps/L_Site01`, the cave, with always-loaded `L_Site01_HC`, `L_Site01_PG` and `L_Site01_HZ`. `/Game/Maps/L_Site02`, Map 2: a bare level from Sprint 0 for travel tests, with `L_Site02_HZ` from Sprint 7 and its room from Sprint 11. Persistent levels hold only player starts and world settings, placed by HC under a lock. |
| `Content/Shared/UI/` UI kit | PG | 7 | 8 | Fonts, panel textures and materials for every widget, following [the HUD rules](art/style.md#hud-and-ui). HC's HUD, prompt and results use it from Sprint 8. |

## Cut list

If a lane falls behind, cut in this order rather than move a checkpoint. Each cut says what comes off the checkpoint lists with it.

1. Any asset outside the minimum presentation kit. The greybox stays, and nothing comes off a checkpoint.
2. The zipline. The team takes the walkway down from the relic chamber; "the zipline" comes off Playable 5.
3. Cave beings in the chase. Ghosts chase the team on their own.
4. The second paths' new traps: the collapsing bridge, the boulder and the falling rocks. The second paths use the first paths' traps, set closer together; they come off Playable 4.
5. The second lever at 4 players. The relic's cage uses one lever at every player count.
6. Sound beyond ambience, trap sounds and the taking.

Never cut joining at 2–4 players with a split-screen pair on the host, first person with the switch to third person, interact and carry, relics, death with no revives, regroups and team-wipe restarts, the first room, the taking, both sets of paths with climbing, jumping and sprinting, the meeting hall's locks, the relic chamber, the escape with ghosts chasing the carrier, headlamps and flares, the drop-off, travel to Map 2, or the minimum presentation kit.

## Risks

| Risk | What we do |
| --- | --- |
| The Macs' first open of the project takes a long time while shaders compile. | Sprint 0 is setup only for the Macs. Windows pushes the bare project by minute 15. |
| Mac clients can't join the Windows host, or travel between maps fails for them. | Playable 1 tests joining. F4's plain travel to Map 2 and back is tested from Sprint 2, long before the run depends on it. |
| Split-screen and Lumen together are too slow on the Windows host. | PG tests split-screen in Sprint 2, and HC-13 tunes scalability for split-screen. |
| A view, headlamp or trap looks different on each machine. | View state is applied from scratch on every machine, headlamps aim from the head on every machine, and traps replicate schedules instead of one-off events. |
| The maze run adds a lot of new work: the taking, climbing, tools, two sets of paths, two puzzles and a chase. | The maze already exists in the prototype, so HZ-6 starts from it. Each new piece is one phase, the cut list says what goes first, and Sprint 13 is a buffer. |
| The solo paths feel lonely, or a player who dies early waits a long time. | Paths are short, bridges and grates let players glimpse each other, the dead watch a teammate, and they come back as soon as the team regroups. |
| The taking looks wrong on clients: a player pops away before the scare plays, or lands in someone else's path. | The server schedules each taking like a trap, and every machine plays it from the same start time. The server moves a player only once the scare covers their screen. Test as a client under network emulation, and with a split-screen pair. |
| Climbing and sprinting cause movement corrections on clients. | Speed and movement-mode changes go through the server and a RepNotify, like the heavy carry's speed. Test them under network emulation from a Mac. |
| Assets break the license or bloat the repo. | The repo is public, so [assets.md](assets.md) only admits assets whose license allows publishing them, records each source, and commits only the chosen candidate. Fonts must use the SIL Open Font License or a similar license. |
| Generated assets are slow or off-style. | Assets are a parallel track that gameplay never waits on, with a minimum kit, library fallbacks and small early deliveries. Every asset starts from a style frame, goes through `M_Stylized` and is checked in `L_StyleTest`, and Stretch makes a look check at each playtest. |
| Epic's MCP tools can't wire Blueprint graphs. | The Sprint 0 smoke test records what they can do in [mcp.md](mcp.md). Agents scaffold assets, place actors and set properties; people wire the graphs. |
| Phases take longer than a sprint. | Each phase is sized for about 30 minutes, and Sprint 13 is a planned buffer before the demo. |
| The repo runs out of Git LFS storage or bandwidth. | Generated assets add up fast. Stretch, who owns the repo, checks its LFS usage on GitHub after the first evening. |
