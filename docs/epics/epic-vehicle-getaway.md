# Epic: Vehicle and getaway chase (VG)

**Machine:** Mac 1 · **Owner:** PK · **Sublevel:** `L_Site01_VG`

## Relationship to other epics (read first)

VG builds the getaway car, its seats, the rival chase and the extraction zone. It depends on contracts from [HC](epic-heist-core.md): interaction, input contexts, carrying, round phases and ending the round. From [HZ](epic-site-hazards.md) it needs only the vehicle yard's ground and the tunnel to it. The sprint table, playable checkpoints and contracts, with when each one works, are in [docs/sprints.md](../sprints.md). Road and yard positions are in [docs/map/site01-layout.md](../map/site01-layout.md).

## Context

The Macs are always clients in playtests, so this lane sees the car's lag and jitter exactly as players will. Vehicle physics is the riskiest networked feature in the demo, which is why it has its own lane and gets tested as a client from its first phase.

## Locked decisions

- The car comes from Unreal's Vehicle template (Chaos Vehicles). The template folder that HC-0 adds belongs to VG, so VG uses it in place rather than moving it. VG's own assets go in `Content/Vehicle/`.
- The driver possesses the car. Each passenger possesses a `BP_PassengerSeat` pawn attached to the car, with its own camera and fire input.
- The first time a character gets in, the car adds `AC_Seated` to it on the server, with replication on, and keeps it. `AC_Seated` replicates `bSeated`, and one function, run by its RepNotify on every machine, applies the state: seated hides the character and turns off its collision and movement; not seated restores them. `BP_CoopCharacter` doesn't change for this.
- Each seat, including the driver's, stores its occupant's character so getting out can return the player to it.
- Server requests go through the pawn the player possesses: the car for the driver, the seat for a passenger. The server checks the requester really is in that seat.
- Rivals are spline followers, not physics cars. They overlap the car and never block it, so they can't push it differently on each machine.
- Car and rival health live on those actors and belong to VG. `AC_Health` is for players only.
- The round ends only through the GameMode's functions.

## Non-goals (for Demo 1)

- Physics cars driven by AI, damage models beyond a health bar, more than one getaway car, and client-side vehicle prediction.
- Stretch goals, only if this lane is ahead: repairing the car from the rear seat, road obstacles and a ramp.

## Dependencies and sequencing

- VG-0 needs HC-0's bare project.
- VG-2 needs HC-1's interaction and the input-context rule, both from Sprint 1.
- VG-5's stowing needs `GetCarried()` and `ReleaseCarried()` from HC-2. Test it with any carryable that has `bIsLoot` turned on, since `BP_Loot` arrives in the same sprint (HC-5).
- `NotifyGetawayStarted()` works from Sprint 0. `RequestEndRound` works from HC-7, in the same sprint as VG-7; test with F3 and F4 until then.
- Players can only walk to the yard after HZ-5 breaks the vault wall open. Until then, the blockout leaves the tunnel open.

## Phases

### VG-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, run `Tools/check-mac.command` until it passes. It checks for Unreal 5.8.3, Xcode 26.0–26.3 with the Metal toolchain, and enough disk space.

- At about minute 15, pull the bare project and open it. The first open compiles shaders for a while.
- Meanwhile, set up MCP with [docs/mcp.md](../mcp.md) and run its smoke test once the editor is up. VG owns that doc, so record what the tools can do there and push it.
- Join Playable 1.

### VG-1: The car and the road (Sprint 1, 45 min)

- In the vehicle template folder, pick a car that seats four, such as the template's offroad car if 5.8 has one. Make `BP_GetawayVehicle` in `Content/Vehicle/` as its child.
- Make `L_Site01_VG` the current level. Greybox the road from the vehicle yard to the extraction zone, about 700 m with two wide bends, per the layout doc. Lay `BP_ChaseSpline` along it, and put the car in the yard.
- Create `S_VehicleScaling` and `DT_VehicleScaling` with rows `2`, `3` and `4`: `RivalCount`, `RivalHealth`, `RamDamage` and `CarHealth`.
- Drive it in single-player Play In Editor.

### VG-2: Driver (Sprint 2, 45 min)

- `BP_GetawayVehicle` implements `BPI_Interactable`. When nobody is driving, `Interact` makes the instigator the driver on the server: store the character, set `bSeated` on its `AC_Seated`, attach it, and possess the car.
- An Exit input on the car sends a Run on Server event from the car, which the driver owns. The server re-possesses the stored character, detaches it beside the door (or the other door if that's blocked), and clears `bSeated`.
- The car adds `IMC_Vehicle` in Receive Controller Changed when a local player takes it, and removes it when they leave. Never clear all mappings.
- Test as a client with network emulation on (Editor Preferences → Level Editor → Play → Multiplayer Options), driving from a Mac.

### VG-3: Passenger seats (Sprint 3, 60 min) → Playable 2

- The car spawns three `BP_PassengerSeat` pawns on the server and attaches them to seat sockets with their collision off.
- `Interact` on a car that already has a driver seats the player in the first free seat the same way: store the character, set `bSeated`, attach, then possess the seat. Each seat has a spring-arm camera for looking around, and `IMC_Passenger`, added and removed the same way as the car's.
- Exit is a Run on Server event on the seat. The server returns the player to their stored character beside the car.
- Get in and out of every seat several times in a row, with four players.

### VG-4: Shooting and the first rival (Sprint 4, 45 min)

- `IA_Fire` in `IMC_Passenger`. The seat sends its aim through a Run on Server event; the server line-traces and calls `Apply Damage`. An unreliable multicast plays the muzzle flash and impact, which are cosmetic.
- `BP_RivalCar` follows `BP_ChaseSpline`. The server replicates one struct holding its distance along the spline, its speed and the server time it was set. Every machine places the rival from the spline each frame, extrapolating from that struct, which keeps it smooth at speed.
- Rivals take damage through their own `Event AnyDamage` and stop when their health runs out. Their collision overlaps the car and never blocks it.
- For now, spawn one rival from a debug trigger in `L_VG_Test`.

### VG-5: Getaway and stowing loot (Sprint 5, 45 min)

- `BP_GetawayStartTrigger` at the yard exit: when the car leaves with a driver during `Collapse`, call `NotifyGetawayStarted()`. When the phase becomes `Getaway`, spawn one rival at the spline's east end, behind the car.
- If the instigator is carrying something with `bIsLoot` on, `Interact` stows it instead of seating them. Call `ReleaseCarried()`, attach the loot hidden in the trunk with physics and collision off, and add its `LootValue` to `LootInVehicle`. Each item counts once.

### VG-6: Car health and ramming (Sprint 6, 60 min) → Playable 3

- The car has replicated `Health`, taken from `CarHealth` and damaged through its own `Event AnyDamage` on the server. The driver's and passengers' HUDs show it on the owning player's screen.
- A rival overlapping the car damages it on the server by `RamDamage`, with a short cooldown.
- Join Playable 3.

### VG-7: Extraction (Sprint 7, 45 min)

- `BP_ExtractionZone`: the car entering it calls `RequestEndRound(true, LootInVehicle, "Extracted")`.
- When the car's health reaches 0, disable it and call `RequestEndRound(false, 0, "The getaway car was destroyed")`.
- The rival count comes from `DT_VehicleScaling`: 1 rival for 2 players, 2 for 3 and 3 for 4.
- Rivals stop and nothing more spawns once the phase is `Extracted` or `Failed`.

### VG-8: The road (Sprint 8, 60 min) → Playable 4

- Finish the road: a narrow section and a tall beacon at extraction.
- Tune speeds, rival pacing and damage under network emulation, from a Mac.
- If other players see the car jitter, tune its replication settings and test again as a client.
- Join Playable 4.

### VG-9: Demo (Sprint 9, 60 min) → Demo 1

- Fix what Playable 4 found. Tune for 2 players (one driver, one shooter, fewer rivals) and for 4.
- Chase feel: camera, top speed, and the moment the rivals appear.

## Critical assets

- `Content/Vehicle/`: `BP_GetawayVehicle`, `BP_PassengerSeat`, `AC_Seated`, `BP_RivalCar`, `BP_ChaseSpline`, `BP_GetawayStartTrigger`, `BP_ExtractionZone`, `IMC_Vehicle`, `IMC_Passenger`, `IA_Fire`, `S_VehicleScaling`, `DT_VehicleScaling`, `L_Site01_VG`
- `Content/Vehicle/Test/L_VG_Test`
- The vehicle template folder that HC-0 adds
- `docs/mcp.md`

## Build and playtest notes

- You're a client in every playtest. If the car feels wrong on your Mac, it is wrong.
- LAN latency is tiny. Before you call the car done, drive it with network emulation set to an average internet profile.

## Verification

- VG-0: the smoke test results are in `docs/mcp.md`, and both Macs join Playable 1.
- VG-1: the car drives in single-player Play In Editor on both Macs and on Windows.
- VG-2: a client gets in, drives and gets out, and is visible and walking again afterwards. The host and the other client see smooth movement.
- VG-3: four players ride at once, and getting in and out of every seat works repeatedly.
- VG-4: a passenger shoots a rival until it stops, and every machine sees the same thing.
- VG-5: leaving the yard during `Collapse` starts `Getaway` and a rival chases. Loot stowed by a client shows up in `LootInVehicle` on the server, once.
- VG-6: a rival touching the car lowers its health on every HUD, and the car isn't pushed off course.
- VG-7: reaching extraction ends the round as a success, and a destroyed car ends it as a failure.
- VG-8: Playable 4 passes.
- VG-9: Demo 1 passes.

## Open questions

- Which car? The template's offroad car, or a free one from Fab? It must seat four.
