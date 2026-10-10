# Site 1 layout: the cave

Every lane builds against these positions, so the puzzles, traps, ghosts and zipline line up without anyone opening someone else's sublevel. Ask your agent to build from this table.

Positions are in meters; 1 m is 100 Unreal units. X points east along the route, Y points north, and the floor is at Z = 0 unless a row says otherwise. Sizes are width (along X) by depth (along Y).

```
 [1 Spawn cavern]-[2 Passage]-G1-[3 Plate hall]-G2-[4 Trap corridor]-[5 Altar cavern]-G3-[6 Haunted gauntlet]-[7 Exit ledge]
   start pad,       spikes        Round 1           Round 2 begins      Round 2 ends          Round 3              zipline or
   daylight shaft                                   key relic nook                                                walkway down
   north passage                                    to the north                                                        |
   (first ghost)                                                                                                  [8 Map exit, 20 m below]
```

G1 to G3 are chamber gates. The start pad opens G1, and each round's gate opens when the round before it clears. Each checkpoint has four spawn spots about 1.5 m apart, so players never land on each other.

## Areas

| # | Area | Center or span (X, Y) | Size | Owner | What goes there |
| --- | --- | --- | --- | --- | --- |
| 1 | Spawn cavern | 0, 0 | 30 × 30, 12 m ceiling | HZ | 4 player starts at X −10, Y −6 to 6 (HC, persistent level). The first checkpoint, with four spawn spots, at (−8, 0) (HC). Start pad at 8, 0 (HC). A crack in the ceiling above −4, 4 lets in a shaft of daylight (HZ). Tutorial relics at (−8, 12) and (10, −12) (HC). A 3 m wide passage leaves the cavern's north wall at X 3.25, clear of the timber shoring, and runs north to a small room around (0, 35), where the first ghost waits (PG-3). |
| 2 | Passage | From (15, 0) to (25, 0) | 4 m wide | HZ | The first spike trap at X 20 (HZ-2). Gate G1 at (25, 0) (HC). |
| 3 | Plate hall: Round 1 | 40, 0 | 30 × 30, 10 m ceiling | HZ | Round start just inside, at X 27, and the round's checkpoint at (28, 0). Plates at (32, −8), (32, 8), (48, −8) and (48, 8). Statue alcoves in the north wall at X 35, 40 and 45. Gate G2 in the east wall at (55, 0), 4 m wide. All of these are HC's. Ghost spawn points at (40, ±12) (PG). |
| 4 | Trap corridor: Round 2 begins | From (55, 0) to (85, 0) | 4 m wide, 4 m ceiling | HZ | Round 2 start at X 57 and the round's checkpoint at (58, 0) (HC). Darts at X 62, the swinging log at X 72 and spikes at X 80 (HZ). The key relic nook branches north at X 70: 3 m wide, running to (70, 25), with spikes at (70, 12) (HZ). The key relic sits at (70, 25) (HC). |
| 5 | Altar cavern: Round 2 ends | 100, 0 | 30 × 24, 12 m ceiling | HZ | The altar at (108, 0) (HC). Gate G3 in the east wall at (115, 0) (HC). Ghost spawn points at (100, ±9) (PG). |
| 6 | Haunted gauntlet: Round 3 | 145, 0 | 60 × 16, 10 m ceiling, dark | HZ | Round 3 start at X 117 and the round's checkpoint at (118, 0) (HC). Levers at (120, −6), plus (120, 6) with 4 players, and the gauntlet gate at (125, 0) (PG). Traps between X 130 and 165: swinging logs at X 140 and 155, spikes at X 148 and darts at X 160 (HZ). The exit lever at (170, 6) (PG). Ghost spawn points at (150, ±6) (PG). |
| 7 | Exit ledge | 180, 0 | 10 × 16, open to a chasm 20 m deep | HZ | The zipline from (182, 0) down to the landing at (260, 0, −20) (PG-7). A 2 m walkway down the south chasm wall, Y −8 to −6, from the ledge edge at (185, −7) to the chasm floor at (255, −7, −20), as the route if the zipline isn't in (HZ). The chasm is 16 m wide, like the ledge, and its floor is at Z −20 with the map exit on it. A fall volume under the chasm sends fallers to the latest checkpoint (HZ). |
| 8 | Map exit | 260, 0, at Z −20 | 10 × 10 | HC | `BP_MapExit`: when every player is inside, the run moves to Map 2. |

## Map 2: the antechamber (`L_Site02`)

| Area | Center (X, Y) | Size | Owner | What goes there |
| --- | --- | --- | --- | --- |
| Antechamber | 0, 0 | 20 × 20, 8 m ceiling | HZ | 4 player starts at X −6, Y −4 to 4 (HC, persistent level). Braziers at (±6, 8). A sealed door with hieroglyphs in the north wall at (0, 10). |

## Changing the layout

HZ owns the layout. Announce any change to a room's position, a gate or a passage at kickoff, and update these tables in the same commit.
