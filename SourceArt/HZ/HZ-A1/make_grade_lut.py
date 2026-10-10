"""HZ-A1: cave color-grading LUT in Unreal's 256 x 16 strip format.

    python3 -I SourceArt/HZ/HZ-A1/make_grade_lut.py

Writes T_CaveGrade_LUT.png, T_CaveGrade_LUT.validation.json and a before/after preview on the
PG-A0 torch-chamber style frame (previews/T_CaveGrade_LUT_preview.png).

Strip layout (what Unreal's Color Grading LUT expects): 16 slices of 16 x 16 side by side.
Blue picks the slice (x // 16), red runs across each slice (x % 16), green runs down (y). Each
value is index / 15, in display (gamma) space. The identity strip leaves the image unchanged.

The grade, all in display space, kept gentle so the LUT can sit at intensity 1:
- shadows lifted toward the style.md shadow color #1E2433, so darks read blue-violet, not black;
- highlights nudged toward torch amber #FFB347, the warm-pool look of the style frames;
- a soft S-curve for contrast and a small saturation lift in the mids, so the reserved relic,
  crystal and trap colors still pop.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import hz_tileables as tx  # noqa: E402

SHADOW = tx.hex_rgb(tx.PALETTE["shadow"])
AMBER = tx.hex_rgb(tx.PALETTE["torch_amber"])
SETTINGS = dict(shadow_lift=0.42, shadow_range=0.42, highlight_warmth=0.10, highlight_from=0.55,
                s_curve=0.18, saturation=1.10)
FRAME = os.path.join(HERE, "..", "..", "PG", "PG-A0", "style-frames", "frame-02-torch-chamber.png")


def grade(c, s=SETTINGS):
    c = np.clip(np.asarray(c, dtype=np.float64), 0, 1)
    luma = (c * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    # Saturation in the mids only, so near-black and near-white stay clean.
    mid = 4 * luma * (1 - luma)
    c = luma + (c - luma) * (1 + (s["saturation"] - 1) * mid)
    # Soft S-curve.
    c = tx.lerp(c, c * c * (3 - 2 * c), s["s_curve"])
    # Colored shadows: blend toward the shadow color where it's dark (a lift, not a crush).
    w = (1 - tx.smoothstep(0.0, s["shadow_range"], luma)) * s["shadow_lift"]
    c = c + w * (SHADOW - c) * (1 - c)
    # Warm highlights.
    wh = tx.smoothstep(s["highlight_from"], 1.0, luma) * s["highlight_warmth"]
    c = tx.lerp(c, c * (AMBER / AMBER.max()) * 1.04, wh)
    return np.clip(c, 0, 1)


def identity_strip():
    x = np.arange(256)
    y = np.arange(16)
    xx, yy = np.meshgrid(x, y)
    return np.stack([(xx % 16) / 15.0, yy / 15.0, (xx // 16) / 15.0], -1)


def apply_lut(img, lut):
    """Trilinear lookup, the way the engine samples the strip."""
    c = np.clip(img, 0, 1) * 15.0
    i0 = np.floor(c).astype(int)
    i1 = np.minimum(i0 + 1, 15)
    f = c - i0
    cube = lut.reshape(16, 16, 16, 3)  # [g][b][r]

    def at(r, g, b):
        return cube[g, b, r]

    out = 0
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                r = i1[..., 0] if dr else i0[..., 0]
                g = i1[..., 1] if dg else i0[..., 1]
                b = i1[..., 2] if db else i0[..., 2]
                wr = f[..., 0] if dr else 1 - f[..., 0]
                wg = f[..., 1] if dg else 1 - f[..., 1]
                wb = f[..., 2] if db else 1 - f[..., 2]
                out = out + at(r, g, b) * (wr * wg * wb)[..., None]
    return out


def main():
    ident = identity_strip()
    lut = grade(ident)
    path = os.path.join(HERE, "T_CaveGrade_LUT.png")
    tx.save_rgb8(path, lut)
    saved = tx.load_float(path)

    # Checks: the identity strip round-trips through the sampler; grey stays ordered and tinted.
    cube = np.random.default_rng(7).random((20000, 3))
    ident_err = float(np.abs(apply_lut(cube, ident) - cube).max())
    greys = np.linspace(0, 1, 16)[:, None] * np.ones(3)
    g_out = apply_lut(greys, saved)
    g_luma = (g_out * np.array([0.2126, 0.7152, 0.0722])).sum(-1)
    named = {k: tx.hex_rgb(v) for k, v in {**tx.PALETTE, **tx.RESERVED}.items()}
    named_out = {k: "#" + "".join(f"{int(round(x * 255)):02X}" for x in apply_lut(v, saved))
                 for k, v in named.items()}

    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    prev = os.path.join(HERE, "previews", "T_CaveGrade_LUT_preview.png")
    frame = Image.open(FRAME).convert("RGB")
    frame = frame.resize((720, int(720 * frame.height / frame.width)), Image.LANCZOS)
    before = np.asarray(frame).astype(np.float64) / 255
    after = apply_lut(before, saved)
    w, h = frame.size
    sheet = Image.new("RGB", (w * 2 + 48, h + 56 + 64 + 16), (24, 28, 40))
    sheet.paste(frame, (16, 40))
    sheet.paste(Image.fromarray((after * 255).round().astype(np.uint8)), (w + 32, 40))
    strip = Image.fromarray((saved * 255).round().astype(np.uint8)).resize((256 * 4, 16 * 4),
                                                                           Image.NEAREST)
    sheet.paste(strip, (16, h + 56))
    d = ImageDraw.Draw(sheet)
    d.text((16, 14), "style frame 02, no grade", fill=(225, 225, 235))
    d.text((w + 32, 14), "through T_CaveGrade_LUT (preview of the LUT alone, before fog)",
           fill=(225, 225, 235))
    d.text((16 + 256 * 4 + 16, h + 56), "T_CaveGrade_LUT.png\n256 x 16, shown 4x", fill=(225, 225, 235))
    sheet.save(prev, optimize=True)

    def rel(p):
        root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
        return os.path.relpath(os.path.abspath(p), root).replace(os.sep, "/")

    im = Image.open(path)
    tx.write_json(os.path.join(HERE, "T_CaveGrade_LUT.validation.json"), {
        "task": "HZ-A1",
        "issue": 52,
        "file": rel(path),
        "generator": "SourceArt/HZ/HZ-A1/make_grade_lut.py",
        "format": "Unreal color grading LUT strip: 16 slices of 16x16; x%16 red, y green, x//16 blue",
        "size_px": list(im.size),
        "png_mode": im.mode,
        "bytes": os.path.getsize(path),
        "sha256": tx.sha256(path),
        "settings": SETTINGS,
        "identity_strip_sampler_max_error": round(ident_err, 6),
        "grey_ramp_luma_out": [round(float(x), 4) for x in g_luma],
        "grey_ramp_monotonic": bool(np.all(np.diff(g_luma) > 0)),
        "black_maps_to": "#" + "".join(f"{int(round(x * 255)):02X}" for x in g_out[0]),
        "white_maps_to": "#" + "".join(f"{int(round(x * 255)):02X}" for x in g_out[-1]),
        "palette_through_lut": named_out,
        "preview": rel(prev),
        "preview_source": rel(FRAME),
        "license": "Own work, generated by our script; public redistribution allowed; no credit needed",
    })
    print("LUT", im.size, "identity err", ident_err, "monotonic", bool(np.all(np.diff(g_luma) > 0)),
          "black->", g_out[0], "white->", g_out[-1])


if __name__ == "__main__":
    main()
