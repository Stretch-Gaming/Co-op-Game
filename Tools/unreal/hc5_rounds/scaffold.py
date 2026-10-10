import sys,json
sys.path.insert(0,str(HERE))
from authoring import *
assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
A=unreal.Actor.static_class();P=unreal.Pawn.static_class()
cp=create('/Game/Puzzles/BP_Checkpoint',A)
for n,k in [('RoundIndex','int')]:var(cp,n,k);BP.set_variable_instance_editable(cp,n,True)
for i,y in enumerate([-300,-100,100,300]):
 c=component(cp,'Spot'+str(i),unreal.SceneComponent.static_class());c.set_editor_property('relative_location',unreal.Vector(0,y,100))
fn(cp,'GetSpawnTransform',[('Slot','int')],[('Spawn','Transform')]);compile_bp(cp)
d=create('/Game/Puzzles/Rounds/BP_RoundDirector',A)
for n,k in [('CurrentCheckpoint',A),('CandidateCheckpoint',A),('CandidateCount','int'),('RetryPending','bool'),('RetryIndex','int'),('RetryAttempt','int'),('ObservedIndex','int'),('ObservedAttempt','int'),('ObservedRoster','int'),('RecoveryAllowed','bool')]:var(d,n,k)
for n,ins,outs in [
 ('BeginDirector',[],[]),('MonitorRound',[],[]),('ScheduleRetry',[],[]),('RetryRound',[],[]),
 ('RequestStart',[('Index','int'),('EnteringPawn',P)],[('Started','bool')]),
 ('SelectCheckpoint',[('Index','int')],[('Found','bool')]),
 ('RecoverPlayer',[('PlayerPawn',P)],[('Restored','bool')]),
 ('RecoverRoster',[],[('Recovered','bool')]),
 ('DispatchReset',[('Index','int'),('Attempt','int')],[])]:fn(d,n,ins,outs)
compile_bp(d);defaults(d,replicates=True)
s=create('/Game/Puzzles/BP_RoundStart',unreal.TriggerBox.static_class());var(s,'RoundIndex','int');BP.set_variable_instance_editable(s,'RoundIndex',True)
fn(s,'TryEnter',[('EnteringActor',A)]);compile_bp(s)
bp=s;g=BP.get_graph(s,'EventGraph')
out={}
for asset in [cp,d,s]:
 g=BP.get_graph(asset,'EventGraph')
 out[asset.get_name()]={term:BP.find_node_types(g,term) for term in ['Spot','GetWorldTransform','RequestStart','SelectCheckpoint','SetActorTransform','ResetforRound','GetPlayerState','IsPlayerControlled','Array_Contains','GetPawn','GetRoundState','ReceiveActorBeginOverlap','RoundIndex']}
(HERE/'scaffold.json').write_text(json.dumps(out,indent=2,default=str))
