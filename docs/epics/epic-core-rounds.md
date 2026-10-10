# Epic: Core, puzzles and rounds (HC)

**Machine:** Windows · **Owner:** Stretch · **Role:** integrator and host · **Folder:** `Content/Puzzles/`, plus `Content/Core/` and `Content/Maps/` · **Sublevel:** `L_Site01_HC`

## Relationship to other epics (read first)

This lane owns the shared core: the GameMode, GameState, GameInstance, player character, controller and state, project settings, and the maps' persistent levels. It also owns interaction, relics, carrying, death integration and checkpoint restarts, the round framework, Rounds 1 and 2, and travel between maps. [PG](epic-player-ghosts.md) adds the player's view, split-screen, ghosts and Round 3. [HZ](epic-cave-traps.md) builds the cave, its traps and its atmosphere. The sprint table, checkpoints and full contract list are in [docs/sprints.md](../sprints.md), room positions in [docs/map/site01-layout.md](../map/site01-layout.md), the asset pipeline in [docs/assets.md](../assets.md), and the design direction in [docs/design/direction-2026-10-09.md](../design/direction-2026-10-09.md).

## Context

The Windows machine merges everyone's work and hosts every playtest, including the split-screen pair. It also makes the final call on visuals and performance. So this lane stops building a few minutes before the others each sprint, and each phase is sized for about 25 minutes.

HC covers what players do with their hands: interact, collect relics, carry things, restart at a checkpoint when the whole team dies, solve the puzzles in Rounds 1 and 2, and move through the rounds and into the next map.

## Locked decisions

- Unreal Engine **5.8.3**, Blueprint-only, made from the Third Person template. Its full-body character carries both the first- and third-person views. The project is named `CoopGame`.
- Maps don't use World Partition. Each map has a persistent level, which HC owns, plus one always-loaded sublevel per lane.
- `BP_CoopGameMode` and `BP_CoopGameState` are children of **GameMode** and **GameState**, not the Base versions.
- Max players is 4, counting split-screen players. Scaling goes through `RoundState.ScalingRow`, which the server keeps in step with the player count in the lobby and locks when a round starts.
- The round state replicates as one struct, so clients never see a round number from one round and a phase from another.
- Interaction has three modes: instant, timed and continuous. The server times holds itself and ends them on release.
- Each chamber is one round. A round starts when the first player enters its chamber, clears when its puzzle is solved, and restarts from its entrance when the whole team is dead.
- Lethal damage kills players immediately; there is no downed state or teammate revive. Dead players cannot move, interact, carry items or hold mechanisms, and stay dead until a server-controlled restart. When the whole team is dead, in any phase, everyone restarts at the latest checkpoint.
- Small relics go straight into the team's count. The key relic is heavy and has to be carried. Collected relics stay collected through restarts.
- Puzzles use stand-ins: a statue holds a pressure plate as well as a player does.
- Only the GameMode changes the round state. The run's progress lives on the server, in the GameInstance, across travel.
- Each pawn adds and removes its own input mapping context.
- Split-screen-safe from day one: no player index 0, HUD widgets on the owning player's screen, input per local player.

## Non-goals (for Demo 1)

- Tool slots and the Scout.
- Split-screen on joining machines, Epic Online Services sessions, menus beyond the results screen, and save data.
- More of Map 2 than its antechamber.

## Dependencies and sequencing

- HC-0 blocks everyone, because the Macs can't open anything until the bare project is pushed. Push it by minute 15.
- HC-2 puts PG-1's `AC_PlayerView` on the real character and wires F5 and F6 to PG's `BPFL_SplitScreen`, whose stub PG publishes in Sprint 1.
- HC-3 needs HZ-2's `AC_Health`. That's a hard gate for Playable 2: if it isn't merged by the end of Sprint 2, HZ finishes it first thing in Sprint 3.
- HC-6's Round 2 uses HZ-4's trap corridor and key relic nook. PG-6's Round 3 uses HC-1's continuous interaction and HC-5's round reset.
- HC-7 brings in HZ-7's Map 2 room, built in the same sprint. The bare `L_Site02` works until it lands.

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
- Team-wipe restart, in any phase: when every connected player is dead, including both local split-screen players, the GameMode waits 3 seconds, moves each player to their own spot at the latest checkpoint and calls `AC_Health.ResetHealth()` on everyone. Dead players never respawn individually. In Sprint 5 this grows into the round restart.
- Host Playable 2, including a split-screen player on the Windows machine.

### HC-4: Carrying (Sprint 4, 45 min)

- `BP_Carryable`: the physics mesh is the root component, with Replicates and Replicate Movement on. Picking up is an instant interaction. On the server it turns physics off and attaches the item to a carry point on the character.
- Its replicated carry state holds the carrier and whether it's free, carried or placed. Its RepNotify applies the matching collision on every machine, so a carried item never blocks its carrier or anyone else.
- `IA_Drop` drops what you're carrying: detach, restore collision, turn physics back on, and give it a small push forward. Interact never drops, so using an altar while carrying works. `GetCarried()` returns the item, and `ReleaseCarried()` hands it to whatever takes it without turning physics on.
- A `bHeavy` carryable halves the carrier's speed. Set the speed through a RepNotify so the server and the owning client agree; otherwise the client stutters from movement corrections.
- `BP_KeyRelic` (heavy) in the key relic nook, at the position in the layout doc, and `BP_Statue` (heavy). A player who dies drops what they're carrying through the server-side `AC_Health.OnDied` binding.
- Test pick up, drop and pick up again, and pick up after a client joins late.

### HC-5: Rounds and restarts (Sprint 5, 45 min)

- `BP_RoundStart` at each chamber entrance: the first player in calls `StartRound(N)`, if N is the next round. Starting a round makes that round's `BP_Checkpoint` the latest.
- `BP_ChamberGate` opens when its round clears. `BP_StartPad` in the spawn cavern: when every connected player, including split-screen players, has stood on it for 3 seconds, the gate to Round 1 opens.
- `FailRound()` works. When the whole team is dead during `Playing`, the phase becomes `Failed`. After 3 seconds, the checkpoint restart from HC-3 runs at the round's checkpoint, the GameMode calls `BPI_RoundReset.ResetForRound(Index, Attempt + 1)` on every actor that implements it, and the round starts again with the next `Attempt`.
- If a player leaves during a round, restart it the same way, so the puzzles match the new player count.
- Every HC puzzle actor implements `BPI_RoundReset`. Carryables go back to where they started; the key relic goes back to its nook.

### HC-6: Rounds 1 and 2 (Sprint 6, 60 min) → Playable 3

- Round 1, the plate hall: `BP_PressurePlate` counts living players and heavy carryables on the server; `bPressed` replicates through a RepNotify that sinks the plate and changes its color. When every enabled plate is pressed, the round clears.
- `BP_PuzzleSetup` reads `PlateCount` and `StatueCount` when Round 1 starts, enables that many plates, and spawns statues in the alcoves. Starting values: 2 players get 3 plates and 2 statues; 3 players get 3 and 1; 4 players get 4 and 1. A restart removes and respawns the statues.
- Round 2, the altar: `BP_Altar` in chamber 2. Using it while carrying the key relic is one server step: release the relic from the carrier, set it to placed on the altar, and clear the round.
- Host Playable 3.

### HC-7: Map 2 and the run (Sprint 7, 45 min)

- `BP_MapExit` volume at the bottom of the zipline and walkway: when every player is inside, call `CompleteMap()`.
- `CompleteMap()` now saves `RelicsCollected` and `RelicsAvailable` in `BP_CoopGameInstance` before traveling. On arrival, the GameMode restores them into the GameState.
- Bring `L_Site02_HZ` into `L_Site02` as an always-loaded sublevel.
- After travel, check that each player's HUD and input come back once, through the normal possession and BeginPlay paths, and that no extra split-screen players appear.

### HC-8: HUD, results and restart (Sprint 8, 45 min)

- `WBP_RoundHUD` on each owning player's screen replaces the relic counter. It shows the round (1 of 3), the relics, and a banner when a round clears or fails. It reads `RoundState` when it's created as well as on change.
- `WBP_Results` in Map 2 shows the relics collected out of those available.
- The host presses R to start a new run: reset the run's state in the GameInstance, then `ServerTravel /Game/Maps/L_Site01?listen`.

### HC-9: Full run (Sprint 9, 60 min) → Playable 4

- In the build window, play every path as a client and fix what breaks: each round's restart, team-wipe restarts outside a round, the zipline and the walkway, travel to Map 2, the results and the restart. Check that the split-screen pair survives travel both ways. Log each result in the sprint log.
- Tune `DT_RoundScaling` and the relic placement from the 2-player and 4-player runs.
- Host Playable 4.

### HC-10: Buffer and performance (Sprint 10, 45 min)

- Finish whatever earlier phases left behind.
- Windows performance pass with 4 players, including the split-screen pair, using `stat fps` and `stat unit` on the host. Aim for 60 fps in each split view; if it's lower, add a split-screen scalability preset rather than cutting lights.

### HC-11: Demo (Sprint 11, 60 min) → Demo 1

- Final fixes.
- Tag the commit `demo-1` and push the tag. Host the demo with 2, 3 and 4 players.

## Asset generation

Follow [docs/assets.md](../assets.md) for specs, licensing, imports and reviews. Raw output goes in `SourceArt/HC/`, imported assets in `Content/Puzzles/Art/`.

| Task | Sprint | Assets | Specs | Used in |
| --- | --- | --- | --- | --- |
| HC-A1: Relic set | 2 | Three small relics (a gold idol, a jade mask and a gem scarab) and one key relic: a heavy, carved stone heart. In place by Sprint 3. | Small relics 20–30 cm, the key relic about 60 cm. Up to 10k triangles each with Nanite on, 1K textures, full PBR. Shiny enough to catch a headlamp in a dark cave. | HC-2, HC-4 |
| HC-A2: Puzzle props | 4 | Pressure plate (2 m stone slab), statue (1.8 m, clearly heavy), altar, chamber gate (4 m wide, portcullis or stone slab). In place by Sprint 6. | Large props get 2K textures. Simple collision on all of them. Pivot at the base, except the gate, which pivots where it opens. | HC-5, HC-6 |
| HC-A3: HUD art | 7 | Relic icon, round banner frame, interact-prompt frame. In place by Sprint 8. | PNG at 512 px with transparency, readable at small sizes in a split view. | HC-8 |

## Critical assets

- `Content/Core/`: `BPI_Interactable`, `E_InteractMode`, `BPI_RoundReset`, `BP_CoopCharacter`, `BP_CoopPlayerController`, `BP_CoopPlayerState`, `BP_CoopGameState`, `S_RoundState`, `BP_CoopGameMode`, `BP_CoopGameInstance`, `E_RoundPhase`, `Input/IMC_Coop`, `Input/IMC_Debug`, `Input/IMC_Host`, `Input/IA_Interact`, `Input/IA_Drop`, `Input/IA_ToggleView`, `Input/IA_Headlamp`, `WBP_InteractPrompt`, `WBP_RelicCounter`, `WBP_RoundHUD`, `WBP_Results`
- `Content/Puzzles/`: `BP_Relic`, `BP_Carryable`, `BP_KeyRelic`, `BP_Statue`, `BP_PressurePlate`, `BP_PuzzleSetup`, `BP_Altar`, `BP_Checkpoint`, `BP_RoundStart`, `BP_ChamberGate`, `BP_StartPad`, `BP_MapExit`, `S_RoundScaling`, `DT_RoundScaling`, `L_Site01_HC`, `Test/L_HC_Test`, `Test/BP_TestInteractable`, `Art/`
- `Content/Maps/L_Site01`, `Content/Maps/L_Site02`
- `CoopGame.uproject`, `Config/DefaultEngine.ini`, `Config/DefaultGame.ini`, `.mcp.json`

## Build and playtest notes

- Merge routine: pull, open the editor, fix broken references, run Play As Client with 2 players, push, then run `Tools\host.bat`. Add the split-screen player with F5 once you're in.
- `Content/Core/` and `Content/Maps/` are read-only until you lock them, even for you. At kickoff, run `git lfs lock` on the files you'll edit, and unlock them after you push.
- Check lighting and performance issues on Windows before calling them bugs. Macs render differently.

## Verification

- HC-0: Playable 1 holds 4 players, and both Macs open the project with no missing-plugin errors.
- HC-1: a client uses each test interactable. A timed hold completes only if the button is held for the whole time, on the server's clock, and a continuous use ends the moment the button is released. F1 to F3 change `RoundState` on every screen.
- HC-2: a client picks up a relic and every screen's count goes up by its value. Each player, including a split-screen player, gets a different `ColorSlot`. F4 takes everyone, including the split-screen player, to Map 2 and back.
- HC-3: lethal damage kills a client on every screen, cancels their interactions and releases held mechanisms. The dead player cannot move, interact or be revived while teammates continue. When the whole team dies in the spawn cavern, everyone restarts there after 3 seconds, on separate spots. Verify both local split-screen players independently.
- HC-4: a client picks up a crate, drops it and picks it up again, and the other clients see the same thing with no collision snags. A client carrying the key relic walks at half speed without stuttering. Killing the carrier drops the item on every screen and prevents further pickups until a restart.
- HC-5: the start pad opens the gate only when every player, including a split-screen player, stands on it. When the whole team dies during a round, it restarts from its entrance with its puzzle reset and the next `Attempt`.
- HC-6: Round 1 clears with 2 players using statues and with 4 players, and the plate count matches the player count. Placing the key relic clears Round 2.
- HC-7: completing the map brings every client, and the split-screen pair, into Map 2 with the relic counts intact, each with one HUD.
- HC-8: the HUD shows the round and relics on every screen, including both split views. R starts a new run and everyone reconnects.
- HC-9: Playable 4 passes.
- HC-10: the host holds 60 fps in each split view, or a split-screen preset is in place.
- HC-11: the `demo-1` tag exists, and the demo has been played with 2, 3 and 4 players.

## Open questions

- Keep the name `CoopGame`, or pick the real title before HC-0? Renaming an Unreal project later is painful.
- Should collected relics be lost when a round restarts, to raise the stakes? The plan keeps them.
