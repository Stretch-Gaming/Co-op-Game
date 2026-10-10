# Visual style

Oct 9, 2026 · PK, for the team

The look we're aiming for is Sea of Thieves in a cave: stylized and finished, not realistic. Three people generate assets with different tools on different days, so the look can't depend on each person's prompts. It comes from a few shared Unreal assets (the [style kit](#the-style-kit)) that every asset goes through, and from the six rules below. The pipeline, specs and licensing rules are in [assets.md](../assets.md).

## The six rules

1. **Chunky and uneven.** Exaggerated proportions, wide bevels that catch light, no perfectly straight lines. Detail goes in the silhouette, not in fine surface noise.
2. **Painted, not photographed.** Smooth color shifts, darker at the bottom and lighter at the top. Highlights on outer edges. Surfaces are mostly matte; only metal and relics are shiny.
3. **Colored shadows, never black.** Sea of Thieves is bright and our cave is dark. Deep blue-violet shadows and tinted fog keep the stylized feel in the dark.
4. **Colors that mean something.** Each color in the table below has one job. Nothing decorative uses the ghost, trap-warning or relic colors.
5. **Lived in.** Rope wraps, chipped stone, patched wood. Everything looks used, but stays readable.
6. **Readable in split-screen first.** If an asset doesn't read at half-screen size under the cave's lighting, it fails, however good the generator's preview looked.

## Palette

| Meaning | Color | Used for |
| --- | --- | --- |
| Path and safety | `#FFB347` torch amber | Torches, braziers, the way forward |
| Ambient light | `#3FD0C9` crystal teal | Crystals, cold fill light |
| Relic | `#E8B33A` gold, `#3FA672` jade | Relics only |
| Threat | `#D6F0FF` ghost white | Ghosts only |
| Danger | `#FF4A2A` trap red | Trap warnings only |
| Shadow | `#1E2433` blue-violet | Shadow tint and fog |
| Cave rock | `#4A4652` mid, `#7A6E68` light | Walls, floor, rocks |
| Map 2 | `#D9A86C` sandstone | The Egyptian antechamber |

Player colors (PG-A1) must stay clearly apart from the reserved colors: relic, threat and danger.

## Shapes

- Big shapes first, then medium, then a little small detail. Generated meshes usually have too much small detail; smooth it out rather than keep it.
- Hand-touched parts (handles, levers, the carried heart) are about 15–20% larger than real life, so they read in first person.
- Stone is slightly lumpy, and wood is slightly bent. Mechanical parts that must line up with a Blueprint (plates, gates, the zipline handle) keep exact dimensions, with uneven bevels and paint on top.

## Making an asset

1. **Start from a style frame.** Make a concept image of the asset with the team's image model, using [`style-reference.png`](../../SourceArt/PG/PG-A0/style-frames/style-reference.png) as the image reference. The [style frames](../../SourceArt/PG/PG-A0/README.md) show what finished scenes should look like. Then run image-to-3D on that concept. That gives much more consistent results than text-to-3D.
2. **Append the prompt suffix** to every image and mesh prompt:

   > stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures

3. **Clean it up** with [Tools/blender/cleanup_export.py](../../Tools/blender/cleanup_export.py): scale, axes, pivot and triangle count.
4. **Don't trust the generator's textures.** Import them, then tint and adjust them through an instance of `M_Stylized`. If they still fight the style, drop them and use the material's painted look on its own.
5. **Check it in `L_StyleTest`** next to the example assets before it replaces a greybox.

## The style kit

Everything lives in `Content/Shared/Style/`, which is lockable. Lock before you edit it.

| Asset | Owner | What it is |
| --- | --- | --- |
| `M_Stylized` | PG (PG-A0) | The shared master material for opaque assets: base color tint, dark-to-light gradient, edge highlight from the packed mask's AO channel, and flat roughness. A static switch turns on world-aligned textures, for rock and anything else without clean UVs. |
| `L_StyleTest` | PG (PG-A0) | A test map with the template character, the cave lighting and one example asset from each lane. Lock it to add yours. |
| Example rock and gold prop | PG (PG-A0) | The first two assets through the pipeline. They set the bar for everything after. |
| Atmosphere preset | HZ (HZ-A1) | A post-process volume with a color grading LUT, and exponential height fog in the shadow color. Placed in `L_Site01_HZ` and copied into `L_StyleTest`. |
| UI kit | PG (PG-A6) | Fonts, panels, icons and `WBP_UIStyleTest`, in `Content/Shared/UI/`, which is lockable too. Every widget is built from it; see [HUD and UI](#hud-and-ui). |

Lane materials are instances of `M_Stylized`. Translucent or glowing materials, such as the ghost and the crystal glow, can be their own lane master materials, but they use the palette above.

## HUD and UI

The HUD sits on top of a dark, scary cave, often in a split-screen half. The first HUD used hollow frames, so the cave showed through them, and thin default text floated over the scene. It looked flat and out of place. These rules replace that look.

1. **Solid, never see-through.** Every panel has an opaque backing plate painted in the shadow family, `#2A3042` at the top to `#161B27` at the bottom. Text and icons never sit directly on the scene.
2. **Depth in four layers.** From back to front: a soft drop shadow in blue-violet, never black, about 4 px down at 1080p; a chunky carved frame of stone or dark wood, lit from above, with a lighter bevel on its top edges and darker lower edges; a recessed plate, with an inner shadow under its top edge; then the content, with its own small shadow. Let pieces overlap: the relic icon breaks out of its plate, and rope wraps sit over the frame's corners.
3. **Two typefaces, never the engine default.** [Cinzel](https://github.com/google/fonts/tree/main/ofl/cinzel), Bold to Black, is for round names, banners, counters and big moments: carved Roman capitals that look cut into the stone. [Alegreya Sans SC](https://github.com/google/fonts/tree/main/ofl/alegreyasanssc), Bold or ExtraBold, is for prompts, labels and names: sturdy and readable at small sizes. Both use the SIL Open Font License, so they can live in this public repo; credit them in [CREDITS.md](../../CREDITS.md).
4. **Warm text with a dark edge.** Text is parchment cream, `#F3E6C8`, with a 2 px outline in `#1E2433` and a soft shadow 3 px below. Headings get a slight carved look from a cream-to-sand gradient. The palette's meanings still hold: relic gold for relic numbers, torch amber for the objective and the way forward, trap red only for danger, ghost white only for ghosts.
5. **The HUD steps back.** A big banner appears when a round starts or clears, holds for about 3 seconds, then shrinks to one small objective line. Counters show at full strength when they change, then dim. In a quiet moment the screen is mostly cave.
6. **Motion with weight.** Banners drop in with one short overshoot, like a stone slab settling, in about 0.35 seconds, and fade out in about 0.5 seconds.
7. **Readable in split-screen first.** Scale each player's HUD to their own view: `S = clamp(min(W/1280, H/720), 0.85, 1.25)`, with a safe margin of `24 × S` px, and no text smaller than 16 px in a 1280 × 720 half. Check every piece in `WBP_UIStyleTest` at 1080p and in both split layouts before it goes into the HUD.

PG builds the UI kit in PG-A6, and HC builds the HUD, the interact prompt and the results from it in HC-8.

## Reference board

Keep the Sea of Thieves reference board **out of this repo**. The repo is public, and those screenshots are copyrighted. Keep it in a private board, such as PureRef or Figma, that PK shares with the team. Style frames you generate yourself can be committed in `SourceArt/<lane>/` like any other generated source.

## Look check

At every playtest, Stretch spends 2 minutes on the Windows host, which is the reference machine for lighting, and names anything that looks out of place. That asset goes back to its lane for the next sprint.
