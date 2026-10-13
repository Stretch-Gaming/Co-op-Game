# Maze-level traversal geometry

Original scripted geometry created for Stretch's requested maze-level correction. `SM_MazeTraversalRock.json` is the deterministic raw mesh (positions, normals, UVs, colors and triangles). The editor creates `Content/Puzzles/Art/MazeLevel/Meshes/SM_MazeTraversalRock` through GeometryScript, assigns the existing team rock material and adds an explicit simple box for consistent movement/query collision. No model, texture or marketplace content was downloaded.

Source: `Tools/unreal/maze_level/bake_scene.py`, `rock_record()`. Rights/license: original geometry owned by the project author; no third-party asset license or version applies. Stretch authorized creation and public GitHub delivery. Public redistribution is permitted under [the project original-art workflow](../../../docs/assets.md). No third-party attribution is required. The material remains the existing shared style kit with its recorded provenance.

Other meshes in that import folder are private derivatives of the immutable Ak47/PK PR122 capture `SourceArt/HC/EnvironmentConnection/Refresh_fd40cdeb/connection.json.gz`, SHA-256 `2008b7a684ba0f82d34b97fe259c20ec7abc46e09d00ead5f9c1dd8c6fcbf0ed`. Their original source/provenance record remains in that folder. This correction restores the second meetup hall and makes four corridor gap/recovery cuts. Original collaborator assets and captures are not overwritten.

`Tools/unreal/maze_level/layout.py` records finite authored placement and dimensions. Editor collision, actual movement and rendered review are separate from its offline envelope checks.
