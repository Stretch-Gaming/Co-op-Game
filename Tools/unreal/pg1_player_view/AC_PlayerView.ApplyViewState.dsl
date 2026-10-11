(fn ApplyViewState ()
  (bind ch (Variables|Default|GetOwnerCharacter))
  (Utilities|IsValid ch
    (:"Is Valid"
      (bind third (== (Variables|Default|GetViewMode) 1))
      (Class|Pawn|SetUseControllerRotationYaw :self ch :bUseControllerRotationYaw (not third))
      (Class|CharacterMovementComponent|SetOrientRotationtoMovement :self (Class|Character|GetCharacterMovement ch) :bOrientRotationToMovement third)
      (if (Pawn|IsLocallyControlled ch)
        (Components|Tick|SetComponentTickEnabled self :bEnabled true)
        (else
          (Variables|Default|SetViewBlend (select third 1.0 0.0))
          (CallFunction|ApplyBlend))))))
