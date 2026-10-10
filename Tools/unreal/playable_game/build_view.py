import sys
import importlib
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *

guard()
if ARGS.get('resume'):
    original_write=write
    def write(bp,name,body,parameters=''):
        if not ARGS.get('finish_defaults') and name not in ('ToggleView','ToggleHeadlamp','OnRep_ViewMode','OnRep_bHeadlampOn','ApplyHeadlamp','ApplyCameraArm','ApplyCameraFov','ApplyLocalCamera','ApplyViewState'):
            return original_write(bp,name,body,parameters)
view=ue.load_asset('/Game/Player/AC_PlayerView')
next_view=f'(select (== {V("ViewMode")} 0) 1 0)'
next_lamp=f'(not {V("HeadlampOn")})'
write(view,'ToggleView',f'(if {AUTH_COMPONENT} {S("ViewMode",next_view)} (CallFunction|ApplyViewState))')
write(view,'ToggleHeadlamp',f'(if {AUTH_COMPONENT} {S("HeadlampOn",next_lamp)} (CallFunction|ApplyViewState))')
write(view,'OnRep_ViewMode','(CallFunction|ApplyViewState)')
write(view,'OnRep_bHeadlampOn','(CallFunction|ApplyViewState)')
for name in ('ApplyHeadlamp','ApplyLocalCamera','ApplyCameraArm','ApplyCameraFov'):
    fn(view,name)
write(view,'ApplyHeadlamp',f"""
 (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
  (:then (bind light (Utilities|Casting|CastToSpotLightComponent :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Script/Engine.SpotLightComponent"))
   (:then
    (Rendering|Components|Light|SetIntensity :self light :NewIntensity (select {V('HeadlampOn')} 2500.0 0.0))
    (Transformation|SetWorldRotation :self light :NewRotation (Pawn|GetBaseAimRotation :self pawn))) (:CastFailed))) (:CastFailed))""")
write(view,'ApplyCameraArm',f"""
 (bind arm (Utilities|Casting|CastToSpringArmComponent :Object (Actor|GetComponentbyClass :self {OWNER} :ComponentClass "/Script/Engine.SpringArmComponent"))
  (:then
   (Class|SpringArmComponent|SetTargetArmLength :self arm :TargetArmLength (Math|Interpolation|FInterpTo :Current (Class|SpringArmComponent|GetTargetArmLength :self arm) :Target (select (== {V('ViewMode')} 0) 0.0 380.0) :DeltaTime (Utilities|Time|GetWorldDeltaSeconds) :InterpSpeed 12.0))
   (Class|SpringArmComponent|SetSocketOffset :self arm :SocketOffset (Utilities|Struct|MakeVector :X 0.0 :Y (select (== {V('ViewMode')} 0) 0.0 45.0) :Z 65.0))) (:CastFailed))""")
write(view,'ApplyCameraFov',f"""
 (bind camera (Utilities|Casting|CastToCameraComponent :Object (Actor|GetComponentbyClass :self {OWNER} :ComponentClass "/Script/Engine.CameraComponent"))
  (:then (Camera|SetFieldOfView :self camera :InFieldOfView (select (== {V('ViewMode')} 0) 90.0 80.0))) (:CastFailed))""")
write(view,'ApplyLocalCamera',f"""
 (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
  (:then (if (Pawn|IsLocallyControlled :self pawn)
   (bind first (== {V('ViewMode')} 0))
   (Class|Pawn|SetUseControllerRotationYaw :self pawn :bUseControllerRotationYaw first)
   (Class|CharacterMovementComponent|SetOrientRotationtoMovement :self (Class|Character|GetCharacterMovement :self pawn) :bOrientRotationToMovement (not first))
   (Rendering|Components|Primitive|SetOwnerNoSee :self (Class|Character|GetMesh :self pawn) :bNewOwnerNoSee first)
   (CallFunction|ApplyCameraArm)
   (CallFunction|ApplyCameraFov))) (:CastFailed))""")
write(view,'ApplyViewState','(CallFunction|ApplyHeadlamp) (CallFunction|ApplyLocalCamera)')
var(view,'PlayerColor','LinearColor',ue.LinearColor(1,1,1,1))
fn(view,'ApplyTeamMarkerColors')
write(view,'ApplyTeamMarkerColors',f"""
 (for marker (Actor|GetComponentsbyTag :self {OWNER} :ComponentClass "/Script/Engine.StaticMeshComponent" :Tag "CoopTeamIndicator")
  (bind mesh (Utilities|Casting|CastToStaticMeshComponent :Object marker)
   (:then
    (bind material (Rendering|Material|CreateDynamicMaterialInstance :self mesh :ElementIndex 0))
    (Rendering|Material|SetVectorParameterValue :self material :ParameterName "Color" :Value {V('PlayerColor')})) (:CastFailed)))""")
write(view,'ApplyColorSlot',f"""
 (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
  (:then
   (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object (Class|Pawn|GetPlayerState :self pawn))
    (:then
     (bind slot (Class|BPCoopPlayerState|GetColorSlot :self ps))
     (if (and (>= slot 0) (not (== slot {V('LastColorSlot')})))
      {S('LastColorSlot','slot')}
      {S('PlayerColor','(select (== slot 0) (Utilities|Struct|MakeLinearColor :R 0.9 :G 0.22 :B 0.18 :A 1.0) (select (== slot 1) (Utilities|Struct|MakeLinearColor :R 0.12 :G 0.75 :B 0.65 :A 1.0) (select (== slot 2) (Utilities|Struct|MakeLinearColor :R 0.85 :G 0.65 :B 0.1 :A 1.0) (Utilities|Struct|MakeLinearColor :R 0.55 :G 0.25 :B 0.85 :A 1.0))))')}
      (CallFunction|ApplyTeamMarkerColors))) (:CastFailed))) (:CastFailed))""")
write(view,'RefreshView','(CallFunction|ApplyViewState) (CallFunction|ApplyColorSlot)')
write(view,'StartView','(CallFunction|RefreshView) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshView" :Time 0.05 :bLooping true)')
event(view,'ReceiveBeginPlay','StartView')
save(view)

character=ue.load_asset('/Game/Core/BP_CoopCharacter')
marker,handle=component(character,'TeamIndicator',ue.StaticMeshComponent)
marker.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Sphere'))
marker.set_material(0,ue.load_asset('/Engine/BasicShapes/BasicShapeMaterial'))
marker.set_editor_property('relative_location',ue.Vector(45,0,25))
marker.set_editor_property('relative_scale3d',ue.Vector(.18,.18,.18))
marker.set_editor_property('component_tags',[ue.Name('CoopTeamIndicator')])
marker.set_collision_profile_name('NoCollision')
marker.set_owner_no_see(True)
marker.set_cast_shadow(False)
movement=BP.get_default_object(character).get_editor_property('character_movement')
assert movement.get_outer()==BP.get_default_object(character)
movement.set_editor_properties({'jump_z_velocity':760.0,'gravity_scale':1.6,'max_step_height':45.0,'air_control':.35})
compile_bp(character)
RESULT={'first_person_default':True,'view_toggle_headlamp_peer_aim_written':True,'color_slots_supported':4,'compiled':True,'runtime_acceptance_pending':True}
(QUEUE/'view-build.json').write_text(json.dumps(RESULT,indent=2))
