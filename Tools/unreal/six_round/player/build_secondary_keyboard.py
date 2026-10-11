"""Primary-run controller authoring, preserving secondary owning input routing.
Writes Core controller + run context + new IA_P2Flare/IA_P2Climb only.
"""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from authoring import *
guard()
pc=ue.load_asset('/Game/Core/BP_CoopPlayerController');assert pc
assets=ue.AssetToolsHelpers.get_asset_tools();folder='/Game/Core/Input'
context=ue.load_asset(folder+'/IMC_RunControls');assert context
for name,key_name in [('Flare','RightAlt'),('Climb','P')]:
 full='IA_P2'+name
 action=ue.load_asset(folder+'/'+full) or assets.create_asset(full,folder,ue.InputAction,ue.InputAction_Factory())
 assert action;action.set_editor_property('value_type',ue.InputActionValueType.BOOLEAN);action.set_editor_property('consume_input',False)
 key=ue.Key();key.set_editor_property('key_name',ue.Name(key_name))
 if not any(mapping.action==action and mapping.key==key for mapping in context.default_key_mappings.mappings):context.map_key(action,key)
 var(pc,'P2'+name,'bool',False)
 for suffix,value in [('On','true'),('Off','false')]:
  handler='Keyboard'+name+suffix;fn(pc,handler)
  write(pc,handler,f'(if (and (Networking|HasAuthority) (and (Pawn|IsLocalPlayerController) (Game|Player|IsPrimaryPlayer))) {S("P2"+name,value)})')
 graph=BP.get_graph(pc,'EventGraph')
 matches=[node for node in BP.find_nodes(graph) if BP._get_node_info(node).type_id.rsplit('|',1)[-1] in (full,'EnhancedInputAction'+full)]
 node=matches[0] if matches else BP.create_node(graph,'Input|EnhancedActionEvents|'+full,ue.IntPoint(0,9000))
 assert node
 for output,suffix in [('Started','On'),('Completed','Off'),('Canceled','Off')]:
  pin=node.find_output_pin(output);assert pin
  for target in list(pin.list_connected_pins()):pin.break_single_pin_link(target)
  call=BP.create_node(graph,'CallFunction|Keyboard'+name+suffix,ue.IntPoint(600,9000),declaring_class=pc.generated_class())
  assert pin.try_create_connection(call.find_execute_pin())
 assert ue.EditorAssetLibrary.save_loaded_asset(action,False)
assert ue.EditorAssetLibrary.save_loaded_asset(context,False)
# ResolveSecondaryLocalPawn already checks the local host/controller identity;
# this function never chooses a player by an array index.
body=''
definitions=[('move','/Game/Input/Actions/IA_Move',f'(Math|Vector|MakeVector :X (- (select {V("P2Right")} 1.0 0.0) (select {V("P2Left")} 1.0 0.0)) :Y (- (select {V("P2Forward")} 1.0 0.0) (select {V("P2Back")} 1.0 0.0)))'),
 ('look','/Game/Input/Actions/IA_Look',f'(Math|Vector|MakeVector :X (* (- (select {V("P2TurnRight")} 1.0 0.0) (select {V("P2TurnLeft")} 1.0 0.0)) 2.0))')]
for name,path,value in definitions:
 assert ue.load_asset(path),path
 body+=f'(Input|InjectInputVectorforAction :self subsystem :Action "{path}.{path.rsplit("/",1)[-1]}" :Value {value})\n'
for flag,path in [('Jump','/Game/Input/Actions/IA_Jump'),('Brace','/Game/Core/Input/IA_Sprint'),('Flare','/Game/Core/Input/IA_ThrowFlare'),('Climb','/Game/Core/Input/IA_Climb'),('Use','/Game/Core/Input/IA_Interact'),('View','/Game/Core/Input/IA_ToggleView'),('Lamp','/Game/Core/Input/IA_Headlamp')]:
 assert ue.load_asset(path),path
 body+=f'(Input|InjectInputVectorforAction :self subsystem :Action "{path}.{path.rsplit("/",1)[-1]}" :Value (Math|Vector|MakeVector :X (select {V("P2"+flag)} 1.0 0.0)))\n'
body+=S('P2View','false')+' '+S('P2Lamp','false')+' '+S('P2Flare','false')
write(pc,'RefreshSplitKeyboard',f'''
 (if (and (Networking|HasAuthority) (and (Pawn|IsLocalPlayerController) (Game|Player|IsPrimaryPlayer)))
  (bind player (CallFunction|ResolveSecondaryLocalPawn))
  (Utilities|IsValid :InputObject player
   (:"Is Valid" (bind controller (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController :self player))
    (:then (bind subsystem (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController controller))
     (Utilities|IsValid :InputObject subsystem (:"Is Valid" {body}) (:"Is Not Valid"))) (:CastFailed))) (:"Is Not Valid")))''')
save(pc)
RESULT={'writes':['/Game/Core/BP_CoopPlayerController','/Game/Core/Input/IMC_RunControls','/Game/Core/Input/IA_P2Flare','/Game/Core/Input/IA_P2Climb'],'secondary_keys':{'sprint':'RightShift','flare':'RightAlt','climb':'P','view':'C','headlamp':'H','move':'arrows','jump':'Slash/RightControl','interact':'Enter'},'retired_injection':'IA_Brace replaced by IA_Sprint','input_route':'resolved secondary local pawn -> its controller -> its Enhanced Input subsystem','runtime_acceptance_pending':True}
(QUEUE/'secondary-keyboard-build.json').write_text(json.dumps(RESULT,indent=2))
