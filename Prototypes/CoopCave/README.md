# CoopProto: two-player co-op prototype (Unreal Engine 5.8, C++)

> **In this repo:** `Prototypes/CoopCave/` is Ak47's standalone C++ prototype of a torch-lit cave work area, for the HZ lane ([#3](https://github.com/StretchGaming/Co-op-Game/issues/3)). It is its own Unreal project (`CoopProto.uproject`). It is separate from `CoopGame.uproject`, and CoopGame doesn't load or build anything in this folder. Use it as a reference for cave layout, rock sizes and torch lighting numbers. The real cave still goes in `Content/Hazards/` and `L_Site01_HZ` as Blueprints. To try it, open a terminal in this folder, run `bash build_mac.sh`, then follow section 2 below from step 3. The `CLAUDE.md` here applies only to this folder.

A playable starting point for an It Takes Two / Unravel-style co-op game:

- **Two players on one machine, side-by-side split screen**
- **Separate controls per player:** keyboard + mouse or gamepad for Player 1, second gamepad for Player 2
- **A 25 m x 25 m torch-lit mine cave** that builds itself when you press Play: faceted rock walls, timber supports, flickering torches with shadows, a workbench, crates, a mine cart on rails, a raised scaffold and a corner of glowing crystals
- **A maze through the north wall:** four paths that cross each other on rock bridges, climb and drop, meet in two halls, and end in a relic chamber (about 205 m x 260 m)
- **Rocks in three sizes:** small ones you walk straight over, medium ones you jump onto, boulders that block the way
- **Co-op moves:** brace (plant your feet) and boost jump (jump next to your braced partner to launch high). The rope between the players is **off**; `coop.Tether 1` brings it back with reel
- **Two camera modes per player:** over-the-shoulder and first person, switched with D-pad up
- **Live tuning:** every feel number (speed, jump, step height, boost, camera) and the cave's lighting can be changed mid-game from the console

All gameplay is C++. There are no Blueprints or input assets, so an AI coding tool can read and change everything that matters.

---

## 1. One-time setup (Mac)

1. **Xcode 26.1.1.** Epic recommends 26.1.1 for UE 5.8, and **Xcode 26.4 does not work** with Unreal. Get 26.1.1 from Apple's developer downloads page (free Apple account), not the App Store, which gives you the newest version. Open it once and let it install its components.
2. **Epic Games Launcher**, then **Unreal Engine 5.8** from the Unreal Engine tab → Library.
3. **macOS Sonoma 14.5 or newer.**
4. **Controllers (optional):** pair Xbox or PlayStation 5 controllers over Bluetooth. Connect them before you press Play.

## 2. First run

1. Put the `CoopProto` folder somewhere simple, e.g. `~/Documents/Unreal/CoopProto`.
2. Build the code. Open Terminal in the folder and run:
   ```
   bash build_mac.sh
   ```
   The first build takes a few minutes. If it fails, copy the first error and paste it to Claude.
3. Double-click `CoopProto.uproject` to open the editor. If it asks which engine version to use, pick 5.8.
4. **Create the empty level (one time only):** File → New Level → **Empty Level**. Then File → Save Current Level As → make a folder `Maps` inside `Content` → name it **Playground** → Save.
5. Press **Play** (the ▶ button). Click inside the game view to capture the mouse. **fn+Shift+F1** frees the mouse on a Mac, and Esc stops.

The cave and its lights build themselves from code. The level stays empty in the editor, and that's expected.

## 3. Controls

### Windows quick start

Run `build_windows.bat`, then `run_windows.bat`. The launcher uses Unreal's built-in empty Entry map with `CoopGameMode`; the cave builds from C++ at runtime, so this path needs no project map asset. It runs in a separate game window with two local players. `UE_ROOT` can override the default engine installation path.

The game and editor target definitions under `Source/` are included for Unreal 5.8 builds. Editor builds use the installed engine's V7 build settings and 5.8 include order.

| | Player 1 keyboard | Gamepad (P1 = pad 1, P2 = pad 2) | P2 from P1's keyboard (solo testing) |
|---|---|---|---|
| Move | WASD | Left stick | Arrow keys |
| Look | Mouse | Right stick | Comma / Period (turn) |
| Jump | Space | A / Cross | / (slash) |
| Brace (hold) | Left Shift | Left trigger | Right Shift |
| Reel (only with the rope on) | R | Right trigger | Enter |
| Switch camera | V | D-pad up | C |
| Jump to a spot (cave 1-5, maze 6-9) | 1-9 | D-pad right / left | |
| Next / previous spot (10-13: the maze's co-op moments) | = / - | D-pad right / left | |
| Back to the start of this spot | press its number again | D-pad down | |

Player 1 is coral and Player 2 is teal. A braced player squashes down and goes darker. Jump right next to a braced partner to boost jump.

## 4. The cave

A 25 m x 25 m mine cave lit by torches. The spots you can jump to:

| # | Spot | What's there |
|---|---|---|
| 1 | Entrance | Start. Small rocks right ahead of each player: walk straight over them. |
| 2 | Workbench | The work area, with a standing torch. |
| 3 | Mine cart | The cart on its rails. Jump into it. |
| 4 | Scaffold | Jump onto the crate, then up onto the platform. |
| 5 | Crystals | The glowing teal corner. |
| 6 | Maze fork | Four tunnel mouths, one per path. |
| 7 | Meeting point A | The sunken hall (-3 m) where all four paths meet. |
| 8 | Meeting point B | The raised hall (+4 m), the second meeting point. |
| 9 | Relic chamber | The end of the maze (+6 m), with the gold idol on its altar. |
| 10 | Boost wall | Path 1's co-op moment, in the trench (see below). |
| 11 | Winch lift | Path 2's co-op moment, on the climb to the +10 m bridge. |
| 12 | Split tunnels | Path 3's co-op moment, just past the fork. |
| 13 | Dip gate | Path 4's co-op moment, at the bottom of the dip before the end. |

### The maze

Through the door in the cave's north wall (between the timber posts). [maze_overview.png](maze_overview.png) is a top-down map with each path's height profile.

- **Four paths** leave the fork. Each floor is tinted its path's color, and crystals in that color mark where a path leaves and enters a room.
- **They wind around each other:** six rock bridges carry one path over another without joining them.
- **They meet twice**, in a sunken hall (-3 m) and a raised hall (+4 m), where you can switch paths.
- **Climbs and drops:** ramps of up to 2 m per 5 m (about 22 degrees). Corners and bridges are flat.
- **Dressing:** rock narrows and rounds off the tunnels, the roof drops between corners, and rubble, stalagmites, puddles, old timber (path 1), crystal walls (path 3) and a caved-in stretch (path 4) line the walls, with pillars, terraces and boulders in the rooms. A 2.5 m lane down the middle of every path stays clear. `coop.Maze.Detail 0` turns it off the next time you press Play.
- Paths 1, 2 and 4 are torch-lit; path 3 is lit by teal crystals. There are 7 dead ends.
- About 60 torches light the maze. Torch and crystal lights more than 50 m from your camera switch off, fading out over the last 12.5 m (`coop.Cave.LightDistance`). The winding walls hide them out there anyway, and even the fork torch you see through the cave door stays at full brightness.

| Path | Length | Height |
|---|---|---|
| 1 Trench (orange) | 295 m | -3 to +6 m |
| 2 Switchback (yellow) | 310 m | -3 to +10 m |
| 3 Crystal run (teal) | 475 m | -3 to +10 m |
| 4 Long haul (purple) | 495 m | -3 to +6 m |

The layout is the table at the top of `CoopPlayground.cpp` (`CoopMaze`): rooms as tile rectangles, paths as waypoints with heights.

**Co-op moments.** Each path has one spot that needs both players: one braces, the other boost jumps, and then the partner follows. They're graybox (engine shapes, flat colors in the path's color, gold plates). Spots 10-13 take you to them.

- **1 Trench: Boost wall** (spot 10). A 2.5 m wall across the trench. Boost your partner over. They drop onto the 1.2 m ledge behind it, where you can see their head, and brace there. Jump against the wall and you boost off them, through the wall.
- **2 Switchback: Winch lift** (spot 11). A 2.5 m cliff in the climb to the +10 m bridge. Boost your partner up. Stand on the lift in front of the cliff; they brace on the gold plate up top and the lift carries you up. Let go of brace and it sinks again.
- **3 Crystal run: Split tunnels** (spot 12). A divider splits the tunnel in two, with a 2.5 m block in each, 4 m apart. Take one tunnel each. Brace by the divider so your partner can boost over the first block, then they brace by the divider at the second block for you. A block is too deep to boost off someone behind it, so you have to take turns.
- **4 Long haul: Dip gate** (spot 13). A gate at the bottom of the dip. Boost your partner onto the 2.5 m ledge on the left; its gold plate opens the gate. Walk through and stand on the gold plate past it, and your partner can jump down and follow. The gate never shuts on anyone.

The heights come from the default tuning, and the table `CoopMaze::Moments` explains the math. A jump lifts your feet 1.84 m (`coop.JumpVelocity` 760, `coop.Gravity` 1.6). A boost jump (`coop.Boost.Up` 1300) would lift them 5.4 m, but a corridor ceiling stops them at 3.58 m. So 2.5 m is out of reach alone and 1.1 m under a boost; the 1.2 m ledge is a plain jump. A boost needs your braced partner within 2 m across (`coop.Boost.Range`) and 1.5 m up or down. The lift and gate speeds are `coop.Maze.LiftSpeed` and `coop.Maze.GateSpeed`.

**Repo art:** the maze uses the shared style kit from the main project ([docs/art/style.md](../../docs/art/style.md)): `SM_StyleTest_Rock` with `MI_Stylized_Rock` for the walls and ceiling, and `MI_Stylized_Gold` for the idol. They're in `Content/Shared/Style/`, at the same `/Game/Shared/Style` path as in CoopGame. The Output Log line `CoopPlayground: repo rock mesh found` confirms they loaded; if that folder is missing, the maze falls back to code-built rocks.

Where they came from: migrated on Oct 10, 2026 from the main project's `Content/Shared/Style/` (main at `8bfd3c5`) with the engine's asset migration (`AssetTools.migrate_packages`, run headless against `CoopGame.uproject`). The migration brought their dependencies too: `M_Stylized`, `MI_StyleTest_Rock` and the textures `T_StyleTest_RockNoise`, `T_StyleTest_Rock_BaseColor`, `T_StyleTest_Rock_ARM` and `T_Stylized_MaskDefault`. They're PG's style kit (PG-A0, [#34](https://github.com/Stretch-Gaming/Co-op-Game/issues/34)), made in the editor for this project, so they can be published here like the rest of the repo. No third-party content or credit is involved. One change from the originals: `M_Stylized` here has **Used with Instanced Static Meshes** turned on (set through the editor's Python, then saved), because the maze draws its rocks as instanced meshes. Without it, a standalone run draws them with the default material. The main project's copy doesn't have that flag yet. If you migrate the kit again, turn it back on here.

**HC's relics and props** dress the maze too, as art only, with none of their Blueprints or puzzle logic. The gold idol (`SM_Relic_GoldIdol`) stands on `SM_Altar` in the relic chamber. The jade mask, gem scarab and stone heart sit on plinths behind it. `SM_ChamberGate_Frame` (the frame only, with no leaf, so the way stays open) marks each path's entrance to the chamber. In both halls, `SM_Statue` stands on the west wall and `SM_Statue_Small` on the east wall, each beside a wall torch so it's lit, and both between path mouths. Each one is optional: the Output Log lists `CoopPlayground: SM_... found` or `missing`, and a missing mesh falls back to the code-built shape or is left out. They're drawn without Nanite and use their own simple collision; the relics have none.

They were migrated the same way on Oct 10, 2026, from `Content/Puzzles/Art/HCA1_Relics/` and `Content/Puzzles/Art/HCA2_Props/` (meshes and their `MI_HCA1_*` and `MI_HCA2_*` instances of `M_Stylized`), into the same paths here. Credits: Stretch scripted them in Blender for this project, so they're the team's own work and need no credit line. The sources and scripts are in [SourceArt/HC/HC-A1](../../SourceArt/HC/HC-A1) ([#18](https://github.com/Stretch-Gaming/Co-op-Game/issues/18)) and [SourceArt/HC/HC-A2](../../SourceArt/HC/HC-A2) ([#19](https://github.com/Stretch-Gaming/Co-op-Game/issues/19)), with the license recorded on those issues. `SM_HCA2_CaveSupport` wasn't brought over: it's a single 104 m piece of L_Site01_HZ's floor and gate enclosures, not a support you can place on its own.

**The maze's look** follows the style sheet; the cave keeps its warm mine look. Maze walls use the style sheet's light rock grey `#7A6E68` and ceilings its lavender mid grey `#4A4652`, and each floor is tinted with its path's color. Its shadows turn from the cave's teal fill to blue-violet `#1E2433`, so teal light is left only near the crystals. The change happens in the door tunnel: the mine's last timber frame stands at the door, and over the tunnel's three tiles the rock turns from the cave's brown to the maze's greys, while the shadows cool. `coop.Maze.ShadowTint` and `coop.Maze.ShadowLift` tune the shadows live.

## 5. What to test in the cave

1. **Small rocks (12-32 cm).** Walk into one. You should step straight over it without jumping.
2. **Medium rocks (50-100 cm).** Jump onto them. Boulders (1.4 m and up) block you.
3. **The scaffold.** From spot 4: crate, then platform. Try a boost jump too.
4. **The light.** Walk past the torches: warm light, shadows from the rocks and timber, cool teal fill in the shadows, crystals glowing in the corner.
5. **Both cameras.** Press V (or D-pad up) and look around in first person.

Things to judge: Can you read where you can go? Is it too dark or too bright? Does stepping over rocks feel right?

## 6. Tuning live, without rebuilding

While playing, press **`** (the key left of 1) to open the console. Type `coop.` and press **Tab** to see every setting. Type a name and a number to change it instantly, for example:

```
coop.StepHeight 30
coop.Cave.Torch 60
coop.Cave.Ambient 1.2
coop.Cave.Exposure -0.5
coop.Cam.StartFirstPerson 1
```

Typing a name on its own shows its current value.

- **Movement:** `coop.WalkSpeed`, `coop.JumpVelocity`, `coop.Gravity`, `coop.AirControl`, `coop.StepHeight` (tallest bump you walk over, cm)
- **Boost jump:** `coop.Boost.Up/Forward/Range`
- **Maze co-op moments:** `coop.Maze.LiftSpeed` (the winch lift), `coop.Maze.GateSpeed` (the dip gate)
- **Cave lighting:** `coop.Cave.Torch` (brightness), `coop.Cave.TorchRadius`, `coop.Cave.TorchShadows` (0 none, 1 the four torches out in the room, 2 all), `coop.Cave.Flicker`, `coop.Cave.Bounce`, `coop.Cave.Crystal`, `coop.Cave.Ambient` (cool fill in the shadows), `coop.Cave.Exposure` (stops), `coop.Cave.Fog`, `coop.Cave.LightDistance` (cm; lights farther from the camera stop drawing, 0 = never)
- **Maze look:** `coop.Maze.ShadowTint` (0 = the cave's teal shadows, 1 = full blue-violet), `coop.Maze.ShadowLift` (how far the darkest shadows are lifted toward `#1E2433`)
- **Camera:** `coop.Cam.Distance/Shoulder/Height/FOV/FPFOV/StartFirstPerson`, `coop.Look.StickYaw/StickPitch/Mouse`
- **The maze:** `coop.Maze.Detail 0` turns off its dressing (rocks, rubble, timber, crystals) the next time you press Play, to compare.
- **The rope:** `coop.Tether 1` ties the players together again the next time you press Play. `coop.Rope.MaxLength/MinLength/ReelSpeed/DragSpeed/AirWeight` tune it.

**Keep a value you like:** add it to `Config/DefaultEngine.ini` under `[ConsoleVariables]` (e.g. `coop.Cave.Torch=60`), or just tell Claude the numbers.

## 7. Changing code

- `CoopPlayground.cpp`: the cave and the maze: layout, rocks, timber, torches, furniture, lighting and the spots
- `CoopMeshKit.cpp`: the faceted rock, crystal and flame shapes
- `CoopTuning.cpp`: default values for every live setting
- `CoopInput.cpp`: every key and button binding

How to apply code changes on a Mac: **close the editor, run `bash build_mac.sh`, reopen.** (On Windows, many code changes can be applied live with Ctrl+Alt+F11.)

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| "The following modules are missing or built with a different engine version" | Click **Yes** to rebuild. If that fails, run `bash build_mac.sh` and send Claude the first error. |
| Opens in the wrong engine version | Open it from the Epic Games Launcher instead: Unreal Engine → Library → launch 5.8 → Browse → pick `CoopProto.uproject`. |
| Black screen / "map not found" | You skipped step 2.4. Create and save `Content/Maps/Playground`. |
| The console doesn't open | Click into the game view first, then press ` (left of 1). |
| Only one view, no split screen | Look for errors in Window → Output Log. Player 2 is created when play starts. |
| Player 2's gamepad does nothing | Connect both controllers *before* pressing Play. The first pad goes to Player 1, the second to Player 2. |
| Mouse stuck in the game | fn+Shift+F1 on a Mac (Shift+F1 on Windows). |
| Build error about Xcode | Check you're on Xcode 26.1.1 (`xcodebuild -version` in Terminal). |
| Low frame rate | Torch shadows cost the most: `coop.Cave.TorchShadows 0`. Playing in a standalone window is faster than in the editor. |
| A code change doesn't show up after `build_mac.sh` | Make sure no CoopProto editor is open. The script builds with `-NoHotReload`, so another Unreal editor running on the same engine (such as CoopGame) no longer leaves you on a stale build. |

## 9. Mac now, Windows for consoles

You can build and play this whole prototype on your Mac. **Xbox and PlayStation development requires a Windows PC**, because the console SDKs and dev kits are Windows-only. When you get there:
- Install UE 5.8 and **Visual Studio 2022 (17.14 or later)** with the "Game development with C++" workload.
- Run `build_windows.bat`, or right-click the `.uproject` → Generate Visual Studio project files.
- The code here is the same on both. Nothing Mac-specific was used.

## 10. Files

```
CoopProto.uproject          Project file (UE 5.8, Enhanced Input, Procedural Mesh)
Content/Shared/Style/       The shared style kit, migrated from CoopGame (see "Repo art" in section 4)
Content/Puzzles/Art/        HC's relics and props, migrated from CoopGame as maze dressing (see "HC's relics and props" in section 4)
Config/DefaultEngine.ini    Split screen on (vertical), default map, game mode, light rendering settings (TAA anti-aliasing)
Config/DefaultInput.ini     Enhanced Input as default
Source/CoopProto/
  CoopGameMode.*            Spawns Player 2, start positions, the cave, spot travel (and the rope with coop.Tether 1)
  CoopCharacter.*           Movement, camera modes, brace / reel / boost, graybox body, first-person hands
  CoopInput.*               All controls, built in code
  CoopTuning.*              Live console settings (coop.*) for every feel number
  CoopTether.*              The rope: constraint, drag, reel, respawn, rope visual (off unless coop.Tether 1)
  CoopPlayground.*          The self-building 25 m cave: rocks, timber, torches, work area, lighting, spots
  CoopMeshKit.*             Faceted shapes built in code: rocks, crystals, flames
  CoopTestCourse.*          The old co-op course (parked: not spawned)
CLAUDE.md                   Rules for AI coding tools working on this project
build_mac.sh / build_windows.bat   One-command builds
```
