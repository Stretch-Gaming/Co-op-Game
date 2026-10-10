"""Add HC-A2 placements to the upstream HC map, preserving every existing actor."""
import json
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/"CoopGame.uproject"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.set_current_level_by_name("L_Site01_HC")
level=levels.get_current_level()
assert level.get_outermost().get_name()=="/Game/Puzzles/L_Site01_HC"
before=[a for a in actors.get_all_level_actors() if a.get_outermost().get_name()=="/Game/Puzzles/L_Site01_HC" and not a.actor_has_tag("HC_A2_Prop")]
snapshot={a.get_name():{"label":a.get_actor_label(),"class":a.get_class().get_path_name(),"location":[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z]} for a in before}
plan=json.loads((root/"Tools/unreal/hc_a2_import/evidence/assemblies_placement.json").read_text())
added=[]
for spec in plan["site_placements"]:
 existing=[a for a in actors.get_all_level_actors() if a.get_actor_label()==spec["label"]]
 if existing:
  assert len(existing)==1 and existing[0].actor_has_tag("HC_A2_Prop")
  pos=existing[0].get_actor_location()
  assert [pos.x,pos.y,pos.z]==spec["location"]
  added.append(existing[0].get_name())
  continue
 a=actors.spawn_actor_from_object(unreal.load_asset(spec["asset"]),unreal.Vector(*spec["location"]),unreal.Rotator(),False)
 assert a.get_outermost().get_name()=="/Game/Puzzles/L_Site01_HC"
 a.set_actor_label(spec["label"]);a.set_folder_path("HC_A2_Props")
 a.set_editor_property("tags",[unreal.Name("HC_A2_Prop"),unreal.Name("HC_A2_ArtOnly")])
 added.append(a.get_name())
for a in before:
 assert snapshot[a.get_name()]=={"label":a.get_actor_label(),"class":a.get_class().get_path_name(),"location":[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z]}
assert unreal.EditorLoadingAndSavingUtils.save_packages([level.get_outermost()],False)
(root/"Tools/unreal/hc_a2_import/evidence/upstream_integration.json").write_text(json.dumps({
 "status":"passed","preserved_upstream_actors":snapshot,"added_hc_a2_actors":added,
 "resolution":"Retained upstream map in Git; added only HC-A2 actors through the editor. No binary text merge or older-map replacement."},indent=2),encoding="utf-8")

