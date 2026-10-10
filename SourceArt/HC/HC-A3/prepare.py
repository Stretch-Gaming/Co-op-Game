"""Prepare HC-A3 deliverables and an offline readability preview.
Requires Python 3 and Pillow. Run from any directory:
python SourceArt/HC/HC-A3/prepare.py --style-reference <PNG or Git LFS object>
Only writes inside this script's asset-task folder. No Unreal/editor interaction.
"""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
NAMES = ("T_HUD_RelicIcon", "T_HUD_RoundBannerFrame", "T_HUD_InteractPromptFrame")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def font(size):
    # Pillow's bundled font keeps the preview independent of system fonts.
    return ImageFont.load_default(size=size)
def visible_bbox(im):
    return im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
def centered(canvas, texture, width, center):
    scaled = texture.resize((width, width), Image.Resampling.LANCZOS)
    box = visible_bbox(scaled)
    ox = round(center[0] - (box[0] + box[2]) / 2)
    oy = round(center[1] - (box[1] + box[3]) / 2)
    canvas.alpha_composite(scaled, (ox, oy))
def run(reference):
    generation = json.loads((ROOT / "generation.json").read_text(encoding="utf-8"))
    assert sha(reference) == generation["reference_sha256"], "Wrong style-reference image"
    outputs = {}
    checks = []
    for record in generation["records"]:
        name = record["name"]
        source = ROOT / record["source"]
        assert sha(source) == record["source_sha256"], "Source hash mismatch"
        with Image.open(source) as raw:
            assert raw.mode == "RGBA", "Source lacks alpha"
            im = raw.resize((512, 512), Image.Resampling.LANCZOS)
        # Add a transparent 12px margin to the icon's full canvas, preserving alpha.
        if name == "T_HUD_RelicIcon":
            inner = im.resize((488, 488), Image.Resampling.LANCZOS)
            im = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            im.alpha_composite(inner, (12, 12))
        path = ROOT / record["output"]
        im.save(path, optimize=True)
        alpha = im.getchannel("A")
        histogram = alpha.histogram()
        assert im.size == (512, 512) and im.mode == "RGBA"
        assert histogram[0] > 0 and histogram[255] > 0
        edges = [alpha.crop(box).getextrema()[1] for box in ((0,0,512,1),(0,511,512,512),(0,0,1,512),(511,0,512,512))]
        assert max(edges) <= 2, "Visible pixels touch canvas boundary"
        row = {"file":path.name,"sha256":sha(path),"bytes":path.stat().st_size,
               "dimensions":[512,512],"mode":"RGBA","alpha_extrema":list(alpha.getextrema()),
               "fully_transparent_pixels":histogram[0],"visible_bounds_alpha_gt_8":list(visible_bbox(im)),
               "max_boundary_alpha":max(edges),"source_sha256":sha(source)}
        if "Frame" in name:
            opening = alpha.crop((150,235,350,285))
            row["central_opening_alpha_extrema"] = list(opening.getextrema())
            # Ignore at most 2/255 alpha generation noise; the opening has no visible panel.
            assert opening.getextrema()[1] <= 2, "Frame contains a visible center fill"
            assert alpha.getpixel((256,256)) <= 2
        checks.append(row)
        outputs[name] = im

    preview = Image.new("RGBA", (1200, 1350), "#101722")
    draw = ImageDraw.Draw(preview)
    draw.text((28,22),"HC-A3 / SOURCE ART READABILITY",font=font(26),fill="#f0e5cd")
    draw.text((28,60),"Offline mockup: 1920 x 1080 horizontal split represented at 62.5% scale.",font=font(16),fill="#b4b5bd")
    draw.text((28,87),"Labels below are preview-only overlays. Delivered texture files contain no text.",font=font(15),fill="#b4b5bd")
    with Image.open(reference) as reference_image:
        background = reference_image.convert("RGBA").resize((1200,675),Image.Resampling.LANCZOS).crop((0,169,1200,507))
    for index, y in enumerate((125,463)):
        panel = background.copy()
        # Two local-player screens; compare cave-reference brightness and a darker cave.
        darkness = 100 if index == 0 else 170
        panel.alpha_composite(Image.new("RGBA",panel.size,(12,16,30,darkness)))
        pd = ImageDraw.Draw(panel)
        pd.text((18,14),"PLAYER "+str(index+1),font=font(15),fill="#eee4cf",stroke_width=1,stroke_fill="#161a26")
        centered(panel,outputs["T_HUD_RelicIcon"],48,(40,58))
        pd.text((74,49),"12 / 18",font=font(18),fill="#fff0d1",stroke_width=1,stroke_fill="#161a26")
        centered(panel,outputs["T_HUD_RoundBannerFrame"],320,(600,104))
        pd.text((600,104),"ROUND 1 / 3",anchor="mm",font=font(18),fill="#fff0d1",stroke_width=1,stroke_fill="#161a26")
        centered(panel,outputs["T_HUD_InteractPromptFrame"],240,(600,270))
        pd.text((600,270),"[E]  Interact",anchor="mm",font=font(14),fill="#fff0d1",stroke_width=1,stroke_fill="#161a26")
        preview.alpha_composite(panel,(0,y))
    draw.line((0,463,1200,463),fill="#e2d0b0",width=2)
    draw.text((28,828),"SMALL-SIZE CUTOUT CHECK / DARK AND LIGHT BACKGROUNDS",font=font(19),fill="#f0e5cd")
    for x,color,label in ((28,"#1E2433","Dark cave"),(616,"#d2c8b8","Light surface")):
        draw.rounded_rectangle((x,864,x+556,1290),radius=12,fill=color)
        ink = "#efe5d1" if x == 28 else "#232833"
        draw.text((x+18,880),label,font=font(18),fill=ink)
        for i,size in enumerate((32,48,64)):
            cx=x+58+i*95
            centered(preview,outputs["T_HUD_RelicIcon"],size,(cx,943))
            draw.text((cx,986),str(size)+"px",anchor="mm",font=font(13),fill=ink)
        centered(preview,outputs["T_HUD_RoundBannerFrame"],240,(x+278,1078))
        draw.text((x+278,1078),"ROUND 1 / 3",anchor="mm",font=font(14),fill=ink)
        draw.text((x+278,1131),"Banner: 240px texture width",anchor="mm",font=font(13),fill=ink)
        centered(preview,outputs["T_HUD_InteractPromptFrame"],200,(x+278,1199))
        draw.text((x+278,1199),"[E]  Interact",anchor="mm",font=font(12),fill=ink)
        draw.text((x+278,1256),"Prompt: 200px texture width",anchor="mm",font=font(13),fill=ink)
    draw.text((28,1311),"Art sizing and alpha checks only. Unreal import, HUD integration and in-game tests remain pending.",font=font(14),fill="#b4b5bd")
    preview.convert("RGB").save(ROOT / "preview.png",optimize=True)
    report = {"schema_version":1,"source_delivery_only":True,
              "processing":"Pillow LANCZOS size conversion; transparent icon padding; no repainting or alpha thresholding.",
              "automated_checks":checks,"preview":{"file":"preview.png","dimensions":[1200,1350],"sha256":sha(ROOT/"preview.png")},
              "visual_review":"See visual-review.md for independent inspection of the prepared textures and preview.",
              "unreal_import":"pending","in_game_split_screen":"pending"}
    (ROOT/"validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style-reference",required=True,type=Path)
    run(parser.parse_args().style_reference)
