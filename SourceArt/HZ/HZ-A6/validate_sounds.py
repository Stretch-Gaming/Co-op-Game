"""HZ-A6: check every SFX_*.wav against the spec and write the manifest and preview sheets.

    python3 -I SourceArt/HZ/HZ-A6/validate_sounds.py [dir]

Writes, in dir (default: this folder):
- HZ-A6_sounds.validation.json: per file, the format, duration, levels, edge and loop-seam
  checks, inputs and processing (from build.json, which make_sounds.py writes), and a sha256;
- SFX_Loops_preview.png and SFX_OneShots_preview.png: spectrograms for review.
"""
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy import signal
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
SR = 48000


def dbfs(v):
    return round(float(20 * np.log10(max(v, 1e-12))), 2)


def seam_check(x):
    """Loop seam metrics for one channel (float, -1..1).

    - seam_step: |last sample - first sample|, compared with the distribution of every
      other sample-to-sample step in the file;
    - rms_ratio / hf_ratio: the file is rolled by half its length so the seam sits in the
      middle, then the RMS and first-difference (high-frequency) energy of the 10 ms window
      straddling the seam are compared with the median of the windows in the second around it.
    """
    steps = np.abs(np.diff(x))
    seam = float(abs(x[0] - x[-1]))
    p999 = float(np.percentile(steps, 99.9))
    y = np.roll(x, len(x) // 2)
    mid = len(x) - len(x) // 2       # index in y where the original sample 0 now sits
    w = int(0.01 * SR)
    starts = range(mid - SR // 2, mid + SR // 2 - w, w // 2)
    rms = np.array([np.sqrt(np.mean(y[s:s + w] ** 2)) for s in starts])
    hf = np.array([np.sqrt(np.mean(np.diff(y[s:s + w]) ** 2)) for s in starts])
    s0 = mid - w // 2
    seam_rms = np.sqrt(np.mean(y[s0:s0 + w] ** 2))
    seam_hf = np.sqrt(np.mean(np.diff(y[s0:s0 + w]) ** 2))
    rms_ratio = float(seam_rms / np.median(rms))
    hf_ratio = float(seam_hf / np.median(hf))
    return {
        'seam_step': round(seam, 6),
        'interior_step_p99_9': round(p999, 6),
        'interior_step_max': round(float(steps.max()), 6),
        'seam_step_percentile': round(float(np.mean(steps < seam) * 100), 2),
        'seam_window_rms_ratio': round(rms_ratio, 3),
        'seam_window_hf_ratio': round(hf_ratio, 3),
        'ok': bool(seam <= p999 and 0.5 < rms_ratio < 2.0 and hf_ratio < 2.0),
    }


def check(path, build):
    sr, raw = wavfile.read(path)
    x = raw.astype(np.float64) / 32768.0
    ch = 1 if x.ndim == 1 else x.shape[1]
    xs = x.reshape(len(x), ch)
    loop = path.stem.endswith('_Loop')
    peak = np.abs(xs).max()
    over = signal.resample_poly(xs, 4, 1, axis=0)
    rec = {
        'file': path.name,
        'sample_rate': int(sr),
        'channels': ch,
        'bit_depth': int(raw.dtype.itemsize * 8),
        'frames': int(len(xs)),
        'duration_s': round(len(xs) / sr, 3),
        'peak_dbfs': dbfs(peak),
        'true_peak_dbtp_4x': dbfs(np.abs(over).max()),
        'rms_dbfs': dbfs(np.sqrt(np.mean(xs ** 2))),
        'dc_offset': round(float(np.abs(xs.mean(axis=0)).max()), 6),
        'clipped_samples': int(np.sum(np.abs(raw.astype(np.int32)) >= 32767)),
        'loops': loop,
    }
    if loop:
        rec['loop_seam'] = [seam_check(xs[:, c]) for c in range(ch)]
    else:
        rec['edges'] = {'first_sample_dbfs': dbfs(np.abs(xs[0]).max()),
                        'last_sample_dbfs': dbfs(np.abs(xs[-1]).max()),
                        'ok': bool(np.abs(xs[0]).max() < 1e-3 and np.abs(xs[-1]).max() < 1e-3)}
    want_ch = 2 if 'Ambience' in path.stem else 1
    rec['spec_ok'] = bool(sr == 48000 and ch == want_ch and rec['clipped_samples'] == 0
                          and -3.6 <= rec['peak_dbfs'] <= -2.4
                          and (rec['loop_seam'][0]['ok'] and rec['loop_seam'][-1]['ok'] if loop else rec['edges']['ok']))
    rec.update(build.get(path.stem, {}))
    rec['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    return rec, xs


def spec_ax(ax, x, title, t0=0.0):
    f, t, S = signal.spectrogram(x, SR, nperseg=1024, noverlap=768)
    ax.pcolormesh(t + t0, f, 10 * np.log10(S + 1e-14), vmin=-130, vmax=-35, shading='auto', cmap='magma')
    ax.set_yscale('symlog', linthresh=200)
    ax.set_ylim(20, 20000)
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=7)


def previews(d, data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    loops = [(r, x) for r, x in data if r['loops']]
    fig, axes = plt.subplots(len(loops), 2, figsize=(14, 3.2 * len(loops)), squeeze=False,
                             gridspec_kw={'width_ratios': [3, 1]})
    for (r, x), (a, b) in zip(loops, axes):
        two = np.concatenate([x[:, 0], x[:, 0]])
        spec_ax(a, two, f"{r['file']}: two passes, seam at {r['duration_s']} s (left channel)")
        a.axvline(r['duration_s'], color='cyan', lw=1, ls='--')
        a.set_ylabel('Hz', fontsize=8)
        w = int(0.025 * SR)
        for c in range(x.shape[1]):
            seg = np.concatenate([x[-w:, c], x[:w, c]])
            b.plot((np.arange(2 * w) - w) / SR * 1000, seg, lw=0.6, label=f'ch {c}')
        b.axvline(0, color='k', lw=0.8, ls='--')
        b.set_title('waveform across the seam (end | start)', fontsize=9)
        b.set_xlabel('ms', fontsize=8)
        b.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(d / 'SFX_Loops_preview.png', dpi=80)
    plt.close(fig)

    shots = [(r, x) for r, x in data if not r['loops']]
    cols = 4
    rows = (len(shots) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(16, 2.6 * rows), squeeze=False)
    for ax in axes.flat:
        ax.axis('off')
    for ax, (r, x) in zip(axes.flat, shots):
        ax.axis('on')
        spec_ax(ax, x[:, 0], f"{r['file'][4:-4]}  {r['duration_s']} s")
        tw = ax.twinx()
        tw.plot(np.arange(len(x)) / SR, x[:, 0], color='white', lw=0.3, alpha=0.6)
        tw.set_ylim(-1, 1)
        tw.set_yticks([])
    fig.tight_layout()
    fig.savefig(d / 'SFX_OneShots_preview.png', dpi=72)
    plt.close(fig)


def main():
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    build_path = d / 'build.json'
    build = json.loads(build_path.read_text()) if build_path.exists() else {}
    data = [check(p, build) for p in sorted(d.glob('SFX_*.wav'))]
    manifest = {
        'task': 'HZ-A6: Cave and trap sounds (#57)',
        'generator': 'make_sounds.py (synthesis + CC0 Kenney sources in raw/, see SOURCES.md)',
        'spec': 'WAV 48 kHz 16-bit PCM, mono except the stereo ambience, peak about -3 dBFS, loops seamless',
        'checked_with': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
        'all_ok': all(r['spec_ok'] for r, _ in data),
        'files': [r for r, _ in data],
    }
    (d / 'HZ-A6_sounds.validation.json').write_text(json.dumps(manifest, indent=2) + '\n')
    previews(d, data)
    for r, _ in data:
        seam = ''
        if r['loops']:
            seam = ' seam ' + ' / '.join(f"{s['seam_step']:.4f}<= p99.9 {s['interior_step_p99_9']:.4f} rms x{s['seam_window_rms_ratio']} hf x{s['seam_window_hf_ratio']}" for s in r['loop_seam'])
        print(f"{'OK ' if r['spec_ok'] else 'BAD'} {r['file']:30s} {r['channels']}ch {r['duration_s']:6.3f}s "
              f"pk {r['peak_dbfs']:6.2f} tp {r['true_peak_dbtp_4x']:6.2f} rms {r['rms_dbfs']:6.2f}{seam}")
    print('all_ok', manifest['all_ok'])


if __name__ == '__main__':
    main()
