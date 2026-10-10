# Epic: Core, puzzles and rounds (HC)

**Machine:** Windows · **Owner:** Stretch · **Role:** integrator and host · **Folder:** `Content/Puzzles/`, plus `Content/Core/` and `Content/Maps/` · **Sublevel:** `L_Site01_HC`

## Relationship to other epics (read first)

This lane owns the shared core: the GameMode, GameState, GameInstance, player character, controller and state, project settings, and the maps' persistent levels. It also owns interaction, relics, carrying, death integration, regroups and checkpoint restarts, the six rounds of the maze run, the first room's puzzle, the meeting hall's locks, the relic and the drop-off, and travel between maps. [PG](epic-player-ghosts.md) adds the player's view, split-screen, sprinting and climbing, the headlamp and flares, the ghosts, the taking, the relic chamber's cage and the chase. [HZ](epic-cave-traps.md) builds the cave, the maze, the traps and the atmosphere. The sprint table, checkpoints and full contract list are in [docs/sprints.md](../sprints.md), room positions in [docs/map/site01-layout.md](../map/site01-layout.md), the asset pipeline in [docs/assets.md](../assets.md), and the design direction in [docs/design/direction-2026-10-10.md](../design/direction-2026-10-10.md).

## Context

The Windows machine merges everyone's work and hosts every playtest, including the split-screen pair. It also makes the final call on visuals and performance. So this lane stops building a few minutes before the others each sprint, and each phase is sized for about 25 minutes.

HC covers what players do with their hands: interact, collect relics, carry things, solve the first room and the meeting hall's locks, carry the relic home to the drop-off, regroup and restart, and move through the rounds and into the next map.

## Locked decisions

- Unreal Engine **5.8.3**, Blueprint-only, made from the Third Person template. Its full-body character carries both the first- and third-person views. The project is named `CoopGame`.
- Maps don't use World Partition. Each map has a persistent level, which HC owns, plus one always-loaded sublevel per lane.
- `BP_CoopGameMode` and `BP_CoopGameState` are children of **GameMode** and **GameState**, not the Base versions.
- Max players is 4, counting split-screen players. Scaling goes through `RoundState.ScalingRow`, which the server keeps in step with the player count in the lobby and locks when a round starts.
- The round state replicates as one struct, so clients never see a round number from one round and a phase from another.
- Interaction has three modes: instant, timed and continuous. The server times holds itself and ends them on release.
- The maze run is six rounds: the first room, the maze, the meeting hall, the deep maze, the relic and the escape. From Round 2 on, each round starts as soon as the one before clears. Each round has a checkpoint; in Rounds 2 and 4, each player's spot is the start of their own path.
- Lethal damage kills players immediately; there is no downed state or teammate revive. Dead players cannot move, interact, carry items or hold mechanisms. They come back when the round clears, at the checkpoint where the team regroups, and never sooner. When the whole team is dead, or the living players can no longer finish the round, the round restarts from its checkpoint with everyone alive.
- Small relics go straight into the team's count. The relic at the end of the maze is heavy and has to be carried home. Collected relics stay collected through restarts.
- Puzzles use stand-ins: a statue holds a pressure plate as well as a player does, and a flare lights a brazier lock without anyone standing there.
- Only the GameMode changes the round state. The run's progress lives on the server, in the GameInstance, across travel.
- Each pawn adds and removes its own input mapping context.
- Split-screen-safe from day one: no player index 0, HUD widgets on the owning player's screen, input per local player.

## Non-goals (for Demo 1)

- Tool slots, roles and the Scout. Every player carries the same tools.
- Split-screen on joining machines, Epic Online Services sessions, menus beyond the results screen, and save data.
- More of Map 2 than its antechamber.

## Dependencies and sequencing

- HC-0 blocks everyone, because the Macs can't open anything until the bare project is pushed. Push it by minute 15.
- HC-2 puts PG-1's `AC_PlayerView` on the real character and wires F5 and F6 to PG's `BPFL_SplitScreen`, whose stub PG publishes in Sprint 1.
- HC-3 needs HZ-2's `AC_Health`. That's a hard gate for Playable 2: if it isn't merged by the end of Sprint 2, HZ finishes it first thing in Sprint 3.
- HC-6 places Round 1 in the first room at the spots HZ-6 marks, and Round 2's start just inside the maze door, where PG-6's taking begins.
- HC-7 puts PG-7's `AC_Traversal` on the character and forwards `IA_Sprint`. HC-8 puts PG-8's `AC_Tools` on it, forwards `IA_ThrowFlare`, and builds the HUD from PG-A6's UI kit.
- HC-9's locks need PG-8's `BPI_Lightable`, flares and headlamp, and HZ-6's meeting hall.
- HC-10's relic needs PG-9's cage, and its drop-off needs HZ-9's escape route to be walkable.

## Phases

### HC-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, install Unreal 5.8.3 and Git LFS on the Windows machine and clone the repo.

**First 15 minutes: the bare project.**

- Create `CoopGame` outside the repo from the Third Person template: Blueprint, no starter content. Close the editor, move `CoopGame.uproject`, `Config/` and `Content/` into the repo root, and reopen it from there.
- Enable the plugins **Unreal MCP**, **All Toolsets** and **Python Editor Script Plugin**, then restart.
- Project Settings, Maps & Modes: set the editor and game default maps to `L_Site01`. Under Local Multiplayer, turn on **Use Splitscreen** and **Skip Assigning Gamepad to Player 1**, so the host plays on keyboard and mouse and the first gamepad becomes player 2.
- Config files, which are text:
  - `Config/DefaultEngine.ini`: `AspectRatioAxisConstraint=AspectRatio_MaintainYFOV` under `[/Script/Engine.LocalPlayer]`, so split views keep their vertical field of view.
  - `Config/DefaultGame.ini`: `MaxPlayers=4` under `[/Script/Engine.GameSession]`.
- Create `/Game/Maps/L_Site01` with File → New Level → **Basic**, which has no World Partition. In the Levels panel, create three sublevels: `/Game/Puzzles/L_Site01_HC`, `/Game/Player/L_Site01_PG` and `/Game/Hazards/L_Site01_HZ`. Set each one to **Always Loaded**.
- Move the Basic level's floor, sun, sky, sky light and fog into `L_Site01_HZ`, because HZ owns the cave and its light; the floor carries Playable 1. Add 4 player starts in the spawn cavern, at the positions in the layout doc, to the persistent level.
- Create `/Game/Maps/L_Site02` as an empty **Basic** level with 4 player starts, for travel tests.
- In the editor console, run `ModelContextProtocol.GenerateClientConfig ClaudeCode` to write `.mcp.json` to the repo root. Commit and push.

**Next 20 minutes: the contracts.** Create every Sprint 0 contract in the contracts table, with final names and inputs and empty logic. Make `BP_CoopCharacter` first, since PG needs it in Sprint 1.

- `BP_CoopCharacter` (a child of the template character), `BP_CoopPlayerController`, and `BP_CoopPlayerState` with `ColorSlot`.
- `BP_CoopGameState` with `S_RoundState` (`Index`, `Phase`, `Attempt`, `PhaseEndsAt`, `ScalingRow`) as `RoundState`, replicated with a RepNotify that fires `OnRoundStateChanged`, plus `GetPlayerCount()`, `RelicsCollected` and `RelicsAvailable`.
- `BP_CoopGameMode`, with `SetRoundPhase` working and the rest as stubs. `BP_CoopGameInstance`, set as the Game Instance Class under Project Settings → Maps & Modes.
- `BPI_Interactable` with `E_InteractMode`, `BPI_RoundReset`, `E_RoundPhase`, and `S_RoundScaling` with `DT_RoundScaling` (rows `2`, `3`, `4`: `PlateCount`, `StatueCount`).
- Set `BP_CoopGameMode` as the project's default GameMode, using the other classes.

If the contracts run over, finish them first thing in Sprint 1. Push, then host Playable 1 for the last 15 minutes.

### HC-1: Interaction and round state (Sprint 1, 45 min)

- If HC-0 used the earlier heist names or separate `RoundIndex` and `RoundPhase` variables, move them to the HC-0 names and the `RoundState` struct first.
- `IMC_Coop` in `Content/Core/Input/`: a copy of the template's default mapping context, plus `IA_Interact` (E, or the gamepad's bottom face button), `IA_Drop` (G, or the right face button), `IA_ToggleView` (V, or a right-stick click) and `IA_Headlamp` (F, or d-pad up). The character adds `IMC_Coop` in Receive Controller Changed when a local player takes it, and removes it when they leave, instead of the template's BeginPlay.
- Interaction on the character:
  - On the owning client, a short sphere trace from the camera about every 0.1 seconds shows `WBP_InteractPrompt` on the owning player's screen when it finds a target whose `CanInteract` is true.
  - `IA_Interact`'s Started event sends `Server_InteractBegin(Target)`. Completed and Canceled send `Server_InteractEnd`.
  - The server keeps the active use. Instant: call `Interact` now. Timed: after the hold time, if the use is still active, call `Interact`. Continuous: call `InteractBegin` now and `InteractEnd` when it stops.
  - The server ends or cancels the use when the button is released, the target goes out of range (4 m, checked 5 times a second) or stops passing `CanInteract`, the player dies, the round resets, or the player leaves.
  - The client shows a simple progress bar during a timed hold.
- `StartRound(Index)`, `ClearRound()` and `SetRoundPhase` work. They only change `RoundState`, so F1 to F3 are useful to the other lanes straight away.
- `IMC_Debug`, which `BP_CoopPlayerController` adds once on the host: F1 starts Round 1, F2 clears the round, F3 fails it and F4 completes the map.
- `BP_TestInteractable` in `Content/Puzzles/Test/`, with one test actor per mode, for the other lanes to test against.

### HC-2: Relics, colors and the split-screen keys (Sprint 2, 45 min)

- `BP_Relic`: an instant interaction. On the server it calls `AddRelics(Value)`, which now works, then hides the relic and turns off its collision. The pickup sound plays through an unreliable multicast. `MinPlayers` (2, 3 or 4) keeps bonus relics hidden when there are fewer players; every relic that's shown counts toward `RelicsAvailable`.
- `WBP_RelicCounter`: a small counter on each owning player's screen. The round HUD replaces it in HC-8.
- Lobby scaling: in the `Lobby` phase, the GameMode updates `RoundState.ScalingRow` whenever a player joins or leaves. From Round 1 it changes only when a round starts.
- Colors: the GameMode gives each joining player, including a split-screen player, the first free `ColorSlot` from 0 to 3.
- Put PG's `AC_PlayerView` on `BP_CoopCharacter` and forward `IA_ToggleView` and `IA_Headlamp` to it. Tell PG to remove it from their test character. Wire F5 and F6 in `IMC_Host` to `BPFL_SplitScreen`.
- Travel test: `CompleteMap()` runs the console command `ServerTravel /Game/Maps/L_Site02?listen` (non-seamless), and F4 triggers it. A second press of F4 in Map 2 travels back to `L_Site01`. Check that both Macs and a split-screen player follow.
- Place the spawn cavern's tutorial relics.

### HC-3: Death and checkpoint restarts (Sprint 3, 60 min) → Playable 2

- Add `AC_Health` to `BP_CoopCharacter`, and tell HZ to remove it from their test character. Bind server-side `OnDied` to cancel the character's active interaction and release any held mechanisms; from HC-4, also call `DropCarried()`. Deny interaction when `IsDead()` is true. Player characters have no revive interaction.
- `BP_Checkpoint` with four spawn spots, so players don't land on each other. Put one in the spawn cavern, and make it the latest checkpoint.
- Team-wipe restart, in any phase: when every connected player is dead, including both local split-screen players, the GameMode waits 3 seconds, moves each player to their own spot at the latest checkpoint and calls `AC_Health.ResetHealth()` on everyone. Dead players never respawn individually. In Sprint 5 this grows into the round restart and the regroup.
- Host Playable 2, including a split-screen player on the Windows machine.

### HC-4: Carrying (Sprint 4, 45 min)

- `BP_Carryable`: the physics mesh is the root component, with Replicates and Replicate Movement on. Picking up is an instant interaction. On the server it turns physics off and attaches the item to a carry point on the character.
- Its replicated carry state holds the carrier and whether it's free, carried or placed. Its RepNotify applies the matching collision on every machine, so a carried item never blocks its carrier or anyone else.
- `IA_Drop` drops what you're carrying: detach, restore collision, turn physics back on, and give it a small push forward. Interact never drops, so using an altar while carrying works. `GetCarried()` returns the item, and `ReleaseCarried()` hands it to whatever takes it without turning physics on.
- A `bHeavy` carryable halves the carrier's speed. Set the speed through a RepNotify so the server and the owning client agree; otherwise the client stutters from movement corrections. PG's sprinting, climbing and flares check it too.
- `BP_KeyRelic` (heavy), the relic at the end of the maze, and `BP_Statue` (heavy). Test the relic in `L_HC_Test`; HC-10 places it. A player who dies drops what they're carrying through the server-side `AC_Health.OnDied` binding.
- Test pick up, drop and pick up again, and pick up after a client joins late.

### HC-5: The six rounds, regroups and restarts (Sprint 5, 45 min)

- The round list for the maze run, with each round's name and objective for the HUD: 1 the first room, 2 the maze, 3 the meeting hall, 4 the deep maze, 5 the relic, 6 the escape. From Round 2 on, the GameMode starts each round as soon as the one before clears.
- `BP_StartPad` starts Round 1. `BP_RoundStart` starts Round 2 when every living player is inside it. `BP_RegroupVolume` clears Rounds 2 and 4 when every living player is inside it. Starting a round makes that round's `BP_Checkpoint` the latest.
- `BP_Checkpoint` spots can sit far apart: in Rounds 2 and 4, the four spots are the four path starts, and `ColorSlot` picks each player's spot.
- `BP_ChamberGate` opens when its round clears. G1, G2 and G3 open when Round 6 starts.
- `FailRound()` works. The phase becomes `Failed` when the whole team is dead during `Playing`, or when the living players can no longer finish the round: each puzzle actor reports how many living players it needs. After 3 seconds, the checkpoint restart from HC-3 runs at the round's checkpoint, the GameMode calls `BPI_RoundReset.ResetForRound(Index, Attempt + 1)` on every actor that implements it, and the round starts again with the next `Attempt`.
- The regroup: when a round clears, every player who died in it comes back at the next round's checkpoint. The GameMode calls `ResetHealth()` and moves them to a free spot, and from Sprint 8 calls PG's `RestockFlares()` on everyone.
- If a player leaves during a round, restart it the same way, so the puzzles and paths match the new player count.
- Every HC puzzle actor implements `BPI_RoundReset`. Carryables go back to where they started.

### HC-6: The first room (Sprint 6, 60 min) → Playable 3

- Round 1 in the first room: place `BP_StartPad`, the four `BP_PressurePlate`s and `BP_PuzzleSetup` with its statue spots at the positions HZ-6 marks in the spawn cavern. The plate puzzle's logic doesn't change: `BP_PressurePlate` counts living players and heavy carryables on the server, and when every enabled plate is pressed, the round clears. Starting values: 2 players get 3 plates and 2 statues; 3 players get 3 and 1; 4 players get 4 and 1. A restart removes and respawns the statues.
- The maze door, a `BP_ChamberGate` in the first room's north wall, opens when Round 1 clears.
- Round 2's `BP_RoundStart` just inside the maze door. When every living player is inside, it starts Round 2, the maze door shuts behind them, and PG's taking begins. Round 2's checkpoint, with its spots at the four path starts.
- `BP_RegroupVolume` in the meeting hall, which clears Round 2.
- Host Playable 3.

### HC-7: Map 2 and the run (Sprint 7, 45 min)

- `CompleteMap()` now saves `RelicsCollected` and `RelicsAvailable` in `BP_CoopGameInstance` before traveling. On arrival, the GameMode restores them into the GameState. Until HC-10's drop-off calls it, F4 triggers it.
- Bring `L_Site02_HZ` into `L_Site02` as an always-loaded sublevel.
- After travel, check that each player's HUD and input come back once, through the normal possession and BeginPlay paths, and that no extra split-screen players appear.
- Put PG's `AC_Traversal` on `BP_CoopCharacter`, add `IA_Sprint` (Left Shift, or a left-stick click) to `IMC_Coop` and forward it. Tell PG to remove the component from their test character.

### HC-8: HUD, results and restart (Sprint 8, 45 min)

- `WBP_RoundHUD` on each owning player's screen, built from PG-A6's UI kit and following [the HUD rules](../art/style.md#hud-and-ui). It shows:
  - The round's name and objective: large when a round starts or clears, then one small line.
  - The team's relics.
  - The team: each player's color, and whether they're alive, dead or carrying the relic.
  - Your tools: the headlamp, and the flares left from PG's `AC_Tools`.
  - The interact prompt and its hold bar.
  - While you're dead, whose view you're watching, and that you'll be back when the team regroups.
- It reads `RoundState` when it's created as well as on change. Restyle `WBP_InteractPrompt` and the results the same way.
- `WBP_Results` in Map 2 shows the relics collected out of those available.
- The host presses R to start a new run: reset the run's state in the GameInstance, then `ServerTravel /Game/Maps/L_Site01?listen`.
- Put PG's `AC_Tools` on `BP_CoopCharacter`, add `IA_ThrowFlare` (Q, or the right bumper) to `IMC_Coop` and forward it.

### HC-9: The meeting hall's locks (Sprint 9, 60 min) → Playable 4

- `BP_CrystalLock`, which implements PG's `BPI_Lightable`. A headlamp lock is lit while a living player's headlamp rests on it, so someone has to hold their aim. A brazier lock is lit while a burning flare is in its bowl. A lock glows when it's lit, on every machine.
- `BP_MazeDoor`, four of them around the meeting hall, one into each second path. When every enabled lock is lit at the same moment, the enabled doors open and latch, and Round 3 clears. A door drops shut behind the first player through it, so each player takes their own.
- Scaling: `BeamLocks` and `FlareLocks` in `DT_RoundScaling`. Starting values: 2 players get 1 headlamp lock and 1 brazier lock; 3 players get 2 and 1; 4 players get 2 and 2. The number of doors that open matches the player count.
- Place the locks on perches you have to climb to see, at the spots HZ-6 marks. Round 4's checkpoint, with its spots just past each door, and the `BP_RegroupVolume` in the relic chamber that clears Round 4.
- The locks and doors implement `BPI_RoundReset`. The locks report the living players they need: one, since flares stand in for missing players.
- Host Playable 4.

### HC-10: The relic and the drop-off (Sprint 10, 45 min)

- Place `BP_KeyRelic` on its pedestal inside PG's cage in the relic chamber. It can be lifted only while the cage is raised or latched. Its first lift in Round 5 calls `ClearRound()`, which starts Round 6, the escape.
- The carrier moves at half speed and can't sprint, climb or throw flares. A carrier who dies drops the relic, and any living player can lift it.
- The drop-off: move the delivered `BP_Altar` into the first room, against the west wall. Using it while carrying the relic is one server step: release the relic from the carrier, set it to placed on the altar, and complete the mission. The phase becomes `MapComplete`, and after a 5-second moment for the team, `CompleteMap()` travels to Map 2.
- When Round 6 restarts, the relic goes back on its pedestal with the cage latched open, so the levers don't have to be done again.
- The altar's round check moves from Round 2 to Round 6. Remove the old Round 2 altar placement from chamber 2.
- The haunted gauntlet's start, coordinator, gate bridge and objective in `Content/Puzzles/Gauntlet/` retire: the relic's first lift replaces the far-side objective, and PG's cage latches open by itself.

### HC-11: Restarts across the run (Sprint 11, 45 min)

- Check each round's team-wipe restart at 2, 3 and 4 players, including both split-screen players. Each player lands on their own spot, and in Rounds 2 and 4 at the start of their own path. Round 2's restart doesn't replay the taking.
- Check the regroup after every round: the dead come back where the team is gathering, with full health and their flares restocked.
- Check that a round fails when the living players can no longer finish it, such as a single survivor in the relic chamber with 2 players.
- A player who leaves mid-run restarts the round with the new count: paths, plates, locks, doors and levers follow it. A player who joins mid-run waits like a dead player and comes in at the next regroup.
- Log each result in the sprint log.

### HC-12: Full run (Sprint 12, 60 min) → Playable 5

- In the build window, play every path as a client and fix what breaks: each round's restart and regroup, the taking, both sets of paths, both puzzles, the escape and its restart, the zipline and the walkway, travel to Map 2, the results and the restart. Check that the split-screen pair survives travel both ways. Log each result in the sprint log.
- Tune `DT_RoundScaling` and the relic placement from the 2-player and 4-player runs.
- Host Playable 5.

### HC-13: Buffer and performance (Sprint 13, 45 min)

- Finish whatever earlier phases left behind.
- Windows performance pass with 4 players, including the split-screen pair, using `stat fps` and `stat unit` on the host. Aim for 60 fps in each split view; if it's lower, add a split-screen scalability preset rather than cutting lights.

### HC-14: Demo (Sprint 14, 60 min) → Demo 1

- Final fixes.
- Tag the commit `demo-1` and push the tag. Host the demo with 2, 3 and 4 players.

## Asset generation

Follow [docs/assets.md](../assets.md) for specs, licensing, imports and reviews. Raw output goes in `SourceArt/HC/`, imported assets in `Content/Puzzles/Art/`.

| Task | Sprint | Assets | Specs | Used in |
| --- | --- | --- | --- | --- |
| HC-A1: Relic set | 2 | Three small relics (a gold idol, a jade mask and a gem scarab) and one key relic: a heavy, carved stone heart, the relic at the end of the maze. In place by Sprint 3. | Small relics 20–30 cm, the key relic about 60 cm. Up to 10k triangles each with Nanite on, 1K textures, full PBR. Shiny enough to catch a headlamp in a dark cave. | HC-2, HC-4, HC-10 |
| HC-A2: Puzzle props | 4 | Pressure plate (2 m stone slab), statue (1.8 m, clearly heavy), altar (now the drop-off), chamber gate (4 m wide, portcullis or stone slab, used for the maze door and G1 to G3). In place by Sprint 6. | Large props get 2K textures. Simple collision on all of them. Pivot at the base, except the gate, which pivots where it opens. | HC-5, HC-6, HC-10 |
| HC-A3: HUD art | 7 | Relic icon, round banner frame, interact-prompt frame. In place by Sprint 8. PG-A6's UI kit replaces the frames with solid, layered panels; the relic icon stays. | PNG at 512 px with transparency, readable at small sizes in a split view. | HC-8 |
| HC-A4: Maze puzzle props | 8 | A crystal lock that glows when it's lit, a brazier for flares, a maze door (3 m wide, carved stone that drops shut), and the relic's pedestal and cage. In place by Sprint 9. | Simple collision. The lock's glow is adjustable: dark when unlit, crystal teal when lit, readable from 15 m in a split view. Doors pivot where they open; the cage pivots at its base. | HC-9, HC-10, PG-9 |

## Critical assets

- `Content/Core/`: `BPI_Interactable`, `E_InteractMode`, `BPI_RoundReset`, `BP_CoopCharacter`, `BP_CoopPlayerController`, `BP_CoopPlayerState`, `BP_CoopGameState`, `S_RoundState`, `BP_CoopGameMode`, `BP_CoopGameInstance`, `E_RoundPhase`, `Input/IMC_Coop`, `Input/IMC_Debug`, `Input/IMC_Host`, `Input/IA_Interact`, `Input/IA_Drop`, `Input/IA_ToggleView`, `Input/IA_Headlamp`, `Input/IA_Sprint`, `Input/IA_ThrowFlare`, `WBP_InteractPrompt`, `WBP_RelicCounter`, `WBP_RoundHUD`, `WBP_Results`
- `Content/Puzzles/`: `BP_Relic`, `BP_Carryable`, `BP_KeyRelic`, `BP_Statue`, `BP_PressurePlate`, `BP_PuzzleSetup`, `BP_Altar`, `BP_Checkpoint`, `BP_RoundStart`, `BP_RegroupVolume`, `BP_ChamberGate`, `BP_StartPad`, `BP_CrystalLock`, `BP_MazeDoor`, `S_RoundScaling`, `DT_RoundScaling`, `L_Site01_HC`, `Test/L_HC_Test`, `Test/BP_TestInteractable`, `Art/`
- `Content/Maps/L_Site01`, `Content/Maps/L_Site02`
- `CoopGame.uproject`, `Config/DefaultEngine.ini`, `Config/DefaultGame.ini`, `.mcp.json`

## Build and playtest notes

- Merge routine: pull, open the editor, fix broken references, run Play As Client with 2 players, push, then run `Tools\host.bat`. Add the split-screen player with F5 once you're in.
- `Content/Core/` and `Content/Maps/` are read-only until you lock them, even for you. At kickoff, run `git lfs lock` on the files you'll edit, and unlock them after you push.
- Check lighting and performance issues on Windows before calling them bugs. Macs render differently.
- The maze splits the team up, so test with players on different paths, not just standing together.

## Verification

- HC-0: Playable 1 holds 4 players, and both Macs open the project with no missing-plugin errors.
- HC-1: a client uses each test interactable. A timed hold completes only if the button is held for the whole time, on the server's clock, and a continuous use ends the moment the button is released. F1 to F3 change `RoundState` on every screen.
- HC-2: a client picks up a relic and every screen's count goes up by its value. Each player, including a split-screen player, gets a different `ColorSlot`. F4 takes everyone, including the split-screen player, to Map 2 and back.
- HC-3: lethal damage kills a client on every screen, cancels their interactions and releases held mechanisms. The dead player cannot move, interact or be revived while teammates continue. When the whole team dies in the spawn cavern, everyone restarts there after 3 seconds, on separate spots. Verify both local split-screen players independently.
- HC-4: a client picks up a crate, drops it and picks it up again, and the other clients see the same thing with no collision snags. A client carrying the relic walks at half speed without stuttering. Killing the carrier drops the item on every screen and prevents further pickups until a restart.
- HC-5: with debug keys, each of the six rounds starts, clears and restarts in order, and Rounds 3 to 6 start as soon as the round before clears. A player who dies comes back at the next checkpoint when the round clears, and not before. When the whole team dies in Round 2, each player restarts at the start of their own path.
- HC-6: the start pad starts Round 1 only when every player, including a split-screen player, stands on it. Round 1 clears with 2 players using statues and with 4 players, the plate count matches the player count, and the maze door opens. Round 2 starts only when the whole living team is past the door.
- HC-7: completing the map brings every client, and the split-screen pair, into Map 2 with the relic counts intact, each with one HUD. Sprint works for a client without stutter.
- HC-8: the HUD shows the round's name and objective, the relics, the team and your flares on every screen, including both split views, and its panels are solid with the UI kit's type. R starts a new run and everyone reconnects.
- HC-9: the locks open the doors with 2 players and with 4, and the number of doors matches the player count. A flare stands in for a missing player. Each player gets through their own door, and nobody can follow them through it.
- HC-10: the relic can't be lifted until the cage is up. Lifting it starts Round 6 on every screen. A carrier who dies drops it and a teammate lifts it. Placing it on the drop-off completes the mission and travels to Map 2.
- HC-11: every restart and regroup in the list passes at 2, 3 and 4 players, including the split-screen pair.
- HC-12: Playable 5 passes.
- HC-13: the host holds 60 fps in each split view, or a split-screen preset is in place.
- HC-14: the `demo-1` tag exists, and the demo has been played with 2, 3 and 4 players.

## Open questions

- Keep the name `CoopGame`, or pick the real title before HC-0? Renaming an Unreal project later is painful.
- Should collected relics be lost when a round restarts, to raise the stakes? The plan keeps them.
- Should the mission complete as soon as the relic is on the altar, or only once every living player is back in the first room too? The plan completes it at once.
