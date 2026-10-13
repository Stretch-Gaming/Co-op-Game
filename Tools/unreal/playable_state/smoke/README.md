# Portable map smoke and owning HUD evidence

The **final current-Character `L_Site01` two-client input/data smoke passed
natively: five checks, zero native log errors**. The [final receipt](evidence/site01-client2-final.json),
[exact native report](evidence/site01-client2-final-native.json) and [native log](evidence/site01-client2-final-log.txt)
are separate from the unchanged [earlier snapshot](evidence/site01-client2.json)
and its [log](evidence/site01-client2-log.txt).

The final smoke binds `Content/Core/BP_CoopCharacter.uasset` to SHA-256
`ae350d7291dc5cc6686b5369017ddb5cd00603f8a276d3ea40d1a8eb84ff78cc`.
Two real joining owners moved 107.79 cm and 108.81 cm from normal spawns, stayed
on the floor, and independently exercised owning V/F input, replicated state
and unique active HUD/prompt data. No approach teleports or gameplay fixtures
were used. Physical devices, pixels/audio, packet emulation and the continuous
default adventure route remain unqualified.

The **four-owner host HUD paint/layout probe failed**. [Reattachment evidence](evidence/hud-reattach-final.json)
retains its false result after eight actual Slate post-tick callbacks: all
viewport/player/HUD/prompt cache, paint and tick sizes stayed zero. The same
eight widgets, owners and saved slots/style were preserved. Data preservation
was false because the two joining `DisplayTeam` labels changed `P0` to `P4`
during the normal roster/timer update. No race was repaired or established,
and no `OnPaint`/game-asset patch was applied. Tick callbacks are not inferred
paint frames; positive native paint geometry remains required.

The parent [compiled and saved six exact Blueprints](evidence/final-compile.json).
Its [read-only final graph proof](evidence/final-graph-proof.json) binds the
final package bytes to all 12 tested Ghost graphs, the patched Character
`UseAllowed` graph and 69 unchanged Character graphs; 55 protected packages
were checked. Package bytes changed during final compile/save, so historical
native patch hashes remain historical. [Restored-state evidence](evidence/restored-final.json)
records stopped PIE, original play/throttle preferences, screen percentage 0,
occlusion queries 1, all four Slate game-layer visibility CVars 1 and the
removed bridge callback. It does not qualify rendering or performance.

## Sources and limits

| File | Role |
| --- | --- |
| `context.py` | Derive this checkout's root and guard the live editor project. |
| `test_site01_smoke.py` | Portable two-client normal-spawn input/data/floor smoke. |
| `inspect_owned_hud.py` | Portable read-only owner/data and optional geometry snapshot. |
| `executed/` | Exact parent-executed scratch sources, retained with original fixed guards. |
| `source-manifest.json` | Source, documentation, dependency and evidence fingerprints. |

Both portable helpers remain **UNEXECUTED in Unreal**, with AST/hash validation
only. Native execution used the archived scratch sources. The child did not control the editor,
edit game assets, or run Git commands. Existing Windows authoring helpers and their
guards remain intact. Runtime Harness imports use the qualified
`Tools.unreal.playable_state.ghosts` namespace.

## Parent-controlled reproduction

Only the parent controls map loading, PIE lifecycle, preferences, callbacks and
native log scans. Serialize editor calls. For the required map smoke, load
`/Game/Maps/L_Site01`, choose **Play As Client**, two players and **Run Under One
Process**, and wait for possession and roster replication. Keep normal spawns.
The portable smoke accepts `ARGS = {"timeout": 35}` and writes
`Saved/PlayableState/Smoke/site01-client2-smoke.json`; archive each attempt before
another run. It drives actual owning Enhanced Input/Blueprint RPC paths.

The portable read-only HUD snapshot accepts
`ARGS = {"report_name": "hud-after", "require_geometry": True}` and writes
`Saved/PlayableState/Smoke/<report_name>.json`. Require two settled host-local
owners; a disclosed native `CreatePlayer` fixture can establish that topology,
and does not prove physical F5 or gamepad behavior. Missing/zero geometry is a
failed strict gate. Owning data alone cannot qualify the visible overlay.

The archived reattachment source is a parent-only PIE fixture with its original
exact-primary guard. It creates no widgets or players and changes only the
existing HUD/prompt attachments, restoring their complete saved viewport slots.
Its exact executed source is frozen; no portable reattachment helper was added.

## Preserved HUD investigation

The initial [HUD API failure](evidence/hud-owned-api-failure.json) used the C++
class name rather than Python `SlateLibrary`. The [corrected owner snapshot](evidence/hud-owned-geometry-failure.json)
passed four owners' data/ownership and then failed strict zero geometry. The
[first viewport diagnostic](evidence/hud-viewport-summary.json) partially
collected layout data and failed on a missing exported Python viewport class;
[loaded-class Floating v2](evidence/hud-viewport-v2-summary.json) completed
collection, retained three optional empty-schema read errors, and still found
zero geometry. Plain protected native paint flags remained unavailable.
`LocalPlayer` objects have the Engine as their outer, so v2's false outer/GI
comparisons are expected and do not prove a roster defect.

Source review establishes that rootless `SSpacer` content is wrapped in an
`SObjectWidget`, geometry getters prefer that wrapper, and Slate stores geometry
before Blueprint `OnPaint` dispatch. A missing paint override can suppress draw
calls but does not by itself explain zero whole-viewport/player/widget geometry.
The native root cause remains unresolved; no speculative graph rewrite is
included. All raw failure receipts remain unchanged, and separate native log
receipts resolve their original pending-scan flags without rewriting them.
