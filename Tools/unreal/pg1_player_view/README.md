# PG-1: first and third person

How `AC_PlayerView`, `S_GhostScaling`, `DT_GhostScaling` and `BPFL_SplitScreen` in `Content/Player/` were built, and the test that checks them. Issue [#23](https://github.com/StretchGaming/Co-op-Game/issues/23).

**Status, 2026-10-10:** only `S_GhostScaling` and `DT_GhostScaling` are committed. Stretch holds LFS locks on `Content/Player/AC_PlayerView.uasset` and `Content/Player/BPFL_SplitScreen.uasset` for HC-INT2 ([#93](https://github.com/StretchGaming/Co-op-Game/issues/93)), so PK's tested versions of those two, and the `BP_PG_TestCharacter` change that uses the component, stay on PK's Mac until the locks are sorted out. This folder records how they were built.

## What's in `Content/Player/`

- **`AC_PlayerView`**, an actor component with Component Replicates on.
  - `ViewMode` is a replicated byte with a RepNotify: 0 is first person, 1 is third person. It starts at 0, so every player starts in first person without pressing anything.
  - On BeginPlay, `FindViewParts()` finds the owner's spring arm, camera and body mesh, and remembers the spring arm's third-person length and offset. Then `ApplyViewState()` runs, and the camera snaps to the current view. The component also binds the owner's Receive Controller Changed delegate, so `ApplyViewState()` runs again on possession.
  - `ToggleView()` calls `Server_ToggleView`, a reliable Run on Server event. The owning player can call it because their character owns the component. The server flips `ViewMode`, and `OnRep_ViewMode` calls `ApplyViewState()` on every machine.
  - `ApplyViewState()` sets the view from scratch. In first person the body turns with the controller's yaw (Use Controller Rotation Yaw on, Orient Rotation to Movement off). In third person it's the template's behavior, where the body turns toward where it moves. On the owning machine, the component's tick then blends `ViewBlend` toward the new view at `BlendSpeed` (4 a second, so it takes 0.25 s). On every other machine it snaps.
  - `ApplyBlend()` moves the camera: the spring arm length runs from 0 to the third-person length, and its offset runs from `FirstPersonOffset` (eye height, 64 cm above the capsule's center) to the template's offset. Below a `ViewBlend` of `HideBodyBelow` (0.2), the body is Owner No See. The owner can't see their own body from inside the head, but everyone else still can.
- **`S_GhostScaling`** and **`DT_GhostScaling`**, with rows `2`, `3` and `4`. `GhostCount` and `LeverCount` are 1, 1 and 2, as in the epic. `GhostSpeed` 250 and `GhostDamage` 20 match `BP_Ghost`'s current numbers in every row, until PG-11 tunes them.
- **`BPFL_SplitScreen`**, a function library with `AddLocalPlayer()` and `RemoveLocalPlayer()` as empty functions, so HC-2 can wire F5 and F6 now. PG-2 fills them in.
- **`BP_PG_TestCharacter`** has a `PlayerView` component. `IA_ToggleView` (V, or a right-stick click, in `IMC_Coop`) calls `PlayerView.ToggleView()` on Started. Remove both once HC-2 puts the component on `BP_CoopCharacter`.

## Files

| File | What it is |
| --- | --- |
| `AC_PlayerView.*.dsl` | Each graph of `AC_PlayerView`, as `BlueprintTools.write_graph_dsl` takes it. `write_graph_dsl` can't make custom events or delegate bindings, so `Server_ToggleView`, its call to `FlipViewMode` and the controller-changed binding were made with `create_node` and `connect_pins`. `AC_PlayerView.EventGraph.dsl` is the graph as `read_graph_dsl` returns it, including those nodes. |
| `pie_view_test.py` | The Play As Client test. See below. |

## The test

`pie_view_test.py` loads `L_PG_Test` and starts Play As Client with `N` clients, set at the top of the file. It drives client A only through real Enhanced Input, injected into A's own input subsystem every frame: `IA_Move`, `IA_Look` and `IA_ToggleView`. Python never calls `ToggleView()` or the RPC. Each step reads every world, the server's and each client's:

1. Every pawn starts in first person: `ViewMode` 0, turning with the controller. The owner's camera is at the eyes, with the body hidden.
2. A walks forward and looks right. Every world sees A face the way A looks.
3. A presses V while walking. Every world sees A in third person and still moving. A's camera pulls back and A sees their body. The other players stay in first person, and every world agrees on A's facing.
4. A strafes in third person, and every world agrees on A's facing.
5. A presses V again. Every world sees A back in first person, facing the way A looks.

It waits in game time, not real time, and holds V for 3 frames, like a real key press. With 4 clients and a second editor open, PIE ran at about 2.5 fps on PK's M4 Pro, and a V held for a single frame was sometimes missed.

It writes its report to `/tmp/pg1/out.json`, then puts the play settings back.

## Results, 2026-10-10, PK's Mac

| Clients | Checks | V to fully third person | V to fully first person |
| --- | --- | --- | --- |
| 2 | 40 of 40 | 0.36 s | 0.37 s |
| 3 | 64 of 64 | 0.43 s | 0.49 s |
| 4 | 94 of 94 | 0.74 s | 0.83 s |

The time is the server round trip plus the 0.25 s blend, in game time, on the owning client. The 4-client times include the low frame rate. The editor log had no errors and no "Accessed None".

A bug that the first run found: the tick's "done blending" check reused the pure `FInterp To Constant` node, which ran again and stepped past the stored value. The tick switched itself off at about 0.8, short of the target. The check now reads the value the Set node stored.

Not checked yet: a person playing with a real mouse and gamepad, the look of the switch on screen, split-screen, and Windows. Run it with `py <path>` in the editor's Cmd box, as [docs/mcp.md](../../../docs/mcp.md) describes.
