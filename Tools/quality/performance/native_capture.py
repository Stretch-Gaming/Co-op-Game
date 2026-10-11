"""Primary-only bounded native CSV capture; no asset/config writes."""
import builtins,datetime,json,time,unreal as ue
from pathlib import Path
assert Path(ue.Paths.project_dir()).resolve()==Path(ROOT).resolve()
assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-')
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert len(worlds)==1 and 'L_ConnectedRoomMaze' in worlds[0].get_path_name()
world=worlds[0];C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
players=ue.GameplayStatics.get_all_actors_of_class(world,C);assert len(players)==1
pawn=next(iter(players));controller=pawn.get_controller();assert pawn.is_locally_controlled()
key='_coop_native_csv_capture';assert not getattr(builtins,key,None),'Capture already active'
output=ROOT/'Saved/QualityPerformance';output.mkdir(exist_ok=True)
name='connected-preview-native-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')+'.csv'
state={'phase':'warmup','begin':time.monotonic(),'handle':None,'filename':name,'world':world.get_path_name(),'warmup_seconds':30,'requested_measurement_seconds':30,'frame_limit':3600,'context':ARGS.get('context'),'position_start':[getattr(pawn.get_actor_location(),c) for c in ('x','y','z')],'rotation_start':[getattr(controller.get_control_rotation(),c) for c in ('pitch','yaw','roll')],'viewport_size':controller.get_viewport_size(),'engine':ue.SystemLibrary.get_engine_version(),'command_line':ue.SystemLibrary.get_command_line(),'gpu_contention':'User preview PID47200 remains open. Other adventure editor closed. This is single-player editor/PIE timing, not an isolated standalone gameplay benchmark.'}
setattr(builtins,key,state)
def finish(error=None):
 try:
  if state['phase']=='capture':ue.SystemLibrary.execute_console_command(world,'csvprofile STOP')
 finally:
  if state['handle'] is not None:ue.unregister_slate_post_tick_callback(state['handle'])
  setattr(builtins,key,None);state['error']=error;state['wall_elapsed_seconds']=time.monotonic()-state['begin'];state['position_end']=[getattr(pawn.get_actor_location(),c) for c in ('x','y','z')];state['phase']='finished';state.pop('handle',None)
  (output/'native-capture-control.json').write_text(json.dumps(state,indent=2,default=str)+'\n')
def tick(delta):
 try:
  now=time.monotonic();assert world in ue.EditorLevelLibrary.get_pie_worlds(True),'PIE ended during capture'
  assert now-state['begin']<95,'Bounded capture timeout'
  if state['phase']=='warmup' and now-state['begin']>=30:
   ue.SystemLibrary.execute_console_command(world,'csvprofile STARTFILE='+name)
   ue.SystemLibrary.execute_console_command(world,'csvprofile FRAMES=3600');state['phase']='capture';state['capture_begin']=now
  elif state['phase']=='capture' and now-state['capture_begin']>=30:finish()
 except Exception as e:finish(str(e))
state['handle']=ue.register_slate_post_tick_callback(tick)
RESULT={'queued':True,'warmup_seconds':30,'measurement_seconds':30,'filename':name,'viewport':state['viewport_size'],'user_game_untouched':True}
