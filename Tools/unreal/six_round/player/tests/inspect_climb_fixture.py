"""Read-only live climb actor/floor query; no geometry or gameplay state edits."""
import json
import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();pawns=list(ue.GameplayStatics.get_all_actors_of_class(server,C))
half=pawns[0].get_component_by_class(ue.CapsuleComponent).get_scaled_capsule_half_height()
records=[]
for actor in ue.GameplayStatics.get_all_actors_with_tag(server,'Climbable'):
 box=actor.get_component_by_class(ue.BoxComponent)
 if not box:continue
 center=box.get_world_location();extent=box.get_scaled_box_extent()
 records.append({'label':actor.get_actor_label(),'center':[center.x,center.y,center.z],'extent':[extent.x,extent.y,extent.z]})
RESULT={'climbs':records};(QUEUE/'qa-climb-fixtures.json').write_text(json.dumps(RESULT,indent=2))
