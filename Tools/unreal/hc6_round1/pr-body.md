Round 1 now has server-owned plate occupancy, scalable plate/statue setup, an all-player start hold and replicated chamber gates. Pawn or server-tagged HC_PlateWeight occupants hold a plate; removing the tag while overlapping releases it. Only existing GameMode StartRound/ClearRound functions change phase.

The actors implement BPI_RoundReset and bind the shared GameState dispatcher, applying the current state immediately. Setup reads GetScalingRow and the unchanged table's 3/2, 3/1 and 4/1 configurations. Prepared prop/material references and the delivered BP_Statue are configurable defaults. Cave placement remains with the cave chat; exact transforms, tags, settings and runtime bindings are documented.

Validation: all six 2/3/4-player client and host split-screen configurations passed 25 checks each. The rendering-editor run includes a native two-view capture; the complete post-rebase regression used NullRHI after restart initialization stalls. Client movement crosses the volumes through Enhanced Input and normal movement replication. Reset checks explicitly dispatch the actor interface, without claiming global recovery. Configurable-class failure/respawn, saved Blueprint status/interfaces/replication, protected asset hashes and a fresh L_Site01 two-client baseline smoke passed. No Blueprint Runtime Error or Accessed None in the post-rebase runtime log.

Only the four actors, HC6 fixtures, bounded tooling and verification document changed. Rebased onto merged HUD #74, prop art #71 and carrying delivery; Core/HUD/carrying/art/maps/scaling-table files are unchanged by this PR. No altar, revive or additional rounds. #11/#12 remain open; actual cave integration, carrying interaction with the puzzle and global recovery acceptance remain separate.

Evidence and placement handoff: docs/hc6-round1-verification.md and Tools/unreal/hc6_round1/delivery-validation.json.

Refs #77, #12 and #11. Do not merge automatically.
