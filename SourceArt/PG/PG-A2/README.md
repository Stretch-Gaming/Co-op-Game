# PG-A2: ghost stand-in

Candidate C02 Long Reach, chosen over C01 Hunched Mantle and C03 Broad Veil because its uneven reaching arms read best at 15 m. It's a stand-in: the real ghost from Meshy replaces it later.

- `SM_Ghost.fbx`: 4,198 triangles, 189 × 75 × 205 cm, centimeters and Z up, pivot at the volume's center of mass. UV0 is the surface unwrap. UV1's V and the linear vertex color both hold the normalized height, bottom 0 and top 1, for the tail fade.
- `SM_Ghost_LongReach_cave.blend`: the editable source. `mesh-stats.json` and `03_neutral_scale_1440x1080.png` show its size against a 1.8 m capsule.

Imported as `Content/Player/Art/SM_Ghost` at scale 1, with Nanite off, normals and vertex colors kept, and no collision. The mesh faces +Y in Unreal, so `BP_Ghost` turns it −90° in yaw. `M_Ghost` is the lane's translucent, unlit master: ghost white `#D6F0FF`, a Fresnel edge fade, a tail fade from the vertex color's red channel, a slow emissive pulse, a depth fade where it passes through walls, and a `RepelFlash` scalar for PG-5.

Made in Blender 5.2.2 LTS with original procedural Python modeling. It's our own work: no third-party inputs, public redistribution allowed, and no credit needed.
