# PG-A3: ghost and taking sounds

Sounds for [#37](https://github.com/StretchGaming/Co-op-Game/issues/37). This folder holds the **taking** set for PG-6 ([#106](https://github.com/StretchGaming/Co-op-Game/issues/106)) and the **chase** loop for PG-10 ([#108](https://github.com/StretchGaming/Co-op-Game/issues/108)). The ghost whisper, attack and repel sounds for PG-5 are still candidates outside the repo, waiting on PK's pick; they come from the same kind of sources and will join this folder.

Every source sound is **CC0 1.0 Universal**, checked on its own Freesound page. CC0 allows editing and publishing in this public repo with no credit, so nothing here needs a `CREDITS.md` row. No CC BY, NC or SA sounds were used, and none of the excluded libraries (Pixabay, Zapsplat, Sonniss, BBC, Envato, Epidemic).

## Files

Every file is a mono PCM WAV at 48 kHz and 24-bit, with its peak normalized to −3 dBFS. Files ending in `_2D` play in 2D, on one player's screen only. Everything else plays in 3D, with attenuation, at the victim or the taker.

| File | Moment | Play | Length |
| --- | --- | --- | --- |
| `SFX_Taking_HandDrag.wav` | A hand drags a victim into the wall: a cloth grab, a body dragged over stone, then the rock closes on them at 2.7 s | 3D, at the victim | 3.6 s |
| `SFX_Taking_FloorCrack.wav` | The floor cracks open and swallows them: a crack, crackling, a heavy break at 0.35 s, rubble falling away | 3D, at the victim | 3.0 s |
| `SFX_Taking_FloorShut.wav` | The floor grinds shut: a stone slab slides and lands at 2.05 s | 3D, at the victim | 2.9 s |
| `SFX_Taking_LightsOut.wav` | The lights cut out: a hum flickers, a headlamp clicks off at 0.66 s, the power dies with a low sweep | 3D, at the victim | 2.4 s |
| `SFX_Taking_HeadlampRoll.wav` | The dropped headlamp lands and rolls | 3D, at the dropped headlamp | 4.6 s |
| `SFX_Taking_Sting_2D.wav` | The taken player's sting: a layered piano and drum hit with a breath in the ear | **2D**, the victim's screen only | 2.6 s |
| `SFX_Taker_Breath_Loop.wav` | The taker's low presence: slow, heavy breathing | 3D, on the taker, looping | 17.6 s loop |
| `SFX_Chase_Loop_2D.wav` | The chase home (PG-10): a pulsing low drone | **2D**, each player's screen, looping | 26.16 s loop |
| `SFX_Chase_Build_Loop_2D.wav` | The chase builds: a clanging rhythm layer to fade in over the drone | **2D**, each player's screen, looping | 26.16 s loop |

The two chase files are exactly the same length. Start both together, with the build layer at zero volume, and raise it as the chase intensifies, so they stay aligned on every loop. Both are peak-normalized separately, so the build layer will probably need about −6 dB to sit under the drone. Peak normalization isn't loudness matching, so set each sound's volume by ear in the editor.

Loop seams, measured as the sample step across the wrap: −109 dBFS for the chase drone, −93 dBFS for the build layer and below −200 dBFS for the breathing, against median sample steps of −57, −36 and −61 dBFS. `validation.json` has the measured format, peak and RMS of each file.

## Every source sound used

All are Freesound sounds under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/), linked directly from each page. Freesound's original downloads need a login, which wasn't available, so these were built from its public high-quality MP3 previews, the same way as the ghost candidates. Writing a WAV doesn't restore what the MP3 encoding lost. Downloading the originals and rebuilding would be a quality upgrade, not a license change.

| Source | Author | Original | Used in | Trim and edit |
| --- | --- | --- | --- | --- |
| [Cloth Grab](https://freesound.org/people/alegemaate/sounds/667271/) | alegemaate | WAV, 44.1 kHz, stereo, 1.2 s | HandDrag | 0–1.0 s, −2 semitones |
| [R18-35-Drag Body Across Floor.wav](https://freesound.org/people/craigsmith/sounds/481863/) | craigsmith | WAV, 48 kHz, 24-bit, mono, 3.2 s | HandDrag | 0–2.1 s, −1 semitone, low-passed at 7 kHz |
| [Stone scratching over rock (close up), H6.wav](https://freesound.org/people/Bini_trns/sounds/354094/) | Bini_trns | WAV, 44.1 kHz, stereo, 16.6 s | HandDrag | 9.6–11.6 s, −5 semitones, under the drag |
| [big stone door suddenly slamming shut](https://freesound.org/people/PaceHeart/sounds/465807/) | PaceHeart | WAV, 44.1 kHz, stereo, 0.9 s | HandDrag, FloorShut | Whole, −5 and −4 semitones, low-passed. An edit of [door slam](https://freesound.org/people/contramundum/sounds/266440/) by contramundum, also CC0 |
| [rock falls with cracking.mp3](https://freesound.org/people/SoundCollectah/sounds/157804/) | SoundCollectah | MP3, 44.1 kHz, stereo, 5.9 s | FloorCrack | 0.22–1.42 s, −2 semitones |
| [RockCrack03](https://freesound.org/people/falcospizaetus/sounds/489905/) | falcospizaetus | WAV, 44.1 kHz, stereo, 4.1 s | FloorCrack | 0.8–2.5 s |
| [Rock Smash](https://freesound.org/people/NeoSpica/sounds/512243/) | NeoSpica | WAV, 48 kHz, stereo, 8.9 s | FloorCrack | The first hit, 0.4–2.0 s, −4 semitones |
| [Rockslide_1.wav](https://freesound.org/people/NinjaSharkStudios/sounds/608957/) | NinjaSharkStudios | WAV, 48 kHz, 24-bit, stereo, 12.3 s | FloorCrack | 1.0–3.5 s, −3 semitones, low-passed at 4 kHz |
| [Stone Slab Door Grinding - Heavy Rock Scrape (Mono)](https://freesound.org/people/NahuelMartinez/sounds/844329/) | NahuelMartinez | WAV, 48 kHz, 24-bit, mono, 16.9 s | FloorShut | 5.2–7.5 s, −2 semitones |
| [Vintage Edison Bulb Flicker & Warm-Up Sound Effect](https://freesound.org/people/hipoidogs/sounds/866662/) | hipoidogs | WAV, 24 kHz, stereo, 5.0 s | LightsOut | Hum 1.15–2.15 s, gated into four flickers; filament pings 1.55–1.8 s |
| [Foley_Object_Flashlight_Small_SingleButton_Mono.wav](https://freesound.org/people/Nox_Sound/sounds/557509/) | Nox_Sound | WAV, 48 kHz, 24-bit, mono, 0.6 s | LightsOut | The first click, 0–0.12 s |
| [Cutting Power](https://freesound.org/people/swag1773/sounds/636578/) | swag1773 | WAV, 44.1 kHz, mono, 3.9 s | LightsOut | 0–1.7 s, −3 semitones, low-passed at 3.5 kHz. Made from [Metro Scratch](https://freesound.org/people/unfa/sounds/243170/) by unfa, also CC0 |
| [FLASHLIGHT_ROLL.wav](https://freesound.org/people/haynze/sounds/423750/) | haynze | WAV, 48 kHz, 24-bit, stereo, 9.0 s | HeadlampRoll | 2.15–6.75 s, high-passed at 140 Hz to drop the wooden floor's boom, compressed to lift the roll |
| [Jumpscare](https://freesound.org/people/qubodup/sounds/814050/) | qubodup | WAV, 44.1 kHz, stereo, 7.4 s | Sting_2D | 0–2.6 s, faded out over 0.9 s |
| [breath stinger1](https://freesound.org/people/Tissman/sounds/530778/) | Tissman | Ogg, 44.1 kHz, stereo, 9.5 s | Sting_2D | 0.05–1.85 s, −3 semitones, under the hit |
| [MONSTER BREATH 1.wav](https://freesound.org/people/mucky_pete7/sounds/574208/) | mucky_pete7 | WAV, 48 kHz, 24-bit, mono, 42.6 s | Taker_Breath_Loop | 8.0–21.5 s, between two quiet gaps; 5 semitones lower and slower; low-passed at 3.5 kHz; 0.4 s loop crossfade |
| [Horror Pulsating Drone Loop](https://freesound.org/people/gerainsan/sounds/457046/) | gerainsan | WAV, 48 kHz, stereo, 13.1 s | Chase_Loop_2D | Whole, 50 ms loop crossfade, played twice |
| [Horror Chase.wav](https://freesound.org/people/jhooper/sounds/141135/) | jhooper | WAV, 44.1 kHz, stereo, 41.7 s | Chase_Build_Loop_2D | 0–26.66 s, 0.5 s loop crossfade |

Every layer also gets short fades, and the one-shot 3D sounds get the same quiet short reflections as the ghost set, so they still localize. No oscillators, generated noise or AI tools were used.

## Reproduce

`scripts/` has the three scripts that made this set. They use only the Python standard library and FFmpeg, and they never run anything they download.

1. `fs_fetch.py` downloads each source's Freesound page and public MP3 preview, and records its license link, into `downloads/PG-A3-taking/freesound/` outside the repo:

       python3 -I fs_fetch.py alegemaate/667271 craigsmith/481863 Bini_trns/354094 PaceHeart/465807 SoundCollectah/157804 falcospizaetus/489905 NeoSpica/512243 NinjaSharkStudios/608957 NahuelMartinez/844329 hipoidogs/866662 Nox_Sound/557509 swag1773/636578 haynze/423750 qubodup/814050 Tissman/530778 mucky_pete7/574208 gerainsan/457046 jhooper/141135

2. `build_taking.py --downloads <that folder> --out <folder>` builds the nine WAVs, with the trims and edits in the table above.
3. `validate.py <folder>` writes `validation.json`.

`build-report.json` records the SHA-256 of every source preview and every output, so a rebuild can be checked against this one.

`fs_fetch.py` writes to PK's local download folder by default; edit `DL` at its top on another machine.

## Sources checked but not used

- **For the drag:** [Body Drag.wav](https://freesound.org/people/Wallch503/sounds/507473/) (Wallch503, broom and footsteps) and [Dragging a body across a concrete floor 2](https://freesound.org/people/PostProdDog/sounds/578493/) (PostProdDog, has grunting), both CC0.
- **For the floor:** [Tomb Door Open, Stone Scrape](https://freesound.org/people/Kinoton/sounds/352829/) and [Heavy stone door opens 2](https://freesound.org/people/PostProdDog/sounds/578491/), both CC0.
- **For the lights:** [An incandescent lamp, the last seconds](https://freesound.org/people/newlocknew/sounds/786515/) (CC0, too quiet and hissy) and [FlashLight OFF.wav](https://freesound.org/people/saha213131/sounds/663649/) (CC0). [Small Hollow Metal Cylinder Impact and Roll](https://freesound.org/people/loganzsound/sounds/850723/) (CC0) rang too much like steel for a headlamp.
- **For the sting:** [Horror Surprise](https://freesound.org/people/qubodup/sounds/814048/), [Plucked Horror Stinger](https://freesound.org/people/zombieallen/sounds/725225/) and [Sting/jumpscare](https://freesound.org/people/hotpin7/sounds/846789/), all CC0.
- **For the breathing:** [Monster breathing](https://freesound.org/people/iut_Paris8/sounds/567723/) (a cat's purr), [Monster heavy breathing and moaning](https://freesound.org/people/rydra_wong/sounds/624592/), [Abberation Breathing](https://freesound.org/people/LucasDuff/sounds/467692/) and [Creepy Breath](https://freesound.org/people/Tommi3426/sounds/353147/), all CC0.
- **For the chase:** [Horror Chase (Loop)](https://freesound.org/people/SuperGamerSVK/sounds/509924/) (8-bit, off-style), [Short Chase Loop](https://freesound.org/people/3ag1e/sounds/745852/) and [Suspense Music Loop](https://freesound.org/people/Ncone/sounds/730224/), all CC0.
- CC BY sounds were searched too, but CC0 covered every moment, so none were used.

## Not yet checked by ear

The agent that built this set couldn't hear playback. The sources, trims and layering were chosen from each sound's description, its spectrogram and its loudness envelope. PK should listen before import, especially for whether the sting is scary rather than cheesy, whether the breathing's quiet lull (about 3.3–7.9 s into the loop) feels like a pause or a gap, and whether the chase's drone and clang belong together.
