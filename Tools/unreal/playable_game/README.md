# HC-INT2 integration checkpoint

All collaborator deliveries available at this checkpoint are combined on `codex/one-playable-game`, including PR #90's maze detail, the later maze fixes on main, and #97, #98, #99, #100 and #118.

This is a work-in-progress checkpoint, not a completed playable acceptance gate. The new six-round maze-run plan in PR #101 changes the route and death rules. Stretch's route choice is pending before the final adventure is finished.

Verified so far:
- Game Blueprints compile with warnings treated as errors.
- Two joining players get their own input and prompts; first person is applied immediately.
- View changes, headlamps and brace input reach the server and peers.
- F5 adds a second host-screen player; shared-keyboard controls stay separate.
- The existing timed interaction path works, and the first-room plate puzzle clears through real overlaps and player inputs.
- The official ghost table's readers compile after its schema is adopted.
- All 33 delivered critters appear on the server and both clients.

Still required: finish the chosen route, apply its death/restart rules, update the baked maze from the newest source, finish presentation, and run the full 2/3/4-player and split-screen mission checks. The merged HZ cave map is adopted; trap placements in that map must be reapplied through the editor. The taking/chase WAVs are preserved as delivered source assets and are not yet imported.
