# Rules for AI coding tools on this project

> These rules apply only inside `Prototypes/CoopCave/`, a standalone C++ prototype. Everywhere else in this repo, follow the root [AGENTS.md](../../AGENTS.md).

## The project
- Two-player co-op game (It Takes Two / Unravel style). **Two players only.** Don't add 3-4 player support.
- **Unreal Engine 5.8, C++.** Don't use APIs from other engine versions. If unsure an API exists in 5.8, say so instead of guessing.
- Target: PC first, then Xbox Series X|S and PlayStation 5. Graphics stay light and stylized.

## How the code is organized
- `Source/CoopProto/CoopGameMode.*`: session setup (spawns Player 2, start spots, the play area, spot travel; the tether only with `coop.Tether 1`)
- `Source/CoopProto/CoopCharacter.*`: player movement, camera, co-op moves (brace, reel, boost jump)
- `Source/CoopProto/CoopInput.*`: **all** controls, built in C++ with Enhanced Input
- `Source/CoopProto/CoopTether.*`: rope between players (constraint, drag, reel, respawn, visual). Off by default.
- `Source/CoopProto/CoopTuning.*`: every feel number as a live console variable (`coop.*`)
- `Source/CoopProto/CoopPlayground.*`: the play area: a self-building 25 m x 25 m torch-lit mine cave with spots to jump to, and the maze north of it (layout table `CoopMaze` at the top of the .cpp; `maze_overview.png` pictures it)
- `Source/CoopProto/CoopMeshKit.*`: faceted shapes built in code (rocks, crystals, flames) for procedural mesh components
- `Source/CoopProto/CoopTestCourse.*`: the old co-op course, parked (not spawned)

## Hard rules
1. **Gameplay logic goes in C++.** Blueprints are only for hooking up art assets and tweaking numbers. Never put logic in Blueprints.
2. **Never create or edit `.uasset` or `.umap` files.** They are binary. If something needs an asset, write the C++ and tell the human exactly what to set up in the editor.
3. **Input stays in `CoopInput.cpp`.** No Input Action or Mapping Context assets.
4. **Keep it light:** no Lumen, Nanite or virtual shadow maps unless the human asks. Settings live in `Config/DefaultEngine.ini`.
5. **Use Unreal conventions:** `A`/`U`/`F` prefixes, `TObjectPtr<>` for `UPROPERTY` object pointers, include what you use, `.generated.h` as the last include in headers.
6. **Small changes.** One feature at a time, and tell the human how to test it.

## Building
- **Mac:** close the editor → `bash build_mac.sh` → reopen. (No Live Coding on Mac.)
- **Windows:** `build_windows.bat`, or Live Coding (Ctrl+Alt+F11) for `.cpp`-only changes. Changes to a `.h` (new `UPROPERTY`, `UFUNCTION`, members, classes) need the editor closed and a full build.
- When a build fails, ask the human for the **first** error lines, not the whole log.

## Tuning values
Every feel number is a console variable in `CoopTuning.cpp` (`coop.*`), read every frame, so the human can tune live with the in-game console without rebuilding. New feel numbers go there too, never as hard-coded constants. Values the human wants to keep go in `Config/DefaultEngine.ini` under `[ConsoleVariables]`.

## The cave
- Small rocks must stay under `coop.StepHeight` (45 cm) so players walk over them; medium rocks 50-100 cm (jumpable); boulders 1.4 m and up.
- Point lights are the expensive part on a Mac in split screen. Keep shadow-casting torches to the few out in the room, and keep huge geometry (walls, ceiling, floor) from casting shadows.
- Lighting numbers are `coop.Cave.*` console variables, like every other feel number.

## Building in rounds
New mechanics get their own spot in `CoopPlayground.cpp` so they can be tested in isolation with a controller. One mechanic per round. Graybox only (engine shapes, flat colors) until the human locks the metrics; then real art.
