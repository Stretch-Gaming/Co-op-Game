"""Six round lifecycle, checkpoint recovery, regroup and authoritative travel."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
guard();gm=ue.load_asset('/Game/Core/BP_CoopGameMode');d=ue.load_asset('/Game/Puzzles/Rounds/BP_RoundDirector')
write(d,'PreparePlayerForCheckpoint',f'''
 (bind player (Utilities|Casting|CastToBP_CoopCharacter :Object PlayerPawn)
  (:then (Class|BPCoopCharacter|CancelUse :self player) (Class|BPCoopCharacter|DropFromServer :self player)
   (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self player :ComponentClass "{HEALTH}"))
    (:then (Class|ACHealth|ResetHealth :self health) (Class|BPCoopCharacter|SetInteractionBlocked :self player :Blocked false)
     (bind tools (Utilities|Casting|CastToAC_Tools :Object (Components|GetComponentbyClass :self player :ComponentClass "/Game/Player/Tools/AC_Tools.AC_Tools_C"))
      (:then (Class|ACTools|RestockFlares :self tools)) (:CastFailed))) (:CastFailed))) (:CastFailed))''','PlayerPawn')
write(d,'RegroupRoster',f'''
 (if (and (Networking|HasAuthority) (CallFunction|SelectCheckpoint :Index Index))
  (bind checkpoint (Utilities|Casting|CastToBP_Checkpoint :Object {V('CurrentCheckpoint')})
   (:then (bind gs {GS} (:then
    (for state (Class|GameStateBase|GetPlayerArray :self gs)
     (bind pawn (PlayerState|GetPawn :self state))
     (Utilities|IsValid :InputObject pawn (:"Is Valid"
      (bind tools (Utilities|Casting|CastToAC_Tools :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Player/Tools/AC_Tools.AC_Tools_C"))
       (:then
        (Class|ACTools|RestockFlares :self tools)
        (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "{HEALTH}"))
         (:then (if (Class|ACHealth|IsDead :self health)
          (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object state)
           (:then (CallFunction|PreparePlayerForCheckpoint :PlayerPawn pawn)
            (Transformation|SetActorTransform :self pawn :NewTransform (Class|BPCheckpoint|GetSpawnTransform :self checkpoint :Slot (Class|BPCoopPlayerState|GetColorSlot :self ps)) :bSweep false :bTeleport true)) (:CastFailed)))) (:CastFailed))) (:CastFailed))) (:"Is Not Valid")))) (:CastFailed))) (:CastFailed)))''','Index')
# Preserve the delivered retry and interface reset machinery. Only retire old independent health recovery.
write(gm,'MonitorAdventureHealth','')
write(d,'MonitorRound',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if {EQ('phase',PLAY)}
    (CallFunction|SelectCheckpoint :Index index)
    {S('ObservedIndex','index')} {S('ObservedAttempt','attempt')})
   (if {EQ('phase',FAIL)} (CallFunction|ScheduleRetry))) (:CastFailed)))''')
write(gm,'StartRound',f'''
 (if (and (Networking|HasAuthority) (and (>= Index 1) (<= Index 6)))
  (bind gs {GS} (:then {STATE}
   (if (and (>= (Class|BPCoopGameState|GetPlayerCount :self gs) 2) (<= (Class|BPCoopGameState|GetPlayerCount :self gs) 4))
    (if (or (and (== Index 1) {EQ('phase',LOBBY)}) (or (and (== Index index) {EQ('phase',FAIL)}) (and (== Index (+ index 1)) {EQ('phase',CLEAR)})))
     (CallFunction|CancelAllUses)
     (Class|BPCoopGameState|SetRoundState :self gs :RoundState (Utilities|Struct|MakeSRoundState :{I} Index :{P} {PLAY} :{A} (select (== Index index) (+ attempt 1) 1) :{T} 0.0 :{R} (CallFunction|ScalingRowForRoster)))
     {S('SixObservedRoster','(Class|BPCoopGameState|GetPlayerCount :self gs)')}
     (CallFunction|RefreshSixObjective)))) (:CastFailed)))''','Index')
write(gm,'RestoreRegroup',f'''
 (bind gs {GS} (:then {STATE}
  (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/Rounds/BP_RoundDirector.BP_RoundDirector_C")
   (bind director (Utilities|Casting|CastToBP_RoundDirector :Object item)
    (:then (Class|BPRoundDirector|RegroupRoster :self director :Index (select (<= index 1) 1 (select (<= index 3) 3 5)))) (:CastFailed)))) (:CastFailed))''')
write(gm,'ClearRound',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and {EQ('phase',PLAY)} (and (>= index 1) (<= index 6)))
    (if (< index 6)
     (CallFunction|CancelAllUses)
     (CallFunction|SetRoundPhase :Phase {CLEAR})
     (CallFunction|RestoreRegroup)
     (if (>= index 2) (CallFunction|StartRound :Index (+ index 1)))
     (else (if {V('MissionDelivered')}
      (CallFunction|CancelAllUses)
      (CallFunction|SetRoundPhase :Phase {COMPLETE})
      {S('MapTravelPending','true')}
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "TravelToResults" :Time 5.0 :bLooping false)))))) (:CastFailed)))''')
write(gm,'FailRound',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if {EQ('phase',PLAY)}
    (CallFunction|CancelAllUses)
    (Class|BPCoopGameState|SetRoundState :self gs :RoundState (Utilities|Struct|MakeSRoundState :{I} index :{P} {FAIL} :{A} attempt :{T} (+ (GameState|GetServerWorldTimeSeconds :self gs) 3.0) :{R} row))
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/Rounds/BP_RoundDirector.BP_RoundDirector_C")
     (bind director (Utilities|Casting|CastToBP_RoundDirector :Object item)
      (:then (Class|BPRoundDirector|ScheduleRetry :self director)) (:CastFailed))))) (:CastFailed)))''')
var(gm,'SixRosterStates',ue.PlayerState.static_class(),array=True)
write(gm,'SixRoundMonitor',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   {S('SixLiving','0')} {S('SixRoster','0')}
   (if (or {EQ('phase',LOBBY)} {EQ('phase',FAIL)})
    (Utilities|Array|Clear :TargetArray {V('SixRosterStates')})
    (for ps (Class|GameStateBase|GetPlayerArray :self gs) (Utilities|Array|AddUnique :TargetArray {V('SixRosterStates')} :NewItem ps)))
   (for state (Class|GameStateBase|GetPlayerArray :self gs)
    (bind pawn (PlayerState|GetPawn :self state))
    (Utilities|IsValid :InputObject pawn (:"Is Valid"
     (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "{HEALTH}"))
      (:then
       (if (and {EQ('phase',PLAY)} (not (Utilities|Array|ContainsItem :TargetArray {V('SixRosterStates')} :ItemToFind state)))
        (Class|ACHealth|SetHealth :self health :Health 0.0)
        (Class|ACHealth|SetDead :self health :bDead true)
        (Class|ACHealth|ApplyHealthState :self health)
        (Utilities|Array|AddUnique :TargetArray {V('SixRosterStates')} :NewItem state))
       {S('SixRoster',f'(+ {V("SixRoster")} 1)')}
       (if (not (Class|ACHealth|IsDead :self health)) {S('SixLiving',f'(+ {V("SixLiving")} 1)')})) (:CastFailed))) (:"Is Not Valid")))
   (if {EQ('phase',PLAY)}
    (if (or (< (Class|BPCoopGameState|GetPlayerCount :self gs) {V('SixObservedRoster')})
     (and (== {V('SixRoster')} (Class|BPCoopGameState|GetPlayerCount :self gs))
      (or (== {V('SixLiving')} 0)
       (or (and (== index 1) (< (+ {V('SixLiving')} (select (== row "2") 2 1)) (select (== row "4") 4 3)))
        (or (and (== index 3) (< {V('SixLiving')} (select (== row "2") 1 2)))
         (and (== index 5) (< {V('SixLiving')} (select (== row "4") 3 2))))))))
     (CallFunction|FailRound)))) (:CastFailed)))''')
write(gm,'BeginSixRounds','(if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "SixRoundMonitor" :Time 0.2 :bLooping true))')
write(gm,'RefreshSixObjective',f'''
 (bind gs {GS} (:then {STATE}
  (Class|BPCoopGameState|SetAreaName :self gs :AreaName "Cave")
  (Class|BPCoopGameState|SetAdventureInstruction :self gs :AdventureInstruction
   (select (== index 1) "The first room: press every plate together."
    (select (== index 2) "The maze: reach the meeting hall."
     (select (== index 3) "The meeting hall: light every lock at once."
      (select (== index 4) "The deep maze: reach the relic chamber."
       (select (== index 5) "The relic: hold the cage and lift the relic." "The escape: carry the relic to the first-room altar."))))))) (:CastFailed))''')
write(gm,'TravelToResults',f'''
 (if (and (Networking|HasAuthority) (and {V('MissionDelivered')} {V('MapTravelPending')}))
  (bind gs {GS} (:then {STATE}
   (if (and (== index 6) {EQ('phase',COMPLETE)})
    (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
     (:then
      (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 2)
      (Class|BPCoopGameInstance|SetRelicsCollected :self gi :RelicsCollected (Class|BPCoopGameState|GetRelicsCollected :self gs))
      (Class|BPCoopGameInstance|SetRelicsAvailable :self gi :RelicsAvailable (Class|BPCoopGameState|GetRelicsAvailable :self gs))
      (Class|BPCoopGameInstance|SetRunPrefixCollected :self gi :RunPrefixCollected (Class|BPCoopGameState|GetRelicsCollected :self gs))
      (Class|BPCoopGameInstance|SetRunPrefixAvailable :self gi :RunPrefixAvailable (Class|BPCoopGameState|GetRelicsAvailable :self gs))
      {S('MapTravelPending','false')}
      (Development|ExecuteConsoleCommand :Command "ServerTravel /Game/Maps/L_Site02?listen")) (:CastFailed)))) (:CastFailed)))''')
write(gm,'CompleteMap','(if (Networking|HasAuthority) (CallFunction|TravelToResults))')
# No volume or legacy map exit can bypass altar delivery.
ex=ue.load_asset('/Game/Puzzles/BP_MapExit');write(ex,'AdventureExitAllowed','(return false)');save(ex)
event(gm,'ReceiveBeginPlay','BeginSixRounds')
for bp in (gm,d):save(bp)
RESULT={'stage':'rounds','runtime_acceptance_pending':True}
