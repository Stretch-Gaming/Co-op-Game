HC-A3 source-art delivery for #20 is ready on branch `codex/hc-a3-hud-art`.

Files are confined to `SourceArt/HC/HC-A3/`:
- `T_HUD_RelicIcon.png`
- `T_HUD_RoundBannerFrame.png`
- `T_HUD_InteractPromptFrame.png`
- Original outputs, exact prompts, provenance, preparation script, validation report and offline preview.

Tool: OpenAI built-in `image_gen.imagegen` in Codex on 2026-10-10, with transparent_background=true. The signed-in account's subscription tier and model version are not exposed by the tool. No separate API or paid fallback was used. Full prompts are in `prompts.md`; the only image input was the project's existing style-reference.png (SHA-256 e1a33275dbc0f87fef385d4e9b0d753730752f9fab57ed299d17ef4bf5004914).

Rights: OpenAI Terms of Use effective January 1, 2026, https://openai.com/policies/terms-of-use/ — output-rights assignment to the user, subject to the terms and applicable law; not CC0. Public redistribution is permitted on that basis. No attribution is required for these outputs. The existing project's style-reference provenance is recorded in PG-A0/README.md.

Validation: all three production PNGs are 512 x 512 RGBA with real alpha, transparent canvas boundaries, recorded SHA-256 hashes and text-free artwork. Offline visual review passed at 32/48/64px for the icon, 240/320px for the banner and 200/240px for the prompt on dark and light backgrounds. Tiny retained alpha noise in the checked frame opening is at most 1/255. The preview includes a two-player composition using the project's style reference.

Only the source-generation delivery is complete. Import into Content/Puzzles/Art/, style-test review, HUD integration and in-game client/split-screen checks are pending. Issue #20 remains open.
