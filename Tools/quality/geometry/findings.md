# Primary native verification

The current visible-surface pass checked70 proposed surface/landmark points and4 nearby rock-clearance offsets. All74 have ground support;73 permit the standing capsule. Seven of eight original local grounded segments are clear. The one rock-edge overlap has clear positions15�90cm outward and a clear sampled detour. No broken passage or floor hole is proved; no geometry changed. These are bounded complex queries, not full-maze walking acceptance. See evidence/native-summary.json.

The first all-collision-surface plan produced18 overlaps on hidden rock tops. Those historical proposals are described below and are superseded for walking-surface interpretation. The native query was corrected to the registered Pawn profile, with capsule object/solid responses and each component response pair checked; Custom is not a registered query profile.

# Native geometry flags reviewed

The 18 standing-capsule flags do not establish 18 broken passages. All18 start already penetrating geometry at time0 and distance0. Every proposed foot position came from the top of hidden detail-collision mesh `Connected_Maze_890`; these are not authored walking positions. The source deliberately builds hidden wall/ceiling collision and separate collision for decorative rocks. A large upward triangle on those volumes can be a rock top or roof rather than the intended tunnel floor.

Across70 source proposals, native rays found support at every point (714 queries). This establishes usable editor physics and sampled support, not that all70 points are accessible player ground or that the map has no holes. Actual character defaults are radius35cm, half-height90cm, step45cm, slope44.765°, profile `Custom`.

Classification:

- Eleven overlaps hit `Connected_Maze_324`, with horizontal impact normals and penetration2.46–21.67cm. The capsule is within35cm of deliberately blocking structural walls. Most likely these are bad standing proposals on wall-adjacent rock tops, not invisible walls added across walking passages.
- Seven hit `Connected_Maze_890` itself. Three have upward/sloping normals, consistent with detail-box/support edges touching the capsule. Two have downward normals, indicating insufficient headroom above the proposed rock-top position. The remaining horizontal/oblique cases include the single severe axis-clearance flag. They merit closer inspection, but decorative support geometry is still the leading explanation.
- No candidate is proved unrelated to authored walls, rocks, ceilings, gaps or mechanics. Do not disable either whole-maze collider or alter difficulty on this evidence.

The three strongest *validation targets*, all in centimetres, are:

| Proposed feet XYZ | Native observation | Interpretation and next validation |
|---|---|---|
| (-3407.59,13224.64,707.43) | `Connected_Maze_890`, penetration50.85cm, normal(-0.675,0.738,0); side-ray Y clearance28.70cm | Highest-priority clearance observation, but this is the top of an axis-aligned detail collision box. At the sameXY, visible colliding procedural geometry is atZ400 (`Connected_Maze_318`),307.43cm below the proposed feet. Read-only native floor/headroom probes at the lower walking surface, followed by real approach walking, distinguish a tunnel obstruction from an inaccessible rock top. No teleport into the overlap. |
| (-4283.22,8710.88,118.16) | `Connected_Maze_890`, penetration47.81cm, normal(0,0,-1) | Headroom fails at this rock-top proposal. The sampled triangle is a flat top of a detail collision box, and no visible colliding procedural floor was found directly underneath in the source. Inspect whether thisXY is in the intended tunnel or inside side/overhead rocks; approach along the real floor before calling it a passage blocker. |
| (-4440.90,18918.02,701.36) | `Connected_Maze_890`, penetration39.30cm, normal(0,0,-1) | Another rock-top headroom failure. The nearby sample-to-sample segment has one missing intermediate support ray; its endpoints are collision-box tops, so the miss does not prove a floor hole. Inspect real floor continuity and try a normal walk around the detail from an accessible position. |

The other short segment in the current saved evidence passes its five support rays and sweeps, but lies atZ1075 on `Connected_Maze_324`; that may be structural roof geometry. It is not proof of an accessible walking route.

Source evidence: `Prototypes/CoopCave/Source/CoopProto/CoopPlayground.cpp` creates detail `BlockerMesh` from each rock hull's axis-aligned bounds (around lines1452–1463), hides the detail collision (2338–2340), and explicitly describes structural walls/ceilings as hidden blocking boxes (2689 onward). The original prototype also retains convex hulls, while the editor derivative uses complex triangle collision. Therefore a mismatch between visible rock shape and its box collision is possible; it needs movement/visual proof and design approval before changing the collision representation.

No fix is proposed. Next gate: rendered inspection and movement from accessible floor at these three spots, with actor identity and actual foot height recorded. Keep the unchanged entrance/return result; do not claim six-round route acceptance from this preview audit.
