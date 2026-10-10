#!/usr/bin/env python3
"""PG-A3 taking and chase sounds, built from CC0 Freesound recordings.

Python standard library + installed FFmpeg. Never executes any downloaded file;
it only decodes the explicit audio paths below. Same approach as the ghost
auditions in /Users/peterkim/CoopGameArt/candidates/PG-A3-library/.

Run: python3 -I build_taking.py [--downloads DIR] [--out DIR]
"""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

SR = 48000
TARGET = 10 ** (-3 / 20)
parser = argparse.ArgumentParser()
parser.add_argument('--downloads', type=Path,
                    default=Path('/Users/peterkim/CoopGameArt/downloads/PG-A3-taking/freesound'))
parser.add_argument('--out', type=Path,
                    default=Path('/Users/peterkim/CoopGameArt/candidates/PG-A3-taking'))
args = parser.parse_args()
META = json.loads((args.downloads / 'meta.json').read_text())

# Freesound id -> short key. Every one is CC0 1.0 (checked on its page).
SRC = {
    'grab': '667271', 'drag': '481863', 'stone': '354094', 'slam': '465807',
    'crack': '157804', 'crackle': '489905', 'smash': '512243', 'crumble': '608957',
    'grind': '844329', 'bulb': '866662', 'click': '557509', 'powercut': '636578',
    'roll': '423750', 'jumpscare': '814050', 'breathsting': '530778',
    'breath': '574208', 'drone': '457046', 'clang': '141135',
}

def path_of(key):
    return META[SRC[key]]['path']

def decode(key, start, seconds, pitch=0, highpass=40, lowpass=16000, keep_time=True, extra=()):
    """Trim, pitch-shift and filter one source. keep_time=False shifts pitch and speed together."""
    ratio = 2 ** (pitch / 12)
    filters = [f'atrim=start={start}:duration={seconds}', 'asetpts=PTS-STARTPTS', 'aresample=48000']
    if pitch:
        filters += [f'asetrate={round(SR * ratio)}', 'aresample=48000']
        if keep_time:
            filters.append(f'atempo={1 / ratio:.9f}')
    filters += [f'highpass=f={highpass}', f'lowpass=f={lowpass}', *extra]
    data = subprocess.check_output(['ffmpeg', '-nostdin', '-v', 'error', '-i', path_of(key), '-ac', '1',
                                    '-af', ','.join(filters), '-ar', str(SR), '-f', 'f32le', 'pipe:1'])
    x = array.array('f', data)
    if sys.byteorder != 'little':
        x.byteswap()
    return x

def scale_peak(x, target=1.0):
    peak = max(abs(v) for v in x)
    if peak == 0:
        raise ValueError('Silent source')
    return array.array('f', (v * target / peak for v in x))

def fade(x, attack=.003, release=.075):
    a, b = round(attack * SR), round(release * SR)
    for i in range(min(a, len(x))):
        x[i] *= math.sin(i / max(1, a - 1) * math.pi / 2) ** 2
    for i in range(min(b, len(x))):
        x[-1 - i] *= math.sin(i / max(1, b - 1) * math.pi / 2) ** 2
    return x

def gate(x, pattern):
    """Flicker: keep only the (start, end) windows, with 4 ms ramps."""
    y = array.array('f', [0.] * len(x))
    r = round(.004 * SR)
    for s, e in pattern:
        a, b = round(s * SR), min(len(x), round(e * SR))
        for i in range(a, b):
            w = min(1., (i - a) / r, (b - 1 - i) / r)
            y[i] = x[i] * max(0., w)
    return y

def mix(total_seconds, layers):
    """layers: (time, gain, samples). Each layer is peak-scaled to 1 before its gain."""
    y = array.array('f', [0.] * round(total_seconds * SR))
    for t, g, x in layers:
        x = scale_peak(x)
        off = round(t * SR)
        for i, v in enumerate(x[:max(0, len(y) - off)]):
            y[off + i] += v * g
    return y

def room(x, wet=.10):
    """Quiet short reflections, as in the ghost set. Keeps events localizable."""
    y = array.array('f', x)
    for delay, weight in [(.029, wet), (.053, wet * .7), (.083, wet * .42), (.117, wet * .23)]:
        off = round(delay * SR)
        for i, v in enumerate(x[:len(x) - off]):
            y[i + off] += v * weight
    return y

def loop_wrap(x, overlap):
    """Raised-cosine head/tail overlap, then rotate to a quiet sample pair (ghost set's method)."""
    k = round(overlap * SR)
    y = array.array('f')
    for i in range(k):
        w = (1 - math.cos(math.pi * i / (k - 1))) / 2
        y.append(x[len(x) - k + i] * (1 - w) + x[i] * w)
    y.extend(x[k:len(x) - k])
    cut = min(range(1, len(y)), key=lambda i: abs(y[i]) + abs(y[i - 1]) + 8 * abs(y[i] - y[i - 1]))
    return y[cut:] + y[:cut]

def write_wav(name, x):
    x = scale_peak(x, TARGET)
    data = array.array('f', x)
    if sys.byteorder != 'little':
        data.byteswap()
    path = args.out / name
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1',
                    '-i', 'pipe:0', '-c:a', 'pcm_s24le', str(path)], input=data.tobytes(), check=True)
    return path

OUT = {}

# 1. A hand drags a victim into rock: a grab, a body dragged over stone, the rock closing on them.
OUT['SFX_Taking_HandDrag.wav'] = room(mix(3.6, [
    (0.00, .80, fade(decode('grab', 0.0, 1.0, pitch=-2, highpass=80, lowpass=9000), .002, .15)),
    (0.85, .80, fade(decode('drag', 0.0, 2.1, pitch=-1, highpass=60, lowpass=7000), .12, .5)),
    (0.95, .50, fade(decode('stone', 9.6, 2.0, pitch=-5, highpass=60, lowpass=5000), .2, .5)),
    (2.70, 1.0, fade(decode('slam', 0.0, .85, pitch=-5, highpass=40, lowpass=2500), .003, .3)),
]))

# 2a. The floor cracks open and swallows them: a crack, crackling, a heavy break, rubble falling away.
OUT['SFX_Taking_FloorCrack.wav'] = room(mix(3.0, [
    (0.00, .80, fade(decode('crack', .22, 1.2, pitch=-2, highpass=60, lowpass=9000), .002, .4)),
    (0.05, .50, fade(decode('crackle', .8, 1.7, highpass=80, lowpass=10000), .01, .4)),
    (0.35, 1.0, fade(decode('smash', .40, 1.6, pitch=-4, highpass=40, lowpass=6000), .002, .5)),
    (0.50, .70, fade(decode('crumble', 1.0, 2.5, pitch=-3, highpass=40, lowpass=4000), .3, .8)),
]))

# 2b. The floor grinds shut: a heavy stone slab slides, then lands.
OUT['SFX_Taking_FloorShut.wav'] = room(mix(2.9, [
    (0.00, .90, fade(decode('grind', 5.2, 2.3, pitch=-2, highpass=40, lowpass=5000), .15, .25)),
    (2.05, 1.0, fade(decode('slam', 0.0, .85, pitch=-4, highpass=30, lowpass=3000), .003, .3)),
]))

# 3a. The lights cut out: a bulb's hum flickers, the headlamp clicks off, the power dies with a low sweep.
hum = decode('bulb', 1.15, 1.0, highpass=80, lowpass=8000)
OUT['SFX_Taking_LightsOut.wav'] = room(mix(2.4, [
    (0.00, .60, gate(hum, [(0, .12), (.2, .26), (.45, .5), (.62, .66)])),
    (0.30, .40, fade(decode('bulb', 1.55, .25, highpass=200, lowpass=9000), .002, .08)),
    (0.66, .80, decode('click', 0.0, .12, highpass=100)),
    (0.66, .80, fade(decode('powercut', 0.0, 1.7, pitch=-3, highpass=30, lowpass=3500), .01, .9)),
]), wet=.08)

# 3b. The dropped headlamp lands and rolls on the floor. High-pass removes the floor's boom;
# compression lifts the roll toward the impact.
OUT['SFX_Taking_HeadlampRoll.wav'] = room(fade(decode(
    'roll', 2.15, 4.6, highpass=140, lowpass=12000,
    extra=('acompressor=threshold=-36dB:ratio=10:attack=1:release=120:makeup=12',)), .002, .4), wet=.08)

# 4. The taken player's sting, 2D on their own screen: a layered piano/drum hit with a breath in the ear.
OUT['SFX_Taking_Sting_2D.wav'] = mix(2.6, [
    (0.00, 1.0, fade(decode('jumpscare', 0.0, 2.6, highpass=30), .002, .9)),
    (0.00, .45, fade(decode('breathsting', .05, 1.8, pitch=-3, highpass=80, lowpass=9000), .01, .8)),
])

# 5. The taker's presence: slow, heavy breathing, a 4th lower and slower, looped between two quiet gaps.
OUT['SFX_Taker_Breath_Loop.wav'] = loop_wrap(
    decode('breath', 8.0, 13.5, pitch=-5, keep_time=False, highpass=40, lowpass=3500), .4)

# 6. The chase (PG-10), 2D: a pulsing drone loop, plus a clanging layer of the same length to fade in
# as the chase builds. Both are 26.2 s and start together, so they stay aligned when looped.
drone = loop_wrap(decode('drone', 0.0, 13.13, highpass=25), .05)
OUT['SFX_Chase_Loop_2D.wav'] = drone + drone
n = len(drone) * 2
clang = decode('clang', 0.0, n / SR + .5, highpass=60, lowpass=12000)
clang = loop_wrap(clang, .5)
clang = clang[:n] if len(clang) >= n else clang + array.array('f', [0.] * (n - len(clang)))
OUT['SFX_Chase_Build_Loop_2D.wav'] = clang

args.out.mkdir(parents=True, exist_ok=True)
report = {}
for name, x in OUT.items():
    p = write_wav(name, x)
    report[name] = dict(seconds=round(len(x) / SR, 3), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    print(name, report[name]['seconds'], 's')
(args.out / 'build-report.json').write_text(json.dumps(dict(
    outputs=report,
    sources={k: dict(id=SRC[k], **{f: META[SRC[k]][f] for f in ('user', 'title', 'page', 'download')},
                     sha256=hashlib.sha256(Path(path_of(k)).read_bytes()).hexdigest())
             for k in SRC}), indent=1))
