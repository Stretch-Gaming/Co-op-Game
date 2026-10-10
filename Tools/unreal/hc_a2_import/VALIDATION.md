# HC-A2 validation

The source/import/collision/assembly gates and approved HZ integration passed in the isolated Windows Unreal 5.8.3 editor. The other-platform appearance/fallback check remains pending, so #19 stays open.

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

The original `site_gate_g1.png`, `site_altar.png` and `split_screen0000*.png` record the earlier missing HZ support. They are historical failure evidence. Stretch subsequently approved HZ floor, local lighting and gate-enclosure changes; the HZ map was locked and the kickoff posted on #19 before authoring.

The current `cave_*` images and `environment_capture.json` cover the supported plate hall, altar, all three gates at Z0/Z200/Z400 and each symbol at an actual 800×450. The daylight gaps found in initial enclosure renders were sealed with alcove returns, an altar entrance bulkhead and caps meeting the ceilings. Amber lighting was reduced and teal fill strengthened. The upper leaf is enclosed through its full travel; it is never shortened or hidden. Existing prototype actors and all HC prop origins remain intact.

See `environment_authoring.json` for the exact 56 boxes and lights, `environment_verification.json` for saved-map readback, 17 floor contacts, closed/open pawn sweeps, leaf-volume clearance and both-face occlusion probes, and `environment_review.json` for the image review. The leaf-volume sweep uses a 0.5 cm offset above the resting floor to exclude floor contact while retaining full leaf dimensions and 400 cm travel.

The HZ support asset has 2,208 opaque triangles, Nanite enabled with 100% fallback triangles/zero error, 56 simple compound boxes and MI_HCA2_Stone. It is analytic team-authored geometry created through editor GeometryScripting APIs. Source art and shared materials are unchanged. This supports #19's props and a short G3 landing; it does not finish the downstream gauntlet/chasm environment visible through G3.

## Client scope

`client_checks.json` records fresh 2/3/4 Play As Client asset-presence/initial-pose checks and a listen-server check with two local controllers. Both local pawns at the plate test positions remain supported at Z92.15 cm instead of falling. The current split-screen renderer image is recorded separately from the historical falling views. These checks establish static-art loading, local views and floor support. They do not establish gameplay RPC/carry/round logic, which belongs to HC-4/5/6.

Physical gamepad routing, the regular PG camera/view behavior and a final team playtest remain outside this art automation. The other-platform appearance/fallback requirement in docs/assets.md cannot be established on this Windows host. `MAC_CHECK.md` contains the bounded teammate handoff. #19 must remain open until that result is recorded.

## Practical editor findings

- Python commandlets lack StaticMeshEditorSubsystem; use a full editor for this importer.
- UE 5.8.3's material vector setter returns false after successfully setting. The importer verifies the actual override/value.
- Automatic Nanite fallback simplification distorted fitted bounds; 100% fallback triangles/zero error preserve them.
- Generic unsaved World duplication followed by load caused a GC crash. The delivery uses LevelEditorSubsystem.new_level_from_template instead.
- The Blueprint DSL requires an explicit `(else ...)`. Both branches are independently exercised; compile success alone was not accepted as pose correctness.

The original dirty checkout, source art, Core, Player, shared materials/maps and project settings are preserved. HZ changes are limited to the explicitly approved, locked sublevel and its unique supporting mesh; original HZ actors are preserved. No hosted subagents were used. #19 must remain open until the remaining art acceptance criteria pass.

Upstream HC-1 integration: the final rebase retained its three test interactables in L_Site01_HC, then added the eleven HC-A2 actors through the editor. See evidence/upstream_integration.json. No older binary map replaced the upstream map.

Fresh continuation correction: earlier presentation evidence did not establish prototype-to-passage connectivity or correct visible-face winding. Current support has clockwise faces, 1/16 cm Nanite position precision, flat frame-side seals, overlapping room joints and balanced local lighting. Gate-side complex rays, 24 connection sweeps and four floor-following spawn routes pass. Approved doorway copies change only two original actor mesh references; their identities/transforms and source mesh assets remain intact. The legacy copied rock shell retains its original triangle-collision policy; generated support, blocker and all HC-A2 props have simple collision.

Only fresh capture/client reports and committed hashes establish the current Windows gate. Older cave_split_screen00000.png records a test-view orientation error; historical site/gallery images do not establish the repaired environment. Mac, physical controller traversal, downstream gauntlet/chasm, navmesh and consuming gameplay remain outside this automated Windows art/placement gate.
