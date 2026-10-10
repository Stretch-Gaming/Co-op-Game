(fn OnInteraction (Instigator) (if (Networking|HasAuthority)
 (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object Instigator) (:then
  (if (Class|BPCoopCharacter|UseAllowed :self pawn :Target self)
   (bind found (CallFunction|FindCoordinator))
   (bind c (Utilities|Casting|CastToBP_HCGauntletCoordinator :Object found)
    (:then (Class|BPHCGauntletCoordinator|CompleteFor :self c :Pawn pawn)) (:CastFailed)))) (:CastFailed))))