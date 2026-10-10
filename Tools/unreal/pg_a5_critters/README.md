# PG-A5: bats and rats in the editor

Editor Python and Blueprint graphs that bring [SourceArt/PG/PG-A5](../../../SourceArt/PG/PG-A5/README.md) into the project and place it in Site 1. Run the Python files from the editor's console with `py <file>`, with `L_Site01` open. Each one writes a JSON report to `/tmp/pga5_tools/out.json`.

| File | What it does |
| --- | --- |
| `import_critters.py` | Imports the four FBXs into `/Game/Player/Art/`, makes the seven `MI_` instances of `M_Stylized`, assigns them by material slot name, and turns off collision and Nanite. Safe to rerun. |
| `create_blueprints.py` | Creates `BP_CaveBat` and `BP_CaveRat` in `/Game/Player/Critters/` with their components. It skips a Blueprint that already exists. |
| `BP_CaveBat.EventGraph.dsl`, `BP_CaveRat.EventGraph.dsl` | Each Blueprint's tick graph, written with Unreal MCP's `BlueprintTools.write_graph_dsl`. The variables they read were added with `add_variable` and made instance-editable. |
| `place_critters.py` | Sets the Blueprints' defaults and places everything in `L_Site01_PG`, then saves only that level. Safe to rerun: it replaces the actors labelled `PG_A5_*`. |

## What's placed

`place_critters.py` places 33 actors in `L_Site01_PG`, in the outliner folder `PG/Critters`. Only the gauntlet is left out, because it has no cave geometry yet.

- **22 hanging bats** (`StaticMeshActor`, `SM_Bat_Hanging`): roosts on the spawn cavern's beams, the plate hall's ceiling corners, the trap corridor before the darts, and the altar cavern's ceiling. Each is traced up to the rock or beam above it. The spawn cavern's rock ceiling hangs below its collision, so bats there go on the beams, where they show.
- **5 flying bats** (`BP_CaveBat`): two circling in the spawn cavern, one in the plate hall and two in the altar cavern. An orbit shrinks until a 30 cm sphere clears it at the top and bottom of the bat's bob.
- **6 rats** (`BP_CaveRat`): two in the spawn cavern (inside the north fence, and beside the mine rails), one along the plate hall's south wall, one in the trap corridor, and two in the altar cavern. Each track must be flat and clear, and both ends must be visible from a spot players stand in. Otherwise the track moves toward that spot.

## How they move

Both Blueprints are cosmetic. They don't replicate, and each machine animates its own copy from its own game time, so copies drift apart between machines, which nobody can see. Nothing collides with them, and they don't affect gameplay, so they don't depend on player count.

- **`BP_CaveBat`** orbits its actor's location, facing the way it flies, and bobs up and down. Its wings flap around shoulder hinges. Instance-editable: `OrbitRadius` (cm), `OrbitSpeed` (degrees a second; a negative value flies the other way), `BobHeight` (cm), `FlapSpeed` (degrees a second), `FlapAngle` and `WingLift` (degrees), and `Phase` (seconds). Tilt the actor to tilt its orbit.
- **`BP_CaveRat`** runs back and forth along its actor's X axis, `HalfLength` cm each way, and pauses at each end, where it turns around. While it runs, it hops slightly. Instance-editable: `HalfLength`, `Speed` (degrees a second of its cycle; 60 gives a run of about 1.8 s and a pause of about 1.2 s) and `Phase`.

## Checked

- Compiled with warnings as errors.
- In Simulate, the bats' heading matches their direction of travel, and the wings flap symmetrically around the shoulders.
- With Play As Client and 2 players in `L_Site01`, the server and both clients had all 33 actors moving. The session logged no errors, warnings or "Accessed None".
