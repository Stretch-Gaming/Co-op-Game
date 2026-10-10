"""HZ-A5: carved hieroglyph decals for Map 2's walls, for deferred decal material instances.
The glyphs are the team's own designs: simple Egyptian-inspired shapes (sun, peaks, water, reed,
bird, feather, loop-cross and so on) drawn from code with Pillow's polygon and line tools and fixed
seeds. They don't trace or copy any existing artwork, and no fonts or images are loaded.

    python3 -I SourceArt/HZ/HZ-A5/make_hieroglyphs.py            # writes here
    python3 -I SourceArt/HZ/HZ-A5/make_hieroglyphs.py OUT

Per decal (T_Hieroglyph_01 to _05):
    _BC    base color, sRGB: the carving's floor and its painted walls
    _Mask  opacity, linear, 1 = carved, 0 = leave the wall alone; zero on every border
    _N     normal, DirectX convention (green down, Y-), linear: the carving sunk into the wall

Needs T_Sandstone_Wall_BC.png and _N.png beside it (from make_sandstone.py) for the contact sheet.
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from scipy import ndimage  # noqa: E402

import hz_tex as tx  # noqa: E402

SEED = 5603
SS = 4  # supersampling for antialiased edges
PX_PER_CM = 10.24  # 1024 px per metre: the size the decals are designed to be placed at

SAND = tx.hex_rgb(tx.SANDSTONE)
CARVE_FLOOR = tx.mix(SAND * 0.60, tx.hex_rgb(tx.SHADOW), 0.22)  # in the groove: shaded, blue-violet
CARVE_LIT = tx.hex_rgb("#E7BE88")  # groove walls that face the light
CARVE_DARK = tx.mix(SAND * 0.42, tx.hex_rgb(tx.SHADOW), 0.35)  # groove walls turned away


# ---------------------------------------------------------------------------------------------
# Glyph vocabulary. Each draws carved (white) shapes into a square box: centre (cx, cy), size s.
# Coordinates are in supersampled pixels. `w` is the stroke width as a fraction of s.

def _line(d, pts, w):
    d.line(pts, fill=255, width=int(w), joint="curve")
    r = w / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)


def _ring(d, cx, cy, r, w):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=int(w))


def g_sun(d, cx, cy, s, rng, rays=12):
    """A disc with a ring and pointed rays."""
    _ring(d, cx, cy, s * 0.26, s * 0.07)
    r = s * 0.08
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    for k in range(rays):
        a = 2 * math.pi * k / rays + rng.uniform(-0.04, 0.04)
        r0, r1, half = s * 0.34, s * (0.47 if k % 2 == 0 else 0.42), 0.11
        d.polygon([(cx + r0 * math.cos(a - half), cy + r0 * math.sin(a - half)),
                   (cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
                   (cx + r0 * math.cos(a + half), cy + r0 * math.sin(a + half))], fill=255)


def g_reed(d, cx, cy, s, rng):
    """A tall stem with a leaf bent over at the top."""
    w = s * 0.09
    _line(d, [(cx, cy + s * 0.42), (cx + s * 0.02, cy - s * 0.15)], w)
    d.polygon([(cx + s * 0.02, cy - s * 0.12), (cx - s * 0.05, cy - s * 0.30), (cx + s * 0.08, cy - s * 0.44),
               (cx + s * 0.22, cy - s * 0.30), (cx + s * 0.10, cy - s * 0.24)], fill=255)


def g_wave(d, cx, cy, s, rng, rows=1, amp=0.07, w=0.075, teeth=8):
    """Zigzag water lines."""
    w = s * w
    step = 0.84 / (teeth - 1)
    for r in range(rows):
        y = cy + (r - (rows - 1) / 2) * s * 0.24
        pts = [(cx - s * 0.42 + i * s * step, y + (s * amp if i % 2 else -s * amp)) for i in range(teeth)]
        _line(d, pts, w)


def g_bird(d, cx, cy, s, rng):
    """A standing bird: round body, wedge head and beak, tail, two legs."""
    w = s * 0.07
    d.ellipse([cx - s * 0.22, cy - s * 0.12, cx + s * 0.16, cy + s * 0.14], fill=255)
    d.ellipse([cx + s * 0.06, cy - s * 0.34, cx + s * 0.24, cy - s * 0.16], fill=255)
    _line(d, [(cx + s * 0.12, cy - s * 0.18), (cx + s * 0.08, cy - s * 0.06)], s * 0.12)
    d.polygon([(cx + s * 0.22, cy - s * 0.29), (cx + s * 0.40, cy - s * 0.24), (cx + s * 0.22, cy - s * 0.20)], fill=255)
    d.polygon([(cx - s * 0.18, cy - s * 0.04), (cx - s * 0.42, cy + s * 0.14), (cx - s * 0.16, cy + s * 0.10)], fill=255)
    _line(d, [(cx - s * 0.04, cy + s * 0.12), (cx - s * 0.06, cy + s * 0.42)], w)
    _line(d, [(cx + s * 0.06, cy + s * 0.12), (cx + s * 0.08, cy + s * 0.42)], w)


def g_eye(d, cx, cy, s, rng):
    """An almond eye with a pupil and a straight brow."""
    w = s * 0.07
    top = [(cx - s * 0.40 + i * s * 0.08, cy - s * 0.17 * math.sin(math.pi * i / 10)) for i in range(11)]
    bot = [(cx + s * 0.40 - i * s * 0.08, cy + s * 0.13 * math.sin(math.pi * i / 10)) for i in range(11)]
    _line(d, top + bot + [top[0], top[1]], w)
    r = s * 0.09
    d.ellipse([cx - r, cy - r * 1.05, cx + r, cy + r * 0.95], fill=255)
    _line(d, [(cx - s * 0.34, cy - s * 0.32), (cx + s * 0.36, cy - s * 0.30)], w)


def g_loopcross(d, cx, cy, s, rng):
    """A loop over a T-shaped cross."""
    w = s * 0.09
    d.ellipse([cx - s * 0.15, cy - s * 0.44, cx + s * 0.15, cy - s * 0.06], outline=255, width=int(w))
    _line(d, [(cx - s * 0.30, cy - s * 0.02), (cx + s * 0.30, cy - s * 0.02)], w)
    _line(d, [(cx, cy - s * 0.04), (cx, cy + s * 0.44)], w * 1.1)


def g_snake(d, cx, cy, s, rng):
    """A horizontal wavy snake with a raised head."""
    w = s * 0.08
    pts = [(cx - s * 0.42 + i * s * 0.07, cy + s * 0.18 + s * 0.07 * math.sin(i * 0.9)) for i in range(10)]
    pts += [(cx + s * 0.26, cy + s * 0.06), (cx + s * 0.26, cy - s * 0.18)]
    _line(d, pts, w)
    d.ellipse([cx + s * 0.18, cy - s * 0.30, cx + s * 0.38, cy - s * 0.14], fill=255)


def g_beetle(d, cx, cy, s, rng):
    """An oval beetle with a split back and six short legs."""
    w = s * 0.06
    d.ellipse([cx - s * 0.16, cy - s * 0.24, cx + s * 0.16, cy + s * 0.30], fill=255)
    d.ellipse([cx - s * 0.10, cy - s * 0.38, cx + s * 0.10, cy - s * 0.22], fill=255)
    for k, yy in enumerate((-0.12, 0.04, 0.20)):
        for side in (-1, 1):
            _line(d, [(cx + side * s * 0.14, cy + s * yy), (cx + side * s * 0.30, cy + s * (yy - 0.08 + 0.08 * k))], w)


def g_feather(d, cx, cy, s, rng):
    """A tall feather with a curled tip."""
    d.polygon([(cx - s * 0.02, cy + s * 0.44), (cx - s * 0.14, cy + s * 0.05), (cx - s * 0.10, cy - s * 0.30),
               (cx + s * 0.04, cy - s * 0.44), (cx + s * 0.18, cy - s * 0.38), (cx + s * 0.08, cy - s * 0.30),
               (cx + s * 0.12, cy + s * 0.05), (cx + s * 0.03, cy + s * 0.44)], fill=255)


def g_peak(d, cx, cy, s, rng):
    """A stepped pyramid peak."""
    d.polygon([(cx - s * 0.42, cy + s * 0.36), (cx, cy - s * 0.40), (cx + s * 0.42, cy + s * 0.36)], fill=255)


VOCAB = [g_reed, g_bird, g_eye, g_loopcross, g_snake, g_beetle, g_feather, g_wave, g_sun, g_peak]


# ---------------------------------------------------------------------------------------------
# Decal layouts. Each returns the coverage of the carving (H, W) in 0..1.

def canvas(w, h):
    img = Image.new("L", (w * SS, h * SS), 0)
    return img, ImageDraw.Draw(img)


def done(img, w, h):
    return np.asarray(img.resize((w, h), Image.LANCZOS), dtype=np.float32) / 255.0


def d01_sun(rng):
    """A rayed sun over a bar: the door motif of frame 06, as a wall panel."""
    w = h = 1024
    img, d = canvas(w, h)
    S = w * SS
    g_sun(d, S * 0.5, S * 0.42, S * 0.78, rng, rays=12)
    _line(d, [(S * 0.28, S * 0.86), (S * 0.72, S * 0.86)], S * 0.045)
    return done(img, w, h)


def d02_peaks(rng):
    """Two peaks under a small sun, over three rows of water."""
    w = h = 1024
    img, d = canvas(w, h)
    S = w * SS
    sw = S * 0.035
    for px, top, half in ((0.40, 0.22, 0.24), (0.66, 0.36, 0.16)):
        d.line([(S * (px - half), S * 0.60), (S * px, S * top), (S * (px + half), S * 0.60)], fill=255,
               width=int(sw), joint="curve")
        d.line([(S * (px - half * 0.45), S * (0.60 - (0.60 - top) * 0.45)),
                (S * (px - half * 0.10), S * 0.60)], fill=255, width=int(sw * 0.8))
    _line(d, [(S * 0.12, S * 0.62), (S * 0.88, S * 0.62)], sw)
    r = S * 0.06
    d.ellipse([S * 0.70 - r, S * 0.16 - r, S * 0.70 + r, S * 0.16 + r], fill=255)
    for k in range(3):
        g_wave(d, S * 0.5, S * (0.71 + 0.095 * k), S * 0.74, rng, amp=0.035, w=0.042, teeth=12)
    return done(img, w, h)


def d03_column(rng):
    """A framed column of five glyphs, read top to bottom."""
    w, h = 512, 2048
    img, d = canvas(w, h)
    W, H = w * SS, h * SS
    sw = W * 0.05
    for x in (0.10, 0.90):
        _line(d, [(W * x, H * 0.03), (W * x, H * 0.97)], sw)
    picks = [VOCAB[i] for i in rng.permutation(7)[:5]]
    for k, g in enumerate(picks):
        cy = H * (0.03 + 0.94 * (k + 0.5) / 5)
        g(d, W * 0.5, cy, W * 0.62, rng)
        if k:
            _line(d, [(W * 0.26, H * (0.03 + 0.94 * k / 5)), (W * 0.74, H * (0.03 + 0.94 * k / 5))], sw * 0.6)
    return done(img, w, h)


def d04_frieze(rng):
    """A band for the top of a wall: border lines, chevrons and glyphs. Tiles left to right."""
    w, h = 2048, 512
    img, d = canvas(w, h)
    W, H = w * SS, h * SS
    sw = H * 0.045
    for y in (0.10, 0.90):
        d.line([(-W * 0.1, H * y), (W * 1.1, H * y)], fill=255, width=int(sw))
    period = W / 4
    glyphs = [g_bird, g_reed, g_loopcross, g_feather]
    for k in range(4):
        for shift in (-W, 0, W):  # draw across the edges, so the band wraps
            x0 = k * period + shift
            # A chevron pair, then a glyph.
            for j in range(2):
                cx = x0 + period * (0.12 + 0.16 * j)
                d.line([(cx - H * 0.14, H * 0.30), (cx, H * 0.70), (cx + H * 0.14, H * 0.30)], fill=255,
                       width=int(sw), joint="curve")
            glyphs[k](d, x0 + period * 0.68, H * 0.50, H * 0.62, rng)
    return done(img, w, h)


def d05_cartouche(rng):
    """A rounded name ring with a bar at its foot, holding three glyphs."""
    w, h = 512, 1024
    img, d = canvas(w, h)
    W, H = w * SS, h * SS
    sw = W * 0.05
    d.rounded_rectangle([W * 0.12, H * 0.05, W * 0.88, H * 0.87], radius=W * 0.36, outline=255, width=int(sw))
    _line(d, [(W * 0.08, H * 0.93), (W * 0.92, H * 0.93)], sw * 1.2)
    g_sun(d, W * 0.5, H * 0.20, W * 0.52, rng, rays=8)
    g_feather(d, W * 0.5, H * 0.45, W * 0.52, rng)
    g_beetle(d, W * 0.5, H * 0.70, W * 0.52, rng)
    return done(img, w, h)


DECALS = [
    ("01", "sun disc with rays over a bar", d01_sun, (100, 100)),
    ("02", "twin peaks, sun and three rows of water", d02_peaks, (100, 100)),
    ("03", "framed column of five glyphs", d03_column, (50, 200)),
    ("04", "frieze band, tiles horizontally", d04_frieze, (200, 50)),
    ("05", "cartouche with three glyphs", d05_cartouche, (50, 100)),
]


# ---------------------------------------------------------------------------------------------

def hand_carve(cov, rng, wrap_x):
    """Wobble the outlines a little, as if cut by hand: no perfectly straight lines."""
    h, w = cov.shape
    amp = max(h, w) * 0.0025
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dy = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 18, mode="wrap")
    dx = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 18, mode="wrap")
    dy *= amp / (dy.std() + 1e-8)
    dx *= amp / (dx.std() + 1e-8)
    return ndimage.map_coordinates(cov, [yy + dy, xx + dx], order=1, mode="grid-wrap" if wrap_x else "constant")


def carve(cov, rng, wrap_x):
    depth_cm, wall_cm = 1.6, 0.9
    inside = cov > 0.5
    if wrap_x:
        pad = 64
        d_in = ndimage.distance_transform_edt(np.pad(inside, ((0, 0), (pad, pad)), mode="wrap"))[:, pad:-pad]
    else:
        d_in = ndimage.distance_transform_edt(inside)
    d_in = d_in / PX_PER_CM + (cov - 0.5) / PX_PER_CM  # sub-pixel edge from the antialiased coverage
    h = -depth_cm * tx.smoothstep(-0.05, wall_cm, d_in)
    h = ndimage.gaussian_filter(h, 1.2, mode="wrap" if wrap_x else "nearest")
    n = tx.normal_from_height(h, 1.0 / PX_PER_CM, wrap=True)

    deep = tx.smoothstep(0, depth_cm, -h)
    face = (n[..., 0] * -0.5 + n[..., 1] * -0.85) / math.hypot(0.5, 0.85)
    slope = np.clip((1 - n[..., 2]) * 5, 0, 1)
    col = tx.mix(SAND * 0.85, CARVE_FLOOR, deep)
    col = tx.mix(col, CARVE_LIT, np.clip(face, 0, 1) * slope * 0.85)
    col = tx.mix(col, CARVE_DARK, np.clip(-face, 0, 1) * slope * 0.75)
    paint = ndimage.gaussian_filter(rng.standard_normal(cov.shape).astype(np.float32), 10, mode="wrap")
    col *= (1 + 0.6 * paint / (paint.std() + 1e-8) * 0.04)[..., None]

    alpha = tx.smoothstep(0.02, 0.45, ndimage.gaussian_filter(cov, 1.5, mode="wrap" if wrap_x else "constant"))
    alpha = np.maximum(alpha, slope * (cov > 0.02))
    # Outside the carving the color doesn't show; fill it with the groove's mean so mips don't halo.
    mean = col[alpha > 0.5].mean(0)
    col = tx.mix(np.broadcast_to(mean, col.shape).astype(np.float32), col, tx.smoothstep(0.0, 0.2, alpha))
    nflat = np.zeros_like(n)
    nflat[..., 2] = 1
    n = tx.mix(nflat, n, tx.smoothstep(0.0, 0.2, alpha))
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.clip(col, 0, 1), alpha, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=HERE)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    dx_check = tx.check_directx_convention()

    wall_bc = tx.read_back(os.path.join(args.out, "T_Sandstone_Wall_BC.png")).astype(np.float32)
    wall_n = tx.decode_normal(tx.read_back(os.path.join(args.out, "T_Sandstone_Wall_N.png")).astype(np.float32))
    wall_px_per_cm = 2048 / 300.0

    report = {
        "generator": tx.rel(os.path.join(HERE, "make_hieroglyphs.py")),
        "command": "python3 -I SourceArt/HZ/HZ-A5/make_hieroglyphs.py",
        "seed": SEED,
        "design_density_px_per_m": PX_PER_CM * 100,
        "normal_convention": "DirectX (green down, Y-); Unreal's own, so leave Flip Green Channel off",
        "normal_self_test": dx_check,
        "color_space": {"BC": "sRGB", "Mask": "linear", "N": "linear"},
        "decals": {},
    }
    tiles = []
    for num, desc, fn, size_cm in DECALS:
        rng = np.random.default_rng(SEED * 10 + int(num))
        wrap_x = num == "04"
        cov = hand_carve(fn(rng), rng, wrap_x)
        col, alpha, n = carve(cov, rng, wrap_x)
        base = os.path.join(args.out, "T_Hieroglyph_%s" % num)
        files = {"BC": tx.save_png(base + "_BC.png", col), "Mask": tx.save_png(base + "_Mask.png", alpha),
                 "N": tx.save_png(base + "_N.png", tx.encode_normal(n))}
        m = tx.read_back(files["Mask"])
        h, w = m.shape
        border = np.concatenate([m[0], m[-1]] + ([] if wrap_x else [m[:, 0], m[:, -1]]))
        entry = {
            "description": desc,
            "resolution_px": [w, h],
            "decal_size_cm": list(size_cm),
            "coverage_percent": round(float((m > 0.5).mean() * 100), 1),
            "border_mask_max": round(float(border.max()), 4),
            "outputs": {k: {"file": tx.rel(p), "sha256": tx.sha256(p), "bytes": os.path.getsize(p)}
                        for k, p in files.items()},
        }
        if wrap_x:
            entry["x_wrap"] = {k: tx.seam_report(tx.read_back(p), axes=("x",))["x"] for k, p in files.items()}
            entry["tileable_x"] = all(tx.seam_ok({"x": v}) for v in entry["x_wrap"].values())
        ok = entry["border_mask_max"] == 0.0 and entry.get("tileable_x", True)
        entry["ok"] = ok
        report["decals"]["T_Hieroglyph_" + num] = entry
        print("T_Hieroglyph_%s" % num, desc, "ok" if ok else "FAILED", flush=True)

        # Contact-sheet tile: the decal on the picked wall at its design size, lit, beside its mask.
        ww, wh = int(size_cm[0] * wall_px_per_cm), int(size_cm[1] * wall_px_per_cm)
        x0, y0 = 300 * (int(num) - 1), 900
        ys, xs = (np.arange(wh) + y0) % 2048, (np.arange(ww) + x0) % 2048
        wbc = tx.resize(wall_bc[np.ix_(ys, xs)], (w, h))
        wn = tx.decode_normal(tx.resize(tx.encode_normal(wall_n[np.ix_(ys, xs)]), (w, h)))
        a = tx.read_back(files["Mask"]).astype(np.float32)
        dbc = tx.read_back(files["BC"]).astype(np.float32)
        dn = tx.decode_normal(tx.read_back(files["N"]).astype(np.float32))
        bc = tx.mix(wbc, dbc, a)
        nn = tx.mix(wn, dn, a)
        nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
        shaded = tx.shade(bc, nn)
        checker = ((np.indices((h, w)) // 32).sum(0) % 2).astype(np.float32) * 0.15 + 0.35
        on_checker = tx.mix(np.repeat(checker[..., None], 3, -1), dbc, a)
        tiles.append((num, desc, size_cm, shaded, on_checker))

    # Contact sheet: each decal on the wall (lit), and its BC over its mask on a checker.
    cell = 440
    rows = []
    for num, desc, size_cm, shaded, on_checker in tiles:
        h, w = shaded.shape[:2]
        sc = cell / max(h, w)
        sz = (max(1, int(w * sc)), max(1, int(h * sc)))
        row = np.zeros((cell, cell * 2 + 24, 3), np.float32) + tx.hex_rgb(tx.SHADOW)
        for j, img in enumerate((shaded, on_checker)):
            small = tx.resize(img, sz)
            ox = j * (cell + 24) + (cell - sz[0]) // 2
            oy = (cell - sz[1]) // 2
            row[oy:oy + sz[1], ox:ox + sz[0]] = small
        rows.append(tx.label(row, "T_Hieroglyph_%s: %s, %d x %d cm" % (num, desc, size_cm[0], size_cm[1])))
    gap = np.zeros((16, rows[0].shape[1], 3), np.float32) + tx.hex_rgb(tx.SHADOW)
    sheet = np.concatenate(sum([[r, gap] for r in rows], [])[:-1], 0)
    tx.save_png(os.path.join(args.out, "T_Hieroglyph_contact_sheet.png"), sheet)

    report["all_ok"] = all(e["ok"] for e in report["decals"].values())
    tx.write_json(os.path.join(args.out, "T_Hieroglyph.validation.json"), report)
    if not report["all_ok"]:
        sys.exit("decal checks failed")


if __name__ == "__main__":
    main()
