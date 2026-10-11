"""Primary-executed resource softlock monitor; parent core lifecycle owns retries.
Does not spawn/refund/restore anything. The only failure action is FailRound.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
guard();gm=ue.load_asset('/Game/Core/BP_CoopGameMode')
for name,kind,value in [('SixResourceLiving','int',0),('SixResourceStatues','int',0),('SixResourceFlares','int',0),('SixResourceActiveFlares','int',0),('SixResourceConfigured','bool',False)]:var(gm,name,kind,value)
for name in ('MonitorSixResources','StartSixResourceMonitor'):fn(gm,name)
write(gm,'MonitorSixResources',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and {EQ('phase',PLAY)} (or (== index 1) (== index 3)))
    {S('SixResourceLiving','0')} {S('SixResourceFlares','0')}
    (for state (Class|GameStateBase|GetPlayerArray :self gs)
     (bind pawn (PlayerState|GetPawn :self state))
     (Utilities|IsValid :InputObject pawn (:"Is Valid"
      (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
       (:then (if (not (Class|ACHealth|IsDead :self health))
        {S('SixResourceLiving',f'(+ {V("SixResourceLiving")} 1)')}
        (bind tools (Utilities|Casting|CastToAC_Tools :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Player/Tools/AC_Tools.AC_Tools_C"))
         (:then {S('SixResourceFlares',f'(+ {V("SixResourceFlares")} (Class|ACTools|GetFlaresLeft :self tools))')}) (:CastFailed)))) (:CastFailed))) (:"Is Not Valid")))
    (if (== index 1)
     {S('SixResourceConfigured','false')} {S('SixResourceStatues','0')}
     (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_PuzzleSetup.BP_PuzzleSetup_C")
      (bind puzzle (Utilities|Casting|CastToBP_PuzzleSetup :Object item)
       (:then (if (and (Class|BPPuzzleSetup|GetReady :self puzzle) (== (Class|BPPuzzleSetup|GetConfiguredAttempt :self puzzle) attempt))
        {S('SixResourceConfigured','true')})) (:CastFailed)))
     (for statue (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_Statue.BP_Statue_C")
      (Utilities|IsValid :InputObject statue (:"Is Valid"
       (bind (x y z) (Math|Vector|BreakVector :InVec (Transformation|GetActorLocation :self statue)))
       (if (>= z -1700.0) {S('SixResourceStatues',f'(+ {V("SixResourceStatues")} 1)')})) (:"Is Not Valid")))
     (if (and {V('SixResourceConfigured')} (< (+ {V('SixResourceLiving')} {V('SixResourceStatues')}) (select (== row "4") 4 3)))
      (CallFunction|FailRound)))
    (if (== index 3)
     {S('SixResourceActiveFlares','0')}
     (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Player/Tools/BP_Flare.BP_Flare_C")
      (bind flare (Utilities|Casting|CastToBP_Flare :Object item)
       (:then (if (Class|BPFlare|IsActive :self flare) {S('SixResourceActiveFlares',f'(+ {V("SixResourceActiveFlares")} 1)')})) (:CastFailed)))
     (if (or (< {V('SixResourceLiving')} (select (== row "2") 1 2))
      (< (+ {V('SixResourceFlares')} {V('SixResourceActiveFlares')}) (select (== row "4") 2 1)))
      (CallFunction|FailRound))))) (:CastFailed)))''')
write(gm,'StartSixResourceMonitor','(if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "MonitorSixResources" :Time 0.2 :bLooping true))')
event(gm,'ReceiveBeginPlay','StartSixResourceMonitor');save(gm)
RESULT={'writes':['/Game/Core/BP_CoopGameMode'],'resource_failures':'R1 configured puzzle needs living+valid above-lost-height statues >= plate count; R3 needs beam-capable living and available/active flare capacity','recover_only_through':'FailRound -> 3s checkpoint/ResetForRound','individual_refunds_or_spawns':False,'runtime_acceptance_pending':True}
