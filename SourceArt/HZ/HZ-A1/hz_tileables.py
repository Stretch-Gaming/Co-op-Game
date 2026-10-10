"""HZ-A1 shared helpers for painted, exactly tileable textures.

Everything here works on a torus: noise is synthesised in the frequency domain, Voronoi cells come
from a periodic KD-tree, blurs and derivatives wrap around. So every map is seamless by
construction, and validate_tileables.py checks that numerically.

Pure numpy / scipy / Pillow. No downloaded data, images or models.
"""
import hashlib
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

# docs/art/style.md palette (sRGB hex). Only the rock and shadow colors are used for surfaces;
# the reserved ones are listed so the validator can prove the textures stay clear of them.
PALETTE = {
    "rock_mid": "#4A4652",
    "rock_light": "#7A6E68",
    "shadow": "#1E2433",
    "torch_amber": "#FFB347",
}
RESERVED = {
    "relic_gold": "#E8B33A",
    "relic_jade": "#3FA672",
    "ghost_white": "#D6F0FF",
    "trap_red": "#FF4A2A",
    "crystal_teal": "#3FD0C9",
}


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, dtype=np.float64), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------------------------
# Periodic noise

def _freqs(n):
    f = np.fft.fftfreq(n) * n  # cycles per tile
    return np.meshgrid(f, f)   # fx varies along columns, fy along rows


def spectral_noise(n, rng, wavelength, aniso=1.0, angle=0.0):
    """Gaussian-filtered white noise with a dominant wavelength (in tile units). Periodic.

    aniso > 1 stretches the blobs along `angle` (radians, image x axis), which reads as brush
    strokes. Returned field has zero mean and unit standard deviation."""
    white = rng.standard_normal((n, n))
    fx, fy = _freqs(n)
    c, s = np.cos(angle), np.sin(angle)
    along = fx * c + fy * s
    across = -fx * s + fy * c
    sigma = 1.0 / max(wavelength, 1e-6)  # cycles per tile
    filt = np.exp(-0.5 * ((along * aniso / sigma) ** 2 + (across / sigma) ** 2))
    out = np.real(np.fft.ifft2(np.fft.fft2(white) * filt))
    out -= out.mean()
    return out / (out.std() + 1e-12)


def fbm(n, rng, wavelength, octaves=4, gain=0.5, lacunarity=2.0):
    total = np.zeros((n, n))
    amp, wl, norm = 1.0, wavelength, 0.0
    for _ in range(octaves):
        total += amp * spectral_noise(n, rng, wl)
        norm += amp
        amp *= gain
        wl /= lacunarity
    total /= norm
    return total / (total.std() + 1e-12)


def blur(a, sigma_px):
    return ndimage.gaussian_filter(a, sigma_px, mode="wrap") if sigma_px > 0 else a


# ---------------------------------------------------------------------------------------------
# Periodic Voronoi

def jittered_sites(rng, count, jitter=0.85):
    """Roughly even sites on the unit torus: a jittered grid, so cell sizes stay chunky."""
    g = int(np.ceil(np.sqrt(count)))
    cells = [(i, j) for i in range(g) for j in range(g)]
    rng.shuffle(cells)
    cells = np.array(cells[:count], dtype=np.float64)
    pts = (cells + 0.5 + (rng.random((count, 2)) - 0.5) * jitter) / g
    return pts % 1.0


def periodic_voronoi(n, sites, warp=None, scale=(1.0, 1.0)):
    """Nearest site index plus exact distance to the cell border, on the torus.

    sites: (M, 2) in [0, 1) as (x, y). warp: optional (dx, dy) arrays in tile units that bend the
    cell borders. scale: anisotropic metric (sx, sy), e.g. (1, 2.5) for cells that are wider
    than tall. Returns idx (n, n), edge distance (n, n) in tile units, rel (n, n, 2) = pixel minus
    its site, wrapped, in tile units."""
    sx, sy = scale
    box = np.array([sx, sy])
    ys, xs = np.mgrid[0:n, 0:n]
    px = (xs + 0.5) / n
    py = (ys + 0.5) / n
    if warp is not None:
        px = px + warp[0]
        py = py + warp[1]
    pts = np.stack([(px % 1.0) * sx, (py % 1.0) * sy], axis=-1).reshape(-1, 2)
    s = (sites % 1.0) * box
    tree = cKDTree(s, boxsize=box)
    _, idx = tree.query(pts, k=3, workers=-1)

    def wrapped(a_idx):
        v = s[a_idx] - pts
        return v - box * np.round(v / box)

    va = wrapped(idx[:, 0])
    edge = np.full(len(pts), np.inf)
    for j in (1, 2):
        vb = wrapped(idx[:, j])
        num = (vb ** 2).sum(1) - (va ** 2).sum(1)
        den = 2 * np.linalg.norm(vb - va, axis=1) + 1e-12
        edge = np.minimum(edge, num / den)
    rel = (-va / box).reshape(n, n, 2)  # back to tile units, pixel relative to its site
    # Distances in the scaled metric; divide by the mean scale to keep them in tile units.
    edge = edge / np.sqrt(sx * sy)
    return idx[:, 0].reshape(n, n), edge.reshape(n, n), rel


def periodic_points_field(n, centers, radii):
    """For scattered round dabs (grit, pebbles): per pixel, nearest center's normalised distance."""
    ys, xs = np.mgrid[0:n, 0:n]
    pts = np.stack([(xs + 0.5) / n, (ys + 0.5) / n], axis=-1).reshape(-1, 2)
    tree = cKDTree(centers % 1.0, boxsize=[1.0, 1.0])
    d, i = tree.query(pts, k=2, workers=-1)
    r = radii[i]
    t = d / r  # < 1 inside a dab
    best = np.argmin(t, axis=1)
    rows = np.arange(len(pts))
    return t[rows, best].reshape(n, n), i[rows, best].reshape(n, n)


# ---------------------------------------------------------------------------------------------
# Derived maps

def normal_from_height(h_cm, tile_cm, strength=1.0):
    """DirectX (green-down) tangent-space normal from a height field in centimeters.

    Image rows increase downward, which is DirectX's +Y, so n = (-dh/dx, -dh/drow, 1)."""
    n = h_cm.shape[0]
    px_cm = tile_cm / n
    dx = (np.roll(h_cm, -1, axis=1) - np.roll(h_cm, 1, axis=1)) / (2 * px_cm)
    dy = (np.roll(h_cm, -1, axis=0) - np.roll(h_cm, 1, axis=0)) / (2 * px_cm)
    v = np.stack([-dx * strength, -dy * strength, np.ones_like(h_cm)], axis=-1)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def cavity_ao(h_cm, tile_cm, radii_cm=(2.0, 6.0, 18.0), depth_cm=4.0):
    """Painted ambient occlusion: how far a pixel sits below its blurred surroundings."""
    n = h_cm.shape[0]
    occ = np.zeros_like(h_cm)
    for r in radii_cm:
        occ += np.maximum(0.0, blur(h_cm, r * n / tile_cm) - h_cm)
    occ /= len(radii_cm)
    return np.clip(1.0 - occ / depth_cm, 0.0, 1.0)


def convexity(h_cm, tile_cm, radius_cm=1.5):
    """Positive on crests and outer edges, negative in creases (scale-free)."""
    n = h_cm.shape[0]
    hs = blur(h_cm, radius_cm * n / tile_cm)
    lap = (np.roll(hs, 1, 0) + np.roll(hs, -1, 0) + np.roll(hs, 1, 1) + np.roll(hs, -1, 1) - 4 * hs)
    c = -lap
    return c / (np.percentile(np.abs(c), 99) + 1e-12)


# ---------------------------------------------------------------------------------------------
# IO

def save_rgb8(path, rgb01):
    a = np.clip(np.round(np.asarray(rgb01) * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(a, "RGB").save(path, optimize=True)


def save_gray8(path, g01):
    a = np.clip(np.round(np.asarray(g01) * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(a, "L").save(path, optimize=True)


def save_gray16(path, g01):
    a = np.clip(np.round(np.asarray(g01) * 65535.0), 0, 65535).astype(np.uint16)
    Image.fromarray(a).save(path)  # Pillow writes uint16 as a 16-bit grayscale PNG


def load_float(path):
    im = Image.open(path)
    a = np.asarray(im)
    scale = 65535.0 if a.dtype == np.uint16 or im.mode.startswith("I") else 255.0
    return a.astype(np.float64) / scale


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def here():
    return os.path.dirname(os.path.abspath(__file__))
