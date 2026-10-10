(fn ApplyBlend ()
  (bind boom (Variables|Default|GetBoom))
  (Utilities|IsValid boom
    (:"Is Valid"
      (bind a (Variables|Default|GetViewBlend))
      (Class|SpringArmComponent|SetTargetArmLength :self boom :TargetArmLength (Math|Float|Lerp :A 0.0 :B (Variables|Default|GetThirdPersonArmLength) :Alpha a))
      (Transformation|SetRelativeLocation boom :NewLocation (Math|Vector|Lerp(Vector) :A (Variables|Default|GetFirstPersonOffset) :B (Variables|Default|GetThirdPersonOffset) :Alpha a))
      (bind body (Variables|Default|GetBody))
      (Utilities|IsValid body
        (:"Is Valid"
          (Rendering|SetOwnerNoSee body :bNewOwnerNoSee (< a (Variables|Default|GetHideBodyBelow))))))))
