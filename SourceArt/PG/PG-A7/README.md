# PG-A7: the taker

Candidate C01 Stilt Stalker, chosen over C02 Hanging Shade and C03 Hunched Crawler. It has the clearest silhouette at 15 m from the front, the side and behind: backward-bent legs, spines on the hump, shoulders and head, one hand hanging past the knee and one reaching forward at chest height. The Hanging Shade's drooped head hid its eyes from the front, and the Crawler read as a beast rather than something that takes people. Candidates and their read tests stayed outside the repo.

| File | Triangles | Size, X × Y × Z (cm) | Material slots |
| --- | ---: | --- | --- |
| `SM_Taker.fbx` | 13,199 | 177 × 130 × 266 | 0 `MI_Taker_Body`, 1 `MI_Taker_Eyes` (200 triangles) |
| `SM_TakerArm.fbx` | 5,500 | 285 × 163 × 122 | 0 `MI_TakerArm_Body` |

Both are rigid static meshes in centimetres with Z up, and both face +X. Blender's X stays Unreal's X, and Blender's Y becomes Unreal's −Y, as with PG-6 and PG-A4. They have no collision: like `BP_Ghost`, the actor's own capsule or traces do that job.

- **Taker:** the pivot is on the floor under the middle of the feet, and it's also the lunge pivot. The feet stand flat at Z 0. The head is 266 cm up, which fits under the 3 m maze passages. The reaching hand ends 145 cm in front of the pivot.
- **Lunge:** pitch the mesh forward about its pivot while it moves forward. In Unreal, forward is negative pitch. `previews/SM_Taker_lunge.png` shows rest, −12° with +45 cm, and −24° with +95 cm. A starting timeline is 0.3 s out to −24° and +95 cm, then 0.6 s back. For a softer hinge, put the mesh under a scene component and pitch that.
- **Reaching arm:** the pivot is where the arm leaves the wall. Place it on the wall's surface with +X pointing out of the wall, at about chest height (130 cm). The root, 36 cm long, is buried behind the wall (X < 0). Five flat shadow veins spread up to 90 cm across the wall face, about 1 cm or more under its plane, so they only show where the rock bulges. They're why the mesh is 163 cm wide. The open hand faces the victim, with its fingers up and curling forward, and its fingertips reach 249 cm out. Slide it out along X from inside the wall, grab, then pull it back in. `previews/SM_TakerArm_in_wall.png` shows it from the side and from the victim's eyes.

The FBX files carry `SOCKET_` empties, which Unreal's FBX importer turns into static mesh sockets. UE 5.8.3 dropped PG-6's `UCX_` collision on import, so check that the sockets survive. If they don't, add them by hand:

| Mesh | Socket | Location in Unreal (cm) | Use |
| --- | --- | --- | --- |
| `SM_Taker` | `Eyes` | (64.0, 0.0, 232.3) | Between the eyes: an eye glow or the look-at point |
| `SM_Taker` | `ReachHand` | (109.9, 44.0, 163.5) | Palm of the reaching hand, where a lunge grabs |
| `SM_TakerArm` | `Palm` | (194.4, −3.8, 8.6) | Palm of the open hand: attach or aim the victim here |

## Materials

`textures/` holds the 1K baked base color (sRGB) and packed ORM mask (sRGB off, `TC_Masks`; red AO floored at 0.32, green roughness, blue metallic) for each mesh. The body is in the shadow family, `#161A26` at the feet to `#4A4562` at the top, with broad painted patches. Ghost white `#D6F0FF` is only on the eyes, which share the body's texture.

Suggested instances, in `Content/Player/Art/`:

| Instance | Parent | Settings |
| --- | --- | --- |
| `MI_Taker_Body` | `/Game/Shared/Style/M_Stylized` | UV mode (`UseWorldAligned` off), `BaseColorTexture` `T_Taker_BaseColor`, `MaskTexture` `T_Taker_ORM`, `Tint` white, `GradientStrength` 0 (the gradient is baked), `EdgeStrength` 0, `CavityStrength` about 0.4, `RoughnessMultiplier` 1, `MetallicMultiplier` 0 |
| `MI_TakerArm_Body` | `M_Stylized` | The same, with `T_TakerArm_BaseColor` and `T_TakerArm_ORM` |
| `MI_Taker_Eyes` | A small unlit, opaque lane master such as `M_TakerEyes` | Emissive ghost white `#D6F0FF` at about 6 to 10, enough to bloom in the dark |

Keep `EdgeStrength` at 0. The edge highlight is torch amber, the path-and-safety color, and the red channel here is plain AO, not tuned to `M_Stylized`'s edge threshold the way HZ-A1's maps are. If `M_Stylized` gets an emissive input, `MI_Taker_Eyes` can be one of its instances. Until then, giving slot 1 `MI_Taker_Body` shows the eyes in flat ghost white, but they won't glow. Nanite can be on, since both meshes are opaque and over 2k triangles. Turn it off if either one gets a translucent fade.

## Checks

- `previews/SM_Taker_read_15m.png` is the read test. It shows the taker 15 m from a player's camera, at the size of one split-screen half (640 × 360 with a 90° horizontal field of view), in a dark cave. The wall 3 m behind it has torch pools, and the player's headlamp falls short. It reads as a silhouette from the front, from 55° and from behind, with both eyes visible from the front. At that distance one pixel is about 4.7 cm, so the limbs are 14 cm or thicker to cover at least 3 pixels.
- `previews/*_preview.png` are four-angle sheets next to a 1.8 m figure.
- Both meshes are closed and manifold, with no boundary edges or loose vertices. The FBX files were reimported into a clean Blender: scale 1, centimetre units, the bounds above, the slot names above, and the sockets parented to their mesh. `metrics.json` has the counts, bounds, sockets and mesh checks.

## Rebuilding

`taker_shapes.py` has the shapes. Each body is a joint graph turned into a mesh by the skin modifier, with no branches: a second limb off a joint starts its own piece. The pieces are then subdivided, fused with a 1 cm voxel remesh, roughened a little and decimated to budget. `taker_look.py` has the preview materials and the read test. `build_taker.py` rebuilds everything here:

    blender -b --factory-startup --python SourceArt/PG/PG-A7/build_taker.py -- SourceArt/PG/PG-A7

`PG-A7_Taker.blend` is the editable source, with one collection per mesh and its sockets, and the textures packed. Made in Blender 5.2.2 LTS with original Python modeling and Cycles bakes. It's our own work: no third-party content or generators, public redistribution allowed, and no credit needed.
