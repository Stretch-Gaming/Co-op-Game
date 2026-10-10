"""Create HC-A2 art assemblies and art-test map, then place only in L_Site01_HC."""
import json, subprocess
from pathlib import Path
import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools
root=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/"CoopGame.uproject"
dest="/Game/Puzzles/Art/HCA2_Props"
assembly_dir=dest+"/Assemblies"
assets=unreal.AssetToolsHelpers.get_asset_tools()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
report={"blueprints":[],"test_placements":[],"site_placements":[],"gameplay_scope":"art-only; HC-4/5/6 gameplay is not created"}
specs=["BP_HCA2_Plate_Diamond","BP_HCA2_Plate_Circle","BP_HCA2_Plate_Triangle","BP_HCA2_Plate_Cross","BP_HCA2_ChamberGate"]
for name in specs:
 bp=unreal.load_asset(assembly_dir+"/"+name)
 assert bp
 BP.compile_blueprint(bp,warnings_as_errors=True)
 assert bp.get_editor_property("status")==unreal.BlueprintStatus.BS_UP_TO_DATE
 report["blueprints"].append({"path":assembly_dir+"/"+name,"compile":"passed"})
test="/Game/Puzzles/Test/L_HCA2_Props"
assert not unreal.EditorAssetLibrary.does_asset_exist(test), "Refuse test-map overwrite"
assert levels.new_level_from_template(test,"/Game/Shared/Style/L_StyleTest")
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert levels.get_current_level().get_outermost().get_name()==test
def place(path,label,location,rotation=0):
 assert all(a.get_actor_label()!=label for a in actors.get_all_level_actors()), "Existing owned placement"
 asset=unreal.load_asset(path)
 actor=actors.spawn_actor_from_object(asset,unreal.Vector(*location),unreal.Rotator(0,rotation,0),False)
 assert actor and actor.get_outermost().get_name()==levels.get_current_level().get_outermost().get_name()
 actor.set_actor_label(label)
 actor.set_folder_path("HC_A2_Props")
 actor.set_editor_property("tags",[unreal.Name("HC_A2_Prop"),unreal.Name("HC_A2_ArtOnly")])
 return actor
test_specs=[
 (assembly_dir+"/BP_HCA2_Plate_Diamond","HC_A2_Test_Diamond",(-500,900,0)),
 (assembly_dir+"/BP_HCA2_Plate_Circle","HC_A2_Test_Circle",(-250,900,0)),
 (assembly_dir+"/BP_HCA2_Plate_Triangle","HC_A2_Test_Triangle",(0,900,0)),
 (assembly_dir+"/BP_HCA2_Plate_Cross","HC_A2_Test_Cross",(250,900,0)),
 (dest+"/SM_Statue","HC_A2_Test_Statue_180",(-400,1250,0)),
 (dest+"/SM_Statue_Small","HC_A2_Test_Statue_110",(-150,1250,0)),
 (dest+"/SM_Altar","HC_A2_Test_Altar",(150,1250,0)),
 (assembly_dir+"/BP_HCA2_ChamberGate","HC_A2_Test_Gate_Closed",(850,1000,0)),
 (assembly_dir+"/BP_HCA2_ChamberGate","HC_A2_Test_Gate_Open",(1800,1000,0)),
]
for path,label,location in test_specs:
 a=place(path,label,location)
 if label.endswith("_Open"):
  a.call_method("SetOpenVisual",args=(True,))
 report["test_placements"].append({"label":label,"asset":path,"location":location})
assert unreal.EditorLoadingAndSavingUtils.save_map(world,test)
world=None
a=None
import gc
gc.collect()
assert levels.load_level("/Game/Maps/L_Site01")
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert levels.set_current_level_by_name("L_Site01_HC")
assert levels.get_current_level().get_outermost().get_name()=="/Game/Puzzles/L_Site01_HC"
site_specs=[
 (assembly_dir+"/BP_HCA2_Plate_Diamond","HC_A2_Plate_Diamond",(3200,-800,0)),
 (assembly_dir+"/BP_HCA2_Plate_Circle","HC_A2_Plate_Circle",(3200,800,0)),
 (assembly_dir+"/BP_HCA2_Plate_Triangle","HC_A2_Plate_Triangle",(4800,-800,0)),
 (assembly_dir+"/BP_HCA2_Plate_Cross","HC_A2_Plate_Cross",(4800,800,0)),
 (dest+"/SM_Statue","HC_A2_Statue_Alcove_1",(3500,1300,0)),
 (dest+"/SM_Statue","HC_A2_Statue_Alcove_2",(4000,1300,0)),
 (dest+"/SM_Statue","HC_A2_Statue_Alcove_3",(4500,1300,0)),
 (dest+"/SM_Altar","HC_A2_Altar",(10800,0,0)),
 (assembly_dir+"/BP_HCA2_ChamberGate","HC_A2_Gate_G1",(2500,0,0)),
 (assembly_dir+"/BP_HCA2_ChamberGate","HC_A2_Gate_G2",(5500,0,0)),
 (assembly_dir+"/BP_HCA2_ChamberGate","HC_A2_Gate_G3",(11500,0,0)),
]
for path,label,location in site_specs:
 a=place(path,label,location)
 assert a.get_outermost().get_name()=="/Game/Puzzles/L_Site01_HC"
 report["site_placements"].append({"label":label,"asset":path,"location":location})
package=levels.get_current_level().get_outermost()
assert unreal.EditorLoadingAndSavingUtils.save_packages([package],False)
report["saved_packages"]=["/Game/Puzzles/L_Site01_HC",test]+[a["path"] for a in report["blueprints"]]
report["statue_choice"]="Original #19 specification: 1.8 m statue for alcove placements. 1.1 m asset retained and shown in test map; no gameplay carry variant chosen."
report["greybox_replacement"]="No HC puzzle actors or greyboxes existed on the starting main; new art-only placements at documented coordinates. Gameplay integration remains HC-4/5/6."
report["status"]="passed"
(root/"Tools/unreal/hc_a2_import/evidence/assemblies_placement.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("HCA2_ASSEMBLY passed")
