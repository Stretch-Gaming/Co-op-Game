import sys,pathlib,importlib,json
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
TEST='/Game/Puzzles/Test/HC4/'
c=create(TEST+'BP_HC4Character',unreal.load_asset('/Game/Core/BP_CoopCharacter').generated_class())
pc=create(TEST+'BP_HC4Controller',unreal.load_asset('/Game/Core/BP_CoopPlayerController').generated_class())
gm=create(TEST+'BP_HC4GameMode',unreal.load_asset('/Game/Core/BP_CoopGameMode').generated_class())
ac=unreal.load_asset('/Game/Puzzles/Carrying/AC_Carrying')
part=component(c,'Carrying',ac.generated_class())
owned(c)
with toolset_registry.tool_raising_exceptions():
    for node in BP.find_nodes(BP.get_graph(c,'EventGraph')): BP.delete_node(node)
for name in ['RequestDrop','RequestRelease','DoDrop','DoRelease','TestInputSetup','TestBegin','RequestReset','DoReset','AddLocal']:
    fn(c,name)
var(c,'ReleasedItem',unreal.Actor.static_class(),True)
var(c,'TestInputController',unreal.PlayerController.static_class())
var(c,'TestAddedLocal','bool')
for name in ['Server_HC4Drop','Server_HC4Release','Server_HC4Reset']:
    owned(c)
    BP.add_event(c,name)
compile_bp(c)
write(c,'DoDrop','(Class|ACCarrying|DropCarried :self (Variables|Default|GetCarrying))')
write(c,'DoRelease','(Variables|Default|SetReleasedItem (Class|ACCarrying|ReleaseCarried :self (Variables|Default|GetCarrying)))')
write(c,'DoReset','''
 (if (Networking|HasAuthority)
   (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_Carryable.BP_Carryable_C")
     (Class|BPCarryable|ResetItem :self item)))''')
for kind in ['Drop','Release','Reset']:
    write(c,'Request'+kind,f'(if (Pawn|IsLocallyControlled) (CallFunction|ServerHC4{kind}))')
    event(c,'Server_HC4'+kind,'Do'+kind)
owned(c)
g=BP.get_graph(c,'EventGraph')
for action,handler in [('IA_Drop','RequestDrop')]:
    e=BP.create_node(g,'Input|EnhancedActionEvents|'+action,unreal.IntPoint(0,900))
    call=BP.create_node(g,'CallFunction|'+handler,unreal.IntPoint(400,900))
    assert e.find_output_pin('Started').try_create_connection(call.find_execute_pin())

mapping=unreal.load_asset(TEST+'IMC_HC4Test')
if not mapping:
    guard()
    mapping=unreal.AssetToolsHelpers.get_asset_tools().create_asset('IMC_HC4Test',TEST.rstrip('/'),unreal.InputMappingContext,unreal.InputMappingContext_Factory())
for name,key,handler in [('IA_HC4Release','H','RequestRelease'),('IA_HC4Reset','F8','RequestReset'),('IA_HC4AddLocal','F9','AddLocal')]:
    action=unreal.load_asset(TEST+name)
    if not action:
        guard()
        action=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,TEST.rstrip('/'),unreal.InputAction,unreal.InputAction_Factory())
        action.set_editor_property('value_type',unreal.InputActionValueType.BOOLEAN)
        k=unreal.Key(); assert k.import_text('(KeyName="'+key+'")')
        mapping.map_key(action,k)
    owned(c)
    e=BP.create_node(g,'Input|EnhancedActionEvents|'+name,unreal.IntPoint(0,1200))
    call=BP.create_node(g,'CallFunction|'+handler,unreal.IntPoint(400,1200))
    assert e.find_output_pin('Started').try_create_connection(call.find_execute_pin())
    guard(); unreal.EditorAssetLibrary.save_loaded_asset(action,False)
guard(); unreal.EditorAssetLibrary.save_loaded_asset(mapping,False)
write(c,'TestInputSetup',f'''
 (if (Pawn|IsLocallyControlled)
   (bind pc (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController))
     (:then
       (if (!= pc (Variables|Default|GetTestInputController))
       (bind sub (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController pc))
       (Utilities|IsValid :InputObject sub
         (:"Is Valid"
           (Input|AddMappingContext :self sub :MappingContext "{TEST}IMC_HC4Test.IMC_HC4Test" :Priority 10)
           (Variables|Default|SetTestInputController pc))
         (:"Is Not Valid")))) (:CastFailed)))''')
write(c,'AddLocal','''(if (and (and (Pawn|IsLocallyControlled) (Networking|HasAuthority)) (not (Variables|Default|GetTestAddedLocal)))
 (Variables|Default|SetTestAddedLocal true)
 (Game|CreateLocalPlayer :ControllerId -1 :bSpawnPlayerController true))''')
write(c,'TestBegin','''
 (CallFunction|HC1BeginPlay)
 (CallFunction|TestInputSetup)
 (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "TestInputSetup" :Time 0.5 :bLooping true)''')
# The audited Core BeginPlay calls HC1BeginPlay; reproduce that call in this fixture override.
owned(c)
e=BP.add_event(c,'ReceiveBeginPlay')
call=BP.create_node(g,'CallFunction|TestBegin',unreal.IntPoint(800,300))
assert e.find_then_pin().try_create_connection(call.find_execute_pin())
compile_bp(c); compile_bp(pc)
defaults(gm,default_pawn_class=c.generated_class(),player_controller_class=pc.generated_class())
for bp in [c,pc,gm]: save(bp)

guard()
editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
path=TEST+'L_HC4_Carrying'
assert not unreal.EditorAssetLibrary.does_asset_exist(path), 'Fixture exists; preserve it.'
assert editor.new_level(path)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',gm.generated_class())
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def spawn(cls,location):
    guard()
    assert world.get_path_name().split('.')[0]==path
    return actors.spawn_actor_from_class(cls,unreal.Vector(*location))
floor=spawn(unreal.StaticMeshActor,(500,0,-25))
floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(unreal.Vector(40,40,0.5))
floor.set_actor_label('HC4_Floor')
sun=spawn(unreal.DirectionalLight,(0,0,500))
sun.set_actor_rotation(unreal.Rotator(pitch=-50,yaw=-20,roll=0),False)
sun.get_component_by_class(unreal.DirectionalLightComponent).set_mobility(unreal.ComponentMobility.MOVABLE)
spawn(unreal.SkyAtmosphere,(0,0,0))
sky=spawn(unreal.SkyLight,(0,0,500))
sky.get_component_by_class(unreal.SkyLightComponent).set_mobility(unreal.ComponentMobility.MOVABLE)
probe=spawn(unreal.TriggerBox,(600,-600,90))
probe.set_actor_label('HC4_PlateWeightOverlapProbe')
probe.tags=[unreal.Name('HC4_WeightProbe')]
box=probe.get_component_by_class(unreal.BoxComponent)
box.set_editor_property('box_extent',unreal.Vector(100,100,100))
box.set_collision_profile_name('Trigger')
box.set_editor_property('generate_overlap_events',True)
for i,y in enumerate([-600,-200,200,600]):
    start=spawn(unreal.PlayerStart,(0,y,100))
    start.set_actor_label('HC4_Start_'+str(i))
    for name,x,z in [('BP_Carryable',150,30),('BP_KeyRelic',600,35),('BP_Statue',1050,65)]:
        item=spawn(unreal.load_asset('/Game/Puzzles/'+name).generated_class(),(x,y,z))
        item.set_actor_label('HC4_'+name+'_'+str(i))
        item.tags=[unreal.Name('HC4_'+name+'_'+str(i))]
        if name=='BP_Statue': item.set_actor_scale3d(unreal.Vector(0.5,0.5,1.1))
guard(); assert editor.save_current_level()
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([c])
RESULT={'fixtures_built':True,'rpc_flags_pending':True,'map':path}
