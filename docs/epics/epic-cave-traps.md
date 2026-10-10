# Epic: Cave, traps and atmosphere (HZ)

**Machine:** Mac 2 · **Owner:** Ak47 · **Folder:** `Content/Hazards/` · **Sublevels:** `L_Site01_HZ`, and `L_Site02_HZ` from Sprint 7

## Relationship to other epics (read first)

HZ builds the places the game happens in and the traps that make them dangerous: the cave and its light, the spike, dart and swinging traps, the trap corridor for Round 2, the hall for Round 3, Map 2's antechamber, and the game's sound. `AC_Health` is HZ's contract: [HC](epic-core-rounds.md) puts it on the player character, and every source of player damage, from traps to [PG](epic-player-ghosts.md)'s ghosts, goes through it. The sprint table, checkpoints and contracts are in [docs/sprints.md](../sprints.md), room positions in [docs/map/site01-layout.md](../map/site01-layout.md), and the asset pipeline in [docs/assets.md](../assets.md).

## Context

The first sprints build a small cave the team can walk around in and keep improving: geometry and the light it needs first, then textures, traps, props and atmosphere, a little each sprint. Because HZ owns the layout, the other lanes build their puzzles, ghosts and zipline into HZ's rooms at the positions in the layout doc, without waiting on HZ.

## Locked decisions

- HZ owns the blockout (floors, walls, ceilings, ramps), the cave's light and atmosphere, and Map 2's room, all in HZ's sublevels. Announce layout changes at kickoff, because the other lanes build on them.
- The cave is dark. Light comes from a shaft of daylight through a crack in the spawn cavern's ceiling, from torches and from glowing crystals, with Lumen for bounce light. Players' headlamps do the rest.
- `AC_Health` covers player health and death only, with Component Replicates on. All player damage goes through `Apply Damage`.
- Lethal damage kills players immediately. There is no downed state, bleed-out or teammate revive. Dead players cannot move or interact, drop carried items and release held mechanisms. They stay dead until HC's GameMode-controlled checkpoint or round restart; a team wipe restarts everyone at the latest checkpoint.
- The server decides when a trap does damage, and every machine knows in advance when that will be. Traps replicate a schedule (a start time in server time plus an interval or speed) or the moment they were triggered, and every machine shows the warning from it. Unreliable multicasts are only for cosmetic effects, such as dust and sound.
- Traps run all the time, not only during rounds, so the cave stays dangerous to explore. Their timing scales through `DT_HazardScaling`, using `RoundState.ScalingRow`.

## Non-goals (for Demo 1)

- Downed state, bleed-out, revives and spectating.
- Chaos Destruction and geometry collections.
- Final art. Generated assets replace the greybox where they pass review.
- Stretch goals, only if this lane is ahead: a rolling boulder, and a cave-in as the map's finale.

## Dependencies and sequencing

- HZ-0 needs HC-0's bare project.
- HZ-2's `AC_Health` is a hard gate for Playable 2. It must be merged by the end of Sprint 2 so HC-3 can wire death handling and checkpoint restarts; if it isn't, finish it first thing in Sprint 3.
- HC places the key relic at (70, 25) in Sprint 4. HZ-4 builds the nook and its trap around that spot, without moving it.
- HZ-5's fall volume kills players through `Apply Damage` and `AC_Health`. HC-3 handles the checkpoint restart only when the whole team is dead.
- HZ-7's Map 2 room goes into HC-0's `L_Site02`, which HC-7 brings in as a sublevel in the same sprint.

## Phases

### HZ-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, run `Tools/check-mac.command` until it passes.

- At about minute 15, pull the bare project and open it. The first open compiles shaders for a while.
- Meanwhile, set up MCP with [docs/mcp.md](../mcp.md) and run its smoke test once the editor is up. Tell PG about anything that behaves differently on your machine.
- Join Playable 1.

### HZ-1: The cave (Sprint 1, 45 min)

- Make `L_Site01_HZ` the current level. Have your agent block out the cave from the layout table with the template's level prototyping meshes: the spawn cavern, the passages, chambers 1 to 3, the trap corridor and key relic nook, the exit ledge, and the walkway down to the map exit. Geometry you can walk through matters more than detail; dressing comes later.
- Only the light the cave needs to be playable: delete the Basic level's floor once the blockout's floors are in, turn the sky light down to near black, let the sun in only through a crack in the spawn cavern's ceiling, with volumetric fog so the shaft shows, and add a few warm torch lights and cold crystal lights on greybox shapes.
- Stub `AC_Health` with Component Replicates on, and its variables, dispatchers and empty functions.
- Create `S_HazardScaling` and `DT_HazardScaling` with rows `2`, `3` and `4`: `SpikeDelay`, `DartInterval` and `SwingSpeed`. There is no revive-duration field.

### HZ-2: Health and spikes (Sprint 2, 45 min)

- `AC_Health`, on the server: bind the owner's OnTakeAnyDamage, ignore damage if already dead, subtract damage and clamp health to 0. At 0, set `bDead` and fire `OnDied` once. The `bDead` RepNotify applies death on every machine: disable movement and interaction and show a simple death look, such as a tint. Dead players no longer hold pressure plates or levers and are ignored by ghosts.
- `IsDead()` exposes the authoritative death state. Server-only `ResetHealth()` restores full health and clears `bDead` only during a GameMode-controlled checkpoint or round restart; the RepNotify restores movement and interaction. There is no revive function or teammate reset path.
- For testing before HC-3 wires death handling: `BP_HZ_TestCharacter` (a child of `BP_CoopCharacter` with the component added) and a test GameMode for `L_HZ_Test`. The test GameMode resets health only when restarting the test after a team wipe; walking into a trigger cannot restore a dead player.
- `BP_Trap_Spikes`: stepping on the plate replicates the server time it was triggered; every machine plays a click and a rumble from that, and the server raises the spikes and does damage after `SpikeDelay`. Put the first one in the passage from the spawn cavern, where it teaches players to watch the floor. Start with 0.6 seconds for 2 players, 0.5 for 3 and 0.4 for 4.

### HZ-3: Darts and the first textures (Sprint 3, 60 min) → Playable 2

- `BP_Trap_Darts`: a wall launcher that fires across the trap corridor on a schedule. It replicates a start time and `DartInterval`, so every machine knows when each volley comes and shows a warning half a second before it; the server does the damage at the same moments.
- Put HZ-A1's cave surfaces on the blockout.
- Once HC-3 has `AC_Health` on the real character, remove it from `BP_HZ_TestCharacter`, so there's only one.
- Join Playable 2.

### HZ-4: Swing and Round 2's corridor (Sprint 4, 45 min)

- `BP_Trap_Swing`: a swinging log whose angle comes from server time, its replicated start time and `SwingSpeed`, so every machine computes the same swing. The server damages whatever it hits.
- Round 2's trap corridor: darts, the swinging log and spikes, timed so a player carrying the key relic at half speed can get through by watching the rhythm.
- The key relic nook around HC's key relic at (70, 25), with spikes guarding the way in.

### HZ-5: Round 3's hall (Sprint 5, 45 min)

- Round 3's hall: dark apart from a few crystals, with two swinging logs, spikes and darts set between PG's gate and exit lever, at the positions in the layout doc. PG builds the round on it in Sprint 6.
- `BP_FallVolume` under the chasm at the exit ledge: on the server, apply lethal damage through `Apply Damage` so a fall kills the player. It does not teleport or reset them individually; HC's GameMode handles the checkpoint restart after a team wipe.

### HZ-6: Light and props (Sprint 6, 60 min) → Playable 3

- Second light pass with HZ-A2's props: real torches and crystals, and a stalagmite or two. Make each chamber's way forward the brightest thing in view.
- Atmosphere across the cave: height fog, drifting dust and dripping water.
- Join Playable 3.

### HZ-7: Map 2 (Sprint 7, 45 min)

- `/Game/Hazards/L_Site02_HZ`, Map 2's antechamber: a 20 m square room in sandstone, two braziers for light, hieroglyphs on the walls, and a sealed door that says the way on opens later. Use HZ-A5's kit.

### HZ-8: Dressing and trap meshes (Sprint 8, 45 min)

- Swap HZ-A3's trap meshes in for the greybox traps, and dress the chambers with HZ-A4's pieces, without moving any of the positions in the layout doc.

### HZ-9: Sound and tuning (Sprint 9, 60 min) → Playable 4

- Sound pass with HZ-A6: cave ambience and drips, torch crackle, and a sound for every trap, played as 3D sound. Trap sounds play from the same schedules as their warnings.
- Tune `DT_HazardScaling` from the 2-player and 4-player runs.
- Join Playable 4.

### HZ-10: Effects and Mac performance (Sprint 10, 45 min)

- Effects: dust when the spikes fire, splinters when a log hits, embers from the torches.
- Mac performance check. If a Mac drops below 30 fps, lower its scalability settings rather than cutting content.

### HZ-11: Demo (Sprint 11, 60 min) → Demo 1

- Final fixes.

## Asset generation

Follow [docs/assets.md](../assets.md) for specs, licensing, imports and reviews. Raw output goes in `SourceArt/HZ/`, imported assets in `Content/Hazards/Art/`. Early deliveries are deliberately small: one material family or a few props.

| Task | Sprint | Assets | Specs | Used in |
| --- | --- | --- | --- | --- |
| HZ-A1: Cave surfaces | 2 | One material family: tileable rock walls and the cave floor (damp rock and grit). The ceiling reuses the wall material. Also the atmosphere preset: a post-process volume with a color grading LUT, and fog in the shadow color from [art/style.md](../art/style.md#palette). In place by Sprint 3. | 2K tileable textures with a painted look, used through world-aligned instances of `M_Stylized`. | HZ-3 |
| HZ-A2: Props and light sources | 4 | A wall torch with a flame, a crystal cluster that glows, and one or two stalagmites. Library props from Fab are fine. In place by Sprint 6. | Props up to 20k triangles with Nanite on for opaque ones. If the crystal material is translucent, turn Nanite off for it. The crystal glow must be adjustable. | HZ-6 |
| HZ-A3: Trap meshes | 5 | A spike plate with spikes, a dart launcher carved into a wall, and darts. In place by Sprint 8. | Plates 2 m square. Simple collision; the damage volumes stay in the Blueprints. | HZ-8 |
| HZ-A4: Dressing | 6 | A swinging log or blade with its chain, carved pillars, bones and old rope. In place by Sprint 8. | The log pivots at its top. | HZ-8 |
| HZ-A5: Map 2 kit | 6 | Sandstone wall and floor materials, an Egyptian pillar, hieroglyph decals, a brazier. In place by Sprint 7. | 2K textures. Decals as material instances. | HZ-7 |
| HZ-A6: Cave and trap sounds | 8 | Cave ambience, drips, torch crackle, and sounds for the spikes, darts and swinging log. In place by Sprint 9. | Mono WAV, 48 kHz, except stereo ambience. Ambience loops cleanly. | HZ-9 |

## Critical assets

- `Content/Hazards/`: `AC_Health`, `S_HazardScaling`, `DT_HazardScaling`, `L_Site01_HZ`, `L_Site02_HZ`, `Art/`
- `Content/Hazards/Traps/`: `BP_Trap_Spikes`, `BP_Trap_Darts`, `BP_Trap_Swing`, `BP_FallVolume`
- `Content/Hazards/Test/`: `L_HZ_Test`, `BP_HZ_TestCharacter`

## Build and playtest notes

- Traps do damage only on the server, then show it everywhere. A trap that only works for the host is the most common bug in this lane.
- Test death replication, disabled interaction and team-wipe restart with two clients, plus both local split-screen players, and test traps with network emulation on, so the warnings still come first.
- Light looks different on Mac and Windows. Windows makes the final call in HC-10.
- If the editor keeps marking `L_Site01` as changed after you move geometry, never save that level; uncheck it in the save dialog.

## Verification

- HZ-0: both Macs join Playable 1.
- HZ-1: a player walks the whole blockout, from the spawn cavern to the map exit by the walkway. The daylight shaft, torches and crystals all show on a Mac and on Windows.
- HZ-2: a client who steps on the spikes hears the click before they rise. Lethal damage kills them on every screen; movement and interaction stop, and further damage does not fire `OnDied` again. They stay dead while a teammate is alive. Only a test GameMode-controlled team restart calls `ResetHealth()`.
- HZ-3: every machine shows each dart volley's warning before it fires, including under network emulation. The cave has its textures.
- HZ-4: the swinging log is in the same place on every machine at the same moment. A player carrying the key relic can cross the corridor by timing the traps.
- HZ-5: Round 3's hall reads as dark but playable with headlamps, and a fall at the ledge kills the player on every machine without an individual checkpoint teleport.
- HZ-6: Playable 3 passes, with the props lighting the way forward.
- HZ-7: Map 2's room loads with its light, and its walls and door read as Egyptian.
- HZ-8: the traps and chambers have their meshes and dressing, and every trap still lines up with its damage.
- HZ-9: every trap and the ambience play on every machine. Playable 4 passes.
- HZ-10: both Macs hold 30 fps or better, with scalability settings if needed.
- HZ-11: Demo 1 passes.

## Open questions

- How dark is too dark? Set the target at the first playtest with the light pass in, on both a Mac and Windows.
