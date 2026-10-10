# PG-A0 — generated visual style review

Created 2026-10-09 for PK’s review. All deliverables are outside the repository in `/Users/peterkim/CoopGameArt/style-frames/`. No Unreal assets were changed. These images were made with the built-in `image_gen.imagegen` tool; its underlying model identifier and model revision are not exposed by the tool, so no model name is inferred. Every generated prompt below is recorded verbatim, including the required art suffix. `transparent_background` was `false` on every generation.

## Reference choice and consistency

Selected `reference-candidate-02.png` as `style-reference.png`: its open floor and broad stepping stones read at small size, the amber exit is unmistakable, teal is restrained, and the shadows remain blue-violet. Every style frame and every object concept—including revised concepts—used the absolute `style-reference.png` path as its sole input image via `referenced_image_paths`. The reference was supplied for style, not as a scene edit target. The selected file is an identical copy of Candidate 2.

The set is visually consistent in broad stone forms, softened bevels, painted gradients, amber/teal cave lighting and blue-violet shadows. The sandstone room carries over this shape and lighting language. The reserved gold/jade, ghost-white and trap-red colors appear on their intended subjects. Hex colors in generative output are visual targets rather than calibrated flat swatches; lighting changes their apparent values.

## Review flags

- `reference-candidate-01.png`: added green foliage/moss makes reserved jade-like colors decorative. Exclude this candidate or regenerate without vegetation if it is chosen later. Its composition also contains more surface detail than Candidate 2.
- `concepts/gold-idol-25cm-first-pass.png`: superseded; excess polygonal paint patches and harder facets. Revised `gold-idol-25cm.png` is smoother and preferred, though some medium-scale painted variation remains.
- `concepts/ghost-hunched-first-pass.png`: superseded; skull-like nose and open mouth. Revised `ghost-hunched.png` has a rounded human face, closed mouth and softer surfaces.
- `frame-05-zipline-exit.png`: coherent style, but pulley/cable arrangement is approximate and should be regenerated if used as a functional assembly reference. Use `concepts/zipline-trolley.png` for the tandem-wheel design. This is a visual concept, not an engineering drawing.
- Ghost object concepts prioritize a connected, readable volume for image-to-3D and appear more solid than the translucent wall ghost. If their literal transparency will define the final rendered ghost material, regenerate for stronger translucency; use the scene frame for material intent.
- No final frame has photographic textures or fine grain. Cave surfaces retain some broad painted chips; simplify further during mesh/material production if required. Half-screen readability was assessed visually, not in-engine. PK makes the final selection.

## Export and contact sheet

The tool produced landscape images at 1672 × 941 px. The six frame deliverables are centered, losslessly cropped to 1664 × 936 px (exactly 16:9), removing 4 px from each horizontal edge, 2 px from the top and 3 px from the bottom. There is no resampling or color change. The references remain unmodified at native resolution. Square object concepts remain unmodified at 1254 × 1254 px.

`contact-sheet.png` is a deterministic Pillow composition of all 17 source deliverables (three candidates, selected reference, six frames, five final concepts, two superseded first passes). Each tile contains its filename and status, with proportional thumbnail scaling. It does not have an image-generation prompt or a reference image of its own. This file and the written `prompts.md` use Python/Pillow and text composition, rather than a generative image model. `prompts.md` is the provenance record, not generated art. No rights or licensing terms are inferred here; the tool name, exact prompts, inputs and original source paths are provided for a later license record.

## Exact generation prompts

### reference-candidate-01.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: none
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-0f52c9fe-2f3d-454e-830e-43d0425e3da8.png`

```text
Use case: stylized-concept
Asset type: finished visual-style reference for a cooperative first-person puzzle game.
Primary request: a dark underground spawn cavern with exactly one shaft of soft daylight from a small roof opening, a few warm torches marking the safe path, and sparse large glowing teal crystals providing cold fill light. View from a standing player's eye height about 1.65 m, without hands, characters or HUD. A polished stylized 3D game-render look, broad hand-painted gradients and clean simple surfaces. Big readable shapes first, medium shapes second, very little small detail. Chunky slightly lumpy rock masses, deliberately uneven silhouettes and wide soft bevels. Sparse rope wraps and broad stone chips, no grit. Mostly matte rock with simple edge highlights. Light beam is subdued daylight, not luminous ghost-white material.
Composition/framing: wide 16:9 landscape, no borders, text, logos or watermarks. Readable even at half-screen thumbnail size. Dark atmospheric but every foreground shape remains readable; tinted fog rather than crushed black. No photographic realism, microtexture, grain, noisy scratches, intricate ornament or extreme lens effects.
Color palette: torch amber #FFB347 means safe path; crystal teal #3FD0C9 means ambient crystal light; shadows and fog deep blue-violet #1E2433, never black. Cave stone mid #4A4652 and light #7A6E68. Reserve #E8B33A gold and #3FA672 jade exclusively for relics, #D6F0FF pale ghost white exclusively for ghosts, and #FF4A2A red exclusively for trap warnings. In this spawn scene there are no relics, ghosts or traps, so omit their reserved colors.
Composition choice A: inviting broad cavern with a low curved path leading around a central uneven rock mound toward an amber-lit tunnel. The daylight shaft falls slightly left of center; crystal clusters frame the right side. Strong clear separation of foreground, midground and background.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### reference-candidate-02.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: none
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-aef22c52-fe00-4ab0-97bb-5e17392c02a7.png`

```text
Use case: stylized-concept
Asset type: finished visual-style reference for a cooperative first-person puzzle game.
Primary request: a dark underground spawn cavern with exactly one shaft of soft daylight from a small roof opening, a few warm torches marking the safe path, and sparse large glowing teal crystals providing cold fill light. View from a standing player's eye height about 1.65 m, without hands, characters or HUD. A polished stylized 3D game-render look, broad hand-painted gradients and clean simple surfaces. Big readable shapes first, medium shapes second, very little small detail. Chunky slightly lumpy rock masses, deliberately uneven silhouettes and wide soft bevels. Sparse rope wraps and broad stone chips, no grit. Mostly matte rock with simple edge highlights. Light beam is subdued daylight, not luminous ghost-white material.
Composition/framing: wide 16:9 landscape, no borders, text, logos or watermarks. Readable even at half-screen thumbnail size. Dark atmospheric but every foreground shape remains readable; tinted fog rather than crushed black. No photographic realism, microtexture, grain, noisy scratches, intricate ornament or extreme lens effects.
Color palette: torch amber #FFB347 means safe path; crystal teal #3FD0C9 means ambient crystal light; shadows and fog deep blue-violet #1E2433, never black. Cave stone mid #4A4652 and light #7A6E68. Reserve #E8B33A gold and #3FA672 jade exclusively for relics, #D6F0FF pale ghost white exclusively for ghosts, and #FF4A2A red exclusively for trap warnings. In this spawn scene there are no relics, ghosts or traps, so omit their reserved colors.
Composition choice B: a compact bowl-shaped spawn chamber, a gently raised central stepping-stone path leading to an offset arched exit. The single daylight shaft marks the center of the chamber, two torches identify the exit, sparse teal crystals balance the foreground. Calm, spatially legible composition.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### reference-candidate-03.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: none
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-f0bb21d5-da85-4233-b165-d7e9c2684b3b.png`

```text
Use case: stylized-concept
Asset type: finished visual-style reference for a cooperative first-person puzzle game.
Primary request: a dark underground spawn cavern with exactly one shaft of soft daylight from a small roof opening, a few warm torches marking the safe path, and sparse large glowing teal crystals providing cold fill light. View from a standing player's eye height about 1.65 m, without hands, characters or HUD. A polished stylized 3D game-render look, broad hand-painted gradients and clean simple surfaces. Big readable shapes first, medium shapes second, very little small detail. Chunky slightly lumpy rock masses, deliberately uneven silhouettes and wide soft bevels. Sparse rope wraps and broad stone chips, no grit. Mostly matte rock with simple edge highlights. Light beam is subdued daylight, not luminous ghost-white material.
Composition/framing: wide 16:9 landscape, no borders, text, logos or watermarks. Readable even at half-screen thumbnail size. Dark atmospheric but every foreground shape remains readable; tinted fog rather than crushed black. No photographic realism, microtexture, grain, noisy scratches, intricate ornament or extreme lens effects.
Color palette: torch amber #FFB347 means safe path; crystal teal #3FD0C9 means ambient crystal light; shadows and fog deep blue-violet #1E2433, never black. Cave stone mid #4A4652 and light #7A6E68. Reserve #E8B33A gold and #3FA672 jade exclusively for relics, #D6F0FF pale ghost white exclusively for ghosts, and #FF4A2A red exclusively for trap warnings. In this spawn scene there are no relics, ghosts or traps, so omit their reserved colors.
Composition choice C: taller cavern with large broad overhead arching rock masses, a shallow curving safe path along one wall toward a torch-lit passage, the daylight shaft glances across a wide stone platform. Prioritize sculptural shapes and a clean navigable floor over decorative detail.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### style-reference.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: none
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-aef22c52-fe00-4ab0-97bb-5e17392c02a7.png`
- Note: Byte-for-byte copy of reference-candidate-02.png. Selected for readable open floor, calm silhouette hierarchy, clear amber route and restrained teal fill.

```text
Use case: stylized-concept
Asset type: finished visual-style reference for a cooperative first-person puzzle game.
Primary request: a dark underground spawn cavern with exactly one shaft of soft daylight from a small roof opening, a few warm torches marking the safe path, and sparse large glowing teal crystals providing cold fill light. View from a standing player's eye height about 1.65 m, without hands, characters or HUD. A polished stylized 3D game-render look, broad hand-painted gradients and clean simple surfaces. Big readable shapes first, medium shapes second, very little small detail. Chunky slightly lumpy rock masses, deliberately uneven silhouettes and wide soft bevels. Sparse rope wraps and broad stone chips, no grit. Mostly matte rock with simple edge highlights. Light beam is subdued daylight, not luminous ghost-white material.
Composition/framing: wide 16:9 landscape, no borders, text, logos or watermarks. Readable even at half-screen thumbnail size. Dark atmospheric but every foreground shape remains readable; tinted fog rather than crushed black. No photographic realism, microtexture, grain, noisy scratches, intricate ornament or extreme lens effects.
Color palette: torch amber #FFB347 means safe path; crystal teal #3FD0C9 means ambient crystal light; shadows and fog deep blue-violet #1E2433, never black. Cave stone mid #4A4652 and light #7A6E68. Reserve #E8B33A gold and #3FA672 jade exclusively for relics, #D6F0FF pale ghost white exclusively for ghosts, and #FF4A2A red exclusively for trap warnings. In this spawn scene there are no relics, ghosts or traps, so omit their reserved colors.
Composition choice B: a compact bowl-shaped spawn chamber, a gently raised central stepping-stone path leading to an offset arched exit. The single daylight shaft marks the center of the chamber, two torches identify the exit, sparse teal crystals balance the foreground. Calm, spatially legible composition.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-01-puzzle-chamber.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-1f7ea892-2cbc-45a4-b716-07a39c298aaf.png`

```text
Use case: stylized-concept
Asset type: finished 16:9 visual style frame for a cooperative first-person puzzle game.
Input images: Image 1 is style-reference.png, the visual style reference only. Match its chunky stone silhouette language, wide softened bevels, broad painted gradients, matte surfaces, restrained edge highlights, and warm/cool lighting balance. Create a new scene rather than copying the spawn composition. Keep surfaces even smoother than the reference: simple broad color planes, no little chips or scattered rubble, no fine surface detail. Polished stylized 3D game-render look.
Composition/framing: exactly 16:9 landscape, standing first-person-height camera about 1.65 m, no hands, people, HUD, text, border, logos or watermark. Main gameplay feature is large and readable at half-screen size.
Color palette and meanings: amber #FFB347 only for torches, braziers and safe path light; teal #3FD0C9 only for crystal ambient light; gold #E8B33A and jade #3FA672 only for relics; pale ghost white #D6F0FF only for ghosts; trap red #FF4A2A only for trap warnings. Deep blue-violet #1E2433 shadows and tinted fog, never black. Cave rock #4A4652 mids and #7A6E68 lights; Egyptian sandstone #D9A86C. Do not use reserved colors decoratively. Mostly matte except metal and relics. Minimal broad readable wear, bent wood and rope wraps only where functional. No photographic textures, grit, micro scratches, grain, realistic horror or fine noise.
Primary request: an underground torch-lit puzzle chamber. A large square inset mechanical pressure plate is clearly visible in the immediate foreground, with exact straight functional perimeter but wide uneven beveled stone edges; a heavy chunky stone statue stands just beside it, visibly ready to be moved onto it. Statue is plain blue-violet cave stone, a simple squat abstract humanoid silhouette, not a gold relic. A shut broad stone door beyond shows the goal. A few amber torches mark the route and a sparse large teal crystal cluster softly fills shadows. Plate and statue are both unmistakable and visually distinct, not merged. No glowing red or ghost-white indicators.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-02-relic-altar.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-75b0ca9b-6082-4429-b3c9-4918324cc07a.png`

```text
Use case: stylized-concept
Asset type: finished 16:9 visual style frame for a cooperative first-person puzzle game.
Input images: Image 1 is style-reference.png, the visual style reference only. Match its chunky stone silhouette language, wide softened bevels, broad painted gradients, matte surfaces, restrained edge highlights, and warm/cool lighting balance. Create a new scene rather than copying the spawn composition. Keep surfaces even smoother than the reference: simple broad color planes, no little chips or scattered rubble, no fine surface detail. Polished stylized 3D game-render look.
Composition/framing: exactly 16:9 landscape, standing first-person-height camera about 1.65 m, no hands, people, HUD, text, border, logos or watermark. Main gameplay feature is large and readable at half-screen size.
Color palette and meanings: amber #FFB347 only for torches, braziers and safe path light; teal #3FD0C9 only for crystal ambient light; gold #E8B33A and jade #3FA672 only for relics; pale ghost white #D6F0FF only for ghosts; trap red #FF4A2A only for trap warnings. Deep blue-violet #1E2433 shadows and tinted fog, never black. Cave rock #4A4652 mids and #7A6E68 lights; Egyptian sandstone #D9A86C. Do not use reserved colors decoratively. Mostly matte except metal and relics. Minimal broad readable wear, bent wood and rope wraps only where functional. No photographic textures, grit, micro scratches, grain, realistic horror or fine noise.
Primary request: a small collectible gold idol about 25 cm tall resting prominently on a chunky carved stone altar in a dark cave. Camera close enough that the idol reads immediately at thumbnail size. Idol has a simple squat humanoid silhouette, broad facial features, wide soft bevels, #E8B33A relic gold, one large restrained #3FA672 jade inset, slightly imperfect hand-carved shape and clean stylized metallic shine. Altar is neutral cave stone with just a few large shallow carvings; it is not gold. Amber torch behind and teal crystal fill. No piles of treasure or tiny ornaments. Keep the idol design suitable for the later isolated image-to-3D concept.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-03-ghost-wall.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-9317e13c-c97e-47bf-9f63-cca1f44fed98.png`

```text
Use case: stylized-concept
Asset type: finished 16:9 visual style frame for a cooperative first-person puzzle game.
Input images: Image 1 is style-reference.png, the visual style reference only. Match its chunky stone silhouette language, wide softened bevels, broad painted gradients, matte surfaces, restrained edge highlights, and warm/cool lighting balance. Create a new scene rather than copying the spawn composition. Keep surfaces even smoother than the reference: simple broad color planes, no little chips or scattered rubble, no fine surface detail. Polished stylized 3D game-render look.
Composition/framing: exactly 16:9 landscape, standing first-person-height camera about 1.65 m, no hands, people, HUD, text, border, logos or watermark. Main gameplay feature is large and readable at half-screen size.
Color palette and meanings: amber #FFB347 only for torches, braziers and safe path light; teal #3FD0C9 only for crystal ambient light; gold #E8B33A and jade #3FA672 only for relics; pale ghost white #D6F0FF only for ghosts; trap red #FF4A2A only for trap warnings. Deep blue-violet #1E2433 shadows and tinted fog, never black. Cave rock #4A4652 mids and #7A6E68 lights; Egyptian sandstone #D9A86C. Do not use reserved colors decoratively. Mostly matte except metal and relics. Minimal broad readable wear, bent wood and rope wraps only where functional. No photographic textures, grit, micro scratches, grain, realistic horror or fine noise.
Primary request: one pale translucent ghost drifting out through a solid cave wall toward the viewer. Its upper torso and reaching arms emerge through the rock face; tapering wispy lower body visibly intersects and dissolves into the wall with no hole or doorway. Hunched chunky spectral humanoid shape, two broad reaching hands, smooth simplified face with recessed blue-violet eyes, a sorrowful threatening expression without gore. Ghost material uses #D6F0FF with translucent blue-violet shaded volume, clean broad spectral ribbons rather than small particles or frayed fabric. A nearby amber torch is offset away from the ghost; faint teal crystal fill. Ghost large and clearly readable; avoid skeleton anatomy or photorealistic horror.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-04-trap-corridor.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-3a81a7f0-0ec8-4be1-886d-1f4c0048511b.png`

```text
Use case: stylized-concept
Asset type: finished 16:9 visual style frame for a cooperative first-person puzzle game.
Input images: Image 1 is style-reference.png, the visual style reference only. Match its chunky stone silhouette language, wide softened bevels, broad painted gradients, matte surfaces, restrained edge highlights, and warm/cool lighting balance. Create a new scene rather than copying the spawn composition. Keep surfaces even smoother than the reference: simple broad color planes, no little chips or scattered rubble, no fine surface detail. Polished stylized 3D game-render look.
Composition/framing: exactly 16:9 landscape, standing first-person-height camera about 1.65 m, no hands, people, HUD, text, border, logos or watermark. Main gameplay feature is large and readable at half-screen size.
Color palette and meanings: amber #FFB347 only for torches, braziers and safe path light; teal #3FD0C9 only for crystal ambient light; gold #E8B33A and jade #3FA672 only for relics; pale ghost white #D6F0FF only for ghosts; trap red #FF4A2A only for trap warnings. Deep blue-violet #1E2433 shadows and tinted fog, never black. Cave rock #4A4652 mids and #7A6E68 lights; Egyptian sandstone #D9A86C. Do not use reserved colors decoratively. Mostly matte except metal and relics. Minimal broad readable wear, bent wood and rope wraps only where functional. No photographic textures, grit, micro scratches, grain, realistic horror or fine noise.
Primary request: a cave trap corridor with one clearly visible set of broad stylized steel spikes protruding from a chunky mechanical floor plate. Wide blunt bases and pointed tips, sparse orderly spikes instead of tiny dense teeth. A clear #FF4A2A red warning glow runs around the trap plate and casts localized red light only at the danger zone. A safe ledge bypass and warm #FFB347 torches indicate where a player can move. Sparse teal crystal ambient light in the distance, blue-violet shadows throughout. Strong readable silhouettes, clean painted iron, no blood or ghost or relic colors.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-05-zipline-exit.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-84d2861d-91d2-478d-8e5f-fd308ddf6ed7.png`

```text
Use case: stylized-concept
Asset type: finished 16:9 visual style frame for a cooperative first-person puzzle game.
Input images: Image 1 is style-reference.png, the visual style reference only. Match its chunky stone silhouette language, wide softened bevels, broad painted gradients, matte surfaces, restrained edge highlights, and warm/cool lighting balance. Create a new scene rather than copying the spawn composition. Keep surfaces even smoother than the reference: simple broad color planes, no little chips or scattered rubble, no fine surface detail. Polished stylized 3D game-render look.
Composition/framing: exactly 16:9 landscape, standing first-person-height camera about 1.65 m, no hands, people, HUD, text, border, logos or watermark. Main gameplay feature is large and readable at half-screen size.
Color palette and meanings: amber #FFB347 only for torches, braziers and safe path light; teal #3FD0C9 only for crystal ambient light; gold #E8B33A and jade #3FA672 only for relics; pale ghost white #D6F0FF only for ghosts; trap red #FF4A2A only for trap warnings. Deep blue-violet #1E2433 shadows and tinted fog, never black. Cave rock #4A4652 mids and #7A6E68 lights; Egyptian sandstone #D9A86C. Do not use reserved colors decoratively. Mostly matte except metal and relics. Minimal broad readable wear, bent wood and rope wraps only where functional. No photographic textures, grit, micro scratches, grain, realistic horror or fine noise.
Primary request: the cave's exit ledge with a taut zipline spanning a large misty chasm to an amber torch-lit landing ledge and exit tunnel. The functional zipline starts from a stout rope-wrapped weathered wooden anchor frame in the near foreground. A readable trolley with pulley wheels and oversized T-bar grip hangs from the cable within reach of the viewer, neutral painted iron, muted brown grip. A single continuous cable visibly crosses the chasm to the opposite anchor. Broad teal crystals and deep blue-violet fog reveal depth; chunky uneven ledges, minimal detail. Emphasize the readable route and plausible mechanical assembly. No ghost, gold decoration or red light.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-06-egyptian-antechamber.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-1b2bbf11-1676-4b86-a93a-a06839aee71b.png`

```text
Use case: stylized-concept
Asset type: finished 16:9 visual style frame for a cooperative first-person puzzle game.
Input images: Image 1 is style-reference.png, the visual style reference only. Match its chunky stone silhouette language, wide softened bevels, broad painted gradients, matte surfaces, restrained edge highlights, and warm/cool lighting balance. Create a new scene rather than copying the spawn composition. Keep surfaces even smoother than the reference: simple broad color planes, no little chips or scattered rubble, no fine surface detail. Polished stylized 3D game-render look.
Composition/framing: exactly 16:9 landscape, standing first-person-height camera about 1.65 m, no hands, people, HUD, text, border, logos or watermark. Main gameplay feature is large and readable at half-screen size.
Color palette and meanings: amber #FFB347 only for torches, braziers and safe path light; teal #3FD0C9 only for crystal ambient light; gold #E8B33A and jade #3FA672 only for relics; pale ghost white #D6F0FF only for ghosts; trap red #FF4A2A only for trap warnings. Deep blue-violet #1E2433 shadows and tinted fog, never black. Cave rock #4A4652 mids and #7A6E68 lights; Egyptian sandstone #D9A86C. Do not use reserved colors decoratively. Mostly matte except metal and relics. Minimal broad readable wear, bent wood and rope wraps only where functional. No photographic textures, grit, micro scratches, grain, realistic horror or fine noise.
Primary request: Map 2, a small underground Egyptian sandstone antechamber warmly lit by two substantial braziers. Broad slightly uneven #D9A86C sandstone blocks, wide rounded bevels, chunky columns and a simple doorway framing the route forward. A few large shallow Egyptian-inspired carved relief shapes, not dense hieroglyph texture. Braziers are muted dark iron with #FFB347 amber flames, no decorative gold. Cool deep blue-violet shadows and softly tinted fog keep continuity with the cave. No daylight aperture, ghosts, relics or traps. Restrained intimate room, finished stylized hand-painted surfaces, spatially readable floor and large forms.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/cave-rock-1m.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-ec2a787c-a0b6-42b9-ab90-11a564dc7903.png`

```text
Use case: stylized-concept
Asset type: single-object concept image for image-to-3D.
Input images: Image 1 is style-reference.png, used ONLY to match the art style: chunky exaggerated shapes, slightly uneven silhouettes, broad soft bevels, smooth hand-painted gradients, simple clean surfaces and restrained edge highlights. Do not copy its cavern, torches or crystals into this image.
Composition/framing: just ONE isolated object, centered, three-quarter view showing front and one side, whole object fully in frame with generous 12 percent margin on all sides, square canvas. Plain uniform light-gray #E2E2E2 background. Even diffuse neutral studio lighting, no dramatic cave lighting, no cast shadow, no ground shadow, no floor plane, no pedestal, no scenic props, no text, dimensions, labels, watermark or border. Broad painted shading on the object itself is allowed. Clean silhouette for image-to-3D reconstruction. No photographic textures, grit, grain, microdetail or fine noise. Mostly matte with simple large color transitions, dark base to lighter top. Colored blue-violet shading #1E2433 rather than pure black.
Primary request: one chunky slightly lumpy cave boulder, about 1 m across, a single connected mass rather than a pile of rocks. A few big rounded uneven rock faces and wide soft bevels, asymmetrical squat silhouette, modest broad chips. Base stone #4A4652, lighter top planes #7A6E68, simple blue-violet lower shading. No crystals, plants, gold, teal emissive color, tiny cracks or debris.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/gold-idol-25cm.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-e6219a27-dfd7-4337-957e-efc0c25ae849.png`

```text
Use case: stylized-concept
Asset type: single-object concept image for image-to-3D.
Input images: Image 1 is style-reference.png, used ONLY to match the art style: chunky exaggerated shapes, slightly uneven silhouettes, broad soft bevels, smooth hand-painted gradients, simple clean surfaces and restrained edge highlights. Do not copy its cavern, torches or crystals into this image.
Composition/framing: just ONE isolated object, centered, three-quarter view showing front and one side, whole object fully in frame with generous 12 percent margin on all sides, square canvas. Plain uniform light-gray #E2E2E2 background. Even diffuse neutral studio lighting, no dramatic cave lighting, no cast shadow, no ground shadow, no floor plane, no pedestal, no scenic props, no text, dimensions, labels, watermark or border. Broad painted shading on the object itself is allowed. Clean silhouette for image-to-3D reconstruction. No photographic textures, grit, grain, microdetail or fine noise. Mostly matte with simple large color transitions, dark base to lighter top. Colored blue-violet shading #1E2433 rather than pure black.
Primary request: one small gold idol about 25 cm tall. Simple squat humanoid figure with oversized squared head, big circular inset eyes, broad rectangular nose, a single simple mouth, stubby arms bent around one big circular jade medallion centered on its belly, two wide squat feet. Match the relic frame design description. Chunky hand-carved proportions and broad soft slightly irregular bevels, clean stylized metal shine in #E8B33A relic gold, the single jade insert #3FA672. Minimal large readable grooves, no fine etching, no gemstones beyond that single jade disk, no altar.
Refinement: surfaces must be very smooth, with ONE broad gradient per large shape; rounded bevels, no mosaic-like polygon paint patches, mottled highlights, hammered-metal dents or granular gold. The jade disk is smooth polished jade, not a faceted gemstone. Use simple broad gleaming edge highlights and muted blue-violet shaded gold. Keep this an expertly finished stylized painted object, not visibly low-poly triangulated surfaces.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/ghost-hunched.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-c4d5b623-7657-4600-bbfb-668afbc73dfb.png`

```text
Use case: stylized-concept
Asset type: single-object concept image for image-to-3D.
Input images: Image 1 is style-reference.png, used ONLY to match the art style: chunky exaggerated shapes, slightly uneven silhouettes, broad soft bevels, smooth hand-painted gradients, simple clean surfaces and restrained edge highlights. Do not copy its cavern, torches or crystals into this image.
Composition/framing: just ONE isolated object, centered, three-quarter view showing front and one side, whole object fully in frame with generous 12 percent margin on all sides, square canvas. Plain uniform light-gray #E2E2E2 background. Even diffuse neutral studio lighting, no dramatic cave lighting, no cast shadow, no ground shadow, no floor plane, no pedestal, no scenic props, no text, dimensions, labels, watermark or border. Broad painted shading on the object itself is allowed. Clean silhouette for image-to-3D reconstruction. No photographic textures, grit, grain, microdetail or fine noise. Mostly matte with simple large color transitions, dark base to lighter top. Colored blue-violet shading #1E2433 rather than pure black.
Primary request: ONE stylized pale ghost, hunched forward, broad shoulders and two chunky reaching arms with simplified separated fingers, large hands 15-20 percent oversized. A smooth simplified mournful angular face with blue-violet recessed eyes, no skull or bones. Both arms visible in three-quarter view. Torso narrows continuously into ONE tapering wispy lower body curling into a single broad pointed tail, no feet and no detached vapor. Translucent #D6F0FF ghost-white material with broad pale blue-violet shading and a few large spectral folds, cohesive readable connected volume, no fine wisps, frayed threads, particles, smoke cloud, grain or aura outside the silhouette. Even lighting must preserve strong contour against the gray background.
Refinement: use a fleshy smooth simplified human face with a broad nose, closed downturned mouth, rounded full cheeks and soft blue-violet eyes. Absolutely no skull-shaped face, skeletal eye sockets, hollow triangular nasal cavity, open scream mouth or exposed teeth. The hunched body has one cohesive rounded volume and a few broad spectral curves. Surfaces use continuous smooth gradients, not polygonal mosaic paint patches. Leave at least 10 percent blank margin around the whole ghost.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/ghost-hooded.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-e9c4aadc-3dea-44d7-b445-c038709cba5e.png`

```text
Use case: stylized-concept
Asset type: single-object concept image for image-to-3D.
Input images: Image 1 is style-reference.png, used ONLY to match the art style: chunky exaggerated shapes, slightly uneven silhouettes, broad soft bevels, smooth hand-painted gradients, simple clean surfaces and restrained edge highlights. Do not copy its cavern, torches or crystals into this image.
Composition/framing: just ONE isolated object, centered, three-quarter view showing front and one side, whole object fully in frame with generous 12 percent margin on all sides, square canvas. Plain uniform light-gray #E2E2E2 background. Even diffuse neutral studio lighting, no dramatic cave lighting, no cast shadow, no ground shadow, no floor plane, no pedestal, no scenic props, no text, dimensions, labels, watermark or border. Broad painted shading on the object itself is allowed. Clean silhouette for image-to-3D reconstruction. No photographic textures, grit, grain, microdetail or fine noise. Mostly matte with simple large color transitions, dark base to lighter top. Colored blue-violet shading #1E2433 rather than pure black.
Primary request: ONE stylized hooded ghost figure in three-quarter view. Oversized soft hood with thick broad rounded rim around a recessed simple blue-violet face, two subtle pale eyes, chunky shoulders, two simple draped arms held slightly apart from the body. One connected flowing ghost robe volume that narrows into ONE tapering wispy lower body with a gently curled pointed tail, no feet. Translucent #D6F0FF ghost-white spectral material, broad pale blue-violet shaded folds, no black face cavity. A small number of smooth large readable folds, no woven cloth texture, frayed hems, tiny wisps, detached particles, smoky cloud, fine noise or aura outside silhouette. Preserve strong contour on the gray background.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/zipline-trolley.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-5351671c-ff27-494a-b2dc-d616644a348d.png`

```text
Use case: stylized-concept
Asset type: single-object concept image for image-to-3D.
Input images: Image 1 is style-reference.png, used ONLY to match the art style: chunky exaggerated shapes, slightly uneven silhouettes, broad soft bevels, smooth hand-painted gradients, simple clean surfaces and restrained edge highlights. Do not copy its cavern, torches or crystals into this image.
Composition/framing: just ONE isolated object, centered, three-quarter view showing front and one side, whole object fully in frame with generous 12 percent margin on all sides, square canvas. Plain uniform light-gray #E2E2E2 background. Even diffuse neutral studio lighting, no dramatic cave lighting, no cast shadow, no ground shadow, no floor plane, no pedestal, no scenic props, no text, dimensions, labels, watermark or border. Broad painted shading on the object itself is allowed. Clean silhouette for image-to-3D reconstruction. No photographic textures, grit, grain, microdetail or fine noise. Mostly matte with simple large color transitions, dark base to lighter top. Colored blue-violet shading #1E2433 rather than pure black.
Primary request: ONE functional stylized zipline trolley assembly with two chunky grooved pulley wheels in tandem, both rolling on the SAME straight cable axis, supported by one broad simple metal side plate and an open opposite bracket. A vertical sturdy stem drops from the plate to an oversized horizontal T-bar grip, brown wrapped handle 15-20 percent larger than real life for first-person visibility. Three-quarter angle clearly reveals both wheel grooves, two wheel axles, bracket and grip without overlap hiding key parts. No cable or anchor structure, just the detachable trolley. Exact functional wheel alignment and axle geometry, slightly uneven wide outer bevels. Neutral muted blue-violet painted iron and muted brown handle wrap, clean medium bevels and very few large bolts, subdued metallic highlights. No gold, jade, ghost-white, red glow, crystals, branding, fine rust, tiny scratches, dangling rope or decorative gears.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/gold-idol-25cm-first-pass.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-48c550bd-c9c9-44a8-893f-5cb0a0e36cc4.png`
- Note: Superseded: excess faceted paint patches, smooth revision preferred.

```text
Use case: stylized-concept
Asset type: single-object concept image for image-to-3D.
Input images: Image 1 is style-reference.png, used ONLY to match the art style: chunky exaggerated shapes, slightly uneven silhouettes, broad soft bevels, smooth hand-painted gradients, simple clean surfaces and restrained edge highlights. Do not copy its cavern, torches or crystals into this image.
Composition/framing: just ONE isolated object, centered, three-quarter view showing front and one side, whole object fully in frame with generous 12 percent margin on all sides, square canvas. Plain uniform light-gray #E2E2E2 background. Even diffuse neutral studio lighting, no dramatic cave lighting, no cast shadow, no ground shadow, no floor plane, no pedestal, no scenic props, no text, dimensions, labels, watermark or border. Broad painted shading on the object itself is allowed. Clean silhouette for image-to-3D reconstruction. No photographic textures, grit, grain, microdetail or fine noise. Mostly matte with simple large color transitions, dark base to lighter top. Colored blue-violet shading #1E2433 rather than pure black.
Primary request: one small gold idol about 25 cm tall. Simple squat humanoid figure with oversized squared head, big circular inset eyes, broad rectangular nose, a single simple mouth, stubby arms bent around one big circular jade medallion centered on its belly, two wide squat feet. Match the relic frame design description. Chunky hand-carved proportions and broad soft slightly irregular bevels, clean stylized metal shine in #E8B33A relic gold, the single jade insert #3FA672. Minimal large readable grooves, no fine etching, no gemstones beyond that single jade disk, no altar.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/ghost-hunched-first-pass.png

- Tool: image_gen.imagegen (built-in; model identifier not exposed)
- Reference image: `/Users/peterkim/CoopGameArt/style-frames/style-reference.png` (sole image input)
- Original tool output: `/Users/peterkim/.codex/generated_images/01a12359-a3f1-7913-96d0-9c010df9b15a/exec-62169977-a9a7-4e88-b37b-389e9838f126.png`
- Note: Superseded: skull-like facial silhouette, non-skeletal revision preferred.

```text
Use case: stylized-concept
Asset type: single-object concept image for image-to-3D.
Input images: Image 1 is style-reference.png, used ONLY to match the art style: chunky exaggerated shapes, slightly uneven silhouettes, broad soft bevels, smooth hand-painted gradients, simple clean surfaces and restrained edge highlights. Do not copy its cavern, torches or crystals into this image.
Composition/framing: just ONE isolated object, centered, three-quarter view showing front and one side, whole object fully in frame with generous 12 percent margin on all sides, square canvas. Plain uniform light-gray #E2E2E2 background. Even diffuse neutral studio lighting, no dramatic cave lighting, no cast shadow, no ground shadow, no floor plane, no pedestal, no scenic props, no text, dimensions, labels, watermark or border. Broad painted shading on the object itself is allowed. Clean silhouette for image-to-3D reconstruction. No photographic textures, grit, grain, microdetail or fine noise. Mostly matte with simple large color transitions, dark base to lighter top. Colored blue-violet shading #1E2433 rather than pure black.
Primary request: ONE stylized pale ghost, hunched forward, broad shoulders and two chunky reaching arms with simplified separated fingers, large hands 15-20 percent oversized. A smooth simplified mournful angular face with blue-violet recessed eyes, no skull or bones. Both arms visible in three-quarter view. Torso narrows continuously into ONE tapering wispy lower body curling into a single broad pointed tail, no feet and no detached vapor. Translucent #D6F0FF ghost-white material with broad pale blue-violet shading and a few large spectral folds, cohesive readable connected volume, no fine wisps, frayed threads, particles, smoke cloud, grain or aura outside the silhouette. Even lighting must preserve strong contour against the gray background.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

