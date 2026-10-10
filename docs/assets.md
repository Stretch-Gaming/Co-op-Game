# Asset generation

Every lane makes its own art, sound and UI, tracked as separate asset tasks from its build work (HC-A1, PG-A2, HZ-A3 and so on). The schedule, with each task's two delivery sprints, is in [sprints.md](sprints.md#asset-generation), and each lane's epic has the full brief and specs for its own.

Three rules keep assets from slowing the game down:

- **Gameplay never waits on art.** Build with greybox shapes first. A generated asset replaces the greybox only after it passes review.
- **Each asset task has two deliveries.** _Generated_: the chosen candidate is saved and recorded. _In place_: it's imported, reviewed and swapped in. Generation can run while you build, but choosing, cleaning up and importing take your own time, so keep early deliveries small.
- **The minimum presentation kit can't be cut.** It's listed in [sprints.md](sprints.md#asset-generation). If a kit asset isn't ready, use a library asset that passes the license check below, rather than greybox.

## Art direction

- **The cave (Map 1):** dark, damp rock. Warm pools of torchlight, cold glowing crystals, one shaft of daylight in the spawn cavern. The way forward is always the brightest thing in view.
- **Relics:** gold, jade and gemstone, shiny enough to catch a headlamp from across a room.
- **Ghosts:** pale and translucent, glowing faintly, fading at the edges.
- **Map 2:** a sandstone Egyptian antechamber, lit by braziers.
- **Readability first:** players must tell each other apart at a glance, even in a split view. Each player has a color variant (PG-A1).

## Tools

PG-A0 picks the tools in Sprint 1, sets the import presets on both a Mac and Windows, takes one prop all the way through, and fills in this section. Other lanes start generating in Sprint 2. Candidates to compare:

- **Meshes:** hosted generators such as [Meshy](https://www.meshy.ai) or [Tripo](https://www.tripo3d.ai), which export textured meshes and have Unreal integrations, or open models such as Hunyuan3D, which need a powerful GPU.
- **Tileable textures:** an image model, or the texture tools in the mesh generator.
- **Sound:** a sound-effects generator.
- **Library assets:** free assets on [Fab](https://www.fab.com), subject to the license check below.

Every tool must run outside the Unreal project, or support both Mac and Windows. Don't add a generator plugin to the project without checking with the team, because any plugin has to work on every machine.

Chosen tools and import presets: _to be filled in by PG-A0._

## Licenses: this repo is public

Anything committed here, raw or imported, is published to the world. Being allowed to use an asset in a game isn't the same as being allowed to publish it in a public repo.

Before you commit an asset, record in its asset task:

- the tool or source, with a URL, and the plan or tier you used;
- the exact license and its version, such as CC0, CC BY 4.0 or a generator's terms;
- whether that license allows publishing the asset in a public repository;
- any attribution it requires.

Then:

- **Commit it** only if its license allows public redistribution. Assets you generated yourself on a plan that gives you the rights, and CC0 assets, usually do. Check: some generators' free tiers make outputs public or require attribution.
- **Add a line to [CREDITS.md](../CREDITS.md)** for anything that requires attribution, such as CC BY.
- **Don't commit it** if the license forbids redistribution, as Fab's standard license does for assets on their own. Pick another asset, or ask an org admin to make the repo private first.

## Specs

| Kind | Rules |
| --- | --- |
| Scale and axes | Real-world size, 1 Unreal unit = 1 cm, Z up. FBX is usually in centimeters; GLB is in meters with Y up, which the importer converts. Check against the 1.8 m template character before you place anything. |
| Pivot | At the base, centered, unless the asset rotates around something else (a gate's hinge, a log's top). |
| Static meshes | Nanite on above about 2k triangles for **opaque and masked** materials. **Nanite off for translucent materials**, such as the ghost and any translucent crystals; Nanite doesn't support them. Simple collision for anything players touch. Keep the triangle counts in your epic's spec. |
| Textures | Base color in sRGB. Normal maps with Normalmap compression, in DirectX convention; if a generator exports OpenGL normals, turn on Flip Green Channel. One packed mask per material, with sRGB off: red for ambient occlusion, green for roughness, blue for metallic. 2K for large props and tileable surfaces, 1K for small props. |
| Materials | Material instances of your lane's master material, not one-off materials from the import. |
| Sound | WAV, 48 kHz. Mono for anything placed in the world, stereo only for ambience. Loops must loop cleanly. |
| UI | PNG with transparency, 512 px, readable at small sizes in a split view. |
| Names | The prefixes in [AGENTS.md](../AGENTS.md#naming): `SM_`, `T_`, `M_`, `MI_`, `SFX_`. File extensions in lowercase. |
| Size | Raw source up to about 50 MB per asset task. If it's bigger, decimate or compress it before committing. |

On a Mac older than M2, Nanite falls back to simplified meshes. Check how your asset looks there if you can.

## Pipeline

1. **Brief.** Start from the asset task's description and specs. Write the prompt or pick the reference images.
2. **Generate.** Keep candidates outside the repo, in a local folder. Only the one you choose goes in.
3. **Check the license** as described above, and record it in the asset task.
4. **Save the chosen raw output**, such as GLB, FBX, PNG or WAV, in `SourceArt/<lane>/<asset task>/`, for example `SourceArt/HZ/HZ-A1/`. Git LFS stores it.
5. **Import** into `Content/<lane folder>/Art/`, through the editor or Unreal MCP, with PG-A0's import presets. Set scale, pivot, collision and Nanite, check the texture settings, and switch the materials to instances of your master material. Reimport from the file in `SourceArt/`, so anyone can redo it.
6. **Check in your test map.** Next to the template character, under the cave's lighting, on your machine and, for anything in the kit, on the other platform too.
7. **Before you push**, run `git lfs ls-files` and check every new binary file is listed. If one isn't, its extension is missing from `.gitattributes`, or isn't lowercase.
8. **Swap it in.** Replace the greybox in your sublevel, then look at it in the next playtest.

An asset is done when it's at the right scale with working materials and collision, it's in place in your sublevel, its source and license are in the task, any credit is in `CREDITS.md`, and nobody at the playtest flagged it.

## Folders

| Lane | Raw output | Imported assets |
| --- | --- | --- |
| HC | `SourceArt/HC/` | `Content/Puzzles/Art/` |
| PG | `SourceArt/PG/` | `Content/Player/Art/` |
| HZ | `SourceArt/HZ/` | `Content/Hazards/Art/` |

Each lane only edits its own folders, as with every other asset.
