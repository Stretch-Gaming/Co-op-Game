# Asset generation

Every lane makes its own art, sound and UI, tracked as separate asset tasks from its build work (HC-A1, PG-A2, HZ-A3 and so on). The tasks for each sprint are in [sprints.md](sprints.md#asset-generation), and each lane's epic has the full brief and specs for its own.

Two rules keep assets from slowing the game down:

- **Gameplay never waits on art.** Build with greybox shapes first. A generated asset replaces the greybox only after it passes review.
- **Assets come a sprint early.** Start generation at kickoff, since it runs while you build. Import before you push.

## Art direction

- **The cave (Map 1):** dark, damp rock. Warm pools of torchlight, cold glowing crystals, one shaft of daylight in the spawn cavern. The way forward is always the brightest thing in view.
- **Relics:** gold, jade and gemstone, shiny enough to catch a headlamp from across a room.
- **Ghosts:** pale and translucent, glowing faintly, fading at the edges.
- **Map 2:** a sandstone Egyptian antechamber, lit by braziers.
- **Readability first:** players must tell each other apart at a glance, even in a split view. Each player has a color variant (PG-A1).

## Tools

PG-A0 picks the tools in Sprint 1, takes one prop all the way through, and fills in this section. Candidates to compare:

- **Meshes:** hosted generators such as [Meshy](https://www.meshy.ai) or [Tripo](https://www.tripo3d.ai), which export textured meshes and have Unreal integrations, or open models such as Hunyuan3D, which need a powerful GPU.
- **Tileable textures:** an image model, or the texture tools in the mesh generator.
- **Sound:** a sound-effects generator.
- **Library assets:** free assets on [Fab](https://www.fab.com), where a good one beats generating from scratch.

Every tool must run outside the Unreal project, or support both Mac and Windows. Don't add a generator plugin to the project without checking with the team, because any plugin has to work on every machine.

Chosen tools: _to be filled in by PG-A0._

## Specs

| Kind | Rules |
| --- | --- |
| Scale | Real-world size, 1 Unreal unit = 1 cm. Check against the 1.8 m template character before you place anything. |
| Pivot | At the base, centered, unless the asset rotates around something else (a gate's hinge, a log's top). |
| Static meshes | Nanite on above about 2k triangles. Simple collision for anything players touch. Keep the triangle counts in your epic's spec. |
| Textures | PBR: base color, normal, and a packed occlusion-roughness-metallic map. 2K for large props and tileable surfaces, 1K for small props. |
| Materials | Material instances of your lane's master material, not one-off materials from the import. |
| Sound | WAV, 48 kHz. Mono for anything placed in the world, stereo only for ambience. Loops must loop cleanly. |
| UI | PNG with transparency, 512 px, readable at small sizes in a split view. |
| Names | The prefixes in [AGENTS.md](../AGENTS.md#naming): `SM_`, `T_`, `M_`, `MI_`, `SFX_`. |

On a Mac older than M2, Nanite falls back to simplified meshes. That's fine, but check how your asset looks there if you can.

## Pipeline

1. **Brief.** Start from the asset task's description and specs. Write the prompt or pick the reference images.
2. **Generate.** Save the raw output, such as GLB, FBX or PNG, in `SourceArt/<lane>/<asset task>/`, for example `SourceArt/HZ/HZ-A1/`. Git LFS stores it.
3. **Record the source.** In the asset task, note the tool, the prompt and the license. Only use assets whose license allows a commercial game.
4. **Import** into `Content/<lane folder>/Art/`, through the editor or Unreal MCP. Set scale, pivot, collision and Nanite, and switch the materials to instances of your master material.
5. **Check in your test map.** Next to the template character, under the cave's lighting.
6. **Swap it in.** Replace the greybox in your sublevel, then look at it in the next playtest.

An asset is done when it's at the right scale with working materials and collision, it's in place in your sublevel, its source and license are in the task, and nobody at the playtest flagged it.

## Folders

| Lane | Raw output | Imported assets |
| --- | --- | --- |
| HC | `SourceArt/HC/` | `Content/Puzzles/Art/` |
| PG | `SourceArt/PG/` | `Content/Player/Art/` |
| HZ | `SourceArt/HZ/` | `Content/Hazards/Art/` |

Each lane only edits its own folders, as with every other asset.
