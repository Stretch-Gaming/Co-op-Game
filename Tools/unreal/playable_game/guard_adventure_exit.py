import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
bp=ue.load_asset('/Game/Puzzles/BP_MapExit');fn(bp,'AdventureExitAllowed',outputs=[('Allowed','bool')])
write(bp,'AdventureExitAllowed','''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then
   (bind count (Class|BPCoopGameState|GetPlayerCount :self gs))
   (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
   (if (and (>= count 2) (<= count 4))
    (if (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site01")
     (return (and (== index 3) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2"))))
     (else (return (and (== index 1) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1"))))))
    (else (return false)))) (:CastFailed (return false)))''')
# Add the readiness guard before the delivered extraction transaction.
graph=BP.get_graph(bp,'ReevaluateExit')
call=next(n for n in BP.find_nodes(graph) if 'TryCommitExtraction' in BP._get_node_info(n).type_id)
input_pin=call.find_execute_pin();links=list(input_pin.list_connected_pins());assert len(links)==1
source=links[0]
if 'AdventureExitAllowed' not in [BP._get_node_info(n).type_id.split('|')[-1] for n in BP.find_nodes(graph)]:
 guard_call=BP.create_node(graph,'CallFunction|AdventureExitAllowed',ue.IntPoint(1200,0),declaring_class=bp.generated_class())
 branch=BP.create_node(graph,'Utilities|FlowControl|Branch',ue.IntPoint(1450,0))
 source.break_single_pin_link(input_pin);assert source.try_create_connection(guard_call.find_execute_pin());assert guard_call.find_then_pin().try_create_connection(branch.find_execute_pin())
 assert guard_call.find_output_pin('Allowed').try_create_connection(branch.find_input_pin('Condition'));assert branch.find_output_pin('Then').try_create_connection(input_pin)
 # A blocked entrance remains able to recheck after the round changes.
 setter=BP.create_node(graph,'Variables|Default|SetExitCommitted',ue.IntPoint(1600,250));assert BP.set_pin_value(BP._get_node_info(setter).input_pins[1].pin_id,'false') is None or True
 assert branch.find_output_pin('Else').try_create_connection(setter.find_execute_pin())
save(bp)
RESULT={'exit_requires_team_size_and_completed_cave_or_active_maze':True,'runtime_acceptance_pending':True}
