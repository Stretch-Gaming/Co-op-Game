"""Primary correction: revalidate live runtime dependencies before starting."""
import sys,importlib
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
start=ue.load_asset('/Game/Puzzles/Gauntlet/BP_HCGauntletStart')
body="(if (Networking|HasAuthority)\n (bind c (Utilities|Casting|CastToBP_HCGauntletCoordinator :Object (CallFunction|FindCoordinator))\n  (:then\n   (Class|BPHCGauntletCoordinator|RefreshState :self c)\n   (if (CallFunction|CanInteract :Instigator Instigator)\n    (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object Instigator)\n     (:then\n      (bind allowed (Class|BPCoopCharacter|UseAllowed :self pawn :Target self))\n      (if allowed\n       (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))\n        (:then (Class|BPCoopGameMode|StartRound :self gm :Index 3)) (:CastFailed))))\n     (:CastFailed))))\n  (:CastFailed)))"
write(start,'OnInteraction',body,'Instigator')
save(start)
snapshot([start],'primary-start-correction.json')
