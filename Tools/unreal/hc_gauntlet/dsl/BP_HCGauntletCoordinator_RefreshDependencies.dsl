(fn RefreshDependencies () 
 (Variables|Default|SetDependencyReady false)
 (bind found (CallFunction|FindBridge))
 (bind bridge (Utilities|Casting|CastToBP_HCGauntletGateBridge :Object found)
  (:then (bind supported (Class|BPHCGauntletGateBridge|SupportsLatch :self bridge))
   (bind gate (CallFunction|FindGate))
   (Utilities|IsValid :InputObject gate (:"Is Valid"
    (Variables|Default|SetDependencyReady (and supported (or (not (Class|BPHCGauntletGateBridge|GetFixtureOnly :self bridge)) (Variables|Default|GetAllowFixtureBridge))))))) (:CastFailed)))