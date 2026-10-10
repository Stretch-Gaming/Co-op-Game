(fn CompleteFor (Pawn) (if (Networking|HasAuthority)
 (CallFunction|RefreshState)
 (bind allowed (CallFunction|HasProgress :Pawn Pawn))
 (if (and allowed (Variables|Default|GetDependencyReady))
  (bind found (CallFunction|FindBridge))
  (bind bridge (Utilities|Casting|CastToBP_HCGauntletGateBridge :Object found) (:then
   (bind requested (Class|BPHCGauntletGateBridge|RequestLatch :self bridge :Index 3 :Attempt (Variables|Default|GetCurrentAttempt)))
   (if requested
    (bind latched (Class|BPHCGauntletGateBridge|QueryLatch :self bridge :Index 3 :Attempt (Variables|Default|GetCurrentAttempt)))
    (if latched
     (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode)) (:then
      (Variables|Default|SetCompleted true) (Variables|Default|SetCompletionCount (+ (Variables|Default|GetCompletionCount) 1))
      (Class|BPCoopGameMode|ClearRound :self gm) (return true)) (:CastFailed (return false)))
     (else (return false))) (else (return false)))) (:CastFailed (return false)))
  (else (return false)))
 (else (return false))))