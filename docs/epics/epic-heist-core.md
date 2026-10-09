# Epic: Heist core and round flow (HC)

**Machine:** Windows · **Owner:** Stretch · **Role:** integrator and host · **Sublevel:** `L_Site01_HC`

## Relationship to other epics (read first)

This lane owns the shared core: the GameMode, GameState, player character and controller, project settings, and the persistent map. The other two lanes, [VG](epic-vehicle-getaway.md) and [HZ](epic-site-hazards.md), build against the contracts HC-0 creates. The sprint table, playable checkpoints and full contract list, with when each contract works, are in [docs/sprints.md](../sprints.md). Room positions are in [docs/map/site01-layout.md](../map/site01-layout.md).

## Context

The Windows machine merges everyone's work, hosts every playtest, and makes the final call on visuals and performance. So this lane stops building a few minutes before the others each sprint, and each phase is sized for about 25 minutes.

The heist lane covers what players do on foot: interact with things, carry them, revive each other, solve the vault puzzle, and move through the round from the start pad to the results screen.

## Locked decisions

- Unreal Engine **5.8.3**, Blueprint-only, made from the Third Person template. The project is named `CoopGame`.
- One map, `L_Site01`, without World Partition. Each lane owns one always-loaded sublevel. The persistent level holds only player starts, nav bounds and world settings, and HC places them under a lock.
- `BP_CoopGameMode` and `BP_CoopGameState` are children of **GameMode** and **GameState**, not the Base versions, so the Restart Game node is available.
- Max players is 4. Every mechanism scales through `GetScalingRow()` and `DT_HeistScaling`, read when the round starts.
- Puzzles use stand-ins: a statue holds a pressure plate as well as a player does.
- All interaction goes through `BPI_Interactable`. The client asks, and the server rechecks distance and `CanInteract` before anything happens.
- Only the GameMode changes the round phase, and the first ending wins.
- Each pawn adds and removes its own input mapping context.
- Split-screen-safe from day one: no player index 0, HUD widgets on the owning player's screen, input contexts per local player.

## Non-goals (for Demo 1)

- Tool slots and the Scout role. The demo's stand-ins are statues you carry.
- Split-screen couch co-op, Epic Online Services sessions, menus beyond the results screen, and save data.
- More than one site.
- Stretch goal, only if this lane is ahead: `BP_Lever`, which a player must hold or a carried wedge jams.

## Dependencies and sequencing

- HC-0 blocks everyone, because the Macs can't open anything until the bare project is pushed. Push it by minute 15.
- HC-3 needs `AC_Health` working from HZ-2. That's a hard gate for Playable 2: if HZ-2 isn't merged by the end of Sprint 2, HZ finishes it first thing in Sprint 3.
- HC-4's puzzle reads the player count when the phase becomes `Heist`. Until HC-6's start pad, the host presses F1 once everyone has joined.
- HC-7's success ending needs `BP_ExtractionZone` from VG-7, in the same sprint. Test with F3 until it's merged.

## Phases

### HC-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, install Unreal 5.8.3 and Git LFS on the Windows machine and clone the repo.

**First 15 minutes: the bare project.**

- Create `CoopGame` outside the repo from the Third Person template: Blueprint, no starter content. Close the editor, move `CoopGame.uproject`, `Config/` and `Content/` into the repo root, and reopen it from there.
- Enable the plugins **Unreal MCP**, **All Toolsets**, **Chaos Vehicles** and **Python Editor Script Plugin**, then restart.
- Add the vehicle content for VG: Content Browser → Add → Add Feature or Content Pack → Vehicle. The folder it creates belongs to VG. If 5.8 doesn't list it, skip this; VG migrates a car from a scratch Vehicle template project instead.
- Project Settings: under Maps & Modes, set the editor and game default maps to `L_Site01`. Under Navigation Mesh, set Runtime Generation to **Dynamic**, so the nav mesh rebuilds at runtime as the site changes. That doesn't stop the editor saving nav data into the persistent level, so only HC ever saves `L_Site01`. In `Config/DefaultGame.ini`, add `MaxPlayers=4` under `[/Script/Engine.GameSession]`.
- Create `/Game/Maps/L_Site01` with File → New Level → **Basic**, which has no World Partition. In the Levels panel, create three sublevels: `/Game/Heist/L_Site01_HC`, `/Game/Vehicle/L_Site01_VG` and `/Game/Hazards/L_Site01_HZ`. Set each one to **Always Loaded**.
- Move the Basic level's floor, sun, sky, sky light and fog into `L_Site01_HZ`, because HZ owns the layout and lighting; the floor carries Playable 1. Add 4 player starts in the spawn yard and one Nav Mesh Bounds Volume to the persistent level, using the positions in the layout doc.
- In the editor console, run `ModelContextProtocol.GenerateClientConfig ClaudeCode` to write `.mcp.json` to the repo root. Commit and push.

**Next 20 minutes: the contracts.** Create every Sprint 0 contract in the contracts table with its final names and inputs. The small ones work straight away:

- `BP_CoopGameState`: `GetPlayerCount()`, `GetScalingRow()`, `RoundPhase` with its RepNotify firing `OnRoundPhaseChanged`, `PhaseEndsAt`, `LootSecured` and `EndReason`.
- `BP_CoopGameMode`: `SetRoundPhase` and `NotifyGetawayStarted` work. `RequestEndRound` only prints its inputs until HC-7. Set it as the project's default GameMode with `BP_CoopCharacter`, `BP_CoopPlayerController`, `BP_CoopPlayerState` and `BP_CoopGameState`.
- Stubs: `BPI_Interactable`, `BP_CoopCharacter` (a child of the template character), `BP_CoopPlayerController`, `BP_CoopPlayerState`, `E_RoundPhase`, and `S_HeistScaling` with `DT_HeistScaling` (rows `2`, `3`, `4`: `PlateCount`, `StatueCount`, `CollapseSeconds`, `LootCount`).

Push. Then host Playable 1 for the last 15 minutes.

### HC-1: Interaction and input (Sprint 1, 45 min)

- `IMC_Coop` in `Content/Core/Input/`: a copy of the template's default mapping context, plus `IA_Interact` (E, or the gamepad's bottom face button). The character adds `IMC_Coop` in Receive Controller Changed when a local player takes it, and removes it when they leave, instead of the template's BeginPlay. Template assets stay untouched.
- `IMC_Debug`, which `BP_CoopPlayerController` adds once, holds the host-only debug keys: F1 starts `Heist`, F2 starts `Collapse`, F3 and F4 request a success and a failure ending.
- On the owning client, run a short sphere trace from the camera about every 0.1 seconds. If the hit actor implements `BPI_Interactable` and `CanInteract` is true, show `WBP_InteractPrompt` with its prompt text on the owning player's screen.
- Pressing Interact sends `Server_Interact(Target)` from the character, which the player owns. If the hold time is above 0, the client shows a simple progress bar first, and cancels if the button is released, the target changes or the player goes down. The server rechecks distance (under 4 m) and `CanInteract`, then calls `Interact`.
- `BP_TestInteractable` in `Content/Heist/Test/`, which prints who used it, for the other lanes to test against.

### HC-2: Carrying (Sprint 2, 45 min)

- `BP_Carryable`: the physics mesh is the root component, with Replicates and Replicate Movement on. Everything below runs on the server.
- Pick up: turn physics off, stop it colliding with pawns, and attach it to a carry point on the character.
- Drop, by pressing Interact again while carrying: detach, restore collision, turn physics back on, and give it a small push forward.
- The character's `Carried` reference replicates. `GetCarried()` returns it. `ReleaseCarried()` lets go and returns the actor without turning physics back on, for VG to stow it.
- Crates in the plate hall to test with.

### HC-3: Statues and revive (Sprint 3, 60 min) → Playable 2

- `bHeavy` carryables halve the carrier's speed. Set the speed through a RepNotify so the server and the owning client agree; otherwise the client stutters from movement corrections. `BP_Statue` is heavy.
- Add `AC_Health` to `BP_CoopCharacter`. The character implements `BPI_Interactable` for revive. `CanInteract` is true only when this character is downed, `AC_Health.CanBeRevived()` is true, and the instigator isn't downed. The prompt is "Revive", with `ReviveSeconds` from `DT_HazardScaling` as the hold time, and `Interact` calls `AC_Health.Revive`.
- A player who goes down drops what they're carrying.
- Host Playable 2.

### HC-4: The vault puzzle (Sprint 4, 45 min)

- `BP_PressurePlate`: on the server, count the players and heavy carryables standing on it. `bPressed` replicates through a RepNotify that sinks the plate and changes its color.
- `BP_VaultDoor`: holds a list of plates in the same sublevel. It opens while every enabled plate is pressed and closes when one is released. When the phase becomes `Collapse`, it opens and stays open, so nobody is trapped.
- `BP_PuzzleSetup`: when the phase becomes `Heist`, it reads `PlateCount` and `StatueCount`, enables that many plates, and spawns statues in the alcoves. Starting values: 2 players get 3 plates and 2 statues; 3 players get 3 and 1; 4 players get 4 and 1. That leaves one player free to walk into the vault.
- Build it all in the plate hall of `L_Site01_HC`.

### HC-5: Loot and the countdown (Sprint 5, 45 min)

- `BP_Loot`: a heavy carryable worth 1000. The first pickup sets the phase to `Collapse` and sets `PhaseEndsAt` to now plus `CollapseSeconds`. Start with 100 seconds for 2 players, 90 for 3 and 80 for 4.
- `LootCount` extra small pieces on the vault shelves, light and worth 250 each: 1 for 2 players, 2 for 3 and 3 for 4.
- `WBP_RoundHUD` on each owning player's screen shows the phase and a countdown from `PhaseEndsAt`.

### HC-6: Start pad and crush (Sprint 6, 60 min) → Playable 3

- `BP_StartPad` in the spawn yard: when every connected player has stood on it for 3 seconds, the phase moves from `Lobby` to `Heist`.
- `BP_SiteVolume` covers the site. When `PhaseEndsAt` passes during `Collapse` or `Getaway`, every player inside gets `AC_Health.ForceDown(false)`.
- Host Playable 3.

### HC-7: Endings (Sprint 7, 45 min)

- `RequestEndRound(bSuccess, LootValue, Reason)` works. It's ignored unless the phase is `Heist`, `Collapse` or `Getaway`, so the first ending wins. It sets `LootSecured` and `EndReason`, then the phase (`Extracted` or `Failed`).
- When every player is down at once, the round fails with "Everyone went down". The GameMode binds each player's `AC_Health.OnDowned` and `OnRevived` when their character spawns.
- `WBP_Results` on each owning player's screen shows success or failure, the reason and the loot. The host presses R to call **Restart Game** on the server; every client should reconnect on its own.

### HC-8: Full run (Sprint 8, 60 min) → Playable 4

- In the build window, trigger every ending as a client and fix what breaks: extraction, everyone down, the car destroyed, and crushed at zero. Log each result in the sprint log.
- Tune `DT_HeistScaling` from the 2-player and 4-player runs.
- Host Playable 4.

### HC-9: Demo (Sprint 9, 60 min) → Demo 1

- Fix what Playable 4 found.
- Windows performance pass with 4 players, using `stat fps` and `stat unit` on the host. Aim for 60 fps.
- Optional: package a Win64 build for Windows-only friends. Keep team playtests on the scripts, because Macs can't run it.
- Tag the commit `demo-1` and push the tag. Host the demo with 2, 3 and 4 players.

## Critical assets

- `Content/Core/`: `BPI_Interactable`, `BP_CoopCharacter`, `BP_CoopPlayerController`, `BP_CoopPlayerState`, `BP_CoopGameState`, `BP_CoopGameMode`, `E_RoundPhase`, `Input/IMC_Coop`, `Input/IMC_Debug`, `Input/IA_Interact`, `WBP_InteractPrompt`, `WBP_RoundHUD`, `WBP_Results`
- `Content/Heist/`: `BP_Carryable`, `BP_Statue`, `BP_Loot`, `BP_PressurePlate`, `BP_VaultDoor`, `BP_PuzzleSetup`, `BP_StartPad`, `BP_SiteVolume`, `S_HeistScaling`, `DT_HeistScaling`, `L_Site01_HC`, `Test/L_HC_Test`, `Test/BP_TestInteractable`
- `Content/Maps/L_Site01`
- `CoopGame.uproject`, `Config/DefaultEngine.ini`, `Config/DefaultGame.ini`, `.mcp.json`

## Build and playtest notes

- Merge routine: pull, open the editor, fix broken references, run Play As Client with 2 players, push, then run `Tools\host.bat`.
- `Content/Core/` and `Content/Maps/` are read-only until you lock them, even for you. At kickoff, run `git lfs lock` on the files you'll edit, and unlock them after you push.
- Check lighting and performance issues on Windows before calling them bugs. Macs render differently.

## Verification

- HC-0: Playable 1 holds 4 players, and both Macs open the project with no missing-plugin errors.
- HC-1: a client sees the prompt on `BP_TestInteractable` and uses it. A hold cancels when the button is released. F1 and F2 change the phase for everyone.
- HC-2: a client picks up a crate, carries it and drops it, and the other clients see it move the same way.
- HC-3: a client carrying a statue walks at half speed without stuttering. One client revives another, and a crushed player can't be revived.
- HC-4: after F1, the vault opens with 2 players using statues and with 4 players, and the plate count matches the player count.
- HC-5: picking up the loot starts the countdown on every screen, and the extra loot count matches the player count.
- HC-6: the start pad starts the round, and a player still inside at zero is crushed.
- HC-7: F3 and F4 show the right results screen on every machine. A second ending after the first is ignored. R restarts the round and every client reconnects.
- HC-8: Playable 4 passes.
- HC-9: the `demo-1` tag exists, and the demo has been played with 2, 3 and 4 players.

## Open questions

- Keep the name `CoopGame`, or pick the real title before HC-0? Renaming an Unreal project later is painful.
- Lever and wedge: worth building if HC gets ahead? Decide at the Sprint 6 retro.
