"""Editor only: replicated rockfall seal, callable by the server taking coordinator."""
import sys, importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import authoring; importlib.reload(authoring)
from authoring import *
guard()
bp=create('/Game/Hazards/Maze/BP_MouthSeal',ue.Actor.static_class())
cdo=BP.get_default_object(bp)
cdo.set_editor_property('replicates',True)
cdo.set_editor_property('always_relevant',True)
var(bp,'OpenPath','int',-1,replicated=True)
var(bp,'SealTime','float',-1,replicated=True)
for i in range(4):
    mesh,_=component(bp,'Rockfall'+str(i),ue.StaticMeshComponent)
    mesh.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'))
    mesh.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Rock'))
    mesh.set_mobility(ue.ComponentMobility.MOVABLE)
    mesh.set_editor_property('relative_scale3d',ue.Vector(4,.5,5.5))
    mesh.set_collision_profile_name('BlockAll')
    var(bp,'Path'+str(i),'vector',ue.Vector(),editable=True)
    var(bp,'Yaw'+str(i),'float',0,editable=True)
for name in ('SRMouthApplySeal','SRMouthBeginSeal','ResetSeal'): fn(bp,name)
fn(bp,'SealAllBut',inputs=[('PathIndex','int')])
write(bp,'SealAllBut',f'''
 (if (and (Networking|HasAuthority) (and (>= PathIndex 0) (< PathIndex 4)))
  {S('OpenPath','PathIndex')}
  (bind gs (Game|GetGameState))
  {S('SealTime','(GameState|GetServerWorldTimeSeconds :self gs)')}
  (CallFunction|SRMouthApplySeal))''','PathIndex')
write(bp,'ResetSeal',f'''(if (Networking|HasAuthority) {S('OpenPath','-1')} {S('SealTime','-1.0')} (CallFunction|SRMouthApplySeal))''')
body=''
for i in range(4):
    body+=f'''(Transformation|SetRelativeLocation :self {V('Rockfall'+str(i))} :NewLocation {V('Path'+str(i))} :bSweep false :bTeleport true)
 (Transformation|SetRelativeRotation :self {V('Rockfall'+str(i))} :NewRotation (Math|Rotator|MakeRotator :Yaw {V('Yaw'+str(i))}) :bSweep false :bTeleport true)
 (bind blocked{i} (and (>= {V('OpenPath')} 0) (!= {V('OpenPath')} {i})))
 (Rendering|SetVisibility :self {V('Rockfall'+str(i))} :bNewVisibility blocked{i})
 (if blocked{i}
  (Collision|SetCollisionEnabled :self {V('Rockfall'+str(i))} :NewType "QueryAndPhysics")
  (else (Collision|SetCollisionEnabled :self {V('Rockfall'+str(i))} :NewType "NoCollision")))
'''
write(bp,'SRMouthApplySeal',body)
write(bp,'SRMouthBeginSeal','(CallFunction|SRMouthApplySeal) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "SRMouthApplySeal" :Time 0.1 :bLooping true)')
event(bp,'ReceiveBeginPlay','SRMouthBeginSeal')
save(bp)
climb=create('/Game/Hazards/Maze/BP_ClimbVolume',ue.Actor.static_class())
climb_box,_=component(climb,'ClimbZone',ue.BoxComponent)
climb_box.set_box_extent(ue.Vector(220,220,300))
climb_box.set_collision_profile_name('OverlapAllDynamic')
climb_box.set_editor_property('generate_overlap_events',True)
BP.get_default_object(climb).set_editor_property('tags',[ue.Name('Climbable')])
save(climb)
RESULT={'asset':bp.get_path_name(),'functions':['SealAllBut(PathIndex)','ResetSeal'],'replicated_schedule':True,'runtime_acceptance_pending':True}
