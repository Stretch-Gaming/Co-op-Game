"""Owned isolated gauntlet fixture: unmodified PG levers/gate, labeled latch simulation."""
import sys,importlib,json
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
probe=create('/Game/Puzzles/Test/HC_Gauntlet/BP_GauntletInputProbe')
fn(probe,'ResolveInput',[('Controller',ue.PlayerController.static_class())],[('Subsystem',ue.Object.static_class())])
compile_bp(probe)
write(probe,'ResolveInput','(return (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController Controller))','Controller')
save(probe)
path='/Game/Puzzles/Test/HC_Gauntlet/L_HCGauntlet_Test'
assert not ue.EditorAssetLibrary.does_asset_exist(path),'Preserve the existing owned fixture; change only through an explicit fixture update'
levels=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
assert levels.new_level(path)
ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world().get_world_settings().set_editor_property('default_game_mode',ue.load_asset('/Game/Core/BP_CoopGameMode').generated_class())
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
floor=actors.spawn_actor_from_class(ue.StaticMeshActor,ue.Vector(800,0,-25))
floor.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(ue.Vector(50,40,.5));floor.set_actor_label('FIXTURE_HC_Gauntlet_Floor')
for y in (-750,-250,250,750):actors.spawn_actor_from_class(ue.PlayerStart,ue.Vector(-650,y,110))
light=actors.spawn_actor_from_class(ue.DirectionalLight,ue.Vector(0,0,600))
light.set_actor_rotation(ue.Rotator(pitch=-60),False)
light.get_component_by_class(ue.DirectionalLightComponent).set_mobility(ue.ComponentMobility.MOVABLE)
placements={}
def spawn(path,tag,location):
 a=actors.spawn_actor_from_class(ue.load_asset(path).generated_class(),ue.Vector(*location))
 a.set_actor_label(tag);a.set_editor_property('tags',[ue.Name(tag)])
 placements[tag]={'asset':path,'position':location,'components':[{'name':comp.get_name(),'class':comp.get_class().get_name()} for comp in a.get_components_by_class(ue.ActorComponent)]}
 return a
l1=spawn('/Game/Player/Round3/BP_Lever','HC_GauntletLever1',(100,-550,0))
l2=spawn('/Game/Player/Round3/BP_Lever','HC_GauntletLever2',(100,550,0))
gate=spawn('/Game/Player/Round3/BP_GauntletGate','HC_GauntletGate',(700,0,0))
# Same owned fixture map references, not production cross-sublevel references.
gate.set_editor_property('Levers',[l1,l2])
c=spawn('/Game/Puzzles/Gauntlet/BP_HCGauntletCoordinator','HC_GauntletCoordinator',(700,0,0))
c.set_editor_property('AllowFixtureBridge',True)
spawn('/Game/Puzzles/Gauntlet/BP_HCGauntletStart','HC_GauntletStart',(-250,1000,110))
spawn('/Game/Puzzles/Gauntlet/BP_HCGauntletObjective','HC_GauntletObjective',(1800,0,110))
spawn('/Game/Puzzles/Test/HC_Gauntlet/BP_FixtureLatchBridge','HC_GauntletBridge',(2000,1000,0))
assert levels.save_current_level()
(HERE/'fixture-level.json').write_text(json.dumps({'map':path,'placements':placements,'latch':'fixture simulation only; PG gate is unmodified and will close after ClearRound cancels holders','health_ghost_trap_cave':'not present; external integration dependencies'},indent=2))
