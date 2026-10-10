import json
from pathlib import Path
import traceback
import unreal
root = Path(__file__).resolve().parents[3]
actual = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()
assert actual == root / "CoopGame.uproject", actual
out = root / "Tools/unreal/hc_a2_import/evidence/editor_inventory.json"
report={"project":str(actual),"engine":unreal.SystemLibrary.get_engine_version()}
try:
 registry=unreal.AssetRegistryHelpers.get_asset_registry()
 registry.search_all_assets(True)
 report["puzzle_assets"]=[str(a.package_name) for a in registry.get_assets_by_path("/Game/Puzzles",True)]
 report["apis"]={name:hasattr(unreal,name) for name in
                 ("KBoxElem","KAggregateGeom","EditorAssetLibrary","StaticMeshEditorSubsystem",
                  "SubobjectDataSubsystem","BlueprintEditorLibrary","AutomationLibrary")}
 world=unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/L_Site01")
 report["actors"]=[]
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  loc=a.get_actor_location()
  report["actors"].append({"name":a.get_name(),"label":a.get_actor_label(),"class":a.get_class().get_path_name(),
   "level":a.get_outermost().get_name(),"location":[loc.x,loc.y,loc.z],
   "meshes":[{"component":c.get_name(),"mesh":c.static_mesh.get_path_name() if c.static_mesh else None}
             for c in a.get_components_by_class(unreal.StaticMeshComponent)]})
 report["status"]="passed"
except Exception:
 report["status"]="failed";report["error"]=traceback.format_exc()
out.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("HCA2_INVENTORY",report["status"])
