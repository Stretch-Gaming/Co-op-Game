import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
pc=ue.load_asset('/Game/Core/BP_CoopPlayerController');assets=ue.AssetToolsHelpers.get_asset_tools();folder='/Game/Core/Input';context=ue.load_asset(folder+'/IMC_RunControls')
keys={'Forward':['Up'],'Back':['Down'],'Left':['Left'],'Right':['Right'],'TurnLeft':['Comma'],'TurnRight':['Period'],'Jump':['Slash','RightControl'],'Brace':['RightShift'],'Use':['Enter'],'View':['C'],'Lamp':['H']}
for name,mappings in keys.items():
 full='IA_P2'+name;action=ue.load_asset(folder+'/'+full) or assets.create_asset(full,folder,ue.InputAction,ue.InputAction_Factory());action.set_editor_property('value_type',ue.InputActionValueType.BOOLEAN);action.set_editor_property('consume_input',False);assert ue.EditorAssetLibrary.save_loaded_asset(action,False)
 var(pc,'P2'+name,'bool',False)
 for key in mappings:
  typed=ue.Key();typed.set_editor_property('key_name',ue.Name(key))
  if not any(m.action==action and m.key==typed for m in context.mappings):context.map_key(action,typed)
 for state,value in [('On','true'),('Off','false')]:
  handler='Keyboard'+name+state;fn(pc,handler);write(pc,handler,f'(if (and (Pawn|IsLocalPlayerController) (Game|Player|IsPrimaryPlayer)) {S("P2"+name,value)})')
 graph=BP.get_graph(pc,'EventGraph');matches=[n for n in BP.find_nodes(graph) if BP._get_node_info(n).type_id in ('Input|EnhancedActionEvents|'+full,'Input|EnhancedActionEvents|EnhancedInputAction'+full)];node=matches[0] if matches else BP.create_node(graph,'Input|EnhancedActionEvents|'+full,ue.IntPoint(0,5500))
 for output,state in [('Started','On'),('Completed','Off'),('Canceled','Off')]:
  handler='Keyboard'+name+state;pin=node.find_output_pin(output)
  if any(handler in BP._get_node_info(p.get_owning_node()).type_id for p in pin.list_connected_pins()):continue
  call=BP.create_node(graph,'CallFunction|'+handler,ue.IntPoint(550,5500),declaring_class=pc.generated_class());assert pin.try_create_connection(call.find_execute_pin())
assert ue.EditorAssetLibrary.save_loaded_asset(context,False)
write(pc,'ResolveSecondaryLocalPawn','''
 (if (and (Networking|HasAuthority) (and (Pawn|IsLocalPlayerController) (Game|Player|IsPrimaryPlayer)))
  (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopPlayerController.BP_CoopPlayerController_C")
   (bind other (Utilities|Casting|CastToBP_CoopPlayerController :Object item)
    (:then (if (and (Pawn|IsLocalPlayerController :self other) (not (Game|Player|IsPrimaryPlayer :self other))) (return (Controller|GetControlledPawn :self other)))) (:CastFailed))))
 (return "None")''')
write(pc,'RefreshSplitKeyboard',f'''
 (if (and (Pawn|IsLocalPlayerController) (Game|Player|IsPrimaryPlayer))
  (bind player (CallFunction|ResolveSecondaryLocalPawn))
  (Utilities|IsValid :InputObject player
   (:"Is Valid"
    (bind controller (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController :self player))
     (:then
      (bind subsystem (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController controller))
      (Utilities|IsValid :InputObject subsystem
       (:"Is Valid"
        (Input|InjectInputVectorforAction :self subsystem :Action "/Game/Input/Actions/IA_Move.IA_Move" :Value (Math|Vector|MakeVector :X (- (select {V('P2Right')} 1.0 0.0) (select {V('P2Left')} 1.0 0.0)) :Y (- (select {V('P2Forward')} 1.0 0.0) (select {V('P2Back')} 1.0 0.0))))
        (Input|InjectInputVectorforAction :self subsystem :Action "/Game/Input/Actions/IA_Look.IA_Look" :Value (Math|Vector|MakeVector :X (* (- (select {V('P2TurnRight')} 1.0 0.0) (select {V('P2TurnLeft')} 1.0 0.0)) 2.0)))
        (Input|InjectInputVectorforAction :self subsystem :Action "/Game/Input/Actions/IA_Jump.IA_Jump" :Value (Math|Vector|MakeVector :X (select {V('P2Jump')} 1.0 0.0)))
        (Input|InjectInputVectorforAction :self subsystem :Action "/Game/Core/Input/IA_Brace.IA_Brace" :Value (Math|Vector|MakeVector :X (select {V('P2Brace')} 1.0 0.0)))
        (Input|InjectInputVectorforAction :self subsystem :Action "/Game/Core/Input/IA_Interact.IA_Interact" :Value (Math|Vector|MakeVector :X (select {V('P2Use')} 1.0 0.0)))
        (Input|InjectInputVectorforAction :self subsystem :Action "/Game/Core/Input/IA_ToggleView.IA_ToggleView" :Value (Math|Vector|MakeVector :X (select {V('P2View')} 1.0 0.0)))
        (Input|InjectInputVectorforAction :self subsystem :Action "/Game/Core/Input/IA_Headlamp.IA_Headlamp" :Value (Math|Vector|MakeVector :X (select {V('P2Lamp')} 1.0 0.0)))
        {S('P2View','false')} {S('P2Lamp','false')}) (:"Is Not Valid"))) (:CastFailed))) (:"Is Not Valid")))''')
event(pc,'ReceiveTick','RefreshSplitKeyboard');save(pc)
character=ue.load_asset('/Game/Core/BP_CoopCharacter');fn(character,'StopAdventureJump');write(character,'StopAdventureJump','(if (Pawn|IsLocallyControlled) (Pawn|Character|StopJumping))')
graph=BP.get_graph(character,'EventGraph');node=next(n for n in BP.find_nodes(graph) if BP._get_node_info(n).type_id.endswith('|EnhancedInputActionIA_Jump'))
for output in ('Completed','Canceled'):
 pin=node.find_output_pin(output)
 if not list(pin.list_connected_pins()):
  call=BP.create_node(graph,'CallFunction|StopAdventureJump',ue.IntPoint(550,6000),declaring_class=character.generated_class());assert pin.try_create_connection(call.find_execute_pin())
save(character)
RESULT={'shared_keyboard':{'move':'Arrows','turn':'Comma/Period','jump':'Slash or Right Ctrl','brace':'Right Shift','interact':'Enter','view':'C','headlamp':'H'},'through_secondary_own_input_subsystem':True,'runtime_acceptance_pending':True}
(QUEUE/'keyboard-build.json').write_text(json.dumps(RESULT,indent=2))
