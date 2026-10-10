# Candidate validation

This is a Blueprint-only candidate based on main `9dc0fab` (PR119, PR124 and PR125). The original HZ maps and standalone connection packages are protected. The default adventure is `/Game/Puzzles/Test/SixRound/L_SixRound_Test`; `play-connected` remains the standalone environment preview.

Verified in the Windows Unreal 5.8.3 editor:

| Check | Result |
| --- | --- |
| Owning controls and initial door, 2/3/4 joining players | Passed |
| Four players: two host locals plus two joining | Passed |
| Second-keyboard view, lamp, sprint, flare, climb and release | Passed |
| Route floor, capsule clearance and separate paths | Passed, 3,723 samples |
| Meeting lock perches and six small relic placements | Passed static traces |
| Walking 2m and sprinting 3.5m gap probes | Passed owning client input |
| 150cm mantle on a plain-floor proof map | Passed; does not certify the cave fixture or whole route |
| Downward Q at -60/-90, exact stock ownership, burn and cleanup | Passed; active near 20 seconds, actors/lights removed by 21 seconds |
| Continuous cage hold, range cancellation, pickup and latch | Passed, two joining clients |
| Two puzzle transaction runs, results and host R restart | Passed, host plus one joining client, 17 checks |
| Launchers | Passed 15 Windows checks and 19 Mac-script checks under Git Bash |
| Final saved-asset audit | Passed 306 candidate assets and 46 changed Blueprint/widget compiles; no graph policy violations |

The two-run test uses disclosed approach positions, damage/physics fixtures and separation of chase ghosts. It proves puzzle transactions, recovery and travel, not a continuous walk through the adventure. No Blueprint runtime errors were found in that slice. Two relative-movement-base network warnings near the brazier approach remain recorded for review.

Team testing is deferred at Stretch's request: actual Macs and gamepads, complete route/trap timing and carrier/zipline traversal, 3/4-player and split-screen complete runs, all-round recovery/disconnect coverage, network emulation, and visual/audio review. Windows editor checks used D3D11 after a device reset.

Evidence hashes:

| Report | SHA-256 |
| --- | --- |
| Host/client two-run transactions | `3f9d27383e7b3a840721d7fe8dfbe21b4a24838089ced1ee35adfedb84cf9d31` |
| Route clearance | `cb62bb08b4e5fd18ed53b9d3fa94cd50dba7310b162cb193cd57f550b5bb7102` |
| Downward flare/burn/cleanup | `5c70267563a3dad08cd41dc0f64179d4551c50ad681bfa9933eed803c4498e57` |
| Continuous cage | `f96075bb063c063cb85c26bef9b6e43bd7b25f1bde77d25beaae6b772162a417` |

Five unused, untracked duplicate SoundWaves under `Content/Player/Audio/` remain only in the local worktree because editor deletion reported success without removing their files. They are excluded from staging/publication. Gameplay references the published `Content/Player/Art/Audio/` assets.

Issue #93 remains open for the deferred acceptance checks. All 46 changed Blueprint/widget assets compiled with warnings treated as errors; saved graph checks found no prohibited player-index-zero calls or global viewport HUD additions. Protected source hashes remained unchanged.
