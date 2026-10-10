"""Owned HC2 test fixtures only; never places actors in the cave."""
import unreal as ue,json
from pathlib import Path
assert Path(ue.Paths.project_dir()).resolve()==ROOT
path='/Game/Puzzles/Test/HC2/L_HC2_Test'
assert not ue.EditorAssetLibrary.does_asset_exist(path),'Preserve existing test level'
level=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
assert level.new_level(path)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
floor=actors.spawn_actor_from_class(ue.StaticMeshActor,ue.Vector(0,0,-25))
floor.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(ue.Vector(60,60,0.5));floor.set_actor_label('HC2_Floor')
light=actors.spawn_actor_from_class(ue.DirectionalLight,ue.Vector(0,0,500))
light.set_actor_rotation(ue.Rotator(pitch=-50,yaw=-20),False)
light.get_component_by_class(ue.DirectionalLightComponent).set_mobility(ue.ComponentMobility.MOVABLE)
actors.spawn_actor_from_class(ue.SkyAtmosphere,ue.Vector())
sky=actors.spawn_actor_from_class(ue.SkyLight,ue.Vector(0,0,500))
sky.get_component_by_class(ue.SkyLightComponent).set_mobility(ue.ComponentMobility.MOVABLE)
for y in (-600,-200,200,600):actors.spawn_actor_from_class(ue.PlayerStart,ue.Vector(0,y,100))
cls=ue.load_asset('/Game/Puzzles/BP_Relic').generated_class()
for name,minimum,value,x,y in [('Base',2,2,300,-800),('Race',2,5,300,-400),('Bonus3',3,3,300,0),('Bonus4',4,4,300,400),('Base2',2,1,300,800)]:
 relic=actors.spawn_actor_from_class(cls,ue.Vector(x,y,110));relic.set_actor_label('HC2_'+name)
 relic.set_editor_property('MinPlayers',minimum);relic.set_editor_property('Value',value)
 relic.set_editor_property('tags',[ue.Name('HC2_'+name)])
 if name=='Bonus3':relic.static_mesh_component.set_static_mesh(ue.load_asset('/Game/Puzzles/Art/HCA1_Relics/SM_Relic_JadeMask'))
 if name=='Bonus4':relic.static_mesh_component.set_static_mesh(ue.load_asset('/Game/Puzzles/Art/HCA1_Relics/SM_Relic_GemScarab'))
assert level.save_current_level()
(HERE/'fixtures.json').write_text(json.dumps({'map':path,'base_value':8,'three_value':11,'four_value':15,'players':4}))
