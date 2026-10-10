# Asset generation

Every lane makes its own art, sound and UI, tracked as separate asset tasks from its build work (HC-A1, PG-A2, HZ-A3 and so on). The schedule, with each task's two delivery sprints, is in [sprints.md](sprints.md#asset-generation), and each lane's epic has the full brief and specs for its own.

Three rules keep assets from slowing the game down:

- **Gameplay never waits on art.** Build with greybox shapes first. A generated asset replaces the greybox only after it passes review.
- **Each asset task has two deliveries.** _Generated_: the chosen candidate is saved and recorded. _In place_: it's imported, reviewed and swapped in. Generation can run while you build, but choosing, cleaning up and importing take your own time, so keep early deliveries small.
- **The minimum presentation kit can't be cut.** It's listed in [sprints.md](sprints.md#asset-generation). If a kit asset isn't ready, use a library asset that passes the license check below, rather than greybox.

## Art direction

The look is stylized and finished, in the spirit of Sea of Thieves, not realistic. The rules, the palette, the prompt suffix and the shared style kit are in [art/style.md](art/style.md). Read it before you generate anything.

- **The cave (Map 1):** dark, damp rock. Warm pools of torchlight, cold glowing crystals, one shaft of daylight in the spawn cavern. The way forward is always the brightest thing in view.
- **Relics:** gold, jade and gemstone, shiny enough to catch a headlamp from across a room.
- **Ghosts:** pale and translucent, glowing faintly, fading at the edges.
- **Map 2:** a sandstone Egyptian antechamber, lit by braziers.
- **Readability first:** players must tell each other apart at a glance, even in a split view. Each player has a color variant (PG-A1).

## Tools

PG-A0 picks the tools, sets the import presets on both a Mac and Windows, and takes one prop all the way through. Other lanes start generating in Sprint 2.

Every tool must run outside the Unreal project, or support both Mac and Windows. Don't add a generator plugin to the project without checking with the team, because any plugin has to work on every machine.

Chosen tools (PG-A0, revised Oct 9, 2026 to avoid paid services):

| Use | Tool | Cost and license |
| --- | --- | --- |
| Most meshes: rocks, crystals, stalagmites, bones, torches, braziers, statues, plates, gates, the altar, trap parts, the zipline | [Blender](https://www.blender.org), modeled by your agent through [Blender MCP](https://github.com/ahujasid/blender-mcp), or by hand, from the style frame and the greybox's dimensions. The chunky, broad-beveled style suits scripted modeling. Export every mesh through [Tools/blender/cleanup_export.py](../Tools/blender/cleanup_export.py), which fixes units, axes and normals and can decimate to a triangle budget. `M_Stylized`'s edge highlight still needs a curvature bake, which isn't in the script yet (PG-A0). | Free. Blender and Blender MCP (MIT) run on Mac and Windows. Your own work, so no credit is needed. |
| Organic shapes that are hard to build by script: the lion idol, the ghosts | [TRELLIS.2](https://github.com/microsoft/TRELLIS.2), image-to-3D from a style frame, run locally. On a Mac with 24 GB or more of memory, use [trellis-mac](https://github.com/shivampkumar/trellis-mac): about 5 minutes per model on an M4 Pro. On an NVIDIA GPU with 24 GB, use the official release. Keep the shape and re-texture it with `M_Stylized`. | Free. TRELLIS.2's code and weights are MIT, and outputs need no credit. Two conditions: **remove the frame's background first**, so the bundled background remover, which is non-commercial (RMBG-2.0, CC BY-NC 4.0), never runs; and accept Meta's DINOv3 license on Hugging Face, which TRELLIS.2's image encoder needs. DINOv3's custom license allows commercial use but doesn't spell out rights in outputs, so read it before the game is sold. |
| Filler props and quick stand-ins | CC0 libraries: [Poly Haven](https://polyhaven.com) (also inside Blender MCP), [Kenney](https://kenney.nl/assets), [Quaternius](https://quaternius.com) and [KayKit](https://kaylousberg.itch.io). Re-material them with `M_Stylized` instances so they match. | Free. CC0 allows publishing here, with no credit needed. |
| Style frames and concept images | OpenAI image generation (ChatGPT's built-in tool, also in Codex), with [`style-reference.png`](../SourceArt/PG/PG-A0/style-frames/style-reference.png) as the reference image. Ask for a transparent background when the image will go to TRELLIS.2. | OpenAI's terms give you the output, so it can be published here with no credit. Record the prompt on the issue. |
| Tileable textures | `M_Stylized`'s world-aligned mode with painted tileables from the image model | As above. |
| Sound | Made yourself (recorded or synthesized), CC0 libraries, or a sound generator whose plan grants the rights | Check each source. |
| UI fonts | Families under the SIL Open Font License from the [google/fonts](https://github.com/google/fonts) repo: Cinzel and Alegreya Sans SC for the HUD (PG-A6). | Free. The OFL allows bundling the font files with the game and publishing them here, as long as each keeps its `OFL.txt` next to it and isn't sold on its own. Credit each family in `CREDITS.md`. |

Optional: [Meshy](https://www.meshy.ai)'s Free plan (100 credits a month, enough for a few models) for a hero asset neither Blender nor TRELLIS.2 gets right. Its free outputs are CC BY 4.0 and shown publicly, so each one needs a line in `CREDITS.md`. Don't buy a paid plan for this project.

Not chosen:

- **Meshy as the main tool**, because the Free plan's credits cover only a few models and the rest needs a paid plan.
- **Tripo**, because its help page says free-plan outputs have no commercial rights.
- **Hunyuan3D**, including its Mac port, because its license excludes the EU, the UK and South Korea.
- **Stable Fast 3D**, because it has no confirmed Mac support and its license is capped by revenue.
- **TripoSG**, because it needs an NVIDIA GPU, makes geometry only and bundles a non-commercial background remover. It's worth a look for shapes if the Windows machine has an NVIDIA GPU with 8 GB or more.

### Setting up the free tools

- **Blender MCP.** Set up and tested on PK's Mac on Oct 9 with Blender 5.2.2 and `mcp-for-blender` 2.1.9:
  1. Install Blender and [uv](https://docs.astral.sh/uv/). On a Mac: `brew install --cask blender` and `brew install uv`. On Windows: `winget install BlenderFoundation.Blender` and `winget install astral-sh.uv`.
  2. Install the Blender add-on with `uvx mcp-for-blender install-addon`, then turn on **Interface: MCP for Blender** in Blender's Preferences → Add-ons.
  3. Register it with your agent, with its anonymous usage telemetry off. Claude Code: `claude mcp add --scope user blender -e DISABLE_TELEMETRY=true -- uvx mcp-for-blender`. Codex: `codex mcp add blender --env BLENDER_MCP_APPS=1 --env BLENDER_MCP_OPENAI_FORMS=1 --env DISABLE_TELEMETRY=true -- uvx mcp-for-blender`. (`uvx mcp-for-blender setup` adds it to every agent app it finds; run it with `--dry-run` first to see which.)
  4. Open Blender. The add-on starts its server on `localhost:9876` by itself; the MCP for Blender tab (press N in the 3D viewport) has Start and Stop. Then start your agent: `claude mcp list` should show `blender` as connected.

  Like Unreal MCP, the server has no authentication, so keep it on your own machine, and save your Blender file before letting an agent run code in it. The add-on's own telemetry, which would send prompts and screenshots, stays off unless you opt in.
- **trellis-mac:** follow its README. It needs about 15 GB for the model weights, a Hugging Face login, and approved access to the gated DINOv3 model. Give it PNGs whose backgrounds are already transparent, and on the first run check its output that the background remover was skipped. Its meshes have about 200K faces and can have small holes: fill the holes in Blender (Mesh → Clean Up → Fill Holes, or a voxel remesh), then let the cleanup script decimate with `--target-triangles`.

Import presets: _to be filled in by PG-A0 once the Unreal project exists._

## Licenses: this repo is public

Anything committed here, raw or imported, is published to the world. Being allowed to use an asset in a game isn't the same as being allowed to publish it in a public repo.

Before you commit an asset, record on its GitHub issue:

- the tool or source, with a URL, and the plan or tier you used;
- the exact license and its version, such as CC0, CC BY 4.0 or a generator's terms;
- whether that license allows publishing the asset in a public repository;
- any attribution it requires.

Then:

- **Commit it** only if its license allows public redistribution. Assets you generated yourself on a plan that gives you the rights, and CC0 assets, usually do. Check: some generators' free tiers make outputs public or require attribution.
- **Add a line to [CREDITS.md](../CREDITS.md)** for anything that requires attribution, such as CC BY.
- **Don't commit it** if the license forbids redistribution, as Fab's standard license does for assets on their own. Pick another asset, or ask Stretch, who owns the repo, to make it private first.

## Specs

| Kind | Rules |
| --- | --- |
| Scale and axes | Real-world size, 1 Unreal unit = 1 cm, Z up. FBX is usually in centimeters; GLB is in meters with Y up, which the importer converts. Check against the 1.8 m template character before you place anything. |
| Pivot | At the base, centered, unless the asset rotates around something else (a gate's hinge, a log's top). |
| Static meshes | Nanite on above about 2k triangles for **opaque and masked** materials. **Nanite off for translucent materials**, such as the ghost and any translucent crystals; Nanite doesn't support them. Simple collision for anything players touch. Keep the triangle counts in your epic's spec. |
| Textures | Base color in sRGB. Normal maps with Normalmap compression, in DirectX convention; if a generator exports OpenGL normals, turn on Flip Green Channel. One packed mask per material, with sRGB off: red for ambient occlusion, green for roughness, blue for metallic. 2K for large props and tileable surfaces, 1K for small props. |
| Materials | Material instances of the shared `M_Stylized` in `Content/Shared/Style/`, not one-off materials from the import. Translucent or glowing materials can be lane master materials, but use the palette in [art/style.md](art/style.md#palette). |
| Sound | WAV, 48 kHz. Mono for anything placed in the world, stereo only for ambience. Loops must loop cleanly. |
| UI | PNG with transparency, 512 px, readable at small sizes in a split view. |
| Names | The prefixes in [AGENTS.md](../AGENTS.md#naming): `SM_`, `T_`, `M_`, `MI_`, `SFX_`. File extensions in lowercase. |
| Size | Raw source up to about 50 MB per asset task. If it's bigger, decimate or compress it before committing. |

On a Mac older than M2, Nanite falls back to simplified meshes. Check how your asset looks there if you can.

## Pipeline

1. **Brief.** Start from the asset task's description and specs. Make a style frame and add the prompt suffix, as [art/style.md](art/style.md#making-an-asset) describes.
2. **Generate.** Keep candidates outside the repo, in a local folder. Only the one you choose goes in.
3. **Check the license** as described above, and record it on the asset's issue.
4. **Save the chosen raw output**, such as GLB, FBX, PNG or WAV, in `SourceArt/<lane>/<asset task>/`, for example `SourceArt/HZ/HZ-A1/`. Git LFS stores it.
5. **Import** into `Content/<lane folder>/Art/`, through the editor or Unreal MCP, with PG-A0's import presets. Set scale, pivot, collision and Nanite, check the texture settings, and switch the materials to instances of your master material. Reimport from the file in `SourceArt/`, so anyone can redo it.
6. **Check it in `L_StyleTest`.** Next to the template character and the example assets, under the cave's lighting, on your machine and, for anything in the kit, on the other platform too. Then check it in your own test map.
7. **Before you push**, run `git lfs ls-files` and check every new binary file is listed. If one isn't, its extension is missing from `.gitattributes`, or isn't lowercase.
8. **Swap it in.** Replace the greybox in your sublevel, then look at it in the next playtest.

An asset is done when it's at the right scale with working materials and collision, it's in place in your sublevel, its source and license are on its issue, any credit is in `CREDITS.md`, and nobody at the playtest flagged it.

## Folders

| Lane | Raw output | Imported assets |
| --- | --- | --- |
| HC | `SourceArt/HC/` | `Content/Puzzles/Art/` |
| PG | `SourceArt/PG/` | `Content/Player/Art/` |
| HZ | `SourceArt/HZ/` | `Content/Hazards/Art/` |

Each lane only edits its own folders, as with every other asset.
