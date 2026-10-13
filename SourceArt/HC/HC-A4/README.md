# HC-A4: crystal headlamp lock — chosen source

Original source for the crystal-lock part of [#105](https://github.com/StretchGaming/Co-op-Game/issues/105), consumed by HC-9's meeting hall. This delivery does not include the brazier, maze door, pedestal or cage. Candidate A uses one broad captive crystal in a carved stone socket; candidate B's narrow cluster was rejected because it resembles HZ's ambient crystal dressing. Candidates were built outside the repository in the live Blender editor through Blender MCP.

The existing [style reference](../../PG/PG-A0/style-frames/style-reference.png) supplied the wide bevels, faceted crystal and diamond stone carving. Geometry is original scripted modeling; no third-party geometry, texture or image-to-mesh generation was used. Existing delivered flare, relic and trap art was not regenerated.

| File | Specification |
| --- | --- |
| `HC-A4_CrystalLock.blend` | Editable cleaned chosen mesh plus wireframe simple collision; isolated asset scene, Blender 5.2.2 LTS |
| `SM_CrystalLock.fbx` | 1,580 visible triangles / 808 vertices, 80 × 80 × 100 cm, centimeter metadata, +Z up, exporter forward −Y, unit scale, base-center pivot |
| `UCX_SM_CrystalLock_00` inside FBX | One closed convex tapered octagonal prism, 24 vertices / 44 triangles, enclosing the visible mesh |
| `validation.json` | Native final-FBX reimport, saved asset-scene reload, bounds/UV/manifold/volume/convexity checks |
| `SM_CrystalLock.validation.json` | Existing cleanup exporter's units, axes, pivot and triangle-budget evidence; no decimation |
| `previews/` | Off/lit cave renders, 15 m views at 1280 × 720 and 90° horizontal FOV, and four-angle sheet beside a 1.8 m scale figure |
| `build_crystal_lock.py`, `render_crystal_lock.py` | Original reproducible modeling, native FBX cleanup, validation and render code |

There are no supplied textures. Source materials are preview materials. Two stable imported material slots, in this order:

0. `M_CrystalLockStone`: opaque stone; use an `M_Stylized` instance tinted **#6B6169**, roughness 0.86 / metallic 0.
1. `M_CrystalLockCrystal`: opaque crystal and diamond inlay; use an HC material with local `Lit` parameter. Unlit: **#263644**, emission 0. Lit: palette crystal teal **#3FD0C9**, emission multiplier 0.8 in the source previews, roughness 0.32. Tune emission under the actual cave exposure; keep the hue teal.

The saved source defaults to unlit. The single opaque crystal provides a clear aiming target and lit silhouette; it is a puzzle mechanism rather than natural cave crystal dressing. Nanite is off for this 1,580-triangle source. Finite UVs are present for later texture work, but no curvature or packed-mask bake is supplied.

## Source checks

Final FBX reimport, isolated saved-blend scene reload and normal editable-mainfile reopen passed. The delivered `.blend` contains one asset scene, just the visible mesh and its UCX, with emission initially off. Dimensions are 80 × 80 × 100 cm within 0.001 cm; visible bounds are −40 / −40 / 0 to +40 / +40 / 100 cm. Unit scale, material-slot order, finite UVs, closed manifold edges, positive volume and absence of degenerate faces passed. The delivered UCX is convex and contains all visual vertices. `cleanup_export.py` kept all 1,580 triangles; no decimation or UV rebake was needed.

The lit/unlit change is visually distinct in the 15 m source renders, and the lit crystal remains visible at native 1280 × 720 size. The four-angle sheet checks the silhouette and the 1 m height beside a 1.8 m figure. These are Blender source checks. Native Unreal import and the bounded Mac replication matrix passed as recorded below. Real cave exposure, rendered 15 m and split-screen readability, Windows appearance and broader gameplay acceptance remain pending. `validation.json` is the original Blender build-time snapshot; its native-import pending markers are superseded by the separate native evidence.

## Import and replacement handoff

Import into `Content/Puzzles/Art/CrystalLock/` as `SM_CrystalLock`: static mesh, scale 1, convert scene units, supplied normals, import materials/textures off, auto-generated collision off, one convex hull per UCX on, Nanite off. Verify two material slots and one simple collision hull. UE 5.8 Interchange can discard UCX when automatic collision is off; the existing flare import uses native legacy FBX import with its console flag restored afterwards. Use that established path and verify the result.

The replacement targets are the `BP_CrystalLock` instances with **Brazier=false** and tag `HeadlampLock`, originally `Six_headlamp_locks_0` and `_1`. The parent's Oct 13 native inspection confirmed both in `/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test`: `/Engine/BasicShapes/Sphere`, actor scale **0.8 / 0.8 / 1**, centered pivot, exact world bounds 80 × 80 × 100 cm, one `DefaultMaterial` and no material overrides. An unattached StaticMeshActor root stores its actor world position in `relative_location` and its actor scale in `relative_scale3d`; those are not zero/identity local offsets. Its world origin matches the actor origin. Recheck the live instances before import; the staged importer now validates this observed alignment before any asset creation.

This source has the final world dimensions baked in. Do not multiply it by the old 0.8 X/Y scales. The saved native integration keeps the existing centered sphere root, collision and transforms, adds a unit-sized `HC_CrystalLockVisual` child with absolute scale and **local Z −50 cm**, and gives the two placed headlamp children NoCollision. The old root's rendering is hidden only on headlamp locks. The root remains the existing gameplay collider, while the new visual shares its world envelope and floor contact. This also keeps the source UCX available without altering gameplay collision.

The original `ApplyLock` toggles hidden/collision/custom-depth state. The added `RefreshCrystalLockPresentation` helper applies the replicated `Lit` value to a local dynamic material on visual slot 1, including initial BeginPlay and every `ApplyLock`/RepNotify/reset. Its entry splice preserves the original body, other graphs and server decisions. Braziers keep their current visual.

## Native integration and bounded qualification

The parent imported and saved `SM_CrystalLock`, `MI_CrystalLockStone`, `M_CrystalLockCrystal`, `BP_CrystalLock` and the HC SixRound test sublevel on October 13. Native mesh bounds are 80 × 80 × 100 cm, the imported stone/crystal slot order is stable, and one supplied UCX hull imported. The stone MI uses the existing shared `M_Stylized`; the HC crystal material supplies the local `Lit` scalar. No shared material, gameplay replication or plugin setting was changed for this asset.

A subsequent read-only inventory found the Blueprint template correctly configured but its existing placed children still holding a null mesh and default collision. The parent's bounded map-only repair bound the delivered mesh and NoCollision to exactly the two headlamp children, preserving the Blueprint, old roots/collision/world bounds and both hidden null-mesh brazier children. The fresh import recipe now explicitly binds and verifies those placed children before saving.

The native Mac matrix passed **4 checks with two joining clients** and **16 checks with four players: two host local players plus two joining clients**. Every actual owning local-player subsystem injected the production F headlamp action at each natively enabled lock. Every peer observed replicated `Lit` and its distinct local MID still bound to slot 1 with scalar `Lit=1`, then `0`; unrelated owner lamps, legacy root geometry/collision/bounds and braziers stayed unchanged. The second non-primary host local player was included. Both captured session logs had zero scanned errors; fixture poses/input were restored.

These sessions started in fresh Lobby and used the authorized server GameMode fixture chain `StartRound(1) → ClearRound() → StartRound(2) → ClearRound()` in one callback; the last clear starts Round 3. This bypasses puzzle completion for an isolated presentation test. Approach teleports and owning-controller aim are disclosed fixtures. No direct `Lit`, `LightBegin`, `ApplyLock`, GameState or phase write replaced owning F input. This does not qualify the natural arrival route, full Round 3 completion, a three-player session, physical keyboard/gamepad focus, packet emulation, Windows or native rendered 15 m/split-screen readability. The other HC-A4 props remain undelivered here.

The [durable native evidence and replay bundle](../../../Tools/unreal/playable_state/crystal_lock/README.md) contains import/repair receipts, complete peer observations, session logs, source hashes and honest executed-version limits. Its [summary](../../../Tools/unreal/playable_state/crystal_lock/evidence/summary.json) records this bounded matrix. The path-adapted portable replay is syntax checked only. A separate native two-client capture run also passed its state checks; root qualitatively saw the teal crystal under the headlamp. Its unlit screenshot captured the restored spawn pose, so it is not a valid lit/unlit comparison pair. Near-fixture background saturation, captured viewport identity, native 15 m and split-pane readability and Windows appearance remain unqualified. Large native screenshots remain external with paths/hashes in the durable preview record.

## Rebuild

Use a separate Blender process and a new, empty external staging directory:

```sh
blender -b --factory-startup --python SourceArt/HC/HC-A4/build_crystal_lock.py -- /tmp/hc-a4-rebuild --repo "$PWD"
```

On Windows, use an external staging path and pass the repository root with `--repo`. This runs only native Blender modeling, the existing `Tools/blender/cleanup_export.py` and FBX reimport. It refuses a nonempty output directory or one inside the repository. The input FBX is a staging intermediate, not part of the chosen delivery. To render previews in the live editor, first save the user's scene, switch to a dedicated external working file/`HC_A4_` scene in a separate MCP call, import the modules, then call `render_crystal_lock.main(build_module, repo_path, preview_directory)` after validation. Do not nest scene-changing operators in context overrides: that crashed the initial live export attempt. The recovered direct-FBX path succeeded.

## Source and license

Tool / plan: free local [Blender](https://www.blender.org/) **5.2.2 LTS** with bundled Python, operated through the already installed [Blender MCP](https://github.com/ahujasid/blender-mcp), protocol 13; telemetry disabled. Original PK geometry, collision, scripts and renders. No paid service, external model, sampled texture, Fab/marketplace asset, Unreal plugin or project-setting change.

Exact modeling brief:

> Crystal headlamp lock matching the existing 80 × 80 × 100 cm world envelope: one broad captive teal crystal, four chunky stone retaining teeth, a carved socket, wide chamfered base and large diamond inlay; dark and unlit until the replicated Lit state activates it. Stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures.

License: **[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)** for these original authored source assets, scripts and renders. Public repository redistribution and commercial use are allowed, with no attribution required. No `CREDITS.md` addition is needed. Blender's application license applies to the tool, not these original outputs. The parent owns posting this provenance on #105 and all commits/review/PR updates.
