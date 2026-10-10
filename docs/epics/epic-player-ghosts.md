# Epic: Player view and ghosts (PG)

**Machine:** Mac 1 · **Owner:** PK · **Folder:** `Content/Player/` · **Sublevel:** `L_Site01_PG`

## Relationship to other epics (read first)

PG builds how players see the game and the ghosts that haunt it: first person with a switch to third person, the headlamp, player colors, split-screen on the host, the ghosts, Round 3's haunted gauntlet, and the zipline out of the cave. It also sets up the team's asset generation pipeline. It builds on [HC](epic-core-rounds.md)'s character, input contexts, interaction modes, round state and round reset. [HZ](epic-cave-traps.md) builds Round 3's hall and its traps. The sprint table, checkpoints and contracts are in [docs/sprints.md](../sprints.md), room positions in [docs/map/site01-layout.md](../map/site01-layout.md), and the asset pipeline in [docs/assets.md](../assets.md).

## Context

The Macs are always clients in playtests, so this lane sees the views and the ghosts exactly as joining players will. Split-screen is tested on the Windows host, where it runs in Demo 1.

## Locked decisions

- **First person by default.** `AC_PlayerView` drives the template character's own spring arm and camera:
  - First person: the camera at eye height with no arm, a 90° field of view, the character turning with the camera (Use Controller Rotation Yaw on, Orient Rotation to Movement off).
  - Third person: the camera over the shoulder, a 75° field of view, the character turning toward its movement (the reverse settings).
  - A switch glides between them in about 0.3 seconds, on the owning player's camera only.
- **The view is applied from scratch.** `ApplyViewState()` sets everything for the current mode, and runs at BeginPlay, whenever the pawn is possessed, and in the RepNotify. A RepNotify alone isn't enough, because it doesn't fire for an unchanged default.
- In first person your body is hidden from your own view (Owner No See), and still casts its shadow (Cast Hidden Shadow on). Everyone else, in every split view, sees your full body.
- **The headlamp is a spotlight on the head**, not on the camera, aimed each frame with Get Base Aim Rotation. That gives the same origin and aim on every machine, in both views. `bHeadlampOn` replicates. The server uses the same origin and aim for ghosts.
- Split-screen runs only on the host machine in Demo 1, in the `Lobby` and `Cleared` phases, with up to 2 local players and 4 in total. The host plays on keyboard and mouse, and the first gamepad becomes player 2.
- **Ghosts are replicated pawns that the server moves directly** through walls, every tick. They don't use the nav mesh or a movement component.
- Round 3 is PG's: its levers, gate and ghosts. HZ builds the hall and its traps.
- `AC_PlayerView` is a component with Component Replicates on, so PG's work doesn't touch `BP_CoopCharacter`; HC adds the component and forwards two keys in HC-2.

## Non-goals (for Demo 1)

- Split-screen on joining machines.
- First-person arms or held items, and animation beyond the template's.
- Ghosts with pathfinding or more than two behaviors.
- Camels in Egypt. They come with Map 2's content after the demo.

## Dependencies and sequencing

- PG-0 needs HC-0's bare project. PG-1 needs HC-0's `BP_CoopCharacter`.
- PG-1 tests on `BP_PG_TestCharacter`, a child of `BP_CoopCharacter` with the component added, in `L_PG_Test`. When HC-2 puts the component on the real character, remove it from the test character so there's only one.
- PG-1 publishes `BPFL_SplitScreen`'s stub, so HC-2 can wire F5 and F6 while PG-2 builds it.
- PG-4 spawns ghosts when a round starts. `StartRound` works from HC-1, so F1 and F2 start and clear rounds until HC-5's chamber triggers are in.
- PG-6's levers need HC-1's continuous interaction and HC-5's round reset. Its hall is HZ-5's, a sprint earlier.
- PG-7's zipline ends at HC-7's `BP_MapExit`, built in the same sprint.

## Phases

### PG-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, run `Tools/check-mac.command` until it passes. It checks for Unreal 5.8.3, Xcode 26.0–26.3 with the Metal toolchain, and enough disk space.

- At about minute 15, pull the bare project and open it. The first open compiles shaders for a while.
- Meanwhile, set up MCP with [docs/mcp.md](../mcp.md) and run its smoke test once the editor is up. PG owns that doc, so record what the tools can do there and push it.
- Join Playable 1.

### PG-1: First and third person (Sprint 1, 45 min)

- `AC_PlayerView` in `Content/Player/`, with Component Replicates on. On BeginPlay it finds the owner's spring arm, camera and body mesh, then calls `ApplyViewState()`.
- `ToggleView()` sends a Run on Server event from the component, which the owning player can call because their character owns it. The server sets the replicated `ViewMode`, and its RepNotify calls `ApplyViewState()` on every machine.
- `S_GhostScaling` and `DT_GhostScaling` with rows `2`, `3` and `4`: `GhostCount`, `GhostSpeed`, `GhostDamage` and `LeverCount`.
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
- On the server, about 5 times a second, it picks the nearest player within 20 m who isn't downed. Every tick it moves its root toward them by `GhostSpeed` times the frame time, slower than a walking player. Touching a player calls `Apply Damage` with `GhostDamage`, then the ghost backs off for 3 seconds.
- A gentle bob and a glow run on the visual mesh only, locally on every machine.
- Place one ghost in the spawn cavern's north passage. Also spawn one from a debug key in `L_PG_Test`, to check spawned ghosts behave like placed ones. Use a translucent greybox sphere until PG-A2's ghost arrives.
- Join Playable 2.

### PG-4: Ghosts each round, and player colors (Sprint 4, 45 min)

- `BP_GhostSpawner` in each chamber, on the server only: when its round starts, spawn `GhostCount` ghosts at its spawn points. Start with 1 ghost for 2 players, 1 for 3 and 2 for 4. They leave when the phase stops being `Playing`, and the spawner implements `BPI_RoundReset`, so a restart brings a fresh set.
- Remove the ghost placed in PG-3, so spawners are the only source.
- `ApplyColorSlot()`: apply PG-A1's color variant for the player's `ColorSlot` on every machine, when the slot replicates, on possession and after travel.

### PG-5: Ghosts back off from light (Sprint 5, 45 min)

- On the server, each lit headlamp picks at most one ghost: the one nearest the center of its cone, within 12 m and not behind a wall (a line trace). It keeps that ghost for at least half a second before switching, so the choice doesn't flicker.
- A picked ghost backs away and dims; every other ghost carries on. So one headlamp holds off one ghost, never two.

### PG-6: The haunted gauntlet (Sprint 6, 60 min) → Playable 3

- Round 3 in chamber 3, built in `L_Site01_PG`. `BP_Lever` is a continuous interaction: active from `InteractBegin` to `InteractEnd`. `LeverCount` levers are needed: 1 for 2 or 3 players, 2 for 4.
- `BP_GauntletGate` stays open while every needed lever is active. `BP_ExitLever`, past the traps, is an instant interaction that latches the gate open and calls `ClearRound()`.
- All three implement `BPI_RoundReset`: a restart releases the levers, closes the gate and unlatches the exit lever.
- The round's ghosts favor the lever holders, so the crossing players' headlamps matter.
- Join Playable 3.

### PG-7: Zipline (Sprint 7, 45 min)

- `BP_Zipline` from the exit ledge down to the map exit. Using it is an instant interaction that spawns a trolley for that player on the server, so several players can ride at once.
- The trolley replicates its rider, its start time in server time and its speed. Every machine places it on the zipline's spline from those, the same way on each.
- The server attaches the rider, turns their movement off through a RepNotify, and at the bottom detaches them onto the landing and turns movement back on. Riders can't be damaged while riding. A round reset or the rider leaving removes the trolley and returns the rider to the latest checkpoint.
- Keep it only if a 4-player test passes by the end of the sprint. Otherwise the walkway is the route out, and the zipline moves to after Demo 1.

### PG-8: Split-screen and view polish (Sprint 8, 45 min)

- Both split views: the HUD in each half, the field of view in each view, the third-person camera in tight passages, and the glide's feel.
- With HC, check that the split-screen pair survives travel to Map 2 and back.

### PG-9: Tuning (Sprint 9, 60 min) → Playable 4

- Under network emulation, from a Mac: tune ghost speed, damage and back-off, and the headlamp's reach.
- Join Playable 4.

### PG-10: Buffer (Sprint 10, 45 min)

- Finish whatever earlier phases left behind, then polish the first moment a ghost appears.

### PG-11: Demo (Sprint 11, 60 min) → Demo 1

- Final fixes. Tune ghosts so 2 players aren't overwhelmed and 4 aren't bored.

## Asset generation

Follow [docs/assets.md](../assets.md) for specs, licensing, imports and reviews. Raw output goes in `SourceArt/PG/`, imported assets in `Content/Player/Art/`.

| Task | Sprint | Assets | Specs | Used in |
| --- | --- | --- | --- | --- |
| PG-A0: Pipeline | 1 | Pick the generators for meshes, textures and sound, and settle the import presets for meshes and textures on both a Mac and Windows. Take one prop all the way from a prompt to placed in a test map, and fill in the open parts of `docs/assets.md`. Build the style kit in [art/style.md](../art/style.md#the-style-kit): `M_Stylized`, `L_StyleTest`, and an example rock and gold prop. | Record each tool's cost, plan and license terms, including whether outputs on that plan can be published in a public repo. | Every lane |
| PG-A1: Player colors | 3 | Four color variants of the template character, such as a helmet, scarf or backpack tint, so players are easy to tell apart in a dark cave and in split views. In place by Sprint 4. | Material instances of `M_Stylized`; no new meshes needed. Colors stay clear of the reserved palette colors. | PG-4 |
| PG-A2: Ghost | 4 | A ghost mesh and a translucent, glowing material that fades at the edges. In place by Sprint 5. | Up to 5k triangles, with **Nanite off**, since Nanite doesn't support translucent materials. The material must read in the dark from 15 m away. | PG-3 onward |
| PG-A3: Ghost sounds | 6 | A whisper loop, an attack shriek, and a hiss when light drives a ghost back. In place by Sprint 8. | Mono WAV, 48 kHz, played as 3D sound with attenuation. | PG-5 onward |
| PG-A4: Zipline | 6 | Cable, anchors and a trolley handle. In place by Sprint 7. | Cable as a spline mesh. Handle up to 2k triangles. | PG-7 |

## Critical assets

- `Content/Player/`: `AC_PlayerView`, `BPFL_SplitScreen`, `S_GhostScaling`, `DT_GhostScaling`, `L_Site01_PG`, `Art/`
- `Content/Player/Ghosts/`: `BP_Ghost`, `BP_GhostSpawner`
- `Content/Player/Round3/`: `BP_Lever`, `BP_GauntletGate`, `BP_ExitLever`
- `Content/Player/Zipline/`: `BP_Zipline`, `BP_ZiplineTrolley`
- `Content/Player/Test/`: `L_PG_Test`, `BP_PG_TestCharacter`
- `docs/mcp.md`, `docs/assets.md`

## Build and playtest notes

- You're a client in every playtest. If a view or a ghost feels wrong on your Mac, it is wrong.
- LAN latency is tiny. Before you call the views or ghosts done, test with network emulation set to an average internet profile (Editor Preferences → Level Editor → Play → Multiplayer Options).
- Split-screen only runs on the host, so test it in Play In Editor with a second local player, then on the Windows machine at the merge.

## Verification

- PG-0: the smoke test results are in `docs/mcp.md`, and both Macs join Playable 1.
- PG-1: a client starts in first person without pressing anything, switches views while moving, and the other clients see them face the right way.
- PG-2: two players play side by side on one screen, each with their own view, headlamp and HUD, while two clients play online. A headlamp points where its player looks, on every machine and in both views.
- PG-3: a placed ghost and a spawned ghost both drift through walls after the nearest standing player, damage them on contact, then back off.
- PG-4: after F1, the ghost count matches the player count, and a restarted round brings a fresh set. Every player has a different color on every screen.
- PG-5: one headlamp drives back one ghost, never two, the same way on every machine.
- PG-6: Round 3 clears with 2 players and with 4. The gate closes the moment a needed lever is released, and a restart resets all three pieces.
- PG-7: two clients ride the zipline at once, smoothly from every other client's point of view, and land on their feet. Or the walkway is confirmed as the route.
- PG-8: the HUD and views look right in both split halves, before and after travel.
- PG-9: Playable 4 passes.
- PG-10: anything left over from earlier phases is done.
- PG-11: Demo 1 passes.

## Open questions

- Should the third-person view be available everywhere, or only outside tight passages where the camera would clip? The plan allows it everywhere and relies on the spring arm's collision.
