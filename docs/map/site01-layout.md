# Site 1 layout

Every lane builds against these positions, so the puzzles, hazards and car line up without anyone opening someone else's sublevel. Ask your agent to build from this table.

Positions are in meters; 1 m is 100 Unreal units. X points east, Y points north, and the floor is at Z = 0. Sizes are width (along X) by depth (along Y).

```
                                                                          N
                                                                          ^
 +------------+     +----------+------------------+-------------+--------+
 | 1 Spawn    |  2  | 3        | 4 Trap corridor  | 5 Plate     | 6      |
 |   yard     |=====| Entrance |==================| hall        |#Vault  |
 |  [pad]     |walk | hall     |                  | [plates]    |        |
 +------------+     +----------+------------------+-------------+--+-----+
                                                                   | 7 Escape
                                                                   | tunnel
 [10 Extraction] <=== 9 Chase road, about 700 m west ====+---------+--+
                                                         | 8 Vehicle  |
                                                         |   yard     |
                                                         +------------+
```

## Areas

| # | Area | Center (X, Y) | Size | Owner | What goes there |
| --- | --- | --- | --- | --- | --- |
| 1 | Spawn yard | 0, 0 | 30 × 30, open sky | HZ | 4 player starts at X −10, Y −6 to 6 (HC, persistent level). Start pad at 8, 0 (HC). |
| 2 | Walkway | 20, 0 | 10 × 6, open sky | HZ | Floor connecting the spawn yard to the entrance hall's west doorway. |
| 3 | Entrance hall | 35, 0 | 20 × 24, 8 m ceiling | HZ | A 6 m doorway in the west wall and a 4 m doorway in the east wall. The first guardian's patrol loop. |
| 4 | Trap corridor | 65, 0 | 40 × 4, 4 m ceiling | HZ | Spikes at X 52. Stretch goals: darts at X 62 and a swinging log at X 74. |
| 5 | Plate hall | 100, 0 | 30 × 30, 10 m ceiling | HZ | Plates at (92, −8), (92, 8), (108, −8) and (108, 8). Statue alcoves in the north wall at X 95, 100 and 105. The vault door in the east wall at (115, 0), 6 m wide. All of these are HC's. The other guardians patrol here. |
| 6 | Vault | 125, 0 | 20 × 16 | HZ | The loot pedestal at (130, 0) and shelves for the extra loot (HC). A 4 m gap in the south wall at (125, −8), left open until the breach wall fills it in HZ-5. |
| 7 | Escape tunnel | From (125, −8) south to (125, −65) | 6 m wide | HZ | Splits around a pillar block between Y −25 and Y −45. Debris falls here. Stretch goal: collapse blockers close the west branch. |
| 8 | Vehicle yard | 125, −75 | 30 × 20, open sky | HZ for the ground, VG for everything on it | The car at (125, −75), facing west. The getaway start trigger across the yard's west edge, at X 110. |
| 9 | Chase road | From (110, −75) west to (−600, −75) | 12 m wide, about 700 m | VG | Two wide bends. The chase spline starts at the yard's east edge (X 140), where rivals spawn behind the car. A cliff or wall keeps players from cutting across on foot. |
| 10 | Extraction zone | −600, −75 | 20 × 20 | VG | A tall beacon that's visible from the road. |

## Volumes

- **Site volume** (HC, `BP_SiteVolume`): covers areas 3 to 7. Anyone inside when the collapse countdown reaches zero is crushed.
- **Nav mesh bounds** (HC, persistent level): one volume from X −20 to 160 and Y −90 to 20, from Z −5 to 15.

## Changing the layout

HZ owns the layout. Announce any change to a room's position or a doorway at kickoff, and update this table in the same commit.
