# Audio signal quality check

Run from the repo root:

`python -B Tools/quality/audio/check_audio.py SourceArt/PG/PG-A3 --output Saved/QualityAudio/signal-quality.json`

Focused tests: `python -B -m unittest discover -s Tools/quality/audio -p test_audio.py`.

No source WAV, native asset, mix gain or playback hook is edited. Standard-library PCM16/24/32 mono reader supports extensible PCM; normalized samples retain signed24-bit precision. Exit0 means analysis completed, including heuristic warnings. Exit2 means malformed/missing/unsupported input prevents analysis. It does not fail artistic intent. Valid formats outside this tool's declared mono integerPCM scope are unsupported, not proof the sound itself is broken.

Thresholds: exact positive/negative full-scale sample counts and longest contiguous run are reported. Full-scale plateaus suggest clipping; a sharp sting could intentionally distort. Prior distortion followed by normalization cannot be ruled out by absence of full-scale samples. DC warns above0.001 amplitude(-60dBFS). Silence uses nonoverlapping100ms RMS blocks: below-80dBFS for at least0.5s is near-silence; below-60dBFS intervals are also listed. Intentional pauses/fades are not defects. Loop seam warns only when endpoint step exceeds both0.01(-40dBFS) and8times natural99th-percentile derivative. Median/p99/max natural derivatives and10ms crossing-boundary derivative RMS/max plus first/last5ms RMS distinguish seam from ordinary transients. Values floored at-240dBFS represent zero, not measured noise-floor precision.

All peaks are SAMPLE peaks. No oversampled true-peak, listening judgment, perceptual loudness, codec, engine limiter/bus gain, spatialization or speaker output is measured. Chase mix uses aligned source samples at native gains1+0.5; four circular-offset stress checks are labelled as hypothetical, not engine behavior. A positive sum-of-individual-peaks bound is a possibility bound, not measured clipping.

## Findings at baseline9dc0fab

Nine sounds analyzed; no structural errors or threshold warnings. All sample peaks about-3dBFS; zero full-scale samples/runs. Largest DC is LightsOut at-79.73dBFS, below warning threshold. No RMS below-80dBFS interval reaches0.5s. This does not prove the intended breathing lull is satisfying.

Loop endpoint steps: drone-109.23dBFS, build-92.63dBFS, breath exactlyzero. All fall well below their natural derivative distributions. No objective crossfade repair is indicated. Equal-length chase layers mixed aligned at1+0.5 peak at-1.229dBFS, no samples above full scale. Offset stress checks125/250/500/1000ms also stay below full scale; worst tested peak-1.027dBFS. Sum-of-peaks upper bound+0.522dBFS means arbitrary alignment is not guaranteed safe, and other gameplay sounds can add energy. Do not reduce the authored mix on that bound alone.

Five synthetic tests pass:24-bit/extensible sign decoding, zero/DC/full-scale plateaus, smooth/broken loops, aligned/offset clipping mix and CLI invalid-input-versus-heuristic exit behavior. Saved evidence is `Saved/QualityAudio/signal-quality.json`.

## Three safe next steps

1. Keep the delivered WAVs/mix/hooks unchanged and retain this QC as a regression check. No measured correction is needed.
2. Stretch listens in game to the breathing lull3.3–7.9s, victim-only sting, and chase drone/build together. Whether the pause, sting character or relative mix should change is a creative decision. Also listen at the loop seam and with both host split views; analytical results cannot establish audibility or scare effectiveness.
3. If playback sounds compressed or harsh, consider rebuilding from original downloads rather than MP3 previews. Source links, edits and CC0 evidence are in `SourceArt/PG/PG-A3/README.md`; this is a quality option requiring listening and access to originals, not an automatic repair. Examples: [monster breath](https://freesound.org/people/mucky_pete7/sounds/574208/), [chase drone](https://freesound.org/people/gerainsan/sounds/457046/), [chase build](https://freesound.org/people/jhooper/sounds/141135/), [sting](https://freesound.org/people/qubodup/sounds/814050/).

No listening snippets/crossfade candidates generated because no objective source issue was found. No claim that the sounds are enjoyable, scary or balanced without hearing.
