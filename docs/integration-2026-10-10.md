# Collaborator integration — 2026-10-10

Stretch's integration combines pending PRs #79, #81, #83, #84, #85, #87,
#88, #89 and #90, plus the saved local altar, round-progression, gauntlet
and cancelled recovery scaffolds. The original interaction RPC probe and
collaborator maze review screenshots are preserved. Existing collaborator
commits remain in the merge ancestry.

The primary checked exact scopes, native validation records and artifact
hashes. All 76 altar, 111 gauntlet and 56 round-progression manifest entries
match their saved delivery bytes. Core and run-ending binaries match their
tested manifests. Four text-file hash differences in those published
manifests are checkout line-ending differences; their committed normalized
text is preserved. No Unreal asset was edited on disk or globally saved.

Fresh combined-project verification on Unreal 5.8.3, CL 58210709:

- All 93 Blueprint assets, including the local probe and isolated recovery
  scaffolds, compile with warnings treated as errors.
- Site 01 passes Play As Client at 2, 3 and 4 players: replicated player
  counts/colors, one carrying component per pawn, distinct owning HUDs and
  input subsystems, actual Enhanced Input movement and floor support.
- A listen host with two local players and a remote client passes the same
  ownership and movement checks. This uses native local-player creation and
  action injection; it does not establish physical gamepad routing.
- All four native smoke intervals, including PIE shutdown, have no errors,
  Blueprint Runtime Error or Accessed None. NullRHI does not validate pixels.
- The combined CoopCave prototype builds on Windows. The first build found
  a lambda parameter hiding AActor.Owner; renaming it to PathOwner fixes the
  compiler error without changing behavior. IDE hot reload was disabled for
  this isolated build so unrelated editors could remain open.
- Git LFS object and pointer checks pass. The main project remains
  Blueprint-only; the pre-existing separate prototype retains its C++ code.

Raw independent records are in the ignored Saved/Integration directory:
compile-candidate.json/log, artifact-audit.json, clients-2/3/4.json,
split-host-3.json, native-summary.json and native-candidate.log. The primary
validation editor is closed and transient play/performance settings restored.
Other editors, including their unsaved packages, were left untouched.

This merges bounded deliveries, not full-game acceptance. Recovery is an
explicitly incomplete, unreferenced scaffold preserved from a cancelled slice.
Production health/revive, cave placement and hooks for later round/gauntlet/
ending actors, actual traveled repeated runs, PG view/split-screen integration,
physical device routing and Mac/network acceptance remain open under their
existing issues. A separate stale destroyed-carryable Drop defect recorded by
the altar delivery also remains open. No incomplete gameplay issue is closed
by this integration. HZ textures and sounds are source deliveries awaiting
their documented imports. Prototype maze changes do not alter the main cave.
