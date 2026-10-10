"""HZ-A1: check the cave textures tile, stay on palette and avoid fine noise; write previews.

    python3 -I SourceArt/HZ/HZ-A1/validate_tileables.py
    python3 -I SourceArt/HZ/HZ-A1/validate_tileables.py --candidates /tmp/HZ-A1

Default: reads the chosen maps in this folder and writes T_<Name>.validation.json plus
previews/T_<Name>_tiled3x3_preview.png (base color tiled 3x3 | lit with the normal map, 3x3).

--candidates: scores every candidate written by make_cave_surfaces.py --candidates and writes
candidates.json and small contact sheets in previews/.

Tileability check: on a seamless texture, the jump across the wrap (last column to first, last
row to first) is no bigger than the ordinary pixel steps right next to it. seam_ratio is the
mean wrap jump divided by the mean of the two neighbouring steps (1.0 is perfect; the limit is
1.25). A crop of the same image that doesn't wrap is measured too, as a control that the check
can fail.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import hz_tileables as tx  # noqa: E402
import make_cave_surfaces as mk  # noqa: E402

SEAM_LIMIT = 1.25
MAPS = {
    "BC": ("base color", "sRGB", "TC_Default (BC1/DXT1)", True),
    "N": ("normal, DirectX green-down", "linear", "TC_Normalmap (BC5)", False),
    "R": ("roughness", "linear", "TC_Grayscale or TC_Masks", False),
    "AO": ("ambient occlusion", "linear", "TC_Grayscale", False),
    "H": ("height, 16-bit", "linear", "TC_Grayscale (or TC_HalfFloat)", False),
    "ORM": ("packed mask: R AO/edge, G roughness, B metallic", "linear", "TC_Masks", False),
}


def rel(path):
    root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    return os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/")


def seam(a):
    a = a if a.ndim == 3 else a[..., None]

    def one(img):
        """Columns of img: wrap step (last column -> first) against the steps either side."""
        steps = np.abs(np.diff(img, axis=1)).mean(axis=(0, 2))
        wrap = float(np.abs(img[:, 0] - img[:, -1]).mean())
        local = wrap / (0.5 * (steps[0] + steps[-1]) + 1e-12)
        return local, wrap / (float(np.median(steps)) + 1e-12), float((steps < wrap).mean())

    lx, mx, px = one(a)
    ly, my, py = one(np.transpose(a, (1, 0, 2)))
    n = a.shape[0]
    c = int(n * 0.37)
    crop = a[: n - c, : n - c]
    cx = one(crop)[0]
    cy = one(np.transpose(crop, (1, 0, 2)))[0]
    return {
        "seam_ratio_x": round(lx, 4), "seam_ratio_y": round(ly, 4),
        "wrap_vs_median_step_x": round(mx, 4), "wrap_vs_median_step_y": round(my, 4),
        "wrap_step_percentile_x": round(px, 4), "wrap_step_percentile_y": round(py, 4),
        "control_nonwrapping_crop_seam_ratio": [round(cx, 3), round(cy, 3)],
        "pass": bool(lx <= SEAM_LIMIT and ly <= SEAM_LIMIT),
    }


def luminance(bc):
    lin = tx.srgb_to_linear(bc)
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]


def style_metrics(bc, tile_cm):
    """Numbers behind style.md rules 1, 2 and 6, from the base color."""
    n = bc.shape[0]
    lum = tx.linear_to_srgb(luminance(bc))  # perceptual lightness proxy
    f = np.fft.fft2(lum - lum.mean())
    power = np.abs(f) ** 2
    fx, fy = np.meshgrid(np.fft.fftfreq(n) * n, np.fft.fftfreq(n) * n)
    cyc = np.hypot(fx, fy)  # cycles per tile
    wl_cm = tile_cm / np.maximum(cyc, 1e-9)
    total = power.sum()
    fine = power[(wl_cm < 8.0) & (cyc > 0)].sum() / total
    big = power[(wl_cm >= 25.0) & (cyc > 0)].sum() / total
    # What survives at split-screen distance: blur away everything under ~25 cm.
    lowpass = np.real(np.fft.ifft2(f * np.exp(-0.5 * (cyc / (tile_cm / 25.0)) ** 2)))
    mean = bc.reshape(-1, 3).mean(0)
    reserved = {}
    flat = bc.reshape(-1, 3)
    sub = flat[:: max(1, len(flat) // 200000)]
    for k, h in tx.RESERVED.items():
        d = np.linalg.norm(sub - tx.hex_rgb(h), axis=1)
        reserved[k] = {"min_distance": round(float(d.min()), 4),
                       "fraction_within_0.15": round(float((d < 0.15).mean()), 6)}
    return {
        "fine_noise_share_under_8cm": round(float(fine), 5),
        "big_shape_share_over_25cm": round(float(big), 5),
        "split_screen_contrast_std": round(float(lowpass.std()), 5),
        "lightness_p05_p95": [round(float(np.percentile(lum, 5)), 4),
                              round(float(np.percentile(lum, 95)), 4)],
        "mean_srgb": [round(float(x), 4) for x in mean],
        "mean_hex": "#" + "".join(f"{int(round(x * 255)):02X}" for x in mean),
        "darkest_srgb_luma": round(float(lum.min()), 4),
        "reserved_colors": reserved,
    }


def load_set(folder, stem):
    return {k: tx.load_float(os.path.join(folder, f"T_{stem}_{k}.png")) for k in MAPS}


def tiled(img, tile_px=384, reps=3):
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize(
        (tile_px, tile_px), Image.LANCZOS)
    a = np.asarray(im)
    return np.tile(a, (reps, reps, 1))


def preview(maps, name, path, tile_cm):
    bc = maps["BC"]
    nrm = maps["N"] * 2.0 - 1.0
    litimg = mk.lit(bc, nrm, maps["AO"])
    left, right = tiled(bc), tiled(litimg)
    gap = 24
    h, w = left.shape[:2]
    sheet = Image.new("RGB", (w * 2 + gap * 3, h + 64), (24, 28, 40))
    sheet.paste(Image.fromarray(left), (gap, 48))
    sheet.paste(Image.fromarray(right), (w + gap * 2, 48))
    d = ImageDraw.Draw(sheet)
    d.text((gap, 14), f"T_{name}_BC tiled 3x3 ({3 * tile_cm / 100:.0f} m across at "
                      f"WorldTileSize {tile_cm})", fill=(225, 225, 235))
    d.text((w + gap * 2, 14), "lit with T_%s_N (DirectX) and _AO, preview light only" % name,
           fill=(225, 225, 235))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path, optimize=True)


def validate_chosen(out):
    report_all = {}
    for surface, s in mk.SURFACES.items():
        name = s["name"]
        gen_path = os.path.join(out, f"T_{name}.generation.json")
        with open(gen_path, encoding="utf-8") as f:
            gen = json.load(f)
        tile_cm = gen["parameters"]["tile_cm"]
        maps = load_set(out, name)
        files = {}
        ok = True
        for k, (what, space, comp, srgb) in MAPS.items():
            p = os.path.join(out, f"T_{name}_{k}.png")
            im = Image.open(p)
            a = maps[k]
            flat = a.reshape(-1, a.shape[-1] if a.ndim == 3 else 1)
            sm = seam(a)
            ok &= sm["pass"] and im.size == (2048, 2048)
            files[k] = {
                "file": rel(p), "contents": what, "color_space": space, "srgb": srgb,
                "suggested_compression": comp, "size_px": list(im.size), "png_mode": im.mode,
                "bytes": os.path.getsize(p), "sha256": tx.sha256(p),
                "channel_min": [round(float(x), 4) for x in flat.min(0)],
                "channel_max": [round(float(x), 4) for x in flat.max(0)],
                "channel_mean": [round(float(x), 4) for x in flat.mean(0)],
                "tileability": sm,
            }
        nrm = maps["N"] * 2.0 - 1.0
        nlen = np.linalg.norm(nrm, axis=-1)
        # Convention check from the height map: in DirectX, green = -dh/d(row), so green should
        # correlate positively with "height rises toward the image top", red with "rises left".
        hgt = maps["H"]
        up = -(np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0))
        left = -(np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1))
        corr_g = float(np.corrcoef(nrm[..., 1].ravel(), up.ravel())[0, 1])
        corr_r = float(np.corrcoef(nrm[..., 0].ravel(), left.ravel())[0, 1])
        prev = os.path.join(out, "previews", f"T_{name}_tiled3x3_preview.png")
        preview(maps, name, prev, tile_cm)
        report = {
            "task": "HZ-A1",
            "issue": 52,
            "surface": surface,
            "used_for": "walls and ceiling" if surface == "rock" else "cave floor",
            "candidate": gen["candidate"],
            "generator": gen["script"],
            "validator": "SourceArt/HZ/HZ-A1/validate_tileables.py",
            "seed": gen["parameters"]["seed"],
            "tool": gen["tool"],
            "license": "Own work, generated by our scripts; public redistribution allowed; no credit needed",
            "size_px": [2048, 2048],
            "design_world_tile_size_cm": tile_cm,
            "texel_density_px_per_m": round(2048 / (tile_cm / 100.0), 1),
            "height_range_cm": gen["height_range_cm"],
            "normal_convention": "DirectX (Unreal), +Y = green = image down; no Flip Green Channel",
            "normal_unit_length_mean_abs_error": round(float(np.abs(nlen - 1).mean()), 4),
            "normal_green_vs_height_slope_corr": round(corr_g, 4),
            "normal_red_vs_height_slope_corr": round(corr_r, 4),
            "normal_convention_check": "DirectX" if corr_g > 0.5 and corr_r > 0.5 else
                                       ("OpenGL" if corr_g < -0.5 else "unclear"),
            "normal_mean_rgb": [round(float(x), 4) for x in maps["N"].reshape(-1, 3).mean(0)],
            "seam_limit_ratio": SEAM_LIMIT,
            "all_tileable_and_2k": bool(ok),
            "style": style_metrics(maps["BC"], tile_cm),
            "files": files,
            "preview": rel(prev),
        }
        tx.write_json(os.path.join(out, f"T_{name}.validation.json"), report)
        report_all[name] = ok
        print(name, "tileable+2K:", ok, "| seam ratios",
              {k: (v["tileability"]["seam_ratio_x"], v["tileability"]["seam_ratio_y"])
               for k, v in files.items()})
    return all(report_all.values())


def score_candidates(folder, out):
    result = {"note": "Candidates were generated outside the repo with make_cave_surfaces.py "
                      "--candidates; only these scores and small contact sheets are kept.",
              "size_px": None, "surfaces": {}}
    for surface, s in mk.SURFACES.items():
        rows = {}
        for key, p in s["candidates"].items():
            maps = load_set(os.path.join(folder, surface, key), f"{s['name']}_{key}")
            result["size_px"] = maps["BC"].shape[0]
            st = style_metrics(maps["BC"], p["tile_cm"])
            sm = seam(maps["BC"])
            rows[key] = {
                "seed": p["seed"], "tile_cm": p["tile_cm"], "mode": p["mode"],
                "seam_ratio_bc": [sm["seam_ratio_x"], sm["seam_ratio_y"]],
                "fine_noise_share_under_8cm": st["fine_noise_share_under_8cm"],
                "big_shape_share_over_25cm": st["big_shape_share_over_25cm"],
                "split_screen_contrast_std": st["split_screen_contrast_std"],
                "lightness_p05_p95": st["lightness_p05_p95"],
                "mean_hex": st["mean_hex"],
                "chosen": key == s["chosen"],
            }
        result["surfaces"][surface] = rows
        src = os.path.join(folder, f"candidates_{surface}.png")
        if os.path.exists(src):
            im = Image.open(src)
            im = im.resize((im.width * 2 // 3, im.height * 2 // 3), Image.LANCZOS)
            os.makedirs(os.path.join(out, "previews"), exist_ok=True)
            im.save(os.path.join(out, "previews", f"T_{s['name']}_candidates_preview.png"),
                    optimize=True)
    tx.write_json(os.path.join(out, "candidates.json"), result)
    print(json.dumps(result["surfaces"], indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--candidates")
    a = ap.parse_args()
    if a.candidates:
        score_candidates(a.candidates, a.out)
        return
    sys.exit(0 if validate_chosen(a.out) else 1)


if __name__ == "__main__":
    main()
