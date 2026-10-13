# HUD geometry readback correction

**All 14 same-widget measurements are positive inside Blueprint and zero through
the Python FGeometry roundtrip. The earlier zero-layout interpretation is
refuted. The existing round HUD is still visibly absent in the parent's native
client window.** [Compact results](evidence/hud-geometry-boundary-summary.json)
and [exact paired native report](evidence/internal-widget-geometry-v3-measure.json)
retain that distinction.

The parent created one instance of the existing Vehicle template widget with
its actual joining controller and `AddToPlayerScreen(0)`. Its nine-widget Overlay
designer tree contains visible Gear/Speed/unit text; the parent selected the
owning Client 1 window and saw `5`, `99` and `Km/h` over the cave. The round HUD
was absent. [Capture metadata](evidence/designer-control-capture-metadata.json)
binds the external native Slate screenshot to SHA-256
`11409412e75c6b162c7e61c8087a1f07c86c878d2ca66d93c296dbd52735e395`.
The PNG is intentionally not copied into this repository. Its recorded owner
is 290 in the initial control session; the later paired measurement uses a fresh
control with owners 292/293. These are separate native sessions. The visible
control proves that the owning player layer can render native designer content.

A four-node function in one unsaved `/Temp/CoopAudit` ActorComponent Blueprint
takes the exact Widget reference, connects `GetCachedGeometry` directly to
`Slate GetLocalSize`, and returns only a reflected Vector2D to Python. It runs
on the CDO; no actor or component is placed or attached. The paired control,
its nine native descendants, both owners' HUDs and both prompts all return
positive internal bounds while the same objects return `[0, 0]` through Python.

| Object | Blueprint internal cached size | Python roundtrip |
| --- | --- | --- |
| Owning control | 1732.862 × 1080.016 | 0 × 0 |
| HUD owner 292 | 1732.862 × 1080.016 | 0 × 0 |
| HUD owner 293 | 1383.784 × 1081.081 | 0 × 0 |
| Prompt owner 292 | 332.468 × 171.271 | 0 × 0 |
| Prompt owner 293 | 713.513 × 367.568 | 0 × 0 |

These are cached widget bounds, not an assertion that each widget drew visible
pixels. Global `ViewportSlotContainer` geometry does not establish an owning
player layer's geometry. No inference from global host zero is needed here.
The all-zero Python gates in earlier ownership, viewport and reattachment
receipts remain actual recorded results, but their zero-layout/attachment
interpretation must not be used as gameplay acceptance evidence.

## Failed attempts and exact sources

The [v1 build](evidence/internal-widget-geometry-build.json) stopped at the
ambiguous `GetLocalSize` catalog leaf after creating the temporary package and
two terminators. [V2](evidence/internal-widget-geometry-v2-build.json) reused that
same package and stopped at a protected `ParentClass` read before adding the
measurement nodes. [V3](evidence/internal-widget-geometry-v3-build.json) uses the
public `BP.get_parent`, exact `Widget|GetCachedGeometry` and
`UserInterface|Geometry|GetLocalSize` catalog IDs, and the original two-terminator
preflight. The strict compile helper returned successfully; the raw build's
later `BS_DIRTY` status after graph readback is preserved. The compiled CDO then
successfully produced all 14 paired results. No Blueprint was saved.

Exact parent-executed scripts are archived under `executed/`, including all
three build versions and the owning-control helper. They preserve the original
fixed-primary, editor-PID and failed-receipt guards. They are historical source
evidence, not portable reproductions. No historical helper or raw receipt was
modified, and original Windows builders and guards remain intact.

## Evidence and limits

The [native designer inventory](evidence/designer-control-inventory.json) shows
that the actual HUD/Results assets each have a CanvasPanel root and the prompt
has a VerticalBox root. Those designer trees are empty; they are not rootless.
The [Vehicle event graph](evidence/designer-control-vehicle-graphs.json) uses only
PreConstruct unit text and explicit custom speed/gear text updates, with no
pawn/vehicle/controller lookup during creation.

`Geometry.h` explicitly declares
`template <> struct TIsPODType<FGeometry> { enum { Value = true }; };`.
The earlier custom-constructor/nonPOD inference is therefore refuted.
`CopyScriptStruct` has a POD memcpy path, so source does not prove a copy bug.
The runtime comparison demonstrates a measurement-boundary divergence without
identifying its mechanism. No geometry-copy, scale, paint-dispatch or startup
race patch is justified by this evidence alone.

Both exact owning controls were removed after observation. The parent finalized
[the internal session scan and cleanup](evidence/internal-geometry-owner-summary.json):
zero native log errors, exact-control cleanup passed. The initial control's
39,771-byte [log](evidence/designer-control-log.txt) also has zero errors in the
parent's finalized scan; the 35,793-byte [internal interval](evidence/internal-widget-geometry-log.txt)
is separately hash bound. Six exact production/template saved asset hashes
remained unchanged. The parent owns disposal of the unsaved diagnostic package
and any subsequent HUD diagnosis/publication.

This probe used two real joining clients on `L_SixRound_Test`. It does not replace
the final `L_Site01` smoke, qualify four-owner rendered HUD behavior, or establish
a continuous mission completion. HUD pixel acceptance remains open.
