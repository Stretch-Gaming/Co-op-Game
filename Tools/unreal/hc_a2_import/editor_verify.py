"""Independent live read-back, assembly poses and simple-physics checks."""
import json, gc, re
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/"CoopGame.uproject"
s=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
manifest=json.loads((root/"Tools/unreal/hc_a2_import/manifest.json").read_text())
report={"mesh_readback":[],"pose_checks":[],"physics_checks":[],"gate_envelope":[]}
for spec in manifest["assets"]:
 mesh=unreal.load_asset(spec["destination"])
 assert mesh
 bounds=mesh.get_bounds()
 actual=[2*getattr(bounds.box_extent,a) for a in ("x","y","z")]
 assert all(abs(x-y)<0.5 for x,y in zip(actual,spec["validation_metadata"]["dimensions_cm"])), (spec["name"],actual,spec["validation_metadata"]["dimensions_cm"])
 assert s.get_nanite_settings(mesh).get_editor_property("enabled")==spec["nanite"]
 slots=mesh.get_editor_property("static_materials")
 expected=spec["material_slots"]
 for i,slot in enumerate(slots):
  assert str(slot.get_editor_property("imported_material_slot_name"))==expected[i]
  material=slot.get_editor_property("material_interface")
  assert material.get_path_name().startswith("/Game/Puzzles/Art/HCA2_Props/Materials/MI_HCA2_")
  assert material.get_editor_property("parent").get_path_name()=="/Game/Shared/Style/M_Stylized.M_Stylized"
 count=s.get_simple_collision_count(mesh)
 assert count==(8 if spec["name"]=="SM_ChamberGate_Frame" else 2 if spec["name"] in ("SM_Statue","SM_Statue_Small","SM_Altar") else 1)
 report["mesh_readback"].append({"name":spec["name"],"dimensions_cm":actual,"nanite":spec["nanite"],"simple_collision_count":count})
assert levels.load_level("/Game/Puzzles/Test/L_HCA2_Props")
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
owned=[a for a in actors.get_all_level_actors() if a.actor_has_tag("HC_A2_Prop")]
assert len(owned)==9,len(owned)
def component(actor,prefix):
 return next(c for c in actor.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith(prefix))
def line(start,end,ignore=()):
 return unreal.SystemLibrary.line_trace_single(world,unreal.Vector(*start),unreal.Vector(*end),
  unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,list(ignore),unreal.DrawDebugTrace.NONE,True)
def box(start,end,ignore=()):
 return unreal.SystemLibrary.box_trace_single(world,unreal.Vector(*start),unreal.Vector(*end),
  unreal.Vector(34,34,88),unreal.Rotator(0,0,0),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,list(ignore),unreal.DrawDebugTrace.NONE,True)
def hit_z(hit):
 text=hit.export_text()
 match=re.search(r"Location=\([^)]*Z=([-+0-9.eE]+)",text)
 assert match, text
 return float(match.group(1))
for actor in owned:
 label=actor.get_actor_label()
 assert actor.get_actor_scale3d()==unreal.Vector(1,1,1)
 for c in actor.get_components_by_class(unreal.StaticMeshComponent): assert c.static_mesh
 loc=actor.get_actor_location()
 if any(symbol in label for symbol in ("Diamond","Circle","Triangle","Cross")):
  top=component(actor,"PlateTop")
  actor.call_method("SetPressedVisual",args=(False,))
  raised=top.get_editor_property("relative_location").z
  high=line((loc.x,loc.y,loc.z+100),(loc.x,loc.y,loc.z-5))
  actor.call_method("SetPressedVisual",args=(True,))
  pressed=top.get_editor_property("relative_location").z
  low=line((loc.x,loc.y,loc.z+100),(loc.x,loc.y,loc.z-5))
  assert abs(raised-9)<0.001 and abs(pressed-2)<0.001
  assert high is not None and low is not None
  assert abs(hit_z(high)-hit_z(low)-7)<0.05
  actor.call_method("SetPressedVisual",args=(False,))
  report["pose_checks"].append({"label":label,"raised_z_cm":raised,"pressed_z_cm":pressed})
  report["physics_checks"].append({"label":label,"raised_surface_cm":hit_z(high),"pressed_surface_cm":hit_z(low)})
 if "_Gate_" in label:
  leaf=component(actor,"GateLeaf")
  actor.call_method("SetOpenVisual",args=(False,))
  closed=leaf.get_editor_property("relative_location").z
  hit=box((loc.x-200,loc.y,loc.z+100),(loc.x+200,loc.y,loc.z+100))
  assert hit is not None,"Closed gate must block pawn-size sweep"
  actor.call_method("SetOpenVisual",args=(True,))
  opened=leaf.get_editor_property("relative_location").z
  clear=box((loc.x-200,loc.y,loc.z+100),(loc.x+200,loc.y,loc.z+100))
  assert clear is None,"Open gate passage must be clear"
  assert abs(closed)<0.001 and abs(opened-400)<0.001
  actor.call_method("SetOpenVisual",args=(label.endswith("_Open"),))
  report["pose_checks"].append({"label":label,"closed_z_cm":closed,"open_z_cm":opened})
  report["physics_checks"].append({"label":label,"closed_blocks_pawn_size_sweep":True,"open_passage_clear":True})
altar=next(a for a in owned if a.get_actor_label()=="HC_A2_Test_Altar")
p=altar.get_actor_location()
hit=line((p.x,p.y,150),(p.x,p.y,90))
assert hit and abs(hit_z(hit)-97)<0.1
report["physics_checks"].append({"label":"altar socket","simple_surface_z_cm":hit_z(hit)})
owned=None;actor=None;altar=None;top=None;leaf=None;world=None;c=None;gc.collect()
assert levels.load_level("/Game/Maps/L_Site01")
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
owned=[a for a in actors.get_all_level_actors() if a.actor_has_tag("HC_A2_Prop")]
assert len(owned)==11
assert all(a.get_outermost().get_name()=="/Game/Puzzles/L_Site01_HC" for a in owned)
for gate in [a for a in owned if "_Gate_" in a.get_actor_label()]:
 p=gate.get_actor_location()
 ignore=[a for a in owned]
 samples=[]
 for z in (525,650,825):
  hit=line((p.x-100,p.y,z),(p.x+100,p.y,z),ignore)
  samples.append({"z_cm":z,"rock_hit_along_x":hit is not None})
 report["gate_envelope"].append({"label":gate.get_actor_label(),"samples":samples,
  "status":"requires visual envelope review; these rays do not alone prove complete leaf concealment"})
report["site_placements_in_HC_only"]=11
settings=unreal.load_object(None,"/Script/UnrealEd.Default__LevelEditorPlaySettings")
report["pie_settings_before"]=unreal.ToolsetLibrary.get_object_properties(settings,["PlayNetMode","PlayNumberOfClients","RunUnderOneProcess","ServerPort"])
report["status"]="passed"
(root/"Tools/unreal/hc_a2_import/evidence/editor_verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("HCA2_VERIFICATION passed")
