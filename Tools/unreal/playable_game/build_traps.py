import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
from editor_toolset.toolsets.blueprint import _BlueprintCache
bp=create('/Game/Hazards/Traps/BP_AdventureTrap',ue.Actor.static_class());BP.get_default_object(bp).set_editor_property('replicates',True);BP.get_default_object(bp).set_editor_property('always_relevant',True)
for name,kind,value,rep in [('Kind','int',0,False),('Damage','float',35,False),('StartTime','float',0,True),('TriggeredAt','float',-1000,True),('Interval','float',3,True),('SpikeDelay','float',.6,True),('SwingSpeed','float',.8,True),('Warning','bool',False,False),('Danger','bool',False,False),('Now','float',0,False),('LastVolley','int',-1,False),('SpikeFired','bool',False,False),('SpikeReady','bool',True,False),('LastWarning','bool',False,False)]:var(bp,name,kind,value,replicated=rep,editable=name in ('Kind','Damage'))
var(bp,'ScalingRow','name',ue.Name('None'))
box,h=component(bp,'DamageBox',ue.BoxComponent);box.set_box_extent(ue.Vector(110,200,140));box.set_editor_property('relative_location',ue.Vector(0,0,130));box.set_collision_profile_name('OverlapAllDynamic');box.set_editor_property('generate_overlap_events',True)
warning,h=component(bp,'WarningTile',ue.StaticMeshComponent);warning.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));warning.set_editor_property('relative_scale3d',ue.Vector(2.2,4,.06));warning.set_editor_property('relative_location',ue.Vector(0,0,4));warning.set_collision_profile_name('NoCollision');warning.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Gold'));warning.set_mobility(ue.ComponentMobility.MOVABLE)
for i,(x,y) in enumerate([(x,y) for x in (-65,0,65) for y in (-125,0,125)]):
 mesh,h=component(bp,'Spike'+str(i),ue.StaticMeshComponent);mesh.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cone'));mesh.set_editor_property('relative_scale3d',ue.Vector(.35,.35,1.2));mesh.set_editor_property('relative_location',ue.Vector(x,y,50));mesh.set_collision_profile_name('NoCollision');mesh.set_mobility(ue.ComponentMobility.MOVABLE);mesh.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Gold'))
beam,h=component(bp,'TrapBeam',ue.StaticMeshComponent);beam.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));beam.set_editor_property('relative_scale3d',ue.Vector(.15,4,.15));beam.set_editor_property('relative_location',ue.Vector(0,0,130));beam.set_collision_profile_name('NoCollision');beam.set_mobility(ue.ComponentMobility.MOVABLE);beam.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Gold'))
for n in ('ApplyTrapScaling','ApplyTrapVisual','DamageOccupants','ProcessSpikes','ProcessDarts','ProcessSwing','RefreshTrap','BeginTrap','EndTrap'):fn(bp,n)
ue.load_asset('/Game/Hazards/DT_HazardScaling');_BlueprintCache.invalidate(bp)
write(bp,'ApplyTrapScaling',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind row (Class|BPCoopGameState|GetScalingRow :self gs))
    (if (!= row {V('ScalingRow')})
     (bind data (Utilities|GetDataTableRow :DataTable "/Game/Hazards/DT_HazardScaling.DT_HazardScaling" :RowName row)
      (:then (bind (spikes darts swing revive) (Utilities|Struct|BreakSHazardScaling :S_HazardScaling data))
       {S('SpikeDelay','spikes')} {S('Interval','darts')} {S('SwingSpeed','swing')} {S('ScalingRow','row')}) (:RowNotFound)))) (:CastFailed)))''')
write(bp,'DamageOccupants',f'''
 (if (Networking|HasAuthority)
  (for player (Collision|GetOverlappingActors :self {V('DamageBox')} :ClassFilter "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
   (Game|Damage|ApplyDamage :DamagedActor player :BaseDamage {V('Damage')} :DamageCauser self)))''')
write(bp,'ProcessSpikes',f'''
 (if (Networking|HasAuthority)
  (bind overlaps (Collision|GetOverlappingActors :self {V('DamageBox')} :ClassFilter "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C"))
  (if (== (Utilities|Array|Length :TargetArray overlaps) 0) {S('SpikeReady','true')})
  (if (and {V('SpikeReady')} (and (> (Utilities|Array|Length :TargetArray overlaps) 0) (> (- {V('Now')} {V('TriggeredAt')}) (+ {V('SpikeDelay')} 2.0))))
   {S('TriggeredAt',V('Now'))} {S('SpikeFired','false')} {S('SpikeReady','false')}
   (Audio|PlaySoundatLocation :Sound "/Game/Hazards/Art/Audio/SFX_Spikes_Arm.SFX_Spikes_Arm" :Location (Transformation|GetActorLocation)))
  (if (and (not {V('SpikeFired')}) (and (>= (- {V('Now')} {V('TriggeredAt')}) {V('SpikeDelay')}) (< (- {V('Now')} {V('TriggeredAt')}) (+ {V('SpikeDelay')} 1.0))))
   {S('SpikeFired','true')} (CallFunction|DamageOccupants)))''')
write(bp,'ProcessDarts',f'''
 (if (and (Networking|HasAuthority) (>= {V('Now')} {V('StartTime')}))
  (bind volley (Math|Float|Floor :A (/ (- {V('Now')} {V('StartTime')}) {V('Interval')})))
  (if (!= volley {V('LastVolley')}) {S('LastVolley','volley')} (CallFunction|DamageOccupants)
   (Audio|PlaySoundatLocation :Sound "/Game/Hazards/Art/Audio/MS_DartLauncher_Fire.MS_DartLauncher_Fire" :Location (Transformation|GetActorLocation))))''')
write(bp,'ProcessSwing',f'''
 (if (Networking|HasAuthority)
  (bind cycle (Math|Float|Floor :A (/ (* (- {V('Now')} {V('StartTime')}) {V('SwingSpeed')}) 3.14159)))
  (bind swing (Math|Trig|Sin(Radians) :A (* (- {V('Now')} {V('StartTime')}) {V('SwingSpeed')})))
  (if (and (!= cycle {V('LastVolley')}) (and (> swing -0.4) (< swing 0.4)))
   {S('LastVolley','cycle')} (CallFunction|DamageOccupants)
   (Audio|PlaySoundatLocation :Sound "/Game/Hazards/Art/Audio/SFX_SwingLog_Whoosh.SFX_SwingLog_Whoosh" :Location (Transformation|GetActorLocation))))''')
visual=f'''{S('Warning','false')} {S('Danger','false')}
 (bind age (- {V('Now')} {V('TriggeredAt')}))
 (if (== {V('Kind')} 0)
  {S('Warning',f'(and (>= age 0.0) (< age {V("SpikeDelay")}))')}
  {S('Danger',f'(and (>= age {V("SpikeDelay")}) (< age (+ {V("SpikeDelay")} 1.0)))')})
 (bind cycle (/ (- {V('Now')} {V('StartTime')}) {V('Interval')}))
 (bind fraction (- cycle (Math|Float|Floor :A cycle)))
 (if (== {V('Kind')} 1)
  {S('Warning',f'(>= fraction (- 1.0 (/ 0.5 {V("Interval")})))')}
  {S('Danger',f'(and (>= {V("Now")} {V("StartTime")}) (< fraction (/ 0.2 {V("Interval")})))')})
 (Rendering|SetVisibility :self {V('WarningTile')} :bNewVisibility (or {V('Warning')} {V('Danger')}))
'''
for i in range(9):visual+=f'(Rendering|SetVisibility :self {V("Spike"+str(i))} :bNewVisibility (and (== {V("Kind")} 0) {V("Danger")}))\n'
visual+=f'''
 (Rendering|SetVisibility :self {V('TrapBeam')} :bNewVisibility (or (and (== {V('Kind')} 1) {V('Danger')}) (== {V('Kind')} 2)))
 (if (== {V('Kind')} 2)
  (Transformation|SetRelativeRotation :self {V('TrapBeam')} :NewRotation (Math|Rotator|MakeRotator :Roll (* (Math|Trig|Sin(Radians) :A (* (- {V('Now')} {V('StartTime')}) {V('SwingSpeed')})) 55.0)) :bSweep false :bTeleport true))
'''
write(bp,'ApplyTrapVisual',visual)
write(bp,'RefreshTrap',f'''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then {S('Now','(GameState|GetServerWorldTimeSeconds :self gs)')}
   (CallFunction|ApplyTrapScaling) (CallFunction|ApplyTrapVisual)
   (if (== {V('Kind')} 0) (CallFunction|ProcessSpikes))
   (if (== {V('Kind')} 1) (CallFunction|ProcessDarts))
   (if (== {V('Kind')} 2) (CallFunction|ProcessSwing))) (:CastFailed))''')
write(bp,'BeginTrap',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState)) (:then {S('StartTime','(+ (GameState|GetServerWorldTimeSeconds :self gs) 3.0)')}) (:CastFailed)))
 (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshTrap" :Time 0.05 :bLooping true)''')
write(bp,'EndTrap','(Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RefreshTrap")')
event(bp,'ReceiveBeginPlay','BeginTrap');event(bp,'ReceiveEndPlay','EndTrap');save(bp)
for name,kind in [('BP_Trap_Spikes',0),('BP_Trap_Darts',1),('BP_Trap_Swing',2)]:
 child=create('/Game/Hazards/Traps/'+name,bp.generated_class());BP.get_default_object(child).set_editor_property('Kind',kind);save(child)
RESULT={'scheduled_spikes_darts_swing':True,'server_damage':True,'shared_table_scaling':True,'runtime_acceptance_pending':True}
(QUEUE/'trap-build.json').write_text(json.dumps(RESULT,indent=2))
