"""HZ-A1: painted, tileable cave rock (walls and ceiling) and cave floor (damp rock and grit).

Each surface is built from a fixed seed as a height field on a torus, then painted: per-facet
color from the style.md rock palette, soft color drift, broad brush strokes, light outer edges
and blue-violet creases (never black). Every map tiles exactly, by construction.

Writes, per surface, into OUT (default: this folder):
  T_<Name>_BC.png   base color, sRGB, 8-bit RGB
  T_<Name>_N.png    normal, DirectX (green-down), linear, 8-bit RGB
  T_<Name>_R.png    roughness, linear, 8-bit gray
  T_<Name>_AO.png   ambient occlusion, linear, 8-bit gray
  T_<Name>_H.png    height, linear, 16-bit gray (range in T_<Name>.generation.json)
  T_<Name>_ORM.png  packed mask for M_Stylized's MaskTexture, linear: R AO/edge, G roughness, B 0
  T_<Name>.generation.json   seed, parameters and height range

    python3 -I SourceArt/HZ/HZ-A1/make_cave_surfaces.py                 # chosen ones, 2048 px
    python3 -I SourceArt/HZ/HZ-A1/make_cave_surfaces.py --candidates /tmp/HZ-A1 --size 1024

--candidates writes every candidate's maps to that folder (keep it outside the repo) and a
contact sheet per surface. README.md explains the choices.
"""
import argparse
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import hz_tileables as tx  # noqa: E402

MID = tx.hex_rgb(tx.PALETTE["rock_mid"])
LIGHT = tx.hex_rgb(tx.PALETTE["rock_light"])
SHADOW = tx.hex_rgb(tx.PALETTE["shadow"])
AMBER = tx.hex_rgb(tx.PALETTE["torch_amber"])
CREASE = tx.lerp(SHADOW, MID, 0.35)                        # blue-violet crease, never black
EDGE = np.clip(tx.lerp(LIGHT, AMBER, 0.10) * 1.18, 0, 1)   # worn outer edge catching light
DAMP = tx.lerp(MID, SHADOW, 0.45)                          # wet rock: darker and cooler

# ---------------------------------------------------------------------------------------------
# Candidates. Lengths are centimeters at the tile size each is designed for (tile_cm, which is
# the WorldTileSize to use). CHOSEN in SURFACES names the one exported to the repo.
#
# Height modes:
#   facet: rounded chunks (Voronoi domes), cut into flat facets by tangent planes, then softened.
#          Reads like the low-poly painted rocks in the style frames.
#   slab:  flat-topped plates with wide rounded bevels down to cracks that grit can fill.

ROCK = {
    "A_facets": dict(
        seed=5201, tile_cm=400, mode="facet",
        chunks=12, scale=(1.0, 1.0), warp=(0.35, 0.025), dome_cm=60.0, chunk_h=(20.0, 5.0),
        chunk_tilt=0.12, facets=110, soften_cm=1.4, lump=(0.25, 1.2),
        value=(0.22, 0.80), facet_value=0.55, stroke=(0.05, 4.0, 0.035), drift=0.06,
        damp=(0.40, 0.08), rough=(0.88, 0.95, 0.80, 0.62), grit=None,
    ),
    "B_strata": dict(
        seed=5202, tile_cm=400, mode="facet",
        chunks=16, scale=(1.0, 2.8), warp=(0.30, 0.02), dome_cm=22.0, chunk_h=(10.0, 3.0),
        chunk_tilt=0.10, facets=160, facet_scale=(1.0, 2.0), soften_cm=1.2, lump=(0.25, 1.0),
        value=(0.12, 0.78), facet_value=0.50, stroke=(0.05, 6.0, 0.035), drift=0.06,
        damp=(0.40, 0.08), rough=(0.88, 0.95, 0.80, 0.62), grit=None,
    ),
    "C_pillows": dict(
        seed=5203, tile_cm=400, mode="facet",
        chunks=20, scale=(1.0, 1.0), warp=(0.35, 0.025), dome_cm=30.0, chunk_h=(12.0, 4.0),
        chunk_tilt=0.10, facets=0, soften_cm=1.0, lump=(0.2, 1.6),
        value=(0.10, 0.80), facet_value=0.0, stroke=(0.05, 4.0, 0.035), drift=0.06,
        damp=(0.40, 0.08), rough=(0.88, 0.95, 0.80, 0.62), grit=None,
    ),
}

FLOOR = {
    "A_slabs": dict(
        seed=5211, tile_cm=300, mode="slab",
        cells=13, scale=(1.0, 1.0), warp=(0.30, 0.02), tilt=0.03, step_cm=1.0, bevel_cm=7.0,
        crack_cm=5.0, facets=60, facet_amt=0.8, soften_cm=0.8, lump=(0.22, 0.8),
        value=(0.35, 0.85), facet_value=0.18, stroke=(0.06, 4.0, 0.03), drift=0.05,
        grit=dict(count=5200, r_cm=(0.7, 2.2), fill_cm=2.6, in_crack=0.95, on_top=0.0004),
        puddles=(0.30, 1.05), damp=(0.30, 0.25), rough=(0.80, 0.93, 0.74, 0.36),
    ),
    "B_cobbles": dict(
        seed=5212, tile_cm=300, mode="slab",
        cells=46, scale=(1.0, 1.0), warp=(0.2, 0.012), tilt=0.05, step_cm=1.2, bevel_cm=9.0,
        crack_cm=4.5, facets=0, facet_amt=0.0, soften_cm=0.8, lump=(0.12, 0.6),
        value=(0.30, 0.85), facet_value=0.0, stroke=(0.04, 4.0, 0.03), drift=0.05,
        grit=dict(count=6500, r_cm=(0.6, 1.8), fill_cm=2.4, in_crack=0.95, on_top=0.0004),
        puddles=(0.30, 1.05), damp=(0.30, 0.25), rough=(0.80, 0.93, 0.74, 0.36),
    ),
    "C_bedrock": dict(
        seed=5213, tile_cm=300, mode="facet",
        chunks=7, scale=(1.0, 1.0), warp=(0.4, 0.03), dome_cm=45.0, chunk_h=(5.0, 2.0),
        chunk_tilt=0.03, facets=70, soften_cm=1.5, lump=(0.3, 1.2),
        value=(0.30, 0.82), facet_value=0.25, stroke=(0.06, 4.0, 0.03), drift=0.05,
        grit=dict(count=3500, r_cm=(0.7, 2.0), fill_cm=1.0, in_crack=0.9, on_top=0.001),
        puddles=(0.30, 0.85), damp=(0.30, 0.25), rough=(0.80, 0.93, 0.74, 0.36),
    ),
}

SURFACES = {
    "rock": dict(name="CaveRock", candidates=ROCK, chosen="A_facets"),
    "floor": dict(name="CaveFloor", candidates=FLOOR, chosen="A_slabs"),
}


# ---------------------------------------------------------------------------------------------
# Height

def grad_tile(h, n):
    """Gradient in height units per tile unit, wrapping."""
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * (n / 2.0)
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * (n / 2.0)
    return gx, gy


def facet_cut(n, rng, d, count, smooth_px, scale=(1.0, 1.0)):
    """Low-poly version of surface d: sample it at jittered points and interpolate linearly over
    a periodic Delaunay triangulation. Facets are flat and meet at continuous ridges and
    valleys, like the planes on the style frames' rocks. Returns the faceted height and a facet
    index per pixel (the same facet gets the same index on both sides of the wrap)."""
    from scipy.spatial import Delaunay
    ds = tx.blur(d, smooth_px)
    sy = scale[1]  # >1 makes facets wider than tall
    sites = tx.jittered_sites(rng, count, jitter=0.9)
    si = np.minimum((sites * n).astype(int), n - 1)
    vals = ds[si[:, 1], si[:, 0]]
    offs = np.array([(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)], dtype=float)
    pts = (sites[None, :, :] + offs[:, None, :]).reshape(-1, 2)
    v = np.tile(vals, len(offs))
    keep = np.all((pts > -0.35) & (pts < 1.35), axis=1)
    pts, v = pts[keep], v[keep]
    tri = Delaunay(pts * np.array([1.0, sy]))
    ys, xs = np.mgrid[0:n, 0:n]
    q = np.stack([(xs + 0.5) / n, (ys + 0.5) / n * sy], -1).reshape(-1, 2)
    simp = tri.find_simplex(q)
    T = tri.transform[simp]
    bary2 = np.einsum("nij,nj->ni", T[:, :2, :], q - T[:, 2, :])
    bary = np.concatenate([bary2, 1 - bary2.sum(1, keepdims=True)], axis=1)
    verts = tri.simplices[simp]
    h = (v[verts] * bary).sum(1).reshape(n, n)
    cen = pts[verts].mean(1) % 1.0
    key = np.round(cen * 4096).astype(np.int64)
    key = (key[:, 0] % 4096) * 4096 + key[:, 1] % 4096
    _, fid = np.unique(key, return_inverse=True)
    return h, fid.reshape(n, n)


def height_facet(n, rng, p):
    tile = p["tile_cm"]
    sites = tx.jittered_sites(rng, p["chunks"])
    wl, amp = p["warp"]
    w = (tx.spectral_noise(n, rng, wl) * amp, tx.spectral_noise(n, rng, wl) * amp)
    cid, edge, rel = tx.periodic_voronoi(n, sites, w, p["scale"])
    m = len(sites)
    hmean, hstd = p["chunk_h"]
    hc = np.maximum(2.0, rng.normal(hmean, hstd, m))
    tilt = rng.normal(0.0, p["chunk_tilt"], (m, 2))
    t = np.clip(edge * tile / p["dome_cm"], 0.0, 1.0)
    dome = 1.0 - (1.0 - t) ** p.get("dome_pow", 2.2)  # rounded shoulder
    d = hc[cid] * dome + (rel[..., 0] * tilt[cid, 0] + rel[..., 1] * tilt[cid, 1]) * tile * dome
    lwl, lamp = p["lump"]
    d = d + tx.fbm(n, rng, lwl, octaves=3, gain=0.45) * lamp
    crevice = 1.0 - dome
    if p["facets"]:
        # Facets sized like the style frames' rock planes: a few per chunk.
        h, fid = facet_cut(n, rng, d, p["facets"], 2.0 * n / 512,
                           p.get("facet_scale", (1.0, 1.0)))
        # Linear facets sit under a rounded cap but bridge over the creases between chunks;
        # the lower of the two keeps both the facets and the chunk creases.
        k = 1.5  # cm; a soft minimum rounds the seam instead of leaving a kink
        h = -k * np.logaddexp(-h / k, -d / k)
    else:
        h, fid = d, cid
    h = tx.blur(h, p["soften_cm"] * n / tile)  # soft, wide bevels instead of knife edges
    return h, cid, fid, m, crevice


def height_slab(n, rng, p):
    tile = p["tile_cm"]
    sites = tx.jittered_sites(rng, p["cells"])
    wl, amp = p["warp"]
    w = (tx.spectral_noise(n, rng, wl) * amp, tx.spectral_noise(n, rng, wl) * amp)
    cid, edge, rel = tx.periodic_voronoi(n, sites, w, p["scale"])
    m = len(sites)
    grad = rng.normal(0.0, p["tilt"], (m, 2))
    base = np.abs(rng.normal(0.0, p["step_cm"], m))
    face = base[cid] + (rel[..., 0] * grad[cid, 0] + rel[..., 1] * grad[cid, 1]) * tile
    lwl, lamp = p["lump"]
    face = face + tx.fbm(n, rng, lwl, octaves=3, gain=0.45) * lamp
    crack = -p["crack_cm"]
    t = np.clip(edge * tile / p["bevel_cm"], 0.0, 1.0)
    prof = 1.0 - (1.0 - t) ** 2.0
    fid = cid
    if p["facets"]:
        # Worn, slightly chipped tops: very shallow facets on each slab.
        f, fid = facet_cut(n, rng, face, p["facets"], 3.0 * n / 512)
        face = face + (f - face) * p["facet_amt"]
    h = crack + (face - crack) * prof
    h = tx.blur(h, p["soften_cm"] * n / tile)
    return h, cid, fid, m, 1.0 - prof


def add_grit(n, rng, p, h, low):
    """Grit and small pebbles: round painted dabs, mostly packed into the low ground."""
    g = p["grit"]
    tile = p["tile_cm"]
    k = g["count"] * 6
    cand = rng.random((k, 2))
    ci = np.minimum((cand * n).astype(int), n - 1)
    lowv = low[ci[:, 1], ci[:, 0]]
    prob = g["on_top"] + (g["in_crack"] - g["on_top"]) * tx.smoothstep(0.25, 0.7, lowv)
    keep = rng.random(k) < prob
    cand = cand[keep][: g["count"]]
    radii = rng.uniform(*g["r_cm"], len(cand))
    # A few bigger pebbles among the grit.
    big = rng.random(len(cand)) < 0.03
    radii = np.where(big, radii * 1.6, radii) / tile
    t, gi = tx.periodic_points_field(n, cand, radii)
    dome = np.sqrt(np.clip(1.0 - t ** 2, 0.0, 1.0)) * (radii[gi] * tile) * 0.75
    # Grit settles on a fill level in the cracks, and sits on the surface elsewhere.
    fill = h.min() + g["fill_cm"]
    seat = np.maximum(h, tx.lerp(h, fill, tx.smoothstep(0.2, 0.8, low)))
    h_new = seat + dome  # dome is zero outside the dabs
    # Between pebbles the fill itself shows: a damp gritty bed.
    h_new = np.maximum(h_new, tx.lerp(h, fill, tx.smoothstep(0.35, 0.9, low)))
    cover = tx.smoothstep(1.0, 0.7, t)
    val = rng.uniform(0.0, 1.0, len(cand))[gi]
    return h_new, cover, val


def build(n, p):
    rng = np.random.default_rng(p["seed"])
    tile = p["tile_cm"]
    if p["mode"] == "facet":
        h, cid, fid, m, low = height_facet(n, rng, p)
    else:
        h, cid, fid, m, low = height_slab(n, rng, p)

    grit_cover = np.zeros((n, n))
    grit_val = np.zeros((n, n))
    bed = np.zeros((n, n))
    if p.get("grit"):
        h0 = h
        h, grit_cover, grit_val = add_grit(n, rng, p, h, low)
        bed = np.clip((h - h0) / 2.0, 0, 1) * (1 - grit_cover)  # visible grit fill between dabs

    h = tx.blur(h, 0.5 * n / 2048)  # anti-alias at any size

    nrm = tx.normal_from_height(h, tile)
    ao = tx.cavity_ao(h, tile, depth_cm=3.5 if p["mode"] == "slab" else 5.0)
    cv = tx.convexity(h, tile, radius_cm=1.2)

    # --- base color (painted) -----------------------------------------------------------------
    vlo, vhi = p["value"]
    v_chunk = rng.uniform(vlo, vhi, m)
    nf = int(fid.max()) + 1
    v_facet = rng.normal(0.0, 1.0, nf)
    warmth = rng.normal(0.0, 1.0, m)
    angle = rng.uniform(0, np.pi, nf)
    v = v_chunk[cid] + p["facet_value"] * 0.5 * np.tanh(v_facet[fid])
    drift = tx.fbm(n, rng, 0.45, octaves=2)
    v = v + p["drift"] * drift
    # Facet shading baked as a direction-free term: steeper reads darker. No key-light
    # direction, so it reads the same on walls, the ceiling and both triplanar mirrors.
    shade = nrm[..., 2] ** 4
    v = v * (0.6 + 0.4 * shade)
    # Broad brush strokes, one direction per facet.
    swl, saniso, samp = p["stroke"]
    angles = np.linspace(0, np.pi, 4, endpoint=False)
    sel = np.digitize(angle, angles[1:])[fid]
    stroke = np.zeros((n, n))
    for i, a in enumerate(angles):
        layer = tx.spectral_noise(n, rng, swl, aniso=saniso, angle=a)
        stroke = np.where(sel == i, layer, stroke)
    v = v + samp * tx.blur(stroke, 1.0 * n / 512)
    v = np.clip(v, 0.0, 1.0)[..., None]
    col = tx.lerp(MID, LIGHT, v)
    col = col + (warmth[cid] * 0.012)[..., None] * np.array([1.0, 0.2, -0.9])
    col = col + (drift * 0.010)[..., None] * np.array([0.8, 0.3, -1.0])

    # Damp: for walls, soft seep patches; for the floor, puddles in the low ground and wet cracks.
    dwl, damp_amt = p["damp"]
    damp = tx.smoothstep(0.7, 1.6, tx.fbm(n, rng, dwl, octaves=2)) * damp_amt * 2.0
    if p.get("puddles"):
        pwl, thr = p["puddles"]
        pn = tx.fbm(n, rng, pwl, octaves=2)
        lowg = -tx.blur(h, 8 * n / tile)
        lowg = (lowg - lowg.mean()) / (lowg.std() + 1e-9)
        puddle = tx.smoothstep(thr, thr + 0.08, 0.6 * pn + 0.6 * lowg)
        damp = np.clip(damp + puddle + 0.6 * tx.smoothstep(0.3, 0.8, low), 0.0, 1.0)
    damp = np.clip(damp, 0.0, 1.0)

    if p.get("grit"):
        gcol = tx.lerp(MID * 0.92, LIGHT * 1.06, grit_val[..., None])
        bedcol = tx.lerp(MID, SHADOW, 0.25)
        col = tx.lerp(col, bedcol, bed[..., None] * 0.9)
        col = tx.lerp(col, gcol, grit_cover[..., None] * 0.9)
    col = tx.lerp(col, DAMP, (damp * 0.40)[..., None])
    crease = np.clip((1.0 - ao) * 1.2 + np.clip(-cv, 0, 1) * 0.45, 0.0, 1.0)
    col = tx.lerp(col, CREASE, crease[..., None] * 0.8)
    edge = tx.smoothstep(0.15, 0.8, cv) * (1.0 - damp * 0.5)
    col = tx.lerp(col, EDGE, edge[..., None] * 0.35)
    bc = np.clip(col, 0.0, 1.0)

    # --- roughness: mostly matte, damp areas glossier ------------------------------------------
    r_face, r_crease, r_edge, r_damp = p["rough"]
    rough = r_face + 0.025 * tx.spectral_noise(n, rng, 0.06)
    rough = tx.lerp(rough, r_crease, np.clip(1.0 - ao, 0, 1))
    rough = tx.lerp(rough, r_edge, tx.smoothstep(0.1, 0.6, cv) * 0.6)
    if p.get("grit"):
        rough = tx.lerp(rough, 0.93, grit_cover * 0.7)
    rough = tx.lerp(rough, r_damp, damp)
    rough = np.clip(rough, 0.0, 1.0)

    # --- packed mask for M_Stylized -----------------------------------------------------------
    # M_Stylized darkens below CavityThreshold (0.4) and adds EdgeColor above EdgeThreshold (0.6),
    # so flat faces sit near 0.5, creases fall under 0.4 and outer edges rise over 0.6.
    edge_mask = np.clip(0.16 + 0.36 * ao + 0.34 * tx.smoothstep(0.05, 0.7, cv), 0.0, 1.0)
    orm = np.stack([edge_mask, rough, np.zeros_like(rough)], axis=-1)
    return dict(bc=bc, nrm=nrm, rough=rough, ao=np.maximum(ao, 0.3), h=h, orm=orm)


# ---------------------------------------------------------------------------------------------
# Output

def save(maps, name, out):
    os.makedirs(out, exist_ok=True)
    h = maps["h"]
    lo, hi = float(h.min()), float(h.max())
    paths = {k: os.path.join(out, f"T_{name}_{k}.png") for k in ("BC", "N", "R", "AO", "H", "ORM")}
    tx.save_rgb8(paths["BC"], maps["bc"])
    tx.save_rgb8(paths["N"], maps["nrm"] * 0.5 + 0.5)
    tx.save_gray8(paths["R"], maps["rough"])
    tx.save_gray8(paths["AO"], maps["ao"])
    tx.save_gray16(paths["H"], (h - lo) / (hi - lo))
    tx.save_rgb8(paths["ORM"], maps["orm"])
    return paths, (lo, hi)


def lit(bc, nrm, ao):
    """Rough stand-in for the in-game look, for previews only: a soft warm key from the image's
    top left plus blue-violet ambient, using the normal map."""
    L = np.array([-0.45, -0.55, 0.70])  # DirectX frame: negative Y points to the image top
    L = L / np.linalg.norm(L)
    d = np.clip((nrm * L).sum(-1), 0, 1)[..., None]
    lin = tx.srgb_to_linear(bc)
    amb = tx.srgb_to_linear(tx.lerp(SHADOW, MID, 0.5)) * 2.2
    key = tx.srgb_to_linear(tx.lerp(np.ones(3), AMBER, 0.25)) * 1.25
    return tx.linear_to_srgb(lin * (amb * ao[..., None] + key * d))


def contact_sheet(surface, results, path, thumb=384):
    labels = list(results)
    w = thumb * 2 * len(labels) + 16 * (len(labels) + 1)
    sheet = Image.new("RGB", (w, thumb + 56), (24, 28, 40))
    draw = ImageDraw.Draw(sheet)
    x = 16
    for key in labels:
        for img in results[key]:
            im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize(
                (thumb, thumb), Image.LANCZOS)
            sheet.paste(im, (x, 40))
            x += thumb
        draw.text((x - 2 * thumb, 14), f"{surface} {key}  (base color | lit with normal)",
                  fill=(220, 220, 230))
        x += 16
    sheet.save(path, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=2048)
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--candidates", help="write every candidate here (outside the repo)")
    ap.add_argument("--only", choices=list(SURFACES), help="one surface")
    a = ap.parse_args()
    for surface, s in SURFACES.items():
        if a.only and surface != a.only:
            continue
        if a.candidates:
            results = {}
            for key, p in s["candidates"].items():
                print(f"{surface} {key} @ {a.size}", flush=True)
                maps = build(a.size, p)
                save(maps, f"{s['name']}_{key}", os.path.join(a.candidates, surface, key))
                results[key] = (maps["bc"], lit(maps["bc"], maps["nrm"], maps["ao"]))
            contact_sheet(surface, results, os.path.join(a.candidates, f"candidates_{surface}.png"))
        else:
            p = s["candidates"][s["chosen"]]
            print(f"{surface} {s['chosen']} @ {a.size} -> {a.out}", flush=True)
            maps = build(a.size, p)
            _, (lo, hi) = save(maps, s["name"], a.out)
            tx.write_json(os.path.join(a.out, f"T_{s['name']}.generation.json"), {
                "task": "HZ-A1",
                "script": "SourceArt/HZ/HZ-A1/make_cave_surfaces.py",
                "candidate": s["chosen"],
                "size_px": a.size,
                "parameters": copy.deepcopy(p),
                "height_range_cm": [round(lo, 4), round(hi, 4)],
                "tool": "Python 3 with numpy, scipy and Pillow; no downloaded data or models",
            })


if __name__ == "__main__":
    main()
