import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
ghost=ue.load_asset('/Game/Player/Ghosts/BP_Ghost')
if not ARGS.get('view_only'):
    var(ghost,'LightUntil','float',-1,replicated=True);var(ghost,'GlowMaterial',ue.MaterialInstanceDynamic.static_class())
    fn(ghost,'RepelFromLight',[('PlayerPawn',ue.Pawn.static_class())]);fn(ghost,'RefreshLightVisual');fn(ghost,'BeginLightVisual')
    write(ghost,'RepelFromLight',f'''
     (if (Networking|HasAuthority)
      (Utilities|IsValid :InputObject PlayerPawn
       (:"Is Valid" {S('Target','PlayerPawn')}
        {S('BackoffUntil',f'(Math|Float|Max(Float) :A {V("BackoffUntil")} :B (+ (Utilities|Time|GetGameTimeinSeconds) 0.6))')}
        (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
         (:then {S('LightUntil','(+ (GameState|GetServerWorldTimeSeconds :self gs) 0.6)')}) (:CastFailed))) (:"Is Not Valid")))''','PlayerPawn')
    fn(ghost,'ApplyLightMaterial')
    write(ghost,'ApplyLightMaterial',f'''
     (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
      (:then (bind lit (< (GameState|GetServerWorldTimeSeconds :self gs) {V('LightUntil')}))
       (Rendering|Material|SetScalarParameterValue :self {V('GlowMaterial')} :ParameterName "EmissiveStrength" :Value (select lit 0.45 1.6))
       (Rendering|Material|SetScalarParameterValue :self {V('GlowMaterial')} :ParameterName "BodyOpacity" :Value (select lit 0.35 0.7))) (:CastFailed))''')
    write(ghost,'RefreshLightVisual',f'''
     (Utilities|IsValid :InputObject {V('GlowMaterial')}
      (:"Is Valid" (CallFunction|ApplyLightMaterial))
      (:"Is Not Valid"
       (bind material (Rendering|Material|CreateDynamicMaterialInstance :self {V('GhostMesh')} :ElementIndex 0))
       {S('GlowMaterial','material')} (CallFunction|ApplyLightMaterial)))''')
    write(ghost,'BeginLightVisual','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshLightVisual" :Time 0.1 :bLooping true)')
    event(ghost,'ReceiveBeginPlay','BeginLightVisual');save(ghost)
view=ue.load_asset('/Game/Player/AC_PlayerView');var(view,'LightGhost',ghost.generated_class());var(view,'LightLockUntil','float',0);var(view,'BestLightScore','float',0)
fn(view,'GhostInLight',[('Candidate',ghost.generated_class())],[('Visible','bool')]);fn(view,'ChooseLightGhost');fn(view,'ApplyGhostLight')
write(view,'GhostInLight',f'''
 (Utilities|IsValid :InputObject Candidate
  (:"Is Valid"
   (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
    (:then
     (bind (eye rotation) (Actor|GetActorEyesViewPoint :self pawn))
     (bind forward (Math|Vector|GetForwardVector :InRot (Pawn|GetBaseAimRotation :self pawn)))
     (bind destination (Transformation|GetActorLocation :self Candidate))
     (bind distance (Math|Vector|VectorLength :A (- destination eye)))
     (bind score (Math|Vector|DotProduct :A forward :B (Math|Vector|Normalize :A (- destination eye))))
     (if (and (<= distance 1200.0) (>= score 0.88295))
      (bind (hit blocked) (Collision|LineTraceByChannel :Start (+ eye (* forward 70.0)) :End destination :TraceChannel "TraceTypeQuery1" :bIgnoreSelf true :DrawDebugType "None"))
      (bind (blocking overlap time hitDistance location impact normal impactNormal material hitActor component bone myBone item element face traceStart traceEnd) (Collision|BreakHitResult :Hit hit))
      (return (or (not blocked) (== hitActor Candidate)))
      (else (return false)))) (:CastFailed (return false)))) (:"Is Not Valid" (return false)))''','Candidate')
write(view,'ChooseLightGhost',f'''
 {S('LightGhost','"None"')} {S('BestLightScore','0.88295')}
 (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
  (:then
   (bind (eye rotation) (Actor|GetActorEyesViewPoint :self pawn))
   (bind forward (Math|Vector|GetForwardVector :InRot (Pawn|GetBaseAimRotation :self pawn)))
   (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Player/Ghosts/BP_Ghost.BP_Ghost_C")
    (bind candidate (Utilities|Casting|CastToBP_Ghost :Object item)
     (:then
      (bind visible (CallFunction|GhostInLight :Candidate candidate))
      (if visible
       (bind score (Math|Vector|DotProduct :A forward :B (Math|Vector|Normalize :A (- (Transformation|GetActorLocation :self candidate) eye))))
       (if (> score {V('BestLightScore')}) {S('BestLightScore','score')} {S('LightGhost','candidate')}))) (:CastFailed)))
   {S('LightLockUntil','(+ (Utilities|Time|GetGameTimeinSeconds) 0.5)')}) (:CastFailed))''')
write(view,'ApplyGhostLight',f'''
 (if (and {AUTH_COMPONENT} {V('HeadlampOn')})
  (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
   (:then
    (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
     (:then
      (bind downed (Class|ACHealth|IsDowned :self health))
      (if (not downed)
       (bind visible (CallFunction|GhostInLight :Candidate {V('LightGhost')}))
       (if (or (not visible) (>= (Utilities|Time|GetGameTimeinSeconds) {V('LightLockUntil')})) (CallFunction|ChooseLightGhost))
       (Utilities|IsValid :InputObject {V('LightGhost')}
        (:"Is Valid" (Class|BPGhost|RepelFromLight :self {V('LightGhost')} :PlayerPawn pawn)) (:"Is Not Valid")))) (:CastFailed))) (:CastFailed)))''')
write(view,'RefreshView','(CallFunction|ApplyViewState) (CallFunction|ApplyColorSlot) (CallFunction|ApplyGhostLight)');save(view)
RESULT={'one_ghost_per_headlamp':True,'clear_cone_and_wall_check':True,'selection_lock_seconds':.5,'replicated_dim':True,'runtime_acceptance_pending':True}
(QUEUE/'headlamp-ghost-build.json').write_text(json.dumps(RESULT,indent=2))
