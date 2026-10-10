(event EventBeginPlay
  (CallFunction|FindViewParts)
  (CallFunction|ApplyViewState)
  (Variables|Default|SetViewBlend (select (Math|Byte|Equal(Byte) (Variables|Default|GetViewMode) 1) 1.0 0.0))
  (CallFunction|ApplyBlend)
  (Pawn|AssignReceiveControllerChangedDelegate (Variables|Default|GetOwnerCharacter) (AddEvent|Custom|ReceiveControllerChangedDelegate_Event)))

(event Custom|ReceiveControllerChangedDelegate_Event (Pawn OldController NewController)
  (CallFunction|ApplyViewState))

(event EventTick (DeltaSeconds)
  (bind _returnvalue 1)
  (bind _returnvalue_1 1.0)
  (bind _returnvalue_2 0.0)
  (bind _viewmode (Variables|Default|GetViewMode))
  (bind _returnvalue_3 (Math|Byte|Equal(Byte) _viewmode _returnvalue))
  (bind _returnvalue_4 (select _returnvalue_3 _returnvalue_1 _returnvalue_2))
  (bind _output_get (Variables|Default|SetViewBlend (Math|Interpolation|FInterpTo_Constant (Variables|Default|GetViewBlend) _returnvalue_4 DeltaSeconds (Variables|Default|GetBlendSpeed))))
  (CallFunction|ApplyBlend)
  (if (== _output_get _returnvalue_4)
    (Components|Tick|SetComponentTickEnabled self)))

(event Custom|Server_ToggleView
  (CallFunction|FlipViewMode))

