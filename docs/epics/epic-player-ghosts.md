# Epic: Player view and ghosts (PG)

**Machine:** Mac 1 · **Owner:** PK · **Folder:** `Content/Player/` · **Sublevel:** `L_Site01_PG`

## Relationship to other epics (read first)

PG builds how players see and move through the game, the tools they carry, and what haunts them: first person with a switch to third person, the headlamp and flares, sprinting and climbing, player colors, split-screen on the host, the dead view, the ghosts and cave beings, the taking, the relic chamber's levers and cage, the chase home and the zipline. It also sets up the team's asset generation pipeline and the UI kit. It builds on [HC](epic-core-rounds.md)'s character, input contexts, interaction modes, round state, round reset and carrying. [HZ](epic-cave-traps.md) builds the maze, its paths and traps, the relic chamber's room and the escape route. The sprint table, checkpoints and contracts are in [docs/sprints.md](../sprints.md), room positions in [docs/map/site01-layout.md](../map/site01-layout.md), the asset pipeline in [docs/assets.md](../assets.md), and the design direction in [docs/design/direction-2026-10-10.md](../design/direction-2026-10-10.md).

## Context

The Macs are always clients in playtests, so this lane sees the views, the taking and the ghosts exactly as joining players will. Split-screen is tested on the Windows host, where it runs in Demo 1.

## Locked decisions

- **First person by default.** `AC_PlayerView` drives the template character's own spring arm and camera:
  - First person: the camera at eye height with no arm, a 90° field of view, the character turning with the camera (Use Controller Rotation Yaw on, Orient Rotation to Movement off).
  - Third person: the camera over the shoulder, a 75° field of view, the character turning toward its movement (the reverse settings).
  - A switch glides between them in about 0.3 seconds, on the owning player's camera only.
- **The view is applied from scratch.** `ApplyViewState()` sets everything for the current mode, and runs at BeginPlay, whenever the pawn is possessed, and in the RepNotify. A RepNotify alone isn't enough, because it doesn't fire for an unchanged default.
- In first person your body is hidden from your own view (Owner No See), and still casts its shadow (Cast Hidden Shadow on). Everyone else, in every split view, sees your full body.
- **The headlamp is a spotlight on the head**, not on the camera, aimed each frame with Get Base Aim Rotation. That gives the same origin and aim on every machine, in both views. `bHeadlampOn` replicates. The server uses the same origin and aim for ghosts and for lighting locks.
- Split-screen runs only on the host machine in Demo 1, in the `Lobby` and `Cleared` phases, with up to 2 local players and 4 in total. The host plays on keyboard and mouse, and the first gamepad becomes player 2.
- **Ghosts and cave beings are replicated pawns that the server moves directly** through walls, every tick. They don't use the nav mesh or a movement component. They chase and they back off from light; nothing more.
- **The taking is scheduled like a trap.** The server picks each victim and replicates who, how and a start time in server time; every machine plays the same scare from that. The server moves a victim only once the scare covers their screen.
- **Every player carries the same tools:** the headlamp and flares. Light is the one defense: a headlamp holds off one ghost, and a flare keeps every ghost out of its glow.
- **Movement and tools are components** with Component Replicates on (`AC_PlayerView`, `AC_Traversal`, `AC_Tools`), so PG's work doesn't touch `BP_CoopCharacter`. HC adds each component and forwards its keys.
- The relic chamber's levers, cage and ghosts are PG's. HZ builds the room, and HC owns the relic.

## Non-goals (for Demo 1)

- Split-screen on joining machines.
- First-person arms or held items, and animation beyond the template's. Climbing and throwing use the template's poses.
- Ghosts with pathfinding or more than two behaviors.
- Tool slots, roles and the Scout's rope and grappling hook.
- Camels in Egypt. They come with Map 2's content after the demo.

## Dependencies and sequencing

- PG-0 needs HC-0's bare project. PG-1 needs HC-0's `BP_CoopCharacter`.
- PG-1 tests on `BP_PG_TestCharacter`, a child of `BP_CoopCharacter` with the component added, in `L_PG_Test`. When HC-2 puts the component on the real character, remove it from the test character so there's only one. The same goes for `AC_Traversal` in HC-7 and `AC_Tools` in HC-8.
- PG-1 publishes `BPFL_SplitScreen`'s stub, so HC-2 can wire F5 and F6 while PG-2 builds it.
- PG-4 spawns ghosts when a round starts. `StartRound` works from HC-1, so F1 and F2 start and clear rounds until HC-5's round actors are in.
- PG-5's dead view needs HC-3's death handling and `AC_Health.bDead`.
- PG-6's taking needs HC-6's Round 2 start and checkpoint, and HZ-6's maze mouth and its `BP_MouthSeal`.
- PG-7 tunes the moves to the measurements in the layout doc, which HZ-7 builds to in the same sprint.
- PG-8 publishes `BPI_Lightable` and the flares, which HC-9's locks use.
- PG-9's cage needs HC-4's relic and HZ-9's relic chamber. PG-10's chase needs HZ-9's escape route and HC-10's relic.

## Phases

### PG-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, run `Tools/check-mac.command` until it passes. It checks for Unreal 5.8.3, Xcode 26.0–26.3 with the Metal toolchain, and enough disk space.

- At about minute 15, pull the bare project and open it. The first open compiles shaders for a while.
- Meanwhile, set up MCP with [docs/mcp.md](../mcp.md) and run its smoke test once the editor is up. PG owns that doc, so record what the tools can do there and push it.
- Join Playable 1.

### PG-1: First and third person (Sprint 1, 45 min)

- `AC_PlayerView` in `Content/Player/`, with Component Replicates on. On BeginPlay it finds the owner's spring arm, camera and body mesh, then calls `ApplyViewState()`.
- `ToggleView()` sends a Run on Server event from the component, which the owning player can call because their character owns it. The server sets the replicated `ViewMode`, and its RepNotify calls `ApplyViewState()` on every machine.
- `S_GhostScaling` and `DT_GhostScaling` with rows `2`, `3` and `4`: `GhostCount`, `GhostSpeed`, `GhostDamage` and `LeverCount`. PG-8 and PG-10 add `FlaresPerPlayer`, `FlareSeconds`, `ChaseWaveSize` and `ChaseWaveSeconds`.
- Publish `BPFL_SplitScreen` with `AddLocalPlayer()` and `RemoveLocalPlayer()` as empty functions, for HC-2.
- Test on `BP_PG_TestCharacter` in `L_PG_Test` as a client. Switch views while moving, and check the other client sees you face the right way.

### PG-2: Split-screen and the headlamp (Sprint 2, 45 min)

- `BPFL_SplitScreen`: `AddLocalPlayer()` calls Create Local Player for the next free gamepad, and `RemoveLocalPlayer()` removes the last one added. Both only work on the host, only in the `Lobby` and `Cleared` phases, and stop at 2 local players or 4 in total.
- Check that the second player gets their own view, their own headlamp, and their own prompt and HUD widgets on their half of the screen.
- `ToggleHeadlamp()`: a spotlight on the character's head, aimed each frame with Get Base Aim Rotation on every machine. `bHeadlampOn` replicates the same way as `ViewMode`.
- Once HC-2 has the component on the real character, remove it from `BP_PG_TestCharacter`.
- With the host, a split-screen player and two Mac clients, play for a few minutes and note the frame rate on Windows.

### PG-3: First ghost (Sprint 3, 60 min) → Playable 2

- `BP_Ghost`: a Pawn with Replicates and Replicate Movement on. Its collision overlaps everything, so it passes through walls.
- On the server, about 5 times a second, it picks the nearest player within 20 m who is alive (`AC_Health.IsDead()` is false). Every tick it moves its root toward them by `GhostSpeed` times the frame time, slower than a walking player. Touching a player calls `Apply Damage` with `GhostDamage`, then the ghost backs off for 3 seconds.
- A gentle bob and a glow run on the visual mesh only, locally on every machine.
- Place one ghost in the spawn cavern's north passage. Also spawn one from a debug key in `L_PG_Test`, to check spawned ghosts behave like placed ones. Use a translucent greybox sphere until PG-A2's ghost arrives.
- Join Playable 2.

### PG-4: Ghosts each round, and player colors (Sprint 4, 45 min)

- `BP_GhostSpawner`, on the server only: when its round starts, spawn `GhostCount` ghosts at its spawn points. Start with 1 ghost for 2 players, 1 for 3 and 2 for 4. They leave when the phase stops being `Playing`, and the spawner implements `BPI_RoundReset`, so a restart brings a fresh set. Spawners go in the first room, the meeting hall and the relic chamber. A spawner on a second path can instead send one ghost through the wall past a player, once, as a scare.
- Remove the ghost placed in PG-3, so spawners are the only source. Its passage is now the maze mouth.
- `ApplyColorSlot()`: apply PG-A1's color variant for the player's `ColorSlot` on every machine, when the slot replicates, on possession and after travel.

### PG-5: Ghosts back off from light, and the dead view (Sprint 5, 45 min)

- On the server, each lit headlamp picks at most one ghost: the one nearest the center of its cone, within 12 m and not behind a wall (a line trace). It keeps that ghost for at least half a second before switching, so the choice doesn't flicker.
- A picked ghost backs away and dims; every other ghost carries on. So one headlamp holds off one ghost, never two.
- The dead view: while its owner is dead, `AC_PlayerView` on the owning client sets the view target to a living teammate, with a short blend, and Interact switches to the next one. When the owner comes back, `ApplyViewState()` returns them to their own camera. Each split-screen player has their own dead view. If nobody is alive, the view stays on your own body until the restart.

### PG-6: The taking (Sprint 6, 60 min) → Playable 3

- `BP_TakingDirector` in `Content/Player/Taking/`, placed in the maze mouth in `L_Site01_PG`. When Round 2 starts, on the server, it picks one living player at random to stay, then takes the others one at a time, 2 to 5 seconds apart.
- Each taking replicates its victim, the way they're taken and a start time in server time. Every machine plays the same scare from that, so everyone still standing sees the victim vanish. Build at least three ways, used in a different order each run:
  - A hand drags them into the wall.
  - The floor gives way and swallows them, then closes.
  - The lights cut out, and when they come back the victim is gone, their headlamp left rolling on the floor.
- On the victim's own screen, the scare plays in first person, then cuts to black, and they come to alone at their spot on Round 2's checkpoint: the start of their own path. Once the scare covers their screen, about half a second in, the server moves them there. Players can't be damaged or interact while they're being taken.
- When the last taking ends, call `SealAllBut(PathIndex)` on HZ's `BP_MouthSeal` with the remaining player's path, so a rockfall leaves them one way on.
- The director implements `BPI_RoundReset`. Round 2's restart doesn't replay the taking.
- Greybox the taker until PG-A7 arrives: a dark shape and a long arm are enough to test the timing.
- Test in `L_PG_Test` with 2, 3 and 4 players, including a split-screen pair and under network emulation, then place it in the maze mouth.
- Join Playable 3.

### PG-7: Climb, jump and sprint, and the zipline (Sprint 7, 45 min)

- `AC_Traversal` in `Content/Player/`, with Component Replicates on. Test it on `BP_PG_TestCharacter` until HC-7 adds it to the real character.
  - Sprint: while `IA_Sprint` is held and the player is moving, their walk speed goes up to about 1.6 times. A Run on Server event sets a replicated value whose RepNotify applies the speed on the server and the owning client, like the heavy carry.
  - Ledge climbing: jumping at a ledge between 1 and 2 m high pulls the player up onto it. The owning client asks the server, and the server checks the ledge with its own traces and moves the character up over about half a second.
  - Climbing walls, ropes and vines: inside a volume with the actor tag `Climbable`, holding forward climbs instead of walking. Jump lets go.
  - A heavy carry turns sprinting and climbing off.
- Measure the moves and record the values in the [layout doc's table](../map/site01-layout.md#moving-through-the-maze), and tune them until every category there holds.
- The zipline now takes the team down from the relic chamber's ledge to the exit ledge at the start of the escape. Move `BP_Zipline` to HZ-9's positions when they're in. Boarding becomes an instant interaction through `BPI_Interactable`. The relic's carrier can ride, with the relic. A round reset removes the trolley and returns the rider to the latest checkpoint.
- Keep the zipline only if a 4-player test passes. Otherwise the walkway is the way down, and the zipline moves to after Demo 1.

### PG-8: Tools: flares and the headlamp (Sprint 8, 45 min)

- `AC_Tools` in `Content/Player/Tools/`, with Component Replicates on. `FlaresLeft` replicates. `IA_ThrowFlare` sends a Run on Server event; the server spawns a replicated `BP_Flare` from the player's hand on a short arc, and counts one down. No throwing while carrying the relic or while dead.
- `BP_Flare` burns for `FlareSeconds`, starting at 20, with a warm light. It replicates its start time, so every machine fades it the same way. Ghosts and cave beings won't enter its glow, about 4 m.
- `BPI_Lightable`, with `LightBegin(Source)` and `LightEnd(Source)`. On the server, a lit headlamp traces from the head along its aim about 5 times a second, within 12 m, and calls them on whatever its beam rests on. A flare that lands in a brazier calls them on it, and `LightEnd` when it burns out.
- Server-only `RestockFlares()` tops a player up to `FlaresPerPlayer`. HC's GameMode calls it when a round clears. Starting values: 3 flares each for 2 players, 2 each for 3 and 4.
- `BP_TestLightable` in `L_PG_Test`: two clients light it with a headlamp and with a flare, and a flare holds a ghost off.

### PG-9: The relic chamber (Sprint 9, 60 min) → Playable 4

- Round 5, in the relic chamber, built in `L_Site01_PG`. Move `BP_Lever` and `BP_GauntletGate` from `Round3/` to `RelicChamber/`, and turn the gate into `BP_RelicCage`, around HC's relic on its pedestal.
- `BP_Lever` is a continuous interaction: active from `InteractBegin` to `InteractEnd`. `LeverCount` levers are needed: 1 for 2 or 3 players, 2 for 4.
- `BP_RelicCage` stays raised while every needed lever is active, and drops the moment one is released. When the relic leaves it, the cage latches open and the levers let go. `IsRaised()` replicates, and HC's relic checks it before it can be lifted.
- All of them implement `BPI_RoundReset`: a Round 5 restart releases the levers and lowers the cage, and a Round 6 restart keeps the cage latched open. The cage tells HC's GameMode it needs `LeverCount` + 1 living players.
- The round's ghosts go for the lever holders, so the free players' headlamps matter.
- Join Playable 4.

### PG-10: The chase (Sprint 10, 45 min)

- `BP_ChaseDirector` in `Content/Player/Ghosts/`: when Round 6 starts, it sends a wave of `ChaseWaveSize` ghosts and cave beings every `ChaseWaveSeconds`, from spawn points along the escape route, both ahead of and behind the team. Starting values: waves of 2, 3 and 4 for 2, 3 and 4 players, every 20 seconds.
- In the escape, ghosts go for the relic's carrier first: the carrier of the actor tagged `Relic`, within 25 m. Otherwise they take the nearest living player. Headlamps and flares hold them off as usual.
- `BP_CaveBeing`: a child of `BP_Ghost` with PG-A7's look, a little faster. It moves and backs off from light the same way.
- Everything the chase spawned leaves when the mission completes or the round restarts.
- Run the escape at 2 and 4 players: it should be hard for a team that leaves the carrier alone, and fair for a team that sticks together.

### PG-11: Split-screen and view polish (Sprint 11, 45 min)

- Both split views: the HUD in each half, the field of view in each view, the third-person camera in tight passages and while climbing, the glide's feel, and the dead view in each half.
- With HC, check that the split-screen pair survives travel to Map 2 and back.

### PG-12: Tuning (Sprint 12, 60 min) → Playable 5

- Under network emulation, from a Mac: tune ghost speed, damage and back-off, the chase's waves, flares, the headlamp's reach, sprinting and climbing, and the taking's timing.
- Join Playable 5.

### PG-13: Buffer (Sprint 13, 45 min)

- Finish whatever earlier phases left behind, then polish the taking: it's the scariest moment of the run.

### PG-14: Demo (Sprint 14, 60 min) → Demo 1

- Final fixes. Tune ghosts and the chase so 2 players aren't overwhelmed and 4 aren't bored.

## Asset generation

Follow [docs/assets.md](../assets.md) for specs, licensing, imports and reviews. Raw output goes in `SourceArt/PG/`, imported assets in `Content/Player/Art/`, and the UI kit in `Content/Shared/UI/`.

| Task | Sprint | Assets | Specs | Used in |
| --- | --- | --- | --- | --- |
| PG-A0: Pipeline | 1 | Pick the generators for meshes, textures and sound, and settle the import presets for meshes and textures on both a Mac and Windows. Take one prop all the way from a prompt to placed in a test map, and fill in the open parts of `docs/assets.md`. Build the style kit in [art/style.md](../art/style.md#the-style-kit): `M_Stylized`, `L_StyleTest`, and an example rock and gold prop. | Record each tool's cost, plan and license terms, including whether outputs on that plan can be published in a public repo. | Every lane |
| PG-A1: Player colors | 3 | Four color variants of the template character, such as a helmet, scarf or backpack tint, so players are easy to tell apart in a dark cave and in split views. In place by Sprint 4. | Material instances of `M_Stylized`; no new meshes needed. Colors stay clear of the reserved palette colors. | PG-4, the HUD's team list |
| PG-A2: Ghost | 4 | A ghost mesh and a translucent, glowing material that fades at the edges. In place by Sprint 5. | Up to 5k triangles, with **Nanite off**, since Nanite doesn't support translucent materials. The material must read in the dark from 15 m away. | PG-3 onward |
| PG-A3: Ghost and taking sounds | 6 | A whisper loop, an attack shriek, and a hiss when light drives a ghost back. For the taking, a sting and a drag for each way a player is taken. For the escape, a chase loop that builds. In place by Sprint 8. | Mono WAV, 48 kHz, played as 3D sound with attenuation. The taken player's sting and the chase loop play in 2D, on that player's screen only. | PG-5, PG-6, PG-10 |
| PG-A4: Zipline | 6 | Cable, anchors and a trolley handle. In place by Sprint 7. | Cable as a spline mesh. Handle up to 2k triangles. | PG-7 |
| PG-A5: Bats and mice | 8 | Ambient life for Site 1: bats hanging from beams and ceilings, bats circling overhead, and mice scurrying along the walls. No gameplay effect. In place by Sprint 8. | Static meshes up to 2.5k triangles, with Nanite and collision off. Colors stay clear of the reserved palette colors. The motion is cosmetic: each machine animates its own copy, with no replication. | Site 1 dressing |
| PG-A6: UI kit, type and depth | 7 | The kit every widget is built from: a display typeface and a text typeface, solid layered panels (a soft shadow, a carved frame, a recessed plate), the brushes or UI material that draw them, small icons for the headlamp, flares, and a player who's alive, dead or carrying the relic, and `WBP_UIStyleTest` showing each piece. In place by Sprint 8. | Follows [the HUD rules](../art/style.md#hud-and-ui). Fonts under the SIL Open Font License, imported as Unreal Font assets. PNG with alpha at twice their largest display size. Lock `Content/Shared/UI/` to edit it. | HC-8 |
| PG-A7: The taker | 7 | The cave being that takes players and joins the chase: a long-limbed shadow creature, plus a reaching hand for the takings. In place by Sprint 9. | Up to 15k triangles. Reads as a silhouette in the dark from 15 m. Ghost white only for its eyes. A rigid mesh with a simple lunge is enough; skeletal only if there's time. | PG-6, PG-10 |
| PG-A8: Flare | 7 | A hand flare with a burning tip, and its hiss. In place by Sprint 8. | Up to 2k triangles. The flame and its light are torch amber. | PG-8 |

## Critical assets

- `Content/Player/`: `AC_PlayerView`, `AC_Traversal`, `BPFL_SplitScreen`, `S_GhostScaling`, `DT_GhostScaling`, `L_Site01_PG`, `Art/`
- `Content/Player/Ghosts/`: `BP_Ghost`, `BP_CaveBeing`, `BP_GhostSpawner`, `BP_ChaseDirector`
- `Content/Player/Taking/`: `BP_TakingDirector`
- `Content/Player/Tools/`: `AC_Tools`, `BP_Flare`, `BPI_Lightable`
- `Content/Player/RelicChamber/`: `BP_Lever`, `BP_RelicCage`
- `Content/Player/Zipline/`: `BP_Zipline`, `BP_ZiplineTrolley`
- `Content/Player/Test/`: `L_PG_Test`, `BP_PG_TestCharacter`, `BP_TestLightable`
- `Content/Shared/UI/`: the UI kit
- `docs/mcp.md`, `docs/assets.md`

## Build and playtest notes

- You're a client in every playtest. If a view, a taking or a ghost feels wrong on your Mac, it is wrong.
- LAN latency is tiny. Before you call the views, the taking, the moves or the ghosts done, test with network emulation set to an average internet profile (Editor Preferences → Level Editor → Play → Multiplayer Options).
- Split-screen only runs on the host, so test it in Play In Editor with a second local player, then on the Windows machine at the merge. Watch the taking from both halves.

## Verification

- PG-0: the smoke test results are in `docs/mcp.md`, and both Macs join Playable 1.
- PG-1: a client starts in first person without pressing anything, switches views while moving, and the other clients see them face the right way.
- PG-2: two players play side by side on one screen, each with their own view, headlamp and HUD, while two clients play online. A headlamp points where its player looks, on every machine and in both views.
- PG-3: a placed ghost and a spawned ghost both drift through walls after the nearest living player, damage them on contact, then back off.
- PG-4: after F1, the ghost count matches the player count, and a restarted round brings a fresh set. Every player has a different color on every screen.
- PG-5: one headlamp drives back one ghost, never two, the same way on every machine. A dead client watches a living teammate, switches with Interact, and gets their own view back when they return.
- PG-6: with 2, 3 and 4 players, every player but one is taken, each in a different way, and every other screen sees each one vanish. Nobody sees a player pop away before the scare. Each taken player comes to at the start of their own path, and the last player has one way on.
- PG-7: a client sprints, climbs a 2 m ledge and a climbing wall, and jumps a long gap, without movement corrections under network emulation. The measured values are in the layout doc. Two clients ride the zipline at once and land on their feet, or the walkway is confirmed as the way down.
- PG-8: a client's flare lands, burns and fades the same way on every screen, and a ghost won't enter its glow. A headlamp and a flare each light the test lightable, as seen from every machine.
- PG-9: Round 5 clears with 2 players and with 4. The cage drops the moment a needed lever is released, and the relic can be lifted only while it's up.
- PG-10: in the escape, ghosts and cave beings go for the carrier first, and headlamps and flares hold them off. A team that sticks together gets the relic home at 2 and at 4 players.
- PG-11: the HUD, views and dead view look right in both split halves, before and after travel.
- PG-12: Playable 5 passes.
- PG-13: anything left over from earlier phases is done.
- PG-14: Demo 1 passes.

## Open questions

- Should the third-person view be available everywhere, or only outside tight passages where the camera would clip? The plan allows it everywhere and relies on the spring arm's collision.
- Should the taking pick the player who stays at random, or let the last player into the maze be the one left? The plan picks at random.
- In the chase, should ghosts go only for the carrier, or for whoever is nearest the carrier? The plan sends them at the carrier first.
