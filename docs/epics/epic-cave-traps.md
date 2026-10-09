# Epic: Cave, traps and atmosphere (HZ)

**Machine:** Mac 2 · **Owner:** Ak47 · **Folder:** `Content/Hazards/` · **Sublevels:** `L_Site01_HZ`, and `L_Site02_HZ` from Sprint 7

## Relationship to other epics (read first)

HZ builds the places the game happens in and the traps that make them dangerous: the cave and its light, the spike, dart and swinging traps, the trap corridor for Round 2, the hall for Round 3, Map 2's antechamber, and the game's sound. `AC_Health` is HZ's contract: [HC](epic-core-rounds.md) puts it on the player character, and every source of player damage, from traps to [PG](epic-player-ghosts.md)'s ghosts, goes through it. The sprint table, checkpoints and contracts are in [docs/sprints.md](../sprints.md), room positions in [docs/map/site01-layout.md](../map/site01-layout.md), and the asset pipeline in [docs/assets.md](../assets.md).

## Context

The first sprints build a small cave the team can walk around in and keep improving: textures, props, light and traps arrive a little each sprint. Because HZ owns the layout, the other lanes build their puzzles, ghosts and zipline into HZ's rooms at the positions in the layout doc, without waiting on HZ.

## Locked decisions

- HZ owns the blockout (floors, walls, ceilings, ramps), the cave's light and atmosphere, and Map 2's room, all in HZ's sublevels. Announce layout changes at kickoff, because the other lanes build on them.
- The cave is dark. Light comes from a shaft of daylight through a crack in the spawn cavern's ceiling, from torches and from glowing crystals, with Lumen for bounce light. Players' headlamps do the rest.
- `AC_Health` covers player health, knockdown and revive only. All player damage goes through `Apply Damage`.
- Downed players can't move. A teammate revives them with a hold interaction. There's no bleed-out or death in Demo 1.
- The server decides when a trap fires, and every machine replays it from replicated state: RepNotify for state changes, server time for constant motion, and unreliable multicasts only for cosmetic effects such as dust and sound.
- Traps run all the time, not only during rounds, so the cave stays dangerous to explore. Their timing scales through `DT_HazardScaling`.

## Non-goals (for Demo 1)

- Bleed-out, death and spectating.
- Chaos Destruction and geometry collections.
- Final art. Generated assets replace the greybox where they pass review.
- Stretch goals, only if this lane is ahead: a rolling boulder, and a cave-in as the map's finale.

## Dependencies and sequencing

- HZ-0 needs HC-0's bare project.
- HZ-2's `AC_Health` is a hard gate for Playable 2. It must be merged by the end of Sprint 2 so HC-3 can wire revive; if it isn't, finish it first thing in Sprint 3.
- HZ-5's key relic nook holds HC's `BP_KeyRelic`, placed by HC in HC-6.
- HZ-6's fall volume sends fallers to HC's `BP_RespawnPoint` for the current round. Find it at runtime by its round number.
- HZ-7's Map 2 room goes into HC-7's `L_Site02`, made in the same sprint.

## Phases

### HZ-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, run `Tools/check-mac.command` until it passes.

- At about minute 15, pull the bare project and open it. The first open compiles shaders for a while.
- Meanwhile, set up MCP with [docs/mcp.md](../mcp.md) and run its smoke test once the editor is up. Tell PG about anything that behaves differently on your machine.
- Join Playable 1.

### HZ-1: The cave (Sprint 1, 45 min)

- Make `L_Site01_HZ` the current level. Have your agent block out the cave from the layout table with the template's level prototyping meshes: the spawn cavern, the passages, chambers 1 to 3, the trap corridor and key relic nook, the exit ledge, and the walkway down to the map exit.
- First light shading. Delete the Basic level's floor once the blockout's floors are in, and turn the sky light down to near black. Let the sun in only through a crack in the spawn cavern's ceiling, with volumetric fog so the shaft shows. Add a few warm torch lights, and cold glowing crystals made from emissive greybox shapes.
- Stub `AC_Health` with its variables, dispatchers and empty functions.
- Create `S_HazardScaling` and `DT_HazardScaling` with rows `2`, `3` and `4`: `SpikeDelay`, `DartInterval`, `SwingSpeed` and `ReviveSeconds`.

### HZ-2: Health, spikes and textures (Sprint 2, 45 min)

- `AC_Health`, on the server: bind the owner's OnTakeAnyDamage, subtract the damage, and go down at 0. The `bDowned` RepNotify stops movement on every machine and shows a simple downed look, such as a tint.
- `Revive(Reviver)` restores half health, but only if `CanBeRevived()`. `ForceDown(bAllowRevive)` downs the player at once, and with `false` they can't be revived. `OnDowned` and `OnRevived` fire on the server.
- For testing before HC-3 wires revive: `BP_HZ_TestCharacter` (a child of `BP_CoopCharacter` with the component added), a test GameMode for `L_HZ_Test`, and `BP_HZ_TestReviveTrigger`, which revives anyone standing in it.
- `BP_Trap_Spikes`: a plate that raises spikes after `SpikeDelay` and damages any pawn on it, then resets. Put the first one in the passage from the spawn cavern, where it teaches players to watch the floor. Start with 0.6 seconds for 2 players, 0.5 for 3 and 0.4 for 4.
- Put HZ-A1's cave surfaces on the blockout.

### HZ-3: Darts and light (Sprint 3, 60 min) → Playable 2

- `BP_Trap_Darts`: a wall launcher that fires across the trap corridor every `DartInterval` seconds. The server replicates the time of each volley, and every machine plays the darts from it; the server applies the damage. Don't use a multicast for the volley itself, since a dropped message would mean damage with no warning.
- Second light pass with HZ-A2's props: real torches and crystals, stalagmites and rubble. Make each chamber's way forward the brightest thing in view.
- Join Playable 2.

### HZ-4: Swing and dressing (Sprint 4, 45 min)

- `BP_Trap_Swing`: a swinging log whose angle comes from server time, so every machine computes it with no replication. The server damages whatever it hits. `SwingSpeed` scales it.
- Dress chambers 1 to 3 with HZ-A4's pieces, without moving any of the positions in the layout doc.

### HZ-5: Round 2's corridor (Sprint 5, 45 min)

- Arrange the trap corridor for Round 2: darts, the swinging log and spikes, timed so a player carrying the key relic at half speed can get through by watching the rhythm.
- The key relic nook, a short side passage with spikes guarding it. Leave the key relic's spot clear for HC.

### HZ-6: Round 3's hall and atmosphere (Sprint 6, 60 min) → Playable 3

- Round 3's hall: dark apart from a few crystals, with two swinging logs, spikes and darts set between PG's gate and exit lever.
- `BP_FallVolume` under the chasm at the exit ledge: a player who falls goes back to the current round's respawn point with 50 damage.
- Atmosphere across the cave: height fog, drifting dust and dripping water.
- Join Playable 3.

### HZ-7: Map 2 (Sprint 7, 45 min)

- `/Game/Hazards/L_Site02_HZ`, Map 2's antechamber: a 20 m square room in sandstone, two braziers for light, hieroglyphs on the walls, and a sealed door that says the way on opens later. Use HZ-A5's kit.

### HZ-8: Sound and tuning (Sprint 8, 60 min) → Playable 4

- Sound pass with HZ-A6: cave ambience and drips, torch crackle, and a sound for every trap, played as 3D sound.
- Tune `DT_HazardScaling` from the 2-player and 4-player runs.
- Join Playable 4.

### HZ-9: Demo (Sprint 9, 60 min) → Demo 1

- Effects: dust when the spikes fire, splinters when a log hits, embers from the torches.
- Mac performance check. If a Mac drops below 30 fps, lower its scalability settings rather than cutting content.
- Fix what Playable 4 found.

## Asset generation

Follow [docs/assets.md](../assets.md) for specs, imports and reviews. Raw output goes in `SourceArt/HZ/`, imported assets in `Content/Hazards/Art/`.

| Task | Sprint | Assets | Specs | Used in |
| --- | --- | --- | --- | --- |
| HZ-A1: Cave surfaces | 1 | Tileable materials for rock walls, the cave floor (damp rock and grit) and the ceiling, plus a kit of 4–6 rock pieces for building walls and boulders. | 2K tileable textures, full PBR. Rock pieces with Nanite on and simple collision. | HZ-2 |
| HZ-A2: Props and light sources | 2 | Stalagmites and stalactites (3 each), crystal clusters in two colors that glow, a wall torch with a flame, rubble. | Props up to 20k triangles with Nanite on. The crystal material's glow must be adjustable. | HZ-3 |
| HZ-A3: Trap meshes | 3 | A spike plate with spikes, a dart launcher carved into a wall, and darts. | Plates 2 m square. Simple collision; the damage volumes stay in the Blueprints. | HZ-3, HZ-5 |
| HZ-A4: Swing and dressing | 4 | A swinging log, or a blade, with its chain or rope; carved pillars, bones and old rope for dressing. | The log pivots at its top. | HZ-4 to HZ-6 |
| HZ-A5: Map 2 kit | 6 | Sandstone wall and floor materials, an Egyptian pillar, hieroglyph decals, a brazier. | 2K textures. Decals as material instances. | HZ-7 |
| HZ-A6: Cave and trap sounds | 7 | Cave ambience, drips, torch crackle, and sounds for the spikes, darts and swinging log. | Mono WAV, 48 kHz, except stereo ambience. Ambience loops cleanly. | HZ-8 |

## Critical assets

- `Content/Hazards/`: `AC_Health`, `S_HazardScaling`, `DT_HazardScaling`, `L_Site01_HZ`, `L_Site02_HZ`, `Art/`
- `Content/Hazards/Traps/`: `BP_Trap_Spikes`, `BP_Trap_Darts`, `BP_Trap_Swing`, `BP_FallVolume`
- `Content/Hazards/Test/`: `L_HZ_Test`, `BP_HZ_TestCharacter`, `BP_HZ_TestReviveTrigger`

## Build and playtest notes

- Fire traps only on the server, then show them everywhere. A trap that only works for the host is the most common bug in this lane.
- Test downed and revive with two clients, not with the host and one client.
- Light looks different on Mac and Windows. Windows makes the final call in HC-9.
- If the editor keeps marking `L_Site01` as changed after you move geometry, never save that level; uncheck it in the save dialog.

## Verification

- HZ-0: both Macs join Playable 1.
- HZ-1: a player walks the whole blockout, from the spawn cavern to the map exit by the walkway. The daylight shaft, torches and crystals all show on a Mac and on Windows.
- HZ-2: a client who steps on the spikes goes down on every screen, and the test trigger revives them. `ForceDown(false)` leaves a player who can't be revived. The cave has its textures.
- HZ-3: a client is hit by darts only when every machine shows a volley. The props light the way forward.
- HZ-4: the swinging log hits the same way on every machine.
- HZ-5: a player carrying the key relic can cross the corridor by timing the traps.
- HZ-6: Round 3's hall reads as dark but playable with headlamps, and a fall at the ledge returns the player to the round's start.
- HZ-7: Map 2's room loads with its light, and its walls and door read as Egyptian.
- HZ-8: every trap and the ambience play on every machine. Playable 4 passes.
- HZ-9: Demo 1 passes.

## Open questions

- How dark is too dark? Set the target at the first playtest with the light pass in, on both a Mac and Windows.
