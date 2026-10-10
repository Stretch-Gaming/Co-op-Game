"""Predeclare PG assets before cross-lane graphs. Run only in six-round editor."""
import sys, importlib
sys.path.insert(0, str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
interface_path='/Game/Player/Tools/BPI_Lightable'
lightable=ue.load_asset(interface_path)
if not lightable:
 lightable=ue.AssetToolsHelpers.get_asset_tools().create_asset('BPI_Lightable','/Game/Player/Tools',ue.Blueprint.static_class(),ue.BlueprintInterfaceFactory())
 assert lightable
for name in ('LightBegin','LightEnd'):fn(lightable,name,[('Source',ue.Actor.static_class())])
for graph in list(BP.list_graphs(lightable)):
 if graph.get_name()=='NewFunction':BP.remove_function_graph(lightable,'NewFunction')
save(lightable)

paths = {
 'traversal':'/Game/Player/AC_Traversal',
 'tools':'/Game/Player/Tools/AC_Tools',
 'flare':'/Game/Player/Tools/BP_Flare',
 'taking':'/Game/Player/Taking/BP_TakingDirector',
 'chase':'/Game/Player/Ghosts/BP_ChaseDirector',
 'cage':'/Game/Player/RelicChamber/BP_RelicCage',
 'lever':'/Game/Player/RelicChamber/BP_Lever',
}
assets={}
for key,path in paths.items():
 if key=='lever' and not ue.load_asset(path):
  assert ue.EditorAssetLibrary.duplicate_asset('/Game/Player/Round3/BP_Lever',path)
 assets[key]=create(path,ue.ActorComponent.static_class() if key in ('tools','traversal') else ue.Actor.static_class())
 cdo=BP.get_default_object(assets[key])
 if key in ('tools','traversal'): cdo.set_is_replicated(True)
 else: cdo.set_editor_properties({'replicates':True,'replicate_movement':True,'always_relevant':key in ('taking','cage','chase')})

def declarations(key,variables,functions):
 bp=assets[key]
 for name,kind,value,rep in variables:var(bp,name,kind,value,notify=rep)
 for name in functions:fn(bp,name)
 return bp

t=declarations('traversal', [('bSprinting','bool',False,True),('bClimbing','bool',False,True),('WalkSpeed','float',500.,False),('SprintSpeed','float',800.,False),('ClimbSpeed','float',220.,False)], ['SprintOnServer','StopSprintOnServer','ClimbOnServer','StopClimbOnServer','RefreshTraversal','ApplyTraversal','BeginTraversal'])
var(t,'InsideClimbable','bool',False)
fn(t,'CanTraverse',outputs=[('Allowed','bool')])
tools=declarations('tools',[('FlaresLeft','int',0,True),('FlareSeconds','float',20.,False),('BeamTarget',ue.Actor.static_class(),None,False)], ['ThrowFlareOnServer','ThrowFlare','RestockFlares','RefreshBeam','BeginTools','EndTools','ClearBeam'])
fn(tools,'CanUseTools',outputs=[('Allowed','bool')])
fn(tools,'GetFlareAllowance',outputs=[('Count','int')])
flare=declarations('flare',[('BurnStarted','float',-1.,True),('BurnSeconds','float',20.,True),('GlowRadius','float',400.,False),('LightTarget',ue.Actor.static_class(),None,False)], ['BeginFlare','RefreshFlare','EndFlare'])
fn(flare,'IsActive',outputs=[('Active','bool')])
fn(flare,'SetBurnSeconds',inputs=[('Seconds','float')])
root,handle=component(flare,'FlareRoot',ue.StaticMeshComponent)
root.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cylinder'))
root.set_editor_property('relative_scale3d',ue.Vector(.06,.06,.22));root.set_collision_profile_name('BlockAllDynamic')
light,handle=component(flare,'FlareLight',ue.PointLightComponent)
light.set_editor_properties({'intensity':2500.,'attenuation_radius':600.,'light_color':ue.Color(255,156,58),'cast_shadows':False})
movement,handle=component(flare,'FlareFlight',ue.ProjectileMovementComponent)
movement.set_editor_properties({'initial_speed':700.,'max_speed':700.,'projectile_gravity_scale':1.,'should_bounce':True,'bounciness':.2})
cage=declarations('cage',[('bRaised','bool',False,True),('bLatched','bool',False,True),('HeldLevers','int',0,False),('RequiredLevers','int',1,True)], ['RefreshCage','ApplyCage','LatchOpen','BeginCage'])
fn(cage,'IsRaised',outputs=[('Raised','bool')]);fn(cage,'ResetCage',inputs=[('Index','int'),('Attempt','int')])
mesh,handle=component(cage,'CageMesh',ue.StaticMeshComponent)
mesh.set_static_mesh(ue.load_asset('/Game/Player/Art/SM_GauntletGate'))
mesh.set_collision_profile_name('BlockAllDynamic')
lever=declarations('lever',[('Holder',ue.Actor.static_class(),None,True),('bHeld','bool',False,True)], ['RefreshLever','BeginLever'])
fn(lever,'BeginHold',[('PlayerPawn',ue.Actor.static_class())]);fn(lever,'EndHold',[('PlayerPawn',ue.Actor.static_class())])
fn(lever,'IsHeld',outputs=[('Held','bool')]);fn(lever,'ResetSixLever',inputs=[('Index','int'),('Attempt','int')])
fn(lever,'CanSixHold',[('PlayerPawn',ue.Actor.static_class())],[('Allowed','bool')])
taking=declarations('taking',[('Victim',ue.Actor.static_class(),None,True),('TakingStarted','float',-1.,True),('ScareStyle','int',0,True),('NextSlot','int',0,False),('RemainingSlot','int',-1,True),('StartedAttempt','int',-1,False),('Teleported','bool',False,False)], ['BeginTaking','RefreshTaking','ScheduleNext','FinishTaking','PlayTakingVisual'])
fn(taking,'TakePlayer',[('PlayerPawn',ue.Actor.static_class())]);fn(taking,'MoveVictimToPath');fn(taking,'ResetTaking',[('Index','int'),('Attempt','int')])
chase=declarations('chase',[('SpawnedAttempt','int',-1,False),('LastWaveAt','float',-100.,False),('WaveNumber','int',0,True)], ['BeginChase','RefreshChase','SpawnWave','ClearChase'])
var(chase,'WaveGhosts',ue.Actor.static_class(),array=True)
fn(chase,'ResetChase',[('Index','int'),('Attempt','int')])
view=ue.load_asset('/Game/Player/AC_PlayerView')
var(view,'SpectatedPawn',ue.Actor.static_class());var(view,'LastSpectatorSlot','int',-1)
for name in ('RefreshSpectator','CycleSpectator'):fn(view,name)
fn(view,'GetHeadlampOn',outputs=[('On','bool')])
for bp in [*assets.values(),view]:save(bp)
RESULT={'stage':'PG declarations','assets':paths,'runtime_acceptance_pending':True}

