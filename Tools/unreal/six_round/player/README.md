# PG six-round authoring slice

These are editor authoring scripts, not evidence that gameplay works. Run only through the primary six-round editor queue, serially, after reviewing generated DSL and acquiring the listed existing-asset locks. No worker editor calls occurred.

Order: `stage0.py` across lanes first; add interfaces below through Class Settings; primary Core contracts; `traversal.py`, `tools.py`, `relic_cage.py`, `taking.py`, `chase.py`, `spectator.py`, `audio.py`; root input/component integration; placement; compile and saved-asset audit; PIE gates.

Writes:

| Script | Assets |
| --- | --- |
| stage0 | /Game/Player/AC_Traversal; /Game/Player/Tools/{AC_Tools,BP_Flare,BPI_Lightable}; /Game/Player/Taking/BP_TakingDirector; /Game/Player/Ghosts/BP_ChaseDirector; /Game/Player/RelicChamber/{BP_Lever,BP_RelicCage}; existing /Game/Player/AC_PlayerView |
| traversal | AC_Traversal |
| tools | AC_Tools, BP_Flare, AC_PlayerView |
| relic_cage | BP_Lever, BP_RelicCage |
| taking | BP_TakingDirector |
| chase | BP_ChaseDirector; existing /Game/Player/Ghosts/BP_Ghost |
| spectator | existing AC_PlayerView |
| audio | BP_TakingDirector, BP_ChaseDirector; /Game/Player/Audio/SFX_Taking_HandDrag, SFX_Taking_FloorCrack, SFX_Taking_FloorShut, SFX_Taking_LightsOut, SFX_Taking_HeadlampRoll, SFX_Taking_Sting_2D, SFX_Taker_Breath_Loop, SFX_Chase_Loop_2D, SFX_Chase_Build_Loop_2D |

New actor interface requirements: BP_RelicCage, BP_TakingDirector, BP_ChaseDirector implement /Game/Core/BPI_RoundReset. New lever duplicates old /Game/Player/Round3/BP_Lever, retaining BPI_Interactable/BPI_RoundReset: root must audit old EventGraph wiring and remove old handlers before installing the two adapters, so they cannot run old gauntlet logic. HC's BP_CrystalLock implements new BPI_Lightable. LightBegin/LightEnd take `Source: Actor`. FlareLock tags identify brazier locks; headlamp locks need beam-source filtering in HC, braziers need flare-source filtering.

Core hooks: Character `GetCarryingRelic()->Carrying bool`, `SetTakingProtected(Protected bool)` server-only; Health `IsDead()->Dead bool`, damage ignores protected victims. Root adds replicated AC_Traversal/AC_Tools components. Owning RPC handlers call SprintOnServer/StopSprintOnServer (hold/release), ClimbOnServer/StopClimbOnServer (climb/release or jump), ThrowFlareOnServer (press). Interact while own health is dead calls own view CycleSpectator locally. Do not invoke gameplay interact for a dead pawn. Tools RestockFlares is server-only and called at each regroup/restart. Cage IsRaised returns `Raised:bool`; KeyRelic first pickup calls cage LatchOpen before clearing Round5. No PG function writes round phases.

Stage1 assumptions requiring primary editor review: generated node labels for MovementMode, AddMovementInput, ProjectileMovement and SetManualCameraFade; interface-message declaring class must be BPI_Lightable. Stage0's projectile UpdatedComponent needs the colliding flare mesh as root or explicitly set updated component; editor audit must confirm an arc and collision. Component references created by the helper must appear in generated variable getters. Existing lever interface event outputs are Instigator; adapters deliberately match that name.

Scaling schema fallback: every PG count queries official GameState.GetScalingRow. Until root expands S_GhostScaling, validated named row equivalents are flare allowance 3/2/2; burn20 seconds; lever1/1/2; chase2/3/4 every20 seconds. Unknown scaling row fails closed: flare allowance0, cage requires999 levers, chase wave0. Replace equivalents with table fields once schema is expanded; do not silently fork the official struct.

Implemented traversal now includes server front/top/capsule-clearance checks and a swept0.5s vertical-first pull-up at100..200cm; root must validate native node IDs/pins and add the MantleOnServer jump RPC hook. SetClimbForwardOnServer(Forward float) supports volume entry/hold/release/backward input; root must forward the owning movement axis. Known unfinished work: separate hand/floor/light-cut scare art; flare mesh root check; separate cave-being presentation; chase-wave lifetime cap; peer replicated camera/visual timing under latency; HUD primary integration. Taking server protection and one-shot teleport schedule are staged; polished victim/peer visuals and client latency gate remain. audio.py stages imports from the repository's existing CC0 PG-A3 files and initial taking/chase playback hooks; no audio was downloaded or imported by this worker, and the source README requests a human listen pass. Sting/breath/build-layer hooks remain for the presentation pass.

Offline evidence: `validate_staged.py` executes script construction against a stub authoring API, captures87 graphs into `generated-dsl.json`, checks Python syntax, Epic native DSL parsing, balanced delimiters, terminal multi-exec statement flow and banned gameplay shortcuts, and records file SHA256 in `staged-validation.json`. It cannot validate Unreal node IDs, pins or gameplay. Native parser code is unchanged; only annotation node types are stubbed for importing outside Unreal. This is still not transpiler validity. audit_runtime.py checks settled death/carry/protection movement restrictions, living spectator ownership, regroup camera restore and continuous cage leases at each root-controlled checkpoint. It performs no game-state mutation and only reports passed after real assertions succeed.

Required PIE gates at player counts2/3/4 plus host split: owning sprint/flare input replicated without affecting another local player; heavy carrier cannot sprint/climb/flare and keeps headlamp; hold/release both lever counts with death/range/disconnect cancellation; protected taking N-1 actual ColorSlots and remaining mouth, no replay on round2 restart; headlamp target enter/leave, multiple sources, flare expiry; dead spectator living cycle per local view/regroup restore; round6 carrier-priority chase, flare safe zone and all cleanup at fail/complete. Run client-input script for initial controls evidence, then route fixtures and human view checks. Scripts alone do not pass these gates.
