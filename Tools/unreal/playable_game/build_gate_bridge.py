import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
gate=ue.load_asset('/Game/Player/Round3/BP_GauntletGate')
if not ARGS.get('bridge_only'):
    var(gate,'bLatched','bool',False,notify=True);var(gate,'LatchedAttempt','int',0,replicated=True)
    fn(gate,'BindAdventureLevers');fn(gate,'ResetAdventureLatch',[('Index','int'),('Attempt','int')]);fn(gate,'RequestAdventureLatch',[('Index','int'),('Attempt','int')],[('Accepted','bool')]);fn(gate,'QueryAdventureLatch',[('Index','int'),('Attempt','int')],[('Latched','bool')])
    write(gate,'GetLeverCount','''
     (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
      (:then (return (select (>= (Utilities|String|StringToInteger :InString (Utilities|String|ToString(Name) :InName (Class|BPCoopGameState|GetScalingRow :self gs))) 4) 2 1))) (:CastFailed (return 1)))''')
    fn(gate,'ApplyAdventureGate')
    write(gate,'ApplyAdventureGate','(Variables|Default|SetTargetLift (select (Variables|Default|GetOpen) (Variables|Default|GetOpenHeight) 0.0))')
    write(gate,'UpdateGate',f'''
     (if (Networking|HasAuthority)
      (bind held (CallFunction|AreLeversHeld)) (bind under (CallFunction|SomeoneUnder))
      {S('Open',f'(or {V("Latched")} (or held (and under (> {V("CurrentLift")} 10.0))))')}
      (CallFunction|ApplyAdventureGate))''')
    write(gate,'OnRep_bLatched','(CallFunction|UpdateGate)')
    write(gate,'BindAdventureLevers',f'''
     (Utilities|Array|Clear :TargetArray {V('Levers')})
     (for item (Actor|GetAllActorswithTag :Tag "HC_GauntletLever")
      (bind lever (Utilities|Casting|CastToBP_Lever :Object item)
       (:then (Utilities|Array|AddUnique :TargetArray {V('Levers')} :NewItem lever)) (:CastFailed)))''')
    write(gate,'ResetAdventureLatch',f'(if (and (Networking|HasAuthority) (== Index 3)) {S("Latched","false")} {S("LatchedAttempt","Attempt")} {S("Open","false")} (CallFunction|ApplyAdventureGate))','Index Attempt')
    write(gate,'RequestAdventureLatch',f'''
     (if (Networking|HasAuthority)
      (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
       (:then
        (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
        (if (and (and (== Index 3) (== index Index)) (and (== attempt Attempt) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1"))))
         {S('Latched','true')} {S('LatchedAttempt','Attempt')} {S('Open','true')} (CallFunction|ApplyAdventureGate) (return true))) (:CastFailed)))
     (return false)''','Index Attempt')
    write(gate,'QueryAdventureLatch',f'(return (and {V("Latched")} (and (== Index 3) (== Attempt {V("LatchedAttempt")}))))','Index Attempt')
    event(gate,'ReceiveBeginPlay','BindAdventureLevers');event(gate,'ResetForRound','ResetAdventureLatch',['Index','Attempt']);save(gate)
bridge=create('/Game/Player/Round3/BP_PlayableGateBridge',ue.load_asset('/Game/Puzzles/Gauntlet/BP_HCGauntletGateBridge').generated_class())
for n in ('SupportsLatch','RequestLatch','QueryLatch'):fn(bridge,n)
fn(bridge,'ResolveAdventureGate',outputs=[('Gate',gate.generated_class())])
write(bridge,'ResolveAdventureGate','''
 (bind items (Actor|GetAllActorswithTag :Tag "HC_GauntletGate"))
 (if (== (Utilities|Array|Length :TargetArray items) 1)
  (for item items
   (bind gate (Utilities|Casting|CastToBP_GauntletGate :Object item) (:then (return gate)) (:CastFailed))))
 (return "None")''')
write(bridge,'SupportsLatch','(bind gate (CallFunction|ResolveAdventureGate)) (Utilities|IsValid :InputObject gate (:"Is Valid" (return true)) (:"Is Not Valid" (return false)))')
for method,target in [('RequestLatch','RequestAdventureLatch'),('QueryLatch','QueryAdventureLatch')]:
 write(bridge,method,f'''
 (bind gate (CallFunction|ResolveAdventureGate))
 (Utilities|IsValid :InputObject gate
  (:"Is Valid" (bind accepted (Class|BPGauntletGate|{target} :self gate :Index Index :Attempt Attempt)) (return accepted)) (:"Is Not Valid" (return false)))''','Index Attempt')
save(bridge)
RESULT={'gate_latch':True,'scaled_lever_count':True,'runtime_tag_connections':True,'runtime_acceptance_pending':True}
(QUEUE/'gate-build.json').write_text(json.dumps(RESULT,indent=2))
