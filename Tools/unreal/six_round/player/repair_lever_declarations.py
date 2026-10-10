"""Undo only stage0 additions to baseline CanHold; editor API signature preflight required."""
import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
guard()
bp=ue.load_asset('/Game/Player/RelicChamber/BP_Lever')
graph=BP.get_graph(bp,'CanHold')
# Primary must inspect remove_function_param signature before executing these calls.
assert hasattr(BP,'remove_function_param'), 'Inspect BlueprintTools parameter-removal API before repair'
if BP._param_name_exists(graph,'PlayerPawn',True):BP.remove_function_param(graph,'PlayerPawn',True)
if BP._param_name_exists(graph,'Allowed',False):BP.remove_function_param(graph,'Allowed',False)
fn(bp,'CanSixHold',[('PlayerPawn',ue.Actor.static_class())],[('Allowed','bool')])
save(bp)
RESULT={'repaired':'only CanHold stage0-added parameters','runtime_acceptance_pending':True}
