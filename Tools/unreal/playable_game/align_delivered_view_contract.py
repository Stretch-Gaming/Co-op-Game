import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
view=ue.load_asset('/Game/Player/AC_PlayerView');var(view,'LocalViewInitialized','bool',False)
write(view,'ApplyCameraArm',f'''
 (bind arm (Utilities|Casting|CastToSpringArmComponent :Object (Components|GetComponentbyClass :self {OWNER} :ComponentClass "/Script/Engine.SpringArmComponent"))
  (:then
   (bind target (select (== {V('ViewMode')} 0) 0.0 380.0))
   (Class|SpringArmComponent|SetTargetArmLength :self arm :TargetArmLength (select {V('LocalViewInitialized')} (Math|Interpolation|FInterptoConstant :Current (Class|SpringArmComponent|GetTargetArmLength :self arm) :Target target :DeltaTime 0.05 :InterpSpeed 1266.6667) target))
   (Class|SpringArmComponent|SetSocketOffset :self arm :SocketOffset (Math|Vector|MakeVector :Y (select (== {V('ViewMode')} 0) 0.0 45.0) :Z 65.0))) (:CastFailed))''')
write(view,'ApplyCameraFov',f'''
 (bind camera (Utilities|Casting|CastToCameraComponent :Object (Components|GetComponentbyClass :self {OWNER} :ComponentClass "/Script/Engine.CameraComponent"))
  (:then (Camera|SetFieldOfView :self camera :InFieldOfView (select (== {V('ViewMode')} 0) 90.0 75.0))) (:CastFailed))''')
write(view,'ApplyLocalCamera',f'''
 (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
  (:then
   (bind first (== {V('ViewMode')} 0))
   (Class|Pawn|SetUseControllerRotationYaw :self pawn :bUseControllerRotationYaw first)
   (Class|CharacterMovementComponent|SetOrientRotationtoMovement :self (Class|Character|GetCharacterMovement :self pawn) :bOrientRotationToMovement (not first))
   (if (Pawn|IsLocallyControlled :self pawn)
    (Rendering|Components|Primitive|SetOwnerNoSee :self (Class|Character|GetMesh :self pawn) :bNewOwnerNoSee first)
    (CallFunction|ApplyCameraArm) (CallFunction|ApplyCameraFov) {S('LocalViewInitialized','true')})) (:CastFailed))''')
save(view)
character=ue.load_asset('/Game/Core/BP_CoopCharacter');mesh=BP.get_default_object(character).get_editor_property('mesh');assert mesh.get_outer()==BP.get_default_object(character);mesh.set_editor_property('cast_hidden_shadow',True);save(character)
RESULT={'first_view_snaps_at_possession':True,'later_switches_glide_seconds':.3,'facing_mode_applied_on_every_peer':True,'third_person_fov':75,'runtime_acceptance_pending':True}
