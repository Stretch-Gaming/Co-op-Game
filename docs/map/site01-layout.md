# Site 1 layout: the cave

Every lane builds against these positions, so the puzzles, traps, ghosts and zipline line up without anyone opening someone else's sublevel. Ask your agent to build from this table.

Positions are in meters; 1 m is 100 Unreal units. X points east along the route, Y points north, and the floor is at Z = 0 unless a row says otherwise. Sizes are width (along X) by depth (along Y).

The run is a loop, as [direction-2026-10-10.md](../design/direction-2026-10-10.md#the-run) describes. The team leaves the first room through the maze door in its north wall, crosses the maze, and comes home through the cave's east chambers, carrying the relic to the drop-off altar.

```
            first paths, one per player               second paths, one per player
 [2 Maze mouth] ===========================> [3 Meeting hall] ===========================> [4 Relic chamber]
   the taking                                  locks, 4 doors                                cage, levers
       ^                                                                                         |
   maze door                                                                          zipline or walkway down
       |                                                                                         v
 [1 First room] <- [10 Passage] <-G1- [9 Plate hall] <-G2- [8 Trap corridor] <- [7 Altar cavern] <-G3- [6 Haunted hall] <- [5 Exit ledge]
   start pad, plates,  spikes            empty now          traps timed for       empty now            dark, traps
   drop-off altar                                           the slow carrier
```

The maze lies north of the first room, as it does in the [CoopCave prototype](../../Prototypes/CoopCave/README.md#the-maze), which it's built from. The gates G1 to G3 stay shut until the escape starts, so nobody wanders the way home early. Each checkpoint has four spawn spots about 1.5 m apart, so players never land on each other. In the maze's two sets of paths, a checkpoint's four spots are the starts of the four paths instead.

## Areas, in the order the team reaches them

Areas 2 to 5 come from the prototype maze. HZ sets their positions in HZ-6 and fills in this table in the same commit. Until then, the constraints in each row hold.

| # | Area | Center or span (X, Y) | Size | Owner | What goes there |
| --- | --- | --- | --- | --- | --- |
| 1 | First room (the spawn cavern) | 0, 0 | 30 × 30, 12 m ceiling | HZ | 4 player starts at X −10, Y −6 to 6 (HC, persistent level). The first checkpoint, with four spawn spots, at (−8, 0) (HC). The start pad at (8, 0) (HC). Round 1's four plates and two statue alcoves on the open floor, at spots HZ marks in HZ-6 (HC). The drop-off altar against the west wall, in view of the player starts (HC). The maze door in the north wall at (0, 15) (HC). The passage leaves through the east wall. A crack in the ceiling above (−4, 4) lets in a shaft of daylight (HZ). Tutorial relics at (−8, 12) and (10, −12) (HC). |
| 2 | Maze mouth | From the maze door at (0, 15) north to the fork | 3 m wide, about 30 m long, dark | HZ | Round 2's start volume, which needs the whole team inside, just past the door (HC). The taking happens along this passage (PG). At the fork, four path mouths. When the taking ends, rockfall seals all but the last player's path (HZ). Round 2's checkpoint spots at the start of each first path, out of sight of the fork (HC). |
| — | First paths | From the fork to the meeting hall | Four paths, 3–4 m wide | HZ | One path per player. Each takes 2 to 3 minutes and has spike, dart and swing traps, ledges to climb, rubble to climb over and gaps to jump, built to [the measurements below](#moving-through-the-maze). Paths cross over and under each other on rock bridges without joining, and grates or cracks let players glimpse each other. Small relics off the main line (HC). |
| 3 | Meeting hall | Set in HZ-6 | About 30 × 30, 14 m ceiling | HZ | The prototype's sunken hall. Every first path ends here. Round 3's checkpoint in the middle (HC). The locks: headlamp locks up on perches you have to climb to see them, and brazier locks on the floor (HC). Four doors, one into each second path (HC). Ghost spawn points (PG). |
| — | Second paths | From the meeting hall's doors to the relic chamber | Four paths | HZ | One path per player. Each takes 3 to 4 minutes and is harder than the first paths: more traps, more climbing and jumping, and stretches to sprint through, like a collapsing bridge, a rolling boulder or falling rocks. Scares, like bats bursting out of a crack (HZ) and a ghost drifting through the wall (PG). Round 4's checkpoint spots just past each door (HC). |
| 4 | Relic chamber | Set in HZ-6, high above the exit ledge | About 24 × 24, 12 m ceiling | HZ | The prototype's relic chamber. Every second path ends here. Round 5's checkpoint (HC). The relic on its pedestal inside the cage, and the levers around it (PG; the relic is HC's). Ghost spawn points (PG). The escape tunnel out to a ledge, where the zipline starts (PG) and the walkway begins (HZ). Round 6's checkpoint at the cage (HC). |
| 5 | Exit ledge | 180, 0 | 10 × 16, open to a chasm 20 m deep | HZ | The zipline from the relic chamber's ledge lands here (PG-7). The walkway down from the relic chamber's ledge is the route if the zipline isn't in (HZ). A fall volume under the chasm kills fallers through `Apply Damage` (HZ). |
| 6 | Haunted hall | 145, 0 | 60 × 16, 10 m ceiling, dark | HZ | The old Round 3 hall, crossed from east to west. Traps between X 130 and 165: swinging logs at X 140 and 155, spikes at X 148 and darts at X 160 (HZ). Chase ghost spawn points at (150, ±6) (PG). |
| 7 | Altar cavern | 100, 0 | 30 × 24, 12 m ceiling | HZ | Empty now: the altar moved to the first room. Gate G3 in the east wall at (115, 0), shut until the escape (HC). Chase ghost spawn points at (100, ±9) (PG). |
| 8 | Trap corridor | From (55, 0) to (85, 0) | 4 m wide, 4 m ceiling | HZ | Crossed from east to west. Darts at X 62, the swinging log at X 72 and spikes at X 80, timed so the relic's carrier, at half speed, gets through by watching the rhythm (HZ). The old key relic nook to the north is closed off. |
| 9 | Plate hall | 40, 0 | 30 × 30, 10 m ceiling | HZ | Empty now: the plates moved to the first room. Gate G2 in the east wall at (55, 0), shut until the escape (HC). Chase ghost spawn points at (40, ±12) (PG). |
| 10 | Passage | From (15, 0) to (25, 0) | 4 m wide | HZ | The spike trap at X 20 (HZ-2): the first trap players meet, and the last one before home. Gate G1 at (25, 0), shut until the escape (HC). |

## Moving through the maze

HZ builds every obstacle to one of these categories, so each one is clearly possible or clearly impossible. PG-7 tunes the moves so the categories hold and records the measured values here.

| Obstacle | Size | How a player gets past |
| --- | --- | --- |
| Step | Up to 45 cm | Walks over it |
| Low ledge | Up to 1 m | Jumps up onto it |
| High ledge | 1 to 2 m | Jumps at it and climbs up |
| Climbing wall, rope or vines | Any height | Climbs it. Marked with rope wraps or handholds in torch amber, so it reads at half-screen size. |
| Wall | Over 2.2 m, unmarked | Can't get past |
| Short gap | 1.5 to 2.5 m | Jumps across from a walk |
| Long gap | 3 to 4 m | Jumps across from a sprint, with at least 6 m of run-up |
| Pit under a gap | Any | Missing a jump drops you into a pit with a climb back out, which costs time. Only chasms that look deadly have a fall volume. |

The relic's carrier moves at half speed and can't sprint or climb, so the escape route from the relic chamber to the first room has no ledges, gaps or climbing walls. Steps up to 45 cm are fine.

## Map 2: the antechamber (`L_Site02`)

| Area | Center (X, Y) | Size | Owner | What goes there |
| --- | --- | --- | --- | --- |
| Antechamber | 0, 0 | 20 × 20, 8 m ceiling | HZ | 4 player starts at X −6, Y −4 to 4 (HC, persistent level). Braziers at (±6, 8). A sealed door with hieroglyphs in the north wall at (0, 10). The results screen shows here after the mission. |

## Changing the layout

HZ owns the layout. Announce any change to a room's position, a gate or a passage at kickoff, and update these tables in the same commit.

## HZ-1 geometry delivery notes

The north passage is centred at X 3.25 m to clear the first room's timber shoring. The existing chasm walkway runs at Y -7 m, from (185, -7, 0) to (255, -7, -20). HC-INT2 incorporates these delivered geometry fixes while keeping the maze-run layout above.
