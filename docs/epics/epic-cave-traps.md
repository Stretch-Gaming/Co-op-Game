# Epic: Cave, traps and atmosphere (HZ)

**Machine:** Mac 2 · **Owner:** Ak47 · **Folder:** `Content/Hazards/` · **Sublevels:** `L_Site01_HZ`, and `L_Site02_HZ` from Sprint 7

## Relationship to other epics (read first)

HZ builds the places the game happens in and the traps that make them dangerous: the cave and its light, the maze and its two sets of paths, the spike, dart and swinging traps, the maze's collapsing bridges, boulder and falling rocks, the relic chamber's room, the way home, Map 2's antechamber, and the game's sound. `AC_Health` is HZ's contract: [HC](epic-core-rounds.md) puts it on the player character, and every source of player damage, from traps to [PG](epic-player-ghosts.md)'s ghosts, goes through it. The sprint table, checkpoints and contracts are in [docs/sprints.md](../sprints.md), room positions and the climbing and jumping measurements in [docs/map/site01-layout.md](../map/site01-layout.md), the asset pipeline in [docs/assets.md](../assets.md), and the design direction in [docs/design/direction-2026-10-10.md](../design/direction-2026-10-10.md).

## Context

The first sprints build a small cave the team can walk around in and keep improving: geometry and the light it needs first, then textures, traps, props and atmosphere, a little each sprint. Because HZ owns the layout, the other lanes build their puzzles, ghosts and zipline into HZ's rooms at the positions in the layout doc, without waiting on HZ.

The maze comes from the CoopCave prototype in `Prototypes/CoopCave/`: its fork, four paths, sunken hall and relic chamber. Stretch's integration in [#93](https://github.com/StretchGaming/Co-op-Game/issues/93) bakes it into the main game. HZ then reshapes it for the maze run.

## Locked decisions

- HZ owns the blockout (floors, walls, ceilings, ramps), the cave's light and atmosphere, the maze, and Map 2's room, all in HZ's sublevels. Announce layout changes at kickoff, because the other lanes build on them.
- The cave is dark. Light comes from a shaft of daylight through a crack in the spawn cavern's ceiling, from torches and from glowing crystals, with Lumen for bounce light. Players' headlamps do the rest.
- `AC_Health` covers player health and death only, with Component Replicates on. All player damage goes through `Apply Damage`.
- Lethal damage kills players immediately. There is no downed state, bleed-out or teammate revive. Dead players cannot move or interact, drop carried items and release held mechanisms. They stay dead until the round clears or HC's GameMode restarts it; a team wipe restarts everyone at the latest checkpoint.
- The server decides when a trap does damage, and every machine knows in advance when that will be. Traps replicate a schedule (a start time in server time plus an interval or speed) or the moment they were triggered, and every machine shows the warning from it. Unreliable multicasts are only for cosmetic effects, such as dust and sound. The collapsing bridge, the boulder, falling rocks and the rockfall at the fork follow the same rules.
- Traps run all the time, not only during rounds, so the cave stays dangerous to explore. Their timing scales through `DT_HazardScaling`, using `RoundState.ScalingRow`.
- **The maze's paths are solo.** Each player has their own; paths never join, and where they cross, it's over a rock bridge. Four are built for each split, whatever the player count.
- **Every obstacle fits a category** in the layout doc's climbing and jumping table, so it's clearly possible or clearly impossible. Climbing walls, ropes and vines carry a volume with the actor tag `Climbable`.
- **Missed jumps cost time, not a life.** A gap drops you into a pit with a climb back out. Only chasms that look deadly have a fall volume.
- **The way home has no ledges, gaps or climbing walls**, because the relic's carrier can't sprint or climb. It's at least 4 m wide, so the team can walk around the carrier.

## Non-goals (for Demo 1)

- Downed state, bleed-out and revives.
- Chaos Destruction and geometry collections. The collapsing bridge drops its planks as animated pieces.
- Final art. Generated assets replace the greybox where they pass review.
- Stretch goals, only if this lane is ahead: a cave-in behind the team as the escape starts.

## Dependencies and sequencing

- HZ-0 needs HC-0's bare project.
- HZ-2's `AC_Health` is a hard gate for Playable 2. It must be merged by the end of Sprint 2 so HC-3 can wire death handling and checkpoint restarts; if it isn't, finish it first thing in Sprint 3.
- HZ-5's fall volume kills players through `Apply Damage` and `AC_Health`. HC handles the restart when the whole team is dead.
- HZ-6 starts from the maze bake in #93. If it isn't in by Sprint 6, bake the maze the same way as the first cave room, with `Tools/unreal/bake_cave_environment.py`, and tell Stretch.
- HZ-6 marks where HC's plates, locks, doors and relic go and where PG's taking, levers and ghosts go, and fills in the layout doc's table. PG-6 calls HZ-6's `BP_MouthSeal`.
- HZ-7 builds to the layout doc's measurements, which PG-7 tunes in the same sprint.
- HZ-9's escape route is where PG-10's chase runs and PG-7's zipline lands.
- HZ-11's Map 2 room goes into `L_Site02`, which HC-7 brings in as a sublevel.

## Phases

### HZ-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, run `Tools/check-mac.command` until it passes.

- At about minute 15, pull the bare project and open it. The first open compiles shaders for a while.
- Meanwhile, set up MCP with [docs/mcp.md](../mcp.md) and run its smoke test once the editor is up. Tell PG about anything that behaves differently on your machine.
- Join Playable 1.

### HZ-1: The cave (Sprint 1, 45 min)

- Make `L_Site01_HZ` the current level. Have your agent block out the cave from the layout table with the template's level prototyping meshes: the first room (the spawn cavern), the passage, the plate hall, the trap corridor, the altar cavern, the haunted hall and the exit ledge. Geometry you can walk through matters more than detail; dressing comes later. The maze comes in HZ-6.
- Only the light the cave needs to be playable: delete the Basic level's floor once the blockout's floors are in, turn the sky light down to near black, let the sun in only through a crack in the spawn cavern's ceiling, with volumetric fog so the shaft shows, and add a few warm torch lights and cold crystal lights on greybox shapes.
- Stub `AC_Health` with Component Replicates on, and its variables, dispatchers and empty functions.
- Create `S_HazardScaling` and `DT_HazardScaling` with rows `2`, `3` and `4`: `SpikeDelay`, `DartInterval` and `SwingSpeed`. There is no revive-duration field.

### HZ-2: Health and spikes (Sprint 2, 45 min)

- `AC_Health`, on the server: bind the owner's OnTakeAnyDamage, ignore damage if already dead, subtract damage and clamp health to 0. At 0, set `bDead` and fire `OnDied` once. The `bDead` RepNotify applies death on every machine: disable movement and interaction and show a simple death look, such as a tint. Dead players no longer hold pressure plates or levers and are ignored by ghosts.
- `IsDead()` exposes the authoritative death state. Server-only `ResetHealth()` restores full health and clears `bDead` only during a GameMode-controlled restart or regroup; the RepNotify restores movement and interaction. There is no revive function or teammate reset path.
- For testing before HC-3 wires death handling: `BP_HZ_TestCharacter` (a child of `BP_CoopCharacter` with the component added) and a test GameMode for `L_HZ_Test`. The test GameMode resets health only when restarting the test after a team wipe; walking into a trigger cannot restore a dead player.
- `BP_Trap_Spikes`: stepping on the plate replicates the server time it was triggered; every machine plays a click and a rumble from that, and the server raises the spikes and does damage after `SpikeDelay`. Put the first one in the passage from the spawn cavern, where it teaches players to watch the floor. Start with 0.6 seconds for 2 players, 0.5 for 3 and 0.4 for 4.

### HZ-3: Darts and the first textures (Sprint 3, 60 min) → Playable 2

- `BP_Trap_Darts`: a wall launcher that fires across the trap corridor on a schedule. It replicates a start time and `DartInterval`, so every machine knows when each volley comes and shows a warning half a second before it; the server does the damage at the same moments.
- Put HZ-A1's cave surfaces on the blockout.
- Once HC-3 has `AC_Health` on the real character, remove it from `BP_HZ_TestCharacter`, so there's only one.
- Join Playable 2.

### HZ-4: Swing and the trap corridor (Sprint 4, 45 min)

- `BP_Trap_Swing`: a swinging log whose angle comes from server time, its replicated start time and `SwingSpeed`, so every machine computes the same swing. The server damages whatever it hits.
- The trap corridor, on the way home: darts, the swinging log and spikes, timed so the relic's carrier, at half speed, can get through by watching the rhythm. The team crosses it from east to west.
- Close off the old key relic nook. The relic now waits at the end of the maze.

### HZ-5: The haunted hall and the fall volume (Sprint 5, 45 min)

- The haunted hall, the old Round 3 hall, now on the way home: dark apart from a few crystals, with two swinging logs, spikes and darts at the positions in the layout doc. Nothing to climb or jump, because the carrier crosses it.
- `BP_FallVolume` under the chasm at the exit ledge: on the server, apply lethal damage through `Apply Damage` so a fall kills the player. It does not teleport or reset them individually; HC's GameMode handles the restart. The maze's deadly chasms reuse it.

### HZ-6: The maze route (Sprint 6, 60 min) → Playable 3

- Bring the prototype maze into `L_Site01_HZ` north of the first room, from the bake in #93, and reshape it for the maze run:
  - The maze mouth: a dark 3 m passage from the maze door at (0, 15) north to the fork, about 30 m long, where the taking happens.
  - Four first paths from the fork to the meeting hall, the prototype's sunken hall.
  - Four second paths from the meeting hall's four doors to the relic chamber, high above the exit ledge.
  - The escape tunnel from the relic chamber out to a ledge, where the zipline starts, and the walkway down to the exit ledge at (180, 0).
- Make the paths solo: remove anywhere two paths meet or let you switch, apart from the meeting hall and the relic chamber. Keep the rock bridges where one path crosses another. Take the prototype's brace-and-boost co-op moments off the paths.
- `BP_MouthSeal` at the fork, in `Content/Hazards/Maze/`: server-only `SealAllBut(PathIndex)` drops a rockfall over every path mouth but one, on a replicated schedule like a trap, with a rumble and dust first. It implements `BPI_RoundReset`.
- Mark where the other lanes' pieces go, and fill in the layout doc's table in the same commit: the drop-off altar, the four path starts for each split, the meeting hall's lock perches and doors, the relic chamber's pedestal and lever spots, and ghost spawn points.
- Greybox is fine: each path just has to be walkable from end to end.
- Join Playable 3.

### HZ-7: The first paths (Sprint 7, 45 min)

- On each of the four first paths: spikes, darts and swinging logs, ledges to climb, rubble to climb over and gaps to jump, each built to a category in the layout doc's table. Each path takes 2 to 3 minutes, and the four take about the same time, so players reach the meeting hall close together.
- Under each gap, a pit with a climb back out. A fall volume only under chasms that look deadly.
- Climbing walls, ropes and vines with `Climbable` volumes, marked so they read at half-screen size. Use HZ-A7's climbing kit as it arrives.
- Places where paths glimpse each other: bridges overhead and below, and grates or cracks in shared walls.

### HZ-8: The second paths (Sprint 8, 45 min)

- On each of the four second paths, harder than the first: traps set closer together, more climbing and jumping, and stretches you have to sprint through. Each path takes 3 to 4 minutes.
- `BP_CollapsingBridge`: stepping on it starts a replicated schedule, and its planks fall one after another behind you, so you have to sprint across. A missed run drops you into a pit with a climb out.
- `BP_Boulder`: a trigger releases a boulder that rolls along a spline from a replicated start time, so every machine sees it in the same place. Outrun it to a side nook. It kills on contact.
- `BP_FallingRocks`: dust and a rumble warn first, then rocks fall and do damage, on the same rules as the spikes.
- Scares that don't hurt: `BP_BatBurst` sends a swarm of bats and a screech out of a crack as a player passes. PG places the occasional ghost that drifts through a wall.

### HZ-9: The relic chamber and the way home (Sprint 9, 60 min) → Playable 4

- The relic chamber: the pedestal's spot in the middle, room for PG's levers around it, the escape tunnel out to the zipline's ledge, and the walkway down to the exit ledge for when the zipline isn't in.
- The way home from the exit ledge to the first room: the haunted hall, the altar cavern, the trap corridor, the plate hall and the passage. Check it against the carrier's rules: no ledges, gaps or climbing walls, steps up to 45 cm, and at least 4 m wide.
- Chase spawn points along the way home for PG, and enough light to see the ghosts coming.
- Join Playable 4.

### HZ-10: Light, props and dressing (Sprint 10, 45 min)

- Second light pass with HZ-A2's props across the cave and the maze: real torches and crystals, and stalagmites. Make the way forward on every path the brightest thing in view.
- Atmosphere everywhere: height fog, drifting dust and dripping water.
- Swap HZ-A3's trap meshes in for the greybox traps, and dress the cave and the maze with HZ-A4's and HZ-A7's pieces, without moving any of the positions in the layout doc.

### HZ-11: Map 2 (Sprint 11, 45 min)

- `/Game/Hazards/L_Site02_HZ`, Map 2's antechamber: a 20 m square room in sandstone, two braziers for light, hieroglyphs on the walls, and a sealed door that says the way on opens later. The results show here after the mission. Use HZ-A5's kit.

### HZ-12: Sound and tuning (Sprint 12, 60 min) → Playable 5

- Sound pass with HZ-A6: cave ambience and drips, torch crackle, and a sound for every trap and maze hazard, played as 3D sound. Trap sounds play from the same schedules as their warnings.
- Tune `DT_HazardScaling` and the paths' timing from the 2-player and 4-player runs.
- Join Playable 5.

### HZ-13: Effects and Mac performance (Sprint 13, 45 min)

- Effects: dust when the spikes fire, splinters when a log hits, embers from the torches, dust when the bridge's planks fall and when the rockfall seals the fork.
- Mac performance check, in the maze as well as the cave. If a Mac drops below 30 fps, lower its scalability settings rather than cutting content.

### HZ-14: Demo (Sprint 14, 60 min) → Demo 1

- Final fixes.

## Asset generation

Follow [docs/assets.md](../assets.md) for specs, licensing, imports and reviews. Raw output goes in `SourceArt/HZ/`, imported assets in `Content/Hazards/Art/`. Early deliveries are deliberately small: one material family or a few props.

| Task | Sprint | Assets | Specs | Used in |
| --- | --- | --- | --- | --- |
| HZ-A1: Cave surfaces | 2 | One material family: tileable rock walls and the cave floor (damp rock and grit). The ceiling reuses the wall material. Also the atmosphere preset: a post-process volume with a color grading LUT, and fog in the shadow color from [art/style.md](../art/style.md#palette). In place by Sprint 3. | 2K tileable textures with a painted look, used through world-aligned instances of `M_Stylized`. | HZ-3 |
| HZ-A2: Props and light sources | 4 | A wall torch with a flame, a crystal cluster that glows, and one or two stalagmites. Library props from Fab are fine. In place by Sprint 6. | Props up to 20k triangles with Nanite on for opaque ones. If the crystal material is translucent, turn Nanite off for it. The crystal glow must be adjustable. | HZ-10 |
| HZ-A3: Trap meshes | 5 | A spike plate with spikes, a dart launcher carved into a wall, and darts. In place by Sprint 10. | Plates 2 m square. Simple collision; the damage volumes stay in the Blueprints. | HZ-10 |
| HZ-A4: Dressing | 6 | A swinging log or blade with its chain, carved pillars, bones and old rope. In place by Sprint 10. | The log pivots at its top. | HZ-10 |
| HZ-A5: Map 2 kit | 6 | Sandstone wall and floor materials, an Egyptian pillar, hieroglyph decals, a brazier. In place by Sprint 11. | 2K textures. Decals as material instances. | HZ-11 |
| HZ-A6: Cave and trap sounds | 8 | Cave ambience, drips, torch crackle, and sounds for the spikes, darts, swinging log, collapsing planks, rolling boulder, falling rocks and the rockfall. In place by Sprint 12. | Mono WAV, 48 kHz, except stereo ambience. Ambience loops cleanly. | HZ-12 |
| HZ-A7: Maze climbing kit | 6 | Climbing-wall handholds, a hanging rope and vines, ledge lips, a plank bridge in loose pieces, a boulder about 3 m across, a rockfall pile and falling rock chunks. In place by Sprint 8. | Handholds and rope wraps in torch amber, so climbables read at half-screen size. Simple collision. The bridge's planks are separate meshes that pivot where they hang. | HZ-7, HZ-8 |

## Critical assets

- `Content/Hazards/`: `AC_Health`, `S_HazardScaling`, `DT_HazardScaling`, `L_Site01_HZ`, `L_Site02_HZ`, `Art/`
- `Content/Hazards/Traps/`: `BP_Trap_Spikes`, `BP_Trap_Darts`, `BP_Trap_Swing`, `BP_FallVolume`, `BP_CollapsingBridge`, `BP_Boulder`, `BP_FallingRocks`
- `Content/Hazards/Maze/`: `BP_MouthSeal`, `BP_BatBurst`
- `Content/Hazards/Test/`: `L_HZ_Test`, `BP_HZ_TestCharacter`

## Build and playtest notes

- Traps do damage only on the server, then show it everywhere. A trap that only works for the host is the most common bug in this lane.
- Test death replication, disabled interaction and team-wipe restart with two clients, plus both local split-screen players, and test traps with network emulation on, so the warnings still come first.
- Walk every path yourself as a client, with a stopwatch. A path that takes much longer than the others leaves three players waiting.
- Light looks different on Mac and Windows. Windows makes the final call in HC-13.
- If the editor keeps marking `L_Site01` as changed after you move geometry, never save that level; uncheck it in the save dialog.

## Verification

- HZ-0: both Macs join Playable 1.
- HZ-1: a player walks the cave's blockout from the first room to the exit ledge. The daylight shaft, torches and crystals all show on a Mac and on Windows.
- HZ-2: a client who steps on the spikes hears the click before they rise. Lethal damage kills them on every screen; movement and interaction stop, and further damage does not fire `OnDied` again. They stay dead while a teammate is alive. Only a test GameMode-controlled team restart calls `ResetHealth()`.
- HZ-3: every machine shows each dart volley's warning before it fires, including under network emulation. The cave has its textures.
- HZ-4: the swinging log is in the same place on every machine at the same moment. A player carrying the relic can cross the corridor from east to west by timing the traps.
- HZ-5: the haunted hall reads as dark but playable with headlamps, and a fall at the ledge kills the player on every machine without an individual checkpoint teleport.
- HZ-6: a player walks from the maze door through the mouth to the fork, along each first path to the meeting hall, through each door along each second path to the relic chamber, and out to the exit ledge by the walkway. `SealAllBut` leaves one path open on every screen. The layout doc's table has every position.
- HZ-7: a client can finish each first path in 2 to 3 minutes using only the moves in the layout doc's table, and every trap warns first on every screen.
- HZ-8: the collapsing bridge, the boulder and the falling rocks are in the same place on every machine at the same moment, and a sprinting client gets past each one.
- HZ-9: a client carrying the relic walks from the relic chamber's ledge down the walkway and all the way home without needing to climb or jump. Playable 4 passes.
- HZ-10: the cave and the maze have their light, props, dressing and trap meshes, every trap still lines up with its damage, and every path's way forward stands out.
- HZ-11: Map 2's room loads with its light, and its walls and door read as Egyptian.
- HZ-12: every trap, maze hazard and the ambience play on every machine. Playable 5 passes.
- HZ-13: both Macs hold 30 fps or better in the cave and the maze, with scalability settings if needed.
- HZ-14: Demo 1 passes.

## Open questions

- How dark is too dark? Set the target at the first playtest with the light pass in, on both a Mac and Windows.
- How many glimpses between paths keep players from feeling lost without letting them meet up? Start with one bridge and one grate per path.
