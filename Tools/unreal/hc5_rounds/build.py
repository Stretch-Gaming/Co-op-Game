import sys,json
sys.path.insert(0,str(HERE))
from authoring import *
assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
original_write=write
def write(bp,name,body,parameters=''):
 if not ARGS.get('functions') or name in ARGS['functions']:original_write(bp,name,body,parameters)
cp=unreal.load_asset('/Game/Puzzles/BP_Checkpoint');d=unreal.load_asset('/Game/Puzzles/Rounds/BP_RoundDirector');s=unreal.load_asset('/Game/Puzzles/BP_RoundStart')
for n,k in [('DirectorReady','bool'),('DirectorCount','int'),('EnteredRoster','bool')]:var(d,n,k)
fn(d,'PreparePlayerForCheckpoint',[('PlayerPawn',unreal.Pawn.static_class())]);compile_bp(d)
write(cp,'GetSpawnTransform','''(return (Transformation|GetWorldTransform :self (select (== Slot 0) (Variables|Default|GetSpot0) (select (== Slot 1) (Variables|Default|GetSpot1) (select (== Slot 2) (Variables|Default|GetSpot2) (Variables|Default|GetSpot3))))))''','Slot')
write(d,'SelectCheckpoint','''
 (Variables|Default|SetCandidateCount 0)
 (Variables|Default|SetCandidateCheckpoint)
 (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_Checkpoint.BP_Checkpoint_C")
  (bind point (Utilities|Casting|CastToBP_Checkpoint :Object item)
   (:then (if (== (Class|BPCheckpoint|GetRoundIndex :self point) Index)
    (Variables|Default|SetCandidateCount (+ (Variables|Default|GetCandidateCount) 1))
    (Variables|Default|SetCandidateCheckpoint point))) (:CastFailed)))
 (if (== (Variables|Default|GetCandidateCount) 1)
  (Variables|Default|SetCurrentCheckpoint (Variables|Default|GetCandidateCheckpoint))
  (return true))
 (return false)''','Index')
write(d,'PreparePlayerForCheckpoint','', 'PlayerPawn')
write(d,'RecoverPlayer','''
 (if (Networking|HasAuthority)
  (Utilities|IsValid :InputObject PlayerPawn
   (:"Is Valid" (CallFunction|PreparePlayerForCheckpoint :PlayerPawn PlayerPawn) (return true)) (:"Is Not Valid")))
 (return false)''','PlayerPawn')
write(d,'RecoverRoster','''
 (if (Networking|HasAuthority)
  (bind checkpoint (Utilities|Casting|CastToBP_Checkpoint :Object (Variables|Default|GetCurrentCheckpoint))
   (:then
    (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
     (:then
      (Variables|Default|SetRecoveryAllowed true)
      (for state (Class|GameStateBase|GetPlayerArray :self gs)
       (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object state)
        (:then
         (bind slot (Class|BPCoopPlayerState|GetColorSlot :self ps))
         (Utilities|IsValid :InputObject (PlayerState|GetPawn :self state)
          (:"Is Valid" (if (or (< slot 0) (> slot 3)) (Variables|Default|SetRecoveryAllowed false)))
          (:"Is Not Valid" (Variables|Default|SetRecoveryAllowed false))))
        (:CastFailed (Variables|Default|SetRecoveryAllowed false))))
      (if (Variables|Default|GetRecoveryAllowed)
       (for state (Class|GameStateBase|GetPlayerArray :self gs)
        (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object state)
         (:then
          (bind pawn (PlayerState|GetPawn :self state))
          (CallFunction|RecoverPlayer :PlayerPawn pawn)
          (Transformation|SetActorTransform :self pawn :NewTransform (Class|BPCheckpoint|GetSpawnTransform :self checkpoint :Slot (Class|BPCoopPlayerState|GetColorSlot :self ps)) :bSweep false :bTeleport true)) (:CastFailed))))
      (return (Variables|Default|GetRecoveryAllowed))) (:CastFailed (return false)))) (:CastFailed (return false))))
 (return false)''')
write(d,'DispatchReset','''
 (if (Networking|HasAuthority)
  (for item (Actor|GetAllActorswithInterface :Interface "/Game/Core/BPI_RoundReset.BPI_RoundReset_C")
   (Class|BPIRoundReset|ResetforRound(Message) :self item :Index Index :Attempt Attempt)))''','Index Attempt')
write(d,'ScheduleRetry','''
 (if (and (Networking|HasAuthority) (not (Variables|Default|GetRetryPending)))
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (if (and (> index 0) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator3")))
     (Variables|Default|SetRetryIndex index)
     (Variables|Default|SetRetryAttempt attempt)
     (Variables|Default|SetRetryPending true)
     (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RetryRound" :Time 3.0 :bLooping false))) (:CastFailed)))''')
write(d,'RetryRound','''
 (if (and (Networking|HasAuthority) (Variables|Default|GetRetryPending))
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (if (and (and (== index (Variables|Default|GetRetryIndex)) (== attempt (Variables|Default|GetRetryAttempt))) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator3")))
     (if (CallFunction|SelectCheckpoint :Index index)
      (if (CallFunction|RecoverRoster)
      (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
       (:then
        (CallFunction|DispatchReset :Index index :Attempt (+ attempt 1))
        (Class|BPCoopGameMode|StartRound :self gm :Index index)
        (Variables|Default|SetRetryPending false)) (:CastFailed))))
     (else (Variables|Default|SetRetryPending false)))) (:CastFailed)))''')
write(d,'RequestStart','''
 (if (and (Networking|HasAuthority) (Variables|Default|GetDirectorReady))
  (Utilities|IsValid :InputObject EnteringPawn
   (:"Is Valid"
    (if (Pawn|IsPlayerControlled :self EnteringPawn)
     (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
      (:then
       (Variables|Default|SetEnteredRoster false)
       (for state (Class|GameStateBase|GetPlayerArray :self gs)
        (if (== (PlayerState|GetPawn :self state) EnteringPawn) (Variables|Default|SetEnteredRoster true)))
       (bind (oldIndex phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
       (bind count (Class|BPCoopGameState|GetPlayerCount :self gs))
       (if (and (and (Variables|Default|GetEnteredRoster) (and (>= count 2) (<= count 4))) (and (and (>= Index 1) (<= Index 3)) (or (and (== Index 1) (and (== oldIndex 0) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator0")))) (and (== Index (+ oldIndex 1)) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2"))))))
        (if (CallFunction|SelectCheckpoint :Index Index)
         (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
          (:then
           (Class|BPCoopGameMode|StartRound :self gm :Index Index)
           (CallFunction|MonitorRound)
           (return true)) (:CastFailed))))
       (return false)) (:CastFailed (return false))))) (:"Is Not Valid" (return false))))
 (return false)''','Index EnteringPawn')
write(d,'MonitorRound','''
 (if (and (Networking|HasAuthority) (Variables|Default|GetDirectorReady))
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (bind count (Class|BPCoopGameState|GetPlayerCount :self gs))
    (if (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1"))
     (if (or (!= index (Variables|Default|GetObservedIndex)) (!= attempt (Variables|Default|GetObservedAttempt)))
      (CallFunction|SelectCheckpoint :Index index)
      (Variables|Default|SetObservedIndex index)
      (Variables|Default|SetObservedAttempt attempt)
      (Variables|Default|SetObservedRoster count)
      (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RetryRound")
      (Variables|Default|SetRetryPending false)
      (else
       (if (< count (Variables|Default|GetObservedRoster))
        (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
         (:then (Class|BPCoopGameMode|FailRound :self gm) (CallFunction|ScheduleRetry)) (:CastFailed))
        (else (Variables|Default|SetObservedRoster count))))))
    (if (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator3")) (CallFunction|ScheduleRetry))) (:CastFailed)))
''')
write(d,'BeginDirector','''
 (if (Networking|HasAuthority)
  (Variables|Default|SetDirectorCount 0)
  (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/Rounds/BP_RoundDirector.BP_RoundDirector_C")
   (Variables|Default|SetDirectorCount (+ (Variables|Default|GetDirectorCount) 1)))
  (Variables|Default|SetDirectorReady (== (Variables|Default|GetDirectorCount) 1))
  (if (Variables|Default|GetDirectorReady)
   (CallFunction|SelectCheckpoint :Index 0)
   (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "MonitorRound" :Time 0.2 :bLooping true)))''')
event(d,'ReceiveBeginPlay','BeginDirector')
write(s,'TryEnter','''
 (if (Networking|HasAuthority)
  (bind pawn (Utilities|Casting|CastToPawn :Object EnteringActor)
   (:then
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/Rounds/BP_RoundDirector.BP_RoundDirector_C")
     (bind director (Utilities|Casting|CastToBP_RoundDirector :Object item)
      (:then (Class|BPRoundDirector|RequestStart :self director :Index (Variables|Default|GetRoundIndex) :EnteringPawn pawn)) (:CastFailed)))) (:CastFailed)))''','EnteringActor')
e=BP.add_event(s,'ReceiveActorBeginOverlap');g=BP.get_graph(s,'EventGraph')
if not list(e.find_then_pin().list_connected_pins()):
 call=BP.create_node(g,'CallFunction|TryEnter',unreal.IntPoint(450,300));assert e.find_then_pin().try_create_connection(call.find_execute_pin());assert e.find_output_pin('OtherActor').try_create_connection(call.find_input_pin('EnteringActor'))
defaults(s,RoundIndex=1)
for b in [cp,d,s]:save(b)
(HERE/'build.json').write_text(json.dumps({'passed':True,'assets':[b.get_path_name() for b in [cp,d,s]]}))


