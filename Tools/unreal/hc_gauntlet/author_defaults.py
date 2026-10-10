"""Remove duplicate-source root transform/physics state from owned HC roles."""
import sys,importlib,json
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
report=[]
for name in ['BP_HCGauntletCoordinator','BP_HCGauntletGateBridge']:
 bp=ue.load_asset('/Game/Puzzles/Gauntlet/'+name);owned(bp)
 d=ue.get_default_object(bp.generated_class())
 report.append({'asset':bp.get_path_name(),'before_scale':str(d.static_mesh_component.get_editor_property('relative_scale3d'))})
 d.static_mesh_component.set_editor_property('relative_scale3d',ue.Vector(1,1,1))
 d.static_mesh_component.set_editor_property('relative_location',ue.Vector())
 d.static_mesh_component.set_editor_property('relative_rotation',ue.Rotator())
 d.static_mesh_component.set_enable_gravity(False);d.static_mesh_component.set_simulate_physics(False)
 save(bp)
fixture=ue.load_asset('/Game/Puzzles/Test/HC_Gauntlet/BP_FixtureLatchBridge')
d=ue.get_default_object(fixture.generated_class())
d.static_mesh_component.set_editor_property('relative_scale3d',ue.Vector(1,1,1));save(fixture)
levels=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
assert levels.load_level('/Game/Puzzles/Test/HC_Gauntlet/L_HCGauntlet_Test')
actor=next(a for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors() if a.actor_has_tag('HC_GauntletCoordinator'))
report.append({'placed_coordinator_scale':str(actor.get_actor_scale3d())})
actor.set_actor_scale3d(ue.Vector(1,1,1));assert levels.save_current_level()
(HERE/'root-defaults.json').write_text(json.dumps(report,indent=2))
