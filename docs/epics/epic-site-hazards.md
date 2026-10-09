# Epic: Site, hazards and atmosphere (HZ)

**Machine:** Mac 2 · **Owner:** Ak47 · **Sublevel:** `L_Site01_HZ`

## Relationship to other epics (read first)

HZ builds the site the other lanes play in, and everything in it that hurts players: the spike trap, guardians and the collapse. It also owns lighting, atmosphere and sound. `AC_Health` is HZ's contract: [HC](epic-heist-core.md) attaches it to the player character, and every source of player damage goes through it. [VG](epic-vehicle-getaway.md) builds on the vehicle yard's ground. The sprint table, playable checkpoints and contracts, with when each one works, are in [docs/sprints.md](../sprints.md). Room positions are in [docs/map/site01-layout.md](../map/site01-layout.md).

## Context

Hazards are self-contained actors in their own folder and sublevel, so this lane rarely needs a lock. That leaves room to also own the site blockout. The layout doc fixes every room's position, so HC can place puzzles and VG can place the car without waiting on HZ.

## Locked decisions

- HZ owns the site blockout (floors, walls, ceilings, ramps) and the sun, sky, fog and post-process, all in `L_Site01_HZ`. Announce layout changes at kickoff, because the other lanes build on it.
- `AC_Health` covers player health, knockdown and revive only. VG owns car and rival health. All player damage goes through `Apply Damage`.
- Downed players can't move. A teammate revives them with a hold interaction. There's no bleed-out or death in Demo 1.
- Guardians are Characters with a simple AI that runs on the server: patrol, see, chase, hit. The nav mesh is generated at runtime.
- The collapse is split. HC owns the countdown and who gets crushed when it ends. HZ owns everything players see and hear, plus debris damage.
- The server decides when a hazard fires, and every machine replays it from replicated state: RepNotify for state changes, server time for timing, and small replicated actors for anything that warns players before it hurts them. Unreliable multicasts are only for cosmetic effects, such as dust and sound.
- Camera shakes use `Play World Camera Shake`, which reaches every local player without a player index.

## Non-goals (for Demo 1)

- Bleed-out, death and spectating.
- Chaos Destruction and geometry collections. Falling props are enough.
- Behavior trees with EQS.
- Final art.
- Stretch goals, only if this lane is ahead: the dart trap, the swinging log and collapse path blockers.

## Dependencies and sequencing

- HZ-0 needs HC-0's bare project.
- HZ-2's `AC_Health` is a hard gate for Playable 2. It must be merged by the end of Sprint 2 so HC-3 can wire revive; if it isn't, finish it first thing in Sprint 3.
- HZ-4's spawner reads the player count when the phase becomes `Heist`. Until HC-6's start pad, the host presses F1 once everyone has joined.
- HZ-5 reacts to the `Collapse` phase. Use F2 (HC-1) until HC-5's loot triggers it.

## Phases

### HZ-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, run `Tools/check-mac.command` until it passes.

- At about minute 15, pull the bare project and open it. The first open compiles shaders for a while.
- Meanwhile, set up MCP with [docs/mcp.md](../mcp.md) and run its smoke test once the editor is up. Tell VG about anything that behaves differently on your machine.
- Join Playable 1.

### HZ-1: Blockout (Sprint 1, 45 min)

- Make `L_Site01_HZ` the current level. Have your agent block out Site 1 from the layout table with the template's level prototyping meshes: spawn yard, walkway, entrance hall, trap corridor, plate hall, vault, escape tunnel and vehicle yard. Leave the gap in the vault's south wall open for now.
- Once the blockout's floors are in, delete the Basic level's floor. Keep the sun, sky and fog, and set a readable midday light.
- Stub `AC_Health` with its variables, dispatchers and empty functions.
- Create `S_HazardScaling` and `DT_HazardScaling` with rows `2`, `3` and `4`: `GuardianCount`, `SpikeDelay`, `DebrisInterval` and `ReviveSeconds`.
- If the editor keeps marking `L_Site01` as changed after you move geometry, turn off automatic navigation updates in Editor Preferences, and never save that level.

### HZ-2: Health and the spike trap (Sprint 2, 45 min)

- `AC_Health`, on the server: bind the owner's OnTakeAnyDamage, subtract the damage, and go down at 0. The `bDowned` RepNotify stops movement on every machine and shows a simple downed look, such as a tint. No ragdoll yet.
- `Revive(Reviver)` restores half health, but only if `CanBeRevived()`. `ForceDown(bAllowRevive)` downs the player at once, and with `false` they can't be revived. `OnDowned` and `OnRevived` fire on the server.
- For testing before HC-3 wires revive: `BP_HZ_TestCharacter` (a child of `BP_CoopCharacter` with the component added), a test GameMode for `L_HZ_Test`, and `BP_HZ_TestReviveTrigger`, which revives anyone standing in it.
- `BP_Trap_Spikes` in the trap corridor: a plate that raises spikes after `SpikeDelay` and damages any pawn on it. Start with 0.6 seconds for 2 players, 0.5 for 3 and 0.4 for 4.

### HZ-3: First guardian (Sprint 3, 60 min) → Playable 2

- `BP_Guardian`, a Character, with `AIC_Guardian` as its AI Controller Class and Auto Possess AI set to **Placed in World or Spawned**, so spawned guardians get a controller too.
- AI Perception with sight. Blueprints can't set teams, so turn on Detect Neutrals, then ignore anything that isn't a player character, or that is downed.
- It patrols between `BP_PatrolPoint` actors, chases with AI MoveTo (retrying if the nav mesh isn't built yet), and hits in melee range with `Apply Damage`; two hits down a player. It goes back to patrolling after losing sight for 5 seconds.
- Place one guardian in the entrance hall.
- Join Playable 2.

### HZ-4: Guardian scaling (Sprint 4, 45 min)

- `BP_GuardianSpawner`, on the server only: when the phase becomes `Heist`, spawn `GuardianCount` guardians on their patrol routes. Start with 1 guardian for 2 players, 2 for 3 and 3 for 4.
- Remove the guardian placed in HZ-3, so the spawner is the only source.
- Guardians stop once the phase is `Extracted` or `Failed`.

### HZ-5: Collapse (Sprint 5, 45 min)

`BP_CollapseDirector` listens to `OnRoundPhaseChanged`. When the phase becomes `Collapse`:

- `BP_BreachWall`, which fills the gap in the vault's south wall, breaks open. Its replicated `bBreached` hides it and turns off its collision on every machine, then plays dust and sound.
- Debris falls in the vault and tunnel, every `DebrisInterval` seconds. For each rock, the server spawns a small replicated `BP_DebrisImpact` actor holding where it lands and the server time it lands. Every machine shows the warning circle from that actor and drops a cosmetic rock, with no collision, to land on time. The server applies the damage once, at that time.
- Everyone nearby gets a camera shake and a rumble.

### HZ-6: Lighting (Sprint 6, 60 min) → Playable 3

- A lighting pass for the site's mood: sun angle, fog, a few torches, and a post-process volume.
- Join Playable 3.

### HZ-7: Sound (Sprint 7, 45 min)

- Ambience for the site.
- Sounds for the spike trap, guardians, the breach and debris.
- A sting when the collapse starts.

### HZ-8: Effects and tuning (Sprint 8, 60 min) → Playable 4

- Dust and impact effects for the breach and the debris.
- Tune `DT_HazardScaling` from the 2-player and 4-player runs.
- Join Playable 4.

### HZ-9: Demo (Sprint 9, 60 min) → Demo 1

- Fix what Playable 4 found. Make sure 2 players aren't overwhelmed and 4 aren't bored.
- Mac performance check. If a Mac drops below 30 fps, lower its scalability settings rather than cutting content.

## Critical assets

- `Content/Hazards/`: `AC_Health`, `BP_Trap_Spikes`, `BP_Guardian`, `AIC_Guardian`, `BP_PatrolPoint`, `BP_GuardianSpawner`, `BP_CollapseDirector`, `BP_BreachWall`, `BP_DebrisImpact`, `S_HazardScaling`, `DT_HazardScaling`, `L_Site01_HZ`
- `Content/Hazards/Test/`: `L_HZ_Test`, `BP_HZ_TestCharacter`, `BP_HZ_TestReviveTrigger`

## Build and playtest notes

- Fire hazards only on the server, then show them everywhere. A trap that only works for the host is the most common bug in this lane.
- Test downed and revive with two clients, not with the host and one client.
- Lighting looks different on Mac and Windows. Windows makes the final call in HC-9.

## Verification

- HZ-0: both Macs join Playable 1.
- HZ-1: a player walks the whole blockout, from the spawn yard across the walkway to the vehicle yard, and the `AC_Health` stub compiles alongside HC's character.
- HZ-2: a client who steps on the spikes goes down on every screen, and the test trigger revives them. `ForceDown(false)` leaves a player who can't be revived.
- HZ-3: the guardian chases and downs a client, then goes back to patrolling.
- HZ-4: after F1, the guardian count matches the player count.
- HZ-5: F2 or the loot breaks the wall open so players can walk through, and debris lands only where its warning appeared, on every machine.
- HZ-6: Playable 3 passes.
- HZ-7: every sound plays on every machine.
- HZ-8: Playable 4 passes.
- HZ-9: Demo 1 passes.

## Open questions

- What is the site? An ancient temple, a modern bank, or something else? The blockout works for any of them, but the lighting pass in HZ-6 needs an answer.
