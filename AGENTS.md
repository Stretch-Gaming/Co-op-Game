# Agent instructions

Read this before changing anything in the Unreal project, through MCP or by hand. It applies to every agent on every machine.

## The project

A 2–4 player online co-op puzzle game in Unreal Engine 5.8.3, Blueprint-only. Players work through rounds of puzzles across a series of maps, collecting relics and getting past traps and ghosts. The first map is an underground cave. Players see the game in first person and can switch to third person, and two players can share the host's screen in split-screen.

- Design: [docs/design/direction-2026-10-09.md](docs/design/direction-2026-10-09.md), which updates [docs/design/two-to-four-players.md](docs/design/two-to-four-players.md)
- Sprint plan, playable checkpoints and shared contracts: [docs/sprints.md](docs/sprints.md)
- Epics, one per lane: [docs/epics/](docs/epics/)
- Map layout: [docs/map/site01-layout.md](docs/map/site01-layout.md)
- Asset generation: [docs/assets.md](docs/assets.md), with the visual style in [docs/art/style.md](docs/art/style.md) and credits in [CREDITS.md](CREDITS.md)
- Unreal MCP setup, and what its tools can do: [docs/mcp.md](docs/mcp.md)

## Lanes

| Lane | Machine | Person | Folder | Sublevel | Test map |
| --- | --- | --- | --- | --- | --- |
| HC: core, puzzles and rounds | Windows | Stretch | `Content/Puzzles/` | `L_Site01_HC` | `Content/Puzzles/Test/L_HC_Test` |
| PG: player view and ghosts | Mac 1 | PK | `Content/Player/` | `L_Site01_PG` | `Content/Player/Test/L_PG_Test` |
| HZ: cave, traps and atmosphere | Mac 2 | Ak47 | `Content/Hazards/` | `L_Site01_HZ`, `L_Site02_HZ` | `Content/Hazards/Test/L_HZ_Test` |

If you don't know which lane you're working for, ask before changing anything.

## Tracking work

Work for this project is tracked in this repo's [GitHub Issues](https://github.com/StretchGaming/Co-op-Game/issues), not in BB Tasks or any other tracker.

- Each lane has an epic issue: [#1](https://github.com/StretchGaming/Co-op-Game/issues/1) for HC, [#2](https://github.com/StretchGaming/Co-op-Game/issues/2) for PG and [#3](https://github.com/StretchGaming/Co-op-Game/issues/3) for HZ. [#4](https://github.com/StretchGaming/Co-op-Game/issues/4) holds the playable checkpoints. Every phase, asset task and ready check is a sub-issue of its lane's epic, with its sprint as the [milestone](https://github.com/StretchGaming/Co-op-Game/milestones).
- Start each commit message with the phase code and end it with the issue number, like `PG-2: split-screen on the host (#24)`. Close the issue when its "Done when" passes, with `Closes #24` in the last commit or by hand.
- Tick off the issue's steps as you go. Comment on it with anything the next sprint needs to know, such as a blocker, or an asset's source and license.
- When the plan changes, update the matching issues in the same push. The docs say what to build; the issues say who's on it and how far along it is.

## Hard rules

1. **Never use `Get Player Character (0)`, `Get Player Controller (0)` or `Get Player Pawn (0)` in gameplay Blueprints.** Use the owning player, the instigator, or the actor that triggered the event. Index 0 breaks multiplayer, and split-screen is part of Demo 1: the host machine can have two local players at once.
2. **Add HUD widgets to the owning player's screen** (`Add to Player Screen` with the owning controller), never globally to the viewport.
3. **Input goes through Enhanced Input mapping contexts added per local player.**
4. **The server decides.** Gameplay state changes (gates, plates, relics, damage, round phase) run on the server and replicate. Clients ask through Run on Server events.
5. **Every system must work at 2, 3 and 4 players.** Look up your lane's scaling table with `BP_CoopGameState.GetScalingRow()`. Never hard-code a count of 3.
6. **Stay Blueprint-only.** Do not add C++ classes or a `Source/` folder without the whole team agreeing.
7. **Every plugin must support both Mac and Windows.** Check before enabling anything from Fab or the marketplace.
8. **Only edit your own lane's folder and sublevel.** Anything else needs a lock (`git lfs lock <path>`) and a heads-up at sprint kickoff.
9. **Place actors only in your lane's sublevel.** Before spawning anything through MCP, make it the current level (in the Levels panel, double-click it). Never place actors in a persistent level (`L_Site01`, `L_Site02`). The one exception is HC, which places the player starts, the map exit and world settings there under a lock.
10. **Don't save hard references between placed actors in different sublevels.** Find another lane's actors at runtime, through the shared contracts in [docs/sprints.md](docs/sprints.md), the GameState or actor tags, and check that the reference is valid before using it.
11. **Only the GameMode changes the round phase.** Other lanes call its functions.
12. **Never edit `.uasset` or `.umap` files on disk.** Change them only through the editor.
13. **This repo is public.** Only commit assets whose license allows publishing them, and record the source and license as [docs/assets.md](docs/assets.md#licenses-this-repo-is-public) describes. Never pull a Fab or marketplace asset into the project without that check.

## Working through Unreal MCP

- The MCP server runs inside the editor, so the editor must be open.
- It runs one tool call at a time on the editor's main thread. Don't send calls in parallel.
- After a batch of changes, compile the Blueprints you touched, Save All, and check that `git status` lists only your lane's files plus any you locked.
- If the save dialog lists a file you don't own, such as `L_Site01` or another lane's sublevel, uncheck it.
- Generated assets go through [docs/assets.md](docs/assets.md): raw output in `SourceArt/<lane>/`, imports in your lane's `Art/` folder, and the source and license recorded on the asset's issue.

## Folder ownership

| Path | Owner | Lockable? |
| --- | --- | --- |
| `Content/Core/` | HC | Yes. Read-only until locked, even for the owner. |
| `Content/Maps/` (the persistent `L_Site01` and `L_Site02`) | HC | Yes |
| `Content/Shared/` | Anyone | Yes |
| `Content/Puzzles/`, including `L_Site01_HC` | HC | No |
| `Content/Player/`, including `L_Site01_PG` | PG | No |
| `Content/Hazards/`, including `L_Site01_HZ` and `L_Site02_HZ` | HZ | No |
| `SourceArt/HC/`, `SourceArt/PG/`, `SourceArt/HZ/` | Each lane | No |
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
- Open `L_Site01` and run Play In Editor with **Net Mode: Play As Client** and at least 2 players. Check your feature as a client; the host view hides most network bugs. Anything with a view, HUD or input also needs a check with a second local player in split-screen.
- Check the Output Log for errors and "Accessed None" warnings.
- Commit only your lane's files plus any you locked. Run `git pull --rebase`, push, then unlock what you locked.
