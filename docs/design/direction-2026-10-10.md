# Design direction: the maze run

Oct 10, 2026 · PK, for the team

This updates [direction-2026-10-09.md](direction-2026-10-09.md). The cave, first person with a switch to third person, split-screen on the host, no car, and the focus on relics, traps and ghosts all stay. What changes is the shape of a run: instead of three chambers in a line, the team solves one room, gets split up in a maze, regroups twice, takes the relic and runs it home. Where the two docs disagree, this one wins.

## The run

1. **The first room.** The team spawns in the cavern lit by the daylight shaft. Everyone stands on the start pad, and Round 1 starts. The room is an old mine, and its puzzle is the mine's work. The team finds a pickaxe and breaks the boulders with it. Each boulder breaks into rocks that lie on a hidden pressure plate, and lifting the rocks off uncovers the plate. The rocks go into the mine cart, and once the cart is full enough, players push it along its rails to the end of the track. When the cart is there and every uncovered plate is held down, by a player or by a spare rock, the gate opens into the first hallway. The details are in [The first room](#the-first-room). The drop-off altar stands in this room, empty, so the team sees where the run ends.
2. **The taking.** The team walks into the maze mouth together, and the door shuts behind them. Then something in the dark takes them, one at a time and without warning, each in a different way: a hand drags someone into the wall, the floor swallows someone, the lights cut out and when they come back someone is gone. Everyone still standing sees each person vanish. It stops when one player is left. Each taken player comes to alone at the start of their own path, and the last player goes on alone down the only way left open.
3. **The first paths.** Each player crosses their own path alone: booby traps, ledges to climb, rubble to climb over, gaps to jump. The paths wind over and under each other on rock bridges, so players catch glimpses of each other but can't join up.
4. **The meeting hall.** Every path ends in the same hall. Together, the players use their tools to light all of the hall's locks at the same moment. That opens one door for each player in the game, four at most.
5. **The second paths.** Each player takes a door, and it closes behind them, so the team splits up again. These paths are harder: more traps, more climbing and jumping, stretches you have to sprint through, like a bridge that collapses behind you or a boulder rolling after you, and scares, like bats bursting out of a crack or a ghost drifting through the wall beside you.
6. **The relic chamber.** The second paths meet in the final chamber, where the relic sits in a cage. One puzzle frees it: players hold levers to keep the cage raised while one of them lifts the relic.
7. **The escape.** The relic is heavy, so its carrier moves slowly. The moment it's lifted, the cave wakes up: ghosts and cave beings pour out and chase the team. The run home starts with the zipline down from the relic chamber, then goes back through the cave's dark halls and trap corridor. Everyone else protects the carrier with their tools.
8. **The drop-off.** Placing the relic on the altar in the first room completes the mission. The run then travels to Map 2, where the results show the relics collected.

## Tools

Every player carries the same two tools in Demo 1:

- **Headlamp.** It lights the way, holds off one ghost at a time, and lights a crystal lock when you keep it aimed at the lock.
- **Flares.** You throw a flare, and it burns for about 20 seconds. Ghosts and cave beings won't enter its glow, and a flare dropped into a brazier lights it. Players start with 2 or 3 and get more each time the team regroups.

The relic's carrier has their hands full: they can't throw flares, sprint or climb, but their headlamp still works. Tool slots, roles and the Scout's rope and grappling hook still come after Demo 1.

## Moving through the maze

Players can sprint, jump, climb up ledges, and climb marked ropes, vines and handholds. HZ builds the paths to the measurements in the [layout doc](../map/site01-layout.md#moving-through-the-maze), and PG tunes the moves to match.

Most missed jumps cost time, not a life: you drop into a pit with a climb back out. Only chasms that look deadly kill you.

## Rounds and checkpoints

The run is six rounds, and the HUD shows each one by name:

| Round | Name | Starts when | Clears when |
| --- | --- | --- | --- |
| 1 | The first room | Everyone is on the start pad | The cart is at the end of its track and every uncovered plate is pressed |
| 2 | The maze | The whole team is inside the maze mouth | Every living player is in the meeting hall |
| 3 | The meeting hall | Round 2 clears | Every lock is lit at once and the doors open |
| 4 | The deep maze | Round 3 clears | Every living player is in the relic chamber |
| 5 | The relic | Round 4 clears | A player lifts the relic |
| 6 | The escape | Round 5 clears | The relic is on the drop-off altar |

Each round has a checkpoint. In Rounds 2 and 4, each player's spot is the start of their own path.

## The first room

The puzzle uses things a mine would have: a pickaxe, boulders, a mine cart on rails and a gate.

1. **Find the pickaxe.** It lies on a crate in the corner by the barrels, away from the player starts. Anyone can pick it up with Interact (E), and it sits in their right hand. While you hold it, your hands are full, so someone else carries the rocks. Drop it with G. Players walk through the pickaxe and the rocks instead of kicking them, so nothing gets knocked out of reach.
2. **Break the boulders.** The dark boulders are the ones you can break. Look at one while holding the pickaxe and swing with the left mouse button (or the right trigger). Three swings break it into three rocks. Interact does nothing on a boulder; its prompt says to left-click, or that you need a pickaxe. Light-colored rocks are scenery.
3. **Uncover the plates.** Each boulder hides a pressure plate under its rocks. The plate appears once every rock has been lifted off it.
4. **Fill the cart.** Carry a rock to the cart and use it to drop the rock in. The count on the cart shows how many rocks it has and how many it needs, and turns green when it has enough. It holds up to three more than it needs.
5. **Push the cart.** Once the cart has enough rocks, hold interact behind it to push it along the rails. Two players push it twice as fast. A lamp lights when it reaches the end of the track.
6. **Hold down the plates.** A plate is pressed by a player standing on it or a rock lying on it. There are more rocks than the cart needs, so a spare rock can hold a plate.
7. **The gate opens.** When the cart is at the end of the track and every uncovered plate is pressed at the same moment, Round 1 clears and the gate opens into the first hallway.

A round restart puts the boulders back, removes every rock, returns the cart to the start of the track and the pickaxe to its crate, and hides the plates again.

## Death

There are still no revives and no downed state. Lethal damage kills you on the spot.

- **While you're dead,** you watch a living teammate's view. Interact switches to the next one.
- **When the team regroups,** you come back. When a round clears, everyone who died in it comes back where the team is gathering: the first room, the meeting hall or the relic chamber. Nothing brings you back sooner.
- **When the whole team dies,** the round restarts from its checkpoint after 3 seconds, with everyone alive. A round also restarts if the living players can no longer finish its puzzle, for example a single survivor in the relic chamber.
- **If the relic's carrier dies,** the relic drops where they fell, and any living player can pick it up. If the escape restarts, the relic goes back on its pedestal with the cage open, so the levers don't have to be done again.

## Making it work for 2 to 4 players

Starting values; tune them in playtests.

| | 2 players | 3 players | 4 players |
| --- | --- | --- | --- |
| Players taken in the taking | 1 | 2 | 3 |
| Paths in use, each time the team splits | 2 | 3 | 4 |
| First room: boulders in play | 3 | 3 | 4 |
| First room: rocks the cart needs | 6 | 7 | 9 |
| Meeting hall: headlamp locks and brazier locks | 1 and 1 | 2 and 1 | 2 and 2 |
| Doors that open | 2 | 3 | 4 |
| Levers to raise the relic's cage | 1 | 1 | 2 |
| Chase: ghosts and cave beings per wave | 2 | 3 | 4 |
| Flares each player starts with | 3 | 2 | 2 |

Four paths are built for each split. With fewer players, the extra paths sit empty. Flares stand in for missing players at the locks: one player can light a brazier and then hold a beam on another lock before the flare burns out.

## The HUD

The HUD needs depth. Today's frames are hollow, so the cave shows through them and thin default text floats over the scene. From now on, every panel is solid and layered (a soft shadow, a carved frame, a recessed plate, then the text), and the text uses a carved display typeface instead of the engine default. The HUD steps back when nothing is happening, so the cave stays scary. The rules are in [art/style.md](../art/style.md#hud-and-ui).

It shows:

- The round's name and objective, large when a round starts or clears, then as one small line.
- The team's relics.
- The team: each player's color, and whether they're alive, dead or carrying the relic.
- Your tools: the headlamp and how many flares you have left.
- The interact prompt and its hold bar.
- While you're dead, whose view you're watching, and that you'll be back when the team regroups.

## Demo 1

The maze run in the cave, from the start pad to the drop-off, then the trip to Map 2 for the results. That still proves a run can move from map to map.

## What changed

| Before | Now |
| --- | --- |
| Three chambers in a line, each one a round | One room, then a maze: the team is split up, regroups twice, takes the relic and runs it home. Six rounds. |
| Round 1 in a plate hall past the spawn cavern | Round 1 is the first room's mining puzzle, in the spawn cavern. The plate hall is on the way home. |
| Plates held down by players, with statues standing in for missing players | Plates hidden under boulders, held down by players or spare rocks. No statues. |
| The key relic carried from a side passage to an altar | The relic waits at the end of the maze and is carried back to the drop-off altar in the first room |
| Round 3: hold levers while the others cross a haunted hall | The levers hold up the relic's cage. The haunted hall is on the way home. |
| Tool slots and the Scout after Demo 1 | Every player has the headlamp and flares in Demo 1. Tool slots and roles still come later. |
| Ghosts in each chamber | Ghosts in each round, plus the taking and the chase home |
| The zipline takes the team out of the cave to the map exit | The zipline takes the team down from the relic chamber at the start of the escape |
| The run ends at the map exit | The mission completes at the drop-off, then Map 2 shows the results |
| Dead players stay dead until a restart | Dead players also come back when the team regroups. Still no revives. |
| The prototype maze's co-op moments, brace and boost, on each path | The paths are solo, so there's no brace or boost on them. They can return in the meeting hall and the relic chamber. |
| Translucent HUD frames with default text | Solid, layered panels with a carved typeface |

## Open questions

- Are the headlamp and flares enough, or does Demo 1 need a third tool? The first room's pickaxe stays in that room; it isn't a tool players carry on.
- How long should each path take? Start with 2 to 3 minutes for the first paths and 3 to 4 for the second, and tune from playtests.
- Should a dead player come back when the team regroups, or stay out until a restart? The plan brings them back, so nobody waits out a whole run.
- In the chase, should ghosts go only for the carrier, or for whoever is nearest the carrier?
- After the drop-off, should the run still travel to Map 2 for the results, or show them in the first room?
