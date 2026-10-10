# Design direction: relics, traps and ghosts across puzzle maps

> Updated by [direction-2026-10-10.md](direction-2026-10-10.md): the maze run. The cave now plays as one room, a maze that splits the team up, two regroups, the relic, and an escape back to a drop-off in the first room. Its Demo 1, death and HUD sections replace the ones below.

Oct 9, 2026 · PK, for the team

This updates [two-to-four-players.md](two-to-four-players.md). Its rules on scaling for 2 to 4 players, stand-ins, split-screen safety and splitting work across the machines still apply. Where the two disagree, this doc wins.

## The game

- **Puzzle rounds across maps.** Most of the game is rounds of puzzle progression through a series of maps. Each chamber in a map is one round: solve its puzzle to open the way to the next.
- **The focus is traps, ghosts, relic collection and levels.** Traps and ghosts are the threats. Relics are what players collect, and the score for the run.
- **The first map is an underground cave.** The run starts in a spawn cavern with dim, shaded light. The team builds this small environment first and keeps improving it with textures, items and traps.

## How it plays

- **First person by default, with a switch to third person.** A player can glide between the two views, which also changes the field of view.
- **Split-screen.** For Demo 1, only on the hosting machine: two players share the Windows screen with gamepads while the Macs join online, for up to 4 players. Split-screen on joining machines comes after the demo.
- **No car.** Maps can end with a themed escape instead, such as a zipline out of the cave or camels in Egypt. These come after the core loop works.

**Death rule (updated Oct 10, 2026).** Lethal damage kills players immediately. There is no downed state, bleed-out or teammate revive. Dead players cannot move, interact, carry items or hold mechanisms, and ghosts ignore them. They remain dead until the server restarts the round or the team at a checkpoint; there is no individual automatic respawn. When the whole team is dead, the GameMode waits 3 seconds and restarts everyone at separate spots at the latest checkpoint, resetting any round in progress. The maze run adds that dead players also come back when a round clears; see [direction-2026-10-10.md](direction-2026-10-10.md#death).

## Demo 1

The cave with three puzzle rounds, then a short trip to Map 2, a small Egyptian antechamber. That proves the run can move from map to map. Replaced by the maze run in [direction-2026-10-10.md](direction-2026-10-10.md#demo-1).

## What changed from the first plan

| Before | Now |
| --- | --- |
| A heist site, a vault and a getaway car chase | Cave chambers, each one a puzzle round, then travel to the next map |
| Guardians | Ghosts that drift through walls and back off from light |
| Loot | Relics: small ones are collected instantly into a team count, and the heavy key relic is carried |
| Third-person camera | First person by default, with a switch to third person |
| Split-screen after the demo | Split-screen on the host in Demo 1 |
| Collapse at the end of the heist | Dropped for now; a cave-in could return as a map finale |
| Knockdown and teammate revive | Lethal damage kills players; no revives. A team wipe triggers a checkpoint restart |
