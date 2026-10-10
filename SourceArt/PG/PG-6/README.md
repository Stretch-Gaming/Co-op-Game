# PG-6: floor lever and gauntlet gate

| File | Triangles | Size, X × Y × Z (cm) | Imported as |
| --- | ---: | --- | --- |
| `SM_Lever_Base.fbx` | 1,492 | 75 × 60 × 65 | `SM_Lever_Base`, one box collision |
| `SM_Lever_Handle.fbx` | 1,472 | 16 × 52 × 85 | `SM_Lever_Handle`, one box collision |
| `SM_GauntletGate.fbx` | 3,472 | 28 × 430 × 400 | `SM_GauntletGate`, one box collision |
| `SM_GauntletGate_Frame.fbx` | 4,504 | 112 × 570 × 524 | `SM_GauntletGate_Frame`, three box collisions (two posts, lintel) |

X is the passage direction and Y spans its width. Each FBX carries its collision as `UCX_<MeshName>_NN` boxes, but the editor's FBX import on Unreal 5.8.3 dropped them. So the imported meshes got the same boxes in editor Python after import: one bounds box each for the lever parts and the gate, and three boxes (two posts and the lintel) on the frame. Redo that after a reimport.

- **Lever base:** pivot at the base centre on the floor. The hinge axle runs along Y through (0, 0, 45) cm. The slot between the iron quadrant plates is 16 cm wide (Y −8 to +8), with nothing in it above 40 cm except the axle.
- **Lever handle:** the origin is exactly on the hinge axis, so place it at (0, 0, 45) cm on the base and rotate it by pitch. At rest it stands upright along +Z, with the top of the grip 77 cm above the hinge (122 cm above the floor). The T grip is 52 cm across, along Y. The handle swings ±45° and more without touching the base. In Blender, a positive Y rotation tilts the grip toward +X.
- **Gate:** pivot at the bottom centre, with a flat bottom at Z 0. It's 430 cm in Y, 400 cm tall and 28 cm thick (X −14 to +14).
- **Frame:** pivot at the bottom centre. The clear opening is exactly 400 cm (Y −200 to +200), with the lintel's underside at 460 cm and its top at 520 cm. The grooves in the posts and the slot through the lintel run X −16 to +16 and out to Y ±219 cm, so the gate slides in them with 2 cm to spare. The gate rises 420 cm, so its top ends at 820 cm, through the lintel. The collision boxes leave the opening (Y −200 to +200, Z 0 to 460) completely free.

`textures/` holds the 1K baked base color (sRGB) and packed ORM mask (sRGB off, `TC_Masks`; red AO, green roughness, blue metallic) for each mesh. They feed `MI_` instances of `/Game/Shared/Style/M_Stylized` in UV mode, with `GradientStrength` at 0 so the baked gradient isn't doubled. `previews/` has a four-angle sheet of each mesh, the lever assembled with the handle at 40°, and the gate closed in its frame. `metrics.json` has the triangle counts, bounds and collision boxes. `PG-6_LeverGate.blend` is the editable source, with one collection per mesh and its textures packed.

`build_lever_gate.py` rebuilds everything here:

    blender -b --factory-startup --python SourceArt/PG/PG-6/build_lever_gate.py -- SourceArt/PG/PG-6

Made in Blender 5.2.2 LTS with original Python modeling and Cycles bakes. It's our own work: no third-party content, public redistribution allowed, and no credit needed.
