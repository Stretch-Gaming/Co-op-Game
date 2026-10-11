(fn FindViewParts ()
  (bind owner (Components|GetOwner))
  (bind ch (Utilities|Casting|CastToCharacter :Object owner)
    (:then
      (Variables|Default|SetOwnerCharacter ch)
      (Variables|Default|SetBody (Class|Character|GetMesh ch))
      (bind arm (Utilities|Casting|CastToSpringArmComponent :Object (Actor|GetComponentbyClass ch :ComponentClass "/Script/Engine.SpringArmComponent"))
        (:then
          (Variables|Default|SetBoom arm)
          (Variables|Default|SetThirdPersonArmLength (Class|SpringArmComponent|GetTargetArmLength arm))
          (Variables|Default|SetThirdPersonOffset (Class|SceneComponent|GetRelativeLocation arm))
          (bind cam (Utilities|Casting|CastToCameraComponent :Object (Actor|GetComponentbyClass ch :ComponentClass "/Script/Engine.CameraComponent"))
            (:then
              (Variables|Default|SetViewCamera cam))
            (:CastFailed)))
        (:CastFailed)))
    (:CastFailed)))
