# Co-op Game: 2 to 4 Players, Local and Online

> Updated by [direction-2026-10-09.md](direction-2026-10-09.md): no car, a cave start, first person with a switch to third person, split-screen on the host for Demo 1, and a focus on relics, traps and ghosts across puzzle maps. The scaling, stand-in and split-screen-safe rules below still apply.

Oct 9, 2026 · Peter Kim

## Design: making it work for 2 to 4 players

Every system must work at 2, 3 and 4 players, because the team's natural size of 3 hides scaling problems.

**Puzzles must scale.** A puzzle that needs exactly three people breaks with two and leaves someone idle with four. Two techniques fix this:

- **Stand-ins:** anything a player can do, an object can also do. A heavy statue can hold a pressure plate and a wedge can jam a lever. Two players solve the "three-person" puzzle with extra effort; four players solve it faster.
- **Scaled mechanisms:** the site reads the player count and sets how many plates, levers or dials appear.

**Roles become tool slots.** Each player carries a limited number of tools (for example, two). With two players, each person covers two roles and has to juggle. With four, people specialize, and a fourth role fits naturally: a Scout with rope, a grappling hook and the map, who finds shortcuts and alternate routes.

**Threat scales too.** Guardian and rival counts, trap timing and loot quantity adjust to the number of players.

**The getaway vehicle seats four.** One driver, plus passengers who shoot back at rivals, hold loot or fix things.

## Tech: what "local" means and how to build for it

Build online first, but follow split-screen-safe rules from day one so couch play can be added later without a rewrite.

"Local" has two meanings:

- **LAN** (everyone on the same network, separate screens): already covered. The listen-server setup works the same over LAN as online.
- **Split-screen couch co-op** (one screen, multiple controllers): Unreal supports this, including from Blueprint, but it touches cameras, HUD and input across the whole project.

**Split-screen-safe rules:**

- Never use "Get Player Character (0)" or "Get Player Controller (0)" in gameplay Blueprints. Always use the owning player, the instigator, or the actor that triggered the event. This one rule prevents most split-screen bugs, and AI agents reach for index 0 constantly, so put it in every agent's instructions.
- Add HUD widgets to the owning player's screen, not the viewport globally.
- Keep input in Enhanced Input mapping contexts per player.

Mixing the two (two people on a couch joining two online players) is the hardest case. Treat it as a later milestone, after a single site is fun.

**Shipping online.** For playtests, `open <ip>` is enough. Before sharing the game outside the team, add a session system so players can find and join games without IP addresses. Epic Online Services is the natural choice: free, usable from Blueprint, and supports both Mac and Windows. It is not needed for the first sprints.

## Changes to the sprint plan

- **Sprint 0:** set the max player count to 4 and confirm 4 players can join (the 3 team machines plus a second client launched from the Windows editor).
- **Every playtest:** test at least once with 2 players and once with 4. The team size makes 3 feel normal, but 2 and 4 are where scaling breaks.
- **Split-screen:** gets its own sprint after the first playable demo, once the core site works online.

## Splitting work across one Windows machine and two Macs

The Windows machine is the build, host and reference machine; the Macs are always clients in playtests, which makes them natural testers for network bugs.

| Machine | Role | Feature lane | Why |
| --- | --- | --- | --- |
| Windows | Integrator + host | Heist lane: interaction, puzzle mechanisms, round flow | Owns GameMode, GameState and the character base most sprints, so the person merging also holds the shared core, with fewer lock handoffs |
| Mac 1 | Feature dev | Vehicle and getaway chase | Vehicle jitter and replication bugs show up on clients, and this person is always a client in playtests |
| Mac 2 | Feature dev | Traps, guardians, collapse, atmosphere and audio | Self-contained actors in their own folder, rarely needs a shared-asset lock |

The Windows person's extra jobs:

- **Merging:** pulls everyone's work at the end of each sprint and resolves any problems.
- **Building and hosting:** launches the playtest build and hosts the listen server.
- **Judging look and performance:** lighting, Lumen and frame rate can differ between Mac and Windows, so the final call on visuals and performance (especially 4-player split-screen) is made on Windows.
- **Packaging:** only Windows can package Windows builds. Shipping to Mac players later means packaging on a Mac.

Because of this, the Windows person takes a smaller feature each sprint, with about 15 minutes budgeted for merge and build.

**Sprint rhythm:**

- Macs push their work about 10 minutes before the sprint ends.
- Windows pulls, merges and launches the build (or Standalone from the editor).
- Everyone pulls the merged commit, so all three are on the exact same version.
- Windows hosts, Macs join with `open <ip>`, and the team playtests.

**Rules that keep Mac and Windows in sync:**

- The Windows dev tests as a client too. The host view hides most network bugs, so use Play As Client in the editor before pushing.
- Every plugin must support Mac. That includes the MCP plugin and anything from Fab; a Windows-only plugin silently breaks the Mac editors.
- Stay Blueprint-only as long as possible. Once C++ is added, every machine has to compile it (Visual Studio on Windows, Xcode on the Macs), which adds setup and a new way for builds to fall out of sync.
