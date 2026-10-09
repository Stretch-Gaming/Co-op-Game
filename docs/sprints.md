# Sprint plan: from an empty repo to the Site 1 demo

Ten sprints take the team from an empty repo to **Demo 1**: one map, Site 1, played start to finish by 2–4 players online. Sprints are 45 minutes, or 60 minutes when they end on a playable checkpoint. The plan fits three evenings, and each evening ends with a build everyone can join and play.

Each machine has its own lane and epic, and each epic phase is one sprint. For example, VG-4 is Mac 1's work in Sprint 4.

> **Sprint 0 update (2026-10-09, 19:35).** The plan is being revised for the new direction: a cave start, first person with a switch to third person, split-screen on the host, relic collection, traps and ghosts, and puzzle rounds across maps. There's no car. The full revision follows shortly. If you haven't done these HC-0 steps yet, use the new names; if you have, rename in HC-1.
>
> - Skip the Vehicle content pack and the Chaos Vehicles plugin, and leave out the Nav Mesh Bounds Volume.
> - Sublevels: `/Game/Puzzles/L_Site01_HC`, `/Game/Player/L_Site01_PG` and `/Game/Hazards/L_Site01_HZ`. PK's lane is now PG (player view and ghosts).
> - Project Settings → Maps & Modes → Local Multiplayer: turn on Use Splitscreen and Skip Assigning Gamepad to Player 1. Engine → Local Player: set Aspect Ratio Axis Constraint to Maintain Y-FOV.
> - `E_RoundPhase`: `Lobby`, `Playing`, `Cleared`, `Failed`, `MapComplete`.
> - `BP_CoopGameState`: `GetPlayerCount()`, `GetScalingRow()`, `RoundIndex`, `RoundPhase` (RepNotify firing `OnRoundPhaseChanged`), `PhaseEndsAt` and `RelicsCollected`.
> - `BP_CoopGameMode`: `SetRoundPhase` works now. `StartRound(Index)`, `ClearRound()`, `FailRound()`, `CompleteMap()` and `AddRelics(Count)` are stubs.
> - `S_RoundScaling` and `DT_RoundScaling` (rows `2`, `3`, `4`: `PlateCount`, `StatueCount`, `RelicsPerRound`) replace the heist scaling table.

| Machine | Person | Lane | Epic |
| --- | --- | --- | --- |
| Windows (integrator + host) | Stretch | HC | [Heist core and round flow](epics/epic-heist-core.md) |
| Mac 1 | PK | VG | [Vehicle and getaway chase](epics/epic-vehicle-getaway.md) |
| Mac 2 | Ak47 | HZ | [Site, hazards and atmosphere](epics/epic-site-hazards.md) |

All three lanes build against one map layout: [map/site01-layout.md](map/site01-layout.md). Editor agent setup: [mcp.md](mcp.md).

## The demo

1. Up to four players spawn in the yard outside the site. Everyone steps on the start pad to begin.
2. A spike trap and patrolling guardians knock players down. A teammate holds Interact for 2 seconds to revive them.
3. In the plate hall, pressure plates open the vault. The number of plates and statues scales with the player count, so one player is always free to walk in.
4. Grabbing the loot starts the collapse. The vault's back wall breaks open, debris falls, and a countdown runs. Anyone still inside at zero is crushed.
5. The loot is heavy. Players carry it down the escape tunnel to the vehicle yard and stow it in the getaway car.
6. One player drives out of the yard and rival cars give chase. Passengers shoot them while the rivals ram the car.
7. Reaching the extraction zone ends the round with a results screen showing the loot secured.

The round fails if everyone is down at once or the car is destroyed.

**Stretch goals** are built only by a lane that's ahead, and never appear on a checkpoint list: the dart trap, the swinging trap, collapse path blockers, a lever that a wedge can jam, repairing the car, and extra road obstacles.

## Sprints

| Sprint | Min | Windows · Stretch · HC | Mac 1 · PK · VG | Mac 2 · Ak47 · HZ | Ends with |
| --- | --- | --- | --- | --- | --- |
| 0. Setup | 60 | Create the project, plugins, settings, map and sublevels, and push by minute 15. Stub the core contracts. | Open the project while shaders compile. Connect MCP and run the smoke test. | Open the project while shaders compile. Connect MCP. | **Playable 1** |
| 1. Blockout | 45 | Interaction: trace, prompt, hold. Input contexts per pawn. Debug keys. | Vehicle content, chase road greybox, scaling table. | Site blockout, `AC_Health` stub, scaling table. | Smoke join |
| 2. Hands | 45 | Carry and drop. | Driver: get in and out. | `AC_Health` working. Spike trap. | Smoke join |
| 3. Hands on | 60 | Heavy statues. Attach `AC_Health` and revive a teammate. | Three passenger seats. | First guardian. | **Playable 2** |
| 4. Vault | 45 | Pressure plates, vault door, puzzle scaled by player count. | Passenger shooting. First rival car. | Guardians scale with player count. | Smoke join |
| 5. Loot | 45 | Loot starts the collapse. Round HUD with countdown. | Getaway start, rivals give chase, stowing loot. | Collapse: wall breach, debris, camera shake. | Smoke join |
| 6. Heist | 60 | Start pad. Crushed at zero. | Car health and ramming. | Lighting pass. | **Playable 3** |
| 7. Endings | 45 | Ending rules, results screen, restart. | Extraction, car destroyed, rival scaling. | Sound pass. | Smoke join |
| 8. Full run | 60 | Run every ending; fix and tune. | Finish the road. Tune under network emulation. | Dust and impact effects. Tune hazards. | **Playable 4** |
| 9. Demo | 60 | Fixes, Windows performance pass, tag `demo-1`. | Fixes and chase feel. | Fixes and Mac performance check. | **Demo 1** |

That's 8 hours 45 minutes of sprints. With 10-minute breaks it fits three evenings, each ending on a checkpoint:

| Evening | Sprints | Time with breaks | Ends with |
| --- | --- | --- | --- |
| 1 | 0–3 | About 4 hours | Playable 2 |
| 2 | 4–6 | About 2 hours 50 minutes | Playable 3 |
| 3 | 7–9 | About 3 hours 5 minutes | Demo 1 |

A phase that runs over moves into the next sprint. Don't stretch a sprint to finish it; use the [cut list](#cut-list) instead. If Playable 4 slips, add one 45-minute buffer sprint before the demo.

After Demo 1, the next milestones are tool slots and the Scout, split-screen couch co-op, and Epic Online Services sessions.

## Playable checkpoints

Each checkpoint is a build anyone on the team can join and play. The times are sprint time from the start of Sprint 0, not counting breaks. A checkpoint only counts if it works for **clients**, not just the host. Test once with 2 players and once with 4; the 4th player is a second client on the Windows machine. How to host and join: [README](../README.md#playtesting).

### Playable 1: Everyone's in (end of Sprint 0, about 1:00)

- Both Macs and a second Windows client join the Windows host, so the session holds 4 players.
- Everyone runs and jumps around the level's floor and sees the others move smoothly.

### Playable 2: Hands on (end of Sprint 3, about 3:30)

- Walk the Site 1 blockout from the spawn yard to the vehicle yard.
- Pick up, carry and drop crates and statues. Statues slow you down. Every client sees the same thing.
- The spike trap knocks you down, and a teammate holds Interact to revive you.
- A guardian patrols the entrance hall, chases whoever it sees, and knocks them down.
- Up to four players pile into the getaway car. One drives, three ride along, and anyone can get out.

### Playable 3: Into the vault (end of Sprint 6, about 6:00)

- Everyone steps on the start pad to begin, and the HUD shows the phase and countdown.
- Open the vault with 2 players using statues, and with 4 players facing more plates and more guardians.
- Grabbing the loot breaks the vault's back wall open. Debris falls after a warning circle, and every screen shakes.
- Anyone still inside when the countdown reaches zero is crushed.
- Carry the loot to the car and stow it. Drive out of the yard; a rival gives chase, and passengers shoot it.

### Playable 4: Full run (end of Sprint 8, about 7:45)

- One full run from the start pad to the results screen with no debug keys, once with 2 players and once with 4.
- Rivals ram the car and its health drops.
- The host restarts the round from the results screen, and every client reconnects.
- Every ending was checked during Sprint 8: extraction, everyone down, the car destroyed, and being crushed by the collapse.

### Demo 1 (end of Sprint 9, about 8:45)

- The full run is fun at 2, 3 and 4 players, lit and with sound.
- The demo commit is tagged `demo-1`.

## Sprint rhythm

**45-minute sprint**

| Time | What happens |
| --- | --- |
| 0:00 | Kickoff, 3 minutes. Confirm your phase, name any locks you need, and log it in [SPRINT_LOG.md](../SPRINT_LOG.md). |
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
| 0:45 | Playtest, 10 minutes. Run the checkpoint list above once with 2 players and once with 4. |
| 0:55 | Retro, 5 minutes. Keep, cut or change. Use the cut list if a lane is behind. |

## Shared contracts

Lanes depend on each other only through these. **Stub by** is the sprint when the asset exists with its final names and inputs. **Works by** is when other lanes can rely on its behavior. Changing a contract after its stub needs a heads-up at kickoff.

Don't save hard references between placed actors in different sublevels; Unreal can't keep them. Find another lane's actors at runtime, through these contracts, the GameState or actor tags, and check that the reference is valid before you use it.

| Contract | Owner | Stub by | Works by | What it is |
| --- | --- | --- | --- | --- |
| `Content/Core/BPI_Interactable` | HC | 0 | 1 | `GetInteractInfo(Instigator)` returns a prompt and a hold time in seconds (0 means instant). `CanInteract(Instigator)` returns a bool. `Interact(Instigator)` runs on the server only, after the server rechecks distance and `CanInteract`. |
| `Content/Core/BP_CoopCharacter` | HC | 0 | 1–3 | The player character, a child of the template character. The interact trace works in Sprint 1. Server-only `GetCarried()` and `ReleaseCarried()` work in Sprint 2. `AC_Health` and revive work in Sprint 3. |
| `Content/Heist/BP_Carryable` | HC | 2 | 2 | Pick up, carry and drop. `bHeavy` halves the carrier's speed and holds a pressure plate. `bIsLoot` and `LootValue`. |
| `Content/Core/BP_CoopGameMode` | HC | 0 | 0, and `RequestEndRound` in 7 | A child of GameMode, not GameModeBase. The only place the round phase changes. Server-only `SetRoundPhase(Phase)`, `NotifyGetawayStarted()` (moves `Collapse` to `Getaway`), and `RequestEndRound(bSuccess, LootValue, Reason)`. The first ending wins, and later calls are ignored. |
| `Content/Core/BP_CoopGameState` | HC | 0 | 0 | A child of GameState. `GetPlayerCount()` counts PlayerStates. `GetScalingRow()` returns the row name `2`, `3` or `4`; a solo test uses `2`. `RoundPhase` (RepNotify) fires `OnRoundPhaseChanged(NewPhase)` on the server and every client. `PhaseEndsAt` in server time (0 means no countdown). `LootSecured`, `EndReason`. |
| `Content/Core/E_RoundPhase` | HC | 0 | 0 | `Lobby`, `Heist`, `Collapse`, `Getaway`, `Extracted`, `Failed`. Every lane stops spawning and damage once the phase is `Extracted` or `Failed`. |
| Debug keys in `BP_CoopPlayerController` | HC | — | 1 | Host only. F1 starts `Heist`; press it after everyone has joined. F2 starts `Collapse`. F3 ends the round as a success and F4 as a failure; both do nothing until Sprint 7. |
| Input contexts | HC for the character and controller, VG for the car and seats | — | 1 | Each pawn adds its own mapping context in Receive Controller Changed when a local player takes it, and removes only that context when the player leaves. Nobody calls Clear All Mappings. Controller-wide keys, such as the debug keys, live in a separate context that `BP_CoopPlayerController` adds once. |
| `Content/Hazards/AC_Health` | HZ | 1 | 2 | Player health only. `Health`, `MaxHealth`, `bDowned` (RepNotify). `IsDowned()`, `CanBeRevived()`, and server-only `Revive(Reviver)` and `ForceDown(bAllowRevive)`. `OnDowned` and `OnRevived` fire on the server. Damage arrives through `Apply Damage` on the owner. |
| `Content/Vehicle/BP_GetawayVehicle` | VG | 2 | 2–6 | Implements `BPI_Interactable`: get in (Sprints 2–3), or stow carried loot (Sprint 5). Holds `LootInVehicle`. Car and rival health belong to VG, not `AC_Health`. |
| `BP_GetawayStartTrigger` | VG | 5 | 5 | Calls `NotifyGetawayStarted()` when the car leaves the yard with a driver during `Collapse`. Rivals spawn when the phase becomes `Getaway`. |
| `BP_ExtractionZone`, and the car being destroyed | VG | 7 | 7 | Extraction calls `RequestEndRound(true, LootInVehicle, ...)`. A destroyed car calls `RequestEndRound(false, 0, ...)`. |
| Scaling tables | Each lane, in its own folder | HC 0, VG and HZ 1 | When first used | `DT_HeistScaling`, `DT_VehicleScaling` and `DT_HazardScaling`, each with rows `2`, `3` and `4`, looked up with `GetScalingRow()`. Read them when the phase becomes `Heist`, never at BeginPlay, when the host may still be alone. Players who join mid-round don't change the scaling until the next round. |
| `/Game/Maps/L_Site01` and its sublevels | HC for the persistent level, each lane for its sublevel | 0 | 0 | The persistent level holds only player starts, nav bounds and world settings, which HC places under a lock. `L_Site01_HC`, `L_Site01_VG` and `L_Site01_HZ` are always loaded, and each lane places actors only in its own. |

## Cut list

If a lane falls behind, cut in this order rather than move a checkpoint. Each cut says what comes off the checkpoint lists with it.

1. Any stretch goal still in progress. Nothing comes off a checkpoint.
2. Debris damage. Debris still falls and the screen still shakes; only the damage goes.
3. Rival ramming. "Rivals ram the car" and the car-destroyed ending come off Playable 4.
4. The start pad. Replace it with a Start interaction the host uses in the spawn yard, so the checkpoints still need no debug keys.
5. Sound and lighting beyond the first pass. Demo 1 ships with greybox lighting.

Never cut joining at 2–4 players, interact and carry, knockdown and revive, the plate puzzle, or loot → collapse → car → extraction → results.

## Risks

| Risk | What we do |
| --- | --- |
| The Macs' first open of the project takes a long time while shaders compile. | Sprint 0 is setup only for the Macs: open the project, connect MCP, join. Windows pushes the bare project by minute 15. |
| Mac clients can't join the Windows host. | Playable 1 tests it first. Check the same engine version and commit, the Windows firewall, and UDP port 7777. See the [README](../README.md#playtesting). |
| Epic's MCP tools can't wire Blueprint graphs. | The Sprint 0 smoke test records what they can do in [mcp.md](mcp.md). Agents scaffold assets, place actors and set properties; people wire the graphs. |
| The car feels laggy or jittery on clients, or rivals push it around. | VG tests as a client under network emulation from Sprint 2. Rivals are spline followers that overlap the car instead of blocking it, so they can't push it differently on each machine. |
| Networked features take longer than a sprint. | Each phase is sized for about 30 minutes, an extra build sprint sits before Playables 2 and 3, and stretch goals stay off the checkpoint lists. |
| The org runs out of Git LFS storage or bandwidth. | Check the org's LFS usage on GitHub after the first session. |
