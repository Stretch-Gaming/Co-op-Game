# Connected preview correction — October 11, 2026

The connected preview loaded the old HZ ghost-room blockout at the maze fork together with the exported maze. The old room's walls, roof and floor occupied Y3200–4200. The earlier client walk checks stopped at Y3600, inside that enclosure, and incorrectly described that as reaching the maze. They did not establish a clear view of the fork or its four paths.

The correction creates `/Game/Puzzles/EnvironmentConnection/L_ConnectedCave` through Unreal Editor's map save API. It removes only these ten actors from the copy:

- `HZ1_GhostRoom_Floor`, `HZ1_GhostRoom_Roof`
- `HZ1_GhostRoom_WallW`, `HZ1_GhostRoom_WallE`, `HZ1_GhostRoom_WallN`, `HZ1_GhostRoom_WallSW`, `HZ1_GhostRoom_WallSE`
- `HZ1_Crystal_GhostRoom_A`, `HZ1_Crystal_GhostRoom_B`, `HZ1_Crystal_GhostRoom_Light`

The reserved `Content/Maps/L_ConnectedRoomMaze.umap` now streams this copy and the existing `L_ConnectedMaze`. Player starts and the moving door are preserved. No maze geometry, materials, puzzle rules or gameplay Blueprints were changed. Historical assembly scripts describe the earlier composition; do not rerun them over this corrected map.

Independent saved-map reload found all 563 expected maze scenery actors and none of the ten old room actors. Native line traces across the old west/east wall positions and roof position are clear. Use `Tools/play-connected.bat` or `Tools/play-connected.command` to start in the cave room, open the stone door with E and walk into the maze. No debug spawn or teleport is part of that launcher.

The scene comes from PK's PR122 export of the team CoopCave prototype at `f883727a33344ab601b4af2eaa57f897464246f5`. Its full source hash is `fd40cdeb47f2233c31125e16a2b62636734eb543ebd4f3ff4ae63a7ca6495b2a`; its connected derivative hash is `2008b7a684ba0f82d34b97fe259c20ec7abc46e09d00ead5f9c1dd8c6fcbf0ed`.

Protected assets have identical before/after SHA-256:

| Asset | SHA-256 |
| --- | --- |
| Original `L_Site01_HZ` | `630adb8963480408229dc2f36ba635f2b2a30590dacea3b2326ee33cf84ab65a` |
| Existing `L_ConnectedMaze` | `f9783965e505168fcd94a742363014c314ca178683783220483236c937fc1aff` |
| Existing `BP_EnvironmentDoor` | `80d0f90e6c962bef4f09f6e80fe234d9666ac112cd1cbd7f152051c710e8c0b0` |

The editor save receipt and client walkthrough evidence are in [evidence/correction-2026-10-11](evidence/correction-2026-10-11/). Local diagnostics and bounded editor scripts remain under ignored `Saved/MazeConnectionAudit/`. This change corrects the connected preview; it does not change the separate six-round candidate or establish full-adventure acceptance.

The two-joining-client gate passes from the actual PlayerStarts, through owning E interaction at the door, into the fork, west to X-1246/Y3493, and back to the cave. No approach teleports were used. `evidence/correction-2026-10-11/clients.json` SHA-256 is `f92c2a03f301c5c49647daa8559d62824aa4ca723de4de63003b4411a67576a4`. The run uses injected Enhanced Input actions. No new Blueprint runtime errors or Accessed None were found in that slice. Play/performance preferences were restored and diagnostic editors closed.

The [publish checks](evidence/correction-2026-10-11/publish-checks.json) also pass: `L_Site01` with two joining clients retains its roster, health and owning movement; in the connected map, owning F5 creates a second host local alongside one joining client, both host locals retain separate owning prompts, and each walks from its normal start through the door, across the open fork and back. No approach teleports or asset saves occur in these checks. No Blueprint runtime errors or Accessed None were found. These are native Windows action tests, not physical gamepad or Mac acceptance. No gameplay Blueprints were changed by this correction.

Stretch confirmed physical WASD works from the normal starting-room spawn. The reported movement failure occurred only in the earlier debug launch that spawned directly in the maze. That diagnostic launch is not the normal playtest route. This change does not claim to repair its unconfirmed cause. Full maze traversal, presentation review, Mac/gamepad checks and team acceptance remain separate gates.
