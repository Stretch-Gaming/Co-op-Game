"""Shared helpers for the HZ-A5 texture scripts (make_sandstone.py, make_hieroglyphs.py): periodic
noise, wrap-aware distance fields, DirectX normals from height, painted lighting for previews,
seam checks and PNG writing. Pure numpy, scipy and Pillow; nothing is downloaded or sampled.

Run the scripts with `python3 -I`; they put this folder on sys.path themselves.
"""
import hashlib
import json
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "../../.."))

# docs/art/style.md palette entries these textures use. Nothing here uses the relic, ghost,
# trap-warning or crystal colors.
SANDSTONE = "#D9A86C"
SHADOW = "#1E2433"
TORCH_AMBER = "#FFB347"
FILL_TEAL = "#C5F1EF"  # crystal teal mixed with 70% white, as in Tools/blender/asset_kit.py


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


def rgb_hex(c):
    c = np.clip(np.round(np.asarray(c, dtype=np.float64) * 255), 0, 255).astype(int)
    return "#%02X%02X%02X" % tuple(c)


def mix(a, b, t):
    """Linear blend; t may be a scalar or an (H, W) array, a and b colors or (H, W, 3) arrays."""
    t = np.asarray(t, dtype=np.float32)
    if t.ndim == 2:
        t = t[..., None]
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------------------------------------
# Periodic noise. Filtering white noise in the frequency domain gives a field that wraps exactly,
# so every map built from it tiles with no seam.

def _freqs(shape):
    h, w = shape
    fy = np.fft.fftfreq(h) * h  # cycles per tile
    fx = np.fft.rfftfreq(w) * w
    return np.meshgrid(fy, fx, indexing="ij")


def band_noise(shape, rng, cycles, width=0.5, aniso=1.0, angle=0.0):
    """Zero-mean, unit-std periodic noise whose features repeat about `cycles` times per tile.
    `aniso` > 1 stretches features along `angle` (radians, 0 = along x) for brush-like streaks."""
    white = rng.standard_normal(shape).astype(np.float32)
    spec = np.fft.rfft2(white)
    fy, fx = _freqs(shape)
    ca, sa = np.cos(angle), np.sin(angle)
    along = fx * ca + fy * sa
    across = -fx * sa + fy * ca
    r = np.sqrt((along * aniso) ** 2 + across ** 2)
    filt = np.exp(-0.5 * ((r - cycles) / max(cycles * width, 0.75)) ** 2)
    filt[0, 0] = 0.0
    out = np.fft.irfft2(spec * filt, s=shape).astype(np.float32)
    out -= out.mean()
    return out / (out.std() + 1e-8)


def fbm(shape, rng, base_cycles, octaves=4, gain=0.5, **kw):
    out = np.zeros(shape, np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        out += amp * band_noise(shape, rng, base_cycles * 2 ** o, **kw)
        total += amp
        amp *= gain
    return out / total


def warp_coords(shape, rng, cycles, amp_px):
    """A smooth periodic displacement field (dy, dx) in pixels."""
    return (band_noise(shape, rng, cycles) * amp_px, band_noise(shape, rng, cycles) * amp_px)


def sample_wrap(img, dy, dx, order=1):
    """Sample a periodic image at (y + dy, x + dx), wrapping at the edges."""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    coords = [yy + dy, xx + dx]
    if img.ndim == 2:
        return ndimage.map_coordinates(img, coords, order=order, mode="grid-wrap")
    return np.stack([ndimage.map_coordinates(img[..., c], coords, order=order, mode="grid-wrap")
                     for c in range(img.shape[2])], axis=-1)


def blur_wrap(img, sigma):
    return ndimage.gaussian_filter(img, sigma, mode="wrap")


# ---------------------------------------------------------------------------------------------
# Distance fields on a torus. Pad by wrapping, run the Euclidean distance transform, crop back.

def edt_wrap(mask, pad):
    """Distance from each pixel to the nearest True pixel of `mask`, measured across the wrap.
    Distances beyond `pad` pixels are only approximate, so pad by more than you need."""
    m = np.pad(mask, pad, mode="wrap")
    d = ndimage.distance_transform_edt(~m)
    return d[pad:-pad, pad:-pad].astype(np.float32)


def label_boundary(labels):
    b = np.zeros(labels.shape, bool)
    for axis in (0, 1):
        for shift in (1, -1):
            b |= labels != np.roll(labels, shift, axis=axis)
    return b


def rounded_inset(labels, radius, pad):
    """Inward distance from each cell's outline, with the cell's corners rounded to `radius`
    pixels. 0 on the outline, growing toward the cell's middle (capped near radius + pad)."""
    d_in = edt_wrap(label_boundary(labels), pad)
    core = d_in > radius
    d_core = edt_wrap(core, pad)
    return radius - d_core + np.where(core, d_in - radius, 0.0)


def fold_max(canvas, pad, shape):
    """Fold a canvas drawn with a `pad`-pixel margin back onto a tile of `shape`, so shapes that
    cross an edge come back in on the opposite side."""
    h, w = shape
    out = np.zeros(shape, canvas.dtype)
    ch, cw = canvas.shape
    for y0 in range(0, ch, h):
        for x0 in range(0, cw, w):
            part = canvas[y0:y0 + h, x0:x0 + w]
            ty = (y0 - pad) % h
            tx = (x0 - pad) % w
            # Place `part` at (ty, tx) on the torus.
            ys = (np.arange(part.shape[0]) + ty) % h
            xs = (np.arange(part.shape[1]) + tx) % w
            out[np.ix_(ys, xs)] = np.maximum(out[np.ix_(ys, xs)], part)
    return out


def raster_wrap(shape, pad, draw_fn, supersample=2):
    """Rasterize with PIL onto a padded canvas (antialiased by supersampling), then wrap it onto
    the tile. `draw_fn(draw, s)` draws in tile pixel coordinates; multiply them by `s` and add
    `pad * s` (the helper passes `off = pad * s` as draw.off)."""
    h, w = shape
    s = supersample
    img = Image.new("L", ((w + 2 * pad) * s, (h + 2 * pad) * s), 0)
    d = ImageDraw.Draw(img)
    d.s = s
    d.off = pad * s
    draw_fn(d)
    img = img.resize((w + 2 * pad, h + 2 * pad), Image.LANCZOS)
    canvas = np.asarray(img, dtype=np.float32) / 255.0
    return fold_max(canvas, pad, shape)


def wrapped_centroids(idx, n, shape):
    """Per-cell centroid (cy, cx) on the torus, and each pixel's wrapped offset from it."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    out = []
    for coord, size in ((yy, h), (xx, w)):
        ang = coord.astype(np.float64) * 2 * np.pi / size
        s = np.bincount(idx.ravel(), np.sin(ang).ravel(), n)
        c = np.bincount(idx.ravel(), np.cos(ang).ravel(), n)
        cen = (np.arctan2(s, c) % (2 * np.pi)) * size / (2 * np.pi)
        off = (coord - cen[idx] + size / 2) % size - size / 2
        out += [cen, off.astype(np.float32)]
    cy, oy, cx, ox = out
    return cy, cx, oy, ox


# ---------------------------------------------------------------------------------------------
# Normals and shading.

def normal_from_height(height_cm, px_cm, wrap=True):
    """Tangent-space normal in DirectX convention (Unreal's): +X right in red, +Y DOWN the image in
    green ("green down", Y-), +Z out of the surface in blue. `height_cm` is height in centimeters,
    `px_cm` the size of one pixel in centimeters. Returns float unit vectors (H, W, 3)."""
    if wrap:
        dhdx = (np.roll(height_cm, -1, 1) - np.roll(height_cm, 1, 1)) / (2 * px_cm)
        dhdr = (np.roll(height_cm, -1, 0) - np.roll(height_cm, 1, 0)) / (2 * px_cm)
    else:
        dhdr, dhdx = np.gradient(height_cm, px_cm)
    n = np.stack([-dhdx, -dhdr, np.ones_like(dhdx)], axis=-1)  # y axis points down the image
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def check_directx_convention():
    """Sanity test: a dome's upper slope must face up the image, which DirectX stores as green
    below 0.5. Raises if the sign is ever flipped."""
    yy, xx = np.mgrid[0:64, 0:64].astype(np.float32)
    dome = np.clip(1 - ((yy - 32) ** 2 + (xx - 32) ** 2) / 400.0, 0, None) * 10
    n = normal_from_height(dome, 1.0, wrap=False)
    g_top, g_bottom = n[22, 32, 1] * 0.5 + 0.5, n[42, 32, 1] * 0.5 + 0.5
    r_left, r_right = n[32, 22, 0] * 0.5 + 0.5, n[32, 42, 0] * 0.5 + 0.5
    assert g_top < 0.5 < g_bottom, (g_top, g_bottom)
    assert r_left < 0.5 < r_right, (r_left, r_right)
    return {"dome_upper_slope_green": round(float(g_top), 3), "dome_lower_slope_green": round(float(g_bottom), 3),
            "dome_left_slope_red": round(float(r_left), 3), "dome_right_slope_red": round(float(r_right), 3)}


def encode_normal(n):
    return np.clip(n * 0.5 + 0.5, 0, 1)


def decode_normal(rgb):
    return rgb * 2.0 - 1.0


# Preview lights, in image space (x right, y DOWN, z out), echoing asset_kit's preview sheet:
# a warm key from the top left, a soft teal fill from the lower right, a blue-violet ambient.
_KEY = np.array([-0.45, -0.60, 0.66], np.float32)
_FILL = np.array([0.55, 0.45, 0.70], np.float32)


def shade(base, n, ao=None, key=1.0):
    k = _KEY / np.linalg.norm(_KEY)
    f = _FILL / np.linalg.norm(_FILL)
    lk = np.clip((n * k).sum(-1), 0, None)[..., None]
    lf = np.clip((n * f).sum(-1), 0, None)[..., None]
    amb = mix(hex_rgb(SHADOW), np.ones(3, np.float32), 0.55)
    light = amb * 0.42 + lk * hex_rgb("#FFD7A3") * 0.95 * key + lf * hex_rgb(FILL_TEAL) * 0.22
    out = base * light
    if ao is not None:
        out *= (0.35 + 0.65 * ao)[..., None]
    return np.clip(out, 0, 1)


# ---------------------------------------------------------------------------------------------
# Checks and output.

def seam_report(a, axes=("x", "y")):
    """Edge-wrap check. For each axis, the mean step across the wrap seam (last column to first,
    or last row to first) is ranked against the mean step across every interior column or row
    boundary of the same image. A seamless tile's seam ranks like any interior line; a hard
    seam ranks at the very top. Also reports the seam's step relative to the interior average."""
    a = np.asarray(a, dtype=np.float64)
    if a.ndim == 3:
        a = a.mean(-1)
    out = {}
    for ax in axes:
        b = a if ax == "x" else a.T
        seam = float(np.abs(b[:, 0] - b[:, -1]).mean())
        lines = np.abs(np.diff(b, axis=1)).mean(0)
        out[ax] = {
            "seam_mean_step": round(seam, 5),
            "interior_mean_step": round(float(lines.mean()), 5),
            "interior_max_line_step": round(float(lines.max()), 5),
            "seam_to_interior_ratio": round(seam / (float(lines.mean()) + 1e-12), 3),
            "seam_percentile_among_lines": round(float((lines < seam).mean() * 100), 1),
        }
    return out


def seam_ok(rep):
    """Pass when every seam step is no larger than the largest interior line step."""
    return all(r["seam_mean_step"] <= r["interior_max_line_step"] for r in rep.values())


def to8(a):
    return np.clip(np.round(np.asarray(a) * 255.0), 0, 255).astype(np.uint8)


def save_png(path, a, bits=8):
    """Save a float image in 0..1: (H, W) grayscale or (H, W, 3) RGB. bits=16 for grayscale only."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if bits == 16:
        arr = np.clip(np.round(np.asarray(a) * 65535.0), 0, 65535).astype(np.uint16)
        Image.fromarray(arr).save(path, optimize=True)
    else:
        Image.fromarray(to8(a)).save(path, optimize=True)
    return path


def read_back(path):
    """The saved file as float 0..1, so checks run on what was written, not on the floats."""
    im = Image.open(path)
    a = np.asarray(im)
    scale = 65535.0 if a.dtype == np.uint16 or im.mode.startswith("I;16") else 255.0
    return a.astype(np.float64) / scale


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path):
    return os.path.relpath(os.path.abspath(path), REPO).replace(os.sep, "/")


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def resize(a, size):
    """Downscale a float image to (w, h) with Lanczos, for previews."""
    im = Image.fromarray(to8(a))
    return np.asarray(im.resize(size, Image.LANCZOS), dtype=np.float32) / 255.0


def label(img, text, xy=(12, 10), fill=(255, 240, 220)):
    """Burn a small caption into a preview (Pillow's built-in bitmap font; no font files)."""
    im = Image.fromarray(to8(img))
    d = ImageDraw.Draw(im)
    x, y = xy
    for line in text.split("\n"):
        d.rectangle([x - 4, y - 2, x + 7 * len(line) + 4, y + 12], fill=(30, 36, 51))
        d.text((x, y), line, fill=fill)
        y += 16
    return np.asarray(im, dtype=np.float32) / 255.0
