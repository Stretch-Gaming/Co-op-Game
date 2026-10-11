"""Cache the authored starting pose, not a physics-adjusted observed key pose.
Run after escape_key_recovery.py. Never rewrite its failure/spawn monitor.
"""
import sys
from pathlib import Path
_core=Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'
sys.path.insert(0,str(_core))
from common import *
guard();gm=ue.load_asset('/Game/Core/BP_CoopGameMode');carry=ue.load_asset('/Game/Puzzles/BP_Carryable');assert gm and carry
# The getter must exist on the inherited carryable schema; no disk/property trick.
assert 'InitialTransform' in BP.list_variables(carry)
begin=BP.read_graph_dsl(BP.get_graph(carry,'BeginCarryable'))
assert 'SetInitialTransform' in begin and 'GetActorTransform' in begin
assert begin.index('SetInitialTransform')<begin.index('ApplyCarryState'),'Initialize before physics is enabled'
parent_events=BP.read_graph_dsl(BP.get_graph(carry,'EventGraph'))
assert 'BeginCarryable' in parent_events,'Carryable BeginPlay must call its initializer'
# First monitor runs after0.2s of world ticking, after the placed actors' synchronous
# BeginPlay dispatch. A native SpawnActorfromClass finishes spawning/BeginPlay before
# returning. Refuse an active child BeginPlay override that might skip this initializer.
key_bp=ue.load_asset('/Game/Puzzles/BP_KeyRelic');assert key_bp
for node in BP.find_nodes(BP.get_graph(key_bp,'EventGraph')):
 leaf=BP._get_node_info(node).type_id.rsplit('|',1)[-1].lower()
 if leaf in ('receivebeginplay','eventbeginplay','beginplay'):
  links=list(node.find_then_pin().list_connected_pins())
  if links:
   assert len(links)==1
   child_events=BP.read_graph_dsl(BP.get_graph(key_bp,'EventGraph'))
   assert '(event EventBeginPlay\n  (|Parent:BeginPlay))' in child_events,'KeyRelic BeginPlay must call only its carryable parent initializer'
fn(gm,'CacheRelicHome')
write(gm,'CacheRelicHome',f'''
 (if (and (Networking|HasAuthority) (not {V('RelicHomeReady')}))
  (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_KeyRelic.BP_KeyRelic_C")
   (Utilities|IsValid :InputObject actor (:"Is Valid"
    (bind key (Utilities|Casting|CastToBP_Carryable :Object actor)
      (:then
       {S('RelicHome','(Class|BPCarryable|GetInitialTransform :self key)')}
       {S('RelicHomeReady','true')}) (:CastFailed))) (:"Is Not Valid"))))''')
save(gm)
RESULT={'writes':['/Game/Core/BP_CoopGameMode'],'modified_graph':'CacheRelicHome only','source_pose':'BP_Carryable.InitialTransform captured at BeginCarryable before ApplyCarryState/physics','initialization_guards':['server authority','valid actor','verified inherited BeginPlay initialization','cast to inherited BP_Carryable'],'first_poll':'existing BeginEscapeRelicMonitor timer0.2s after synchronous actor BeginPlay; active child BeginPlay override rejected for inspection','unchanged':['MonitorEscapeRelic','RestoreMissingRelic','failure countdown','spawn/refund behavior'],'focused_tests':['record placed transform, BeginCarryable.InitialTransform and GM.RelicHome after first poll; InitialTransform and RelicHome must match including rotation/scale even after physics settles','destroy free escape key -> game-driven failure/retry, replacement initial transform equals original authored pose and cage remains latched open','normal existing-key escape wipe -> same authored transform as missing-key retry'],'native_node_assumptions':['BP_Carryable.GetInitialTransform inherited variable getter available','saved BeginEscapeRelicMonitor remains the existing looping0.2s timer; primary verifies receipt/native graph'],'runtime_acceptance_pending':True}
