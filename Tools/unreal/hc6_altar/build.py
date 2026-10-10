import sys,pathlib,json,importlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import authoring;importlib.reload(authoring)
from authoring import *
guard();assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
bp=unreal.load_asset('/Game/Puzzles/BP_Altar');owned(bp)
with toolset_registry.tool_raising_exceptions():
 for n in BP.find_nodes(BP.get_graph(bp,'EventGraph')):BP.delete_node(n)
 for g in BP.list_graphs(bp):
  if g.get_name() not in ['UserConstructionScript','CanInteract','GetInteractInfo','EventGraph']:BP.remove_function_graph(bp,g.get_name())
 for n in list(BP.list_variables(bp)):BP.remove_variable(bp,n)
 for name in ['CanInteract','GetInteractInfo']:
  for n in BP.find_nodes(BP.get_graph(bp,name)):
   if n.get_class().get_name() not in ['K2Node_FunctionEntry','K2Node_FunctionResult']:BP.delete_node(n)
A=unreal.Actor.static_class()
for n,k,r in [('Completed','bool',True),('PlacedKey',A,True),('TransactionBusy','bool',False),('CandidateCharacter',A,False),('CandidateKey',A,False),('ClearCallCount','int',False),('AcceptCount','int',False),('ResetCount','int',False),('SocketName','name',False)]:var(bp,n,k,r)
for n,ins,outs in [('IsRoundActive',[],[('Active','bool')]),('CanAccept',[('Instigator',A)],[('Allowed','bool')]),('AcceptKey',[('Instigator',A)],[]),('ApplyAltarState',[],[]),('BeginAltar',[],[]),('ResetAltar',[('Index','int'),('Attempt','int')],[])]:fn(bp,n,ins,outs)
compile_bp(bp)
socket=component(bp,'AltarSocket',unreal.SceneComponent.static_class());socket.set_editor_property('relative_location',unreal.Vector(0,0,125.305));socket.set_mobility(unreal.ComponentMobility.MOVABLE)
mesh=BP.get_default_object(bp).static_mesh_component;mesh.set_static_mesh(unreal.load_asset('/Game/Puzzles/Art/HCA2_Props/SM_Altar'));mesh.set_editor_property('relative_scale3d',unreal.Vector(1,1,1));mesh.set_mobility(unreal.ComponentMobility.MOVABLE);mesh.set_simulate_physics(False);mesh.set_collision_profile_name('BlockAll');mesh.set_is_replicated(True)
defaults(bp,replicates=True,replicate_movement=True,always_relevant=True,Completed=False,TransactionBusy=False)
BP.set_variable_instance_editable(bp,'SocketName',True)
V=lambda n:f'(Variables|Default|Get{n})'
S=lambda n,v:f'(Variables|Default|Set{n} {v})'
write(bp,'IsRoundActive','''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then
   (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
   (return (and (== index 2) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")))))
  (:CastFailed (return false)))''')
write(bp,'CanAccept',f'''
 (bind active (CallFunction|IsRoundActive))
 (if (and (Networking|HasAuthority) (and (not {V('Completed')}) (and (not {V('TransactionBusy')}) active)))
  (Utilities|IsValid :InputObject Instigator (:"Is Valid"
   (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object Instigator) (:then
    (if (and (not (Actor|ActorHasTag :self pawn :Tag "Downed")) (<= (Transformation|GetDistanceTo :OtherActor pawn) 400.0))
     (bind carried (Class|BPCoopCharacter|GetCarried :self pawn))
     (Utilities|IsValid :InputObject carried (:"Is Valid"
     (bind key (Utilities|Casting|CastToBP_KeyRelic :Object carried) (:then
      (bind (state carrier) (Class|BPCarryable|GetCarryState :self key))
      (if (and (== state 1) (== carrier pawn))
       {S('CandidateCharacter','pawn')} {S('CandidateKey','key')} (return true)
       (else (return false)))) (:CastFailed (return false)))) (:"Is Not Valid" (return false)))
     (else (return false)))) (:CastFailed (return false)))) (:"Is Not Valid" (return false)))
  (else (return false)))''','Instigator')
write(bp,'CanInteract',f'''
 (Utilities|IsValid :InputObject Instigator (:"Is Valid"
  (if (Networking|HasAuthority) (bind allowed (CallFunction|CanAccept :Instigator Instigator)) (return allowed)
   (else (bind active (CallFunction|IsRoundActive)) (return (and (not {V('Completed')}) active))))) (:"Is Not Valid" (return false)))''','Instigator')
write(bp,'GetInteractInfo','(return "Place key relic" 0.0 (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator0"))','Instigator')
write(bp,'ApplyAltarState',f'(Rendering|SetRenderCustomDepth :self (Variables|StaticMeshActor|GetStaticMeshComponent) :bValue {V("Completed")})')
write(bp,'OnRep_Completed','(CallFunction|ApplyAltarState)');write(bp,'OnRep_PlacedKey','(CallFunction|ApplyAltarState)')
write(bp,'BeginAltar','(CallFunction|ApplyAltarState)')
write(bp,'AcceptKey',f'''
 (bind allowed (CallFunction|CanAccept :Instigator Instigator))
 (if allowed
  (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode)) (:then
   {S('TransactionBusy','true')}
   (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object {V('CandidateCharacter')}) (:then
    (bind released (Class|BPCoopCharacter|ReleaseCarried :self pawn))
    (if (== released {V('CandidateKey')})
     {S('PlacedKey','released')}
     (bind attached (Transformation|AttachActorToComponent :self released :Parent (Variables|Default|GetAltarSocket) :SocketName {V('SocketName')} :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false))
     (if attached
      {S('Completed','true')} {S('AcceptCount',f'(+ {V("AcceptCount")} 1)')}
      (CallFunction|ApplyAltarState) (Networking|ForceNetUpdate)
      {S('ClearCallCount',f'(+ {V("ClearCallCount")} 1)')}
      (Class|BPCoopGameMode|ClearRound :self gm)
      (else (Class|BPIRoundReset|ResetforRound(Message) :self released :Index 2 :Attempt 0) {S('PlacedKey','"None"')}))
     (else))
    {S('TransactionBusy','false')}) (:CastFailed {S('TransactionBusy','false')}))) (:CastFailed)))''','Instigator')
fn(bp,'ClearAltar')
write(bp,'ClearAltar',f'''
 {S('PlacedKey','"None"')} {S('CandidateKey','"None"')} {S('CandidateCharacter','"None"')} {S('Completed','false')}
 {S('ResetCount',f'(+ {V("ResetCount")} 1)')} {S('TransactionBusy','false')} (CallFunction|ApplyAltarState) (Networking|ForceNetUpdate)''')
write(bp,'ResetAltar',f'''
 (if (Networking|HasAuthority)
  {S('TransactionBusy','true')}
  (bind key (Utilities|Casting|CastToBP_KeyRelic :Object {V('PlacedKey')})
   (:then (Class|BPIRoundReset|ResetforRound(Message) :self key :Index Index :Attempt Attempt) (CallFunction|ClearAltar))
   (:CastFailed (CallFunction|ClearAltar))))''','Index Attempt')
event(bp,'ReceiveBeginPlay','BeginAltar')
g=BP.get_graph(bp,'EventGraph')
for event_name,handler,params in [('Interact','AcceptKey',['Instigator']),('ResetForRound','ResetAltar',['Index','Attempt'])]:
 e=BP.add_event(bp,event_name);call=BP.create_node(g,'CallFunction|'+handler,unreal.IntPoint(400,600))
 assert e.find_then_pin().try_create_connection(call.find_execute_pin())
 for p in params:assert e.find_output_pin(p).try_create_connection(call.find_input_pin(p))
save(bp)
RESULT={'authored':bp.get_path_name(),'functions':[g.get_name() for g in BP.list_graphs(bp)]}






