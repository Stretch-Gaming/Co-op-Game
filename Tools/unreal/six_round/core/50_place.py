"""Place six-round gameplay only in the new isolated HC test sublevel."""
import sys,json
from pathlib import Path
_core=Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'
sys.path.insert(0,str(_core))
from common import *
from test_map_contract import *
guard();args=globals().get('ARGS',{});validate_args(args);positions=json.loads((ROOT/'Tools/unreal/six_round/world/positions.json').read_text())
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert ue.EditorAssetLibrary.does_asset_exist(PERSISTENT) and ue.EditorAssetLibrary.does_asset_exist(DOOR)
assert editor.load_level(PERSISTENT)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();assert world.get_outermost().get_name()==PERSISTENT
hc=ue.GameplayStatics.get_streaming_level(world,HC_LEVEL.rsplit('/',1)[-1]);assert hc and str(hc.get_world_asset_package_f_name())==HC_LEVEL
package=hc.get_loaded_level().get_outermost();assert writable_package(package)==HC_LEVEL
# Retire the old three-chamber gameplay route without touching HZ scenery or PG actors.
retired={'BP_RoundDirector_C','BP_Checkpoint_C','BP_StartPad_C','BP_RoundStart_C','BP_RegroupVolume_C','BP_PressurePlate_C','BP_PuzzleSetup_C','BP_ChamberGate_C','BP_KeyRelic_C','BP_Altar_C','BP_CrystalLock_C','BP_MazeDoor_C','BP_HCGauntletCoordinator_C','BP_HCGauntletObjective_C','BP_HCGauntletStart_C'}
for actor in actors.get_all_level_actors():
 if actor.get_level().get_outermost().get_name()!=package.get_name():continue
 if actor.actor_has_tag('SixRoundHC') or actor.get_class().get_name() in retired:safe_actor(actor,package);assert actors.destroy_actor(actor)
ue.EditorLevelUtils.make_level_current(hc)
def spawn(path,label,location,props=None,tags=(),yaw=0):
 cls=ue.load_asset(path).generated_class() if isinstance(path,str) else path
 actor=actors.spawn_actor_from_class(cls,ue.Vector(*location),ue.Rotator(yaw=yaw));assert actor
 safe_actor(actor,package)
 actor.set_actor_label(label);actor.tags=[ue.Name('SixRoundHC')]+[ue.Name(t) for t in tags]
 for k,v in (props or {}).items():actor.set_editor_property(k,v)
 return actor
spawn('/Game/Puzzles/Rounds/BP_RoundDirector','Six_RoundDirector',(0,0,0))
for idx in range(7):
 spots=positions['checkpoints'][str(max(idx,1))];base=spots[0]
 cp=spawn('/Game/Puzzles/BP_Checkpoint',f'Six_Checkpoint_{idx}',base,{'RoundIndex':idx},tags=[f'Checkpoint{idx}'])
 for comp in cp.get_components_by_class(ue.SceneComponent):
  for slot,spot in enumerate(spots):
   if comp.get_name()=='Spot'+str(slot):comp.set_relative_location(ue.Vector(*(spot[k]-base[k] for k in range(3))),False,False)
pad=spawn('/Game/Puzzles/BP_StartPad','Six_StartPad',positions['startpad']);pad.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(350,350,180))
for slot,pos in enumerate(positions['plates']):spawn('/Game/Puzzles/BP_PressurePlate',f'Six_Plate_{slot}',pos,{'PlateSlot':slot},tags=['HC_Round1'])
spawn('/Game/Puzzles/BP_PuzzleSetup','Six_PlatePuzzle',(0,0,0),{'StatueTransforms':[ue.Transform(location=ue.Vector(*pos)) for pos in positions['statues']],'StatueClass':ue.load_asset('/Game/Puzzles/BP_Statue').generated_class()})
# One physical barrier, with the delivered centered mesh and exact closed/open roots.
connection_door=spawn(DOOR,'Six_ConnectionDoor',[325,1400,200],tags=['ConnectionDoor','MazeEntrance'])
mesh=ue.load_asset('/Game/Puzzles/EnvironmentConnection/Art/SM_ConnectionDoor');assert mesh
bounds=mesh.get_bounds();assert min(bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z)>0
connection_door.set_actor_scale3d(ue.Vector(300/(bounds.box_extent.x*2),35/(bounds.box_extent.y*2),400/(bounds.box_extent.z*2)))
entrance_origin,entrance_extent=connection_door.get_actor_bounds(False)
assert (entrance_origin-ue.Vector(325,1400,200)).length()<1.0
assert abs(entrance_extent.x-150)<1 and abs(entrance_extent.y-17.5)<1 and abs(entrance_extent.z-200)<1
assert connection_door.get_level().get_outermost().get_name()==HC_LEVEL
for idx,(key,starts) in enumerate([('maze_mouth',True),('meeting',False),('relic',False)]):
 data=positions[key];round_index=2 if idx<2 else 4
 loc=list(data['center']);extent=list(data['extent'])
 if key!='maze_mouth':loc[2]+=150;extent[2]=300
 zone=spawn('/Game/Puzzles/BP_RegroupVolume',f'Six_Zone_{key}',loc,{'RoundIndex':round_index,'StartsRound':starts})
 zone.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(*extent))
for brazier,key in [(False,'headlamp_locks'),(True,'braziers')]:
 for slot,pos in enumerate(positions['meeting'][key]):
  lock=spawn('/Game/Puzzles/BP_CrystalLock',f'Six_{key}_{slot}',pos,{'Brazier':brazier,'LockSlot':slot},tags=['FlareLock' if brazier else 'HeadlampLock'])
  lock.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cylinder' if brazier else '/Engine/BasicShapes/Sphere'))
  lock.set_actor_scale3d(ue.Vector(.8,.8,1.0));lock.static_mesh_component.set_collision_profile_name('BlockAllDynamic')
for slot,pos in enumerate(positions['meeting']['doors']):
 yaw=90 if slot<2 else (0 if slot==2 else 180)
 door=spawn('/Game/Puzzles/BP_MazeDoor',f'Six_PathDoor_{slot}',pos,{'PathSlot':slot},yaw=yaw)
 door.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));door.static_mesh_component.set_relative_scale3d(ue.Vector(.3,4,5))
 door.static_mesh_component.set_relative_location(ue.Vector(0,0,250),False,False)
 box=door.get_component_by_class(ue.BoxComponent);box.set_absolute(False,False,True);box.set_box_extent(ue.Vector(350,180,300));box.set_collision_profile_name('OverlapAllDynamic');box.set_editor_property('generate_overlap_events',True)
spawn('/Game/Puzzles/BP_KeyRelic','Six_KeyRelic',positions['relic']['key'],tags=['Relic'])
spawn('/Game/Puzzles/BP_Altar','Six_DropoffAltar',positions['altar'])
for name,pos in positions['gates'].items():spawn('/Game/Puzzles/BP_ChamberGate','Six_Return_'+name,pos,{'RoundIndex':99,'OpenHeight':650.0},yaw=90)
all_actors=actors.get_all_level_actors()
assert len([a for a in all_actors if a.actor_has_tag('ConnectionDoor')])==1
assert not [a for a in all_actors if a.get_class().get_name()=='BP_EnvironmentDoor_C' or a.get_actor_label()=='Six_MazeDoor']
assert not [a for a in all_actors if a.get_class().get_name()=='BP_EnvironmentPreview_C']
saved=save_exact(ue,[package])
# Shared narrow consumer owns exactly the tagged optional pickups. Save HC first:
# its exact-map load must not discard the newly authored puzzle placements.
small_script=_core/'place_small_relics.py'
small_scope={'__file__':str(small_script),'ROOT':ROOT,'QUEUE':QUEUE,'ARGS':args}
exec(compile(small_script.read_text(encoding='utf-8-sig'),str(small_script),'exec'),small_scope)
small_relics=small_scope['RESULT']
RESULT={'stage':'hc_test_placements','persistent':PERSISTENT,'saved':saved,'sole_connection_door':connection_door.get_path_name(),'door_bounds':{'center':[entrance_origin.x,entrance_origin.y,entrance_origin.z],'extent':[entrance_extent.x,entrance_extent.y,entrance_extent.z]},'writes':[HC_LEVEL],'small_relics':small_relics,'runtime_acceptance_pending':True}
QUEUE.mkdir(parents=True,exist_ok=True);(QUEUE/'test-map-hc-placement.json').write_text(json.dumps(RESULT,indent=2))
