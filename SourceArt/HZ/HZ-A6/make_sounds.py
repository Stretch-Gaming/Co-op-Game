"""HZ-A6: cave and trap sounds.

Builds every SFX_*.wav in this folder from two kinds of input:
- synthesis (numpy/scipy, fixed seeds): the cave ambience loop, the drips, the torch
  crackle loop, and synthesized layers in the trap sounds;
- CC0 Kenney sounds in raw/ (from soundcn's copy of the Kenney packs, see SOURCES.md),
  layered and processed for the spikes, darts and swinging log.

    python3 -I SourceArt/HZ/HZ-A6/make_sounds.py [out_dir]
    python3 -I SourceArt/HZ/HZ-A6/validate_sounds.py

out_dir defaults to this folder. Needs numpy, scipy and ffmpeg (decode only).
Every output is 48 kHz 16-bit PCM WAV, mono except the stereo ambience, peak -3 dBFS.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parent))
import sfx_kit as k  # noqa: E402

SR = k.SR
PEAK_DB = -3.0


# ----------------------------------------------------------------------------- helpers

def onset(x, rel_db=-30):
    """Index of the first sample within rel_db of the peak."""
    return int(np.argmax(np.abs(x) > np.abs(x).max() * k.db(rel_db)))


def from_onset(x, pre=0.002, rel_db=-30):
    i = max(0, onset(x, rel_db) - k.secs(pre))
    return x[i:]


def unit(x):
    return x / (np.abs(x).max() + 1e-12)


def energy_center(x, win=0.03):
    """Time (s) of the loudest point of x's smoothed envelope."""
    w = k.secs(win)
    e = np.convolve(x ** 2, np.ones(w) / w, mode='same')
    return np.argmax(e) / SR


def mix_len(*parts):
    return max(start + len(x) for x, start in parts)


def mix(*parts, extra=0.0):
    """parts: (signal, start_seconds). Returns the sum."""
    parts = [(x, k.secs(s)) for x, s in parts]
    y = np.zeros(mix_len(*parts) + k.secs(extra))
    for x, s in parts:
        k.add_at(y, x, s)
    return y


def finish(x, rng, room_rt60=None, wet_db=-14.0, fade_out=0.04, tail_db=-58):
    """Common end of a one-shot: optional small room, rumble filter, trim, fades, -3 dBFS."""
    if room_rt60:
        x = k.reverb(x, k.cave_ir(rng, room_rt60), wet_db)
    x = k.hp(x, 30, order=2)
    x = k.trim_tail(x, tail_db, pad=0.03)
    x = k.fade(x, 0.0005, fade_out)
    return k.normalize(x, PEAK_DB)


def quiver(rng, f, decay, length=0.4):
    """Stylized dart-shaft quiver: a buzzy decaying tone with a fast tremolo."""
    n = k.secs(length)
    t = k.t_axis(n)
    vib = 1 + 0.01 * np.sin(2 * np.pi * 9 * t)
    ph = 2 * np.pi * np.cumsum(f * (1 - 0.06 * (1 - np.exp(-t / 0.15))) * vib) / SR
    tone = np.tanh(2.2 * np.sin(ph)) * 0.7 + 0.3 * np.sin(2 * ph)
    trem = 0.55 + 0.45 * np.cos(2 * np.pi * rng.uniform(22, 28) * t)
    return k.lp(tone * trem * k.env_exp(n, 0.002, decay), 2500)


def thump(f0, f1, decay, length=0.3):
    """A sine that drops in pitch: the weight under an impact."""
    n = k.secs(length)
    t = k.t_axis(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * k.env_exp(n, 0.001, decay)


# ----------------------------------------------------------------------------- loops

def cave_ambience():
    """Stereo, 30 s. Low rumble, breathing air, a faint two-note wind moan, distant drips
    and two pebble trickles, all built circularly so the loop seam is invisible."""
    rng = np.random.default_rng(6001)
    n = k.secs(30.0)

    def rms(x):
        return np.sqrt(np.mean(x ** 2))

    common = rng.standard_normal(n)
    bed = np.zeros((n, 2))
    for ch in range(2):
        # Rumble: brown-ish noise, 22-140 Hz, partly shared between channels.
        r = 0.75 * common + 0.66 * rng.standard_normal(n)
        r = k.fft_shape(r, lambda f: k.band_gain(f, 22, 140) / (1 + f / 40))
        r *= 1 + 0.25 * np.tanh(k.periodic_smooth(rng, n, 0.08))
        bed[:, ch] += r / rms(r) * k.db(-27)
        # Air: pink noise 180-2200 Hz that slowly breathes, differently per side.
        a = k.fft_shape(rng.standard_normal(n), lambda f: k.band_gain(f, 180, 2200) / np.sqrt(f + 20))
        a *= 0.6 + 0.4 * np.tanh(k.periodic_smooth(rng, n, 0.12))
        bed[:, ch] += a / rms(a) * k.db(-35)
        # Wind moan: two narrow noise bands (a soft fifth), fading in and out.
        m = k.fft_shape(rng.standard_normal(n), lambda f: np.exp(-0.5 * ((f - 247) / 5) ** 2)
                        + 0.7 * np.exp(-0.5 * ((f - 370) / 6) ** 2))
        m *= 0.5 + 0.5 * np.tanh(1.5 * k.periodic_smooth(rng, n, 0.05))
        bed[:, ch] += m / rms(m) * k.db(-41)

    # Distant drips and pebbles go through a long, wrapped cave reverb.
    far = np.zeros((n, 2))
    times = np.sort(rng.uniform(0, 30, 11))
    for t0 in times:
        d = k.drip(rng, rng.uniform(650, 1500), rng.uniform(1.6, 2.3), rng.uniform(0.02, 0.05))
        d = k.lp(d, 5000) * k.db(rng.uniform(-8, 0))
        pan = rng.uniform(0.15, 0.85)
        k.add_wrapped(far, np.stack([d * np.cos(pan * np.pi / 2), d * np.sin(pan * np.pi / 2)], 1), k.secs(t0))
    for t0 in rng.uniform(0, 30, 2):
        pan = rng.uniform(0.2, 0.8)
        t = t0
        for j in range(rng.integers(5, 9)):
            m = k.secs(0.04)
            tick = k.modal(m, rng.uniform(1800, 4200, 3), rng.uniform(0.004, 0.01, 3), [1, 0.5, 0.3])
            tick *= k.db(-6 - 3 * j + rng.uniform(-2, 2))
            k.add_wrapped(far, np.stack([tick * np.cos(pan * np.pi / 2), tick * np.sin(pan * np.pi / 2)], 1),
                          k.secs(t))
            t += rng.uniform(0.03, 0.12)
    ir = k.cave_ir(rng, 2.6, length=2.8, bright=3500, channels=2)
    for ch in range(2):
        far[:, ch] = k.reverb_circular(far[:, ch], ir[:, ch], wet_db=0, dry=0.3)
    far *= k.db(-12) / (np.abs(far).max() + 1e-12)

    y = bed + far
    for ch in range(2):
        y[:, ch] = k.fft_shape(y[:, ch], lambda f: k.band_gain(f, 18, None, order=2))
    return k.normalize(y, PEAK_DB), [], 'Synthesized: rumble, air, wind moan, distant drips and pebbles, circular cave reverb.'


def torch_crackle():
    """Mono, 12 s. A low flickering roar, faint gas hiss, and crackles and pops in clusters."""
    rng = np.random.default_rng(6002)
    n = k.secs(12.0)
    flick = 0.65 + 0.35 * np.tanh(k.periodic_smooth(rng, n, 2.5))
    slow = 0.85 + 0.15 * np.tanh(k.periodic_smooth(rng, n, 0.25))
    roar = k.fft_shape(rng.standard_normal(n), lambda f: k.band_gain(f, 70, 700) / (1 + f / 300))
    roar *= flick * slow
    roar *= k.db(-22) / np.sqrt(np.mean(roar ** 2))
    hiss = k.fft_shape(rng.standard_normal(n), lambda f: k.band_gain(f, 2500, 9000)) * flick
    hiss *= k.db(-44) / np.sqrt(np.mean(hiss ** 2))

    crack = np.zeros(n)

    def crackle(amp):
        m = k.secs(0.03)
        e = rng.standard_normal(m) * k.env_exp(m, 0.00005, rng.uniform(0.0006, 0.003))
        ev = k.peak_filter(e, rng.uniform(1500, 7000), rng.uniform(1.5, 5)) + 0.4 * k.hp(e, 900)
        return unit(ev) * amp

    def pop(amp):
        m = k.secs(0.09)
        e = rng.standard_normal(m) * k.env_exp(m, 0.0001, rng.uniform(0.004, 0.01))
        ev = k.peak_filter(e, rng.uniform(350, 1100), rng.uniform(4, 8)) + 0.5 * k.hp(e, 1500)
        return unit(ev) * amp

    t = 0.0
    while True:
        t += rng.exponential(1 / 7.5)
        if t >= 12.0:
            break
        amp = k.db(rng.uniform(-26, 0))
        is_pop = rng.random() < 0.15
        k.add_wrapped(crack, pop(amp) if is_pop else crackle(amp * 0.8), k.secs(t))
        for _ in range(rng.integers(0, 4)):
            k.add_wrapped(crack, crackle(amp * rng.uniform(0.3, 0.8)), k.secs(t + rng.uniform(0.004, 0.035)))
    crack *= k.db(-6)

    y = roar + hiss + crack
    y = k.fft_shape(y, lambda f: k.band_gain(f, 40, None))
    return k.normalize(y, PEAK_DB), [], 'Synthesized: flickering low roar, gas hiss, clustered crackles and pops, built circularly.'


# ----------------------------------------------------------------------------- drips

def drip_variant(seed, f0, rise, tau, second=None):
    def build():
        rng = np.random.default_rng(seed)
        x = k.drip(rng, f0, rise, tau, n=k.secs(0.3))
        if second:
            x = mix((x, 0), (k.drip(rng, *second[1:], n=k.secs(0.3)) * second[0][1], second[0][0]))
        x = k.hp(x, 300)
        x = k.reverb(x, k.cave_ir(rng, 1.3, length=1.4, bright=4500), wet_db=-11)
        x = k.trim_tail(x, -55, pad=0.02)
        x = k.fade(x, 0.0003, 0.15)
        return k.normalize(x, PEAK_DB), [], 'Synthesized: rising-pitch drop with a tick, short cave reverb.'
    return build


# ----------------------------------------------------------------------------- spikes

def spikes_arm():
    """Trigger: a metal latch click, then a grinding stone rumble that swells into the rise."""
    rng = np.random.default_rng(6021)
    latch = unit(from_onset(k.load_raw('kenney_rpg-audio/metalLatch.ogg')))
    knock = unit(k.lp(from_onset(k.load_raw('kenney_sci-fi-sounds/lowFrequency_explosion_001.ogg')), 250, 4))
    knock = k.fade(knock[:k.secs(0.5)], 0, 0.2)
    n = k.secs(0.75)
    t = k.t_axis(n)
    grind = k.lp(rng.standard_normal(n), 160, 4) * (0.65 + 0.35 * np.sin(2 * np.pi * 24 * t))
    gate = (rng.random(n) < 40 / SR).cumsum() % 2          # random stick-slip on/off, about 40 Hz
    grit = k.bp(rng.standard_normal(n) * k.lp(gate.astype(float), 60), 300, 1200, order=3)
    swell = np.clip((t - 0.03) / 0.3, 0, 1) ** 2 * np.clip((0.72 - t) / 0.22, 0, 1)
    rumble = unit((unit(grind) + 0.15 * unit(grit)) * swell)
    x = mix((latch, 0), (knock * 0.35, 0.01), (rumble * 0.5, 0.02))
    return finish(x, rng, room_rt60=0.6, wet_db=-14, fade_out=0.08), \
        ['kenney_rpg-audio/metalLatch.ogg', 'kenney_sci-fi-sounds/lowFrequency_explosion_001.ogg'], \
        'metalLatch as the click; lowFrequency_explosion_001 low-passed at 250 Hz as a knock; ' \
        'synthesized grinding rumble that swells over 0.3 s; small room.'


def spikes_rise():
    """The damage moment: a short metal "shk" into a clang, a stone thud and a sub thump."""
    rng = np.random.default_rng(6022)
    knife = k.load_raw('kenney_rpg-audio/drawKnife3.ogg')
    pk = int(np.argmax(np.abs(knife)))
    knife = unit(k.fade(knife[max(0, pk - k.secs(0.06)):], 0.01, 0.05))
    hit = k.secs(0.06) / SR
    clang = unit(from_onset(k.load_raw('kenney_impact-sounds/impactMetal_heavy_001.ogg')))
    stone = unit(k.lp(from_onset(k.load_raw('kenney_impact-sounds/impactMining_003.ogg')), 1200))
    stone = k.fade(stone[:k.secs(0.45)], 0, 0.15)
    x = mix((knife * 0.9, 0), (clang * 0.8, hit), (stone * 0.6, hit), (thump(85, 45, 0.09) * 0.5, hit))
    return finish(x, rng, room_rt60=0.7, wet_db=-14, fade_out=0.06), \
        ['kenney_rpg-audio/drawKnife3.ogg', 'kenney_impact-sounds/impactMetal_heavy_001.ogg',
         'kenney_impact-sounds/impactMining_003.ogg'], \
        'drawKnife3 cut to 60 ms before its peak as the scrape; impactMetal_heavy_001 clang and ' \
        'impactMining_003 (low-passed 1.2 kHz) at the peak; synthesized 85-45 Hz thump; small room.'


def spikes_retract():
    """A slower, lower scrape sliding down, ending in a stone clunk."""
    rng = np.random.default_rng(6023)
    scrape = unit(k.hp(from_onset(k.repitch(k.load_raw('kenney_rpg-audio/drawKnife2.ogg'), 0.7)), 300))
    n = k.secs(0.65)
    t = k.t_axis(n)
    fc = 1200 * (500 / 1200) ** (t / 0.6)
    rate = 30 + 8 * np.tanh(k.lp(rng.standard_normal(n), 8) * 20)     # stick-slip rate, 22-38 Hz
    rough = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * np.cumsum(rate) / SR))
    grind = k.svf_bandpass(rng.standard_normal(n), fc, 2.5) * k.lp(rough, 400)
    grind = unit(grind * np.clip(t / 0.03, 0, 1) * np.clip((0.62 - t) / 0.15, 0, 1))
    clunk = unit(k.lp(from_onset(k.load_raw('kenney_impact-sounds/impactMining_002.ogg')), 900))
    clunk = k.fade(clunk[:k.secs(0.35)], 0, 0.12)
    x = mix((scrape * 0.6, 0), (grind * 0.7, 0), (clunk * 0.9, 0.62), (thump(75, 45, 0.08) * 0.5, 0.62))
    return finish(x, rng, room_rt60=0.6, wet_db=-14, fade_out=0.08), \
        ['kenney_rpg-audio/drawKnife2.ogg', 'kenney_impact-sounds/impactMining_002.ogg'], \
        'drawKnife2 slowed to 0.7x (lower) and high-passed as the slide; synthesized grind sweeping ' \
        '1.2 kHz to 500 Hz; impactMining_002 low-passed at 900 Hz plus a synthesized thump as the end clunk at 0.62 s.'


# ----------------------------------------------------------------------------- darts

def dart_arm():
    """The half-second warning: a ratchet winding up, with a little wooden strain."""
    rng = np.random.default_rng(6031)
    ratchet = unit(from_onset(k.load_raw('kenney_rpg-audio/beltHandle2.ogg')))
    ratchet = unit(ratchet + k.peak_filter(ratchet, 700, 3, 2.0))
    strain = unit(from_onset(k.repitch(k.load_raw('kenney_rpg-audio/creak3.ogg'), 0.9)))
    x = mix((ratchet, 0), (strain * 0.25, 0.05))
    return finish(x, rng, room_rt60=0.5, wet_db=-16, fade_out=0.05), \
        ['kenney_rpg-audio/beltHandle2.ogg', 'kenney_rpg-audio/creak3.ogg'], \
        'beltHandle2 as the ratchet, with a +6 dB resonance at 700 Hz for body; creak3 slowed to 0.9x ' \
        'at -12 dB underneath; small room.'


def dart_fire(seed, wood, decay, tube):
    def build():
        rng = np.random.default_rng(seed)
        clack = unit(from_onset(k.load_raw(wood)))
        clack = k.fade(clack[:k.secs(0.18)], 0, 0.06)
        n = k.secs(0.25)
        t = k.t_axis(n)
        fc = 1100 + 2400 * np.exp(-t / 0.02)
        puff = unit(k.svf_bandpass(rng.standard_normal(n), fc, 1.2) * k.env_exp(n, 0.0015, decay))
        tone = thump(tube, tube * 0.85, 0.035, 0.2)
        x = mix((clack * 0.7, 0), (puff, 0.004), (tone * 0.5, 0.004))
        return finish(x, rng, room_rt60=0.5, wet_db=-14, fade_out=0.05), [wood], \
            f'{Path(wood).stem} cut to 0.18 s as the mechanism clack; synthesized air puff ' \
            f'(band-pass sweeping 3.5 kHz to 1.1 kHz) and a {tube} Hz tube "thoomp"; small room.'
    return build


def dart_whoosh():
    """A short flyby: knifeSlice2's swish, softened, over a synthesized band-pass sweep."""
    rng = np.random.default_rng(6041)
    swish = k.load_raw('kenney_rpg-audio/knifeSlice2.ogg')
    c = energy_center(swish)
    swish = unit(k.hp(swish * k.bell(len(swish), c, 0.08), 900))
    n = k.secs(0.5)
    t = k.t_axis(n)
    fc = 900 + 2100 * np.exp(-0.5 * ((t - 0.2) / 0.07) ** 2) + 400 * (t > 0.2)
    synth = unit(k.svf_bandpass(rng.standard_normal(n), fc, 1.8) * k.bell(n, 0.2, 0.06))
    x = mix((swish * 0.8, max(0.0, 0.2 - c)), (synth * 0.7, 0))
    return finish(x, rng, fade_out=0.05), ['kenney_rpg-audio/knifeSlice2.ogg'], \
        'knifeSlice2 shaped by a bell envelope around its loudest point and high-passed at 900 Hz; ' \
        'synthesized flyby (band-pass sweeping up to 3 kHz and back) under it.'


def dart_impact_wood(seed, src, qf, qdecay, qgain, cut):
    def build():
        rng = np.random.default_rng(seed)
        hit = unit(from_onset(k.load_raw(src)))
        hit = k.fade(hit[:k.secs(cut)], 0, 0.08)
        x = mix((hit, 0), (quiver(rng, qf, qdecay) * qgain, 0.003))
        return finish(x, rng, room_rt60=0.5, wet_db=-16, fade_out=0.06), [src], \
            f'{Path(src).stem} cut to {cut} s as the hit; synthesized shaft quiver at {qf} Hz; small room.'
    return build


def dart_impact_stone():
    """Ricochet off stone: a gritty hit, a small metal ting and two lighter bounces."""
    rng = np.random.default_rng(6053)
    hit = unit(k.lp(from_onset(k.load_raw('kenney_impact-sounds/impactMining_002.ogg')), 3000))
    hit = k.fade(hit[:k.secs(0.25)], 0, 0.1)
    ting = unit(from_onset(k.load_raw('kenney_impact-sounds/impactMetal_medium_004.ogg')))
    bounce = unit(from_onset(k.repitch(k.load_raw('kenney_impact-sounds/impactWood_medium_003.ogg'), 1.5)))
    bounce = k.fade(bounce[:k.secs(0.12)], 0, 0.05)
    x = mix((hit, 0), (ting * 0.5, 0.002), (bounce * 0.32, 0.11), (bounce * 0.16, 0.19))
    return finish(x, rng, room_rt60=0.5, wet_db=-16, fade_out=0.06), \
        ['kenney_impact-sounds/impactMining_002.ogg', 'kenney_impact-sounds/impactMetal_medium_004.ogg',
         'kenney_impact-sounds/impactWood_medium_003.ogg'], \
        'impactMining_002 low-passed at 3 kHz and cut to 0.25 s; impactMetal_medium_004 at -6 dB; ' \
        'impactWood_medium_003 sped up 1.5x as two bounces at 0.11 s and 0.19 s; small room.'


# ----------------------------------------------------------------------------- swinging log

def log_creak(seed, src, ratio):
    def build():
        rng = np.random.default_rng(seed)
        x = from_onset(k.repitch(k.load_raw(src), ratio), rel_db=-40)
        x = unit(x + k.peak_filter(x, 260, 2.0, 1.5))
        return finish(x, rng, room_rt60=0.6, wet_db=-16, fade_out=0.08), [src], \
            f'{Path(src).stem} slowed to {ratio}x (lower, heavier) with a 260 Hz body resonance; small room.'
    return build


def log_whoosh():
    """A heavy low "whoom": knifeSlice slowed to 0.4x over a synthesized low band-pass sweep."""
    rng = np.random.default_rng(6071)
    slow = k.repitch(k.load_raw('kenney_rpg-audio/knifeSlice.ogg'), 0.4)
    c = energy_center(slow, 0.06)
    slow = unit(k.lp(slow * k.bell(len(slow), c, 0.2), 2500))
    n = k.secs(1.2)
    t = k.t_axis(n)
    shape = k.bell(n, 0.55, 0.18)
    fc = 180 + 450 * shape
    air = unit(k.svf_bandpass(rng.standard_normal(n), fc, 1.2) * shape)
    sub = np.sin(2 * np.pi * 55 * t) * shape
    x = mix((air, 0), (sub * 0.25, 0), (slow * 0.6, max(0.0, 0.55 - c)))
    return finish(x, rng, fade_out=0.1), ['kenney_rpg-audio/knifeSlice.ogg'], \
        'knifeSlice slowed to 0.4x, shaped by a bell around its loudest point and low-passed at 2.5 kHz; ' \
        'synthesized low band-pass sweep (180-630 Hz) and a 55 Hz sub swell.'


# ----------------------------------------------------------------------------- the list

SOUNDS = {
    'SFX_CaveAmbience_Loop': cave_ambience,
    'SFX_TorchCrackle_Loop': torch_crackle,
    'SFX_Drip_01': drip_variant(6011, 1050, 2.0, 0.035),
    'SFX_Drip_02': drip_variant(6012, 780, 1.7, 0.045),
    'SFX_Drip_03': drip_variant(6013, 1350, 2.3, 0.028, second=((0.11, 0.5), 950, 2.1, 0.03)),
    'SFX_Spikes_Arm': spikes_arm,
    'SFX_Spikes_Rise': spikes_rise,
    'SFX_Spikes_Retract': spikes_retract,
    'SFX_DartLauncher_Arm': dart_arm,
    'SFX_DartLauncher_Fire_01': dart_fire(6032, 'kenney_impact-sounds/impactWood_medium_000.ogg', 0.04, 200),
    'SFX_DartLauncher_Fire_02': dart_fire(6033, 'kenney_impact-sounds/impactWood_medium_003.ogg', 0.055, 170),
    'SFX_Dart_Whoosh': dart_whoosh,
    'SFX_Dart_Impact_01': dart_impact_wood(6051, 'kenney_rpg-audio/chop.ogg', 165, 0.22, 0.4, 0.24),
    'SFX_Dart_Impact_02': dart_impact_wood(6052, 'kenney_impact-sounds/impactPlank_medium_001.ogg', 215, 0.16, 0.32, 0.35),
    'SFX_Dart_Impact_03': dart_impact_stone,
    'SFX_SwingLog_Creak_01': log_creak(6061, 'kenney_rpg-audio/creak1.ogg', 0.82),
    'SFX_SwingLog_Creak_02': log_creak(6062, 'kenney_rpg-audio/creak2.ogg', 0.82),
    'SFX_SwingLog_Creak_03': log_creak(6063, 'kenney_rpg-audio/creak3.ogg', 0.75),
    'SFX_SwingLog_Whoosh': log_whoosh,
}


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else k.HERE
    out.mkdir(parents=True, exist_ok=True)
    build = {}
    for i, (name, fn) in enumerate(SOUNDS.items()):
        x, inputs, notes = fn()
        k.write_wav(out / f'{name}.wav', x, seed=9000 + i)
        build[name] = {'inputs': ['raw/' + p for p in inputs], 'processing': notes}
        print(f'{name:28s} {x.shape[0] / SR:6.3f} s  {"stereo" if x.ndim > 1 else "mono"}')
    (out / 'build.json').write_text(json.dumps(build, indent=2) + '\n')


if __name__ == '__main__':
    main()
