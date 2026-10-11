"""Read UE native CSV timings; never launches processes or changes engine settings."""
import argparse
import csv
import hashlib
import io
import json
import math
import pathlib
from stats import summary

METRICS = ('GameThreadTime', 'RenderThreadTime', 'GPUTime')


def parse(text, discard_frames=0):
    if not isinstance(discard_frames, int) or discard_frames < 0:
        raise ValueError('discard_frames must be a nonnegative integer')
    rows = list(csv.reader(io.StringIO(text.lstrip('\ufeff'))))
    headers = [r for r in rows if r and r[0] == 'EVENTS']
    if not headers:
        raise ValueError('Missing UE EVENTS header')
    header = headers[-1]  # UE final summary header includes columns added during capture.
    indices = {}
    for metric in METRICS + ('FrameTime',):
        matches = [i for i, name in enumerate(header) if name.rsplit('/', 1)[-1] == metric]
        if len(matches) > 1:
            raise ValueError('Ambiguous native metric: ' + metric)
        if matches:
            indices[metric] = matches[0]
        elif metric in METRICS:
            raise ValueError('Missing native metric: ' + metric)
    metadata, frames, incomplete = {}, [], 0
    for line, row in enumerate(rows, 1):
        if not row or row[0] == 'EVENTS':
            continue
        if row[0].startswith('[') and row[0].endswith(']'):
            if len(row) % 2:
                raise ValueError('Unpaired metadata at line ' + str(line))
            metadata.update({row[i].strip('[]'): row[i+1] for i in range(0, len(row), 2)})
            continue
        if len(row) <= max(indices.values()):
            incomplete += 1  # Early rows may precede registration of final columns.
            continue
        sample = {}
        for metric, index in indices.items():
            try:
                value = float(row[index])
            except ValueError as exc:
                raise ValueError(f'Invalid {metric} at line {line}') from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError(f'Nonfinite or negative {metric} at line {line}')
            sample[metric] = value
        frames.append(sample)
    kept = frames[discard_frames:]
    if not kept:
        raise ValueError('No complete native timing rows remain after warmup discard')
    warnings = [f'{incomplete} early rows lack required columns'] if incomplete else []
    if all(frame['GPUTime'] == 0 for frame in kept):
        warnings.append('GPUTime is entirely zero: GPU timing unavailable; do not claim measured GPU cost')
    return {'method': 'Native UE CSV millisecond timers; thread/GPU values overlap and must not be summed.',
            'metadata': metadata, 'header': header, 'valid_rows_before_discard': len(frames),
            'discarded_valid_frames': discard_frames, 'incomplete_rows': incomplete,
            'metrics': {metric: summary([f[metric] for f in kept]) for metric in indices},
            'raw_samples_ms': kept, 'warnings': warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', type=pathlib.Path)
    parser.add_argument('--discard-frames', type=int, default=0)
    args = parser.parse_args()
    if args.csv_file.stat().st_size > 128 * 1024 * 1024:
        parser.error('Input exceeds the bounded 128 MiB reader limit')
    raw = args.csv_file.read_bytes()
    result = parse(raw.decode('utf-8-sig'), args.discard_frames)
    result.update(source=str(args.csv_file.resolve()), source_sha256=hashlib.sha256(raw).hexdigest())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
