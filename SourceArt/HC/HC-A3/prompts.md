# HC-A3 exact generation prompts

Tool: OpenAI built-in image_gen.imagegen in Codex. Date: 2026-10-10. Mode: stylized-concept generation with transparent_background=true. Each call used the existing team style reference as its only image input. Model version and subscription tier are not exposed by the tool. No separate API request or paid fallback was used.

Reference: SourceArt/PG/PG-A0/style-frames/style-reference.png
Reference SHA-256: e1a33275dbc0f87fef385d4e9b0d753730752f9fab57ed299d17ef4bf5004914

## T_HUD_RelicIcon

Use case: stylized-concept. Asset: T_HUD_RelicIcon, a single production game HUD texture.
Input image 1 is the team's STYLE REFERENCE only; borrow its painted chunky shapes and gold lion idol visual language, never copy its scene.
Create one centered gold lion relic icon, simplified frontal seated idol with a single jade-green inset jewel. Bold broad silhouette, expressive carved lion face, stout mane and large paws. Gold #E8B33A and jade #3FA672; highlights broad and warm, shadows blue-violet. Readable at 32 and 48 pixels, restrained large details, no fine lines.
Square 512x512 PNG, actual transparent alpha background, approximately 15% clear margin on each side, entire idol visible. No ground plane, no background scene, no cast shadow outside silhouette, no border, no text, numbers, logos or watermark.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures

## T_HUD_RoundBannerFrame

Use case: stylized-concept. Asset: T_HUD_RoundBannerFrame, one production game HUD texture.
Input image is STYLE REFERENCE only. Borrow broad beveled painted stone and worn rope, not its scene.
Create a flat front-facing horizontal hollow rectangular round-banner border. A broad simple blue-violet slate-stone border with slightly chipped chunky bevels, short worn rope wraps at the two ends, thin warm amber #FFB347 highlights. Main stone #4A4652, shadow #1E2433, highlight #7A6E68. Palette accents are muted amber, not relic gold. NO jewel, ghost-white, trap-red, skull or lettering.
512x512 square canvas, border centered, outer bounds roughly x=36..476 y=176..336 (440px wide, 160px tall), hollow inner opening roughly x=84..428 y=213..299. Outside AND entire center genuinely transparent alpha. Keep all border decoration within outer bounds and clear margin. Top and bottom rails straight enough for readable widget text; understated corners.
This is ONLY an EMPTY FRAME: absolutely no opaque panel filling the center, no background scene or ground, no text, glyphs, letters, numbers, icon, progress meter, logos or watermark. No cast shadow beyond border. Clean cutout edges. Readable when full square texture is scaled to 320px and 240px wide.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures

## T_HUD_InteractPromptFrame

Use case: stylized-concept. Asset: T_HUD_InteractPromptFrame, a single production HUD texture matching our slate stone round-banner border.
Input image is the team's STYLE REFERENCE only; borrow broad painted stone bevels and worn rope, do not copy its scene.
Create a flat front-facing simple hollow rectangular interaction prompt border, smaller and quieter than a round banner. Rounded chunky slate-stone corners, broad subtly uneven bevel, a small worn rope wrap at each end, restrained muted warm amber edge highlight. Slate #4A4652, shadows #1E2433, highlights #7A6E68, amber #FFB347. NO gold jewels, relic symbol, ghost-white or trap-red.
Square 512x512 PNG canvas. Centered horizontal outer border roughly x=48..464 y=184..328, transparent inner opening roughly x=80..432 y=212..300. Entire outside AND center genuinely transparent alpha. All decoration stays within the outer bounds. Clear wide opening to fit an input key and action label added by the game. Simple enough to read when the full texture is scaled to 200px wide.
ONLY AN EMPTY FRAME. No filled center/panel, scene, ground, text, letters, numbers, glyphs, button legend, progress bar, logos or watermark. No cast shadow beyond the silhouette.
stylized hand-painted game asset, chunky exaggerated proportions, slightly uneven shapes, soft wide bevels, simple painted color, gradient from dark base to lighter top, no fine surface noise, no photo textures
