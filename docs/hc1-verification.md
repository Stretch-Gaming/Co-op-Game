# HC-1: Interaction and round state

The main game now handles instant, timed and continuous interaction through
`BPI_Interactable`. The owning pawn proposes a target; reliable character RPCs
send press/release to the server. The server validates the target, permission,
line of sight and a 400 cm range before use. Timed uses run on the server clock.
Continuous use calls `InteractBegin` and `InteractEnd` once per lifecycle.

Active use ends on release, range/permission loss, a blocked/downed state,
round-state change, or pawn end play. There is no revive implementation in this
slice. `SetInteractionBlocked` provides a server-only hook for later systems;
the `Downed` actor tag also blocks use.

`IMC_Coop` and the mouse-look context are added per pawn on controller changes
and removed when that pawn loses control. Cleanup removes only these contexts.
The controller's template mapping setup is replaced by host debug setup.
`WBP_InteractPrompt` belongs to the owning player's screen and shows the target
prompt and a timed-hold progress bar.

## Controls

| Action | Keyboard | Gamepad |
| --- | --- | --- |
| Interact | E | A / Cross |
| Jump | Space | X / Square |
| Drop mapping, gameplay comes with carrying | G | B / Circle |
| View mapping, gameplay comes with PG integration | V | Right-stick click |
| Headlamp mapping, gameplay comes with PG integration | F | D-pad up |

Gamepad Jump moves from the template's bottom face button to the left face
button so Jump and Interact do not share a press. Movement and look retain the
template mappings.

The primary local host controller adds `IMC_Debug` once. F1 starts Round 1,
F2 clears it, F3 marks it failed, and F4 marks the map complete. At this phase,
F4 changes the phase; map travel belongs to HC-2. StartRound sets the round
index, increments the attempt when restarting the same index, and clears the
countdown. Relic counts and the other shared objects remain untouched.

## Test fixtures and evidence

`BP_TestInteractable` exposes prompt, mode, hold duration and permission. It
replicates instant/begin/end counters and active users. The dedicated
`L_HC_Test` contains four start lanes, with all three modes in each lane. The
main cave has one marker per mode in the HC sublevel, near the spawn positions.

Windows, Unreal 5.8.3:

- Two, three and four Play As Client players passed instant use, short-hold
  cancellation, full server-timed completion, continuous release, range loss,
  permission loss, round-reset cancellation and pawn-end-play cleanup. Results
  replicated to every world; successful intervals had no errors or Accessed None.
- Both local split-screen players had separate input contexts, focused targets
  and owning-player widgets, and interacted independently in the main cave.
- The downed-state flag ended continuous use without adding revive gameplay.
- All four host debug handlers changed the replicated round phase; the second
  local player could not trigger host-only debug behavior.
- The prompt was visually checked in both split views.
- Win64 Development packaging succeeded with both the main map and HC test map;
  the packaged main game loaded `BP_CoopGameMode` and Site 01 with no startup
  errors or Accessed None. Original template asset hashes were restored and
  independently verified after incidental editor resaves.

Acceptance actions use native gameplay timers. Direct calls from editor Python
force local callspace in Unreal and therefore do not exercise Blueprint RPC
transport. Do not substitute such calls for the client network test.

Authoring source: `Tools/unreal/hc1_build.py`. The four RPC event signatures and
their reliable server/owning-client flags were configured through the Blueprint
editor; the script wires their existing nodes and preserves unrelated event
chains. Main gameplay remains Blueprint-only.

Cross-machine Mac joins and physical gamepad routing still require the team
checkpoint; the Windows tests do not complete issue #58.
