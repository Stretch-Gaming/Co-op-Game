(fn ValidatePawn (Pawn) 
 (Utilities|IsValid :InputObject Pawn (:"Is Valid"
  (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object Pawn) (:then
   (bind pc (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController :self pawn)) (:then
    (Utilities|IsValid :InputObject (Class|Pawn|GetPlayerState :self pawn) (:"Is Valid"
     (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState)) (:then
      (return (and (and (== (Pawn|GetControlledPawn :self pc) pawn)
                       (== (Class|Controller|GetPlayerState :self pc) (Class|Pawn|GetPlayerState :self pawn)))
                   (and (Utilities|Array|ContainsItem :TargetArray (Class|GameStateBase|GetPlayerArray :self gs) :ItemToFind (Class|Pawn|GetPlayerState :self pawn))
                        (and (not (Actor|ActorHasTag :self pawn :Tag "Downed")) (not (Class|BPCoopCharacter|GetInteractionBlocked :self pawn)))))))
      (:CastFailed (return false)))) (:"Is Not Valid" (return false))))
    (:CastFailed (return false)))) (:CastFailed (return false))))
  (:"Is Not Valid" (return false))))