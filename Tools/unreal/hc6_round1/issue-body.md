Bounded actor delivery for HC-6 #12 and the start-pad/gate portion of HC-5 #11, under HC epic #1. Owner: Stretch. Branch: codex/hc6-round1 from origin/main. Preserve PR #74.

- [ ] Server-only Pawn / HC_PlateWeight occupancy; replicated pressed visuals.
- [ ] GetScalingRow-driven Round 1 setup (3/2, 3/1, 4/1); configurable statue class.
- [ ] All connected players including split-screen hold start pad for 3 seconds; departure cancels.
- [ ] Gate consumes replicated round state; existing GameMode StartRound/ClearRound change phase.
- [ ] BPI_RoundReset on four actors; fixture reset validation.
- [ ] Compile and real client tests at 2/3/4 players plus split-screen; separate fixture/integrated evidence.
- [ ] Exact placement handoff and scoped PR pushed without merge.

Own only the four requested Puzzles actors, Content/Puzzles/Test/HC6/, Tools/unreal/hc6_round1/, and docs/hc6-round1-verification.md. No cave placement, carrying/statue implementation, Core/table changes, altar, revive, later rounds, or global recovery completion. Full #11/#12 remain open.
