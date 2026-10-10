# HC-A3 HUD source art

Source delivery for [issue #20](https://github.com/Stretch-Gaming/Co-op-Game/issues/20), prepared by Stretch on 2026-10-10. Branch: `codex/hc-a3-hud-art`.

## Deliverables

| File | Purpose | Format |
| --- | --- | --- |
| T_HUD_RelicIcon.png | Gold lion relic with jade inset; counter icon | 512 x 512 RGBA PNG |
| T_HUD_RoundBannerFrame.png | Slate, rope and amber-accented empty round banner | 512 x 512 RGBA PNG |
| T_HUD_InteractPromptFrame.png | Smaller empty interaction frame | 512 x 512 RGBA PNG |

All three production textures have actual alpha transparency and no baked-in text. The gold/jade colors are confined to the relic; frames use cave slate and muted amber. Original 1254 x 1254 tool outputs are retained under `sources/`. Only the three top-level `T_HUD_*.png` files are intended for import. `preview.png` is review evidence, not a game texture.

![Offline split-screen and small-size readability preview](preview.png)

## Preparation and evidence

- `prompts.md`: exact prompts, tool mode and reference image identity.
- `generation.json`: raw source hashes and provenance.
- `prepare.py`: repeatable size conversion, alpha checks and offline preview.
- `validation.json`: production-file SHA-256 hashes, dimensions, alpha statistics and preview hash.
- `visual-review.md`: independent visual inspection and its limits.

Reproduce with Python 3.10+ and Pillow 10.1+:

```text
python SourceArt/HC/HC-A3/prepare.py --style-reference SourceArt/PG/PG-A0/style-frames/style-reference.png
```

Hydrate the existing style reference from Git LFS first. The script verifies its recorded hash and writes only into this HC-A3 directory. Processing consists of LANCZOS size conversion, transparent padding for the icon and preview compositing. The generated color and alpha are preserved; there is no semantic repainting or alpha thresholding.

The icon is shown at 32, 48 and 64px texture width; use 48px or larger where the inset jewel should remain distinct. The banner is checked at 240px and 320px texture width, and the prompt at 200px and 240px. These are full square-canvas sizes, not tightly cropped artwork sizes. Frames have generous vertical transparent padding; keep their square aspect ratio when laying out the widget.

Preview labels are separate demonstration overlays. They are not present in the production textures. The split-screen panel uses the team's existing style reference at two brightness levels; it is an offline mockup, not an Unreal screenshot.

## Rights and provenance

Tool: OpenAI built-in `image_gen.imagegen` in Codex, used through the signed-in account on 2026-10-10. The tool does not expose the account subscription tier or model version. No separate API request, paid fallback or third-party asset service was used.

Terms: [OpenAI Terms of Use, effective January 1, 2026](https://openai.com/policies/terms-of-use/), sections “What you can do” and “Ownership of content.” OpenAI assigns its rights, if any, in output to the user to the extent permitted by law. This is an output-rights assignment under those terms, not a CC0 license. The terms permit use of the service subject to compliance and impose no attribution requirement for these output assets. Public repository redistribution is permitted on that basis. No credit entry is required.

The only image input was the project's existing OpenAI-generated style reference, whose provenance and permission to publish are recorded in `SourceArt/PG/PG-A0/README.md`. Reference SHA-256: `e1a33275dbc0f87fef385d4e9b0d753730752f9fab57ed299d17ef4bf5004914`. No game screenshots, third-party logos, stock art or external fonts were added. The preview reuses that same project reference and Pillow's bundled font.

## Engine integration

The engine delivery is recorded in [integration/README.md](integration/README.md), including actual Unreal 5.8.3 imports under `Content/Puzzles/Art/HCA3_UI/`, owning-player HUD construction, runtime checks and screenshots. The original source-art gate in PR #68 did not use the editor; the follow-up integration gate does. The three production PNGs remain unchanged.
