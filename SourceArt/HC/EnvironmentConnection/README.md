# Environment connection source

Team-authored derivative of the existing cave/maze and HC stone-door assets. Public redistribution is permitted under the same project permissions as the existing assets. No downloaded or marketplace content added.

The captured maze source is `SourceArt/HC/MazeIntegration/scene.json.gz`(PR90 reference). Its exact SHA256and cut/translation settings are recorded in provenance.json. This separate source copy keeps geometry north ofY3200, translates itX-175 to match the existing room's north passage, and excludes non-environment volume909. Boundary triangles retain interpolated normals, UVs and vertex colors. Source capture and teammate-owned maps are unchanged.

Unreal editor GeometryScripting creates13clipped mesh assets under`Content/Puzzles/EnvironmentConnection/Art`. `SM_ConnectionDoor` is an editor-created, centered copy of team-authored `Content/Puzzles/Art/HCA2_Props/SM_ChamberGate_Leaf`, preserving its materials. Existing source credits remain in the project CREDITS.md. The connected map and these derived assets belong to HC.
