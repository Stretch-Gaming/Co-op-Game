# Final rendered owning HUD evidence

**The round HUD now visibly renders on joining clients and both host split-screen
panes. The final `L_Site01` two-client native smoke passed five checks with zero
log errors.** This [final packet](evidence/hud-paint-final-summary.json) supersedes
the earlier “HUD absent / no paint patch / root cause unresolved” descriptions in
the unchanged historical README and geometry-boundary note. Raw historical
failures remain intact; the Python geometry divergence itself remains unresolved.

The parent changed only the three existing HC `OnPaint` graphs. Integer literal
operands and roster indexes had retyped shared scale pins and dropped 256
connections, making layout multiply operands compile as zero. Float literals
and explicit integer-to-float roster geometry conversions restored all expected
scale fanouts: **HUD 165, Prompt 55, Results 48**, with no empty multiply operands.
Native strict compilation passed, function terminators stayed intact and all
other 4/2/1 graphs were preserved. [Before pins](evidence/hud-paint-before-pin-summary.json)
retain the broken scale nodes, missing consumers and hashes of other graphs;
the 2.2 MB full inventory is intentionally excluded.

A subsequent [24-literal tint patch](evidence/hud-panel-tint-repair.json) restored
the existing solid panel colors. Native `DrawBox` sends its Tint directly to
Slate, so the brush tint alone did not color these draws. No brush/font assets,
widget designer trees, owning-player logic, input or gameplay data changed.
Actual DrawTextFormatted FontSize is single-precision float; no truncation or
deprecated explicit precision-conversion node was added.

## Native and pixel acceptance

| Evidence | Recorded result |
| --- | --- |
| [Three joining owners](evidence/fixed-hud-joining-3.json) | Owners 298/299/300 have distinct HUD/prompt instances and positive Blueprint-internal HUD bounds. |
| [Four-player host split](evidence/fixed-hud-host_split-4.json) | Host primary 301 and secondary 304 plus joining owners 302/303; all four own distinct widgets. |
| [Living host screenshot](evidence/fixed-hud-host-four-dark-0.png) | Both panes show objective, relics, tools and roster; primary has 3 flares, secondary 2. |
| [Dead-secondary screenshot](evidence/fixed-hud-host-four-dead-0.png) | Secondary displays “watching P2” and its own 1 flare; primary still has 3. |
| [Secondary input test](evidence/owned-hud-secondary.json) | Five checks pass through owning Q/F/E, death, spectator cycling and blocked dead movement/Q. |
| [Final Site01 native smoke](evidence/site01-client2-smoke-hud-final-native.json) | Owners 305/306 move 118.45/110.95 cm from normal spawns with floor support and isolated V/F/HUD data; five checks, no gameplay fixtures. |
| [Separate Site01 UI snapshot](evidence/fixed-hud-site01-final-owner-summary.json) | Fresh owners 307/308 have positive internal geometry and unique owned widgets. |
| [Site01 Client 1 screenshot](evidence/fixed-hud-site01-final-0.png) | Objective, flare stock, relics and the two-person roster visibly render. |

The host split fixture uses native `CreatePlayer` for the second local owner.
The secondary test injects synthetic Enhanced Input through each actual local
player and discloses downward aim and server lethal damage fixtures. It proves
owning Blueprint/RPC behavior, not physical devices or physical F5. Its own
stock remains 1 while spectating a living target with 3; the primary camera and
all four original HUD identities stay owned.

The `L_Site01` callback completed all five checks. Its outer driver then timed
out on an **additional HUD snapshot output-name request**; the [false driver
receipt](evidence/site-smoke-hud-final-driver-timeout.json) is retained separately.
The later successful UI snapshot 307/308 is a different session and does not
rewrite that timeout. The old default two-client dark snapshot was overwritten
by a later default-name readback; it is not included or invented. Its capture
metadata remains, and the fresh Site01 UI receipt supplies final two-owner data.

All finalized [2/3/4 profile native log scans](evidence/fixed-hud-log-summary.json)
contain zero errors. Final Site01 smoke and UI logs are separately preserved;
raw pending-scan flags remain raw, with parent finalized scan results in the
compact summary. Only the living host, dead host and Site01 Client 1 PNGs are
copied: **7,392,369 bytes total**. Other 2/3/joining capture metadata is retained
without additional image copies. The child inspected these local images only;
the parent alone operated the editor and native windows.

## Sources and reproduction limits

`executed/repair_hud_paint_float.py`, its exact packet and tint patch are the
parent-executed mutation sources. `read_fixed_hud.py`, its named-output v2,
secondary-owner test and adapted final Site01 helper are archived unchanged.
Source-only analysis scripts evaluate selected pure builder AST fragments;
**the whole original Windows builder was never executed for this repair** and
its guards remain intact. Helper hashes are separate from repair receipts'
`source_sha256`, which refers to the builder source.

The float repair builder hash is `5b04f60c…`, panel-tint source `1d8d1681…`, and
final builder source `6bc10178…`. The last source-only R1 objective literal now
says MineRocks, matching already-saved native data. All three final generated
paint bodies are byte-identical to the tested panel-tint source bodies; no
additional native changes followed that source correction. Full hashes and
final widget bindings are in the [source manifest](source-manifest.json).

Continuous full-route play, Results rendering/travel, visible interaction prompt
and progress, Windows, physical keyboards/gamepads, packet emulation and
performance qualification remain pending. Play/render settings and the task bridge were [restored](evidence/restored-hud-final.json).
The editor was closed without saving inspection dirtiness and [reopened cleanly](evidence/editor-relaunch-hud-final.json):
PIE stopped, no dirty packages, no temporary diagnostic Blueprint, and the three
final widget hashes unchanged. The parent owns commits, Codex review and publication. This packet adds evidence text/scripts
and the three authorized screenshots; it makes no editor or game asset changes.
