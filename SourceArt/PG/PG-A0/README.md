# PG-A0: style reference and style frames

The team's visual anchor, described in [docs/art/style.md](../../../docs/art/style.md).

- `style-frames/style-reference.png`: the style reference. Use it as the reference image for every concept image you generate, then run image-to-3D on the concept.
- `style-frames/frame-01` to `frame-06`: style frames for the puzzle chamber, relic altar, ghost, trap corridor, zipline exit and Map 2 antechamber. Aim for these when you judge an asset in `L_StyleTest`.
- `style-frames/concepts/`: single-object concepts, ready for Meshy image-to-3D: a cave rock, the gold idol, two ghosts and the zipline trolley.
- `style-frames/prompts.md`: the exact prompt and reference behind every image.

Made with OpenAI image generation (built into Codex) on Oct 9, 2026. OpenAI's terms assign the output to the user, so these can be published here and need no credit. Known gaps: the zipline frame's pulley is only approximate (use the trolley concept), and the ghost concepts look more solid than the final translucent material will.

To clean up a generated mesh before import, use [Tools/blender/cleanup_export.py](../../../Tools/blender/cleanup_export.py):

```sh
blender -b --python Tools/blender/cleanup_export.py -- input.glb SM_Name.fbx --name SM_Name --target-triangles 5000
```

It applies transforms, converts to centimeters and Z up, sets the pivot to the base center, optionally decimates, and exports FBX.
