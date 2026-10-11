import sys,importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent));import authoring;importlib.reload(authoring)
from authoring import *
from editor_toolset.toolsets.blueprint import _BlueprintCache
guard()
asset_tools=ue.AssetToolsHelpers.get_asset_tools()
for material_name,tint in [('MI_SixRound_TrapWarning',ue.LinearColor(1.0,.068,.023,1.0)),('MI_SixRound_ClimbAmber',ue.LinearColor(1.0,.45,.064,1.0))]:
 path='/Game/Hazards/Art/SixRoundMaze/Materials/'+material_name
 mi=ue.load_asset(path) or asset_tools.create_asset(material_name,'/Game/Hazards/Art/SixRoundMaze/Materials',ue.MaterialInstanceConstant,ue.MaterialInstanceConstantFactoryNew())
 ue.MaterialEditingLibrary.set_material_instance_parent(mi,ue.load_asset('/Game/Shared/Style/M_Stylized'))
 ue.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi,'Tint',tint)
 ue.MaterialEditingLibrary.update_material_instance(mi)
 assert ue.EditorAssetLibrary.save_loaded_asset(mi,False)
trap_warning=ue.load_asset('/Game/Hazards/Art/SixRoundMaze/Materials/MI_SixRound_TrapWarning')
bp=create('/Game/Hazards/Traps/SixRound/BP_SixRoundTrap',ue.Actor.static_class());BP.get_default_object(bp).set_editor_property('replicates',True);BP.get_default_object(bp).set_editor_property('always_relevant',True)
for name,kind,value,rep in [('Kind','int',0,False),('Damage','float',35,False),('StartTime','float',0,True),('TriggeredAt','float',-1000,True),('Interval','float',3,True),('SpikeDelay','float',.6,True),('SwingSpeed','float',.8,True),('Warning','bool',False,False),('Danger','bool',False,False),('Now','float',0,False),('LastVolley','int',-1,False),('SpikeFired','bool',False,False),('SpikeReady','bool',True,False),('LastWarning','bool',False,False)]:var(bp,name,kind,value,replicated=rep,editable=name in ('Kind','Damage'))
var(bp,'ScalingRow','name',ue.Name('None'))
box,h=component(bp,'DamageBox',ue.BoxComponent);box.set_box_extent(ue.Vector(110,200,140));box.set_editor_property('relative_location',ue.Vector(0,0,130));box.set_collision_profile_name('OverlapAllDynamic');box.set_editor_property('generate_overlap_events',True)
warning,h=component(bp,'WarningTile',ue.StaticMeshComponent);warning.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));warning.set_editor_property('relative_scale3d',ue.Vector(2.2,4,.06));warning.set_editor_property('relative_location',ue.Vector(0,0,4));warning.set_collision_profile_name('NoCollision');warning.set_material(0,trap_warning);warning.set_mobility(ue.ComponentMobility.MOVABLE)
for i,(x,y) in enumerate([(x,y) for x in (-65,0,65) for y in (-125,0,125)]):
 mesh,h=component(bp,'Spike'+str(i),ue.StaticMeshComponent);mesh.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cone'));mesh.set_editor_property('relative_scale3d',ue.Vector(.35,.35,1.2));mesh.set_editor_property('relative_location',ue.Vector(x,y,50));mesh.set_collision_profile_name('NoCollision');mesh.set_mobility(ue.ComponentMobility.MOVABLE);mesh.set_material(0,trap_warning)
beam,h=component(bp,'TrapBeam',ue.StaticMeshComponent);beam.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));beam.set_editor_property('relative_scale3d',ue.Vector(.15,4,.15));beam.set_editor_property('relative_location',ue.Vector(0,0,130));beam.set_collision_profile_name('NoCollision');beam.set_mobility(ue.ComponentMobility.MOVABLE);beam.set_material(0,trap_warning)
var(bp,'CarrierSafe','bool',False,editable=True)
for n in ('SRTrapApplyTrapScaling','SRTrapApplyTrapVisual','SRTrapDamageOccupants','SRTrapProcessSpikes','SRTrapProcessDarts','SRTrapProcessSwing','SRTrapRefreshTrap','SRTrapBeginTrap','SRTrapEndTrap','SRTrapResetSchedule','SRTrapConfigureSwingContact'):fn(bp,n)
ue.load_asset('/Game/Hazards/DT_HazardScaling');_BlueprintCache.invalidate(bp)
write(bp,'SRTrapApplyTrapScaling',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind row (Class|BPCoopGameState|GetScalingRow :self gs))
    (if (!= row {V('ScalingRow')})
     (bind data (Utilities|GetDataTableRow :DataTable "/Game/Hazards/DT_HazardScaling.DT_HazardScaling" :RowName row)
      (:then (bind (spikes darts swing revive) (Utilities|Struct|BreakSHazardScaling :S_HazardScaling data))
       {S('SpikeDelay','spikes')} {S('Interval','darts')} {S('SwingSpeed','swing')} {S('ScalingRow','row')}) (:RowNotFound)))) (:CastFailed)))''')
write(bp,'SRTrapDamageOccupants',f'''
 (if (Networking|HasAuthority)
  (bind damageGS (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (bind (damageIndex damagePhase damageAttempt damageEnds damageRow) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self damageGS)))
    (if (Utilities|Enum|Equal(Enum) damagePhase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1"))
     (for player (Collision|GetOverlappingActors :self {V('DamageBox')} :ClassFilter "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
      (Game|Damage|ApplyDamage :DamagedActor player :BaseDamage {V('Damage')} :DamageCauser self)))) (:CastFailed)))''')
write(bp,'SRTrapProcessSpikes',f'''
 (if (Networking|HasAuthority)
  (bind overlaps (Collision|GetOverlappingActors :self {V('DamageBox')} :ClassFilter "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C"))
  (if (== (Utilities|Array|Length :TargetArray overlaps) 0) {S('SpikeReady','true')})
  (if (and {V('SpikeReady')} (and (> (Utilities|Array|Length :TargetArray overlaps) 0) (> (- {V('Now')} {V('TriggeredAt')}) (+ {V('SpikeDelay')} 2.0))))
   {S('TriggeredAt',V('Now'))} {S('SpikeFired','false')} {S('SpikeReady','false')}
   (Audio|PlaySoundatLocation :Sound "/Game/Hazards/Art/Audio/SFX_Spikes_Arm.SFX_Spikes_Arm" :Location (Transformation|GetActorLocation)))
  (if (and (not {V('SpikeFired')}) (and (>= (- {V('Now')} {V('TriggeredAt')}) {V('SpikeDelay')}) (< (- {V('Now')} {V('TriggeredAt')}) (+ {V('SpikeDelay')} 1.0))))
   {S('SpikeFired','true')} (CallFunction|SRTrapDamageOccupants)))''')
write(bp,'SRTrapProcessDarts',f'''
 (if (and (Networking|HasAuthority) (>= {V('Now')} {V('StartTime')}))
  (bind volley (Math|Float|Floor :A (/ (- {V('Now')} {V('StartTime')}) {V('Interval')})))
  (if (!= volley {V('LastVolley')}) {S('LastVolley','volley')} (CallFunction|SRTrapDamageOccupants)
   (Audio|PlaySoundatLocation :Sound "/Game/Hazards/Art/Audio/MS_DartLauncher_Fire.MS_DartLauncher_Fire" :Location (Transformation|GetActorLocation))))''')
# Swing contact is authored by the same narrow patch used for existing assets
# below; it never calls the fixed DamageBox helper used by spikes and darts.
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
write(bp,'SRTrapApplyTrapVisual',visual)
write(bp,'SRTrapResetSchedule',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then {S('StartTime','(+ (GameState|GetServerWorldTimeSeconds :self gs) 3.0)')}
    {S('TriggeredAt','-1000.0')} {S('LastVolley','-1')} {S('SpikeFired','false')} {S('SpikeReady','true')}) (:CastFailed)))''')
write(bp,'SRTrapRefreshTrap',f'''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then {S('Now','(GameState|GetServerWorldTimeSeconds :self gs)')}
   (CallFunction|SRTrapApplyTrapScaling)
   (if {V('CarrierSafe')} {S('Interval','8.0')} {S('SwingSpeed','0.35')} {S('SpikeDelay','1.8')})
   (CallFunction|SRTrapApplyTrapVisual)
   (if (== {V('Kind')} 0) (CallFunction|SRTrapProcessSpikes))
   (if (== {V('Kind')} 1) (CallFunction|SRTrapProcessDarts))
   (if (== {V('Kind')} 2) (CallFunction|SRTrapProcessSwing))) (:CastFailed))''')
write(bp,'SRTrapBeginTrap',f'''
 (CallFunction|SRTrapConfigureSwingContact)
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then {S('StartTime','(+ (GameState|GetServerWorldTimeSeconds :self gs) 3.0)')}
    (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "SRTrapRefreshTrap" :Time 0.05 :bLooping true))
   (:CastFailed))
  (else (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "SRTrapRefreshTrap" :Time 0.05 :bLooping true)))''')
write(bp,'SRTrapEndTrap','(Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "SRTrapRefreshTrap")')
event(bp,'ReceiveBeginPlay','SRTrapBeginTrap');event(bp,'ReceiveEndPlay','SRTrapEndTrap');save(bp)
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fix_swing_contact;importlib.reload(fix_swing_contact)
fix_swing_contact.apply_swing_contact(bp)
for name,kind in [('BP_SixRoundSpikes',0),('BP_SixRoundDarts',1),('BP_SixRoundSwing',2)]:
 child=create('/Game/Hazards/Traps/SixRound/'+name,bp.generated_class());BP.get_default_object(child).set_editor_property('Kind',kind);save(child)
RESULT={'scheduled_spikes_darts_swing':True,'server_damage':True,'shared_table_scaling':True,'runtime_acceptance_pending':True}
(QUEUE/'trap-build.json').write_text(json.dumps(RESULT,indent=2))
