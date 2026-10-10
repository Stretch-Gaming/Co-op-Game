import json, sys, traceback
from pathlib import Path
import unreal
folder=Path(__file__).resolve().parent
sys.path.insert(0,str(folder))
import import_hc_a2
import importlib
importlib.reload(import_hc_a2)
report={"project":unreal.Paths.get_project_file_path(),"engine":unreal.SystemLibrary.get_engine_version()}
try:
 report["result"]=import_hc_a2.run(["--execute","--project-file",str(folder.parents[2]/"CoopGame.uproject")])
 report["status"]="passed"
except Exception:
 report["status"]="failed";report["error"]=traceback.format_exc()
(folder/"evidence/editor_import.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("HCA2_IMPORT",report["status"])
