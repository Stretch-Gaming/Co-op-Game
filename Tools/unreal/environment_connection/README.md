# Connected room and maze

Open `/Game/Maps/L_ConnectedRoomMaze` to walk the existing cave room directly into the maze. Both environments are loaded together. The north passage is300cm wide, joins the maze fork atY3200, and never changes maps.

Start in the cave room. Walk with WASD, look with the mouse, and press E near the closed stone door to raise it. Follow the north passage into the team's maze. F5 adds a second local player; the existing arrow-key controls work for that player. This map excludes puzzle/round levels and places no puzzle actors.

The room now uses HC-owned `L_ConnectedCave`, copied from `L_Site01_HZ` through the editor. Ten legacy ghost-room actors were removed only from that copy because their walls and roof occupied the maze fork. The original HZ map is unchanged. See [the connection correction](CONNECTION_CORRECTION.md). The HC-owned `L_ConnectedMaze` contains the exported team scenery, trimmed atY3200 and shiftedX-175 to line up with the room's north passage. The existing HC stone-door artwork is copied and centered for correct interaction/collision.

Door API: `/Game/Puzzles/EnvironmentConnection/BP_EnvironmentDoor`; actor tag`ConnectionDoor`; `OpenFromPlayer(Instigator)` validates native interaction and runs on the server; replicated`Open` plus actor movement raises the panel450cm. Closed bounds center(325,1400,200), extent(150,17.5,200). It is independent of plates, rounds and puzzle state. A later adventure adapter can use this environment without adding another doorway barrier.

Editor-only assembly/verification scripts live here; runtime remains Blueprint-only. Run scripts through the guarded `playable_game/run_environment.py` wrapper. Generation order: build_meshes, build_door, assemble_map, center_door, remove_invalid_volume, quiet_preview. Committed source and maps are ready to open without regenerating.

Validation: two joining clients physically walk from room to maze and back through native movement/E input; both retain the same world/roster. Both local host players also physically crossed the doorway and fork; the host walked back. Presentation is checked separately. Initial approach positions are explicit fixtures; the passage itself is walked, not teleported.

Current scenery: the PR122 source is adopted privately under Refresh_fd40cdeb; see Tools/unreal/connection_refresh and SourceArt/HC/EnvironmentConnection/Refresh_fd40cdeb. Original source/build scripts here describe the historic PR124 geometry and refuse to overwrite the refreshed map. The door and the room are preserved; no trap placements are adopted into the walk-through preview.
