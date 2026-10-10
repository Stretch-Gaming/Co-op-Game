# HUD dimensions and margins

All values below are physical pixels per local-player viewport. Texture widths are full square-canvas dimensions; visible bounds are recorded separately in geometry-and-validation.json.

| Output | Mode | Local viewport | HUD scale | Safe margin | Icon / banner / prompt width |
| --- | --- | --- | --- | --- | --- |
| 1280 x 720 | full | 1280 x 720 | 1.0 | 24 | 64 / 340 / 300 |
| 1280 x 720 | split-horizontal | 1280 x 360 | 0.85 | 20 | 54 / 289 / 255 |
| 1280 x 720 | split-vertical | 640 x 720 | 0.85 | 20 | 54 / 289 / 255 |
| 1920 x 1080 | full | 1920 x 1080 | 1.25 | 30 | 80 / 425 / 375 |
| 1920 x 1080 | split-horizontal | 1920 x 540 | 0.85 | 20 | 54 / 289 / 255 |
| 1920 x 1080 | split-vertical | 960 x 1080 | 0.85 | 20 | 54 / 289 / 255 |

Text never drops below 16px. Clear/failed states retain the round number below the status banner. Source textures remain square; transparent canvas portions may extend outside the player viewport while visible artwork stays inside the safe area.
