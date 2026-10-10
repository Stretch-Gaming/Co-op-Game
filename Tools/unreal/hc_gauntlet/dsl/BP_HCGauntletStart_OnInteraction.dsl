(fn OnInteraction (Instigator) (if (Networking|HasAuthority)
 (bind c (Utilities|Casting|CastToBP_HCGauntletCoordinator :Object (CallFunction|FindCoordinator))
  (:then
   (Class|BPHCGauntletCoordinator|RefreshState :self c)
   (if (CallFunction|CanInteract :Instigator Instigator)
    (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object Instigator)
     (:then
      (bind allowed (Class|BPCoopCharacter|UseAllowed :self pawn :Target self))
      (if allowed
       (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
        (:then (Class|BPCoopGameMode|StartRound :self gm :Index 3)) (:CastFailed))))
     (:CastFailed))))
  (:CastFailed))))