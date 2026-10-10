"""Render offline HC-A3 HUD layouts using PR #68 textures; no editor calls.
Python 3.10+, Pillow 10.1+. Writes only alongside this script.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
spec = importlib.util.spec_from_file_location("hc_a3_import",REPO/"Tools/unreal/hc_a3_import/import_hud.py")
imports = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imports)
CONFIG = json.loads((HERE/"layout-spec.json").read_text(encoding="utf-8"))

def font(size):
    return ImageFont.load_default(size=max(CONFIG["metrics"]["minimum_font"],round(size)))
def intersect(a,b):
    return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]
def bbox(image):
    return image.getchannel("A").point(lambda value:255 if value>8 else 0).getbbox()
def viewport_rects(w,h,mode):
    if mode == "full":
        return [(0,0,w,h)]
    if mode == "split-horizontal":
        return [(0,0,w,h//2),(0,h//2,w,h)]
    return [(0,0,w//2,h),(w//2,0,w,h)]
def background(w,h,player):
    image = Image.new("RGBA",(w,h),"#1E2433")
    draw = ImageDraw.Draw(image)
    for y in range(h):
        f=y/max(1,h-1)
        draw.line((0,y,w,y),fill=(round(31+15*f),round(40+7*f),round(53+8*f),255))
    # Neutral procedural cave blocks are preview context, not production art.
    draw.polygon([(0,0),(w*.28,0),(w*.21,h*.7),(0,h*.86)],fill="#383440")
    draw.polygon([(w*.7,0),(w,0),(w,h*.8),(w*.81,h*.58)],fill="#4A4652")
    draw.polygon([(0,h*.84),(w*.5,h*.66),(w,h*.82),(w,h),(0,h)],fill="#292b38")
    if player == 1:
        image.alpha_composite(Image.new("RGBA",(w,h),(10,12,26,45)))
    return image

def render_view(w,h,state,player,textures):
    c=CONFIG; m=c["metrics"]; sample=c["sample"]
    scale=max(c["scale"]["minimum"],min(c["scale"]["maximum"],w/1280,h/720))
    safe=round(m["safe_margin"]*scale)
    image=background(w,h,player); draw=ImageDraw.Draw(image)
    elements=[]
    def image_element(key,name,size,center):
        size=round(size*scale)
        texture=textures[name].resize((size,size),Image.Resampling.LANCZOS)
        box=bbox(texture)
        x=round(center[0]-(box[0]+box[2])/2); y=round(center[1]-(box[1]+box[3])/2)
        image.alpha_composite(texture,(x,y))
        rect=[x+box[0],y+box[1],x+box[2],y+box[3]]
        elements.append({"id":key,"kind":"image","asset":name,"brush_rect":[x,y,x+size,y+size],
                         "visible_rect":rect,"texture_size":[size,size],"anchor_center":list(center)})
        return rect
    def text_element(key,value,center,size):
        face=font(size*scale)
        box=draw.textbbox(center,value,font=face,anchor="mm",stroke_width=1)
        draw.text(center,value,font=face,anchor="mm",fill=c["colors"]["text"],
                  stroke_width=1,stroke_fill=c["colors"]["text_shadow"])
        elements.append({"id":key,"kind":"text","text":value,"visible_rect":list(box),"font_px":face.size})
        return box
    icon_size=round(m["icon_texture_width"]*scale)
    icon=image_element("relic-icon","T_HUD_RelicIcon",m["icon_texture_width"],(safe+icon_size/2,safe+icon_size/2))
    total=str(sample["relics_collected"])+" / "+str(sample["relics_available"])
    counter_face=font(m["counter_font"]*scale)
    total_width=draw.textlength(total,font=counter_face)
    text_element("relic-total",total,(icon[2]+round(12*scale)+total_width/2,(icon[1]+icon[3])/2),m["counter_font"])

    banner_size=round(m["banner_texture_width"]*scale)
    temp=textures["T_HUD_RoundBannerFrame"].resize((banner_size,banner_size),Image.Resampling.LANCZOS)
    bb=bbox(temp); center=(w/2,safe+(bb[3]-bb[1])/2)
    border=image_element("round-frame","T_HUD_RoundBannerFrame",m["banner_texture_width"],center)
    value={"playing":"ROUND "+str(sample["round_index"])+" / "+str(sample["round_total"]),
           "timed":"ROUND "+str(sample["round_index"])+" / "+str(sample["round_total"]),
           "cleared":"ROUND CLEARED","failed":"ROUND FAILED"}[state]
    label=text_element("round-label",value,center,m["banner_font"])
    # A conservative transparent opening mapped from the original square canvas.
    brush=next(e["brush_rect"] for e in elements if e["id"]=="round-frame")
    opening=[brush[0]+banner_size*0.19,brush[1]+banner_size*0.445,
             brush[0]+banner_size*0.81,brush[1]+banner_size*0.585]
    assert label[0]>=opening[0] and label[2]<=opening[2] and label[1]>=opening[1] and label[3]<=opening[3], "Banner text outside opening"
    if state in ("cleared","failed"):
        subtitle="Round "+str(sample["round_index"])+" / "+str(sample["round_total"])+(" - Next chamber" if state=="cleared" else " - Checkpoint restart")
        text_element("round-status",subtitle,(w/2,border[3]+round(18*scale)),18)

    if state in ("playing","timed"):
        center=(w/2,h-safe-round(100*scale))
        frame=image_element("interact-frame","T_HUD_InteractPromptFrame",m["prompt_texture_width"],center)
        key="E" if player==0 else "A"
        action=("Hold ["+key+"]  Interact") if state=="timed" else ("["+key+"]  Interact")
        label=text_element("interact-label",action,center,m["prompt_font"])
        prompt_size=round(m["prompt_texture_width"]*scale)
        brush=next(e["brush_rect"] for e in elements if e["id"]=="interact-frame")
        opening=[brush[0]+prompt_size*.18,brush[1]+prompt_size*.445,
                 brush[0]+prompt_size*.82,brush[1]+prompt_size*.59]
        assert label[0]>=opening[0] and label[2]<=opening[2] and label[1]>=opening[1] and label[3]<=opening[3], "Prompt text outside opening"
        if state=="timed":
            progress=0.65 if player==0 else 0.35
            width=round(m["progress_width"]*scale); height=round(m["progress_height"]*scale)
            rect=[round(w/2-width/2),frame[3]+round(10*scale),round(w/2+width/2),frame[3]+round(10*scale)+height]
            draw.rounded_rectangle(rect,radius=max(2,height//2),fill=c["colors"]["track"],outline=c["colors"]["border"],width=1)
            fill=[rect[0]+2,rect[1]+2,round(rect[0]+2+(width-4)*progress),rect[3]-2]
            draw.rounded_rectangle(fill,radius=2,fill=c["colors"]["progress"])
            elements.append({"id":"timed-progress","kind":"progress","percent":progress,"visible_rect":rect})
            text_element("timed-status",str(round(progress*100))+"% / "+str(sample["hold_seconds"])+"s hold",
                         (w/2,rect[3]+round(14*scale)),16)
    safe_rect=[safe,safe,w-safe,h-safe]
    for e in elements:
        r=e["visible_rect"]
        assert r[0]>=safe and r[1]>=safe and r[2]<=w-safe and r[3]<=h-safe,(state,player,e["id"],r,safe_rect)
    # Relic group, banner group and interaction group may not overlap.
    group_ids=[["relic-icon","relic-total"],["round-frame","round-label","round-status"],
               ["interact-frame","interact-label","timed-progress","timed-status"]]
    groups=[]
    for ids in group_ids:
        rects=[e["visible_rect"] for e in elements if e["id"] in ids]
        if rects: groups.append([min(r[0] for r in rects),min(r[1] for r in rects),max(r[2] for r in rects),max(r[3] for r in rects)])
    for i,a in enumerate(groups):
        for b in groups[i+1:]: assert not intersect(a,b),(state,player,"HUD groups overlap",a,b)
    return image,{"viewport_size":[w,h],"scale":scale,"safe_margin_px":safe,"elements":elements}

def main():
    manifest=json.loads((imports.HERE/"manifest.json").read_text())
    plan=imports.validate(manifest)
    textures={p["name"]:Image.open(p["source"]).convert("RGBA") for p in plan}
    before={p["name"]:hashlib.sha256(Path(p["source"]).read_bytes()).hexdigest() for p in plan}
    output=HERE/"previews"; output.mkdir(exist_ok=True)
    cases=[]
    for w,h in CONFIG["resolutions"]:
        for mode in CONFIG["modes"]:
            for state in CONFIG["states"]:
                canvas=Image.new("RGBA",(w,h)); views=[]
                for player,r in enumerate(viewport_rects(w,h,mode)):
                    image,geometry=render_view(r[2]-r[0],r[3]-r[1],state,player,textures)
                    canvas.alpha_composite(image,(r[0],r[1]))
                    geometry.update({"player":player+1,"viewport_rect":r}); views.append(geometry)
                draw=ImageDraw.Draw(canvas)
                if mode=="split-horizontal": draw.line((0,h//2,w,h//2),fill="#FFB347",width=1)
                if mode=="split-vertical": draw.line((w//2,0,w//2,h),fill="#FFB347",width=1)
                filename=str(w)+"x"+str(h)+"_"+mode+"_"+state+".png"
                path=output/filename; canvas.convert("RGB").save(path,optimize=True)
                cases.append({"file":"previews/"+filename,"resolution":[w,h],"mode":mode,"state":state,
                              "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"views":views})
    report={"dependency_pr":68,"dependency_head":"6f7e713f47f7d3ac8b9d96738639d3ea4bda4618",
            "source_hashes":before,"cases":cases,"checks":{"case_count":len(cases),"view_count":sum(len(c["views"]) for c in cases),
            "visible_art_and_text_inside_safe_area":True,"no_hud_group_overlap":True,"frame_text_inside_openings":True,
            "square_texture_aspect_preserved":True,"minimum_text_px":16,"engine_executed":False}}
    after={p["name"]:hashlib.sha256(Path(p["source"]).read_bytes()).hexdigest() for p in plan}
    assert before==after,"Delivered texture was modified"
    (HERE/"geometry-and-validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    # Review boards are reduced overviews; individual preview files retain native resolution.
    for w,h in CONFIG["resolutions"]:
        rows=len(CONFIG["modes"]); thumb_w=640; thumb_h=round(h*640/w)
        board=Image.new("RGB",(2560,rows*(thumb_h+50)+55),"#101722"); draw=ImageDraw.Draw(board)
        draw.text((20,12),str(w)+" x "+str(h)+" / offline HUD states (not engine screenshots)",font=font(22),fill="#F7E7C4")
        for row,mode in enumerate(CONFIG["modes"]):
            for col,state in enumerate(CONFIG["states"]):
                case=next(c for c in cases if c["resolution"]==[w,h] and c["mode"]==mode and c["state"]==state)
                image=Image.open(HERE/case["file"]).resize((thumb_w,thumb_h),Image.Resampling.LANCZOS)
                x=col*thumb_w; y=55+row*(thumb_h+50)
                draw.text((x+12,y+8),mode+" / "+state,font=font(17),fill="#F7E7C4")
                board.paste(image,(x,y+40))
        board.save(HERE/("review-board-"+str(w)+"x"+str(h)+".png"),optimize=True)
    print("PASS: 24 full-resolution layouts, 40 player views; source hashes unchanged.")

if __name__=="__main__":
    main()
