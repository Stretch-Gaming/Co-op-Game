# PG-A4: zipline parts

Candidate A: the timber-yoke trolley, chosen over the open iron trolley B because it reads better at split-screen size.

| File | Triangles | Size, X × Y × Z (cm) | Imported as |
| --- | ---: | --- | --- |
| `SM_ZiplineTrolley.fbx` (trolley A) | 1,612 | 60 × 57 × 90 | `SM_ZiplineTrolley`, no collision |
| `SM_ZiplineAnchor_Top.fbx` | 2,588 | 108 × 148 × 322 | `SM_ZiplineAnchor_Top`, one box collision |
| `SM_ZiplineAnchor_Bottom.fbx` | 2,964 | 130 × 145 × 272 | `SM_ZiplineAnchor_Bottom`, one box collision |
| `SM_ZiplineCable.fbx` | 1,920 | 100 × 4 × 4 | `SM_ZiplineCable`, no collision; one spline mesh per meter, forward axis X |

Every origin sits on the cable's centerline. The trolley's T-bar is 64 cm below the cable, and a rider's feet hang 245 cm below it (`BP_ZiplineTrolley`'s `RiderPoint` at −155 cm, plus a 90 cm capsule half-height). So both anchors are tall timber gantries:

- **Top anchor:** the cable eye is 280 cm above the floor it stands on. Its posts and braces stand behind the eye, up to 106 cm back, so put the eye about 30 cm in from the ledge edge. The rider then starts over the drop instead of over the ledge.
- **Bottom anchor:** the eye is 230 cm above the landing floor. Its strapped skid, ballast rock and flax backstay sit behind the eye, up to 117 cm along the cable. A rider lets go 125 cm before the eye (`BP_Zipline.RideEndInset`) with their feet about 15 cm above the landing.

`textures/` holds 1K baked base color (sRGB) and packed ORM masks (sRGB off, `TC_Masks`; red AO, green roughness, blue metallic). They feed the `MI_Zipline*` instances of `/Game/Shared/Style/M_Stylized` in UV mode, with `GradientStrength` at 0 so the baked gradient isn't doubled. `previews/` has a four-angle sheet of each anchor. `PG-A4_ZiplineParts.blend` is the editable source, with one collection per mesh.

`build_tall_anchors.py` rebuilds both anchors in that file: it replaces the two anchor meshes, bakes their textures, exports the FBX files and saves the `.blend`.

    blender -b SourceArt/PG/PG-A4/PG-A4_ZiplineParts.blend --python SourceArt/PG/PG-A4/build_tall_anchors.py -- <output folder>

Then copy the output over these files and reimport over the existing assets, so references and material instances are kept.

Made in Blender 5.2.2 LTS with original Python modeling and Cycles bakes. It's our own work: no third-party content, public redistribution allowed, and no credit needed.
