exec(compile((HERE/'build.py').read_text().split('co=ue.load_asset')[0],str(HERE/'build.py'),'exec'),globals())
from editor_toolset.toolsets.actor import ActorTools as AT
TEST='/Game/Puzzles/Test/HC_RunEnding/'
gm=ue.load_asset(TEST+'BP_RunEndingFixtureGM');results=ue.load_asset('/Game/Puzzles/UI/Results/AC_RunResults')
pc=ue.load_asset(TEST+'BP_RunEndingFixturePC') or BP.create(TEST.rstrip('/'),'BP_RunEndingFixturePC',ue.load_asset('/Game/Core/BP_CoopPlayerController').generated_class())
if not BP.find_node_types(BP.get_graph(pc,'EventGraph'),'GetRunResults'):AT.add_component(pc,results.generated_class(),'RunResults')
if 'RestartInputEvents' not in BP.list_variables(pc):BP.add_variable(pc,'RestartInputEvents','int')
if 'TestInputAdded' not in BP.list_variables(pc):BP.add_variable(pc,'TestInputAdded','bool')
for n in ('FixtureBegin','FixtureRestart'):fn(pc,n)
compile_bp(pc)
action=ue.load_asset(TEST+'IA_FixtureRestart') or ue.AssetToolsHelpers.get_asset_tools().create_asset('IA_FixtureRestart',TEST.rstrip('/'),ue.InputAction,ue.InputAction_Factory())
action.set_editor_property('value_type',ue.InputActionValueType.BOOLEAN)
mapping=ue.load_asset(TEST+'IMC_FixtureRestart')
if not mapping:
 mapping=ue.AssetToolsHelpers.get_asset_tools().create_asset('IMC_FixtureRestart',TEST.rstrip('/'),ue.InputMappingContext,ue.InputMappingContext_Factory());key=ue.Key();assert key.import_text('(KeyName="R")');mapping.map_key(action,key)
write(pc,'FixtureBegin','''(fn FixtureBegin ()
 (CallFunction|HC1SetupDebugInput :self self)
 (if (and (Pawn|IsLocalController) (not (Variables|Default|GetTestInputAdded)))
  (bind sub (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController self))
  (Utilities|IsValid :InputObject sub
   (:"Is Valid" (Input|AddMappingContext :self sub :MappingContext "/Game/Puzzles/Test/HC_RunEnding/IMC_FixtureRestart.IMC_FixtureRestart" :Priority 20) (Variables|Default|SetTestInputAdded true)) (:"Is Not Valid"))))''')
write(pc,'FixtureRestart','''(fn FixtureRestart () (Variables|Default|SetRestartInputEvents (+ (Variables|Default|GetRestartInputEvents) 1)) (Class|ACRunResults|RequestLocalRestart :self (Variables|Default|GetRunResults)))''')
event(pc,'ReceiveBeginPlay','FixtureBegin')
g=BP.get_graph(pc,'EventGraph')
if not BP.find_nodes(g,'EnhancedInputActionIA_FixtureRestart'):
 e=BP.create_node(g,'Input|EnhancedActionEvents|IA_FixtureRestart',ue.IntPoint(0,500));call=BP.create_node(g,'CallFunction|FixtureRestart',ue.IntPoint(400,500));assert e.find_output_pin('Started').try_create_connection(call.find_execute_pin())
compile_bp(pc);ue.get_default_object(gm.generated_class()).set_editor_property('player_controller_class',pc.generated_class())
for bp in (gm,pc):compile_bp(bp);assert ue.EditorAssetLibrary.save_loaded_asset(bp,False)
for a in (mapping,action):assert ue.EditorAssetLibrary.save_loaded_asset(a,False)
level=ue.get_editor_subsystem(ue.LevelEditorSubsystem);path=TEST+'L_Site02'
if not ue.EditorAssetLibrary.does_asset_exist(path):
 assert level.new_level(path)
 world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();world.get_world_settings().set_editor_property('default_game_mode',gm.generated_class());actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
 floor=actors.spawn_actor_from_class(ue.StaticMeshActor,ue.Vector(600,0,-25));floor.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(ue.Vector(40,40,0.5))
 light=actors.spawn_actor_from_class(ue.DirectionalLight,ue.Vector(0,0,500));light.set_actor_rotation(ue.Rotator(pitch=-50,yaw=-20),False);light.get_component_by_class(ue.DirectionalLightComponent).set_mobility(ue.ComponentMobility.MOVABLE)
 for y in (-600,-200,200,600):actors.spawn_actor_from_class(ue.PlayerStart,ue.Vector(0,y,100))
 coord=actors.spawn_actor_from_class(ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator').generated_class(),ue.Vector(0,0,300));coord.set_actor_label('RunCoordinator')
 for i in range(2):
  exit=actors.spawn_actor_from_class(ue.load_asset('/Game/Puzzles/BP_MapExit').generated_class(),ue.Vector(1200,0,200));exit.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(350,350,300));exit.set_actor_label('RunExit'+str(i))
 assert level.save_current_level()
for bp in [ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator'),ue.load_asset('/Game/Puzzles/BP_MapExit')]:compile_bp(bp);assert ue.EditorAssetLibrary.save_loaded_asset(bp,False)
(HERE/'fixture-build.json').write_text(json.dumps({'passed':True,'fixture_only':True,'no_travel':True,'map':path,'graphs':{b.get_path_name():{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(b)} for b in (gm,pc)}},indent=2))
