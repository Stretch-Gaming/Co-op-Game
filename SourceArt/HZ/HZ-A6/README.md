# HZ-A6: Cave and trap sounds

Raw sounds for [#57](https://github.com/StretchGaming/Co-op-Game/issues/57), used by HZ-9's sound pass. The loops, drips and torch are synthesized. The trap sounds layer CC0 Kenney sounds with synthesized parts. Where every input comes from and how it was processed is in [SOURCES.md](SOURCES.md).

| File | Ch | Length | Plays | Made from |
| --- | --- | --- | --- | --- |
| `SFX_CaveAmbience_Loop.wav` | 2 | 30.0 s | Looping 2D bed | Synthesized |
| `SFX_TorchCrackle_Loop.wav` | 1 | 12.0 s | Looping, on each torch and brazier | Synthesized |
| `SFX_Drip_01`–`03.wav` | 1 | 1.0–1.1 s | Random one-shots around the cave | Synthesized |
| `SFX_Spikes_Arm.wav` | 1 | 1.12 s | When the plate is stepped on (click, then rumble) | Kenney + synthesis |
| `SFX_Spikes_Rise.wav` | 1 | 0.78 s | When the spikes rise, `SpikeDelay` after the trigger | Kenney + synthesis |
| `SFX_Spikes_Retract.wav` | 1 | 1.28 s | When the spikes go back down | Kenney + synthesis |
| `SFX_DartLauncher_Arm.wav` | 1 | 0.49 s | With the volley warning, 0.5 s before it fires | Kenney |
| `SFX_DartLauncher_Fire_01`–`02.wav` | 1 | 0.47–0.48 s | At each volley, from the launcher | Kenney + synthesis |
| `SFX_Dart_Whoosh.wav` | 1 | 0.46 s | On each dart in flight | Kenney + synthesis |
| `SFX_Dart_Impact_01`–`03.wav` | 1 | 0.54–0.66 s | Where a dart lands (01–02 stick and quiver, 03 bounces off stone) | Kenney + synthesis |
| `SFX_SwingLog_Whoosh.wav` | 1 | 1.21 s | Through the bottom of each swing | Kenney + synthesis |

Every file is a 48 kHz, 16-bit PCM WAV, peak-normalized to -3 dBFS with no clipping. Only the ambience is stereo. The one-shots start and end on silence. The two loops are built circularly (FFT filtering, wrapped events and a wrapped reverb), so the last sample runs into the first like any other pair of samples.

## Checks

`HZ-A6_sounds.validation.json` has, for every file: sample rate, channels, bit depth, length, peak, 4x-oversampled true peak, RMS, DC offset, clipped samples, the inputs and processing, and a sha256. One-shots also get an edge check. Loops get a seam check on each channel:

- **Seam step:** the jump from the last sample to the first, compared with every other sample-to-sample step in the file. The ambience's seam steps are 0.0049 and 0.0040 against a 99.9th percentile of 0.054. The torch's is 0.0008 against 0.28.
- **Seam window:** the file is rolled by half its length so the seam sits in the middle. Then the 10 ms window across it is compared with the windows in the second around it, for level (RMS) and for high-frequency energy (first difference). A click would show up as a high-frequency ratio well above 1. The ambience measures 0.77 and 0.96 for level, and 1.09 and 1.17 for high frequencies. The torch measures 0.93 and 1.05.

`SFX_Loops_preview.png` shows each loop's spectrogram over two passes, with the seam marked, and its waveform across the seam. `SFX_OneShots_preview.png` shows a spectrogram and waveform for every one-shot.

## Rebuilding

From the repo root, with Python 3, numpy, scipy and matplotlib, and ffmpeg on the PATH (it only decodes the OGGs):

```sh
python3 -I SourceArt/HZ/HZ-A6/make_sounds.py        # writes SFX_*.wav and build.json here
python3 -I SourceArt/HZ/HZ-A6/validate_sounds.py    # writes the validation JSON and the previews
```

Pass a folder to either script to write somewhere else, for example `/tmp/HZ-A6`. Every random choice uses a fixed seed, so two runs on the same machine produce byte-identical WAVs (checked with sha256). A different numpy, scipy or ffmpeg build can change the last bit of some samples, and then the hashes won't match, but the sounds will be the same.

Each sound has its own fixed dither seed in `SOUNDS`, so adding or removing a sound doesn't change the bytes of the others. The swinging log's creaks were dropped after a listen, which is why the dither seeds skip from 9014 to 9018.

The levels and timings are constants in `make_sounds.py`, one function per sound. For example, the ambience's layer levels are the `k.db(...)` values in `cave_ambience()`, and the drip reverb is the `cave_ir(...)` call in `drip_variant()`.

## Files

- `make_sounds.py`: builds every sound.
- `sfx_kit.py`: shared DSP: filters, envelopes, modal hits, the cave reverb, circular helpers for the loops, the OGG loader and the WAV writer.
- `validate_sounds.py`: the checks and previews.
- `raw/`: the 16 Kenney OGGs the trap sounds use, unchanged from soundcn. See [SOURCES.md](SOURCES.md).
- `build.json`: each output's inputs and processing, written by `make_sounds.py`.
