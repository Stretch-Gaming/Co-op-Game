# Epic: Player view and ghosts (PG)

**Machine:** Mac 1 · **Owner:** PK · **Folder:** `Content/Player/` · **Sublevel:** `L_Site01_PG`

## Relationship to other epics (read first)

PG builds how players see the game and the ghosts that haunt it: first person with a switch to third person, the headlamp, split-screen on the host, the ghosts, Round 3's haunted gauntlet, and the zipline out of the cave. It also picks the asset generation pipeline for the team. It builds on [HC](epic-core-rounds.md)'s character, input contexts, interaction and round framework. [HZ](epic-cave-traps.md) builds Round 3's hall and its traps. The sprint table, checkpoints and contracts are in [docs/sprints.md](../sprints.md), room positions in [docs/map/site01-layout.md](../map/site01-layout.md), and the asset pipeline in [docs/assets.md](../assets.md).

## Context

The Macs are always clients in playtests, so this lane sees the views and the ghosts exactly as joining players will. Split-screen is tested on the Windows host, where it runs in Demo 1.

## Locked decisions

- **First person by default.** `AC_PlayerView` drives the template character's own spring arm and camera. First person puts the camera at eye height with no arm and a 90° field of view. Third person pulls back over the shoulder with a 75° field of view. A switch glides between them in about 0.3 seconds.
- In first person, your own body is hidden from your view (Owner No See) but still casts its shadow. Everyone else, in every split view, sees your full body.
- The view mode replicates. First person turns the character with the camera; third person turns it toward movement. Every machine applies the same rotation settings, so other players see you facing the right way.
- The headlamp is a spotlight on the camera. It replicates so everyone sees it, and the server uses it to decide which ghosts are lit.
- Split-screen runs only on the host machine in Demo 1. The host plays on keyboard and mouse, and the first gamepad becomes player 2.
- Ghosts are floating pawns that drift through walls and are moved by the server. They don't use the nav mesh.
- Round 3 is PG's: its levers, gate and ghosts. HZ builds the hall and its traps.
- `AC_PlayerView` is a component, so PG's work doesn't touch `BP_CoopCharacter`; HC adds the component and forwards two keys in HC-2.

## Non-goals (for Demo 1)

- Split-screen on joining machines, and more than one local player added on the host per gamepad.
- First-person arms or held items, and animation beyond the template's.
- Ghosts with pathfinding or more than two behaviors.
- Camels in Egypt. They come with Map 2's content after the demo.

## Dependencies and sequencing

- PG-0 needs HC-0's bare project.
- PG-1 tests on `BP_PG_TestCharacter`, a child of `BP_CoopCharacter` with the component added, in `L_PG_Test`. HC puts the component on the real character in HC-2.
- PG-2's host keys F5 and F6 are wired by HC-2, in the same sprint. Test with your own key on the test character until then.
- PG-4 spawns ghosts when a round starts. `StartRound` works from HC-1, so F1 and F2 start and clear rounds until HC-4's chamber triggers are in.
- PG-6's Round 3 sits in HZ-6's hall, built in the same sprint. HZ-1's blockout is enough to start.
- PG-7's zipline ends at HC-7's `BP_MapExit`.

## Phases

### PG-0: Setup (Sprint 0, 60 min) → Playable 1

Before the sprint, run `Tools/check-mac.command` until it passes. It checks for Unreal 5.8.3, Xcode 26.0–26.3 with the Metal toolchain, and enough disk space.

- At about minute 15, pull the bare project and open it. The first open compiles shaders for a while.
- Meanwhile, set up MCP with [docs/mcp.md](../mcp.md) and run its smoke test once the editor is up. PG owns that doc, so record what the tools can do there and push it.
- Join Playable 1.

### PG-1: First and third person (Sprint 1, 45 min)

- `AC_PlayerView` in `Content/Player/`, with Component Replicates on. On BeginPlay it finds the owner's spring arm and camera. `ToggleView()` sends a Run on Server event that sets the replicated `ViewMode`. Its RepNotify plays the glide on the owning player's camera, sets Owner No See on the body and applies the rotation settings on every machine.
- `ToggleHeadlamp()` replicates `bHeadlampOn` the same way.
- `S_GhostScaling` and `DT_GhostScaling` with rows `2`, `3` and `4`: `GhostCount`, `GhostSpeed`, `GhostDamage` and `LeverCount`.
- Test on `BP_PG_TestCharacter` in `L_PG_Test` as a client. Switch views while moving, and check the other client sees you face the right way.

### PG-2: Split-screen on the host (Sprint 2, 45 min)

- `BPFL_SplitScreen` in `Content/Player/`: `AddLocalPlayer()` calls Create Local Player for the next free gamepad, and `RemoveLocalPlayer()` removes the last one added. Both only work on the host.
- Check that the second player gets their own view and mode, their own headlamp, and their own prompt and HUD widgets on their half of the screen.
- With the host, a split-screen player and two Mac clients, play for a few minutes and note the frame rate on Windows.

### PG-3: First ghost (Sprint 3, 60 min) → Playable 2

- `BP_Ghost`: a Pawn with floating movement and Replicate Movement on. Its collision overlaps everything, so it passes through walls.
- On the server, about 5 times a second: pick the nearest player within 20 m who isn't downed, and drift toward them at `GhostSpeed`, slower than a walking player. Touching a player calls `Apply Damage` with `GhostDamage`, then the ghost backs off for 3 seconds.
- A gentle bob and a translucent glow run locally on every machine and aren't replicated.
- Place one ghost in the spawn cavern's north passage.
- Join Playable 2.

### PG-4: Ghosts each round (Sprint 4, 45 min)

- `BP_GhostSpawner` in each chamber, on the server only: when its round starts, spawn `GhostCount` ghosts at its spawn points. Start with 1 ghost for 2 players, 1 for 3 and 2 for 4. They leave when the phase stops being `Playing`, so a restart brings back a fresh set.
- Remove the ghost placed in PG-3, so spawners are the only source.

### PG-5: Ghosts back off from light (Sprint 5, 45 min)

- On the server, a ghost inside any player's headlamp cone, within 12 m, backs away and dims. The server knows each player's aim, so this needs nothing new from clients.
- Tune so one headlamp holds a ghost off but can't hold two at once.

### PG-6: The haunted gauntlet (Sprint 6, 60 min) → Playable 3

- Round 3 in chamber 3, built in `L_Site01_PG`. `BP_Lever` implements `BPI_Interactable` and stays active only while a player holds Interact on it. `LeverCount` levers are needed: 1 for 2 or 3 players, 2 for 4.
- `BP_GauntletGate` stays open while every needed lever is held. `BP_ExitLever`, past the traps, opens it for good and calls `ClearRound()`.
- The round's ghosts favor the lever holders, so the crossing players' headlamps matter.
- Join Playable 3.

### PG-7: Zipline (Sprint 7, 45 min)

- `BP_Zipline` from the exit ledge down to the map exit. Interacting attaches the player to a trolley that moves along the zipline's spline on the server. Like the ghosts, it replicates one struct holding the distance and the server time, and every machine places it from the spline.
- While riding, the character's movement is off, through a RepNotify. At the bottom it's detached and dropped onto the landing.
- If it isn't solid by the end of the sprint, leave the walkway as the only route and move the zipline to after Demo 1.

### PG-8: Tuning (Sprint 8, 60 min) → Playable 4

- Under network emulation, from a Mac: tune ghost speed, damage and back-off, and the view glide.
- Split-screen polish on Windows: check the HUD in both halves, the field of view in each view, and that the split pair survives travel to Map 2.
- Join Playable 4.

### PG-9: Demo (Sprint 9, 60 min) → Demo 1

- Fix what Playable 4 found. Tune ghosts so 2 players aren't overwhelmed and 4 aren't bored.
- Feel: the glide, the headlamp's reach, and the first moment a ghost appears.

## Asset generation

Follow [docs/assets.md](../assets.md) for specs, imports and reviews. Raw output goes in `SourceArt/PG/`, imported assets in `Content/Player/Art/`.

| Task | Sprint | Assets | Specs | Used in |
| --- | --- | --- | --- | --- |
| PG-A0: Pipeline | 1 | Pick the generator for meshes, textures and sound. Take one prop all the way from a prompt to placed in a test map, and fill in the open parts of `docs/assets.md`. | Record the tools, their costs and their licenses. | Every lane |
| PG-A1: Player variants | 2 | Four color variants of the template character, such as a helmet, scarf or backpack tint, so players are easy to tell apart in a dark cave and in split views. | Material instances of one master material; no new meshes needed. | PG-2 onward |
| PG-A2: Ghost | 3 | A ghost mesh and a translucent, glowing material that fades at the edges. | Up to 5k triangles. The material must read in the dark from 15 m away. | PG-3 |
| PG-A3: Ghost sounds | 5 | A whisper loop, an attack shriek, and a hiss when light drives a ghost back. | Mono WAV, 48 kHz, played as 3D sound with attenuation. | PG-5, PG-6 |
| PG-A4: Zipline | 6 | Cable, anchors and a trolley handle. | Cable as a spline mesh. Handle up to 2k triangles. | PG-7 |

## Critical assets

- `Content/Player/`: `AC_PlayerView`, `BPFL_SplitScreen`, `S_GhostScaling`, `DT_GhostScaling`, `L_Site01_PG`, `Art/`
- `Content/Player/Ghosts/`: `BP_Ghost`, `BP_GhostSpawner`
- `Content/Player/Round3/`: `BP_Lever`, `BP_GauntletGate`, `BP_ExitLever`
- `Content/Player/Zipline/`: `BP_Zipline`
- `Content/Player/Test/`: `L_PG_Test`, `BP_PG_TestCharacter`
- `docs/mcp.md`, `docs/assets.md`

## Build and playtest notes

- You're a client in every playtest. If a view or a ghost feels wrong on your Mac, it is wrong.
- LAN latency is tiny. Before you call the views or ghosts done, test with network emulation set to an average internet profile (Editor Preferences → Level Editor → Play → Multiplayer Options).
- Split-screen only runs on the host, so test it in Play In Editor with a second local player, then on the Windows machine at the merge.

## Verification

- PG-0: the smoke test results are in `docs/mcp.md`, and both Macs join Playable 1.
- PG-1: a client switches views while moving, and the other clients see them face the right way. The headlamp shows on every machine.
- PG-2: two players play side by side on one screen, each with their own view, headlamp and HUD, while two clients play online.
- PG-3: the ghost drifts through walls after the nearest standing player, damages them on contact, then backs off.
- PG-4: after F1, the ghost count matches the player count, and a restarted round brings a fresh set.
- PG-5: a headlamp drives a ghost back on every machine.
- PG-6: Round 3 clears with 2 players and with 4. The gate closes whenever a needed lever is let go.
- PG-7: a client rides the zipline smoothly from every other client's point of view, and lands on their feet.
- PG-8: Playable 4 passes.
- PG-9: Demo 1 passes.

## Open questions

- Which generator: Meshy, Tripo, Hunyuan3D or something else? PG-A0 decides, with the team's budget in mind.
- Should the third-person view be available everywhere, or only outside tight passages where the camera would clip? The plan allows it everywhere and relies on the spring arm's collision.
