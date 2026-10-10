# Collaborator integration — 2026-10-10

Stretch's integration combines pending PRs #79, #81, #83, #84, #85, #87,
#88, #89, #90 and #91, plus the saved local altar, round-progression, gauntlet
and cancelled recovery scaffolds. The original interaction RPC probe and
collaborator maze review screenshots are preserved. Existing collaborator
commits remain in the merge ancestry. The newly published HZ-A6 sound-import
branch is included, with its audio assets and cave ambience/torch placement.
Source-art PRs concurrently merged by their owner are reconciled without
rewriting collaborator history.

The primary checked exact scopes, native validation records and artifact
hashes. All 76 altar, 111 gauntlet and 56 round-progression manifest entries
match their saved delivery bytes. Core and run-ending binaries match their
tested manifests. Three PG follow-up tooling entries in the Core manifest
have stale text hashes; independent reads confirm the candidate is identical
to the published scripts and their source worktree. The run-ending document's
text hash differs only by checkout line endings. These historical records are
preserved with this qualification. No Unreal asset was edited on disk or
globally saved.

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
  this isolated build so unrelated editors could remain open. The newly
  published style PR's additive conflicts retain the co-op moment stations,
  mover members and logic alongside the new rock/prop/grade implementation.
  A native Windows standalone startup loads all eight HC meshes and the
  style-kit mesh/materials, creates four co-op moments and two movers, and
  builds the 496-tile/six-bridge maze plus its detail. Its startup/runtime log
  has no errors or Accessed None; this is a startup check, not a controller
  traversal or a full visual acceptance pass.
- Git LFS object and pointer checks pass. The main project remains
  Blueprint-only; the pre-existing separate prototype retains its C++ code.

Raw independent records are in the ignored Saved/Integration directory:
compile-candidate.json/log, artifact-audit.json, clients-2/3/4.json,
split-host-3.json, native-summary.json and native-candidate.log. The primary
validation editor is closed and transient play/performance settings restored.
Other editors, including their unsaved packages, were left untouched.
The passing matrix before audio import is retained in
Saved/Integration/before-sound-import. The final matrix also passes with the
imported ambience/torch placements. Prototype startup evidence is in
prototype-style-runtime.log and its successful build in windows-prototype-build.log.

This merges bounded deliveries, not full-game acceptance. Recovery is an
explicitly incomplete, unreferenced scaffold preserved from a cancelled slice.
Production health/revive, cave placement and hooks for later round/gauntlet/
ending actors, actual traveled repeated runs, PG view/split-screen integration,
physical device routing and Mac/network acceptance remain open under their
existing issues. A separate stale destroyed-carryable Drop defect recorded by
the altar delivery also remains open. No incomplete gameplay issue is closed
by this integration. HZ textures remain source deliveries awaiting their
documented imports. HZ-A6 sounds are imported and its cave loops placed;
remaining trap schedule hooks are separate. Prototype maze changes do not
alter the main cave. The audio-sublevel update changes the main-map smoke
inputs, so the native roster/ownership/movement matrix is repeated for that
final map revision; unchanged Blueprint compile inputs are not retested.
