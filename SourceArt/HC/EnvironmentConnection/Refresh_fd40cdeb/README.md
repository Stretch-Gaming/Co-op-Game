# Refreshed connected maze scenery

This is the current scenery capture used by L_ConnectedMaze. The source is PR #122 at the commit and hashes in provenance.json. The complete new capture is scene.json.gz; connection.json.gz contains the north portion trimmed at Y3200 and shifted X-175 to keep the existing room doorway.

All procedural scenery is baked privately under Content/Puzzles/EnvironmentConnection/Refresh_fd40cdeb. No shared index-based maze meshes are overwritten. The nonblocking colour-grade volume at index912 is excluded. The room, moving door, player starts and seam walls remain unchanged. No traps or puzzles are activated by this scenery update.

The parent folder's older capture remains as historical PR124 source. The current update tools and checks are in Tools/unreal/connection_refresh. Assets are authored through Unreal Editor only. Geometry is original team work and permits public redistribution.
