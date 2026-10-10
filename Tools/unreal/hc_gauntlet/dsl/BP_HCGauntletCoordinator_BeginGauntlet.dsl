(fn BeginGauntlet () (if (Networking|HasAuthority)
 (CallFunction|RefreshState)
 (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "UpdateProgress" :Time 0.1 :bLooping true)))