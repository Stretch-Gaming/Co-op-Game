"""Isolated-editor asset collision and client-load smoke-test coordinator."""
import hashlib
import json
from pathlib import Path
import sys
import time
import unreal as ue
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
assert '-HCA1Smoke' in ue.SystemLibrary.get_command_line().split()
assert Path(ue.Paths.project_dir()).resolve()==ROOT
ue.log('HC-A1_ISOLATED_PROJECT: '+ROOT.as_posix())
world=ue.EditorLoadingAndSavingUtils.load_map('/Game/Puzzles/Test/L_HCA1_AssetTest')
actor_subsystem=ue.get_editor_subsystem(ue.EditorActorSubsystem)
heart=next(a for a in actor_subsystem.get_all_level_actors() if a.get_actor_label()=='HCA1_SM_KeyRelic_StoneHeart')
pos=heart.get_actor_location()
def probe(y):
 result=ue.SystemLibrary.line_trace_single(world,ue.Vector(pos.x+100,pos.y+y,pos.z+19),ue.Vector(pos.x-100,pos.y+y,pos.z+19),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],ue.DrawDebugTrace.NONE,True)
 return bool(result[0]) if isinstance(result,tuple) else result is not None
report={'engine':ue.SystemLibrary.get_engine_version(),'collision_probes':{},'sessions':[],'gameplay_pickup_or_carry_tested':False,'test_note':'Static imported-art loading and collider smoke only. BP_Relic/BP_KeyRelic do not exist on current main.'}
state={'started':time.monotonic(),'last_control':None,'count':None,'sampled':False,'warmup_done':False,'busy':False}
ue.EditorPythonScripting.set_keep_python_script_alive(True)

def tick(delta):
 if state['busy']:
  return
 state['busy']=True
 try:
  if time.monotonic()-state['started']>600:
   raise RuntimeError('Smoke coordinator timeout')
  if not state['warmup_done']:
   if time.monotonic()-state['started']<3:
    return
   checks={'stone_center_hit':probe(0),'left_outer_handle_hit':probe(-35),'right_outer_handle_hit':probe(35)}
   ue.log('HC-A1_COLLISION_PROBES: '+json.dumps(checks))
   assert checks=={'stone_center_hit':True,'left_outer_handle_hit':False,'right_outer_handle_hit':False},'Collision probe mismatch'
   report['collision_probes']=checks
   loaded=ue.EditorLoadingAndSavingUtils.load_map('/Game/Maps/L_Site01')
   assert loaded
   assert ue.EditorLevelUtils.add_level_to_world(loaded,'/Game/Puzzles/Test/L_HCA1_AssetTest',ue.LevelStreamingAlwaysLoaded)
   assert ue.get_editor_subsystem(ue.LevelEditorSubsystem).set_current_level_by_name('L_HCA1_AssetTest')
   state['warmup_done']=True
   (HERE/'smoke_ready.json').write_text(json.dumps({'project':str(ROOT),'engine':report['engine'],'collision_probes':report['collision_probes'],'editor_app_python_exposed':hasattr(ue,'EditorAppToolset'),'port':8002},indent=2)+'\n')
  control_path=HERE/'smoke_control.json'
  if control_path.exists():
   control=json.loads(control_path.read_text())
   if control!=state['last_control']:
    state['last_control']=control
    if control.get('action')=='configure':
     assert not ue.EditorLevelLibrary.get_pie_worlds(True)
     state['count']=control['clients']
     state['sampled']=False
     (HERE/'smoke_configured.json').write_text(json.dumps({'clients':state['count'],'play_net_mode':'configured through isolated MCP API'})+'\n')
    elif control.get('action')=='finish':
     assert not ue.EditorLevelLibrary.get_pie_worlds(True)
     report['shared_master_unchanged']=hashlib.sha256((ROOT/'Content/Shared/Style/M_Stylized.uasset').read_bytes()).hexdigest()=='ed0865b6345022cdf19fde9bf660756f0ea17b2bedece13a1e860ecd4e20e1d9'
     assert report['shared_master_unchanged']
     (HERE/'engine_smoke_validation.json').write_text(json.dumps(report,indent=2)+'\n')
     ue.log('HC-A1_SMOKE_VALIDATION_COMPLETE')
     ue.unregister_slate_post_tick_callback(handle)
     ue.EditorPythonScripting.set_keep_python_script_alive(False)
     return
  worlds=ue.EditorLevelLibrary.get_pie_worlds(True)
  if state['count'] and not state['sampled'] and len(worlds)>=state['count']+1:
   samples=[]
   for w in worlds:
    relics=[a for a in ue.GameplayStatics.get_all_actors_of_class(w,ue.StaticMeshActor) if a.get_actor_label().startswith('HCA1_SM_')]
    game_state=ue.GameplayStatics.get_game_state(w)
    if len(relics)!=4 or game_state is None:
     return
    samples.append({'world':w.get_path_name(),'game_state_role':str(game_state.get_local_role()),'player_count':len(game_state.get_editor_property('player_array')),'relics':[{'name':a.get_actor_label(),'mesh':a.static_mesh_component.static_mesh.get_path_name()} for a in relics]})
   if any(s['player_count']<state['count'] for s in samples):
    return
   report['sessions'].append({'requested_clients':state['count'],'mode':'Play As Client; one process; dedicated PIE server','world_count':len(worlds),'samples':samples})
   (HERE/('smoke_clients_'+str(state['count'])+'.json')).write_text(json.dumps(report['sessions'][-1],indent=2)+'\n')
   state['sampled']=True
   ue.log('HC-A1_CLIENT_LOAD_PASSED_'+str(state['count']))
 except Exception as error:
  ue.log_error('HC-A1_SMOKE_FAILED: '+repr(error))
  ue.unregister_slate_post_tick_callback(handle)
  ue.EditorPythonScripting.set_keep_python_script_alive(False)
 finally:
  state['busy']=False
handle=ue.register_slate_post_tick_callback(tick)
