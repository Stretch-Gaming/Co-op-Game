"""HZ-A5: painted, tileable sandstone for Map 2's walls and floor, for world-aligned M_Stylized
instances. Everything is drawn from fixed seeds with numpy and scipy: no photos, no downloads.

    python3 -I SourceArt/HZ/HZ-A5/make_sandstone.py                 # writes the picked sets here
    python3 -I SourceArt/HZ/HZ-A5/make_sandstone.py OUT --candidates /tmp/HZ-A5-candidates

Two candidates per material are built every run. The picked one is written to OUT (default: this
folder) as 2048 x 2048 PNGs; both are shown side by side in T_Sandstone_<Wall|Floor>_candidates.png.
With --candidates DIR the full-size maps of every candidate go to DIR too (keep DIR outside the repo).

Per material (Wall, Floor):
    _BC   base color, sRGB
    _N    normal, DirectX convention (green down, Y-), linear
    _R    roughness, linear
    _AO   ambient occlusion, linear, 1 = open
    _H    height, 16-bit, linear, 0 = deepest joint, 1 = highest face
    _ARM  M_Stylized's packed mask, linear: R = cavity/edge (0.5 flat, above 0.6 convex edges,
          below 0.4 joints), G = roughness, B = metallic (0)
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import hz_tex as tx  # noqa: E402

N = 2048
PICK = {"Wall": "A", "Floor": "A"}

SAND = tx.hex_rgb(tx.SANDSTONE)
# Painted variations around the palette's sandstone, for block-to-block color shifts. None of
# them is near the reserved relic gold (#E8B33A) or trap red.
VARIANTS = [tx.hex_rgb(h) for h in ("#D9A86C", "#E2B681", "#CF9C62", "#D8A074", "#D4AA78")]
HIGHLIGHT = tx.hex_rgb("#F3D6A6")  # sunlit edge
FRESH = tx.hex_rgb("#E9C08F")  # inside a chip, where newer stone shows
MORTAR = tx.hex_rgb("#7A6062")  # joints: a warm violet-brown, never black
SHADE = tx.mix(SAND * 0.62, tx.hex_rgb(tx.SHADOW), 0.25)  # down-facing bevels and cracks


# ---------------------------------------------------------------------------------------------
# Layouts. Each returns an integer label per pixel; labels wrap across the tile's edges.

def split_exact(total, lo, hi, rng):
    """Random lengths in [lo, hi] that sum exactly to `total` (after a gentle rescale)."""
    for _ in range(200):
        parts = []
        while sum(parts) < total - lo * 0.5:
            parts.append(rng.uniform(lo, hi))
        parts = np.array(parts) * total / sum(parts)
        if parts.min() >= lo * 0.85 and parts.max() <= hi * 1.15:
            return parts
    raise RuntimeError("could not split %s into [%s, %s]" % (total, lo, hi))


def coursed(rng, tile_cm, course_lo, course_hi, block_lo, block_hi, min_joint_cm, warp, split_p=0.0):
    """Running-bond courses: rows of blocks whose vertical joints stay `min_joint_cm` away from
    the joints of the row below. `warp` = (cycles, px) wobbles every line. `split_p` cuts that
    share of blocks into two smaller stacked slabs, for a random-ashlar floor."""
    px = N / tile_cm
    heights = split_exact(tile_cm, course_lo, course_hi, rng)
    rows = []
    for r in range(len(heights)):
        for _ in range(500):
            widths = split_exact(tile_cm, block_lo, block_hi, rng)
            offset = rng.uniform(0, tile_cm)
            joints = (np.cumsum(widths) + offset) % tile_cm
            ok = True
            for prev in rows[-1:] + (rows[:1] if r == len(heights) - 1 else []):
                d = np.abs(joints[:, None] - prev[1][None, :])
                d = np.minimum(d, tile_cm - d)
                ok &= d.min() >= min_joint_cm
            if ok:
                break
        rows.append((widths, joints, offset))
    dy, dx = tx.warp_coords((N, N), rng, warp[0], warp[1])
    ey, ex = tx.warp_coords((N, N), rng, warp[0] * 6, warp[1] * 0.35)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    y0 = rng.uniform(0, tile_cm)  # keep the tile's edge off a bed joint
    y = ((yy + dy + ey) / px + y0) % tile_cm
    x = ((xx + dx + ex) / px) % tile_cm
    cum_h = np.cumsum(heights)
    row = np.minimum(np.searchsorted(cum_h, y, side="right"), len(heights) - 1)
    lab = np.zeros((N, N), np.int32)
    splits = 0
    for r, (widths, _joints, offset) in enumerate(rows):
        m = row == r
        xr = (x[m] - offset) % tile_cm
        i = np.minimum(np.searchsorted(np.cumsum(widths), xr, side="right"), len(widths) - 1)
        if split_p:
            cut = np.where(rng.random(len(widths)) < split_p, rng.uniform(0.4, 0.6, len(widths)), 2.0)
            splits += int((cut < 1).sum())
            rel_y = (y[m] - (cum_h[r] - heights[r])) / heights[r]
            i = i + 50 * (rel_y > cut[i])
        lab[m] = r * 100 + i
    return lab, {"courses_cm": [round(float(h), 1) for h in heights],
                 "blocks_per_course": [len(r[0]) for r in rows], "split_blocks": splits}


def voronoi(rng, tile_cm, cells, relax, warp, metric=2):
    """Relaxed Voronoi flagstones on the torus. metric=np.inf (Chebyshev) gives squarish slabs
    with mostly straight, axis-aligned joints."""
    from scipy.spatial import cKDTree
    pts = rng.uniform(0, N, (cells, 2))
    grid = np.mgrid[0:N:8, 0:N:8].reshape(2, -1).T.astype(np.float64) + 4
    offs = np.array([(i, j) for i in (-N, 0, N) for j in (-N, 0, N)], np.float64)
    for _ in range(relax):  # Lloyd relaxation, on a coarse grid
        tree = cKDTree((pts[None] + offs[:, None]).reshape(-1, 2))
        _, k = tree.query(grid, p=metric)
        owner = k % cells
        rep = (pts[None] + offs[:, None]).reshape(-1, 2)[k]
        delta = grid - rep
        for c in range(cells):
            sel = owner == c
            if sel.any():
                pts[c] = (pts[c] + delta[sel].mean(0)) % N
    dy, dx = tx.warp_coords((N, N), rng, warp[0], warp[1])
    ey, ex = tx.warp_coords((N, N), rng, warp[0] * 6, warp[1] * 0.35)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float64)
    q = np.stack([(yy + dy + ey).ravel() % N, (xx + dx + ex).ravel() % N], 1)
    tree = cKDTree((pts[None] + offs[:, None]).reshape(-1, 2))
    _, k = tree.query(q, p=metric)
    return (k % cells).reshape(N, N).astype(np.int32), {"cells": cells, "lloyd_iterations": relax, "metric": "chebyshev" if metric == np.inf else "euclidean"}


# ---------------------------------------------------------------------------------------------
# Sculpting: rounded, beveled blocks with lumps, tilt, chips and a few cracks.

def chip(h, chipmask, cy, cx, r_px, floor_level, rng):
    """Bite an irregular cone out of h around (cy, cx), wrapping at the edges."""
    k = int(r_px * 1.6) + 2
    ys = (np.arange(cy - k, cy + k + 1)) % N
    xs = (np.arange(cx - k, cx + k + 1)) % N
    oy, ox = np.mgrid[-k:k + 1, -k:k + 1].astype(np.float32)
    ang = np.arctan2(oy, ox)
    p1, p2 = rng.uniform(0, 2 * np.pi, 2)
    rad = r_px * (1 + 0.22 * np.sin(3 * ang + p1) + 0.12 * np.sin(5 * ang + p2))
    dist = np.sqrt(oy ** 2 + ox ** 2) / rad
    bite = floor_level + np.clip(dist, 0, None) ** 1.6 * (h[np.ix_(ys, xs)].max() - floor_level)
    win = h[np.ix_(ys, xs)]
    h[np.ix_(ys, xs)] = np.minimum(win, bite)
    chipmask[np.ix_(ys, xs)] = np.maximum(chipmask[np.ix_(ys, xs)], tx.smoothstep(1.05, 0.7, dist))


def sculpt(lab, rng, tile_cm, gap_cm, bevel_cm, radius_cm, relief_cm, lump_cm, tilt_cm,
           chips, chip_cm, cracks, crack_len_cm, edge_noise_cm):
    px_cm = tile_cm / N
    uniq, idx = np.unique(lab, return_inverse=True)
    idx = idx.reshape(lab.shape)
    n = len(uniq)
    cy, cx, oy, ox = tx.wrapped_centroids(idx, n, lab.shape)
    half_h = np.sqrt(np.bincount(idx.ravel(), (oy ** 2).ravel(), n) / np.bincount(idx.ravel(), None, n)) * 1.73
    half_w = np.sqrt(np.bincount(idx.ravel(), (ox ** 2).ravel(), n) / np.bincount(idx.ravel(), None, n)) * 1.73

    radius_px = radius_cm / px_cm
    s = tx.rounded_inset(lab, radius_px, int(radius_px + bevel_cm / px_cm + 64)) * px_cm
    s = tx.blur_wrap(s, 2.5)  # soften the pixel staircase of the label edges
    s += tx.fbm((N, N), rng, 9, octaves=2) * edge_noise_cm
    t = np.clip((s - gap_cm) / bevel_cm, 0, 1)
    prof = 1 - (1 - t) ** 2.2

    lumps = tx.fbm((N, N), rng, 4, octaves=2)
    offs = rng.normal(0, 0.18, n).astype(np.float32) * relief_cm
    sy, sx = rng.uniform(-1, 1, (2, n)).astype(np.float32)
    tilt = (sy[idx] * oy / (half_h[idx] + 1) + sx[idx] * ox / (half_w[idx] + 1)) * tilt_cm
    plateau = relief_cm + offs[idx] + lumps * lump_cm + tilt
    floor_ = tx.band_noise((N, N), rng, 30) * 0.15
    h = floor_ + (plateau - floor_) * prof

    chipmask = np.zeros((N, N), np.float32)
    near = np.argwhere((t > 0.15) & (t < 0.95))
    for _ in range(chips):
        y0, x0 = near[rng.integers(len(near))]
        r = rng.uniform(*chip_cm) / px_cm
        chip(h, chipmask, int(y0), int(x0), r, relief_cm * rng.uniform(0.25, 0.5), rng)

    crackmask = np.zeros((N, N), np.float32)
    if cracks:
        inner = np.argwhere((t > 0.5) & (t < 1.0))
        paths = []
        for _ in range(cracks):
            y0, x0 = inner[rng.integers(len(inner))]
            ang = rng.uniform(0, 2 * np.pi)
            pts = [(float(x0), float(y0))]
            steps = int(rng.uniform(*crack_len_cm) / px_cm / 14)
            for _ in range(max(steps, 3)):
                ang += rng.normal(0, 0.45)
                x, y = pts[-1]
                pts.append((x + np.cos(ang) * 14, y + np.sin(ang) * 14))
            paths.append((pts, rng.uniform(0.9, 1.5) / px_cm))

        def draw(d):
            for pts, w in paths:
                for i in range(len(pts) - 1):
                    taper = 1 - i / len(pts)
                    (x1, y1), (x2, y2) = pts[i], pts[i + 1]
                    d.line([(x1 * d.s + d.off, y1 * d.s + d.off), (x2 * d.s + d.off, y2 * d.s + d.off)],
                           fill=255, width=max(1, int(w * taper * d.s)))
        crackmask = tx.raster_wrap((N, N), 64, draw)
        crackmask = tx.blur_wrap(crackmask, 1.2)
        h -= crackmask * relief_cm * 0.35 * prof

    h = tx.blur_wrap(h, 1.0)
    return {"h": h, "prof": prof, "t": t, "idx": idx, "n": n, "oy": oy, "ox": ox, "half_h": half_h,
            "half_w": half_w, "chip": chipmask, "crack": crackmask, "px_cm": px_cm, "relief": relief_cm,
            "lumps": lumps}


# ---------------------------------------------------------------------------------------------
# Painting.

def paint(g, rng, stroke_angle, top_gradient):
    h, prof, idx, n = g["h"], g["prof"], g["idx"], g["n"]
    nrm = tx.normal_from_height(h, g["px_cm"])

    pick = rng.choice(len(VARIANTS), n, p=[0.34, 0.2, 0.18, 0.14, 0.14])
    var = np.stack(VARIANTS)[pick]
    val = np.clip(1 + rng.normal(0, 0.045, n), 0.9, 1.1).astype(np.float32)
    col = tx.mix(SAND, var[idx], 0.55) * val[idx][..., None]

    mottle = tx.fbm((N, N), rng, 3, octaves=3)
    col *= (1 + 0.045 * mottle)[..., None]
    strokes = tx.band_noise((N, N), rng, 16, width=0.4, aniso=4.0, angle=stroke_angle)
    strokes = tx.smoothstep(-0.35, 0.35, strokes) - 0.5  # soft-posterized: reads as brush patches
    col = tx.mix(col, tx.mix(col, HIGHLIGHT, 0.5), np.clip(strokes, 0, None) * 0.22)
    col *= (1 - 0.05 * np.clip(-strokes, 0, None))[..., None]

    if top_gradient:  # each block a little lighter at its top and darker at its foot
        v = np.clip(-g["oy"] / (g["half_h"][idx] + 1), -1, 1)
        col *= (1 + 0.05 * v)[..., None]
    else:  # floor: worn lighter toward each slab's middle
        r = np.sqrt((g["oy"] / (g["half_h"][idx] + 1)) ** 2 + (g["ox"] / (g["half_w"][idx] + 1)) ** 2)
        col *= (1 + 0.035 * np.clip(1 - r, 0, 1))[..., None]

    # Painted light on the bevels: top-left facing edges catch light, the others fall to shade.
    face = (nrm[..., 0] * -0.5 + nrm[..., 1] * -0.85) / np.hypot(0.5, 0.85)
    tilt = 1 - nrm[..., 2]
    col = tx.mix(col, HIGHLIGHT, np.clip(face, 0, 1) * np.clip(tilt * 6, 0, 1) * 0.55)
    col = tx.mix(col, SHADE, np.clip(-face, 0, 1) * np.clip(tilt * 6, 0, 1) * 0.40)

    curv = h - tx.blur_wrap(h, 10)
    rim = np.clip(curv / (g["relief"] * 0.18), 0, 1) * prof
    col = tx.mix(col, HIGHLIGHT, rim * 0.35)

    col = tx.mix(col, FRESH, g["chip"] * 0.35)
    col = tx.mix(col, SHADE, g["crack"] * 0.75)

    ao = np.clip(1 - 1.4 * np.clip(tx.blur_wrap(h, 14) - h, 0, None) / g["relief"], 0.35, 1)
    ao = np.minimum(ao, 0.45 + 0.55 * prof ** 0.5)
    gap = 1 - prof ** 0.7
    col = tx.mix(col, MORTAR * (1 + 0.08 * mottle)[..., None], gap)
    col = tx.mix(col, col * tx.mix(SHADE / SAND, np.ones(3, np.float32), 0.3), (1 - ao) * 0.45)

    rough = np.clip(0.88 + 0.03 * mottle - 0.08 * rim + 0.07 * gap + 0.04 * g["chip"], 0.7, 0.98)
    cav = 0.5 + 0.5 * np.clip(curv / (g["relief"] * 0.22), -1, 1)
    cav = np.where(prof < 0.5, np.minimum(cav, 0.15 + 0.5 * prof), cav)
    arm = np.stack([cav, rough, np.zeros_like(rough)], -1)
    hn = (h - h.min()) / (h.max() - h.min())
    return {"BC": np.clip(col, 0, 1), "N": tx.encode_normal(nrm), "R": rough, "AO": ao, "H": hn, "ARM": arm,
            "_normal": nrm}


# ---------------------------------------------------------------------------------------------

CANDIDATES = {
    "Wall": {
        "tile_cm": 300, "seed": 5601, "stroke_angle": 0.05, "top_gradient": True,
        "A": dict(name="coursed ashlar", layout=("coursed", dict(course_lo=54, course_hi=66, block_lo=80,
                  block_hi=140, min_joint_cm=22, warp=(5, 5))),
                  sculpt=dict(gap_cm=1.0, bevel_cm=6.0, radius_cm=6.0, relief_cm=5.0, lump_cm=0.5, tilt_cm=0.6,
                              chips=12, chip_cm=(6, 11), cracks=3, crack_len_cm=(15, 35), edge_noise_cm=0.5)),
        "B": dict(name="rough uneven courses", layout=("coursed", dict(course_lo=38, course_hi=88, block_lo=45,
                  block_hi=150, min_joint_cm=12, warp=(4, 14))),
                  sculpt=dict(gap_cm=1.4, bevel_cm=7.0, radius_cm=9.0, relief_cm=6.0, lump_cm=1.2, tilt_cm=1.2,
                              chips=24, chip_cm=(6, 13), cracks=8, crack_len_cm=(15, 40), edge_noise_cm=0.9)),
    },
    "Floor": {
        "tile_cm": 400, "seed": 5602, "stroke_angle": 0.6, "top_gradient": False,
        "A": dict(name="random-ashlar flagstones", layout=("coursed", dict(course_lo=95, course_hi=140, block_lo=80,
                  block_hi=190, min_joint_cm=30, warp=(4, 11), split_p=0.3)),
                  sculpt=dict(gap_cm=1.6, bevel_cm=7.0, radius_cm=10.0, relief_cm=5.0, lump_cm=0.6, tilt_cm=0.9,
                              chips=10, chip_cm=(7, 13), cracks=4, crack_len_cm=(25, 50), edge_noise_cm=0.6)),
        "B": dict(name="squarish Voronoi flagstones", layout=("voronoi", dict(cells=11, relax=3, warp=(4, 9),
                  metric=np.inf)),
                  sculpt=dict(gap_cm=1.6, bevel_cm=7.0, radius_cm=12.0, relief_cm=5.0, lump_cm=0.6, tilt_cm=0.9,
                              chips=10, chip_cm=(7, 13), cracks=4, crack_len_cm=(25, 50), edge_noise_cm=0.6)),
    },
}


def build(material, key):
    spec = CANDIDATES[material]
    cand = spec[key]
    # One seed per material and candidate, so changing one never shifts the other.
    rng = np.random.default_rng(spec["seed"] * 10 + ord(key))
    kind, args = cand["layout"]
    if kind == "coursed":
        lab, layout_info = coursed(rng, spec["tile_cm"], **args)
    else:
        lab, layout_info = voronoi(rng, spec["tile_cm"], **args)
    g = sculpt(lab, rng, spec["tile_cm"], **cand["sculpt"])
    maps = paint(g, rng, spec["stroke_angle"], spec["top_gradient"])
    maps["_info"] = dict(layout_info, cells=int(g["n"]))
    maps["_prof"] = g["prof"]
    maps["_chip"] = g["chip"]
    return maps


def lit(maps):
    return tx.shade(maps["BC"], tx.decode_normal(maps["N"]), maps["AO"])


def tiled(img, tiles, panel):
    big = np.tile(img, (tiles, tiles, 1) if img.ndim == 3 else (tiles, tiles))
    if big.ndim == 2:
        big = np.repeat(big[..., None], 3, -1)
    return tx.resize(big, (panel, panel))


def save_set(material, maps, out, picked_key):
    base = os.path.join(out, "T_Sandstone_%s" % material)
    files = {}
    for k in ("BC", "N", "R", "AO", "ARM"):
        files[k] = tx.save_png("%s_%s.png" % (base, k), maps[k])
    files["H"] = tx.save_png("%s_H.png" % base, maps["H"], bits=16)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=HERE)
    ap.add_argument("--candidates", help="also write every candidate's full maps here (outside the repo)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    dx_check = tx.check_directx_convention()

    for material in ("Wall", "Floor"):
        spec = CANDIDATES[material]
        built = {}
        for key in ("A", "B"):
            print("building", material, key, spec[key]["name"], flush=True)
            built[key] = build(material, key)
            if args.candidates:
                save_set(material + "_" + key, built[key], args.candidates, key)

        # Candidates sheet: each candidate lit and tiled 3 x 3, side by side.
        panels = []
        for key in ("A", "B"):
            tag = "%s: %s%s" % (key, spec[key]["name"], "  (picked)" if key == PICK[material] else "")
            panels.append(tx.label(tiled(lit(built[key]), 3, 768), tag))
        gap = np.full((768, 16, 3), tx.hex_rgb(tx.SHADOW))
        sheet = np.concatenate([panels[0], gap, panels[1]], 1)
        tx.save_png(os.path.join(args.out, "T_Sandstone_%s_candidates.png" % material), sheet)

        maps = built[PICK[material]]
        files = save_set(material, maps, args.out, PICK[material])

        # Preview: base color and lit, both tiled 3 x 3, over a strip of the single-tile maps.
        bc3 = tx.label(tiled(maps["BC"], 3, 1024), "T_Sandstone_%s_BC, 3 x 3 = %d cm" % (material, spec["tile_cm"] * 3))
        lit3 = tx.label(tiled(lit(maps), 3, 1024), "Lit with _N and _AO (preview lights, not Unreal)")
        strip = []
        for k in ("BC", "N", "R", "AO", "H"):
            m = maps[k]
            strip.append(tx.label(tiled(m, 1, 409), "_" + k))
        strip = np.concatenate(strip + [np.full((409, 2048 - 409 * 5, 3), tx.hex_rgb(tx.SHADOW))], 1)
        preview = np.concatenate([np.concatenate([bc3, lit3], 1), strip], 0)
        tx.save_png(os.path.join(args.out, "T_Sandstone_%s_preview.png" % material), preview)

        # Validation, on the files as written.
        prof = maps["_prof"]
        face = (prof > 0.98) & (maps["_chip"] < 0.05)
        bc_written = tx.read_back(files["BC"])
        seams = {}
        for k, path in files.items():
            seams[k] = tx.seam_report(tx.read_back(path))
        report = {
            "generator": tx.rel(os.path.join(HERE, "make_sandstone.py")),
            "command": "python3 -I SourceArt/HZ/HZ-A5/make_sandstone.py",
            "seed": spec["seed"],
            "candidates": {k: spec[k]["name"] for k in ("A", "B")},
            "picked": PICK[material],
            "layout": maps["_info"],
            "resolution_px": [N, N],
            "tile_size_cm": spec["tile_cm"],
            "texel_density_px_per_m": round(N / spec["tile_cm"] * 100, 1),
            "world_aligned": {"UseWorldAligned": True, "WorldTileSize": float(spec["tile_cm"])},
            "outputs": {k: {"file": tx.rel(p), "sha256": tx.sha256(p), "bytes": os.path.getsize(p)}
                        for k, p in files.items()},
            "color_space": {"BC": "sRGB", "N": "linear", "R": "linear", "AO": "linear", "H": "linear",
                            "ARM": "linear"},
            "bit_depth": {"BC": 8, "N": 8, "R": 8, "AO": 8, "H": 16, "ARM": 8},
            "normal_convention": "DirectX (green down, Y-); Unreal's own, so leave Flip Green Channel off",
            "normal_self_test": dx_check,
            "arm_channels": {"R": "cavity/edge for M_Stylized: 0.5 flat, >0.6 convex edges, <0.4 joints",
                             "G": "roughness", "B": "metallic (0)"},
            "palette_reference": tx.SANDSTONE,
            "face_mean_color": tx.rgb_hex(bc_written[face].mean(0)),
            "overall_mean_color": tx.rgb_hex(bc_written.reshape(-1, 3).mean(0)),
            "roughness_range": [round(float(maps["R"].min()), 3), round(float(maps["R"].max()), 3)],
            "seams": seams,
            "tileable": all(tx.seam_ok(r) for r in seams.values()),
            # The same check on the base color cropped by 37 px, which can't tile: it must fail.
            "control_cropped_bc_fails": not tx.seam_ok(tx.seam_report(bc_written[:-37, :-37])),
        }
        tx.write_json(os.path.join(args.out, "T_Sandstone_%s.validation.json" % material), report)
        print(material, "tileable:", report["tileable"], "face mean", report["face_mean_color"], flush=True)
        if not report["tileable"] or not report["control_cropped_bc_fails"]:
            sys.exit("seam check failed for " + material)


if __name__ == "__main__":
    main()
