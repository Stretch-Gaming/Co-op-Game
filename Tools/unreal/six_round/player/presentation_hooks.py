"""Primary-run behavior/presentation hooks; imports no source or art assets.

The other task owns /Game/Player/Art/Taker. Run only after its imported meshes
and assigned materials are ready. Original taking schedule/fade, ghost tick,
health, collision, round writers and audio graphs are preserved.
"""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from authoring import *
guard()
mesh_path=ARGS.get('taker_mesh','/Game/Player/Art/Taker/SM_Taker')
arm_path=ARGS.get('arm_mesh','/Game/Player/Art/Taker/SM_TakerArm')
taker_mesh=ue.load_asset(mesh_path);arm_mesh=ue.load_asset(arm_path)
assert isinstance(taker_mesh,ue.StaticMesh) and isinstance(arm_mesh,ue.StaticMesh),'Wait for the other task imported art; no placeholder import or disk copy'
assert len(taker_mesh.get_editor_property('static_materials'))==2 and len(arm_mesh.get_editor_property('static_materials'))==1
body_mat=ue.load_asset(ARGS['body_material']) if 'body_material' in ARGS else taker_mesh.get_material(0)
eyes_mat=ue.load_asset(ARGS['eyes_material']) if 'eyes_material' in ARGS else taker_mesh.get_material(1)
arm_mat=ue.load_asset(ARGS['arm_material']) if 'arm_material' in ARGS else arm_mesh.get_material(0)
for material in (body_mat,eyes_mat,arm_mat):assert material and material.get_path_name().startswith('/Game/Player/'),'Imported assigned lane materials must be ready'
floor_mat=ue.load_asset(ARGS.get('floor_material','/Game/Shared/Style/MI_Stylized_Rock'));assert floor_mat

# Render-only blackout is reconstructed on every world from server schedule.
view=ue.load_asset('/Game/Player/AC_PlayerView')
var(view,'VisualBlackoutUntil','float',-1.)
fn(view,'SetVisualBlackout',[('EndAt','float')]);fn(view,'IsVisualBlackout',outputs=[('Blackout','bool')]);fn(view,'ShouldRenderHeadlamp',outputs=[('Visible','bool')])
blackout_max=f'(Math|Float|Max(Float) :A {V("VisualBlackoutUntil")} :B EndAt)'
write(view,'SetVisualBlackout',S('VisualBlackoutUntil',blackout_max),'EndAt')
write(view,'IsVisualBlackout',f'''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then (return (< (GameState|GetServerWorldTimeSeconds :self gs) {V('VisualBlackoutUntil')}))) (:CastFailed (return false)))''')
write(view,'ShouldRenderHeadlamp',f'''
 (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self {OWNER} :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
  (:then (bind dead (Class|ACHealth|IsDead :self health)) (bind blackout (CallFunction|IsVisualBlackout))
   (return (and {V('HeadlampOn')} (and (not dead) (not blackout))))) (:CastFailed (return false)))''')
write(view,'ApplyHeadlamp',f'''
 (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
  (:then (bind light (Utilities|Casting|CastToSpotLightComponent :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Script/Engine.SpotLightComponent"))
   (:then (bind visible (CallFunction|ShouldRenderHeadlamp))
    (Rendering|Components|Light|SetIntensity :self light :NewIntensity (select visible 2500.0 0.0))
    (Transformation|SetWorldRotation :self light :NewRotation (Pawn|GetBaseAimRotation :self pawn))) (:CastFailed))) (:CastFailed))''')
save(view)

taking=ue.load_asset('/Game/Player/Taking/BP_TakingDirector')
for name,value in [('PresentationAttempt','int'),('PresentationStyleOffset','int'),('PresentationStyleNumber','int')]:
 var(taking,name,value,-1 if name=='PresentationAttempt' else 0)
fn(taking,'NextPresentationStyle',outputs=[('Style','int')])
write(taking,'NextPresentationStyle',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (if (!= attempt {V('PresentationAttempt')}) {S('PresentationAttempt','attempt')} {S('PresentationStyleNumber','0')} {S('PresentationStyleOffset','(Math|Random|RandomInteger :Max 3)')})
    (bind total (+ {V('PresentationStyleOffset')} {V('PresentationStyleNumber')}))
    (bind style (select (< total 3) total (- total 3)))
    {S('PresentationStyleNumber',f'(+ {V("PresentationStyleNumber")} 1)')}
    (return style)) (:CastFailed (return 0))) (else (return 0)))''')
arm,_=component(taking,'TakingArm',ue.StaticMeshComponent);arm.set_static_mesh(arm_mesh);arm.set_material(0,arm_mat)
arm.set_collision_profile_name('NoCollision');arm.set_editor_property('relative_scale3d',ue.Vector(1,1,1))
arm.set_mobility(ue.ComponentMobility.MOVABLE)
for name in ('TakingFloorLeft','TakingFloorRight'):
 slab,_=component(taking,name,ue.StaticMeshComponent);slab.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));slab.set_material(0,floor_mat)
 slab.set_editor_property('relative_scale3d',ue.Vector(.95,.7,.06));slab.set_collision_profile_name('NoCollision')
 slab.set_mobility(ue.ComponentMobility.MOVABLE)
void_path='/Game/Player/Taking/M_TakingVoid';void=ue.load_asset(void_path)
if not void:
 void=ue.AssetToolsHelpers.get_asset_tools().create_asset('M_TakingVoid','/Game/Player/Taking',ue.Material,ue.MaterialFactoryNew())
 assert void
 color=ue.MaterialEditingLibrary.create_material_expression(void,ue.MaterialExpressionConstant3Vector,-200,0)
 color.set_editor_property('constant',ue.LinearColor(.008,.011,.016,1))
 void.set_editor_property('shading_model',ue.MaterialShadingModel.MSM_UNLIT)
 assert ue.MaterialEditingLibrary.connect_material_property(color,'',ue.MaterialProperty.MP_EMISSIVE_COLOR)
 ue.MaterialEditingLibrary.recompile_material(void);assert ue.EditorAssetLibrary.save_loaded_asset(void,False)
hole,_=component(taking,'TakingFloorVoid',ue.StaticMeshComponent);hole.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Plane'));hole.set_material(0,void)
hole.set_editor_property('relative_scale3d',ue.Vector(1.9,1.9,1));hole.set_collision_profile_name('NoCollision')
hole.set_mobility(ue.ComponentMobility.MOVABLE)
body,_=component(taking,'TakingShadowBody',ue.StaticMeshComponent);body.set_static_mesh(taker_mesh);body.set_material(0,body_mat);body.set_material(1,eyes_mat);body.set_collision_profile_name('NoCollision')
body.set_mobility(ue.ComponentMobility.MOVABLE)
for name in ('RefreshTakingPresentation','BeginTakingPresentation','HideTakingPresentation'):fn(taking,name)
write(taking,'HideTakingPresentation',' '.join(f'(Rendering|SetVisibility :self {V(name)} :bNewVisibility false)' for name in ('TakingArm','TakingFloorLeft','TakingFloorRight','TakingFloorVoid','TakingShadowBody')))
write(taking,'RefreshTakingPresentation',f'''
 (Utilities|IsValid :InputObject {V('Victim')}
  (:"Is Valid" (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind age (- (GameState|GetServerWorldTimeSeconds :self gs) {V('TakingStarted')}))
    (bind active (and (>= age 0.0) (< age 0.65)))
    (bind outward (Math|Float|Clamp(Float) :Value (/ age 0.35) :Min 0.0 :Max 1.0))
    (bind inward (Math|Float|Clamp(Float) :Value (/ (- age 0.35) 0.3) :Min 0.0 :Max 1.0))
    (Transformation|SetActorRotation :NewRotation (Math|Rotator|MakeRotator :Yaw (+ (.yaw (Transformation|GetActorRotation :self {V('Victim')})) 180.0)))
    (Rendering|SetVisibility :self {V('TakingArm')} :bNewVisibility (and active (== {V('ScareStyle')} 0)))
    (Transformation|SetRelativeLocation :self {V('TakingArm')} :NewLocation (Utilities|Struct|MakeVector :X (- (+ -350.0 (* outward 101.0)) (* inward 180.0)) :Z -45.0) :bSweep false)
    (Rendering|SetVisibility :self {V('TakingFloorLeft')} :bNewVisibility (and active (== {V('ScareStyle')} 1)))
    (Rendering|SetVisibility :self {V('TakingFloorRight')} :bNewVisibility (and active (== {V('ScareStyle')} 1)))
    (Rendering|SetVisibility :self {V('TakingFloorVoid')} :bNewVisibility (and active (== {V('ScareStyle')} 1)))
    (Transformation|SetRelativeLocation :self {V('TakingFloorLeft')} :NewLocation (Utilities|Struct|MakeVector :Y (- 0.0 (+ 38.0 (* outward 95.0))) :Z 4.0) :bSweep false)
    (Transformation|SetRelativeLocation :self {V('TakingFloorRight')} :NewLocation (Utilities|Struct|MakeVector :Y (+ 38.0 (* outward 95.0)) :Z 4.0) :bSweep false)
    (Transformation|SetRelativeLocation :self {V('TakingFloorVoid')} :NewLocation (Utilities|Struct|MakeVector :Z 5.0) :bSweep false)
    (Rendering|SetVisibility :self {V('TakingShadowBody')} :bNewVisibility (and active (== {V('ScareStyle')} 2)))
    (Transformation|SetRelativeLocation :self {V('TakingShadowBody')} :NewLocation (Utilities|Struct|MakeVector :X (+ -210.0 (* outward 95.0)) :Z -176.0) :bSweep false)
    (Transformation|SetRelativeRotation :self {V('TakingShadowBody')} :NewRotation (Math|Rotator|MakeRotator :Pitch (* outward -24.0)) :bSweep false)
    (if (and active (and (== {V('ScareStyle')} 2) (>= age 0.2)))
     (for pawn (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
      (if (<= (Math|Vector|Distance(Vector) :V1 (Transformation|GetActorLocation :self pawn) :V2 {V('VictimOrigin')}) 1200.0)
       (bind playerView (Utilities|Casting|CastToAC_PlayerView :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Game/Player/AC_PlayerView.AC_PlayerView_C"))
        (:then (Class|ACPlayerView|SetVisualBlackout :self playerView :EndAt (+ {V('TakingStarted')} 1.1))) (:CastFailed)))))) (:CastFailed (CallFunction|HideTakingPresentation))))
  (:"Is Not Valid" (CallFunction|HideTakingPresentation)))''')
write(taking,'BeginTakingPresentation','(CallFunction|HideTakingPresentation) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshTakingPresentation" :Time 0.016 :bLooping true)')
event(taking,'ReceiveBeginPlay','BeginTakingPresentation');save(taking)

# A component BeginPlay preserves the parent's ghost BeginPlay/Tick entirely.
ghost=ue.load_asset('/Game/Player/Ghosts/BP_Ghost');cave=create('/Game/Player/Ghosts/BP_CaveBeing',ghost.generated_class())
BP.get_default_object(cave).set_editor_properties({'replicates':True,'replicate_movement':True})
cave_body,_=component(cave,'CaveBeingBody',ue.StaticMeshComponent);cave_body.set_static_mesh(taker_mesh);cave_body.set_material(0,body_mat);cave_body.set_material(1,eyes_mat)
cave_body.set_editor_properties({'relative_location':ue.Vector(0,0,-96),'relative_rotation':ue.Rotator(),'relative_scale3d':ue.Vector(1,1,1),'component_tags':[ue.Name('CaveBeingBody')]})
cave_body.set_collision_profile_name('NoCollision');cave_body.set_mobility(ue.ComponentMobility.MOVABLE)
fn(cave,'ApplyChaseSpeed')
chase_speed=f'(* {V("GhostSpeed")} 1.12)'
write(cave,'ApplyChaseSpeed',f'(if (Networking|HasAuthority) {S("GhostSpeed",chase_speed)})')
save(cave)
look=create('/Game/Player/Ghosts/AC_CaveBeingPresentation',ue.ActorComponent.static_class())
var(look,'bSpeedApplied','bool',False)
for name in ('HideParentGhostVisual','RefreshCaveBody','ApplyCaveSpeed','BeginCavePresentation'):fn(look,name)
write(look,'HideParentGhostVisual',f'''
 (for item (Actor|GetComponentsbyClass :self {OWNER} :ComponentClass "/Script/Engine.StaticMeshComponent")
  (bind mesh (Utilities|Casting|CastToStaticMeshComponent :Object item) (:then (Rendering|SetVisibility :self mesh :bNewVisibility false)) (:CastFailed)))
 (for item (Actor|GetComponentsbyTag :self {OWNER} :ComponentClass "/Script/Engine.StaticMeshComponent" :Tag "CaveBeingBody")
  (bind mesh (Utilities|Casting|CastToStaticMeshComponent :Object item) (:then (Rendering|SetVisibility :self mesh :bNewVisibility true)) (:CastFailed)))''')
write(look,'RefreshCaveBody',f'''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then (for item (Actor|GetComponentsbyTag :self {OWNER} :ComponentClass "/Script/Engine.StaticMeshComponent" :Tag "CaveBeingBody")
   (bind mesh (Utilities|Casting|CastToStaticMeshComponent :Object item)
    (:then (Transformation|SetRelativeLocation :self mesh :NewLocation (Utilities|Struct|MakeVector :Z (+ -96.0 (* (Math|Trig|Sin(Radians) :A (* (GameState|GetServerWorldTimeSeconds :self gs) 2.0)) 8.0))) :bSweep false)) (:CastFailed)))) (:CastFailed))''')
write(look,'ApplyCaveSpeed',f'''
 (if (and {AUTH_COMPONENT} (not {V('SpeedApplied')}))
  (bind pawn (Utilities|Casting|CastToBP_CaveBeing :Object {OWNER})
   (:then (Class|BPCaveBeing|ApplyChaseSpeed :self pawn) {S('SpeedApplied','true')}) (:CastFailed)))''')
write(look,'BeginCavePresentation','(CallFunction|HideParentGhostVisual) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ApplyCaveSpeed" :Time 0.05 :bLooping false) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshCaveBody" :Time 0.05 :bLooping true)')
event(look,'ReceiveBeginPlay','BeginCavePresentation');save(look)
component(cave,'CaveBeingPresentation',look.generated_class());save(cave)
chase=ue.load_asset('/Game/Player/Ghosts/BP_ChaseDirector')
fn(chase,'SpawnCaveBeingWaveMember',[('Location','Vector')])
write(chase,'SpawnCaveBeingWaveMember',f'''
 (if (Networking|HasAuthority)
  (bind spawned (Game|SpawnActorfromClass :Class "/Game/Player/Ghosts/BP_CaveBeing.BP_CaveBeing_C" :SpawnTransform (Math|Transform|MakeTransform :Location Location) :CollisionHandlingOverride "AlwaysSpawn")
   (:then (Actor|SetLifeSpan :self spawned :InLifespan 45.0) (Utilities|Array|Add :TargetArray {V('WaveGhosts')} :NewItem spawned))))''','Location')
save(chase)
RESULT={'writes':['/Game/Player/AC_PlayerView','/Game/Player/Taking/BP_TakingDirector','/Game/Player/Taking/M_TakingVoid','/Game/Player/Ghosts/BP_CaveBeing','/Game/Player/Ghosts/AC_CaveBeingPresentation','/Game/Player/Ghosts/BP_ChaseDirector'],'readonly_imported_art':[mesh_path,arm_path,body_mat.get_path_name(),eyes_mat.get_path_name(),arm_mat.get_path_name()],'art_imports':False,'preserved':'Taking server schedule, immune/teleport and owning fade; original Ghost parent BeginPlay/Tick; existing chase/audio/round phase functions','remaining_primary_hooks':['SpawnWave odd member calls SpawnCaveBeingWaveMember(Location); existing ghost branch stays for even members. No wave-count/timing change.','TakePlayer sets ScareStyle from NextPresentationStyle instead of independent RandomInteger; server offset cycles three distinct styles for at most three victims, resetting on each attempt.'],'unverified':'Native inherited GhostSpeed getter and component APIs need primary compile; camera/body/floor/blackout art needs rendered split/client review; cave-being eye dim depends on imported eye shader and is not claimed','runtime_acceptance_pending':True}
(QUEUE/'presentation-hooks.json').write_text(json.dumps(RESULT,indent=2))
