import sys,pathlib,importlib,json
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import authoring;importlib.reload(authoring)
from authoring import *
guard();assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
TEST='/Game/Puzzles/Test/HC6_Altar/'
probe=create(TEST+'BP_HC6InputProbe',unreal.Actor.static_class())
fn(probe,'ResolveInput',[('Controller',unreal.PlayerController.static_class())],[('Subsystem',unreal.Object.static_class())])
write(probe,'ResolveInput','(return (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController Controller))','Controller');save(probe)
editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);path=TEST+'L_HC6_Altar'
assert not unreal.EditorAssetLibrary.does_asset_exist(path),'Preserve existing fixture'
assert editor.new_level(path)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',unreal.load_asset('/Game/Core/BP_CoopGameMode').generated_class())
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def spawn(cls,loc,label):
 assert world.get_path_name().split('.')[0]==path
 a=actors.spawn_actor_from_class(cls,unreal.Vector(*loc));a.set_actor_label(label);a.tags=[unreal.Name(label)];return a
floor=spawn(unreal.StaticMeshActor,(300,0,-25),'AltarFixtureFloor');floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(35,35,.5))
sun=spawn(unreal.DirectionalLight,(0,0,500),'AltarFixtureLight');sun.set_actor_rotation(unreal.Rotator(pitch=-50,yaw=-20),False);sun.get_component_by_class(unreal.DirectionalLightComponent).set_mobility(unreal.ComponentMobility.MOVABLE)
spawn(unreal.SkyAtmosphere,(0,0,0),'AltarFixtureSky');sky=spawn(unreal.SkyLight,(0,0,500),'AltarFixtureSkyLight');sky.get_component_by_class(unreal.SkyLightComponent).set_mobility(unreal.ComponentMobility.MOVABLE)
for i,y in enumerate([-600,-200,200,600]):spawn(unreal.PlayerStart,(-500,y,100),'AltarStart'+str(i))
spawn(unreal.load_asset('/Game/Puzzles/BP_Altar').generated_class(),(600,0,0),'Altar')
for name,cls,loc in [('KeyA','BP_KeyRelic',(0,-300,35)),('KeyB','BP_KeyRelic',(0,300,35)),('Wrong','BP_Statue',(0,700,65))]:spawn(unreal.load_asset('/Game/Puzzles/'+cls).generated_class(),loc,name)
assert editor.save_current_level()
bp=unreal.load_asset('/Game/Puzzles/BP_Altar')
out={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
pathlib.Path(__file__).parent.joinpath('saved-graphs.json').write_text(json.dumps(out,indent=2))
RESULT={'map':path,'graphs':out}
