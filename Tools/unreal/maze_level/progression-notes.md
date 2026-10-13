# HC maze progression stage

`progression.py` authors five HC Blueprints only. The primary runs it in stopped
Unreal and independently inspects/validates the result. It performs no actor
placement, level save, Core edit, player edit, project-setting edit or GUI action.

Rounds stay mining, taking/first traversal, two meetup puzzles, third traversal,
cage, and maze return. Round 3 has Hall A puzzle, travel, Hall B puzzle, complete.
Only the GameMode changes phase. Hall A opens its exits without clearing R3;
Hall B arrival requires every living possessed roster member, revives/restocks
through the existing director, and advances the same round to its second puzzle.
Only Hall B success permits the inherited R3 clear. Existing native retry still
owns the three-second hold, recovery, interface reset and attempt increment.

Place the unique RoundIndex=3 `BP_MazeCheckpoint` at (-175,9250,-300), unit scale,
zero rotation. Configure inherited Spot0..3 for Hall A. HallBSpot0..3 are offsets
to (-175,15500,400), plus the usual four ColorSlot offsets and 100cm spawn height.
The Hall B latch switches its spawn transforms before RegroupRoster(3). A retry
preserves cleared Hall A; it resumes travel at A or the puzzle at B as appropriate.
Keep exactly one RoundDirector and one checkpoint per index. Move checkpoint4 to
Hall B/third-segment starts; keep checkpoint5/6 near the relic. The composition
audit must accept checkpoint children instead of exact class equality.

Tag each lock `Maze.HallA` or `Maze.HallB`; retain FlareLock/HeadlampLock and unique
LockSlot values per type/hall. Enabled counts must match the existing row: one/two
headlamps and one/two braziers at 2/3/4 players. Team doors use HallNumber 0 for A,
1 for B, retain existing door components, and need blockers on every hall exit.
The HallB arrival child inherits the regroup timer; configure its overlap box
inside the restored hall. Resource monitoring skips travel and counts active
flares only within 180cm of an active hall brazier. Mining invokes the complete
inherited monitor and keeps the existing mining retry/reset hook.

The optional return bridge is a replicated StaticMeshActor with Open=false until
R6. The primary configures mesh/collision and places it only across a maze gap.
It is not an external return route. R6 opens hall doors, resets existing mouth
seals, preserves missing-key recreation/home caching and widens lost-key bounds
to the original maze. Bounds are conservative; actual floor reachability and
heavy-carrier traversal remain native acceptance checks.

Native AddFunctionOverride automatically emits its parent-call node even though
that action is absent from the palette (primary's parent-api.json). The stage
preserves this existing node and all its data input links, rewiring only exec.
StartRound runs preparation, native parent, then mouth-seal opening. ClearRound
runs an allow predicate then the native parent only on true. MonitorSixResources
runs the R3 helper on true and native parent on false. No mining or retry graph
is reconstructed from decompiler text. The receipt records preserved node paths,
types and before/after data-input links, plus parent graph fingerprints. Already
authored override graphs block a rerun for primary inspection.

Native checks still pending: compile/save/readback, exact parent dispatch,
wrong-hall/early-clear denial, all living Hall B arrival, dead revival, one retry
before/after B, mining regression, 2/3/4 joining and host split, source-state
replication, results/restart, lost-key recovery and continuous maze return.
The owning HUD currently hardcodes R3 text; primary must make its instruction
read the existing replicated AdventureInstruction to expose the hall stages.
