# PG-A4: zipline parts

Candidate A: the timber-yoke trolley, chosen over the open iron trolley B because it reads better at split-screen size.

| File | Triangles | Size, X × Y × Z (cm) | Imported as |
| --- | ---: | --- | --- |
| `SM_ZiplineTrolley.fbx` (trolley A) | 1,612 | 60 × 57 × 90 | `SM_ZiplineTrolley`, no collision |
| `SM_ZiplineAnchor_Top.fbx` | 2,176 | 95 × 148 × 239 | `SM_ZiplineAnchor_Top`, one box collision |
| `SM_ZiplineAnchor_Bottom.fbx` | 892 | 124 × 109 × 132 | `SM_ZiplineAnchor_Bottom`, one box collision |
| `SM_ZiplineCable.fbx` | 1,920 | 100 × 4 × 4 | `SM_ZiplineCable`, no collision; one spline mesh per meter, forward axis X |

Every origin sits on the cable's centerline. The trolley's T-bar is 64 cm below the cable, and the top anchor's foot is 197 cm below it, so `BP_Zipline` puts the cable 2.7 m above the boarding floor with the anchor on a plinth. `textures/` holds 1K baked base color (sRGB) and packed ORM masks (sRGB off, `TC_Masks`; red AO, green roughness, blue metallic). They feed the `MI_Zipline*` instances of `/Game/Shared/Style/M_Stylized` in UV mode, with `GradientStrength` at 0 so the baked gradient isn't doubled. `PG-A4_ZiplineParts.blend` is the editable source, with one collection per mesh.

Made in Blender 5.2.2 LTS with original Python modeling and Cycles bakes. It's our own work: no third-party content, public redistribution allowed, and no credit needed.
