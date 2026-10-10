"""Create HC-A2 art assemblies and art-test map, then place only in L_Site01_HC."""
import json, subprocess
from pathlib import Path
import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools
from toolset_registry.helpers import compile_blueprint
root=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/"CoopGame.uproject"
dest="/Game/Puzzles/Art/HCA2_Props"
assembly_dir=dest+"/Assemblies"
assets=unreal.AssetToolsHelpers.get_asset_tools()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
report={"blueprints":[],"test_placements":[],"site_placements":[],"gameplay_scope":"art-only; HC-4/5/6 gameplay is not created"}
specs=[
 ("BP_HCA2_Plate_Diamond",[("PlateBase","SM_PressurePlate_Base",0),("PlateTop","SM_PressurePlate_Top",9)],"plate"),
 ("BP_HCA2_Plate_Circle",[("PlateBase","SM_PressurePlate_Base",0),("PlateTop","SM_PressurePlate_Top_Circle",9)],"plate"),
 ("BP_HCA2_Plate_Triangle",[("PlateBase","SM_PressurePlate_Base",0),("PlateTop","SM_PressurePlate_Top_Triangle",9)],"plate"),
 ("BP_HCA2_Plate_Cross",[("PlateBase","SM_PressurePlate_Base",0),("PlateTop","SM_PressurePlate_Top_Cross",9)],"plate"),
 ("BP_HCA2_ChamberGate",[("GateFrame","SM_ChamberGate_Frame",0),("GateLeaf","SM_ChamberGate_Leaf",0)],"gate"),
]
for name,parts,kind in specs:
 path=assembly_dir+"/"+name
 assert not unreal.EditorAssetLibrary.does_asset_exist(path), "Refuse existing assembly: "+path
 bp=BP.create(assembly_dir,name,unreal.Actor.static_class())
 for component_name,mesh_name,z in parts:
  c=ActorTools.add_component(bp,unreal.StaticMeshComponent.static_class(),component_name)
  c.set_editor_property("mobility",unreal.ComponentMobility.MOVABLE)
  c.set_editor_property("static_mesh",unreal.load_asset(dest+"/"+mesh_name))
  c.set_editor_property("relative_location",unreal.Vector(0,0,z))
  c.set_collision_profile_name("BlockAll")
  BP.compile_blueprint(bp)
 function="SetPressedVisual" if kind=="plate" else "SetOpenVisual"
 graph=BP.add_function_graph(bp,function)
 BP.add_function_param(graph,"Active","bool",True)
 target="PlateTop" if kind=="plate" else "GateLeaf"
 set_nodes=[n for n in BP.find_node_types(graph,"SetRelativeLocation") if n=="Transformation|SetRelativeLocation"]
 get_nodes=[n for n in BP.find_node_types(graph,"Get"+target) if n.startswith("Variables|") and n.endswith("|Get"+target)]
 assert len(set_nodes)==1 and len(get_nodes)==1, (set_nodes,get_nodes)
 active_z,inactive_z=(2,9) if kind=="plate" else (400,0)
 code=f'(fn {function} (Active) (if Active ({set_nodes[0]} :self ({get_nodes[0]}) :NewLocation "(X=0,Y=0,Z={active_z})") (else ({set_nodes[0]} :self ({get_nodes[0]}) :NewLocation "(X=0,Y=0,Z={inactive_z})"))))'
 if "SetRelativeLocation" not in BP.read_graph_dsl(graph):
  BP.write_graph_dsl(graph,code)
 assert "(else" in BP.read_graph_dsl(graph), "Missing false branch"
 compiled_graph=BP.read_graph_dsl(graph)
 compile_blueprint(bp,True)
 assert bp.get_editor_property("status")==unreal.BlueprintStatus.BS_UP_TO_DATE
 assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
 report["blueprints"].append({"path":path,"components":parts,"cosmetic_function":function,
                              "graph":compiled_graph,"compile":"passed"})
(root/"Tools/unreal/hc_a2_import/evidence/assemblies.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("HCA2_ASSEMBLIES passed")
