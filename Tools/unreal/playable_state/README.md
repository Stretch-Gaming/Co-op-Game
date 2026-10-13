# Playable-state integration — October 13, 2026

This HC integration slice brings the delivered first-room mining into the default six-round map, repairs resource retry and held-tool validation, restores the visible owning HUD, preserves longer ghost backoff, and imports the original crystal-lock source with replicated light feedback. It leaves the character art unchanged.

Start the assembled map `/Game/Puzzles/Test/SixRound/L_SixRound_Test`. Use the team start pad, mine three hits per boulder, load the cart, push it to the track end, and hold the enabled plates. Two/three/four-player quotas are 6/7/9 rocks and active deposits/plates are 3/3/4. The old alternative statue-only solution is retired from this derivative.

| Native Mac UE5.8.3 gate | Result | Evidence and limits |
| --- | --- | --- |
| Mining room, joining 2/3/4 and four-player host split; two-player wipe/lost-rock retry | 6 cases, 143 check entries, 0 native log errors | [Mining packet](mining/README.md); owning synthetic input, approach/settling fixtures and isolated ghosts. |
| Ghost target/backoff cases | 18 cases, 47 checks, 0 native log errors | [Ghost packet](ghosts/README.md); host split covers the named subset. |
| Crystal Lit/MID presentation | 4 two-client + 16 host-split checks, 0 native log errors | [Crystal packet](crystal_lock/README.md); isolated Round 3 fixture, not natural arrival. |
| Final `L_Site01` two-client smoke after HUD repair | 5 checks, 0 native log errors | [Final HUD packet](smoke/HUD-PAINT-README.md); normal-spawn floor/movement and owning V/F/HUD data. |
| Joining 2/3/4 and both host HUD panes | Native ownership and rendered round HUD pass | [Final HUD packet](smoke/HUD-PAINT-README.md); restored 256 scale links and existing panel colors, with client and host screenshots. |
| Secondary host Q/F, death and spectator E | 5 checks, 0 native log errors | Own stock and widgets stay independent while spectating. Synthetic input and lethal damage fixture are disclosed. |

All changed gameplay and widget Blueprints compiled with warnings treated as errors. [Gameplay compile receipt](evidence/final-compile.json) and [read-only graph proof](evidence/final-graph-proof.json) bind the final Character/Ghost package fingerprints to the preserved patches; [HUD receipts](smoke/HUD-PAINT-README.md) bind the final three widgets. Historical receipts remain unchanged when later editor saves rewrote package bytes. All 55 protected package fingerprints match; the only additional scenery change is the explicitly owned HC copy’s eleven decorative cart pieces, with 1,699 other actors proved unchanged.

Exact reservations covered Core Character, Core GameMode, Player Ghost and the HZ derivative WorldRoute map. Other game asset changes are HC puzzle/art/test/UI packages. Every binary was changed through the editor; no C++, plugin, project-setting, original cave/mining Blueprint/input or persistent-map edit is included. Original [CC0 crystal source and provenance](../../../SourceArt/HC/HC-A4/README.md) are delivered.

Play preferences, screen percentage and hardware occlusion queries were [restored](evidence/restored-final.json), all PIE worlds stopped, and the external task bridge removed. The Blender scene was restored by its source worker. The temporary rendering budget does not qualify performance, audio or pixels.

The draft remains open for uninterrupted maze/climb/heavy-carrier return with live ghosts, broader death/retry rosters and phases, Results rendering/travel, interaction prompt pixels/progress, Windows, physical devices and packet testing. Larger issues stay open until those acceptance gates pass. Python geometry readbacks still diverge from positive Blueprint-internal measurements; the old zero-layout interpretation is superseded by the rendered HUD evidence. Replays are root-controlled, bounded, checkout-guarded and syntax checked; the packets distinguish exact native-tested scratch sources from path-adapted copies.
