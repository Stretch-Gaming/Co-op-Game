import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
guard()
bp=ue.load_asset('/Game/Player/Ghosts/BP_ChaseDirector');ghost=ue.load_asset('/Game/Player/Ghosts/BP_Ghost')
var(bp,'WaveSize','int',2);var(ghost,'BestDist','float',2000.);var(ghost,'BestPawn',ue.Pawn.static_class())
fn(ghost,'IsInFlareGlow',[('Candidate',ue.Actor.static_class())],[('Safe','bool')]);fn(ghost,'RefreshFlareRepulsion')
write(ghost,'IsPlayerDowned','''
 (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self Player :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
  (:then (bind dead (Class|ACHealth|IsDead :self health)) (return dead)) (:CastFailed (return true)))''','Player')
write(ghost,'IsInFlareGlow','''
 (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Player/Tools/BP_Flare.BP_Flare_C")
  (bind active (Class|BPFlare|IsActive :self actor))
  (if (and active (<= (Transformation|GetDistanceTo :self Candidate :OtherActor actor) 450.0)) (return true)))
 (return false)''','Candidate')
write(ghost,'UpdateTarget',f'''
 (if (Networking|HasAuthority)
  {S('BestDist','2500.0')} {S('BestPawn','"None"')}
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
     (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object actor)
      (:then (bind dead (CallFunction|IsPlayerDowned :Player pawn))
       (bind safe (CallFunction|IsInFlareGlow :Candidate pawn))
       (bind distance (Transformation|GetDistanceTo :OtherActor pawn))
       (if (and (not dead) (and (not safe) (<= distance 2500.0)))
        (bind carrying (Class|BPCoopCharacter|GetCarryingRelic :self pawn))
        (if (and (== index 6) carrying) {S('BestPawn','pawn')} {S('BestDist','-1.0')}
         (else (if (< distance {V('BestDist')}) {S('BestPawn','pawn')} {S('BestDist','distance')}))))) (:CastFailed)))
    {S('Target',V('BestPawn'))}) (:CastFailed {S('Target','"None"')})))''')
write(ghost,'RefreshFlareRepulsion',f'''
 (if (Networking|HasAuthority)
  (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Player/Tools/BP_Flare.BP_Flare_C")
   (bind active (Class|BPFlare|IsActive :self actor))
   (if (and active (< (Transformation|GetDistanceTo :OtherActor actor) 450.0))
    {S('BackoffUntil','(+ (Utilities|Time|GetGameTimeinSeconds) 0.2)')}
    (Transformation|SetActorLocation :NewLocation (+ (Transformation|GetActorLocation) (* (Math|Vector|Normalize :A (- (Transformation|GetActorLocation) (Transformation|GetActorLocation :self actor))) 25.0)) :bSweep false))))''')
fn(ghost,'BeginFlareRepulsion');write(ghost,'BeginFlareRepulsion','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshFlareRepulsion" :Time 0.05 :bLooping true)')
event(ghost,'ReceiveBeginPlay','BeginFlareRepulsion');save(ghost)
write(bp,'ClearChase',f'''
 (if (Networking|HasAuthority) (for actor {V('WaveGhosts')}
  (Utilities|IsValid :InputObject actor (:"Is Valid" (Actor|DestroyActor :self actor)) (:"Is Not Valid")))
  (Utilities|Array|Clear :TargetArray {V('WaveGhosts')}) {S('WaveNumber','0')})''')
write(bp,'SpawnWave',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind row (Class|BPCoopGameState|GetScalingRow :self gs))
    {S('WaveSize','(select (== row "2") 2 (select (== row "3") 3 (select (== row "4") 4 0)))')}
    (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
     (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object actor)
      (:then (bind carrying (Class|BPCoopCharacter|GetCarryingRelic :self pawn))
       (if carrying
        (for i (range {V('WaveSize')})
         (bind spawned (Game|SpawnActorfromClass :Class "/Game/Player/Ghosts/BP_Ghost.BP_Ghost_C" :SpawnTransform (Math|Transform|MakeTransform :Location (+ (Transformation|GetActorLocation :self pawn) (Utilities|Struct|MakeVector :X (select (== i 0) -1500.0 1500.0) :Y (* i 250.0) :Z 100.0))) :CollisionHandlingOverride "AlwaysSpawn")
          (:then (Actor|SetLifeSpan :self spawned :InLifespan 45.0) (Utilities|Array|Add :TargetArray {V('WaveGhosts')} :NewItem spawned)))))) (:CastFailed)))
    {S('WaveNumber',f'(+ {V("WaveNumber")} 1)')}
    {S('LastWaveAt','(GameState|GetServerWorldTimeSeconds :self gs)')}) (:CastFailed)))''')
write(bp,'RefreshChase',f'''
 (if (Networking|HasAuthority) (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
   (if (and (== index 6) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")))
    (if (!= attempt {V('SpawnedAttempt')}) (CallFunction|ClearChase) {S('SpawnedAttempt','attempt')} {S('LastWaveAt','-100.0')})
    (if (>= (- (GameState|GetServerWorldTimeSeconds :self gs) {V('LastWaveAt')}) 20.0) (CallFunction|SpawnWave))
    (else (CallFunction|ClearChase) {S('SpawnedAttempt','-1')}))) (:CastFailed)))''')
fn(bp,'ResetChase',[('Index','int'),('Attempt','int')]);write(bp,'ResetChase','(CallFunction|ClearChase)','Index Attempt')
write(bp,'BeginChase','(if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshChase" :Time 0.2 :bLooping true))')
event(bp,'ResetForRound','ResetChase',['Index','Attempt']);event(bp,'ReceiveBeginPlay','BeginChase');save(bp)
RESULT={'stage':'carrier chase','runtime_acceptance_pending':True,'cave_beings':'same replicated ghost family, distinct art/speed pending','scaling_fallback':'GetScalingRow -> waves2/3/4,20 seconds'}

