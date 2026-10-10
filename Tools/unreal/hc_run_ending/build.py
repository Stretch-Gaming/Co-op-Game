"""Owned HC7/HC8 Blueprint authoring. Core hooks remain explicit integration boundaries."""
import json, pathlib, unreal as ue, toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).resolve().parent
assert pathlib.Path(ue.Paths.project_dir()).resolve()==ROOT
assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-58210709')
assert not ue.EditorLevelLibrary.get_pie_worlds(True)

def owned(bp):
 p=bp.get_path_name().split('.')[0];assert p=='/Game/Puzzles/BP_MapExit' or p.startswith(('/Game/Puzzles/Run/','/Game/Puzzles/UI/Results/','/Game/Puzzles/Test/HC_RunEnding/')),p

def compile_bp(bp):
 owned(bp)
 with toolset_registry.tool_raising_exceptions():BP.compile_blueprint(bp,warnings_as_errors=True)
 assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE,bp.get_path_name()

def fn(bp,n,inputs=(),outputs=()):
 owned(bp);g=BP.add_function_graph(bp,n)
 for isinput,ps in [(True,inputs),(False,outputs)]:
  for p,t in ps:
   if not BP._param_name_exists(g,p,isinput):
    if isinstance(t,str):BP.add_function_param(g,p,t,isinput)
    else:BP.add_object_function_param(g,p,t,isinput)
 return g

def write(bp,n,text):
 owned(bp);g=BP.get_graph(bp,n)
 with toolset_registry.tool_raising_exceptions():
  for node in BP.find_nodes(g):
   if node.get_class().get_name() not in ('K2Node_FunctionEntry','K2Node_FunctionResult'):BP.delete_node(node)
  blueprint_dsl.Transpiler(g,BP.create_node,BP.connect_pins,BP._get_node_info,BP.set_pin_value,lambda gr:BP.find_nodes(gr),delete_node_fn=BP.delete_node,find_node_types_fn=lambda f:BP.find_node_types(g,f)).transpile(text)
 compile_bp(bp)

def event(bp,n,handler):
 g=BP.get_graph(bp,'EventGraph');e=BP.add_event(bp,n);output=e.find_then_pin()
 links=list(output.list_connected_pins())
 if links:
  assert len(links)==1
  linked=links[0].get_owning_node();typ=BP._get_node_info(linked).type_id
  if handler in typ:return
  assert 'Parent:' in typ,typ
  output=linked.find_then_pin();links=list(output.list_connected_pins())
  if links:
   assert len(links)==1 and handler in BP._get_node_info(links[0].get_owning_node()).type_id
   return
 call=BP.create_node(g,'CallFunction|'+handler,ue.IntPoint(400,0));assert output.try_create_connection(call.find_execute_pin())
co=ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator');
if 'ResultsActive' not in BP.list_variables(co):BP.add_variable(co,'ResultsActive','bool');BP.set_variable_replication(co,'ResultsActive',ue.BlueprintVariableReplication.REPLICATED)
ex=ue.load_asset('/Game/Puzzles/BP_MapExit');ac=ue.load_asset('/Game/Puzzles/UI/Results/AC_RunResults')
fn(co,'IsSingleton',outputs=[('Ready','bool')])
write(co,'IsSingleton','''(fn IsSingleton () (bind actors (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/Run/BP_RunCoordinator.BP_RunCoordinator_C")) (return (== (Utilities|Array|Length :TargetArray actors) 1)))''')
for n in ('CaptureSnapshot','TryCommitExtraction','RestoreResults'):fn(co,n,outputs=[('Accepted','bool')])
fn(co,'RequestRestart',[('RequestingController',ue.PlayerController.static_class())],[('Accepted','bool')])
for n in ('ResolveCoordinator',):fn(ex,n,outputs=[('Coordinator',co.generated_class())])
fn(ex,'IsRosterPawnInside',[('State',ue.PlayerState.static_class())],[('Ready','bool')])
for n in ('ReevaluateExit','StartExit','StopExit'):fn(ex,n)
for n in ('RefreshResults','ClearResults','StartResults','StopResults','RequestLocalRestart'):fn(ac,n)
for bp in (co,ex,ac):compile_bp(bp)
write(co,'CaptureSnapshot','''(fn CaptureSnapshot ()
 (if (and (and (Networking|HasAuthority) (CallFunction|IsSingleton)) (not (Variables|Default|GetSnapshotCommitted)))
  (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
   (:then (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
    (:then (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
     (:then
      (Variables|Default|SetSnapshotCommitted true)
      (Variables|Default|SetCapturedCollected (Class|BPCoopGameState|GetRelicsCollected :self gs))
      (Variables|Default|SetCapturedAvailable (Class|BPCoopGameState|GetRelicsAvailable :self gs))
      (Class|BPCoopGameInstance|SetRelicsCollected :self gi :RelicsCollected (Variables|Default|GetCapturedCollected))
      (Class|BPCoopGameInstance|SetRelicsAvailable :self gi :RelicsAvailable (Variables|Default|GetCapturedAvailable))
      (return true)) (:CastFailed (return false)))) (:CastFailed (return false)))) (:CastFailed (return false)))
  (else (return false))))''')
write(co,'TryCommitExtraction','''(fn TryCommitExtraction ()
 (if (CallFunction|CaptureSnapshot)
  (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
   (:then (Variables|Default|SetCompletionCount (+ (Variables|Default|GetCompletionCount) 1))
    (Class|BPCoopGameMode|CompleteMap :self gm) (return true)) (:CastFailed (return false)))
  (else (return false))))''')
write(co,'RestoreResults','''(fn RestoreResults ()
 (if (and (and (and (Networking|HasAuthority) (CallFunction|IsSingleton)) (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site02")) (not (Variables|Default|GetSnapshotCommitted)))
  (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
   (:then (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
    (:then (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
     (:then
      (Variables|Default|SetCapturedCollected (Class|BPCoopGameInstance|GetRelicsCollected :self gi))
      (Variables|Default|SetCapturedAvailable (Class|BPCoopGameInstance|GetRelicsAvailable :self gi))
      (Class|BPCoopGameState|SetRelicsCollected :self gs :RelicsCollected (Variables|Default|GetCapturedCollected))
      (Class|BPCoopGameState|SetRelicsAvailable :self gs :RelicsAvailable (Variables|Default|GetCapturedAvailable))
      (Variables|Default|SetSnapshotCommitted true)
      (Variables|Default|SetResultsActive true)
      (Class|BPCoopGameMode|SetRoundPhase :self gm :Phase "NewEnumerator4") (return true))
     (:CastFailed (return false)))) (:CastFailed (return false)))) (:CastFailed (return false)))
  (else (return false))))''')
write(co,'RequestRestart','''(fn RequestRestart (RequestingController)
 (if (and (and (Networking|HasAuthority) (CallFunction|IsSingleton)) (and (and (Variables|Default|GetSnapshotCommitted) (Variables|Default|GetResultsActive)) (not (Variables|Default|GetRestartInProgress))))
  (Utilities|IsValid :InputObject RequestingController
   (:"Is Valid"
    (if (and (Pawn|IsLocalController :self RequestingController) (Game|Player|IsPrimaryPlayer :self RequestingController))
     (if (Utilities|Array|ContainsItem :TargetArray (Actor|GetAllActorsOfClass :ActorClass "/Script/Engine.PlayerController") :ItemToFind RequestingController)
      (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
       (:then (if (Utilities|Array|ContainsItem :TargetArray (Class|GameStateBase|GetPlayerArray :self gs) :ItemToFind (Class|Controller|GetPlayerState :self RequestingController))
        (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
         (:then (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
          (:then (Variables|Default|SetRestartInProgress true)
           (Class|BPCoopGameInstance|SetRelicsCollected :self gi :RelicsCollected 0)
           (Class|BPCoopGameInstance|SetRelicsAvailable :self gi :RelicsAvailable 0)
           (Class|BPCoopGameMode|CompleteMap :self gm) (return true)) (:CastFailed (return false)))) (:CastFailed (return false)))
        (else (return false)))) (:CastFailed (return false)))
      (else (return false))) (else (return false))))
   (:"Is Not Valid" (return false))) (else (return false))))''')
write(ex,'ResolveCoordinator','''(fn ResolveCoordinator ()
 (bind actors (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/Run/BP_RunCoordinator.BP_RunCoordinator_C"))
 (if (== (Utilities|Array|Length :TargetArray actors) 1) (for actor actors
  (bind coordinator (Utilities|Casting|CastToBP_RunCoordinator :Object actor)
   (:then (return coordinator)) (:CastFailed))))
 (return "None"))''')
write(ex,'IsRosterPawnInside','''(fn IsRosterPawnInside (State)
 (Utilities|IsValid :InputObject State
  (:"Is Valid"
   (bind pawn (PlayerState|GetPawn :self State))
   (Utilities|IsValid :InputObject pawn
    (:"Is Valid"
     (bind pc (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController :self pawn))
      (:then
       (if (and (== (Class|Controller|GetPlayerState :self pc) State) (== (Class|Pawn|GetPlayerState :self pawn) State))
        (bind box (Utilities|Casting|CastToBoxComponent :Object (Variables|TriggerBase|GetCollisionComponent))
         (:then (return (Math|Geometry|IsPointinBoxwithTransform :Point (Transformation|GetActorLocation :self pawn) :BoxWorldTransform (Transformation|GetWorldTransform :self box) :BoxExtent (Components|Box|GetUnscaledBoxExtent :self box))))
         (:CastFailed (return false))) (else (return false)))) (:CastFailed (return false))))
    (:"Is Not Valid" (return false)))) (:"Is Not Valid" (return false))))''')
write(ex,'ReevaluateExit','''(fn ReevaluateExit ()
 (if (and (Networking|HasAuthority) (not (Variables|Default|GetExitCommitted)))
  (Variables|Default|SetRequiredPlayers 0) (Variables|Default|SetReadyPlayers 0)
  (Utilities|Array|Clear :TargetArray (Variables|Default|GetSeenStates))
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (for state (Class|GameStateBase|GetPlayerArray :self gs)
     (if (not (Utilities|Array|ContainsItem :TargetArray (Variables|Default|GetSeenStates) :ItemToFind state))
      (Utilities|Array|AddUnique :TargetArray (Variables|Default|GetSeenStates) :NewItem state)
      (Variables|Default|SetRequiredPlayers (+ (Variables|Default|GetRequiredPlayers) 1))
      (if (CallFunction|IsRosterPawnInside :State state) (Variables|Default|SetReadyPlayers (+ (Variables|Default|GetReadyPlayers) 1)))))
    (Variables|Default|SetAllReady (and (> (Variables|Default|GetRequiredPlayers) 0) (== (Variables|Default|GetRequiredPlayers) (Variables|Default|GetReadyPlayers))))
    (if (Variables|Default|GetAllReady)
     (bind coordinator (CallFunction|ResolveCoordinator))
     (Utilities|IsValid :InputObject coordinator
      (:"Is Valid" (Variables|Default|SetExitCommitted true)
       (if (not (Class|BPRunCoordinator|TryCommitExtraction :self coordinator)) (Variables|Default|SetExitCommitted false))) (:"Is Not Valid"))))
   (:CastFailed (Variables|Default|SetAllReady false)))))''')
write(ex,'StartExit','''(fn StartExit () (if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ReevaluateExit" :Time 0.2 :bLooping true)))''')
write(ex,'StopExit','''(fn StopExit () (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "ReevaluateExit"))''')
event(ex,'ReceiveBeginPlay','StartExit');event(ex,'ReceiveEndPlay','StopExit')
for bp in (co,ex):compile_bp(bp);assert ue.EditorAssetLibrary.save_loaded_asset(bp,False)
(HERE/'build-exit.json').write_text(json.dumps({'passed':True,'assets':{bp.get_path_name():{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)} for bp in (co,ex)}},indent=2))
