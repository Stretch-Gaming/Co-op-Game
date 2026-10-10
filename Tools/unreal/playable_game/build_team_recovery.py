import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
gm=ue.load_asset('/Game/Core/BP_CoopGameMode');var(gm,'HealthyPlayers','int',0);var(gm,'HealthRosterPlayers','int',0);fn(gm,'MonitorAdventureHealth');fn(gm,'StartAdventureHealthMonitor')
write(gm,'MonitorAdventureHealth',f'''
 (if (Networking|HasAuthority)
  {S('HealthyPlayers','0')} {S('HealthRosterPlayers','0')}
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (for ps (Class|GameStateBase|GetPlayerArray :self gs)
     (bind pawn (PlayerState|GetPawn :self ps))
     (Utilities|IsValid :InputObject pawn
      (:"Is Valid"
       (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
        (:then
         {S('HealthRosterPlayers',f'(+ {V("HealthRosterPlayers")} 1)')}
         (bind downed (Class|ACHealth|IsDowned :self health))
         (if (not downed) {S('HealthyPlayers',f'(+ {V("HealthyPlayers")} 1)')})) (:CastFailed))) (:"Is Not Valid")))
    (if (and (and (>= {V('HealthRosterPlayers')} 2) (== {V('HealthyPlayers')} 0)) (== {V('HealthRosterPlayers')} (Class|BPCoopGameState|GetPlayerCount :self gs)))
     (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
     (if (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1"))
      (CallFunction|FailRound)
      (else (if (or (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator0")) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2")))
       (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/Rounds/BP_RoundDirector.BP_RoundDirector_C")
        (bind director (Utilities|Casting|CastToBP_RoundDirector :Object item)
         (:then (Class|BPRoundDirector|RecoverRoster :self director)) (:CastFailed)))))))) (:CastFailed)))''')
write(gm,'StartAdventureHealthMonitor','(if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "MonitorAdventureHealth" :Time 0.2 :bLooping true))')
event(gm,'ReceiveBeginPlay','StartAdventureHealthMonitor');save(gm)
progress=create('/Game/Puzzles/Maze/BP_MazeProgress',ue.Actor.static_class());var(progress,'LowestY','float',0);var(progress,'SafeStage','int',0)
for name in ('MonitorMaze','BeginMaze'):fn(progress,name)
write(progress,'MonitorMaze',f'''
 (if (Networking|HasAuthority)
  {S('LowestY','999999.0')}
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (for state (Class|GameStateBase|GetPlayerArray :self gs)
     (bind pawn (PlayerState|GetPawn :self state))
     (Utilities|IsValid :InputObject pawn
      (:"Is Valid" (bind (x y z) (Math|Vector|BreakVector :InVec (Transformation|GetActorLocation :self pawn)))
       {S('LowestY',f'(Math|Float|Min(Float) :A {V("LowestY")} :B y)')}) (:"Is Not Valid" {S('LowestY','-1000.0')})))
    (if (>= (Class|BPCoopGameState|GetPlayerCount :self gs) 2)
     (if (and (> {V('LowestY')} 9100.0) (< {V('SafeStage')} 1)) {S('SafeStage','1')})
     (if (and (> {V('LowestY')} 15400.0) (< {V('SafeStage')} 2)) {S('SafeStage','2')})
     (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_Checkpoint.BP_Checkpoint_C")
      (bind checkpoint (Utilities|Casting|CastToBP_Checkpoint :Object item)
       (:then (if (and (== (Class|BPCheckpoint|GetRoundIndex :self checkpoint) 1) (> {V('SafeStage')} 0))
        (Transformation|SetActorLocation :self checkpoint :NewLocation (select (== {V('SafeStage')} 1) (Math|Vector|MakeVector :Y 9400.0 :Z -200.0) (Math|Vector|MakeVector :Y 15500.0 :Z 500.0)) :bSweep false :bTeleport true))) (:CastFailed))))) (:CastFailed)))''')
write(progress,'BeginMaze','(if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "MonitorMaze" :Time 0.2 :bLooping true))')
event(progress,'ReceiveBeginPlay','BeginMaze');save(progress)
RESULT={'whole_team_down_recovery':True,'maze_safe_meeting_points':True,'runtime_acceptance_pending':True}
