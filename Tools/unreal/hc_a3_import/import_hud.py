"""HC-A3 UI texture import preparation. Default: validate and print; no writes.
Python 3.10+, standard library only. Unreal is imported ONLY after explicit --apply.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEST = "/Game/Puzzles/Art/HCA3_UI"
HASHES = {
    "T_HUD_RelicIcon": "f951444d51dfac80b3321b1f5be89ed1bfb8f4c9b7381ed7c6c0f424637374b1",
    "T_HUD_RoundBannerFrame": "49dbcfc2cb2940c940cc91ac9719de2ddac48a77a0417da4bf42971d0c05c4fd",
    "T_HUD_InteractPromptFrame": "3813050f24a3ce1cb0b57b8f2892842c4f9326074a24f3546d7149c11f64257c"
}
SETTINGS = {
    "compression_settings": "TC_EDITOR_ICON",
    "lod_group": "TEXTUREGROUP_UI",
    "mip_gen_settings": "TMGS_NO_MIPMAPS",
    "srgb": True,
    "compression_no_alpha": False,
    "never_stream": True,
    "virtual_texture_streaming": False,
    "address_x": "TA_CLAMP",
    "address_y": "TA_CLAMP",
    "filter": "TF_BILINEAR"
}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def png_alpha(data):
    """Decode only the approved 512px, non-interlaced, 8-bit RGBA PNG format."""
    require(data.startswith(b"\x89PNG\r\n\x1a\n"), "Not a PNG; hydrate Git LFS sources")
    pos, idat, header, ended = 8, bytearray(), None, False
    while pos < len(data):
        require(pos + 12 <= len(data), "Truncated PNG")
        length = struct.unpack(">I", data[pos:pos+4])[0]
        tag = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+length]
        require(pos+12+length <= len(data), "Truncated PNG chunk")
        crc = struct.unpack(">I",data[pos+8+length:pos+12+length])[0]
        require(zlib.crc32(tag+chunk) & 0xffffffff == crc, "PNG CRC mismatch")
        if tag == b"IHDR":
            require(header is None and pos == 8 and length == 13, "Invalid IHDR")
            header = struct.unpack(">IIBBBBB",chunk)
        elif tag == b"IDAT":
            idat.extend(chunk)
        elif tag == b"IEND":
            require(length == 0, "Invalid IEND")
            ended = True
            pos += 12
            break
        pos += length + 12
    require(ended and pos == len(data), "PNG lacks final IEND")
    require(header == (512,512,8,6,0,0,0), "Expected 512x512 non-interlaced 8-bit RGBA")
    raw = zlib.decompress(bytes(idat))
    stride = 512*4
    require(len(raw) == 512*(stride+1), "Unexpected decoded PNG length")
    previous = bytearray(stride)
    alpha = []
    for y in range(512):
        offset = y*(stride+1)
        kind = raw[offset]
        require(kind <= 4, "Unknown PNG filter")
        row = bytearray(raw[offset+1:offset+1+stride])
        for i in range(stride):
            left = row[i-4] if i >= 4 else 0
            up = previous[i]
            corner = previous[i-4] if i >= 4 else 0
            if kind == 1:
                predictor = left
            elif kind == 2:
                predictor = up
            elif kind == 3:
                predictor = (left+up)//2
            elif kind == 4:
                p = left+up-corner
                choices = (abs(p-left),abs(p-up),abs(p-corner))
                predictor = (left,up,corner)[choices.index(min(choices))]
            else:
                predictor = 0
            row[i] = (row[i]+predictor) & 255
        alpha.extend(row[3::4])
        previous = row
    return alpha

def validate(manifest, repo=REPO):
    require(manifest.get("schema_version") == 1, "Unsupported manifest")
    require(manifest.get("engine_version") == "5.8.3", "Wrong engine target")
    require(manifest.get("destination_root") == DEST+"/", "Destination outside HC-A3")
    require(manifest.get("texture_settings") == SETTINGS, "Texture settings differ from approved UI preset")
    entries = manifest.get("assets",[])
    require(len(entries) == 3 and {e.get("name") for e in entries} == set(HASHES), "Expected exactly 3 approved textures")
    repo = Path(repo).resolve()
    plan = []
    for entry in entries:
        name = entry["name"]
        relative = "SourceArt/HC/HC-A3/"+name+".png"
        require(entry.get("source") == relative, "Source path is not an approved HUD PNG")
        require(entry.get("sha256") == HASHES[name], "Manifest hash differs from PR #68")
        require(entry.get("dimensions") == [512,512], "Wrong manifest dimensions")
        package = DEST+"/"+name
        require(entry.get("destination_path") == DEST and entry.get("destination_object") == package+"."+name, "Invalid texture destination")
        path = (repo/relative).resolve()
        require(path.is_relative_to(repo), "Source escapes repository")
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == HASHES[name], "Source hash mismatch: "+name)
        alpha = png_alpha(data)
        require(min(alpha) == 0 and max(alpha) == 255, "No real transparent/opaque pixels: "+name)
        edge = alpha[:512]+alpha[-512:]+alpha[::512]+alpha[511::512]
        require(max(edge) == 0, "Canvas boundary is not fully transparent: "+name)
        opening = [alpha[y*512+x] for y in range(235,285) for x in range(150,350)]
        if "Frame" in name:
            require(max(opening) <= 2, "Frame opening contains visible fill")
        plan.append({"source":str(path),"sha256":HASHES[name],"destination_object":entry["destination_object"],"name":name,"alpha_range":[min(alpha),max(alpha)],"max_edge_alpha":max(edge)})
    return plan

def apply_imports(plan, repo=REPO, unreal_module=None):
    # Called only by explicit --apply after complete source/manifest validation.
    if unreal_module is None:
        import unreal as unreal_module
    u = unreal_module
    require(re.match(r"^5\.8\.3(?:-|\+|$)",u.SystemLibrary.get_engine_version()) is not None, "Apply requires Unreal 5.8.3")
    require(Path(u.Paths.get_project_file_path()).resolve() == (Path(repo)/"CoopGame.uproject").resolve(), "Open editor project differs from script checkout")
    require({p["name"] for p in plan} == set(HASHES) and len(plan) == 3, "Invalid apply plan")
    for p in plan:
        name = p["name"]
        require(p["destination_object"] == DEST+"/"+name+"."+name, "Apply destination outside HC-A3")
        require(Path(p["source"]).resolve() == (Path(repo)/("SourceArt/HC/HC-A3/"+name+".png")).resolve(), "Apply source outside approved files")
        require(hashlib.sha256(Path(p["source"]).read_bytes()).hexdigest() == HASHES[name], "Source changed after validation")
        require(not u.EditorAssetLibrary.does_asset_exist(DEST+"/"+name), "Refusing to overwrite existing texture: "+name)
    properties = {
        "compression_settings":u.TextureCompressionSettings.TC_EDITOR_ICON,
        "lod_group":u.TextureGroup.TEXTUREGROUP_UI,
        "mip_gen_settings":u.TextureMipGenSettings.TMGS_NO_MIPMAPS,
        "srgb":True,"compression_no_alpha":False,"never_stream":True,
        "virtual_texture_streaming":False,"address_x":u.TextureAddress.TA_CLAMP,
        "address_y":u.TextureAddress.TA_CLAMP,"filter":u.TextureFilter.TF_BILINEAR
    }
    tasks = []
    for p in plan:
        factory = u.TextureFactory()
        for key,value in {"create_material":False,"edit_after_new":False,"no_alpha":False,
                          "compression_settings":properties["compression_settings"],
                          "lod_group":properties["lod_group"],"mip_gen_settings":properties["mip_gen_settings"]}.items():
            factory.set_editor_property(key,value)
        task = u.AssetImportTask()
        for key,value in {"filename":p["source"],"destination_path":DEST,"destination_name":p["name"],
                          "automated":True,"replace_existing":False,"replace_existing_settings":False,
                          "save":False,"async_":False,"factory":factory}.items():
            task.set_editor_property(key,value)
        tasks.append(task)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    textures = []
    for p,task in zip(plan,tasks):
        objects = list(task.get_objects())
        require(list(task.get_editor_property("imported_object_paths")) == [p["destination_object"]], "Unexpected import output; stop and inspect HC-A3 folder")
        require(len(objects) == 1 and isinstance(objects[0],u.Texture2D), "Import did not yield exactly one Texture2D")
        texture = objects[0]
        require(texture.get_path_name() == p["destination_object"], "Unexpected texture object path")
        for key,value in properties.items():
            texture.set_editor_property(key,value)
        for key,value in properties.items():
            require(texture.get_editor_property(key) == value, "Texture property failed: "+key)
        textures.append(texture)
    # Save only these new textures. Never Save All or touch widgets/materials/maps/Core.
    for texture in textures:
        require(u.EditorAssetLibrary.save_loaded_asset(texture,only_if_is_dirty=False), "Texture save failed")
    return [texture.get_path_name() for texture in textures]

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply",action="store_true",help="Explicitly create 3 new textures in the matching UE 5.8.3 editor")
    args = parser.parse_args(argv)
    manifest = json.loads((HERE/"manifest.json").read_text(encoding="utf-8"))
    plan = validate(manifest)
    result = {"mode":"apply" if args.apply else "dry-run","engine_target":"5.8.3",
              "dependency":"PR #68 / codex/hc-a3-hud-art","proposed_imports":plan,
              "texture_settings":SETTINGS,"writes_performed":False}
    print(json.dumps(result,indent=2))
    if args.apply:
        imported = apply_imports(plan)
        print(json.dumps({"mode":"apply","saved_textures":imported},indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
