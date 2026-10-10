"""Narrow post-retry restock splice; preserve the current StartRound graph.
Run after rounds20. Capture the Failed phase into a real member BEFORE the
RoundState setter; a pure DSL bind would re-read the changed phase afterward.
"""
import sys
from pathlib import Path
_core=Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'
sys.path.insert(0,str(_core))
from common import *
guard();gm=ue.load_asset('/Game/Core/BP_CoopGameMode')
var(gm,'WasCheckpointRetry','bool',False)
for name in ('CaptureCheckpointRetry','RestockAfterCheckpointRetry'):fn(gm,name)
write(gm,'CaptureCheckpointRetry',f'''
 {S('WasCheckpointRetry','false')}
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   {S('WasCheckpointRetry',EQ('phase',FAIL))}) (:CastFailed)))''')
write(gm,'RestockAfterCheckpointRetry',f'''
 (if (and (Networking|HasAuthority) {V('WasCheckpointRetry')})
  (bind gs {GS} (:then {STATE}
   (if {EQ('phase',PLAY)}
    (for state (Class|GameStateBase|GetPlayerArray :self gs)
     (bind pawn (PlayerState|GetPawn :self state))
     (Utilities|IsValid :InputObject pawn (:"Is Valid"
      (bind tools (Utilities|Casting|CastToAC_Tools :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Player/Tools/AC_Tools.AC_Tools_C"))
       (:then (Class|ACTools|RestockFlares :self tools)) (:CastFailed))) (:"Is Not Valid"))))
   {S('WasCheckpointRetry','false')}) (:CastFailed {S('WasCheckpointRetry','false')})))''')
graph=BP.get_graph(gm,'StartRound')
def leaf(node):return ''.join(ch for ch in BP._get_node_info(node).type_id.rsplit('|',1)[-1] if ch.isalnum()).lower()
def calls(name):return [n for n in BP.find_nodes(graph) if leaf(n)==name.lower()]
state_setters=[n for n in BP.find_nodes(graph) if leaf(n) in ('setroundstate','setwithnotifyroundstate')]
assert len(state_setters)==1,'Inspect saved StartRound: one replicated RoundState setter expected'
refreshes=calls('RefreshSixObjective');assert len(refreshes)==1,'Inspect saved StartRound: one objective tail call expected'
# Refuse partial/ambiguous installation. Re-running an already installed pair is safe.
before_calls=calls('CaptureCheckpointRetry');after_calls=calls('RestockAfterCheckpointRetry')
assert len(before_calls)==len(after_calls) and len(before_calls) in (0,1),'Partial retry splice needs primary inspection'
if before_calls:
 assert list(state_setters[0].find_execute_pin().list_connected_pins())==[before_calls[0].find_then_pin()],'Existing capture is not immediately before state assignment'
 assert list(refreshes[0].find_then_pin().list_connected_pins())==[after_calls[0].find_execute_pin()],'Existing restock is not immediately after objective tail'
if not before_calls:
 setter=state_setters[0];incoming=list(setter.find_execute_pin().list_connected_pins());assert len(incoming)==1
 capture=BP.create_node(graph,'CallFunction|CaptureCheckpointRetry',ue.IntPoint(1300,1200),declaring_class=gm.generated_class());assert capture
 incoming[0].break_single_pin_link(setter.find_execute_pin())
 assert incoming[0].try_create_connection(capture.find_execute_pin());assert capture.find_then_pin().try_create_connection(setter.find_execute_pin())
 tail=refreshes[0].find_then_pin();existing=list(tail.list_connected_pins());assert len(existing)<=1,'Preserve unexpected tail fan-out manually'
 restock=BP.create_node(graph,'CallFunction|RestockAfterCheckpointRetry',ue.IntPoint(2200,1200),declaring_class=gm.generated_class());assert restock
 for pin in existing:tail.break_single_pin_link(pin)
 assert tail.try_create_connection(restock.find_execute_pin())
 for pin in existing:assert restock.find_then_pin().try_create_connection(pin)
save(gm)
RESULT={'writes':['/Game/Core/BP_CoopGameMode'],'modified_graph':'StartRound narrow before-setter/after-objective splice','actual_snapshot_member':'WasCheckpointRetry','initial_round_and_clear_to_round2_extra_refund':False,'primary_canonical_integration':'Capture Failed phase before SetRoundState, then RestockFlares only after successful retry StartRound writes new ScalingRow','focused_tests':['3-player round4 remote middle-slot disconnect -> remaining row2 and3 flares','Round1 clear; spend one flare before maze-mouth start2 -> start2 must preserve spent stock','ordinary same-row wipe -> one final full allowance, one attempt increment'],'native_node_assumptions':['saved StartRound has one SetRoundState/SetwithNotifyRoundState and one RefreshSixObjective tail call','all four created call nodes have ordinary exec/then pins'],'runtime_acceptance_pending':True}
