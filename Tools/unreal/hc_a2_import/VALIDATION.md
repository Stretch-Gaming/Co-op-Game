# HC-A2 validation

The source/import/collision/assembly gates passed in the isolated Windows Unreal 5.8.3 editor. The main-cave visual acceptance gate has not passed, so #19 is not complete.

## Passed

- All ten hydrated FBX SHA-256 hashes/sizes match committed LFS pointers. Direct FBX inspection agrees with validation metadata, effective cm dimensions, base-centered pivots and material slots.
- The current offline gate passed 22 safety tests, Python syntax, source/hash/metadata checks, default read-only dry run and destination isolation. Repeat dry runs report existing destinations; execution still refuses overwrites.
- Ten meshes and three M_Stylized instances were imported through FbxFactory/editor APIs. The shared parent was never modified.
- Exported normals are preserved and MikkTSpace tangents are recomputed. Full-fidelity Nanite fallbacks restore the authored bounds; five opaque meshes use Nanite and five plate parts do not.
- Simple collision is present on all meshes: six single boxes, two boxes on each statue/altar, eight split frame boxes.
- Five art Blueprints compile without warnings/errors. Both true and false pose branches are inspected, then compiled after inspection because UE 5.8.3's graph reader marks assets dirty.
- Live physics/pose tests verify all four +9/+2 cm plate endpoints and 7 cm contact-height changes, gate 0/+400 cm endpoints, closed pawn-size blocking/open passage clearance, and altar contact at Z97.
- Nine art-test placements and eleven main-map placements were saved only in HC-owned maps. The HC test map uses L_StyleTest as a template; the shared map file is unchanged.

See `evidence/editor_import.json`, `compound_collision.json`, `pose_graphs.json`, `editor_verification.json`, `nanite_fallback.json` and `tangent_finalize.json`. Historical recovery records are retained separately and are not passing-gate evidence.

## Visual review

The renderer captured six actual images; this is not a mockup. In `symbols_and_statues.png` and the actual 800×450 `symbols_half_screen.png`, the four symbols read distinctly and both owl sizes/altar retain the supplied shapes. The test lighting is deliberately strong amber with teal fill; `gate_closed.png` is overlit, so it establishes geometry rather than proving the final cave-light balance.

The main-map renders show unresolved environment integration: `site_gate_g1.png` is very dark, and `site_altar.png` shows the altar outside a usable enclosing cavern. Gate upper-space probes found no rock across sampled Z525/650/825 at G1/G2/G3. `gate_open.png` shows the leaf's full upward travel in the test gallery; that exposure is intentional for assembly review, not a claimed concealed cave gate.

Consequently, **main-cave placement, lighting and leaf concealment remain pending HZ work/review**. No HZ geometry or lighting was modified, no leaf was hidden, no travel was shortened and no asset was resized to mask the issue. The concrete gate clearance/enclosure requirements are in `enclosure_plan.json`.

## Client scope

`client_checks.json` records 2/3/4 Play As Client asset-presence and initial-pose checks plus the current split-screen result. The 2/3/4-player asset-presence/initial-pose checks and two-local-controller check passed. `split_screen00000.png` confirms two local views, but both players fall at the planned puzzle coordinates, reinforcing the main-map floor/geometry blocker. These checks establish static-art loading and local view creation, not final visual acceptance or gameplay RPC transport. Carrying, pressure-plate counting, GameMode gate/round decisions and altar relic interaction belong to HC-4/5/6 and are not implemented by art fixtures.

Physical gamepad routing, teammate Mac appearance/fallback checks and a final team playtest are not established by this Windows automation. The minimum-kit other-platform requirement in docs/assets.md remains pending.

## Practical editor findings

- Python commandlets lack StaticMeshEditorSubsystem; use a full editor for this importer.
- UE 5.8.3's material vector setter returns false after successfully setting. The importer verifies the actual override/value.
- Automatic Nanite fallback simplification distorted fitted bounds; 100% fallback triangles/zero error preserve them.
- Generic unsaved World duplication followed by load caused a GC crash. The delivery uses LevelEditorSubsystem.new_level_from_template instead.
- The Blueprint DSL requires an explicit `(else ...)`. Both branches are independently exercised; compile success alone was not accepted as pose correctness.

The original dirty checkout, source art, Core, Player, Hazards, shared materials/maps and project settings are preserved. No hosted subagents were used. #19 must remain open until the remaining art acceptance criteria pass.

Upstream HC-1 integration: the final rebase retained its three test interactables in L_Site01_HC, then added the eleven HC-A2 actors through the editor. See evidence/upstream_integration.json. No older binary map replaced the upstream map.
