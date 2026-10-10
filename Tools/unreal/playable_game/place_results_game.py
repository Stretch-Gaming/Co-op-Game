import json
import unreal as ue
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
if not ue.EditorAssetLibrary.does_asset_exist('/Game/Puzzles/L_Site02_HC'):
 assert editor.new_level('/Game/Puzzles/L_Site02_HC');assert editor.save_current_level()
assert editor.load_level('/Game/Maps/L_Site02');world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();tag='AdventureResultsSetup'
hz=ue.GameplayStatics.get_streaming_level(world,'L_Site02_HZ');hc=ue.GameplayStatics.get_streaming_level(world,'L_Site02_HC')
if not hc:
 hc=ue.EditorLevelUtils.add_level_to_world(world,'/Game/Puzzles/L_Site02_HC',ue.LevelStreamingAlwaysLoaded);assert hc
 assert ue.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False)
assert hz and hc
for actor in actors.get_all_level_actors():
 if actor.actor_has_tag(tag):assert actors.destroy_actor(actor)
ue.EditorLevelUtils.make_level_current(hz)
def spawn(cls,name,location):
 actor=actors.spawn_actor_from_class(cls,ue.Vector(*location),ue.Rotator());actor.set_actor_label(name);actor.set_editor_property('tags',[ue.Name(tag)]);return actor
def shape(name,location,scale,mesh='/Engine/BasicShapes/Cube',material='/Game/Puzzles/Art/HCA2_Props/Materials/MI_HCA2_Stone'):
 actor=spawn(ue.StaticMeshActor,name,location);component=actor.static_mesh_component;component.set_static_mesh(ue.load_asset(mesh));actor.set_actor_scale3d(ue.Vector(*scale));component.set_material(0,ue.load_asset(material));component.set_collision_profile_name('BlockAll');return actor
shape('Egypt_Floor',(0,0,-25),(20,20,.5))
for name,p,scale in [('West',(-1050,0,400),(1,22,8)),('East',(1050,0,400),(1,22,8)),('North',(0,1050,400),(20,1,8)),('South',(0,-1050,400),(20,1,8))]:shape('Egypt_'+name,p,scale)
for x in (-700,700):
 for y in (-650,650):shape('Egypt_Column_'+str(x)+'_'+str(y),(x,y,350),(1,1,7),'/Engine/BasicShapes/Cylinder')
for x in (-600,600):
 shape('Egypt_Brazier_'+str(x),(x,800,80),(.8,.8,1.6),'/Engine/BasicShapes/Cylinder','/Game/Shared/Style/MI_Stylized_Gold')
 light=spawn(ue.PointLight,'Egypt_BrazierLight_'+str(x),(x,800,210)).get_component_by_class(ue.PointLightComponent);light.set_mobility(ue.ComponentMobility.MOVABLE);light.set_editor_property('intensity',3500);light.set_editor_property('attenuation_radius',2200);light.set_light_color(ue.LinearColor(1,.53,.22,1));light.set_editor_property('cast_shadows',False)
shape('Egypt_SealedDoor',(0,985,300),(4,.4,6),material='/Game/Shared/Style/MI_Stylized_Gold')
assert ue.EditorLoadingAndSavingUtils.save_packages([hz.get_loaded_level().get_outermost()],False)
ue.EditorLevelUtils.make_level_current(hc)
co=spawn(ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator').generated_class(),'Egypt_RunCoordinator',(0,0,0));co.set_actor_hidden_in_game(True);co.set_actor_enable_collision(False)
assert ue.EditorLoadingAndSavingUtils.save_packages([hc.get_loaded_level().get_outermost()],False)
RESULT={'results_room_placed':True,'singleton_results_coordinator':True,'runtime_acceptance_pending':True}
