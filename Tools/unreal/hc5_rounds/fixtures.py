import sys,json
sys.path.insert(0,str(HERE))
from authoring import *
assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
TEST='/Game/Puzzles/Test/HC5/'
command=unreal.load_asset(TEST+'BP_HC5Command')
if not command:command=unreal.EditorAssetLibrary.duplicate_asset('/Game/Puzzles/BP_Carryable',TEST+'BP_HC5Command')
for n,k in [('CommandKind','int'),('CommandRound','int'),('ResetCount','int'),('LastResetIndex','int'),('LastResetAttempt','int')]:var(command,n,k)
for n in ['ResetCount','LastResetIndex','LastResetAttempt']:BP.set_variable_replication(command,n,unreal.BlueprintVariableReplication.REPLICATED)
for n in ['CommandKind','CommandRound']:BP.set_variable_instance_editable(command,n,True)
fn(command,'RunCommand',[('Instigator',unreal.Actor.static_class())]);fn(command,'RecordReset',[('Index','int'),('Attempt','int')]);compile_bp(command)
write(command,'GetInteractInfo','(return "HC5 fixture command" 0.0 (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator0"))','Instigator')
write(command,'CanInteract','(return true)','Instigator')
write(command,'RunCommand','''
 (if (Networking|HasAuthority)
  (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
   (:then
    (if (== (Variables|Default|GetCommandKind) 1) (Class|BPCoopGameMode|ClearRound :self gm))
    (if (== (Variables|Default|GetCommandKind) 2) (Class|BPCoopGameMode|FailRound :self gm))
    (if (== (Variables|Default|GetCommandKind) 0)
     (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_RoundStart.BP_RoundStart_C")
      (bind entrance (Utilities|Casting|CastToBP_RoundStart :Object item)
       (:then (if (== (Class|BPRoundStart|GetRoundIndex :self entrance) (Variables|Default|GetCommandRound)) (Class|BPRoundStart|TryEnter :self entrance :EnteringActor Instigator))) (:CastFailed))))) (:CastFailed)))''','Instigator')
write(command,'RecordReset','''(if (Networking|HasAuthority)
 (Variables|Default|SetResetCount (+ (Variables|Default|GetResetCount) 1))
 (Variables|Default|SetLastResetIndex Index)
 (Variables|Default|SetLastResetAttempt Attempt))''','Index Attempt')
g=BP.get_graph(command,'EventGraph')
for node in BP.find_nodes(g):BP.delete_node(node)
for ev,handler,params in [('Interact','RunCommand',['Instigator']),('ResetForRound','RecordReset',['Index','Attempt'])]:
 e=BP.add_event(command,ev);call=BP.create_node(g,'CallFunction|'+handler,unreal.IntPoint(400,600));assert e.find_then_pin().try_create_connection(call.find_execute_pin())
 for p in params:assert e.find_output_pin(p).try_create_connection(call.find_input_pin(p))
compile_bp(command);defaults(command,replicates=True,always_relevant=True)
mesh=BP.get_default_object(command).static_mesh_component;mesh.set_simulate_physics(False);mesh.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));mesh.set_editor_property('relative_scale3d',unreal.Vector(.5,.5,.5));save(command)
probe=create(TEST+'BP_HC5InputProbe',unreal.Actor.static_class());fn(probe,'ResolveInput',[('Controller',unreal.PlayerController.static_class())],[('Subsystem',unreal.Object.static_class())]);write(probe,'ResolveInput','(return (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController Controller))','Controller');save(probe)
gm=create(TEST+'BP_HC5GameMode',unreal.load_asset('/Game/Core/BP_CoopGameMode').generated_class());save(gm)
editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);path=TEST+'L_HC5_Rounds';assert not unreal.EditorAssetLibrary.does_asset_exist(path),'Preserve existing fixture map';assert editor.new_level(path)
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();w.get_world_settings().set_editor_property('default_game_mode',gm.generated_class());actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def spawn(c,location,tag):
 assert w.get_path_name().split('.')[0]==path
 a=actors.spawn_actor_from_class(c,unreal.Vector(*location));a.tags=[unreal.Name(tag)];a.set_actor_label(tag);return a
floor=spawn(unreal.StaticMeshActor,(4500,0,-50),'HC5_Floor');floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(110,60,1))
for i,y in enumerate([-600,-200,200,600]):spawn(unreal.PlayerStart,(0,y,100),'HC5_Start'+str(i))
director=spawn(unreal.load_asset('/Game/Puzzles/Rounds/BP_RoundDirector').generated_class(),(0,1800,0),'HC5_Director')
for i in range(4):
 cp=spawn(unreal.load_asset('/Game/Puzzles/BP_Checkpoint').generated_class(),(i*3000,0,0),'HC5_Checkpoint'+str(i));cp.set_editor_property('RoundIndex',i)
 if i:
  start=spawn(unreal.load_asset('/Game/Puzzles/BP_RoundStart').generated_class(),(i*3000+500,0,100),'HC5_Entrance'+str(i));start.set_editor_property('RoundIndex',i);box=start.get_component_by_class(unreal.BoxComponent);box.set_editor_property('box_extent',unreal.Vector(100,650,150));box.set_collision_profile_name('Trigger');box.set_editor_property('generate_overlap_events',True)
for name,kind,index,y in [('Enter1',0,1,-1800),('Enter2',0,2,-1200),('Enter3',0,3,-600),('Clear',1,0,600),('Fail',2,0,1200)]:
 a=spawn(command.generated_class(),(600,y,60),'HC5_'+name);a.set_editor_property('CommandKind',kind);a.set_editor_property('CommandRound',index)
spawn(probe.generated_class(),(0,0,0),'HC5_InputProbe')
assert unreal.EditorLoadingAndSavingUtils.save_map(w,path)
(HERE/'fixtures.json').write_text(json.dumps({'passed':True,'map':path,'health_or_death_fixture':False}))
