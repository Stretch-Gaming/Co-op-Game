# Concrete UMG handoff

This is an implementation specification for a later authorized editor pass. No Widget Blueprint or Core asset is changed here. Reuse the existing HC-1 prompt/HUD creation path; the integrator must lock any Core asset before changing it.

## Owning-player root and hierarchy

Create or reuse the HUD with its actual owning PlayerController, and add it with **Add to Player Screen**. Never select a controller by index or add this HUD globally to the viewport. Each local player receives a separate instance. Enhanced Input supplies that local player's current action key; E/A in these previews are illustrative labels.

Suggested tree inside the existing HUD:

```text
PlayerCanvas [Clip to Bounds; Self Hit Test Invisible]
  RelicGroup
    RelicImage [T_HUD_RelicIcon]
    RelicTotalText
  RoundGroup
    RoundFrameImage [T_HUD_RoundBannerFrame]
    RoundLabelText
    RoundStatusText
  InteractGroup
    InteractFrameImage [T_HUD_InteractPromptFrame]
    ActionText
    TimedProgressBar
    TimedStatusText
```

Use Image brushes with Draw As Image, white tint and their original square aspect. Do not use Box/nine-slice or stretch them into rectangles. All display-only children are hit-test invisible and do not capture focus. The progress bar uses solid-color Slate brushes; it needs no texture import or material.

## Geometry and scale

`layout-spec.json` is the source of design metrics, and `dimensions.md` lists all six local viewport configurations. Values are physical pixels for offline design.

For local viewport `W,H`, use `S = clamp(min(W/1280,H/720),0.85,1.25)` and safe margin `round(24*S)`. Design widths: relic 64*S, banner 340*S, prompt 300*S. Counter/banner font 22*S, prompt 18*S, with text never smaller than 16px. Round to whole pixels.

Use the **owning player's screen widget geometry**, rather than assigning the full window dimensions to both players. Convert these physical-pixel design values to current UMG CanvasSlot units using the active viewport/DPI scale. Avoid applying project DPI scaling and this HUD scale twice. The actual UE 5.8.3 conversion is part of the deferred engine acceptance.

The relic group anchors to the local top-left safe area. The round group anchors to local top-center. The interaction group anchors to local bottom-center. Progress is below the interaction border; its status is below the progress bar. The generator records exact slot positions, element rectangles and text sizes in `geometry-and-validation.json`.

The frame PNGs contain substantial transparent vertical padding. Position the square image by its **visible artwork center**, not by the canvas center. The input source-visible rectangles at alpha > 8 are:
- Relic: (61,45)-(451,461)
- Round frame: (20,177)-(492,353)
- Interaction frame: (27,176)-(485,362)

For square display width D and intended visible center C, compute CanvasSlot top-left as `C - D * ((left+right)/1024, (top+bottom)/1024)`. Resampling can vary the edge by one pixel; generated per-case brush rectangles are the exact offline evidence. Canvas padding can extend beyond a local viewport; Clip to Bounds clips that transparent padding while the visible border remains inside the safe margin. Do not crop or overwrite the source textures.

Text uses a centered TextBlock independent of each image. Single-line text belongs within the recorded opening. Use ellipsis for long action prompts, with a minimum 16px font; never shrink arbitrarily to fit. Preview text shadows are dark blue-violet, with warm cream foreground. Cleared/failed status is conveyed by words, not color alone.

## Presentation inputs and state mapping

Team values come from the existing `BP_CoopGameState` contracts in docs/sprints.md:
- Relic total: `RelicsCollected / RelicsAvailable`.
- Round number: `RoundState.Index`, out of Demo 1's three rounds.
- Round phase: `RoundState.Phase`; bind to `OnRoundStateChanged`, and read the initial state when binding so late-created HUDs are current.

The “timed” preview is a local presentation substate during Playing; it is not a new round phase. Playing displays “ROUND N / 3” and the applicable local action prompt. Timed displays “Hold [current key] Action” and progress. Cleared displays “ROUND CLEARED” plus round number and next-chamber guidance. Failed displays “ROUND FAILED” plus round number and checkpoint guidance. Interaction/progress is collapsed for Cleared/Failed.

Use `GetInteractInfo(Instigator)` for action text, mode and hold time, with the owning pawn as instigator. Only show the prompt for a valid target that passes CanInteract. The hold presentation needs confirmed active-use start/cancel data from HC-1. Proposed presentation fields `HoldStartServerTime`, `HoldSeconds`, `bActiveUse` and cancellation are a handoff contract, not claims that these fields already exist.

After server confirmation, cosmetic progress is `clamp((ServerWorldTimeSeconds-HoldStartServerTime)/HoldSeconds,0,1)` when HoldSeconds > 0. The server alone completes timed interaction. Do not use RoundState.PhaseEndsAt as an interaction timer. Hide/reset progress on release, canceled input, invalid target, server cancellation, round transition or loss of possession. If confirmed hold timing is unavailable, do not show a misleading completion bar.

Refresh replicated relic values through the integration's existing notification path; do not invent a new gameplay authority. No extra RPC or gameplay behavior is introduced by this specification.

## Later engine acceptance

After a separate import/integration pass: verify the three textures' settings and alpha in UE 5.8.3, owning-player widget placement and local key labels, DPI at both resolutions and both split orientations, timed cancel/complete behavior as a client, phase banners and current state after creation, and client behavior with 2, 3 and 4 connected players. Check for Accessed None and duplicate HUDs. These tests remain pending.
