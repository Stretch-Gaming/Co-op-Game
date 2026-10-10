"""Editor-only HC-A2 compound collision authoring, bounded to four imported meshes."""
import json
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
actual=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()
assert actual==root/"CoopGame.uproject"
dest="/Game/Puzzles/Art/HCA2_Props"
subsystem=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
plans={}
for name,scale in (("SM_Statue",1.0),("SM_Statue_Small",110/180)):
 plans[name]=[([-52*scale,-51*scale,0],[52*scale,51*scale,60*scale]),
              ([-43*scale,-47*scale,60*scale],[43*scale,47*scale,180*scale])]
plans["SM_Altar"]=[([-40,-40,0],[40,40,76]),([-45,-45,76],[45,45,97])]
frame=[]
for sign in (-1,1):
 for x0,x1 in ((-65,-17),(17,65)):
  ys=sorted([sign*200,sign*300])
  frame.append(([x0,ys[0],0],[x1,ys[1],400]))
 ys=sorted([sign*218,sign*300])
 frame.append(([-17,ys[0],0],[17,ys[1],400]))
frame += [([-65,-330,400],[-17,330,511.2]),([17,-330,400],[65,330,511.2])]
plans["SM_ChamberGate_Frame"]=frame
report=[]
for name,ranges in plans.items():
 mesh=unreal.load_asset(dest+"/"+name)
 assert mesh and mesh.get_path_name().split(".")[0]==dest+"/"+name
 assert subsystem.get_simple_collision_count(mesh)==0, "Refuse to replace reviewed collision"
 boxes=[]
 for i,(lo,hi) in enumerate(ranges):
  box=unreal.KBoxElem()
  box.set_editor_property("center",unreal.Vector(*[(a+b)/2 for a,b in zip(lo,hi)]))
  box.set_editor_property("rotation",unreal.Rotator(0,0,0))
  for axis,size in zip(("x","y","z"),[b-a for a,b in zip(lo,hi)]):
   box.set_editor_property(axis,size)
  box.set_editor_property("name",unreal.Name("HC_A2_Box_"+str(i+1)))
  boxes.append(box)
 body=mesh.get_editor_property("body_setup")
 geometry=body.get_editor_property("agg_geom")
 geometry.set_editor_property("box_elems",boxes)
 body.set_editor_property("agg_geom",geometry)
 body.set_editor_property("collision_trace_flag",unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
 settings=subsystem.get_nanite_settings(mesh)
 subsystem.set_nanite_settings(mesh,settings,True)
 assert subsystem.get_simple_collision_count(mesh)==len(boxes)
 assert unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
 report.append({"mesh":name,"boxes":[{"min_cm":lo,"max_cm":hi} for lo,hi in ranges],
                "simple_collision_count":len(boxes),"saved":True})
(root/"Tools/unreal/hc_a2_import/evidence/compound_collision.json").write_text(
 json.dumps({"status":"passed","plans":report,"notes":[
  "Gate posts/lintel split around X +/-17 cm slot; Y +/-200 cm, Z0..400 cm passage clear.",
  "Gate core starts at Y +/-218 cm; 430 cm leaf ends at +/-215 cm.",
  "Altar cap collision top at Z97 cm keeps relic socket base accessible; pedestal collision is coarse.",
  "Both statue sizes have independently scaled plinth/owl boxes; all gameplay uses simple collision."]},indent=2),encoding="utf-8")
print("HCA2_COLLISION passed")
