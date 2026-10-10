#!/usr/bin/env python3
"""Check format, peak, and loop seams of the delivered WAVs. Writes validation.json next to them."""
import array, json, math, subprocess, sys
from pathlib import Path
root = Path(sys.argv[1])
out = {}
for p in sorted(root.glob('SFX_*.wav')):
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(p)]))['streams'][0]
    x = array.array('f', subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'f32le', '-']))
    peak = max(abs(v) for v in x)
    rms = math.sqrt(sum(v * v for v in x) / len(x))
    steps = sorted(abs(x[i] - x[i - 1]) for i in range(1, len(x)))
    r = dict(codec=info['codec_name'], sample_rate=int(info['sample_rate']), channels=info['channels'],
             bits=int(info.get('bits_per_raw_sample') or 0), seconds=round(len(x) / 48000, 3),
             peak_dbfs=round(20 * math.log10(peak), 2), rms_dbfs=round(20 * math.log10(rms), 2),
             first_last_abs_dbfs=[round(20 * math.log10(abs(x[0]) + 1e-12), 1), round(20 * math.log10(abs(x[-1]) + 1e-12), 1)])
    if 'Loop' in p.name:
        seam = abs(x[0] - x[-1])
        r['loop_seam_step_dbfs'] = round(20 * math.log10(seam + 1e-12), 1)
        r['median_step_dbfs'] = round(20 * math.log10(steps[len(steps) // 2] + 1e-12), 1)
    out[p.name] = r
    print(p.name, r)
(root / 'validation.json').write_text(json.dumps(out, indent=1))
