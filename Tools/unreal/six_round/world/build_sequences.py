"""Server-triggered replicated schedules for the second paths. Editor authoring only."""
import sys,importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import authoring;importlib.reload(authoring)
from authoring import *
guard()
bp=create('/Game/Hazards/Traps/BP_SprintSequence',ue.Actor.static_class())
cdo=BP.get_default_object(bp);cdo.set_editor_property('replicates',True);cdo.set_editor_property('always_relevant',True)
for name,kind,value,rep,editable in [('Kind','int',0,False,True),('StartTime','float',-1,True,False),('Now','float',0,False,False),('Age','float',-1,False,False),('Span','float',350,False,True),('WarningTime','float',1.4,True,True),('RunSpeed','float',420,True,True),('Damage','float',100,False,True),('NextHit','float',0,False,False),('ScalingRow','name',ue.Name('None'),False,False)]:var(bp,name,kind,value,replicated=rep,editable=editable)
var(bp,'LastCosmeticStart','float',-1)
trigger,_=component(bp,'TriggerZone',ue.BoxComponent);trigger.set_box_extent(ue.Vector(180,210,140));trigger.set_editor_property('relative_location',ue.Vector(-440,0,120));trigger.set_collision_profile_name('OverlapAllDynamic');trigger.set_editor_property('generate_overlap_events',True)
damage,_=component(bp,'DamageZone',ue.BoxComponent);damage.set_box_extent(ue.Vector(160,220,180));damage.set_editor_property('relative_location',ue.Vector(0,0,150));damage.set_collision_profile_name('OverlapAllDynamic');damage.set_editor_property('generate_overlap_events',True)
for i in range(7):
    plank,_=component(bp,'Plank'+str(i),ue.StaticMeshComponent);plank.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));plank.set_editor_property('relative_scale3d',ue.Vector(.55,4.9,.2));plank.set_editor_property('relative_location',ue.Vector((i-3)*50,0,-10));plank.set_mobility(ue.ComponentMobility.MOVABLE);plank.set_collision_profile_name('BlockAll');plank.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Wood'))
rock,_=component(bp,'MovingRock',ue.StaticMeshComponent);rock.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Sphere'));rock.set_editor_property('relative_scale3d',ue.Vector(1.8,1.8,1.8));rock.set_editor_property('relative_location',ue.Vector(-700,0,90));rock.set_collision_profile_name('NoCollision');rock.set_mobility(ue.ComponentMobility.MOVABLE);rock.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Rock'))
warning,_=component(bp,'WarningStrip',ue.StaticMeshComponent);warning.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));warning.set_editor_property('relative_scale3d',ue.Vector(9,4.8,.04));warning.set_editor_property('relative_location',ue.Vector(0,0,3));warning.set_collision_profile_name('NoCollision');warning.set_mobility(ue.ComponentMobility.MOVABLE);warning.set_material(0,ue.load_asset('/Game/Hazards/Art/SixRoundMaze/Materials/MI_SixRound_TrapWarning'))
for i in range(6):
    wing,_=component(bp,'BatWing'+str(i),ue.StaticMeshComponent)
    wing.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cone'))
    wing.set_editor_property('relative_scale3d',ue.Vector(.6,.16,.15))
    wing.set_editor_property('relative_location',ue.Vector(0,0,160))
    wing.set_collision_profile_name('NoCollision');wing.set_mobility(ue.ComponentMobility.MOVABLE)
    wing.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Wood'))
for n in ('SRSequenceBeginSequence','SRSequenceRefreshSequence','SRSequenceApplySequenceVisual','SRSequenceTriggerSequence','SRSequenceDamageSequence','SRSequenceResetSchedule','SRSequenceApplySequenceScaling'):fn(bp,n)
write(bp,'SRSequenceApplySequenceScaling',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind row (Class|BPCoopGameState|GetScalingRow :self gs))
    (if (!= row {V('ScalingRow')})
     {S('ScalingRow','row')}
     (if (== row "2") {S('RunSpeed','380.0')})
     (if (== row "3") {S('RunSpeed','400.0')})
     (if (== row "4") {S('RunSpeed','420.0')}))) (:CastFailed)))''')
write(bp,'SRSequenceResetSchedule',f'''(if (Networking|HasAuthority) {S('StartTime','-1.0')} {S('NextHit','0.0')} (CallFunction|SRSequenceRefreshSequence))''')
write(bp,'SRSequenceTriggerSequence',f'''
 (if (and (Networking|HasAuthority) (< {V('StartTime')} 0.0))
  (bind bodies (Collision|GetOverlappingActors :self {V('TriggerZone')} :ClassFilter "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C"))
  (if (> (Utilities|Array|Length :TargetArray bodies) 0)
   {S('StartTime',V('Now'))} {S('NextHit','0.0')}))''')
write(bp,'SRSequenceDamageSequence',f'''
 (if (Networking|HasAuthority)
  (bind damageGS (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (bind (damageIndex damagePhase damageAttempt damageEnds damageRow) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self damageGS)))
    (if (and (Utilities|Enum|Equal(Enum) damagePhase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")) (and (>= {V('StartTime')} 0.0) (and (>= {V('Age')} {V('WarningTime')}) (< {V('Age')} (+ {V('WarningTime')} 4.0)))))
     (if (and (or (== {V('Kind')} 1) (and (== {V('Kind')} 2) (and (>= (- {V('Age')} {V('WarningTime')}) 1.2) (< (- {V('Age')} {V('WarningTime')}) 1.7)))) (>= {V('Now')} {V('NextHit')}))
      {S('NextHit','(+ (Variables|Default|GetNow) 0.3)')}
      (for body (Collision|GetOverlappingActors :self {V('DamageZone')} :ClassFilter "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
       (Game|Damage|ApplyDamage :DamagedActor body :BaseDamage {V('Damage')} :DamageCauser self))))) (:CastFailed)))''')
body=f'''(bind bridge (== {V('Kind')} 0))
 (bind armed (>= {V('StartTime')} 0.0))
 (bind dangerAge (- {V('Age')} {V('WarningTime')}))
 (Rendering|SetVisibility :self {V('WarningStrip')} :bNewVisibility (and armed (and (>= {V('Age')} 0.0) (< {V('Age')} {V('WarningTime')}))))
'''
for i in range(7):
    body+=f'''(Rendering|SetVisibility :self {V('Plank'+str(i))} :bNewVisibility bridge)
 (bind dropped{i} (and armed (>= dangerAge {i*.15+.25:.2f})))
 (if bridge
  (if dropped{i}
   (Transformation|SetRelativeLocation :self {V('Plank'+str(i))} :NewLocation (Math|Vector|MakeVector :X {i*50-150:.1f} :Y 0.0 :Z -410.0) :bSweep false :bTeleport true)
   (else (Transformation|SetRelativeLocation :self {V('Plank'+str(i))} :NewLocation (Math|Vector|MakeVector :X {i*50-150:.1f} :Y 0.0 :Z -10.0) :bSweep false :bTeleport true)))
  (Collision|SetCollisionEnabled :self {V('Plank'+str(i))} :NewType "QueryAndPhysics")
  (else (Collision|SetCollisionEnabled :self {V('Plank'+str(i))} :NewType "NoCollision")))
'''
body+=f'''(Rendering|SetVisibility :self {V('MovingRock')} :bNewVisibility (and armed (and (not bridge) (and (>= dangerAge 0.0) (< dangerAge 4.0)))))
 (if (== {V('Kind')} 1)
  (bind offset (Math|Vector|MakeVector :X (+ -700.0 (* (Math|Float|Clamp(Float) :Value dangerAge :Min 0.0 :Max 4.0) {V('RunSpeed')})) :Y 0.0 :Z 90.0))
  (Transformation|SetRelativeLocation :self {V('MovingRock')} :NewLocation offset :bSweep false :bTeleport true)
  (Transformation|SetRelativeLocation :self {V('DamageZone')} :NewLocation offset :bSweep false :bTeleport true)
  (Transformation|SetRelativeRotation :self {V('MovingRock')} :NewRotation (Math|Rotator|MakeRotator :Pitch (* dangerAge 200.0)) :bSweep false :bTeleport true))
 (if (== {V('Kind')} 2)
  (Transformation|SetRelativeLocation :self {V('MovingRock')} :NewLocation (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (Math|Float|Max(Float) :A 80.0 :B (- 650.0 (* dangerAge 450.0)))) :bSweep false :bTeleport true)
  (Transformation|SetRelativeLocation :self {V('DamageZone')} :NewLocation (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 140.0) :bSweep false :bTeleport true))
 (if (== {V('Kind')} 3)
  (Transformation|SetRelativeLocation :self {V('MovingRock')} :NewLocation (Math|Vector|MakeVector :X (* dangerAge 400.0) :Y (* dangerAge 300.0) :Z (+ 120.0 (* dangerAge 160.0))) :bSweep false :bTeleport true))
'''
for i in range(6):
    body+=f'''(Rendering|SetVisibility :self {V('BatWing'+str(i))} :bNewVisibility (and (== {V('Kind')} 3) (and armed (and (>= dangerAge 0.0) (< dangerAge 3.0)))))
 (Transformation|SetRelativeLocation :self {V('BatWing'+str(i))} :NewLocation (Math|Vector|MakeVector :X (+ {i*25:.1f} (* dangerAge 450.0)) :Y (+ {i*50-125:.1f} (* dangerAge {100+i*30:.1f})) :Z (+ {140+i*25:.1f} (* dangerAge 160.0))) :bSweep false :bTeleport true)
 (Transformation|SetRelativeRotation :self {V('BatWing'+str(i))} :NewRotation (Math|Rotator|MakeRotator :Roll (* (Math|Trig|Sin(Radians) :A (+ (* dangerAge 20.0) {i*.8:.1f})) 45.0)) :bSweep false :bTeleport true)
'''
body+=f'''(if (and armed (!= {V('LastCosmeticStart')} {V('StartTime')}))
 {S('LastCosmeticStart',V('StartTime'))}
 (if (== {V('Kind')} 3)
  (Audio|PlaySoundatLocation :Sound "/Game/Hazards/Art/Audio/SFX_SwingLog_Whoosh.SFX_SwingLog_Whoosh" :Location (Transformation|GetActorLocation))
  (else (Audio|PlaySoundatLocation :Sound "/Game/Hazards/Art/Audio/SFX_Spikes_Arm.SFX_Spikes_Arm" :Location (Transformation|GetActorLocation)))))
'''
write(bp,'SRSequenceApplySequenceVisual',body)
write(bp,'SRSequenceRefreshSequence',f'''
 (bind gs (Game|GetGameState))
 {S('Now','(GameState|GetServerWorldTimeSeconds :self gs)')}
 {S('Age',f'(- {V("Now")} {V("StartTime")})')}
 (CallFunction|SRSequenceApplySequenceScaling) (CallFunction|SRSequenceTriggerSequence) (CallFunction|SRSequenceApplySequenceVisual) (CallFunction|SRSequenceDamageSequence)''')
write(bp,'SRSequenceBeginSequence','(CallFunction|SRSequenceRefreshSequence) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "SRSequenceRefreshSequence" :Time 0.05 :bLooping true)')
event(bp,'ReceiveBeginPlay','SRSequenceBeginSequence');save(bp)
for folder,name,kind in [('Traps','BP_CollapsingBridge',0),('Traps','BP_Boulder',1),('Traps','BP_FallingRocks',2),('Maze','BP_BatBurst',3)]:
    child=create('/Game/Hazards/'+folder+'/'+name,bp.generated_class());BP.get_default_object(child).set_editor_property('Kind',kind);save(child)
RESULT={'assets':['BP_SprintSequence','BP_CollapsingBridge','BP_Boulder','BP_FallingRocks','BP_BatBurst'],'replicated_start_time':True,'server_damage_playing_only':True,'reset_handler':'SRSequenceResetSchedule','interface_hook':'Primary adds BPI_RoundReset after this build, then ResetForRound event -> SRSequenceResetSchedule','runtime_acceptance_pending':True}
