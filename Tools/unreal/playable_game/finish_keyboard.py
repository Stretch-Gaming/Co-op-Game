import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
character=ue.load_asset('/Game/Core/BP_CoopCharacter');fn(character,'StopAdventureJump');write(character,'StopAdventureJump','(if (Pawn|IsLocallyControlled) (Pawn|Character|StopJumping))')
graph=BP.get_graph(character,'EventGraph');node=next(n for n in BP.find_nodes(graph) if BP._get_node_info(n).type_id.endswith('|EnhancedInputActionIA_Jump'))
for output in ('Completed','Canceled'):
 pin=node.find_output_pin(output)
 if not list(pin.list_connected_pins()):
  call=BP.create_node(graph,'CallFunction|StopAdventureJump',ue.IntPoint(550,6000),declaring_class=character.generated_class());assert pin.try_create_connection(call.find_execute_pin())
save(character)
RESULT={'shared_keyboard':{'move':'Arrows','turn':'Comma/Period','jump':'Slash or Right Ctrl','brace':'Right Shift','interact':'Enter','view':'C','headlamp':'H'},'through_secondary_own_input_subsystem':True,'runtime_acceptance_pending':True}
(QUEUE/'keyboard-build.json').write_text(json.dumps(RESULT,indent=2))
