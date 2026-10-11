import sys,importlib,json
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
guard()
bp=ue.load_asset('/Game/Player/Taking/BP_TakingDirector')
positions=json.loads((HERE/'world/positions.json').read_text())['first_path_starts']
for slot,pos in enumerate(positions):var(bp,'PathStart'+str(slot),'Vector',ue.Vector(*pos))
var(bp,'NextTakingAt','float',-1.);var(bp,'VisualStarted','float',-1.)
var(bp,'VictimOrigin','Vector',ue.Vector(),replicated=True)
var(bp,'EligiblePlayers',ue.Actor.static_class(),array=True);var(bp,'bSealed','bool',False)
fn(bp,'ChooseRemainingPlayer')
write(bp,'ChooseRemainingPlayer',f'''
 (Utilities|Array|Clear :TargetArray {V('EligiblePlayers')})
 (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
  (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self actor :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (bind dead (Class|ACHealth|IsDead :self health))
    (if (not dead) (Utilities|Array|Add :TargetArray {V('EligiblePlayers')} :NewItem actor))) (:CastFailed)))
 (if (> (Utilities|Array|Length :TargetArray {V('EligiblePlayers')}) 0)
  (bind chosen (Utilities|Array|Get(acopy) {V('EligiblePlayers')} (Math|Random|RandomInteger :Max (Utilities|Array|Length :TargetArray {V('EligiblePlayers')}))))
  (bind pawn (Utilities|Casting|CastToPawn :Object chosen)
   (:then (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object (Class|Pawn|GetPlayerState :self pawn))
    (:then {S('RemainingSlot','(Class|BPCoopPlayerState|GetColorSlot :self ps)')}) (:CastFailed))) (:CastFailed)))''')
arm,handle=component(bp,'TakingArm',ue.StaticMeshComponent)
arm.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));arm.set_editor_property('relative_scale3d',ue.Vector(.15,3.,.15));arm.set_collision_profile_name('NoCollision')
write(bp,'TakePlayer',f'''
 (if (Networking|HasAuthority)
  (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object PlayerPawn)
   (:then {S('Victim','pawn')} {S('Teleported','false')} {S('VictimOrigin','(Transformation|GetActorLocation :self pawn)')}
    (Class|BPCoopCharacter|SetTakingProtected :self pawn :Protected true)
    (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
     (:then {S('TakingStarted','(+ (GameState|GetServerWorldTimeSeconds :self gs) 0.5)')}
      {S('ScareStyle','(Math|Random|RandomInteger :Max 3)')}) (:CastFailed))) (:CastFailed)))''','PlayerPawn')
write(bp,'MoveVictimToPath',f'''
 (if (and (Networking|HasAuthority) (not {V('Teleported')}))
  (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object {V('Victim')})
   (:then (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object (Class|Pawn|GetPlayerState :self pawn))
    (:then (bind slot (Class|BPCoopPlayerState|GetColorSlot :self ps))
     (if (and (>= slot 0) (<= slot 3))
      (Transformation|SetActorLocation :self pawn :NewLocation (select (== slot 0) {V('PathStart0')} (select (== slot 1) {V('PathStart1')} (select (== slot 2) {V('PathStart2')} {V('PathStart3')}))) :bSweep false :bTeleport true)
      {S('Teleported','true')})) (:CastFailed))) (:CastFailed)))''')
fn(bp,'UnprotectVictim')
write(bp,'UnprotectVictim',f'''
 (if (Networking|HasAuthority)
  (Utilities|IsValid :InputObject {V('Victim')}
   (:"Is Valid" (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object {V('Victim')})
    (:then (Class|BPCoopCharacter|SetTakingProtected :self pawn :Protected false)) (:CastFailed))) (:"Is Not Valid")))''')
write(bp,'FinishTaking',f'(if (Networking|HasAuthority) (CallFunction|UnprotectVictim) {S("Victim",chr(34)+"None"+chr(34))} {S("TakingStarted","-1.0")})')
fn(bp,'CanTake',[('PlayerPawn',ue.Actor.static_class())],[('Allowed','bool')])
fn(bp,'HasActiveVictim',outputs=[('Active','bool')])
write(bp,'HasActiveVictim',f'(Utilities|IsValid :InputObject {V("Victim")} (:"Is Valid" (return true)) (:"Is Not Valid" (return false)))')
write(bp,'CanTake','''
 (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self PlayerPawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
  (:then (bind dead (Class|ACHealth|IsDead :self health)) (return (not dead))) (:CastFailed (return false)))''','PlayerPawn')
write(bp,'ScheduleNext',f'''
 (if (Networking|HasAuthority)
  (for slot (range 4)
   (if (and (>= slot {V('NextSlot')}) (and (!= slot {V('RemainingSlot')}) (not (CallFunction|HasActiveVictim))))
    (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
     (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object actor)
      (:then (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object (Class|Pawn|GetPlayerState :self pawn))
       (:then (bind playerSlot (Class|BPCoopPlayerState|GetColorSlot :self ps))
        (bind allowed (CallFunction|CanTake :PlayerPawn pawn))
        (if (and allowed (and (== slot playerSlot) (not (CallFunction|HasActiveVictim))))
         (CallFunction|TakePlayer :PlayerPawn pawn) {S('NextSlot','(+ slot 1)')})) (:CastFailed))) (:CastFailed)))))
  (if (not (CallFunction|HasActiveVictim)) {S('NextSlot','4')}
   (else (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
    (:then {S('NextTakingAt','(+ (GameState|GetServerWorldTimeSeconds :self gs) (Math|Random|RandomFloatinRange :Min 2.0 :Max 5.0))')}) (:CastFailed)))))''')
fn(bp,'ProcessTakingPlayer')
write(bp,'ProcessTakingPlayer',f'''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then (bind now (GameState|GetServerWorldTimeSeconds :self gs))
   (Utilities|IsValid :InputObject {V('Victim')}
    (:"Is Valid" (if (>= (- now {V('TakingStarted')}) 0.65) (CallFunction|MoveVictimToPath))
     (if (>= (- now {V('TakingStarted')}) 1.3) (CallFunction|FinishTaking)))
    (:"Is Not Valid" (if (and (>= now {V('NextTakingAt')}) (< {V('NextSlot')} 4)) (CallFunction|ScheduleNext))))) (:CastFailed))''')
write(bp,'PlayTakingVisual',f'''
 (Utilities|IsValid :InputObject {V('Victim')}
  (:"Is Valid" (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind age (- (GameState|GetServerWorldTimeSeconds :self gs) {V('TakingStarted')}))
    (Actor|SetActorHiddenInGame :bNewHidden (or (< age 0.0) (> age 0.65)))
    (Transformation|SetActorLocation :NewLocation (+ {V('VictimOrigin')} (Utilities|Struct|MakeVector :Z (select (== {V('ScareStyle')} 1) -100.0 80.0))) :bSweep false)
    (bind pawn (Utilities|Casting|CastToPawn :Object {V('Victim')})
     (:then (if (Pawn|IsLocallyControlled :self pawn)
      (bind pc (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController :self pawn))
       (:then (bind camera (Class|PlayerController|GetPlayerCameraManager :self pc))
        (Camera|Fading|SetManualCameraFade :self camera :InFadeAmount (select (and (>= age 0.35) (< age 1.15)) 1.0 0.0) :Color (Utilities|Struct|MakeLinearColor :R 0.0 :G 0.0 :B 0.0) :bInFadeAudio true)) (:CastFailed)))) (:CastFailed))) (:CastFailed)))
  (:"Is Not Valid" (Actor|SetActorHiddenInGame :bNewHidden true)))''')
fn(bp,'TakingAuthorityTick')
write(bp,'TakingAuthorityTick',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (bind now (GameState|GetServerWorldTimeSeconds :self gs))
    (if (and (== index 2) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")))
     (if (!= {V('StartedAttempt')} attempt)
      (CallFunction|FinishTaking) {S('StartedAttempt','attempt')} {S('NextSlot','0')}
      (CallFunction|ChooseRemainingPlayer) {S('Sealed','false')}
      {S('NextTakingAt','(+ now 1.0)')})
     (if (== attempt 1)
      (CallFunction|ProcessTakingPlayer)
      (if (and (not {V('Sealed')}) (and (>= {V('NextSlot')} 4) (not (CallFunction|HasActiveVictim))))
       (for seal (Actor|GetAllActorsOfClass :ActorClass "/Game/Hazards/Maze/BP_MouthSeal.BP_MouthSeal_C")
        (Class|BPMouthSeal|SealAllBut :self seal :PathIndex {V('RemainingSlot')})) {S('Sealed','true')}))
     (else (CallFunction|FinishTaking)))) (:CastFailed)))''')
write(bp,'RefreshTaking','(CallFunction|TakingAuthorityTick) (CallFunction|PlayTakingVisual)')
fn(bp,'ResetTaking',[('Index','int'),('Attempt','int')]);write(bp,'ResetTaking','(CallFunction|FinishTaking)','Index Attempt')
write(bp,'BeginTaking','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshTaking" :Time 0.05 :bLooping true)')
event(bp,'ResetForRound','ResetTaking',['Index','Attempt']);event(bp,'ReceiveBeginPlay','BeginTaking');save(bp)
RESULT={'stage':'taking schedule','runtime_acceptance_pending':True,'visuals':'three greybox styles, owning victim fade; polished hand/floor/light-cut art pending'}
