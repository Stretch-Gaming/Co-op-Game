(fn CanInteract (Instigator) (bind found (CallFunction|FindCoordinator))
 (bind c (Utilities|Casting|CastToBP_HCGauntletCoordinator :Object found)
 (:then (bind allowed (Class|BPHCGauntletCoordinator|HasProgress :self c :Pawn Instigator)) (return allowed)) (:CastFailed (return false))))