# Epic: Core, puzzles and rounds (HC)

**Machine:** Windows · **Owner:** Stretch · **Role:** integrator and host · **Folder:** `Content/Puzzles/`, plus `Content/Core/` and `Content/Maps/` · **Sublevel:** `L_Site01_HC`

## Relationship to other epics (read first)

This lane owns the shared core: the GameMode, GameState, player character and controller, project settings, and the maps' persistent levels. It also owns relics, carrying, revive, the round framework, Rounds 1 and 2, and travel between maps. [PG](epic-player-ghosts.md) adds the player's view, split-screen, ghosts and Round 3. [HZ](epic-cave-traps.md) builds the cave, its traps and its atmosphere. The sprint table, checkpoints and full contract list are in [docs/sprints.md](../sprints.md), room positions in [docs/map/site01-layout.md](../map/site01-layout.md), the asset pipeline in [docs/assets.md](../assets.md), and the design direction in [docs/design/direction-2026-10-09.md](../design/direction-2026-10-09.md).

## Context

The Windows machine merges everyone's work and hosts every playtest, including the split-screen pair. It also makes the final call on visuals and performance. So this lane stops building a few minutes before the others each sprint, and each phase is sized for about 25 minutes.

HC covers what players do with their hands: interact, collect relics, carry things, revive each other, solve the puzzles in Rounds 1 and 2, and move through the rounds and into the next map.

## Locked decisions

- Unreal Engine **5.8.3**, Blueprint-only, made from the Third Person template. Its full-body character carries both the first- and third-person views. The project is named `CoopGame`.
- Maps don't use World Partition. Each map has a persistent level, which HC owns, plus one always-loaded sublevel per lane.
- `BP_CoopGameMode` and `BP_CoopGameState` are children of **GameMode** and **GameState**, not the Base versions.
- Max players is 4, counting split-screen players. Every mechanism scales through `GetScalingRow()`, read when a round starts.
- Each chamber is one round. A round starts when the first player enters its chamber, clears when its puzzle is solved, and restarts from its entrance when everyone is down at once.
- Small relics go straight into the team's count. The key relic is heavy and has to be carried.
- Puzzles use stand-ins: a statue holds a pressure plate as well as a player does.
- All interaction goes through `BPI_Interactable`. The client asks, and the server rechecks distance and `CanInteract` before anything happens.
- Only the GameMode changes the round phase. The run's progress lives on the server and travels with it between maps.
- Each pawn adds and removes its own input mapping context.
- Split-screen-safe from day one: no player index 0, HUD widgets on the owning player's screen, input per local player.

## Non-goals (for Demo 1)

- Tool slots and the Scout.
- Split-screen on joining machines, Epic Online Services sessions, menus beyond the results screen, and save data.
- More of Map 2 than its antechamber.

## Dependencies and sequencing

- HC-0 blocks everyone, because the Macs can't open anything until the bare project is pushed. Push it by minute 15.
- HC-2 puts PG-1's `AC_PlayerView` on the real character and wires F5 and F6 to PG-2's split-screen functions.
- HC-3 needs HZ-2's `AC_Health`. That's a hard gate for Playable 2: if it isn't merged by the end of Sprint 2, HZ finishes it first thing in Sprint 3.
- HC-5's Round 1 uses the chambers from HZ-1's blockout. HC-6's Round 2 uses HZ-5's trap corridor and key relic nook.
- HC-7's travel needs HZ-7's Map 2 antechamber, built in the same sprint. A bare floor works until it lands.

## Phases

### HC-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, install Unreal 5.8.3 and Git LFS on the Windows machine and clone the repo.

**First 15 minutes: the bare project.**

- Create `CoopGame` outside the repo from the Third Person template: Blueprint, no starter content. Close the editor, move `CoopGame.uproject`, `Config/` and `Content/` into the repo root, and reopen it from there.
- Enable the plugins **Unreal MCP**, **All Toolsets** and **Python Editor Script Plugin**, then restart.
- Project Settings:
  - Maps & Modes: set the editor and game default maps to `L_Site01`. Under Local Multiplayer, turn on **Use Splitscreen** and **Skip Assigning Gamepad to Player 1**, so the host plays on keyboard and mouse and the first gamepad becomes player 2.
  - Engine → Local Player: set Aspect Ratio Axis Constraint to **Maintain Y-FOV**, so split views keep their vertical field of view.
  - In `Config/DefaultGame.ini`, add `MaxPlayers=4` under `[/Script/Engine.GameSession]`.
- Create `/Game/Maps/L_Site01` with File → New Level → **Basic**, which has no World Partition. In the Levels panel, create three sublevels: `/Game/Puzzles/L_Site01_HC`, `/Game/Player/L_Site01_PG` and `/Game/Hazards/L_Site01_HZ`. Set each one to **Always Loaded**.
- Move the Basic level's floor, sun, sky, sky light and fog into `L_Site01_HZ`, because HZ owns the cave and its light; the floor carries Playable 1. Add 4 player starts in the spawn cavern, at the positions in the layout doc, to the persistent level.
- In the editor console, run `ModelContextProtocol.GenerateClientConfig ClaudeCode` to write `.mcp.json` to the repo root. Commit and push.

**Next 20 minutes: the contracts.** Create every Sprint 0 contract in the contracts table with its final names and inputs:

- `BP_CoopGameState`: `GetPlayerCount()`, `GetScalingRow()`, `RoundIndex`, `RoundPhase` with its RepNotify firing `OnRoundPhaseChanged`, `PhaseEndsAt` and `RelicsCollected`. These all work now.
- `BP_CoopGameMode`: `SetRoundPhase` works. `StartRound(Index)`, `ClearRound()`, `FailRound()`, `CompleteMap()` and `AddRelics(Count)` are stubs that print their inputs. Set it as the project's default GameMode with `BP_CoopCharacter`, `BP_CoopPlayerController`, `BP_CoopPlayerState` and `BP_CoopGameState`.
- Stubs: `BPI_Interactable`, `BP_CoopCharacter` (a child of the template character), `BP_CoopPlayerController`, `BP_CoopPlayerState`, `E_RoundPhase`, and `S_RoundScaling` with `DT_RoundScaling` (rows `2`, `3`, `4`: `PlateCount`, `StatueCount`).

Push. Then host Playable 1 for the last 15 minutes.

### HC-1: Interaction and input (Sprint 1, 45 min)

- If HC-0 used the earlier heist names (a `Heist` or `Vehicle` folder, heist round phases or the heist scaling table), rename them to the ones in HC-0 first. Fix up redirectors, and lock `L_Site01` for the sublevel rename.
- `IMC_Coop` in `Content/Core/Input/`: a copy of the template's default mapping context, plus `IA_Interact` (E, or the gamepad's bottom face button), `IA_ToggleView` (V, or a right-stick click) and `IA_Headlamp` (F, or d-pad up). The character adds `IMC_Coop` in Receive Controller Changed when a local player takes it, and removes it when they leave, instead of the template's BeginPlay. Template assets stay untouched.
- `IMC_Debug`, which `BP_CoopPlayerController` adds once on the host, holds the debug keys: F1 starts Round 1, F2 clears the round, F3 fails it and F4 completes the map. `IMC_Host` holds F5 and F6 for split-screen players, wired in HC-2.
- On the owning client, run a short sphere trace from the camera about every 0.1 seconds. If the hit actor implements `BPI_Interactable` and `CanInteract` is true, show `WBP_InteractPrompt` with its prompt text on the owning player's screen.
- Pressing Interact sends `Server_Interact(Target)` from the character, which the player owns. If the hold time is above 0, the client shows a simple progress bar first, and cancels if the button is released, the target changes or the player goes down. The server rechecks distance (under 4 m) and `CanInteract`, then calls `Interact`.
- `BP_TestInteractable` in `Content/Puzzles/Test/`, which prints who used it, for the other lanes to test against.
- `StartRound(Index)` and `ClearRound()` work now. They only set `RoundIndex` and the phase, so F1 and F2 are useful to the other lanes straight away. Other lanes read their scaling tables when a round starts.

### HC-2: Relics and carrying (Sprint 2, 45 min)

- `BP_Relic`: `Interact` is instant. On the server it calls `AddRelics(Value)`, which now works, then hides the relic and turns off its collision. The pickup sound plays through an unreliable multicast. `MinPlayers` (2, 3 or 4) hides bonus relics when there are fewer players.
- `BP_Carryable`: the physics mesh is the root component, with Replicates and Replicate Movement on. On the server, picking up turns physics off, stops it colliding with pawns and attaches it to a carry point on the character. Pressing Interact again drops it: detach, restore collision, physics on, and a small push forward. The character's `Carried` reference replicates; `GetCarried()` returns it and `ReleaseCarried()` lets go without turning physics back on.
- Put PG's `AC_PlayerView` on `BP_CoopCharacter` and forward `IA_ToggleView` and `IA_Headlamp` to it. Wire F5 and F6 in `IMC_Host` to `BPFL_SplitScreen.AddLocalPlayer` and `RemoveLocalPlayer`.
- `WBP_RelicCounter`, a small counter on each owning player's screen, so Playable 2 shows the team's relics. The round HUD replaces it in HC-6.
- Place the spawn cavern's tutorial relics, and a few crates to test carrying with.

If time runs out, carrying moves to HC-3.

### HC-3: Revive and the key relic (Sprint 3, 60 min) → Playable 2

- A `bHeavy` carryable halves the carrier's speed. Set the speed through a RepNotify so the server and the owning client agree; otherwise the client stutters from movement corrections. `BP_KeyRelic` is heavy; place it in the key relic nook, at the position in the layout doc.
- Add `AC_Health` to `BP_CoopCharacter`. The character implements `BPI_Interactable` for revive: `CanInteract` is true only when this character is downed, `AC_Health.CanBeRevived()` is true and the instigator isn't downed. The prompt is "Revive", with `ReviveSeconds` from `DT_HazardScaling` as the hold time, and `Interact` calls `AC_Health.Revive`.
- A player who goes down drops what they're carrying.
- Host Playable 2, including a split-screen player on the Windows machine.

### HC-4: Rounds and the start pad (Sprint 4, 45 min)

- `BP_RoundStart` at each chamber entrance: the first player in calls `StartRound(N)`, if N is the next round.
- `BP_ChamberGate` opens when its round is cleared. `BP_RespawnPoint` marks each round's restart position.
- `BP_StartPad` in the spawn cavern: when every connected player, including split-screen players, has stood on it for 3 seconds, the gate to Round 1 opens.

### HC-5: Round 1 and restarts (Sprint 5, 45 min)

- Round 1, the plate hall: `BP_PressurePlate` counts players and heavy carryables on the server; `bPressed` replicates through a RepNotify that sinks the plate and changes its color. When every enabled plate is pressed, the round clears.
- `BP_PuzzleSetup` reads `PlateCount` and `StatueCount` when Round 1 starts, enables that many plates, and spawns `BP_Statue` (heavy) in the alcoves. Starting values: 2 players get 3 plates and 2 statues; 3 players get 3 and 1; 4 players get 4 and 1.
- `FailRound()` works: when every player is down at once, the phase becomes `Failed`. After 3 seconds, everyone is revived at the round's `BP_RespawnPoint`, the round's puzzle actors reset, and the round starts again. Collected relics stay collected.

### HC-6: Round 2 and the HUD (Sprint 6, 60 min) → Playable 3

- Round 2, the altar: `BP_Altar` in chamber 2. Interacting with it while carrying the key relic places it, and the round clears. The key relic starts in HZ's trapped nook and goes back there when the round restarts.
- `WBP_RoundHUD` on each owning player's screen shows the round (1 of 3), the relics collected, and a banner when a round clears or fails.
- Host Playable 3.

### HC-7: Map 2 and results (Sprint 7, 45 min)

- `BP_MapExit` volume at the bottom of the zipline and walkway: when every player is inside, call `CompleteMap()`.
- `CompleteMap()` saves the run's relic count in the GameInstance on the server, then runs the console command `ServerTravel /Game/Maps/L_Site02?listen`.
- `/Game/Maps/L_Site02`, a persistent level with 4 player starts and `L_Site02_HZ` as its sublevel. On arrival, the GameMode restores the relic count into the GameState.
- `WBP_Results` on each owning player's screen shows the relics collected out of the total. The host presses R to start a new run: reset the count, then `ServerTravel /Game/Maps/L_Site01?listen`.

### HC-8: Full run (Sprint 8, 60 min) → Playable 4

- In the build window, play every path as a client and fix what breaks: each round's restart, the zipline and the walkway, travel to Map 2, the results and the restart. Check that the split-screen pair survives travel. Log each result in the sprint log.
- Tune `DT_RoundScaling` and the relic placement from the 2-player and 4-player runs.
- Host Playable 4.

### HC-9: Demo (Sprint 9, 60 min) → Demo 1

- Fix what Playable 4 found.
- Windows performance pass with 4 players, including the split-screen pair, using `stat fps` and `stat unit` on the host. Aim for 60 fps in each split view; if it's lower, add a split-screen scalability preset rather than cutting lights.
- Tag the commit `demo-1` and push the tag. Host the demo with 2, 3 and 4 players.

## Asset generation

Follow [docs/assets.md](../assets.md) for specs, imports and reviews. Raw output goes in `SourceArt/HC/`, imported assets in `Content/Puzzles/Art/`.

| Task | Sprint | Assets | Specs | Used in |
| --- | --- | --- | --- | --- |
| HC-A1: Relic set | 1 | Three small relics (a gold idol, a jade mask and a gem scarab) and one key relic: a heavy, carved stone heart. | Small relics 20–30 cm, the key relic about 60 cm. Up to 10k triangles each with Nanite on, 1K textures, full PBR. Shiny enough to catch the eye in a dark cave. | HC-2, HC-3 |
| HC-A2: Puzzle props | 3 | Pressure plate (2 m stone slab), statue (1.8 m, clearly heavy), altar, chamber gate (4 m wide, portcullis or stone slab). | Large props get 2K textures. Simple collision on all of them. Pivot at the base, except the gate, which pivots where it opens. | HC-4 to HC-6 |
| HC-A3: HUD art | 5 | Relic icon, round banner frame, interact-prompt frame. | PNG at 512 px with transparency, readable at small sizes in a split view. | HC-6 |

## Critical assets

- `Content/Core/`: `BPI_Interactable`, `BP_CoopCharacter`, `BP_CoopPlayerController`, `BP_CoopPlayerState`, `BP_CoopGameState`, `BP_CoopGameMode`, `E_RoundPhase`, `Input/IMC_Coop`, `Input/IMC_Debug`, `Input/IMC_Host`, `Input/IA_Interact`, `Input/IA_ToggleView`, `Input/IA_Headlamp`, `WBP_InteractPrompt`, `WBP_RelicCounter`, `WBP_RoundHUD`, `WBP_Results`
- `Content/Puzzles/`: `BP_Relic`, `BP_Carryable`, `BP_KeyRelic`, `BP_Statue`, `BP_PressurePlate`, `BP_PuzzleSetup`, `BP_Altar`, `BP_RoundStart`, `BP_ChamberGate`, `BP_RespawnPoint`, `BP_StartPad`, `BP_MapExit`, `S_RoundScaling`, `DT_RoundScaling`, `L_Site01_HC`, `Test/L_HC_Test`, `Test/BP_TestInteractable`, `Art/`
- `Content/Maps/L_Site01`, `Content/Maps/L_Site02`
- `CoopGame.uproject`, `Config/DefaultEngine.ini`, `Config/DefaultGame.ini`, `.mcp.json`

## Build and playtest notes

- Merge routine: pull, open the editor, fix broken references, run Play As Client with 2 players, push, then run `Tools\host.bat`. Add the split-screen player with F5 once you're in.
- `Content/Core/` and `Content/Maps/` are read-only until you lock them, even for you. At kickoff, run `git lfs lock` on the files you'll edit, and unlock them after you push.
- Check lighting and performance issues on Windows before calling them bugs. Macs render differently.

## Verification

- HC-0: Playable 1 holds 4 players, and both Macs open the project with no missing-plugin errors.
- HC-1: a client sees the prompt on `BP_TestInteractable` and uses it. A hold cancels when the button is released. F1 to F4 change the round phase for everyone.
- HC-2: a client picks up a relic and every screen's count goes up by its value. A client picks up a crate, carries it and drops it, and the other clients see it move the same way.
- HC-3: a client carrying the key relic walks at half speed without stuttering. One client revives another, and a player who can't be revived can't be.
- HC-4: the start pad opens the gate only when every player, including a split-screen player, stands on it. Entering chamber 1 starts Round 1.
- HC-5: Round 1 clears with 2 players using statues and with 4 players, and the plate count matches the player count. When everyone goes down, the round restarts from its entrance with the puzzle reset.
- HC-6: placing the key relic clears Round 2, and the HUD shows the round and relics on every screen, including both split views.
- HC-7: completing the map brings every client, and the split-screen pair, into Map 2 with the relic count intact. R starts a new run and everyone reconnects.
- HC-8: Playable 4 passes.
- HC-9: the `demo-1` tag exists, and the demo has been played with 2, 3 and 4 players.

## Open questions

- Keep the name `CoopGame`, or pick the real title before HC-0? Renaming an Unreal project later is painful.
- Should collected relics be lost when a round restarts, to raise the stakes? The plan keeps them.
