"""Independent HC-A3 offline evidence checks; writes reports only in layout/."""
import importlib.util,json,pathlib,hashlib
from PIL import Image
root=pathlib.Path.cwd()
spec=importlib.util.spec_from_file_location("hud",root/"Tools/unreal/hc_a3_import/import_hud.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
d=root/"SourceArt/HC/HC-A3/layout"
r=json.loads((d/"geometry-and-validation.json").read_text())
rows=[]
expected={(w,h,mode,state) for w,h in ((1280,720),(1920,1080)) for mode in ("full","split-horizontal","split-vertical") for state in ("playing","timed","cleared","failed")}
assert len(r["cases"])==24 and {(c["resolution"][0],c["resolution"][1],c["mode"],c["state"]) for c in r["cases"]}==expected
assert sum(len(c["views"]) for c in r["cases"])==40
for name,sha in m.HASHES.items():
    p=root/"SourceArt/HC/HC-A3"/(name+".png")
    im=Image.open(p)
    assert m.png_alpha(p.read_bytes())==list(im.getchannel("A").tobytes())
    assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
for c in r["cases"]:
    p=d/c["file"]; im=Image.open(p)
    assert list(im.size)==c["resolution"]
    assert hashlib.sha256(p.read_bytes()).hexdigest()==c["sha256"]
    for v in c["views"]:
        w,h=v["viewport_size"]; safe=v["safe_margin_px"]
        ids={e["id"]:e for e in v["elements"]}
        assert "relic-total" in ids and "round-label" in ids
        assert (c["state"]=="timed")==("timed-progress" in ids)
        if c["state"] in ("cleared","failed"):
            assert "2 / 3" in ids["round-status"]["text"]
        for e in v["elements"]:
            x1,y1,x2,y2=e["visible_rect"]
            assert safe<=x1<x2<=w-safe and safe<=y1<y2<=h-safe
            if e["kind"]=="image":
                assert e["texture_size"][0]==e["texture_size"][1]
            if e["kind"]=="text":
                assert e["font_px"]>=16
for w,h in ((1280,720),(1920,1080)):
    for mode in ("full","split-horizontal","split-vertical"):
        c=next(c for c in r["cases"] if c["resolution"]==[w,h] and c["mode"]==mode and c["state"]=="timed")
        v=c["views"][0]; ids={e["id"]:e for e in v["elements"]}
        rows.append("| "+str(w)+" x "+str(h)+" | "+mode+" | "+str(v["viewport_size"][0])+" x "+str(v["viewport_size"][1])+" | "+str(v["scale"])+" | "+str(v["safe_margin_px"])+" | "+str(ids["relic-icon"]["texture_size"][0])+" / "+str(ids["round-frame"]["texture_size"][0])+" / "+str(ids["interact-frame"]["texture_size"][0])+" |")
(d/"dimensions.md").write_text("# HUD dimensions and margins\n\nAll values below are physical pixels per local-player viewport. Texture widths are full square-canvas dimensions; visible bounds are recorded separately in geometry-and-validation.json.\n\n| Output | Mode | Local viewport | HUD scale | Safe margin | Icon / banner / prompt width |\n| --- | --- | --- | --- | --- | --- |\n"+"\n".join(rows)+"\n\nText never drops below 16px. Clear/failed states retain the round number below the status banner. Source textures remain square; transparent canvas portions may extend outside the player viewport while visible artwork stays inside the safe area.\n",encoding="utf-8")
(d/"independent-checks.json").write_text(json.dumps({"passed":True,"cases":24,"player_views":40,"png_alpha_decoder_matches_pillow":True,"original_source_hashes_unchanged":True,"native_preview_dimensions_and_hashes_verified":True,"text_and_visible_art_in_safe_area":True,"aspect_ratios_verified":True,"round_number_retained_in_end_states":True,"no_unreal_execution":True},indent=2)+"\n",encoding="utf-8")
print("Independent gate passed: PNG decoder agrees with Pillow; native layouts, sources and geometry verified.")
