"""Core six-round owning input/RPC integration. Run declarations, configure RPC flags
(and Forward float pin) in Slate, then rerun with ARGS['axis_ready']=True.
No runtime editor Python; every generated gameplay hook is Blueprint.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round'))
from authoring import *
guard();c=ue.load_asset('/Game/Core/BP_CoopCharacter');pc=ue.load_asset('/Game/Core/BP_CoopPlayerController')
ARGS=globals().get('ARGS',{})
for name,path in [('Traversal','/Game/Player/AC_Traversal'),('Tools','/Game/Player/Tools/AC_Tools')]:
 comp,_=component(c,name,ue.load_asset(path).generated_class());comp.set_is_replicated(True)
var(c,'SixInputReady','bool',False);var(c,'SixInputController',ue.PlayerController.static_class())
BP.set_variable_replication(c,'bTakenProtected',ue.BlueprintVariableReplication.REP_NOTIFY)
fn(c,'OnRep_bTakenProtected');fn(c,'ApplyTakingProtection');fn(c,'CanAcceptSixInput',outputs=[('Allowed','bool')])
for name in ('SetupSixInput','RemoveSixInput','RequestFlare','RequestClimb','RequestStopClimb','FlareOnServer','ClimbOnServer','StopClimbOnServer'):fn(c,name)
fn(c,'ClimbForwardOnServer',[('Forward','float')]);fn(c,'RequestClimbForward',[('Forward','float')]);fn(c,'RequestClimbAxis',[('Axis','Vector2D')])
for name in ('Server_ThrowFlare','Server_Climb','Server_StopClimb','Server_SetClimbForward'):BP.add_event(c,name)
compile_bp(c)
assets=ue.AssetToolsHelpers.get_asset_tools();folder='/Game/Core/Input';definitions={'IA_Sprint':['LeftShift','Gamepad_LeftThumbstick'],'IA_ThrowFlare':['Q','Gamepad_RightShoulder'],'IA_Climb':['T','Gamepad_FaceButton_Top']}
context=ue.load_asset(folder+'/IMC_SixRound') or assets.create_asset('IMC_SixRound',folder,ue.InputMappingContext,ue.InputMappingContext_Factory())
for name,keys in definitions.items():
 action=ue.load_asset(folder+'/'+name) or assets.create_asset(name,folder,ue.InputAction,ue.InputAction_Factory());action.set_editor_property('value_type',ue.InputActionValueType.BOOLEAN);action.set_editor_property('consume_input',True)
 for key_name in keys:
  key=ue.Key();key.set_editor_property('key_name',ue.Name(key_name))
  if not any(m.action==action and m.key==key for m in context.default_key_mappings.mappings):context.map_key(action,key)
 assert ue.EditorAssetLibrary.save_loaded_asset(action,False)
assert ue.EditorAssetLibrary.save_loaded_asset(context,False)
# Remove the retired brace key, so Shift produces one sprint request.
run=ue.load_asset(folder+'/IMC_RunControls');brace=ue.load_asset(folder+'/IA_Brace')
if run and brace:run.unmap_all_keys_from_action(brace);assert ue.EditorAssetLibrary.save_loaded_asset(run,False)
HEALTH='/Game/Hazards/AC_Health.AC_Health_C';TRAV='/Game/Player/AC_Traversal.AC_Traversal_C';TOOLS='/Game/Player/Tools/AC_Tools.AC_Tools_C'
write(c,'CanAcceptSixInput',f'''
 (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :ComponentClass "{HEALTH}"))
  (:then (bind dead (Class|ACHealth|IsDead :self health)) (return (and (not dead) (not {V('TakenProtected')})))) (:CastFailed (return false)))''')
write(c,'SetupSixInput',f'''
 (if (and (Pawn|IsLocallyControlled) (not {V('SixInputReady')}))
  (bind controller (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController))
   (:then (bind subsystem (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController controller))
    (Utilities|IsValid :InputObject subsystem (:"Is Valid"
     (Input|AddMappingContext :self subsystem :MappingContext "/Game/Core/Input/IMC_SixRound.IMC_SixRound" :Priority 3)
     {S('SixInputController','controller')} {S('SixInputReady','true')}) (:"Is Not Valid"))) (:CastFailed)))''')
fn(c,'RemoveSixMapping')
write(c,'RemoveSixMapping',f'''
  (Utilities|IsValid :InputObject {V('SixInputController')} (:"Is Valid"
   (bind subsystem (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController {V('SixInputController')}))
   (Utilities|IsValid :InputObject subsystem (:"Is Valid" (Input|RemoveMappingContext :self subsystem :MappingContext "/Game/Core/Input/IMC_SixRound.IMC_SixRound")) (:"Is Not Valid"))) (:"Is Not Valid"))''')
write(c,'RemoveSixInput',f'(if {V("SixInputReady")} (CallFunction|RemoveSixMapping) {S("SixInputReady","false")} {S("SixInputController",chr(34)+"None"+chr(34))})')
fn(c,'RefreshSixInput');write(c,'RefreshSixInput','(CallFunction|RemoveSixInput) (CallFunction|SetupSixInput)')
write(c,'ApplyTakingProtection',f'''
 (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :ComponentClass "{HEALTH}"))
  (:then (bind dead (Class|ACHealth|IsDead :self health))
   (if (or dead {V('TakenProtected')})
    (Pawn|Components|CharacterMovement|DisableMovement :self (Class|Character|GetCharacterMovement))
    (else (Pawn|Components|CharacterMovement|SetMovementMode :self (Class|Character|GetCharacterMovement) :NewMovementMode "MOVE_Walking")))
   (if (Networking|HasAuthority) (CallFunction|SetInteractionBlocked :Blocked (or dead {V('TakenProtected')})))) (:CastFailed))''')
write(c,'OnRep_bTakenProtected','(CallFunction|ApplyTakingProtection)')
write(c,'SetTakingProtected',f'''
 (if (Networking|HasAuthority)
  {S('TakenProtected','Protected')}
  (if Protected (CallFunction|CancelUse) (CallFunction|DropFromServer))
  (CallFunction|ApplyTakingProtection))''','Protected')
write(c,'SetInteractionBlocked',f'''
 (if (Networking|HasAuthority)
  (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :ComponentClass "{HEALTH}"))
   (:then {S('InteractionBlocked',f'(or Blocked (or {V("TakenProtected")} (Class|ACHealth|IsDead :self health)))')}
    (if {V('InteractionBlocked')} (CallFunction|CancelUse))) (:CastFailed)))''','Blocked')
# Existing reliable RPCs are reused, and their original custom events keep their flags.
for handler,method in [('BraceOnServer','SprintOnServer'),('UnbraceOnServer','StopSprintOnServer'),('BoostOnServer','MantleOnServer'),('ClimbOnServer','ClimbOnServer'),('StopClimbOnServer','StopClimbOnServer')]:
 write(c,handler,f'(if (Networking|HasAuthority) (bind traversal (Utilities|Casting|CastToAC_Traversal :Object (Components|GetComponentbyClass :ComponentClass "{TRAV}")) (:then (Class|ACTraversal|{method} :self traversal)) (:CastFailed)))')
write(c,'FlareOnServer',f'(if (and (Networking|HasAuthority) (not {V("TakenProtected")})) (bind tools (Utilities|Casting|CastToAC_Tools :Object (Components|GetComponentbyClass :ComponentClass "{TOOLS}")) (:then (Class|ACTools|ThrowFlareOnServer :self tools)) (:CastFailed)))')
write(c,'ClimbForwardOnServer',f'(if (Networking|HasAuthority) (bind traversal (Utilities|Casting|CastToAC_Traversal :Object (Components|GetComponentbyClass :ComponentClass "{TRAV}")) (:then (Class|ACTraversal|SetClimbForwardOnServer :self traversal :Forward Forward)) (:CastFailed)))','Forward')
for name,rpc,allow in [('RequestBraceStart','ServerBraceStart',True),('RequestBraceStop','ServerBraceStop',False),('RequestBoost','ServerRequestBoost',True),('RequestFlare','ServerThrowFlare',True),('RequestClimb','ServerClimb',True),('RequestStopClimb','ServerStopClimb',False)]:
 write(c,name,f'(if (Pawn|IsLocallyControlled) '+('(bind allowed (CallFunction|CanAcceptSixInput)) (if allowed ' if allow else '')+f'(CallFunction|{rpc})'+(')' if allow else '')+')')
write(c,'RequestJump','(if (Pawn|IsLocallyControlled) (bind allowed (CallFunction|CanAcceptSixInput)) (if allowed (CallFunction|RequestBoost) (CallFunction|RequestStopClimb) (Pawn|Character|Jump)))')
write(c,'PressInteract',f'''
 (if (Pawn|IsLocallyControlled)
  (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :ComponentClass "{HEALTH}"))
   (:then (if (Class|ACHealth|IsDead :self health)
    (bind view (Utilities|Casting|CastToAC_PlayerView :Object (Components|GetComponentbyClass :ComponentClass "/Game/Player/AC_PlayerView.AC_PlayerView_C"))
     (:then (Class|ACPlayerView|CycleSpectator :self view)) (:CastFailed))
    (else (if (not {V('TakenProtected')})
     {S('InputHeld','true')} {S('LocalUseTarget',V('FocusedTarget'))}
     (CallFunction|ServerInteractBegin :Target {V('FocusedTarget')}))))) (:CastFailed)))''')
# Replace only specific RPC execution links; preserve unrelated event chains.
def exclusive_rpc(name,handler,params=()):
 node=BP.add_event(c,name)
 for pin in list(node.find_then_pin().list_connected_pins()):node.find_then_pin().break_single_pin_link(pin)
 event(c,name,handler,params)
for rpc,handler in [('Server_BraceStart','BraceOnServer'),('Server_BraceStop','UnbraceOnServer'),('Server_RequestBoost','BoostOnServer'),('Server_ThrowFlare','FlareOnServer'),('Server_Climb','ClimbOnServer'),('Server_StopClimb','StopClimbOnServer')]:exclusive_rpc(rpc,handler)
# Axis RPC is declared here; primary adds Forward:float input before the axis-ready stage.
axis_node=BP.add_event(c,'Server_SetClimbForward')
if ARGS.get('axis_ready'):
 assert axis_node.find_output_pin('Forward'),'Primary must add Forward float event input first'
 exclusive_rpc('Server_SetClimbForward','ClimbForwardOnServer',['Forward'])
 write(c,'RequestClimbForward','(if (Pawn|IsLocallyControlled) (CallFunction|ServerSetClimbForward :Forward Forward))','Forward')
 write(c,'RequestClimbAxis','(bind (x y) (Math|Vector2D|BreakVector2D :InVec Axis)) (CallFunction|RequestClimbForward :Forward y)','Axis')
else:
 write(c,'RequestClimbForward','','Forward');write(c,'RequestClimbAxis','','Axis')
def bind_action(name,outputs):
 graph=BP.get_graph(c,'EventGraph');matches=[n for n in BP.find_nodes(graph) if BP._get_node_info(n).type_id.rsplit('|',1)[-1] in (name,'EnhancedInputAction'+name)]
 node=matches[0] if matches else BP.create_node(graph,'Input|EnhancedActionEvents|'+name,ue.IntPoint(100,6800))
 for output,handler in outputs.items():
  pin=node.find_output_pin(output)
  for target in list(pin.list_connected_pins()):pin.break_single_pin_link(target)
  call=BP.create_node(graph,'CallFunction|'+handler,ue.IntPoint(600,6800),declaring_class=c.generated_class());assert pin.try_create_connection(call.find_execute_pin())
 return node
bind_action('IA_Sprint',{'Started':'RequestBraceStart','Completed':'RequestBraceStop','Canceled':'RequestBraceStop'})
# The secondary keyboard bridge now injects IA_Sprint directly.
bind_action('IA_ThrowFlare',{'Started':'RequestFlare'})
bind_action('IA_Climb',{'Started':'RequestClimb','Completed':'RequestStopClimb','Canceled':'RequestStopClimb'})
if ARGS.get('axis_ready'):
 # Keep the inherited template movement binding; this is a second observing handler.
 graph=BP.get_graph(c,'EventGraph')
 matches=[n for n in BP.find_nodes(graph) if BP._get_node_info(n).type_id.rsplit('|',1)[-1] in ('IA_Move','EnhancedInputActionIA_Move')]
 move=matches[0] if matches else BP.create_node(graph,'Input|EnhancedActionEvents|IA_Move',ue.IntPoint(100,7600))
 # Enhanced action nodes do not expose a parent-override property in UE5.8.
 # The template movement handler lives in the parent; this class observes its own event.
 for output in ('Triggered','Completed','Canceled'):
  execute=move.find_output_pin(output)
  if any('RequestClimbAxis' in BP._get_node_info(p.get_owning_node()).type_id for p in execute.list_connected_pins()):continue
  call=BP.create_node(graph,'CallFunction|RequestClimbAxis',ue.IntPoint(600,7600),declaring_class=c.generated_class())
  existing=list(execute.list_connected_pins())
  if existing:
   sequence=BP.create_node(graph,'Utilities|FlowControl|Sequence',ue.IntPoint(350,7600))
   for link in existing:execute.break_single_pin_link(link)
   assert execute.try_create_connection(sequence.find_execute_pin())
   assert sequence.find_output_pin('Then_0').try_create_connection(existing[0])
   assert sequence.find_output_pin('Then_1').try_create_connection(call.find_execute_pin())
  else:assert execute.try_create_connection(call.find_execute_pin())
  value=move.find_output_pin('ActionValue')
  assert value,'Inspect EnhancedAction IA_Move output: ActionValue Vector2D expected'
  assert value.try_create_connection(call.find_input_pin('Axis'))
if ARGS.get('axis_ready'):
 import movement_input,importlib
 importlib.reload(movement_input);movement_input.install(c)
# Append per-local setup/removal without changing existing possession, HUD or controller chains.
event(c,'ReceiveBeginPlay','SetupSixInput');event(c,'ReceiveControllerChanged','RefreshSixInput');event(c,'ReceiveEndPlay','RemoveSixInput')
compile_bp(c);save(c)
RESULT={'new_rpcs_require_server_reliable':['Server_ThrowFlare','Server_Climb','Server_StopClimb','Server_SetClimbForward'], 'event_parameter_ui':{'Server_SetClimbForward':{'Forward':'float'}},'axis_ready':bool(ARGS.get('axis_ready')),'headlamp_keyboard':'F unchanged; climb T','secondary_keyboard_contract':'Existing RightShift IA_P2Brace injects IA_Brace→sprint. Flare RightAlt and climb P require controller extension; gamepad second owner uses own IMC_SixRound immediately.','writes':['Core/BP_CoopCharacter','Core/Input/IA_Sprint','Core/Input/IA_ThrowFlare','Core/Input/IA_Climb','Core/Input/IMC_SixRound','Core/Input/IMC_RunControls'],'runtime_acceptance_pending':True}
