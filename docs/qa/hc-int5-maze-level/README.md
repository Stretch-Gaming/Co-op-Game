# HC-INT5 maze-level candidate

Windows Unreal 5.8.3. The default `/Game/Puzzles/Test/SixRound/L_SixRound_Test` keeps the normal mining room, then uses the actual PR122 maze and both original meetup halls. The extra outside rooms, tubes and carrier walkway are retired. Both halls gate onward travel within round 3; six rounds remain. Original teammate maps, Core/input Blueprints, flare and persistent entry map retain their saved hashes.

New finite authored variety: 36 rock/ledge/weave clusters, 31 shoulder rubble groups and four nonlethal gaps with same-path recovery. Ten 150cm ledges have native owning-input mantle/landing proof. Each colored path has additions; return additions leave 160cm of untouched floor. Geometry/source and rights are recorded in [SourceArt](../../../SourceArt/HC/MazeLevel/README.md).

| Gate | Actual result and scope |
| --- | --- |
| Changed Blueprint compile/protected assets | [Pass](final-audit.json), warnings treated as errors. Protected originals unchanged. |
| Original Site01 regression | [Pass](site01-smoke.json), Play As Client with two joining clients; both movement contexts respond and HUDs belong to their respective controllers. |
| Original first room/mining/door | [Pass](mining-runtime.json), two joining clients, 21 original native transaction checks plus natural team start/entry. |
| Hall progression | [Pass](hall-runtime.json), 2/3/4 joining clients and four-player host split; actual owning F/Q, HallA-only denial, partial HallB denial, B revive/restock, replicated instructions, R3 retries at A/B. |
| Second host owner | [Pass](hall-runtime-secondary.json), explicitly uses the secondary host controller plus a joining client for both hall puzzles. |
| Native geometry | [Pass](geometry.json), 624 route samples; no floor/capsule/gap failures. Five existing low rocks are within the character's 45cm step limit; actual carrying walk also covers them. |
| Four jumps/recovery pits and ten ledges | [Bounded passes](traversal-components.json). Initial approach fixtures, then actual owning actions. Selected successes are retained from partial harness runs; their later errors are disclosed, not relabeled whole-run passes. |
| Continuous heavy return | [Pass for the entire walk](carrier-walk-final.json): all 78 guide points, 268.54 seconds, carrying speed 165cm/s, zero pawn position setters during return. Its later altar-focus fixture failed, so that whole harness is not marked passed. |
| Drop/re-pick, delivery, results/restart | [Separate pass](delivery-final.json): lethal carrier damage/drop, joining teammate owning E re-pick, exactly one delivery, both owners reach results, host R returns both to normal lobby. Explicit approach fixtures; earlier rounds bypassed only for setup. |
| Native rendering | D3D11 inspection cameras show the restored halls and additions, no package saves. Separate from normal packaged startup and player views. |

![Restored meetup hall B](meeting_hall_B.png)
![Recoverable gap](gap_recovery.png)
![Rock ledge](rock_ledge.png)

This is a playtest candidate. Scripted network transactions and movement use owning Enhanced Input, not physical keyboards/controllers. Ghosts were isolated during focused transaction/traversal checks. Full uninterrupted mission/chase, human fairness and readability at half-screen size, physical devices and native Mac runs remain team acceptance. Teal3 recovery uses the inner stair line, 25cm inward from its center, to avoid an existing angled wall; this deserves particular attention during human playtesting.

The source receipts preserve failed early approach/aim/route-guide fixtures. The corrected carrier guide goes around existing relic-room props and follows original corridors; it does not move or replace those props. [Files and hashes](files.json) identify this published evidence. Windows package/build/startup receipts are linked separately on the PR because they are created from the clean committed candidate.

Cross-lane lease IDs: WORLD `56891949`, PG `56891950`; [kickoff](https://github.com/Stretch-Gaming/Co-op-Game/issues/93#issuecomment-6153959559). [Asset provenance and progress](https://github.com/Stretch-Gaming/Co-op-Game/issues/93#issuecomment-6155145422). Related to #93; full team acceptance remains open.
