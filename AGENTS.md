# Agent instructions

Read this before changing anything in the Unreal project, through MCP or by hand. It applies to every agent on every machine.

> **Sprint 0 update (2026-10-09, 19:35).** The plan is being revised for the new direction: a cave start, first person with a switch to third person, split-screen on the host, relic collection, traps and ghosts, and puzzle rounds across maps. There's no car. The full revision follows shortly. If you haven't done these HC-0 steps yet, use the new names; if you have, rename in HC-1.
>
> - Skip the Vehicle content pack and the Chaos Vehicles plugin, and leave out the Nav Mesh Bounds Volume.
> - Sublevels: `/Game/Puzzles/L_Site01_HC`, `/Game/Player/L_Site01_PG` and `/Game/Hazards/L_Site01_HZ`. PK's lane is now PG (player view and ghosts).
> - Project Settings → Maps & Modes → Local Multiplayer: turn on Use Splitscreen and Skip Assigning Gamepad to Player 1. Engine → Local Player: set Aspect Ratio Axis Constraint to Maintain Y-FOV.
> - `E_RoundPhase`: `Lobby`, `Playing`, `Cleared`, `Failed`, `MapComplete`.
> - `BP_CoopGameState`: `GetPlayerCount()`, `GetScalingRow()`, `RoundIndex`, `RoundPhase` (RepNotify firing `OnRoundPhaseChanged`), `PhaseEndsAt` and `RelicsCollected`.
> - `BP_CoopGameMode`: `SetRoundPhase` works now. `StartRound(Index)`, `ClearRound()`, `FailRound()`, `CompleteMap()` and `AddRelics(Count)` are stubs.
> - `S_RoundScaling` and `DT_RoundScaling` (rows `2`, `3`, `4`: `PlateCount`, `StatueCount`, `RelicsPerRound`) replace the heist scaling table.

## The project

A 2–4 player online co-op heist in Unreal Engine 5.8.3, Blueprint-only. Players break into a site, solve scaled puzzles, grab loot, escape a collapse, and drive a four-seat getaway car past rivals to extraction.

- Design: [docs/design/two-to-four-players.md](docs/design/two-to-four-players.md)
- Sprint plan, playable checkpoints and shared contracts: [docs/sprints.md](docs/sprints.md)
- Epics, one per lane: [docs/epics/](docs/epics/)
- Map layout: [docs/map/site01-layout.md](docs/map/site01-layout.md)
- Unreal MCP setup, and what its tools can do: [docs/mcp.md](docs/mcp.md)

## Lanes

| Lane | Machine | Person | Folder | Sublevel | Test map |
| --- | --- | --- | --- | --- | --- |
| HC | Windows | Stretch | `Content/Heist/` | `L_Site01_HC` | `Content/Heist/Test/L_HC_Test` |
| VG | Mac 1 | PK | `Content/Vehicle/` | `L_Site01_VG` | `Content/Vehicle/Test/L_VG_Test` |
| HZ | Mac 2 | Ak47 | `Content/Hazards/` | `L_Site01_HZ` | `Content/Hazards/Test/L_HZ_Test` |

If you don't know which lane you're working for, ask before changing anything.

## Hard rules

1. **Never use `Get Player Character (0)`, `Get Player Controller (0)` or `Get Player Pawn (0)` in gameplay Blueprints.** Use the owning player, the instigator, or the actor that triggered the event. Index 0 breaks multiplayer and split-screen.
2. **Add HUD widgets to the owning player's screen** (`Add to Player Screen` with the owning controller), never globally to the viewport.
3. **Input goes through Enhanced Input mapping contexts added per local player.**
4. **The server decides.** Gameplay state changes (doors, plates, loot, damage, round phase) run on the server and replicate. Clients ask through Run on Server events.
5. **Every system must work at 2, 3 and 4 players.** Look up your lane's scaling table with `BP_CoopGameState.GetScalingRow()`. Never hard-code a count of 3.
6. **Stay Blueprint-only.** Do not add C++ classes or a `Source/` folder without the whole team agreeing.
7. **Every plugin must support both Mac and Windows.** Check before enabling anything from Fab or the marketplace.
8. **Only edit your own lane's folder and sublevel.** Anything else needs a lock (`git lfs lock <path>`) and a heads-up at sprint kickoff.
9. **Place actors only in your lane's sublevel.** Before spawning anything through MCP, make it the current level (in the Levels panel, double-click it). Never place actors in the persistent `L_Site01`. The one exception is HC, which places the player starts, nav bounds and world settings there under a lock.
10. **Don't save hard references between placed actors in different sublevels.** Find another lane's actors at runtime, through the shared contracts in [docs/sprints.md](docs/sprints.md), the GameState or actor tags, and check that the reference is valid before using it.
11. **Only the GameMode changes the round phase.** Other lanes call its functions.
12. **Never edit `.uasset` or `.umap` files on disk.** Change them only through the editor.

## Working through Unreal MCP

- The MCP server runs inside the editor, so the editor must be open.
- It runs one tool call at a time on the editor's main thread. Don't send calls in parallel.
- After a batch of changes, compile the Blueprints you touched, Save All, and check that `git status` lists only your lane's files plus any you locked.
- If the save dialog lists a file you don't own, such as `L_Site01` or another lane's sublevel, uncheck it.

## Folder ownership

| Path | Owner | Lockable? |
| --- | --- | --- |
| `Content/Core/` | HC | Yes. Read-only until locked, even for the owner. |
| `Content/Maps/` (the persistent `L_Site01`) | HC | Yes |
| `Content/Shared/` | Anyone | Yes |
| `Content/Heist/`, including `L_Site01_HC` | HC | No |
| `Content/Vehicle/`, including `L_Site01_VG` | VG | No |
| The vehicle template folder that HC-0 adds, such as `Content/VehicleTemplate/` | VG | No. VG uses it in place; nobody moves it. |
| `Content/Hazards/`, including `L_Site01_HZ` | HZ | No |
| Template folders, such as `Content/ThirdPerson/`, `Content/Characters/` and `Content/LevelPrototyping/` | HC | No. Don't edit them; duplicate what you need into your lane folder. |
| `CoopGame.uproject`, `Config/`, `.mcp.json` | HC | No (text files). Ask HC for project setting or plugin changes. |

## Naming

| Prefix | Asset type |
| --- | --- |
| `BP_` | Blueprint actor or class |
| `BPI_` | Blueprint interface |
| `AC_` | Actor component |
| `AIC_` | AI controller |
| `WBP_` | Widget Blueprint |
| `E_` | Enum |
| `S_` | Struct |
| `DT_` | Data table |
| `DA_` | Data asset |
| `IA_` / `IMC_` | Input action / input mapping context |
| `L_` | Level |
| `SM_` / `SK_` / `M_` / `MI_` / `T_` | Static mesh / skeletal mesh / material / material instance / texture |
| `SFX_` / `MS_` | Sound / MetaSound |

## Before you push

- Compile every Blueprint you changed, with no errors.
- Open `L_Site01` and run Play In Editor with **Net Mode: Play As Client** and at least 2 players. Check your feature as a client; the host view hides most network bugs.
- Check the Output Log for errors and "Accessed None" warnings.
- Commit only your lane's files plus any you locked. Run `git pull --rebase`, push, then unlock what you locked.
