# Shared style anchor — v3

Seven style frames and five isolated object concepts. All new images use the same built-in image generation tool as the selected v1 set. `transparent_background` was `false` on every new call. The tool does not expose its underlying model name or revision. Our own generated artwork; no third-party assets or credits required.

The shared reference removes the glowing animal and red sun glyph. Frame 01 changes the decorative jade cat and its plinth to matte stone. The other five selected v1 frames are copied without pixel changes, including the corrected underground torch chamber and ghost-free sandstone chamber.

## File names and scene subjects

The frame filenames describe the selected v1 scenes. The titles below identify each image's subject. `ghost-sheet.png` is the requested rounded sheet variant.

| File | Actual subject |
| --- | --- |
| `style-reference.png` | 00 / Shared style reference |
| `frame-01-spawn-cavern.png` | 01 / Cave spawn cavern |
| `frame-02-torch-chamber.png` | 02 / Torch-lit chamber |
| `frame-03-relic-altar.png` | 03 / Relic on an altar |
| `frame-04-ghost-corridor.png` | 04 / Ghost in a corridor |
| `frame-05-pressure-plates.png` | 05 / Pressure-plate puzzle |
| `frame-06-egyptian-antechamber.png` | 06 / Map 2 sandstone antechamber |
| `concepts/cave-rock-1m.png` | Cave rock / approximately 1 m |
| `concepts/gold-idol-25cm.png` | Gold lion idol / approximately 25 cm |
| `concepts/ghost-sheet.png` | Rounded sheet ghost |
| `concepts/ghost-hunched.png` | Hunched reaching ghost |
| `concepts/zipline-trolley.png` | Two-wheel zipline trolley with T-bar |

## Exact prompts and image inputs

### style-reference.png

00 / Shared style reference.

v3 localized removal edit; the input reference ancestry is recorded below.

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference.png`

Exact prompt:

```text
Edit the supplied shared game style reference, preserving its exact wide 16:9 composition, camera, large foreground cave boulder on the left, gold lion relic with its single jade chest inset on the altar at the right, rope-bound timber torch support, teal crystal clusters, floor path and blue-violet cave shadows. Make two localized removals only: completely remove the pale blue-white glowing animal statue/creature in the high far-right alcove, replacing it with an empty dim blue-violet stone recess and its ordinary stone shelf; completely remove the red sun glyph on the far central wall, replacing the entire glyph with uninterrupted plain blue-violet stone. No replacement character, statue, symbol, light or decorative prop in those two areas. Remove the local glow cast by the removed creature. Keep the existing warm amber key light, teal ambient fill, brightness, smooth painted gradients, big-medium-small lumpy masses and wide soft bevels. Relic gold and jade occur only on the foreground collectible lion idol. No ghost-white object or trap-red mark anywhere. No text, border or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-01-spawn-cavern.png

01 / Cave spawn cavern.

Original v1 scene generation:

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference.png`

Exact prompt:

```text
Use case: stylized-concept.
Asset type: visual target for a finished stylized 3D co-op puzzle game.
Output: one landscape 16:9 frame. Clean smooth hand-painted surfaces, broad bevels, substantial slightly uneven forms, clear silhouettes at half-screen size. No fine grain, speckles, photographic texture, labels or UI.
Input image 1 is the shared style reference: carry over its palette, shape language, smooth material finish and warm/cool lighting balance, while creating the scene and composition specified below.

Using the attached style reference for shapes, materials and lighting, create an eye-level 16:9 frame of the first underground spawn cavern, about 30 meters wide with a 12-meter ceiling. The room feels welcoming but mysterious. In the left-midground, one crack in the ceiling admits a broad shaft of shaded daylight onto four separated safe standing spots; a chunky start pad and the eastbound passage form the main readable route to the right. A smaller north passage recedes into cool shadow without competing with the route. Use lumpy rocks with broad shoulders and a few soft chipped edges, #4A4652 mid stone rising to #7A6E68 on upper planes. Keep #1E2433 blue-violet shadows and gentle fog. Amber #FFB347 torches lead toward the start pad and exit; sparse #3FD0C9 crystals provide cold fill away from the main light pool. Two small optional tutorial relics sit in side nooks, using gold #E8B33A and jade #3FA672 only on those relics. Props have thick rope wraps and bent timber, with broad painted gradients, no fine cracks or surface grain. The route remains the brightest environmental feature and the layout remains readable at half-screen size. No ghost, trap-red decoration, words or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

v3 stone-statue edit:

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/01_spawn_cavern.png`

Exact prompt:

```text
Edit only the small green cat statue and its green plinth in the far-right wall alcove of the supplied cave spawn cavern. Make the statue and plinth ordinary matte gray-violet cave stone, using stone mid #4A4652 and stone light #7A6E68 with blue-violet #1E2433 in the shaded surfaces. Preserve the cat shape, pose, size and position; it is plain carved stone decoration, without jade, teal, gold, emission or jewel details. Keep every other part of the image unchanged: exact wide 16:9 composition and camera, daylight shaft, four player arrival stones, central spawn platform, amber torches and warm route on the right, teal crystal clusters, blue-violet shadow corridor, left gold collectible lion idol with its jade inset, timber and rope, lumpy cave walls, broad bevels and smooth painted gradients. No new props, characters, symbols, text or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-02-torch-chamber.png

02 / Torch-lit chamber.

Copied unchanged from `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/02_torch_chamber_v2.png`.

Generation stage 1:

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference.png`

Exact prompt:

```text
Use case: stylized-concept.
Asset type: visual target for a finished stylized 3D co-op puzzle game.
Output: one landscape 16:9 frame. Clean smooth hand-painted surfaces, broad bevels, substantial slightly uneven forms, clear silhouettes at half-screen size. No fine grain, speckles, photographic texture, labels or UI.
Input image 1 is the shared style reference: carry over its palette, shape language, smooth material finish and warm/cool lighting balance, while creating the scene and composition specified below.

Using the attached style reference, create a finished 16:9 eye-level frame looking through a cave chamber toward its open east gate. The chamber is built from heavy uneven cave stone, with large wall masses, medium shelves and only a few broad old chips. Worn timber supports are slightly bent, with thick rope wraps and patched broad planks. A close foreground torch and two distant torches create separate pools of #FFB347 amber light, with the brightest environmental pool at the gate; #3FD0C9 crystal light gently outlines the opposite wall. Stone uses #4A4652 and #7A6E68, darker at the base and brighter on upper planes, with #1E2433 blue-violet shadows and tinted haze between depth layers. Wide bevels catch soft highlights; nearly everything is matte. Keep the central path uncluttered and silhouettes legible at half-screen size. Do not introduce gold or jade ornament, ghost-white trim, trap-red paint, noisy rock texture, characters, text or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

Generation stage 2:

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/02_torch_chamber.png`

Exact prompt:

```text
Edit only the area beyond the open timber-framed gate in this torch-lit underground cave chamber. Replace the outdoor sky, mountains and daylight landscape seen through that gate with another fully enclosed underground cave chamber: broad lumpy matte blue-violet stone walls and ceiling, a clear continuation of the walking path, amber torchlight illuminating that safe route, restrained teal cold fill and soft colored haze in the distance. There must be no sky, outdoor landscape, sun or exterior opening behind this gate. Keep that gate's destination as the brightest environmental light pool by using warm underground torchlight rather than daylight. Preserve everything in the foreground and current chamber: camera, 16:9 frame, torches, crystals, timber/rope supports, barrels, rock shapes, palette, smooth painted material finish, and broad bevels. No new characters, relics, signs, text or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-03-relic-altar.png

03 / Relic on an altar.

Copied unchanged from `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/03_relic_altar.png`.

Generation stage 1:

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference.png`

Exact prompt:

```text
Use case: stylized-concept.
Asset type: visual target for a finished stylized 3D co-op puzzle game.
Output: one landscape 16:9 frame. Clean smooth hand-painted surfaces, broad bevels, substantial slightly uneven forms, clear silhouettes at half-screen size. No fine grain, speckles, photographic texture, labels or UI.
Input image 1 is the shared style reference: carry over its palette, shape language, smooth material finish and warm/cool lighting balance, while creating the scene and composition specified below.

Using the attached style reference, create a 16:9 three-quarter close scene of a small 25-centimeter gold guardian idol on a substantial waist-height cave altar. The idol has a squat body, oversized angular head, slightly unequal crown lobes, a broad carved nose, simple recessed eyes and mouth, wide rounded edges and one large worn chip. Its silhouette must read immediately when the frame is reduced. Use relic gold #E8B33A with a darker shaded gold-violet base and a light warm top; one broad jade #3FA672 inset may appear, but only on the relic. Give the metal broad soft shiny highlights, not microscopic scratches. The altar's level contact surface is precise and broad while its sides are uneven chipped stone, matte #4A4652 rising to #7A6E68, with #1E2433 shadow tint. Amber #FFB347 torchlight leads the eye to the relic; cold #3FD0C9 ambient fill separates it from the wall. Show a quiet section of the eastern gate in the distance to establish gameplay context. No decorative gold outside the relic, ghost-white paint, trap-red accents, fine glyphs, words or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-04-ghost-corridor.png

04 / Ghost in a corridor.

Copied unchanged from `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/04_ghost_corridor.png`.

Generation stage 1:

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference.png`

Exact prompt:

```text
Use case: stylized-concept.
Asset type: visual target for a finished stylized 3D co-op puzzle game.
Output: one landscape 16:9 frame. Clean smooth hand-painted surfaces, broad bevels, substantial slightly uneven forms, clear silhouettes at half-screen size. No fine grain, speckles, photographic texture, labels or UI.
Input image 1 is the shared style reference: carry over its palette, shape language, smooth material finish and warm/cool lighting balance, while creating the scene and composition specified below.

Using the attached style reference, create a 16:9 first-person-height frame of a pale humanoid ghost in the north passage off the spawn cavern, a narrow three-meter-wide cave corridor. The ghost floats above the floor with an oversized simple head and a broad tapering body, a few substantial flowing silhouette folds and minimal facial detail. It is translucent #D6F0FF ghost white, faintly luminous, with soft fading edges; its inner mass remains readable against colored darkness. Suggest a gentle drifting motion through posture, not blur. Keep ghost white entirely on the ghost. Surround it with lumpy broad-beveled #4A4652 / #7A6E68 rock, #1E2433 blue-violet shadow and restrained tinted fog. A nearby #FFB347 torch makes the safe side of the passage clear, while sparse #3FD0C9 crystals provide a quiet cool edge light. Do not let bloom flatten the ghost into an unreadable white blob; show depth and separation at half-screen size. No photoreal horror, tiny tendrils, gold decoration, trap-red decoration, player arms, words or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-05-pressure-plates.png

05 / Pressure-plate puzzle.

Copied unchanged from `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/05_pressure_plate_puzzle.png`.

Generation stage 1:

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference.png`

Exact prompt:

```text
Use case: stylized-concept.
Asset type: visual target for a finished stylized 3D co-op puzzle game.
Output: one landscape 16:9 frame. Clean smooth hand-painted surfaces, broad bevels, substantial slightly uneven forms, clear silhouettes at half-screen size. No fine grain, speckles, photographic texture, labels or UI.
Input image 1 is the shared style reference: carry over its palette, shape language, smooth material finish and warm/cool lighting balance, while creating the scene and composition specified below.

Using the attached style reference, create a 16:9 raised eye-level gameplay composition of a 30-meter cave plate hall with four separated pressure plates arranged as two near and two far positions. The east gate is the clearest destination; three big carved statue alcoves occupy the north wall. Plates are thick substantial mechanical slabs with exact flat contact surfaces and square footprints, readable large symbols, uneven wide bevels and a few painted worn edges on top of their precise proportions. Use only cave stone #4A4652 and #7A6E68 on the mechanisms, with bent timber and thick rope where appropriate. Amber #FFB347 torches mark the gate and safe route; #3FD0C9 crystals give soft opposite-side fill. Keep blue-violet #1E2433 in shadows and haze, smooth dark-bottom-to-light-top gradients, big wall masses and sparse medium detail. Allow enough empty floor around each plate that four players could stand separately; show the puzzle clearly even when the image is half-screen size. No relic-gold ornament, jade plate coding, ghost-white puzzle trim, trap-red activation lights, tiny symbols, readable text or HUD. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### frame-06-egyptian-antechamber.png

06 / Map 2 sandstone antechamber.

Copied unchanged from `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/06_sandstone_antechamber_v2.png`.

Generation stage 1:

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference.png`

Exact prompt:

```text
Use case: stylized-concept.
Asset type: visual target for a finished stylized 3D co-op puzzle game.
Output: one landscape 16:9 frame. Clean smooth hand-painted surfaces, broad bevels, substantial slightly uneven forms, clear silhouettes at half-screen size. No fine grain, speckles, photographic texture, labels or UI.
Input image 1 is the shared style reference: carry over its palette, shape language, smooth material finish and warm/cool lighting balance, while creating the scene and composition specified below.

Using the attached style reference to preserve the same finish, create a 16:9 eye-level scene of a compact Egyptian-inspired sandstone antechamber, 20 meters square with an eight-meter ceiling. Two squat chunky braziers stand near the far wall and frame a broad sealed door with a few large original carved pictograms. Four clear arrival spots occupy the near floor. Sandstone #D9A86C replaces the cave rock as the main material, shaded darker and cooler at the base with smoothly painted warmer upper planes; use #1E2433 blue-violet for deep shadows and restrained fog rather than black. All blocks and pillars are slightly uneven with broad worn bevels, large chipped corners and readable big-medium-small form hierarchy. Braziers glow #FFB347 amber and make the sealed door the brightest environmental target. Use only a restrained #3FD0C9 cool fill in deeper recesses. Stone and wood remain matte, with no fine grain or dirt. No gold or jade architectural ornament, white glowing glyphs, trap-red decoration, camels, ornate filigree, real historical text, labels or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

Generation stage 2:

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/06_sandstone_antechamber.png`

Exact prompt:

```text
Edit only the far-right recessed alcove behind the sandstone pillar in this antechamber. Remove the pale blue translucent animal/ghost standing in that alcove and replace its occupied area with an empty dim blue-violet stone recess continuous with the surrounding masonry. There must be no ghost, animal or character in this room. Preserve everything else: 16:9 composition, sandstone blocks and pillars, their broad painted gradients, four near-floor arrival markers, the centered sealed door and its large carved pictograms, both amber braziers, restrained teal cold fill on the opposite side, soft bevels, lighting and camera. No additional decorative objects, words, labels or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/cave-rock-1m.png

Cave rock / approximately 1 m.

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v3/style-reference.png`

Exact prompt:

```text
Create one isolated object concept for Meshy image-to-3D. Use the supplied shared reference for its finished stylized 3D shape language, broad soft bevels, smooth painted gradients and simple palette. Transfer the object style into a square studio product view; do not reproduce the cave scene or its dramatic colored lighting. One object only, centered, clear three-quarter view, full object visible with generous margin on every side. Solid uniform light-gray #D9D9D9 background, no floor plane or horizon, no cast shadow or contact shadow beneath or beside the object. Even diffuse neutral studio illumination, restrained surface highlights, crisp silhouette and readable geometry. No text, labels, dimensions, ruler, reference capsule, UI, border, other object or scenery. Subject: a single roughly one-meter cave boulder, broad squat mass with a stable nearly flat base. Strong big-medium-small hierarchy: one large asymmetrical domed body, two or three medium lumpy shoulders, very few small broad chips. Rounded chunky planar surfaces, wide bevels and slightly uneven silhouette; neither a perfect sphere nor many tiny polygons. Matte stone mid #4A4652 and stone light #7A6E68, painted dark blue-violet #1E2433 at the base smoothly rising to lighter gray-violet on the upper surfaces. Keep the stone finish smooth and spacious, without cracks, speckles, fine facets, moss, crystals, markings or precious materials. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/gold-idol-25cm.png

Gold lion idol / approximately 25 cm.

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v3/style-reference.png`
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/03_relic_altar.png`

Exact prompt:

```text
Create one isolated object concept for Meshy image-to-3D. Use the supplied shared reference for its finished stylized 3D shape language, broad soft bevels, smooth painted gradients and simple palette. Transfer the object style into a square studio product view; do not reproduce the cave scene or its dramatic colored lighting. One object only, centered, clear three-quarter view, full object visible with generous margin on every side. Solid uniform light-gray #D9D9D9 background, no floor plane or horizon, no cast shadow or contact shadow beneath or beside the object. Even diffuse neutral studio illumination, restrained surface highlights, crisp silhouette and readable geometry. No text, labels, dimensions, ruler, reference capsule, UI, border, other object or scenery. Subject: one small collectible gold lion guardian idol, approximately 25 cm tall, closely following the gold lion in both references. Sitting compactly on its own flat-bottomed haunches with oversized front paws, broad square-rounded head, short thick muzzle, rounded small ears, large simple brow, broad recessed mouth and a short chunky mane formed from a few medium lobes. Slightly uneven hand-carved volumes and broad soft bevels. Metal color relic gold #E8B33A, rich darker golden brown at the base and soft pale gold on top; one large circular jade #3FA672 jewel inset in the chest, clearly part of this collectible relic. Simple broad facial carving and limb divisions; no fine filigree, etched spirals, fur strands or granular wear. One connected idol only, no altar or separate display stand. Soft metallic highlights show the forms without hard bright white glare. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/ghost-sheet.png

Rounded sheet ghost.

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v3/style-reference.png`
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/04_ghost_corridor.png`

Exact prompt:

```text
Create one isolated object concept for Meshy image-to-3D. Use the supplied shared reference for its finished stylized 3D shape language, broad soft bevels, smooth painted gradients and simple palette. Transfer the object style into a square studio product view; do not reproduce the cave scene or its dramatic colored lighting. One object only, centered, clear three-quarter view, full object visible with generous margin on every side. Solid uniform light-gray #D9D9D9 background, no floor plane or horizon, no cast shadow or contact shadow beneath or beside the object. Even diffuse neutral studio illumination, restrained surface highlights, crisp silhouette and readable geometry. No text, labels, dimensions, ruler, reference capsule, UI, border, other object or scenery. Subject: a friendly eerie simple rounded sheet ghost based on the ghost silhouette in the corridor reference. One large rounded head flowing into a broad draped sheet body, two simple small pale blue luminous eyes, no mouth, two short rounded raised side flaps suggesting arms. Only three or four large soft vertical folds. The lower half narrows smoothly into one broad curved tapering wispy tail with a clearly visible pointed end; no legs or feet, no separate smoke wisps. Reserved ghost-white #D6F0FF with blue-violet tinted lower folds and a smooth pale blue-to-white upward gradient. Suggest softly spectral material with a slightly translucent rim, while keeping the main volume sufficiently opaque, continuous and clearly bounded for image-to-3D. No bloom, surrounding glow cloud or particles; retain a clean readable silhouette against the gray. No hood accessories, cloth weave or fine wrinkles. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/ghost-hunched.png

Hunched reaching ghost.

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v3/style-reference.png`

Exact prompt:

```text
Create one isolated object concept for Meshy image-to-3D. Use the supplied shared reference for its finished stylized 3D shape language, broad soft bevels, smooth painted gradients and simple palette. Transfer the object style into a square studio product view; do not reproduce the cave scene or its dramatic colored lighting. One object only, centered, clear three-quarter view, full object visible with generous margin on every side. Solid uniform light-gray #D9D9D9 background, no floor plane or horizon, no cast shadow or contact shadow beneath or beside the object. Even diffuse neutral studio illumination, restrained surface highlights, crisp silhouette and readable geometry. No text, labels, dimensions, ruler, reference capsule, UI, border, other object or scenery. Subject: a single hunched spectral ghost with a large rounded head bowed forward, broad sloping shoulders and a curved leaning torso. Two thick arms reach forward and slightly apart, both visible in three-quarter view and separated from the torso in silhouette; simple chunky hands each with three broad finger-like lobes, no spindly fingers. Two small pale blue luminous eyes under a simple heavy brow, no open mouth or sharp teeth. The lower torso narrows into one continuous broad curved tapering wispy tail with a visible pointed tip; no legs, feet, separate smoke wisps, torn strips or disconnected pieces. Reserved ghost-white #D6F0FF on the upper volume, cool blue-violet in the lower shaded folds, with broad smooth painted gradients. A slightly translucent rim suggests a ghost, but the core and reaching arms remain opaque enough and clearly bounded for image-to-3D. Large smooth forms with very few folds, wide soft bevels, no cloth weave, fine wrinkles, particles, bloom or surrounding halo. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

### concepts/zipline-trolley.png

Two-wheel zipline trolley with T-bar.

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v3/style-reference.png`

Exact prompt:

```text
Create one isolated object concept for Meshy image-to-3D. Use the supplied shared reference for its finished stylized 3D shape language, broad soft bevels, smooth painted gradients and simple palette. Transfer the object style into a square studio product view; do not reproduce the cave scene or its dramatic colored lighting. One object only, centered, clear three-quarter view, full object visible with generous margin on every side. Solid uniform light-gray #D9D9D9 background, no floor plane or horizon, no cast shadow or contact shadow beneath or beside the object. Even diffuse neutral studio illumination, restrained surface highlights, crisp silhouette and readable geometry. No text, labels, dimensions, ruler, reference capsule, UI, border, other object or scenery. Subject: a single hand-held zipline trolley built as one connected chunky mechanical assembly. Exactly TWO large grooved pulley wheels mounted at the very top, in a front-to-back tandem line on a compact open metal frame. Use a three-quarter side view that clearly reveals both circular wheel faces, their thick rims and simple visible axle hubs; the second wheel is offset in perspective, not hidden. A thick central hanger stem descends below the wheel frame to an oversized horizontal T-bar grip, with two broad rounded hand-grip ends extending left and right from the stem. Make the T-bar easy to hold with two hands and unmistakable in silhouette. The entire two-wheel frame, stem and T-bar belong to one connected object. Charcoal blue-violet painted steel #1E2433 and muted slate metal with warm brown wooden grip ends and broad tan rope wraps; simple restrained steel highlights. Wide softened edges, a little hand-built unevenness in the finish, mechanically coherent wheel axles and sturdy thick components. No gold, jade, ghost-white or red warning paint. No cable, suspended track, rider, extra wheel, trigger, motor, backpack, attachment scenery or separate parts. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

## Prior shared-reference ancestry

This records the earlier text generation and simplification used by all copied v1 scenes. The prior reference contains reserved-color objects that the v3 removal edit above replaces.

Original output: `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference_v1.png`.

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- None; original image generated from text.

Exact prompt:

```text
Use case: stylized-concept.
Asset type: shared style reference for a finished stylized 3D co-op puzzle game. Render a single landscape 16:9 frame, no collage or text. Smooth hand-painted 3D surfaces, broad readable geometry and colored shadows. This is a visual target for in-game assets, with restrained detail and clear forms when reduced to half-screen size.

Create one finished 16:9 visual reference image for an underground cooperative puzzle adventure, an eye-level three-quarter view of a small cave chamber with a clear quiet composition. A one-meter lumpy stone boulder fills the left foreground, an old broad-beveled stone altar holds a 25-centimeter chunky carved gold guardian idol on the right, and a worn rope-bound timber torch lights a simple open passage in the rear center. Establish the same visual language everywhere: asymmetrical silhouettes, exaggerated substantial shapes, big planes interrupted by medium shoulders and a few broad chips, softened wide edges, slightly bent timber, thick rope wraps, smooth painted color shifts from dark bottoms to lighter tops, broad restrained edge highlights. Stone uses mid #4A4652 and light #7A6E68, with blue-violet #1E2433 in shadow and gentle tinted fog. The torch is amber #FFB347 and lights the way forward; sparse crystals supply teal #3FD0C9 fill. Only the idol uses gold #E8B33A; a single broad inset on the idol may use relic jade #3FA672. Stone and wood are matte, gold has soft shiny glints. Keep shadow color visible and shapes readable even in darkness. A small alcove in the distant right contains a faint translucent ghost silhouette in #D6F0FF; a distant inactive spike warning has one restrained #FF4A2A mark. These semantic accents stay isolated to those objects. Prioritize the rock, idol, lighting and material finish as the reusable reference for all later art, with no human characters, labels, layout grid or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

Simplified v1 output: `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference.png`.

Tool: `image_gen.imagegen (ChatGPT built-in image generation)`.

Reference image inputs (in order):
- `/Users/peterkim/CoopGameArt/candidates/PG-A0/style-frames-v1/00_style_reference_v1.png`

Exact prompt:

```text
Use case: stylized-concept, surface-detail simplification of the supplied shared game style reference. Preserve the wide 16:9 composition, viewpoint, boulder/altar/idol sizes and positions, cave route, amber torch and teal fill, blue-violet shadows, crystals, and the placement of the distant ghost and trap warning. Change only the amount and scale of surface detail: simplify the boulder and cave walls into a few large lumpy planar masses with medium shoulders and very few broad chips; remove clusters of tiny rubble and fine facets, leaving clean spacious floor planes. Simplify the gold idol's decorative carving into large chunky head/body/limb volumes with simple recessed facial features and at most one broad jade inset. Keep its gold metal finish, and keep the stone matte. All surfaces should have smooth hand-painted color gradients with wide soft bevels. No etched filigree, granular texture, speckles, tiny cracks, brush grain or photographic wear. Preserve the lit route and visible colored shadow floor. No text, labels, border or UI. stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
```

## Contact sheet

`contact-sheet.png` is a review composite, not a generated concept. Tool: Python 3 and Pillow. Inputs: the twelve PNGs in the table above, in that order. No image-generation prompt. Rebuild with `python3 scripts/build_contact_sheet.py` from this folder, using a Python environment with Pillow installed.

## Review and next step

The five concepts are centered isolated whole-object views on a plain light-gray background, with even studio lighting and no floor cast shadows. The trolley has two top wheels and a large T-bar. Rock and idol sizes are design targets, not measured mesh dimensions. These are concept PNGs for Meshy; geometry, exact scale, materials, topology and Unreal imports remain later steps.
