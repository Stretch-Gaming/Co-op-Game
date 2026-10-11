"""Jump releases this player's climbing lease before the validated mantle request."""
import sys
sys.path.insert(0,str(HERE))
from authoring import *
guard()
c=ue.load_asset('/Game/Core/BP_CoopCharacter')
write(c,'RequestJump','(if (Pawn|IsLocallyControlled) (bind allowed (CallFunction|CanAcceptSixInput)) (if allowed (CallFunction|RequestBoost) (CallFunction|RequestStopClimb) (Pawn|Character|Jump)))')
graph=BP.get_graph(c,'EventGraph')
for node in BP.find_nodes(graph):
    if BP._get_node_info(node).type_id.rsplit('|',1)[-1] in ('IA_Brace','EnhancedInputActionIA_Brace'):
        for name in ('Started','Completed','Canceled'):
            pin=node.find_output_pin(name)
            for target in list(pin.list_connected_pins()):pin.break_single_pin_link(target)
save(c)
RESULT={'jump_releases_climbing':True,'secondary_sprint_action':'IA_Sprint','runtime_pending':True}
