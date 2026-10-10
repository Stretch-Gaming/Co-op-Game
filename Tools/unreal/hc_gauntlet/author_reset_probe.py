"""Labeled fixture caller for the actual Blueprint interface message path."""
import sys,importlib,json
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
bp=ue.load_asset('/Game/Puzzles/Test/HC_Gauntlet/BP_GauntletInputProbe')
fn(bp,'DispatchFixtureReset',[('TargetActor',ue.Actor.static_class()),('Index','int'),('Attempt','int')])
compile_bp(bp)
write(bp,'DispatchFixtureReset','(Class|BPIRoundReset|ResetforRound(Message) :self TargetActor :Index Index :Attempt Attempt)','TargetActor Index Attempt')
save(bp)
snapshot([bp],'reset-probe.json')
