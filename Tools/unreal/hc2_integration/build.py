"""HC-2 editor authoring; preserves HC-1 interaction and shared signatures.
Execute through editor_loop.py in this checkout with Core files LFS-locked.
"""
import json
from pathlib import Path
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
CORE='/Game/Core/'
I='Index_11_91104438409472A6DD374BADC8DC29B1'
P='Phase_15_0B3D934F45B47D0BD2F25CA01264D4DF'
A='Attempt_12_246832B34F4E147660E8729696BDD44A'
T='PhaseEndsAt_13_75E3D82F49994607AFA23C8B57E08350'
R='ScalingRow_14_43C74C304230A92B6620E1A520A230C0'

def load(name):
 a=ue.load_asset(CORE+name);assert a,name;return a

def compile_bp(bp):
 BP.compile_blueprint(bp)
 assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE,bp.get_path_name()

def var(bp,name,kind):
 if name not in BP.list_variables(bp):
  if isinstance(kind,str):BP.add_variable(bp,name,kind)
  else:BP.add_object_variable(bp,name,kind)

def fn(bp,name,inputs=(),outputs=()):
 g=BP.add_function_graph(bp,name)
 existing={p.name for n in BP.get_node_infos(BP.find_nodes(g,entry_points_only=True)) for p in n.output_pins}
 for p,k in inputs:
  if p not in existing:
   if isinstance(k,str):BP.add_function_param(g,p,k,True)
   else:BP.add_object_function_param(g,p,k,True)
 existing_outputs={pin.name for node in BP.find_nodes(g) if isinstance(node,ue.K2Node_FunctionResult) for pin in BP._get_node_info(node).input_pins}
 for p,k in outputs:
  if p not in existing_outputs:BP.add_function_param(g,p,k,False)
 return g

def write(bp,name,text):
 g=BP.get_graph(bp,name)
 with toolset_registry.tool_raising_exceptions():
  blueprint_dsl.Transpiler(g,BP.create_node,BP.connect_pins,BP._get_node_info,BP.set_pin_value,lambda x:BP.find_nodes(x),delete_node_fn=BP.delete_node,find_node_types_fn=lambda f:BP.find_node_types(g,f)).transpile(text)
 compile_bp(bp)

def wire(bp,event,handler,param=None):
 e=BP.add_event(bp,event)
 then=e.find_then_pin()
 links=list(then.list_connected_pins())
 if links:
  assert len(links)==1 and handler in BP._get_node_info(links[0].get_owning_node()).type_id,event
  return
 call=BP.create_node(BP.get_graph(bp,'EventGraph'),'CallFunction|'+handler,ue.IntPoint(450,1200))
 assert then.try_create_connection(call.find_execute_pin())
 if param:assert e.find_output_pin(param).try_create_connection(call.find_input_pin(param))

def start():
 assert Path(ue.Paths.project_dir()).resolve()==ROOT
 assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-')
 gm,gs,ps=load('BP_CoopGameMode'),load('BP_CoopGameState'),load('BP_CoopPlayerState')
 for n in ('RelicsCollected','RelicsAvailable'):BP.set_variable_replication(gs,n,ue.BlueprintVariableReplication.REPLICATED)
 BP.set_variable_replication(ps,'ColorSlot',ue.BlueprintVariableReplication.REPLICATED)
 compile_bp(ps)
 ue.get_default_object(ps.generated_class()).set_editor_property('ColorSlot',-1)
 for name in ('Slot0Used','Slot1Used','Slot2Used','Slot3Used'):var(gm,name,'bool')
 var(gm,'AvailableValue','int')
 fn(gm,'ScalingRowForRoster',outputs=[('Row','name')])
 fn(gm,'AllocateColor',[('JoiningState',ue.PlayerState.static_class())])
 for n in ('RefreshLobby','RefreshRelicTotals','HC2BeginPlay'):fn(gm,n)
 relic=ue.load_asset('/Game/Puzzles/BP_Relic')
 if not relic:
  relic=BP.create('/Game/Puzzles','BP_Relic',ue.StaticMeshActor.static_class())
  # BPI_Interactable is added through Class Settings before scaffold execution.
 assert {'CanInteract','GetInteractInfo'}.issubset({str(f.name) for f in BP.list_functions(relic)}),'Add BPI_Interactable in Class Settings before scaffold execution'
 for name,kind in [('Value','int'),('MinPlayers','int'),('Collected','bool'),('Available','bool'),('PickupFeedbackCount','int')]:var(relic,name,kind)
 var(relic,'PickupSound',ue.SoundBase.static_class())
 for name in ('Value','MinPlayers','PickupSound'):BP.set_variable_instance_editable(relic,name,True)
 for name in ('Collected','Available'):BP.set_variable_replication(relic,name,ue.BlueprintVariableReplication.REP_NOTIFY)
 for name in ('RefreshAvailability','ApplyVisuals','PlayPickupSound','HC2RelicBeginPlay'):fn(relic,name)
 fn(relic,'Collect',[('Instigator',ue.Actor.static_class())])
 for n in ('Interact','Multicast_Pickup'):BP.add_event(relic,n)
 compile_bp(relic)
 (HERE/'scaffold.json').write_text(json.dumps({'passed':True,'relic':relic.get_path_name()}))

def logic():
 gm,gs,ps=load('BP_CoopGameMode'),load('BP_CoopGameState'),load('BP_CoopPlayerState')
 relic=ue.load_asset('/Game/Puzzles/BP_Relic')
 write(gm,'ScalingRowForRoster','''(fn ScalingRowForRoster ()
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
    (:then (bind count (Class|BPCoopGameState|GetPlayerCount :self gs))
      (return (Utilities|String|StringToName :InString (select (>= count 4) "4" (select (>= count 3) "3" "2")))))
    (:CastFailed (return "2"))))''')
 slots='\n'.join(f'(Variables|Default|SetSlot{i}Used false)' for i in range(4))
 marks='\n'.join(f'(if (== slot {i}) (Variables|Default|SetSlot{i}Used true))' for i in range(4))
 select='(select (not (Variables|Default|GetSlot0Used)) 0 (select (not (Variables|Default|GetSlot1Used)) 1 (select (not (Variables|Default|GetSlot2Used)) 2 (select (not (Variables|Default|GetSlot3Used)) 3 -1))))'
 write(gm,'AllocateColor',f'''(fn AllocateColor (JoiningState)
  (if (Networking|HasAuthority)
    (bind joining (Utilities|Casting|CastToBP_CoopPlayerState :Object JoiningState)
      (:then {slots}
        (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
          (:then
            (for other (Class|GameStateBase|GetPlayerArray :self gs)
              (if (!= other JoiningState)
                (bind state (Utilities|Casting|CastToBP_CoopPlayerState :Object other)
                  (:then (bind slot (Class|BPCoopPlayerState|GetColorSlot :self state)) {marks}) (:CastFailed))))
            (Class|BPCoopPlayerState|SetColorSlot :self joining :ColorSlot {select})) (:CastFailed))) (:CastFailed))))''')
 write(gm,'RefreshLobby',f'''(fn RefreshLobby ()
  (if (Networking|HasAuthority)
    (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
      (:then
        (for item (Class|GameStateBase|GetPlayerArray :self gs)
          (bind state (Utilities|Casting|CastToBP_CoopPlayerState :Object item)
            (:then (if (< (Class|BPCoopPlayerState|GetColorSlot :self state) 0) (CallFunction|AllocateColor :JoiningState state))) (:CastFailed)))
        (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
        (bind nextRow (CallFunction|ScalingRowForRoster))
        (if (and (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator0")) (!= row nextRow))
          (Class|BPCoopGameState|SetRoundState :self gs :RoundState (Utilities|Struct|MakeSRoundState :{I} index :{P} phase :{A} attempt :{T} ends :{R} nextRow)))
        (CallFunction|RefreshRelicTotals)) (:CastFailed))))''')
 write(gm,'RefreshRelicTotals','''(fn RefreshRelicTotals ()
  (if (Networking|HasAuthority)
    (Variables|Default|SetAvailableValue 0)
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_Relic.BP_Relic_C")
      (bind relic (Utilities|Casting|CastToBP_Relic :Object item)
        (:then
          (Class|BPRelic|RefreshAvailability :self relic)
          (if (or (Class|BPRelic|GetAvailable :self relic) (Class|BPRelic|GetCollected :self relic))
            (Variables|Default|SetAvailableValue (+ (Variables|Default|GetAvailableValue) (Class|BPRelic|GetValue :self relic))))) (:CastFailed)))
    (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
      (:then (Class|BPCoopGameState|SetRelicsAvailable :self gs :RelicsAvailable (Variables|Default|GetAvailableValue))) (:CastFailed))))''')
 write(gm,'AddRelics','''(fn AddRelics (Count)
  (if (and (Networking|HasAuthority) (> Count 0))
    (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
      (:then (Class|BPCoopGameState|SetRelicsCollected :self gs :RelicsCollected (+ (Class|BPCoopGameState|GetRelicsCollected :self gs) Count))) (:CastFailed))))''')
 write(gm,'HC2BeginPlay','''(fn HC2BeginPlay ()
  (if (Networking|HasAuthority)
    (CallFunction|RefreshLobby)
    (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshLobby" :Time 0.2 :bLooping true)))''')
 wire(gm,'ReceiveBeginPlay','HC2BeginPlay')
 write(gm,'StartRound',f'''(fn StartRound (Index)
  (if (and (Networking|HasAuthority) (> Index 0))
    (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
      (:then
        (bind (oldIndex phase oldAttempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
        (CallFunction|CancelAllUses)
        (Class|BPCoopGameState|SetRoundState :self gs :RoundState (Utilities|Struct|MakeSRoundState :{I} Index :{P} (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1") :{A} (select (== Index oldIndex) (+ oldAttempt 1) 1) :{T} 0.0 :{R} (CallFunction|ScalingRowForRoster)))
        (CallFunction|RefreshRelicTotals)) (:CastFailed))))''')
 write(gm,'CompleteMap','''(fn CompleteMap ()
  (if (Networking|HasAuthority)
    (CallFunction|CancelAllUses)
    (CallFunction|SetRoundPhase :Phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator4"))
    (Development|ExecuteConsoleCommand :Command (select (Utilities|String|Contains :SearchIn (Game|GetCurrentLevelName :bRemovePrefixString true) :Substring "L_Site02") "ServerTravel /Game/Maps/L_Site01?listen" "ServerTravel /Game/Maps/L_Site02?listen"))))''')
 write(relic,'GetInteractInfo','''(fn GetInteractInfo (Instigator)
  (return "Collect relic" 0.0 (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator0")))''')
 write(relic,'CanInteract','''(fn CanInteract (Instigator)
  (Utilities|IsValid :InputObject Instigator (:"Is Valid" (return (and (Variables|Default|GetAvailable) (not (Variables|Default|GetCollected))))) (:"Is Not Valid" (return false))))''')
 write(relic,'ApplyVisuals','''(fn ApplyVisuals ()
  (bind visible (and (Variables|Default|GetAvailable) (not (Variables|Default|GetCollected))))
  (Rendering|SetActorHiddenInGame :bNewHidden (not visible))
  (Collision|SetActorEnableCollision :bNewActorEnableCollision visible))''')
 for name in ('Collected','Available'):
  write(relic,'OnRep_'+name,f'(fn OnRep_{name} () (CallFunction|ApplyVisuals))')
 write(relic,'RefreshAvailability','''(fn RefreshAvailability ()
  (if (Networking|HasAuthority)
    (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
      (:then
        (bind count (Utilities|String|StringToInteger :InString (Utilities|String|ToString(Name) (Class|BPCoopGameState|GetScalingRow :self gs))))
        (Variables|Default|SetAvailable (and (>= count (Variables|Default|GetMinPlayers)) (> (Variables|Default|GetValue) 0)))
        (CallFunction|ApplyVisuals)) (:CastFailed))))''')
 write(relic,'Collect','''(fn Collect (Instigator)
  (if (Networking|HasAuthority)
    (CallFunction|RefreshAvailability)
    (if (CallFunction|CanInteract :Instigator Instigator)
      (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object Instigator)
        (:then
          (if (Class|BPCoopCharacter|UseAllowed :self pawn :Target self)
            (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
              (:then
                (Variables|Default|SetCollected true)
                (CallFunction|ApplyVisuals)
                (Class|BPCoopGameMode|AddRelics :self gm :Count (Variables|Default|GetValue))
                (CallFunction|MulticastPickup)) (:CastFailed)))) (:CastFailed)))))''')
 write(relic,'PlayPickupSound',''''(fn PlayPickupSound ()
  (Utilities|IsValid :InputObject (Variables|Default|GetPickupSound)
    (:"Is Valid"
      (Audio|PlaySoundatLocation :Sound (Variables|Default|GetPickupSound) :Location (Transformation|GetActorLocation))
      (Variables|Default|SetPickupFeedbackCount (+ (Variables|Default|GetPickupFeedbackCount) 1)))
    (:"Is Not Valid")))''')
 write(relic,'HC2RelicBeginPlay','''(fn HC2RelicBeginPlay ()
  (CallFunction|ApplyVisuals)
  (if (Networking|HasAuthority) (CallFunction|RefreshAvailability)))''')
 wire(relic,'ReceiveBeginPlay','HC2RelicBeginPlay')
 wire(relic,'Interact','Collect','Instigator')
 wire(relic,'Multicast_Pickup','PlayPickupSound')
 cdo=ue.get_default_object(relic.generated_class())
 cdo.set_editor_property('replicates',True)
 cdo.set_editor_property('always_relevant',True)
 cdo.set_editor_property('Value',1);cdo.set_editor_property('MinPlayers',2)
 cdo.set_editor_property('PickupSound',ue.load_asset('/Game/Core/Audio/SFX_RelicPickup'))
 cdo.set_editor_property('Available',False);cdo.set_editor_property('Collected',False)
 cdo.static_mesh_component.set_static_mesh(ue.load_asset('/Game/Puzzles/Art/HCA1_Relics/SM_Relic_GoldIdol'))
 cdo.static_mesh_component.set_collision_profile_name('BlockAll')
 for bp in (gm,gs,ps,relic):
  compile_bp(bp);assert ue.EditorAssetLibrary.save_loaded_asset(bp)
 (HERE/'build.json').write_text(json.dumps({'passed':True,'saved':[b.get_path_name() for b in (gm,gs,ps,relic)]},indent=2))

if __name__=='__main__':
 if ARGS.get('stage')=='scaffold':start()
 else:logic()
