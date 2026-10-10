"""Place only tagged small relics in the isolated HC stream; no Blueprint edits.
Manifest small_relic_spots stores authored floor+80cm (make_positions source).
Tutorial floor is authored Z0. Only Tutorial0 has a primary-approved150cm east adjustment around native existing rock; all other unsafe XY is reported, never relocated.
Native traces are preflight evidence, not actual owning-input pickup proof.
"""
import sys,json,hashlib
from pathlib import Path
_core=Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'
sys.path.insert(0,str(_core))
from common import *
from test_map_contract import *

guard();args=globals().get('ARGS',{});validate_args(args)
assert not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE before placement'
protected=[ROOT/'Content/Hazards/L_Site01_HZ.umap',ROOT/'Content/Puzzles/EnvironmentConnection/L_ConnectedMaze.umap',ROOT/'Content/Puzzles/EnvironmentConnection/BP_EnvironmentDoor.uasset']
def hashes():return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
before=hashes()
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert ue.EditorAssetLibrary.does_asset_exist(PERSISTENT) and editor.load_level(PERSISTENT)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();assert world.get_outermost().get_name()==PERSISTENT
hc=ue.GameplayStatics.get_streaming_level(world,HC_LEVEL.rsplit('/',1)[-1]);assert hc
assert str(hc.get_world_asset_package_f_name())==HC_LEVEL
package=hc.get_loaded_level().get_outermost();assert writable_package(package)==HC_LEVEL
ue.EditorLevelUtils.make_level_current(hc)
old=[a for a in actors.get_all_level_actors() if a.get_level().get_outermost().get_name()==HC_LEVEL and a.actor_has_tag('SixRound.SmallRelic')]
assert all(a.get_class().get_name()=='BP_Relic_C' for a in old),'Refuse unexpected actor with owned relic tag'
layout=json.loads((ROOT/'Tools/unreal/six_round/world/positions.json').read_text())
spots=[{'name':f'Six_SmallRelic_{i}','xy':p[:2],'floor_z':p[2]-80,'source':'manifest floor+80'} for i,p in enumerate(layout['small_relic_spots'])]
spots += [{'name':f'Six_TutorialRelic_{i}','xy':xy,'floor_z':0,'source':'tutorial authored floor0'} for i,xy in enumerate([[-650,1200],[1000,-1200]])]
spots[-2]['placement_adjustment']={'requested_xy':[-800,1200],'actual_xy':[-650,1200],'reason':'native existing Cave_procedural_320 rock obstructed visibility at the requested spawn-room point; primary approved150cm east'}
assert len(spots)==6 and len({tuple(p['xy']) for p in spots})==6
bp=ue.load_asset('/Game/Puzzles/BP_Relic');assert bp
cdo=ue.get_default_object(bp.generated_class());mesh=cdo.static_mesh_component
assert cdo.get_editor_property('replicates')
assert not cdo.get_editor_property('Collected') and cdo.get_editor_property('Value')==1 and cdo.get_editor_property('MinPlayers')==2
static=mesh.get_editor_property('static_mesh');assert static
bounds=static.get_bounds();relative=mesh.get_editor_property('relative_location');scale=mesh.get_editor_property('relative_scale3d');rotation=mesh.get_editor_property('relative_rotation')
assert max(abs(rotation.pitch),abs(rotation.yaw),abs(rotation.roll))<.01,'Review rotated mesh before deriving root height'
assert min(scale.x,scale.y,scale.z)>0
bottom=relative.z+(bounds.origin.z-bounds.box_extent.z)*scale.z
character=ue.get_default_object(ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class());capsule=character.get_component_by_class(ue.CapsuleComponent)
radius=capsule.get_scaled_capsule_radius();half=capsule.get_scaled_capsule_half_height()
report={'writes':[HC_LEVEL],'protected_before':before,'spots':[],'unsafe':[],'native_pickup_pending':True}
created=[]
def trace(a,b,ignore):
 hit=ue.SystemLibrary.line_trace_single(world,ue.Vector(*a),ue.Vector(*b),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
 return hit.to_dict() if hit else None

def vector_data(value):return [value.x,value.y,value.z] if value is not None else None

def collision_diagnostics(component):
 # Diagnostics must not replace the placement failure with an optional getter error.
 data={'component_path':component.get_path_name()}
 for label,method in (('profile','get_collision_profile_name'),('enabled','get_collision_enabled')):
  try:data[label]=str(getattr(component,method)())
  except Exception as exc:data[label+'_unavailable']=str(exc)
 for label,names in (('visibility',('VISIBILITY','ECC_VISIBILITY')),('pawn',('PAWN','ECC_PAWN'))):
  try:
   channel=next(getattr(ue.CollisionChannel,name) for name in names if hasattr(ue.CollisionChannel,name))
   data[label+'_response']=str(component.get_collision_response_to_channel(channel))
  except Exception as exc:data[label+'_response_unavailable']=str(exc)
 return data

def record():
 QUEUE.mkdir(parents=True,exist_ok=True);(QUEUE/'small-relic-placement.json').write_text(json.dumps(report,indent=2))

# Check all authored coordinates before changing any existing actor.
for spot in spots:
 x,y=spot['xy'];z=spot['floor_z'];data=trace([x,y,z+150],[x,y,z-100],old)
 if not data or abs(data['impact_point'].z-z)>=45 or data['impact_normal'].z<.7:
  report['unsafe'].append({'name':spot['name'],'kind':'authored_floor_missing_or_steep','placement_adjustment':spot.get('placement_adjustment'),'expected':z,'hit_z':data['impact_point'].z if data else None});continue
 spot['actual_floor_z']=data['impact_point'].z;spot['root_z']=z+20-bottom
 # Candidate stand points are probe positions only; the collectible never moves XY.
 approaches=[]
 for dx,dy in ((0,-110),(0,110),(-110,0),(110,0)):
  px,py=x+dx,y+dy;floor=trace([px,py,z+100],[px,py,z-120],old)
  if not floor or abs(floor['impact_point'].z-z)>60 or floor['impact_normal'].z<.7:continue
  feet=floor['impact_point'].z;center=ue.Vector(px,py,feet+half+5)
  blocked=ue.SystemLibrary.capsule_trace_single(world,center,center,radius,half,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,old,ue.DrawDebugTrace.NONE,True)
  if not blocked:approaches.append([px,py,feet])
 if not approaches:report['unsafe'].append({'name':spot['name'],'kind':'no_safe_adjacent_capsule','placement_adjustment':spot.get('placement_adjustment')});continue
 spot['approaches']=approaches
if report['unsafe']:report['passed']=False;record();raise AssertionError(report['unsafe'])
try:
 for spot in spots:
  x,y=spot['xy'];actor=actors.spawn_actor_from_class(bp.generated_class(),ue.Vector(x,y,spot['root_z']));assert actor
  safe_actor(actor,package);created.append(actor);actor.set_actor_label(spot['name']);actor.tags=[ue.Name('SixRoundHC'),ue.Name('SixRound.SmallRelic')]
  actor.set_editor_property('Value',1);actor.set_editor_property('MinPlayers',2)
  actor.set_actor_hidden_in_game(False);actor.set_actor_enable_collision(True)
  origin,extent=actor.get_actor_bounds(False)
  assert 0<extent.z<150 and max(extent.x,extent.y)<100,'Pickup mesh should stay small and off the walking lane'
  assert abs((origin.z-extent.z)-(spot['floor_z']+20))<2,'Mesh-relative root height mismatch'
  visible=[];rays=[]
  native_bounds={'origin':vector_data(origin),'extent':vector_data(extent),'actor_path':actor.get_path_name(),'collision':collision_diagnostics(actor.static_mesh_component)}
  for stand in spot['approaches']:
   start=[stand[0],stand[1],stand[2]+half+60];end=[origin.x,origin.y,origin.z]
   hit=trace(start,end,old);hit_actor=hit.get('hit_actor') if hit else None
   rays.append({'stand':stand,'trace_start':start,'trace_end':end,'hit_actor_label':hit_actor.get_actor_label() if hit_actor else None,'hit_actor_path':hit_actor.get_path_name() if hit_actor else None,'impact_point':vector_data(hit.get('impact_point')) if hit else None,'impact_normal':vector_data(hit.get('impact_normal')) if hit else None,'hit_pickup':hit_actor==actor})
   if hit and hit_actor==actor:visible.append(stand)
  if not visible:
   report['unsafe'].append({'name':spot['name'],'kind':'pickup_visibility_collision_blocked','placement_adjustment':spot.get('placement_adjustment'),'pickup':native_bounds,'approach_rays':rays});raise AssertionError(report['unsafe'])
  report['spots'].append({'name':spot['name'],'source':spot['source'],'root':[x,y,spot['root_z']],'authored_floor_z':spot['floor_z'],'actual_floor_z':spot['actual_floor_z'],'placement_adjustment':spot.get('placement_adjustment'),'mesh_bottom_clearance':20,'safe_visible_approaches':visible,'pickup':native_bounds,'approach_rays':rays})
 # Only replace the tagged set after every new placement is validated.
 for actor in old:safe_actor(actor,package);assert actors.destroy_actor(actor)
 assert hashes()==before,'Protected source changed during placement'
 report['saved']=save_exact(ue,[package]);assert hashes()==before
 report['protected_after']=hashes();report['expected_small_value']=6;report['passed']=True;record()
except Exception:
 for actor in created:assert actors.destroy_actor(actor)
 report['passed']=False;record();raise
RESULT=report
