import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
from editor_toolset.toolsets.blueprint import _BlueprintCache
health=ue.load_asset('/Game/Hazards/AC_Health');ue.load_asset('/Game/Hazards/DT_HazardScaling');_BlueprintCache.invalidate(health)
write(health,'GetReviveSeconds','''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then
   (bind data (Utilities|GetDataTableRow :DataTable "/Game/Hazards/DT_HazardScaling.DT_HazardScaling" :RowName (Class|BPCoopGameState|GetScalingRow :self gs))
    (:then (bind (spikes darts swing revive) (Utilities|Struct|BreakSHazardScaling :S_HazardScaling data)) (return revive)) (:RowNotFound (return 3.0)))) (:CastFailed (return 3.0)))''')
save(health)
proxy=ue.load_asset('/Game/Puzzles/Recovery/BP_HCReviveTarget');var(proxy,'TargetPawn',ue.Pawn.static_class(),replicated=True)
BP.set_variable_replication(proxy,'HoldSeconds',ue.BlueprintVariableReplication.REPLICATED)
cdo=BP.get_default_object(proxy);cdo.set_editor_property('replicates',True);cdo.set_editor_property('replicate_movement',True);cdo.set_editor_property('always_relevant',True)
mesh,handle=component(proxy,'StaticMeshComponent',ue.StaticMeshComponent);mesh.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Sphere'));mesh.set_editor_property('relative_scale3d',ue.Vector(.7,.7,.7));mesh.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Gold'));mesh.set_collision_profile_name('BlockAllDynamic');mesh.set_editor_property('cast_shadow',False)
fn(proxy,'CanRevive',[('Instigator',ue.Actor.static_class())],[('Allowed','bool')]);fn(proxy,'FinishRevive',[('Instigator',ue.Actor.static_class())])
for name in ('RefreshReviveTarget','BeginReviveTarget','EndReviveTarget'):fn(proxy,name)
write(proxy,'CanRevive',f'''
 (Utilities|IsValid :InputObject {V('TargetPawn')}
  (:"Is Valid"
   (if (and (not (== Instigator {V('TargetPawn')})) (<= (Transformation|GetDistanceTo :self {V('TargetPawn')} :OtherActor Instigator) 400.0))
    (bind targetHealth (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self {V('TargetPawn')} :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
     (:then
      (bind targetDown (Class|ACHealth|IsDowned :self targetHealth))
      (bind helper (Utilities|Casting|CastToPawn :Object Instigator)
       (:then
        (bind helperHealth (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self helper :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
         (:then (bind helperDown (Class|ACHealth|IsDowned :self helperHealth)) (return (and targetDown (not helperDown)))) (:CastFailed (return false)))) (:CastFailed (return false)))) (:CastFailed (return false))))
   (return false)) (:"Is Not Valid" (return false)))''','Instigator')
write(proxy,'CanInteract','(bind allowed (CallFunction|CanRevive :Instigator Instigator)) (return allowed)','Instigator')
write(proxy,'GetInteractInfo',f'(return "Hold E to revive your teammate" {V("HoldSeconds")} (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator1"))','Instigator')
write(proxy,'FinishRevive',f'''
 (if (Networking|HasAuthority)
  (bind allowed (CallFunction|CanRevive :Instigator Instigator))
  (if allowed
   (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self {V('TargetPawn')} :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
    (:then (Class|ACHealth|Revive :self health :Reviver Instigator)) (:CastFailed))))''','Instigator')
write(proxy,'RefreshReviveTarget',f'''
 (Utilities|IsValid :InputObject {V('TargetPawn')}
  (:"Is Valid"
   (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self {V('TargetPawn')} :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
    (:then
     (bind downed (Class|ACHealth|IsDowned :self health))
     (Actor|SetActorHiddenInGame :bNewHidden (not downed)) (Collision|SetActorEnableCollision :bNewActorEnableCollision downed)
     (if (Networking|HasAuthority)
      (bind seconds (Class|ACHealth|GetReviveSeconds :self health)) {S('HoldSeconds','seconds')}
      (Transformation|SetActorLocation :NewLocation (+ (Transformation|GetActorLocation :self {V('TargetPawn')}) (Math|Vector|MakeVector :X 90.0 :Z -20.0)) :bSweep false :bTeleport true))) (:CastFailed)))
  (:"Is Not Valid" (if (Networking|HasAuthority) (Actor|DestroyActor))))''')
write(proxy,'BeginReviveTarget','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshReviveTarget" :Time 0.1 :bLooping true)')
write(proxy,'EndReviveTarget','(Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RefreshReviveTarget")')
event(proxy,'Interact','FinishRevive',['Instigator']);event(proxy,'ReceiveBeginPlay','BeginReviveTarget');event(proxy,'ReceiveEndPlay','EndReviveTarget');save(proxy)
character=ue.load_asset('/Game/Core/BP_CoopCharacter')
write(character,'CreateReviveTarget',f'''
 (if (Networking|HasAuthority)
  (Utilities|IsValid :InputObject {V('ReviveTarget')}
   (:"Is Valid")
   (:"Is Not Valid"
    (bind target (Game|SpawnActorfromClass :Class "/Game/Puzzles/Recovery/BP_HCReviveTarget.BP_HCReviveTarget_C" :SpawnTransform (Transformation|GetActorTransform) :Owner self :CollisionHandlingOverride "AlwaysSpawn")
     (:then {S('ReviveTarget','target')} (Class|BPHCReviveTarget|SetTargetPawn :self target :TargetPawn self))))))''')
write(character,'RefreshAdventurePlayer','''
 (if (Networking|HasAuthority)
  (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (bind downed (Class|ACHealth|IsDowned :self health))
    (CallFunction|SetInteractionBlocked :Blocked downed)
    (if downed (CallFunction|ReleaseCarried) (CallFunction|UnbraceOnServer))) (:CastFailed)))''')
write(character,'AdventurePlayerBegin','(CallFunction|CreateReviveTarget) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshAdventurePlayer" :Time 0.1 :bLooping true)')
write(character,'AdventurePlayerEnd',f'''
 (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RefreshAdventurePlayer")
 (if (Networking|HasAuthority)
  (Utilities|IsValid :InputObject {V('ReviveTarget')} (:"Is Valid" (Actor|DestroyActor :self {V('ReviveTarget')})) (:"Is Not Valid")))''')
event(character,'ReceiveBeginPlay','AdventurePlayerBegin');event(character,'ReceiveEndPlay','AdventurePlayerEnd');save(character)
director=ue.load_asset('/Game/Puzzles/Rounds/BP_RoundDirector')
write(director,'PreparePlayerForCheckpoint','''
 (bind player (Utilities|Casting|CastToBP_CoopCharacter :Object PlayerPawn)
  (:then (Class|BPCoopCharacter|CancelUse :self player) (Class|BPCoopCharacter|ReleaseCarried :self player) (Class|BPCoopCharacter|UnbraceOnServer :self player)
   (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self player :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
    (:then (Class|ACHealth|ResetHealth :self health) (Class|BPCoopCharacter|SetInteractionBlocked :self player :Blocked false)) (:CastFailed))) (:CastFailed))''','PlayerPawn')
save(director)
RESULT={'timed_revive':True,'scaled_revive_time':True,'downed_uses_and_carry_cancelled':True,'checkpoint_resets_health':True,'runtime_acceptance_pending':True}
(QUEUE/'recovery-build.json').write_text(json.dumps(RESULT,indent=2))
