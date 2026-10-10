# Cave integration into CoopGame

The first cave room from `Prototypes/CoopCave` is baked into the main game's
`Content/Hazards/L_Site01_HZ.umap`. Open the root `CoopGame.uproject` and play
`/Game/Maps/L_Site01` to use the existing Quinn humanoids, animation Blueprint,
Enhanced Input, movement, jumping and network replication in this environment.

This transfers the environment only. The standalone prototype's placeholder
players, C++ GameMode, brace, boost, tether and camera controls remain in that
prototype. This room is an integration checkpoint, not the complete Site 01
layout or HZ-1 delivery.

## Source and assets

- Source: this repository's `Prototypes/CoopCave/Source/CoopProto/CoopPlayground.cpp`,
  from revision `074dafc`, with procedural seed 2610.
- Rights: geometry generated from the team's existing procedural source. No
  external generator, paid asset library or downloaded mesh was used.
- `cave.json` is the reproducible raw snapshot, stored with Git LFS. It contains
  287 engine-primitive instances, 17 procedural sections, five collision guards
  and 15 point lights. It contains no character or gameplay code.
- Baked meshes and materials live in `Content/Hazards/Art/CavePrototype/`.
  Engine primitives remain references to the installed engine. Opaque materials
  use the shared `M_Stylized` through HZ material instances; the glow material
  uses the exported vertex colors.
- Meshes are conventional static meshes with Nanite disabled. Collision is
  retained on walkable/blocking pieces; decorative ceiling rocks and pebbles
  remain nonblocking. Generated blocking rock meshes use triangle collision.

## Reproduce the current snapshot

1. Build the standalone prototype, then run `coop.ExportCave` in its game
   console. The exporter writes `Prototypes/CoopCave/Saved/CaveTransfer/cave.json`.
2. Copy that export to this folder. Acquire the HZ sublevel lock and coordinate
   with its owner before replacing their environment.
3. Open the root project in Unreal 5.8.3 with `-EnablePlugins=GeometryScripting`,
   load `L_Site01`, and execute `Tools/unreal/bake_cave_environment.py` in the
   editor Python console, then call its `run()` function.
4. The importer replaces only its tagged actors and the original bootstrap
   environment in the HZ sublevel. It saves the HZ sublevel and its generated
   assets explicitly. Core, PG, HC and persistent-map assets are untouched.

The importer reuses the baked mesh assets for this snapshot. When procedural
geometry changes, replace/reimport those meshes through the editor before
rebaking; existing mesh assets are not overwritten from a different snapshot.
Geometry Scripting is needed only for baking; the main game has no dependency
on it at runtime.

## Windows build and validation

The main project is Blueprint-only. Package with Unreal's BuildCookRun for
Win64 Development, using `-build -cook -map=/Game/Maps/L_Site01 -stage -pak
-package -archive` and `-AdditionalCookerOptions=-DisablePython`. Close this
project's editor before building. Generated target files stay in `Intermediate`.

Validation on Windows with Unreal 5.8.3:

- Reloaded the saved map: 329 tagged environment actors, all in HZ; the original
  four player starts and main Core Blueprints remained intact.
- Verified all 17 baked meshes against the exported triangle counts.
- Play As Client at two, three and four players: humanoid spawning, existing
  round-state contracts, replicated movement and jumping passed with no errors
  or `Accessed None` in each test interval.
- Two local players: both split-screen views rendered the cave; the second
  humanoid moved over 10 metres and jumped over 90 cm.

The packaged game also exposed a template `GameFeatureData` asset scan in
`Config/DefaultGame.ini`. Editor tools load that plugin, but its class is absent
from the main game. The scan is now editor-only to prevent a runtime startup
ensure while keeping the editor's asset-manager rule valid. No GameFeature
assets are used by this project.

Mac rendering and a cross-machine network session still need the team playtest.
