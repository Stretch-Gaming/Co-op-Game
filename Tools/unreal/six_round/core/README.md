# HC six-round integration packet

These are editor authoring scripts. Shipped behavior is Blueprint gameplay. The primary runs them serially in the isolated six-round editor after reviewing the assets and acquiring the locks. The worker did not call the editor or change any binary assets.

Order: primary/player declarations → `00_contracts.py` → primary adds declared interfaces → player graphs → `10_health.py` → `20_rounds.py` → `30_puzzles.py` → `40_relic.py` → world/player placement → `50_place.py` → `60_run.py` → primary character integration → `90_character_hooks.py`. Compile/save after each stage. Do not re-run `00_contracts.py` after graph implementation: it resets declared defaults. `50_place.py` is repeatable and replaces HC route actors only.

Expected asset writes:

- Core: `BP_CoopGameMode`; character hooks in `BP_CoopCharacter` (`CreateReviveTarget`, `RefreshAdventurePlayer`, `ReceiveHealthDamage`).
- Hazards: `AC_Health`.
- Puzzles: `Rounds/BP_RoundDirector`, `BP_Carryable` (CanClaim only), `BP_KeyRelic`, `BP_Altar`, `BP_MapExit`, `BP_PressurePlate`, `BP_ChamberGate`, `Recovery/BP_HCReviveTarget`.
- New Puzzles: `BP_RegroupVolume`, `BP_CrystalLock`, `BP_MazeDoor`.
- Placement: only `Puzzles/L_Site01_HC`. Persistent levels and other lane sublevels are neither edited nor saved by core scripts.

Required UI interface additions between stages 0 and 1: CrystalLock implements Core/BPI_RoundReset and Player/Tools/BPI_Lightable; MazeDoor implements Core/BPI_RoundReset. The installed toolset cannot add interfaces; `common.interface()` records the requirement without pretending to modify the Blueprint. Stage0 RESULT lists it.

Contracts:

- GameMode is the only round writer. Index remains 1–6 in the existing S_RoundState. Round1 clear waits for the whole living team in the maze mouth; subsequent clears advance immediately. Round6 only completes after `MissionDelivered` is set by the validated altar transaction. Legacy map exit cannot finish a mission.
- Dead players remain dead until a regroup/retry. Health IsDowned is a dead-query compatibility alias; Revive is empty. Dead bodies cannot hold plates. Native input interaction/carry is denied by health and interaction guards. Damage ignores Character.GetTakenProtected.
- Three-second failures use the existing RoundDirector ScheduleRetry/RetryRound and BPI_RoundReset dispatcher. Checkpoints and regroups use ColorSlot. Regroup restores dead only, at first room/meeting/relic chamber, and restocks all tools. New mid-round players wait dead; departures trigger retry with the new scaling row.
- Player dependencies: Tools.RestockFlares; Flare.IsActive; Cage.IsRaised/LatchOpen, actor tag RelicCage. Headlamp source is Character and flare source is BP_Flare. Braziers carry FlareLock tag. No placed cross-sublevel object references.
- Geometry reads `world/positions.json`; its route heights remain a separate world-lane playability gate.

Verification files:

- `validate_syntax.py`: offline Python AST and Epic's actual S-expression parser; also rejects cast-continuation followed by unreachable siblings. `syntax-report.json` records 57 expanded graph functions, no syntax failures. This does not confirm node resolution, compile status or gameplay.
- `test_native_flow.py`: fresh Lobby PIE with 2, 3 or 4 players, every pawn having its own local PIE input owner. Starts at pad and uses owning Enhanced Input for statues/drop, flares, headlamp aim, levers, key and altar. Test approach teleports and statue physics settling are fixtures. It stops at MapComplete, before travel. Does not certify a walked route.
- `test_wipe.py`: run during Playing round2/4/6 after the taking completes. ApplyDamage fixtures cause deaths; owning movement/interact attempts verify denial. Then checks replicated death, delay, next attempt, full health, ColorSlot checkpoint and escape key/cage reset. Repeat independently for split-screen owners.

Open integration gates: editor node resolution/compile fixes; OnDied dispatcher addition and single fire; restock inside PreparePlayerForCheckpoint on retry; full route traversal and 2/3/4 network/split play; carrier death/drop/re-pickup; impossible puzzles and late join/leave; five-second results travel and host native R restart; Output Log; presentation review. The scripts and offline syntax gate are not mission-completion evidence.
