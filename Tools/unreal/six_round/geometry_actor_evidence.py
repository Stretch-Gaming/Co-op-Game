"""Read-only actor and movement contracts for diagnosing clearance failures."""
import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
items=[]
for actor in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors():
    center,extent=actor.get_actor_bounds(False)
    mesh=actor.get_component_by_class(ue.StaticMeshComponent)
    asset=mesh.get_editor_property('static_mesh') if mesh else None
    items.append({'path':actor.get_path_name(),'label':actor.get_actor_label(),'class':actor.get_class().get_name(),'level':actor.get_level().get_outermost().get_name(),
                  'center':[center.x,center.y,center.z],'extent':[extent.x,extent.y,extent.z],
                  'location':[actor.get_actor_location().x,actor.get_actor_location().y,actor.get_actor_location().z],
                  'mesh':asset.get_path_name() if asset else None,'tags':[str(tag) for tag in actor.tags]})
(QUEUE/'world-actor-bounds.json').write_text(json.dumps(items,indent=2))
character=BP.get_default_object(ue.load_asset('/Game/Core/BP_CoopCharacter'))
capsule=character.get_component_by_class(ue.CapsuleComponent)
carry=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying')
graphs={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(carry)}
speed={name:body for name,body in graphs.items() if 'CarrySpeed' in body or 'SavedSpeed' in body}
report={'capsule':{'radius':capsule.get_editor_property('capsule_radius'),'half_height':capsule.get_editor_property('capsule_half_height')},'carrying_speed_graphs':speed}
(QUEUE/'movement-contract.json').write_text(json.dumps(report,indent=2))
RESULT={'actors':len(items),'bounds':'Saved/SixRound/world-actor-bounds.json','movement':report}
