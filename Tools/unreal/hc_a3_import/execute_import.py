"""Execute the already-reviewed HC-A3 texture importer inside UE 5.8.3 only."""
import json
from pathlib import Path
import runpy
import traceback
import unreal

repo = Path(__file__).resolve().parents[3]
out = repo / "SourceArt/HC/HC-A3/integration"
out.mkdir(parents=True,exist_ok=True)
try:
    api = runpy.run_path(str(repo/"Tools/unreal/hc_a3_import/import_hud.py"),run_name="hc_a3_import")
    manifest = json.loads((repo/"Tools/unreal/hc_a3_import/manifest.json").read_text())
    plan = api["validate"](manifest)
    saved = api["apply_imports"](plan)
    records = []
    for p in plan:
        texture = unreal.load_asset(p["destination_object"])
        assert texture and texture.get_class().get_name()=="Texture2D"
        props = {key:str(texture.get_editor_property(key)) for key in api["SETTINGS"]}
        records.append({"path":texture.get_path_name(),"source_sha256":p["sha256"],
                        "properties":props,"source_file":texture.get_editor_property("asset_import_data").get_first_filename()})
    report={"passed":True,"engine_version":unreal.SystemLibrary.get_engine_version(),
            "project":unreal.Paths.get_project_file_path(),"saved":saved,"textures":records}
    (out/"texture-import.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    unreal.log("HC-A3 texture imports verified and saved.")
except Exception:
    (out/"texture-import-error.txt").write_text(traceback.format_exc(),encoding="utf-8")
    raise
