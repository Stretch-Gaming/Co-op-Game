# HZ-A6 sources

Checked on Oct 10, 2026. Every file in `raw/` is a CC0 sound by Kenney, taken from the copy of the Kenney packs in [soundcn](https://github.com/kapishdima/soundcn) at commit [`7cbfbb3`](https://github.com/kapishdima/soundcn/tree/7cbfbb3f56e8548b81fb26410bdcea657447d087) (`7cbfbb3f56e8548b81fb26410bdcea657447d087`). soundcn keeps Kenney's original OGG files under `assets/kenney_*/`, which are better than the MP3s embedded in its registry, so those are what we downloaded.

## License check

- For each item below, soundcn's `registry.json` at that commit lists `"author": "Kenney <https://kenney.nl>"` and `"meta": {"license": "CC0"}`.
- The upstream packs are CC0 on kenney.nl: [Impact Sounds](https://kenney.nl/assets/impact-sounds), [RPG Audio](https://kenney.nl/assets/rpg-audio) and [Sci-fi Sounds](https://kenney.nl/assets/sci-fi-sounds).
- CC0 allows publishing in a public repo and needs no credit, so there's no line in `CREDITS.md`.
- **No Blizzard or All Rights Reserved soundcn items were used.** soundcn also holds 110 items marked `© Blizzard Entertainment, Inc. — All Rights Reserved`, such as `black-rock-doors-*`, `deadmine-door-*`, `bell-toll-*` and `chest-open`. We left all of them out by keeping only items whose license is `CC0` and whose author is Kenney (703 of the 813 sounds; the registry's 3 other entries are code, not sounds, and have no license).
- Nothing came from Freesound or any other site.

## Raw files

URL pattern: `https://raw.githubusercontent.com/kapishdima/soundcn/7cbfbb3f56e8548b81fb26410bdcea657447d087/assets/<pack>/<file>`

| File in `raw/` | soundcn item | Kenney pack | License | sha256 (first 12) |
| --- | --- | --- | --- | --- |
| `kenney_impact-sounds/impactMetal_heavy_001.ogg` | `impact-metal-heavy-001` | Impact Sounds | CC0 | `83554049f81f` |
| `kenney_impact-sounds/impactMetal_medium_004.ogg` | `impact-metal-medium-004` | Impact Sounds | CC0 | `03e10f800199` |
| `kenney_impact-sounds/impactMining_002.ogg` | `impact-mining-002` | Impact Sounds | CC0 | `059558ec7511` |
| `kenney_impact-sounds/impactMining_003.ogg` | `impact-mining-003` | Impact Sounds | CC0 | `4237fa2cd803` |
| `kenney_impact-sounds/impactPlank_medium_001.ogg` | `impact-plank-medium-001` | Impact Sounds | CC0 | `d7c304319f8b` |
| `kenney_impact-sounds/impactWood_medium_000.ogg` | `impact-wood-medium-000` | Impact Sounds | CC0 | `1723a9fd2510` |
| `kenney_impact-sounds/impactWood_medium_003.ogg` | `impact-wood-medium-003` | Impact Sounds | CC0 | `635c37cfcd85` |
| `kenney_rpg-audio/beltHandle2.ogg` | `belt-handle-2` | RPG Audio | CC0 | `f3b692d5c832` |
| `kenney_rpg-audio/chop.ogg` | `chop` | RPG Audio | CC0 | `d00c2b3c9fff` |
| `kenney_rpg-audio/creak1.ogg` | `creak-1` | RPG Audio | CC0 | `8a346186fd29` |
| `kenney_rpg-audio/creak2.ogg` | `creak-2` | RPG Audio | CC0 | `8a990afdc03a` |
| `kenney_rpg-audio/creak3.ogg` | `creak-3` | RPG Audio | CC0 | `f9638787f950` |
| `kenney_rpg-audio/drawKnife2.ogg` | `draw-knife-2` | RPG Audio | CC0 | `d5df6a4130cb` |
| `kenney_rpg-audio/drawKnife3.ogg` | `draw-knife-3` | RPG Audio | CC0 | `a11ae62fb1a6` |
| `kenney_rpg-audio/knifeSlice.ogg` | `knife-slice` | RPG Audio | CC0 | `4cd96dc630be` |
| `kenney_rpg-audio/knifeSlice2.ogg` | `knife-slice-2` | RPG Audio | CC0 | `6c2064d0ef98` |
| `kenney_rpg-audio/metalLatch.ogg` | `metal-latch` | RPG Audio | CC0 | `ba9ba60b172b` |
| `kenney_sci-fi-sounds/lowFrequency_explosion_001.ogg` | `low-frequency-explosion-001` | Sci-fi Sounds | CC0 | `cdda50600a49` |

## Output to input

Synthesized means built by `make_sounds.py` and `sfx_kit.py` with fixed seeds: our own work, no credit needed. The same mapping, in machine-readable form, is in `build.json` and in each entry of `HZ-A6_sounds.validation.json`.

| Output | Inputs | Processing |
| --- | --- | --- |
| `SFX_CaveAmbience_Loop` | Synthesized | Low rumble, breathing air, a faint two-note wind moan, distant drips and pebble trickles, and a long cave reverb, all built circularly so the loop has no seam. |
| `SFX_TorchCrackle_Loop` | Synthesized | Flickering low roar, faint gas hiss, and clustered crackles and pops, built circularly. |
| `SFX_Drip_01`–`03` | Synthesized | A rising-pitch water "plink" with a small tick, then a short cave reverb. `03` is a double drop. |
| `SFX_Spikes_Arm` | `metalLatch`, `lowFrequency_explosion_001` | The latch is the click. The explosion, low-passed at 250 Hz, is a soft knock under it. A synthesized grinding rumble swells over 0.3 s into the rise. Small room. |
| `SFX_Spikes_Rise` | `drawKnife3`, `impactMetal_heavy_001`, `impactMining_003` | The knife draw, cut to 60 ms before its peak, is the "shk". The metal clang and the mining hit (low-passed at 1.2 kHz) land at its peak, with a synthesized 85–45 Hz thump. Small room. |
| `SFX_Spikes_Retract` | `drawKnife2`, `impactMining_002` | The knife draw, slowed to 0.7x and high-passed, plus a synthesized grind sweeping from 1.2 kHz down to 500 Hz, is the slide. The mining hit, low-passed at 900 Hz, plus a synthesized thump is the clunk at 0.62 s. Small room. |
| `SFX_DartLauncher_Arm` | `beltHandle2`, `creak3` | The belt handle is the ratchet, with a resonance at 700 Hz added for body. The creak, slowed to 0.9x, sits about 12 dB under it. Small room. |
| `SFX_DartLauncher_Fire_01` | `impactWood_medium_000` | The wood hit, cut to 0.18 s, is the mechanism's clack. A synthesized air puff (band-pass sweeping from 3.5 kHz down to 1.1 kHz) and a 200 Hz tube "thoomp". Small room. |
| `SFX_DartLauncher_Fire_02` | `impactWood_medium_003` | As `_01`, with a longer puff and a 170 Hz tube. |
| `SFX_Dart_Whoosh` | `knifeSlice2` | The slice, shaped by a bell envelope around its loudest point and high-passed at 900 Hz, over a synthesized flyby (a band-pass sweeping up to 3 kHz and back). |
| `SFX_Dart_Impact_01` | `chop` | The chop, cut to 0.24 s, is the hit, with a synthesized 165 Hz shaft quiver. Small room. |
| `SFX_Dart_Impact_02` | `impactPlank_medium_001` | The plank hit, cut to 0.35 s, with a synthesized 215 Hz quiver. Small room. |
| `SFX_Dart_Impact_03` | `impactMining_002`, `impactMetal_medium_004`, `impactWood_medium_003` | A ricochet off stone: the mining hit (low-passed at 3 kHz, cut to 0.25 s), a small metal ting about 6 dB down, and the wood hit sped up 1.5x as two lighter bounces at 0.11 s and 0.19 s. Small room. |
| `SFX_SwingLog_Creak_01`–`03` | `creak1`, `creak2`, `creak3` | Each creak slowed (0.82x, 0.82x, 0.75x) so it sounds heavier, with a 260 Hz body resonance added. Small room. |
| `SFX_SwingLog_Whoosh` | `knifeSlice` | The slice, slowed to 0.4x, shaped by a bell envelope and low-passed at 2.5 kHz, over a synthesized low band-pass sweep (180–630 Hz) and a 55 Hz sub swell. |

Every Kenney input is decoded with ffmpeg, resampled to 48 kHz with scipy's polyphase filter and folded from stereo to mono. Every one-shot then gets a 30 Hz high-pass (300 Hz for the drips), raised-cosine fades at both ends and a trim of the silent tail. The loops have no fades; their low cut is applied in the FFT domain so it stays circular. Every output is peak-normalized to -3 dBFS and written as 16-bit PCM with seeded TPDF dither.
